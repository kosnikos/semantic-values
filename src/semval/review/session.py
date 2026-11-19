"""A review session: pooled runs, a text provider and a labeller's stores, as JSON payloads.

No HTTP here (see ``server``). In blind mode no payload names a run, a model or a run
setting; the runs behind each verdict are still written to the label file.

Rows. A *model row* is a proposed (value, stance): in normal mode the first run's stance per
value, in blind mode every distinct unjudged stance. An *owner row* is a value the owner
marked present that no shown model row covers (an added value). A row's verdict is derived
from the one label of its (document, value), so sibling rows always agree.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from semval.review.highlights import NO_LIMIT, assign_colors, merged_spans, text_pieces
from semval.review.labels import (
    DEFAULT_LABELS_DIR,
    LabelRecord,
    LabelStore,
    NoteStore,
    Verdict,
    label_paths,
)
from semval.review.pool import (
    STANCE_ORDER,
    Proposal,
    judged_keys,
    pool_proposals,
    run_documents,
    shared_target,
    unjudged,
)
from semval.review.texts import DocInfo, RawDocsProvider, TextProvider, TextUnavailable
from semval.tagging.base import RunManifest
from semval.tagging.runfiles import DEFAULT_PATHS, RunPaths, load_run, load_run_tags
from semval.tags import EvidenceSpan, Stance
from semval.targets import TargetSet
from semval.values import load_framework

NOTE_MAX_CHARS = 8000  # keeps any note's JSON well under the server's body limit


class ReviewMode(StrEnum):
    REVIEW = "review"
    BLIND = "blind"


class RowKind(StrEnum):
    MODEL = "model"  # a proposed (value, stance)
    OWNER = "owner"  # a value the owner marked present that no shown model row covers


class SessionError(ValueError):
    """A request the session refuses (HTTP 400)."""


class NotFound(LookupError):
    """An unknown document (HTTP 404)."""


class VerdictIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    value_id: str
    verdict: Verdict
    model_stance: Stance | None = None
    corrected_stance: Stance | None = None


class NoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    note: str = Field(max_length=NOTE_MAX_CHARS)


@dataclass
class ReviewSession:
    runs: list[RunManifest]
    proposals: list[Proposal]
    targets: TargetSet
    provider: TextProvider
    labels: LabelStore
    notes: NoteStore
    labeller: str = "owner"
    blind: bool = False
    level_id: str = field(init=False)
    documents: list[str] = field(init=False)

    def __post_init__(self) -> None:
        _, self.level_id = shared_target(self.runs)
        if self.targets.level_id != self.level_id:
            raise ValueError(f"targets are for {self.targets.level_id}, runs for {self.level_id}")
        self._pairs = {(p.document_id, p.value_id, p.stance): p for p in self.proposals}
        # every proposed (document, value), with the union of its evidence over the stances
        spans: dict[tuple[str, str], set[EvidenceSpan]] = {}
        for p in self.proposals:
            spans.setdefault((p.document_id, p.value_id), set()).update(p.evidence)
        self._evidence = {k: sorted(v, key=lambda e: (e.start, e.end)) for k, v in spans.items()}
        self._target = {t.id: t for t in self.targets.targets}
        self._rank = {t.id: i for i, t in enumerate(self.targets.targets)}
        run_docs = run_documents(self.runs)
        if self.blind:
            # fixed for the session: what is judged now stays on screen until a restart
            self._prejudged = judged_keys(self.labels, self.labeller, self.level_id)
            shown = unjudged(self.proposals, self._prejudged, run_docs)
            self.documents = list(dict.fromkeys(p.document_id for p in shown))
        else:
            self._prejudged = set()
            first: dict[tuple[str, str], Proposal] = {}
            for p in self.proposals:
                first.setdefault((p.document_id, p.value_id), p)
            shown = list(first.values())
            self.documents = list(dict.fromkeys([*run_docs, *(p.document_id for p in shown)]))
        self._shown: dict[str, list[Proposal]] = {}
        for p in shown:
            self._shown.setdefault(p.document_id, []).append(p)

    # -- reading -------------------------------------------------------------------------

    def _labels_by_doc(self) -> dict[str, dict[str, LabelRecord]]:
        out: dict[str, dict[str, LabelRecord]] = {}
        for r in self.labels.all():
            if r.labeller == self.labeller and r.level_id == self.level_id:
                out.setdefault(r.document_id, {})[r.value_id] = r
        return out

    def _value(self, value_id: str) -> dict[str, Any]:
        t = self._target.get(value_id)
        return {
            "value_id": value_id,
            "name": t.name if t else value_id,
            "definition": t.definition if t else "",
        }

    @staticmethod
    def _paint(rows: list[dict], addable: list[dict]) -> None:
        """Per-article colours: table order first, then the add list."""
        colors = assign_colors([x["value_id"] for x in [*rows, *addable]])
        for x in [*rows, *addable]:
            x["color"] = colors[x["value_id"]]

    def _model_rows(self, doc_id: str) -> list[Proposal]:
        def order(p: Proposal) -> tuple:
            start = min((e.start for e in p.evidence), default=float("inf"))
            return (
                start,
                self._rank.get(p.value_id, len(self._rank)),
                STANCE_ORDER.index(p.stance),
            )

        return sorted(self._shown.get(doc_id, []), key=order)

    def _rows(self, doc_id: str, labels: dict[str, LabelRecord]) -> tuple[list[dict], list]:
        """Rows for the table, and each row's evidence (empty for owner rows)."""
        rows, evidence = [], []
        for p in self._model_rows(doc_id):
            label = labels.get(p.value_id)
            present = label.present_stance() if label else None
            if label is None:
                verdict = None
            elif present is None:
                verdict = Verdict.NOT_PRESENT
            else:
                verdict = Verdict.CORRECT if present == p.stance else Verdict.WRONG_CALL
            row = {
                "row_id": f"m|{p.value_id}|{p.stance}", "kind": RowKind.MODEL, **self._value(p.value_id),
                "stance": p.stance, "spans": len(merged_spans(p.evidence, NO_LIMIT)),
                "evidence_unresolved": p.evidence_unresolved,
                "verdict": verdict, "verdict_stance": present,
            }  # fmt: skip
            if not self.blind:
                row["source_runs"] = p.runs
            rows.append(row)
            evidence.append(p.evidence)
        covered = {r["value_id"] for r in rows}
        owner = [
            rec
            for v, rec in labels.items()
            if v not in covered
            and rec.present_stance() is not None
            and (doc_id, v) not in self._prejudged
        ]
        for rec in sorted(owner, key=lambda r: self._rank.get(r.value_id, len(self._rank))):
            rows.append({
                "row_id": f"o|{rec.value_id}", "kind": RowKind.OWNER, **self._value(rec.value_id),
                "stance": None, "spans": 0, "evidence_unresolved": False,
                "verdict": Verdict.ADDED, "verdict_stance": rec.present_stance(),
            })  # fmt: skip
            evidence.append([])
        return rows, evidence

    def _addable(self, rows: list[dict], labels: dict[str, LabelRecord]) -> list[dict]:
        taken = {r["value_id"] for r in rows} | {
            v for v, rec in labels.items() if rec.present_stance() is not None
        }
        return [self._value(t.id) for t in self.targets.targets if t.id not in taken]

    def _table(self, doc_id: str) -> dict[str, Any]:
        labels = self._labels_by_doc().get(doc_id, {})
        rows, _ = self._rows(doc_id, labels)
        addable = self._addable(rows, labels)
        self._paint(rows, addable)
        return {"document_id": doc_id, "rows": rows, "addable": addable}

    def items_payload(self) -> dict[str, Any]:
        by_doc = self._labels_by_doc()
        documents, items = [], []
        for doc_id in self.documents:
            rows, _ = self._rows(doc_id, by_doc.get(doc_id, {}))
            model = [r for r in rows if r["kind"] == RowKind.MODEL]
            documents.append({
                "document_id": doc_id, "rows": len(model),
                "judged": sum(r["verdict"] is not None for r in model),
            })  # fmt: skip
            items += [
                {"document_id": doc_id, "value_id": r["value_id"], "stance": r["stance"],
                 "verdict": r["verdict"]}
                for r in model
            ]  # fmt: skip
        out: dict[str, Any] = {
            "mode": ReviewMode.BLIND if self.blind else ReviewMode.REVIEW,
            "labeller": self.labeller,
            "documents": documents,
            "items": items,
        }
        if not self.blind:
            out["settings"] = self._settings()
        return out

    def _settings(self) -> dict[str, Any]:
        return {
            "framework_id": self.targets.framework_id,
            "level_id": self.level_id,
            "runs": [
                {"run_id": r.run_id, "status": r.status,
                 **r.spec.model_dump(mode="json", exclude={"framework_id", "level_id"})}
                for r in self.runs
            ],
        }  # fmt: skip

    def _info(self, doc_id: str) -> DocInfo:
        try:
            return self.provider.info(doc_id)
        except TextUnavailable:
            return DocInfo()

    def doc_payload(self, doc_id: str) -> dict[str, Any]:
        if doc_id not in self.documents:
            raise NotFound(doc_id)
        labels = self._labels_by_doc().get(doc_id, {})
        rows, evidence = self._rows(doc_id, labels)
        addable = self._addable(rows, labels)
        self._paint(rows, addable)
        text_error, pieces = None, []
        try:
            text = self.provider.text(doc_id)
        except TextUnavailable as e:
            text_error = str(e)
        else:
            spans = {i: merged_spans(ev, len(text)) for i, ev in enumerate(evidence) if ev}
            for i, s in spans.items():
                rows[i]["spans"] = len(s)
            pieces = text_pieces(text, spans)
        return {
            "document_id": doc_id,
            "index": self.documents.index(doc_id) + 1,
            "total": len(self.documents),
            "meta": self._info(doc_id).model_dump(mode="json"),
            "pieces": pieces,
            "text_error": text_error,
            "rows": rows,
            "addable": addable,
            "note": self.notes.get(self.labeller, doc_id),
        }

    # -- writing -------------------------------------------------------------------------

    def save_verdict(self, body: Any) -> dict[str, Any]:
        """Store one verdict (ValidationError or SessionError if refused); the new table."""
        v = VerdictIn.model_validate(body)
        if v.document_id not in self.documents:
            raise SessionError(f"unknown document {v.document_id!r}")
        if v.value_id not in self._target:
            raise SessionError(f"{v.value_id!r} is not a target of level {self.level_id}")
        key = (v.document_id, v.value_id)
        proposed = key in self._evidence
        if v.verdict == Verdict.ADDED and proposed:
            raise SessionError(f"{v.value_id} was proposed here: judge its row, do not add it")
        if v.verdict != Verdict.ADDED and proposed and v.model_stance is None:
            raise SessionError(f"a verdict on proposed {v.value_id} needs its model_stance")
        runs: list[str] = []
        if v.model_stance is not None:
            p = self._pairs.get((v.document_id, v.value_id, v.model_stance))
            if p is None:
                raise SessionError(f"no run proposed {v.value_id} {v.model_stance} here")
            runs = list(p.runs)
        old = self._labels_by_doc().get(v.document_id, {}).get(v.value_id)
        rec = LabelRecord(
            labeller=self.labeller, document_id=v.document_id, value_id=v.value_id,
            level_id=self.level_id, model_stance=v.model_stance, verdict=v.verdict,
            corrected_stance=v.corrected_stance, note=old.note if old else "", source_runs=runs,
            model_evidence=self._evidence.get(key, []),
            owner_evidence=old.owner_evidence if old else [],
        )  # fmt: skip
        self.labels.upsert(rec)
        return {**self._table(v.document_id), "saved": rec.updated.isoformat()}

    def save_note(self, body: Any) -> dict[str, Any]:
        n = NoteIn.model_validate(body)
        if n.document_id not in self.documents:
            raise SessionError(f"unknown document {n.document_id!r}")
        self.notes.set(self.labeller, n.document_id, n.note)
        return {"document_id": n.document_id, "saved": True}


def open_session(
    run_ids: Sequence[str],
    *,
    blind: bool = False,
    labeller: str = "owner",
    paths: RunPaths = DEFAULT_PATHS,
    labels_dir: Path = DEFAULT_LABELS_DIR,
    provider: TextProvider | None = None,
) -> ReviewSession:
    """Load runs, their framework level and their samples' texts into a session.

    ValueError if a run is missing or the runs do not share framework and level.
    """
    runs = [load_run(paths.runs_dir, r) for r in dict.fromkeys(run_ids)]
    framework_id, level_id = shared_target(runs)
    fw_dir = Path(paths.framework_dir)
    targets = load_framework(fw_dir / f"{framework_id}.yaml", local_dir=fw_dir / "local")
    tags = {r.run_id: load_run_tags(paths.runs_dir, r.run_id) for r in runs}
    if provider is None:
        provider = RawDocsProvider.from_samples(
            [r.input_sample for r in runs], paths.samples_dir, paths.raw_dir
        )
    labels_path, notes_path = label_paths(labels_dir, labeller)
    return ReviewSession(
        runs=runs,
        proposals=pool_proposals(runs, tags),
        targets=targets.target_set(level_id),
        provider=provider,
        labels=LabelStore(labels_path),
        notes=NoteStore(notes_path),
        labeller=labeller,
        blind=blind,
    )
