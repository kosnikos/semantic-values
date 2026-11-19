"""In-domain few-shot examples built from paragraphs the owner has confirmed.

Newspaper text is copyrighted, so these examples live only in ``data/fewshot/local/`` (git
ignored). The file names its source articles (``source_documents``) so that scoring can drop
them: an article whose paragraph is in the prompt must not be scored.
"""

import logging
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from semval.fsutil import atomic_write_text
from semval.review.labels import DEFAULT_LABELS_DIR, LabelRecord, LabelStore, label_paths
from semval.tagging.base import RawTag
from semval.tagging.prompt import MAX_QUOTES, FewShotExample
from semval.tagging.runfiles import (
    DEFAULT_PATHS,
    RunPaths,
    load_run,
    load_run_tags,
    load_sample,
    read_text,
)
from semval.tags import Stance, ValueTag
from semval.units import Segment, UnitLevel, document_id_of, segment

log = logging.getLogger(__name__)

DEFAULT_LOCAL_PATH = Path("data/fewshot/local/articles.yaml")
MIN_PARAGRAPH_CHARS = 200
PER_ARTICLE_CAP = 2
TARGET_PER_STANCE = 2
LANGUAGE_ORDER = ("el", "en")
NOTICE = (
    "Local only, not for commit: newspaper text is copyrighted. The articles in "
    "source_documents must be excluded from scoring."
)
SOURCE_TEMPLATE = "{doc} (local, owner-confirmed; labeller {labeller}, run {run})"

# Reasons a paragraph with reject/mention tags is left out, in the order they are checked.
NO_LABEL = "tag without an owner label"
STANCE_DIFFERS = "owner's stance differs or value absent"
UNRESOLVED = "unresolved evidence"
TOO_SHORT = f"shorter than {MIN_PARAGRAPH_CHARS} chars"


@dataclass(frozen=True)
class _Candidate:
    example: FewShotExample
    document_id: str


@dataclass(frozen=True)
class Assessment:
    """The qualifying paragraphs and, per rule, how many paragraphs it alone-or-first rejected."""

    candidates: list[_Candidate]
    paragraphs_with_reject_or_mention: int
    disqualified: Counter[str]


def _quotes(text: str, tags: Iterable[ValueTag], seg: Segment, doc_text: str) -> list[str]:
    out: list[str] = []
    for t in tags:
        for e in t.evidence:
            s, end = max(e.start, seg.start), min(e.end, seg.end)
            q = doc_text[s:end] if s < end else ""
            if q.strip():
                out.append(q)
    return list(dict.fromkeys(out))[:MAX_QUOTES]


def assess(
    run_id: str,
    labeller: str,
    *,
    paths: RunPaths = DEFAULT_PATHS,
    labels_dir: Path = DEFAULT_LABELS_DIR,
) -> Assessment:
    run = load_run(paths.runs_dir, run_id)
    if run.spec.unit != UnitLevel.PARAGRAPH:
        raise ValueError(f"run {run_id} is not a paragraph-unit run")
    level = run.spec.level_id
    docs = {d.id: d for d in load_sample(run.input_sample, paths.samples_dir).documents}
    labels: dict[tuple[str, str], LabelRecord] = {
        (r.document_id, r.value_id): r
        for r in LabelStore(label_paths(labels_dir, labeller)[0]).all()
        if r.labeller == labeller and r.level_id == level
    }
    by_seg: dict[str, list[ValueTag]] = {}
    for t in load_run_tags(paths.runs_dir, run_id):
        by_seg.setdefault(t.segment_id, []).append(t)

    texts: dict[str, str] = {}
    segs: dict[str, dict[str, Segment]] = {}
    cands: list[_Candidate] = []
    seen, why = 0, Counter[str]()
    for seg_id in sorted(by_seg):
        tags = by_seg[seg_id]
        if not any(t.stance in (Stance.REJECT, Stance.MENTION) for t in tags):
            continue
        seen += 1
        doc_id = document_id_of(seg_id)
        if doc_id not in docs:
            raise ValueError(f"{seg_id}: document not in sample {run.input_sample}")
        if doc_id not in texts:
            texts[doc_id] = read_text(paths.raw_dir, docs[doc_id])
            segs[doc_id] = {s.id: s for s in segment(doc_id, texts[doc_id], UnitLevel.PARAGRAPH)}
        seg = segs[doc_id][seg_id]
        reason = None
        for t in tags:
            rec = labels.get((doc_id, t.value_id))
            if rec is None:
                reason = NO_LABEL
                break
            if rec.present_stance() != t.stance:
                reason = STANCE_DIFFERS
                break
        if reason is None and any(t.evidence_unresolved for t in tags):
            reason = UNRESOLVED
        if reason is None and seg.end - seg.start < MIN_PARAGRAPH_CHARS:
            reason = TOO_SHORT
        if reason:
            why[reason] += 1
            continue
        doc_text = texts[doc_id]
        raw: dict[tuple[str, Stance], list[ValueTag]] = {}
        for t in tags:
            raw.setdefault((t.value_id, t.stance), []).append(t)
        raw_tags = [
            RawTag(
                value_id=v,
                stance=s.value,
                quotes=_quotes(doc_text, group, seg, doc_text),  # type: ignore[arg-type]
            )
            for (v, s), group in raw.items()
        ]
        cands.append(
            _Candidate(
                FewShotExample(
                    id=seg_id,
                    text=doc_text[seg.start : seg.end],
                    language=docs[doc_id].language,
                    tags=raw_tags,
                    source=SOURCE_TEMPLATE.format(doc=doc_id, labeller=labeller, run=run_id),
                ),
                doc_id,
            )
        )
    return Assessment(cands, seen, why)


def _wanted(c: _Candidate, have: Counter[str]) -> int:
    """The candidate's reject/mention coverage still missing, summed over its stances."""
    stances = {t.stance for t in c.example.tags} & {"reject", "mention"}
    return sum(max(0, TARGET_PER_STANCE - have[s]) for s in stances)


def pick(cands: Sequence[_Candidate], n: int) -> list[FewShotExample]:
    """Deterministic choice: languages alternate (el first), reject and mention are covered
    first, then paragraphs of articles already used, then the id. At most
    ``PER_ARTICLE_CAP`` paragraphs per article."""
    left = sorted(cands, key=lambda c: c.example.id)
    chosen: list[_Candidate] = []
    per_doc: Counter[str] = Counter()
    have: Counter[str] = Counter()
    while len(chosen) < n:
        eligible = [c for c in left if per_doc[c.document_id] < PER_ARTICLE_CAP]
        if not eligible:
            break
        lang = LANGUAGE_ORDER[len(chosen) % len(LANGUAGE_ORDER)]
        pool = [c for c in eligible if c.example.language == lang] or eligible
        best = min(
            pool,
            key=lambda c: (-_wanted(c, have), per_doc[c.document_id] == 0, c.example.id),
        )
        chosen.append(best)
        left.remove(best)
        per_doc[best.document_id] += 1
        have.update({t.stance for t in best.example.tags})
    return [c.example for c in chosen]


def select_label_examples(
    run_id: str,
    labeller: str,
    n: int = 6,
    *,
    paths: RunPaths = DEFAULT_PATHS,
    labels_dir: Path = DEFAULT_LABELS_DIR,
) -> list[FewShotExample]:
    """Up to ``n`` paragraphs of ``run_id`` whose every tag the labeller confirmed."""
    a = assess(run_id, labeller, paths=paths, labels_dir=labels_dir)
    return pick(a.candidates, n)


def write_local_fewshot(
    path: Path, examples: Sequence[FewShotExample], *, run_id: str, labeller: str
) -> list[str]:
    """Write the examples with a header naming their source articles; returns those ids."""
    docs = sorted({document_id_of(e.id) for e in examples})
    doc: dict[str, Any] = {
        "notice": NOTICE,
        "source_run": run_id,
        "labeller": labeller,
        "source_documents": docs,
        "examples": [e.model_dump(mode="json", exclude_none=True) for e in examples],
    }
    atomic_write_text(
        Path(path), yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100)
    )
    return docs


def excluded_documents(paths: Iterable[Path]) -> set[str]:
    """Articles named by the few-shot files' ``source_documents`` (none for files without it)."""
    out: set[str] = set()
    for p in paths:
        data = yaml.safe_load(Path(p).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            out.update(str(d) for d in data.get("source_documents") or [])
    return out
