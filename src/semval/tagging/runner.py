"""Resumable tagging runs over a sample: ``data/runs/<run_id>/{manifest.json,tags.jsonl}``.

The runner owns the ledger. Taggers report each billed attempt and the runner records it,
so every dollar spent is in the ledger, refusals and retries included. A run stops cleanly
with ``STOPPED_BUDGET`` when the next call would pass the cap (or a recorded call did), and
the same ``run_id`` resumes it without re-tagging finished segments. ``tags.jsonl`` holds
``ValueTag``s only: offsets, never text.
"""

import datetime
import logging
import os
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import yaml

from semval.config import priced_model, retry_max_tokens
from semval.fsutil import atomic_write_text
from semval.tagging.base import (
    CallPath,
    RunManifest,
    RunStatus,
    TagBatchResult,
    Tagger,
    TaggerKind,
    TaggerSpec,
)
from semval.tagging.claude import ClaudeTagger, make_client
from semval.tagging.ledger import BudgetExceeded, CostLedger, cost_of
from semval.tagging.prompt import FewShotExample
from semval.tagging.quotes import resolve_quotes
from semval.tagging.runfiles import (  # noqa: F401 (re-exported)
    DEFAULT_PATHS,
    DEFAULT_RUNS_DIR,
    MANIFEST,
    TAGS,
    RunPaths,
    load_sample,
    read_text,
)
from semval.tags import Stance, ValueTag
from semval.units import Document, Segment, UnitLevel, segment
from semval.values import load_framework

log = logging.getLogger(__name__)


@runtime_checkable
class BudgetAware(Protocol):
    spend_guard: Callable[[float], bool] | None


@runtime_checkable
class BatchResumable(Protocol):
    on_batch_submitted: Callable[[str, list[str]], None] | None
    resume_batch_id: str | None


@runtime_checkable
class MaxTokensAware(Protocol):
    max_tokens_for: dict[str, int]


def make_run_id(
    spec: TaggerSpec, unit: UnitLevel | None = None, now: datetime.datetime | None = None
) -> str:
    unit = unit or spec.unit
    ts = (now or datetime.datetime.now(datetime.UTC)).strftime("%Y%m%dT%H%M%S")
    return (
        f"{ts}-{spec.kind}-{spec.model or 'none'}-{spec.effort or 'none'}-"
        f"{spec.level_id}-{unit or 'none'}-fs{int(spec.few_shot)}"
    )


def make_tagger(spec: TaggerSpec, client: Any = None, few_shot: Sequence[FewShotExample] = ()):
    if spec.kind != TaggerKind.CLAUDE:
        raise ValueError(f"build the {spec.kind} tagger yourself and pass it as tagger=")
    return ClaudeTagger(spec, client if client is not None else make_client(), few_shot)


def load_few_shot(path: Path) -> list[FewShotExample]:
    """A YAML list of examples, or a mapping with an ``examples`` list."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    items = data.get("examples") if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        raise ValueError(f"{path}: expected a non-empty list of few-shot examples")
    return [FewShotExample.model_validate(x) for x in items]


def select_documents(
    docs: list[Document], limit: int | None, limit_per_country: int | None
) -> list[Document]:
    """In sample order: at most ``limit_per_country`` per country, then ``limit`` in all."""
    per: dict[str, int] = {}
    out = []
    for d in docs:
        if limit_per_country is not None and per.get(d.country, 0) >= limit_per_country:
            continue
        per[d.country] = per.get(d.country, 0) + 1
        out.append(d)
    return out if limit is None else out[:limit]


def _save(run_dir: Path, m: RunManifest) -> None:
    atomic_write_text(run_dir / MANIFEST, m.model_dump_json(indent=2) + "\n")


def _keep_done_tags(run_dir: Path, done: set[str]) -> None:
    """Drop tags of segments the manifest does not list as done (a crash between appending
    tags and saving the manifest); those segments are tagged again."""
    path = run_dir / TAGS
    if not path.exists():
        return
    lines = [x for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    kept = [x for x in lines if ValueTag.model_validate_json(x).segment_id in done]
    if len(kept) != len(lines):
        log.warning("dropping %d tags of unfinished segments", len(lines) - len(kept))
    atomic_write_text(path, "".join(x + "\n" for x in kept))


def _open(
    run_dir: Path, run_id: str, spec: TaggerSpec, sample: str, prompt_sha: str, wording: dict
) -> RunManifest:
    path = run_dir / MANIFEST
    if not path.exists():
        run_dir.mkdir(parents=True, exist_ok=True)
        return RunManifest(
            run_id=run_id,
            spec=spec,
            input_sample=sample,
            prompt_sha256=prompt_sha,
            status=RunStatus.RUNNING,
            definition_wording=wording,
            started=datetime.datetime.now(datetime.UTC),
        )
    m = RunManifest.model_validate_json(path.read_text(encoding="utf-8"))
    for what, old, new in [
        ("spec", m.spec, spec),
        ("sample", m.input_sample, sample),
        ("prompt", m.prompt_sha256, prompt_sha),
    ]:
        if old != new:
            raise ValueError(f"run {run_id} exists with a different {what}; use a new run id")
    _keep_done_tags(run_dir, set(m.segments_done))
    m.status = RunStatus.RUNNING
    m.finished = None
    log.info("resuming run %s: %d segments done", run_id, len(m.segments_done))
    return m


def _to_value_tags(
    res: TagBatchResult, segs: dict[str, Segment], texts: dict[str, str], run_id: str
) -> list[ValueTag]:
    out = []
    for sid, raws in res.tags_by_segment.items():
        seg = segs[sid]
        for raw in raws:
            spans, unresolved = resolve_quotes(texts[seg.document_id], seg, raw.quotes)
            out.append(
                ValueTag(
                    segment_id=sid,
                    value_id=raw.value_id,
                    stance=Stance(raw.stance),
                    evidence=spans,
                    evidence_unresolved=unresolved or not raw.quotes,
                    confidence=raw.confidence,
                    run_id=run_id,
                )
            )
    return out


def _append_tags(run_dir: Path, tags: list[ValueTag]) -> None:
    with (run_dir / TAGS).open("a", encoding="utf-8", newline="\n") as f:
        for t in tags:
            f.write(t.model_dump_json() + "\n")
        f.flush()
        os.fsync(f.fileno())


class _Run:
    def __init__(self, m: RunManifest, run_dir: Path, ledger: CostLedger, docs_text: dict):
        self.m, self.run_dir, self.ledger, self.texts = m, run_dir, ledger, docs_text

    def record(self, res: TagBatchResult) -> bool:
        """Charge every call to the ledger; False if the cap was passed."""
        ok = True
        for c in res.calls:
            model, batch = priced_model(c.model), c.path == CallPath.BATCH
            cost = cost_of(c.usage, model, batch)
            try:
                self.ledger.record(self.m.run_id, c.usage, model, batch)
            except BudgetExceeded as e:
                log.warning("%s", e)
                ok = False
            self.m.usage_totals = self.m.usage_totals + c.usage
            self.m.cost_usd += cost
        return ok

    def store(self, res: TagBatchResult, segs: dict[str, Segment]) -> None:
        _append_tags(self.run_dir, _to_value_tags(res, segs, self.texts, self.m.run_id))
        done = set(self.m.segments_done)
        for sid in [*res.tags_by_segment, *res.refused]:
            if sid not in done:
                self.m.segments_done.append(sid)
                done.add(sid)
            self.m.failures.pop(sid, None)
        self.m.refused_segments += [s for s in res.refused if s not in self.m.refused_segments]
        self.m.refusals += res.refusals
        self.m.failures.update(res.failed)
        for sid in [*res.tags_by_segment, *res.refused]:
            self.m.truncated.pop(sid, None)
        self.m.truncated.update(res.truncated)
        self.m.served_by.update(res.served_by)


def run_tagging(
    spec: TaggerSpec,
    sample_name: str,
    run_id: str | None = None,
    limit: int | None = None,
    *,
    limit_per_country: int | None = None,
    unit: UnitLevel | None = None,
    tagger: Tagger | None = None,
    client: Any = None,
    few_shot: Sequence[FewShotExample] = (),
    ledger: CostLedger | None = None,
    paths: RunPaths = DEFAULT_PATHS,
) -> RunManifest:
    """Create or resume run ``run_id`` over sample ``sample_name`` and return its manifest.

    ``unit`` is needed only when the spec leaves it open (the lexicon works at any level).
    ``limit`` caps the documents in all, ``limit_per_country`` per country.
    """
    if spec.unit is not None and unit is not None and unit != spec.unit:
        raise ValueError(f"unit {unit} contradicts the spec's {spec.unit}")
    unit = spec.unit or unit
    if unit is None:
        raise ValueError("no unit: the spec leaves it open, so pass unit=")
    run_spec = spec.model_copy(update={"unit": unit})
    tagger = tagger or make_tagger(spec, client, few_shot)
    if tagger.spec.model_copy(update={"unit": unit}) != run_spec:
        raise ValueError("the tagger's spec does not match the run spec")

    fw_dir = Path(paths.framework_dir)
    framework = load_framework(fw_dir / f"{spec.framework_id}.yaml", local_dir=fw_dir / "local")
    targets = framework.target_set(spec.level_id)
    info = tagger.prompt_info(targets)
    ledger = ledger or CostLedger(Path(paths.runs_dir) / "ledger.jsonl")
    if spec.model is not None:
        ledger.total()  # fail closed on a damaged ledger before spending anything

    run_id = run_id or make_run_id(run_spec)
    run_dir = Path(paths.runs_dir) / run_id
    m = _open(run_dir, run_id, run_spec, sample_name, info.prompt_sha256, info.definition_wording)
    _save(run_dir, m)

    sample_docs = load_sample(sample_name, paths.samples_dir).documents
    docs = select_documents(sample_docs, limit, limit_per_country)
    # A submitted batch is fetched for exactly the segments it holds, whatever the limits.
    pending = dict(m.pending_batch_segments) if m.pending_batch_id else {}
    by_id = {d.id: d for d in sample_docs}
    selected = {d.id for d in docs}
    chosen = set(selected)
    for doc_id in dict.fromkeys(pending.values()):
        if doc_id not in by_id:
            raise ValueError(f"run {run_id}: pending batch document {doc_id} left the sample")
        if doc_id not in chosen:
            docs.append(by_id[doc_id])
            chosen.add(doc_id)
    texts = {d.id: read_text(paths.raw_dir, d) for d in docs}
    meta = {d.id: d.meta() for d in docs}
    segs = {s.id: s for d in docs for s in segment(d.id, texts[d.id], unit) if s.level == unit}
    if missing := [sid for sid in pending if sid not in segs]:
        raise ValueError(f"run {run_id}: pending batch segments not found: {missing[:3]}")

    # A truncated answer gets one retry at the raised cap; after that it stays a failure.
    retry_cap = retry_max_tokens(spec.effort) if spec.effort is not None else None
    exhausted = {
        sid for sid, cap in m.truncated.items() if retry_cap is not None and cap >= retry_cap
    }
    if exhausted:
        log.warning("%d segments truncated even at the raised cap; not retried", len(exhausted))
    done = set(m.segments_done)
    pending_segs = [segs[sid] for sid in pending]
    skip = done | set(pending) | exhausted
    rest = [s for s in segs.values() if s.document_id in selected and s.id not in skip]
    seg_text = {sid: texts[s.document_id][s.start : s.end] for sid, s in segs.items()}

    run = _Run(m, run_dir, ledger, texts)
    if isinstance(tagger, BudgetAware) and spec.model is not None:
        tagger.spend_guard = ledger.can_spend
    if isinstance(tagger, MaxTokensAware) and retry_cap is not None:
        tagger.max_tokens_for = {s.id: retry_cap for s in rest if s.id in m.truncated}
    if pending and not isinstance(tagger, BatchResumable):
        raise ValueError(f"run {run_id} has a pending batch but the tagger cannot fetch it")
    if isinstance(tagger, BatchResumable):
        tagger.resume_batch_id = m.pending_batch_id

        def submitted(batch_id: str, segment_ids: list[str]) -> None:
            m.pending_batch_id = batch_id
            m.pending_batch_segments = {sid: segs[sid].document_id for sid in segment_ids}
            _save(run_dir, m)

        tagger.on_batch_submitted = submitted

    if spec.batch:
        chunks = [c for c in (pending_segs, rest) if c]
    elif spec.model is not None:  # paid calls: store each one as soon as it returns
        chunks = [[s] for s in rest]
    else:
        by_doc: dict[str, list[Segment]] = {}
        for s in rest:
            by_doc.setdefault(s.document_id, []).append(s)
        chunks = list(by_doc.values())

    try:
        for chunk in chunks:
            res = tagger.tag(chunk, {s.id: seg_text[s.id] for s in chunk}, targets, meta)
            within_cap = run.record(res)
            run.store(res, segs)
            m.pending_batch_id = None
            m.pending_batch_segments = {}
            if not within_cap or res.skipped:
                m.status = RunStatus.STOPPED_BUDGET
                _save(run_dir, m)
                log.warning("run %s stopped at the budget cap; resume with the same id", run_id)
                return m
            _save(run_dir, m)
    except Exception:
        m.status = RunStatus.FAILED
        _save(run_dir, m)
        raise
    m.status = RunStatus.FAILED if m.failures else RunStatus.DONE
    m.finished = datetime.datetime.now(datetime.UTC)
    _save(run_dir, m)
    return m
