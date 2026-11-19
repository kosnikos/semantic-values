"""A review session over the Touché23 few-shot candidates.

The candidates play the part of one run: documents are the candidate item ids, texts come
from ``ToucheTextProvider`` (the same rendering that becomes ``FewShotExample.text``), and
the proposals are the drafted tags with their quotes as evidence spans. Verdicts go to the
usual ``LabelStore`` under the labeller, at leaf level, with ``CANDIDATES_RUN_ID`` as the
source run.
"""

from collections.abc import Sequence
from pathlib import Path

from semval.datasets.touche23 import ToucheItem, ToucheTextProvider
from semval.review.labels import DEFAULT_LABELS_DIR, LabelStore, NoteStore, label_paths
from semval.review.pool import Proposal
from semval.review.session import ReviewSession
from semval.tagging.base import RunManifest, RunStatus, TaggerKind, TaggerSpec
from semval.tagging.fewshot_candidates import (
    CANDIDATES_RUN_ID,
    DRAFT_EFFORT,
    DRAFT_MODEL,
    Candidate,
)
from semval.tagging.runfiles import DEFAULT_PATHS, RunPaths
from semval.tags import EvidenceSpan, Stance
from semval.units import UnitLevel
from semval.values import LEAF_LEVEL, load_framework

FRAMEWORK_ID = "schwartz19"


def _spans(text: str, quotes: Sequence[str]) -> list[EvidenceSpan]:
    out = []
    for q in quotes:
        start = text.find(q)
        if q and start >= 0:
            out.append(EvidenceSpan(start=start, end=start + len(q)))
    return sorted(set(out), key=lambda e: (e.start, e.end))


def open_candidate_session(
    candidates: Sequence[Candidate],
    items: Sequence[ToucheItem],
    *,
    labeller: str = "owner",
    labels_dir: Path = DEFAULT_LABELS_DIR,
    paths: RunPaths = DEFAULT_PATHS,
    framework_id: str = FRAMEWORK_ID,
) -> ReviewSession:
    """Candidates as one pseudo-run at leaf level, over the items' rendered texts."""
    by_id = {i.id: i for i in items}
    missing = [c.id for c in candidates if c.id not in by_id]
    if missing:
        raise ValueError(f"candidates without a Touché23 item: {missing[:3]}")
    spec = TaggerSpec(
        kind=TaggerKind.CLAUDE, model=DRAFT_MODEL, effort=DRAFT_EFFORT,
        framework_id=framework_id, level_id=LEAF_LEVEL, unit=UnitLevel.ARTICLE,
    )  # fmt: skip
    run = RunManifest(
        run_id=CANDIDATES_RUN_ID, spec=spec, input_sample="touche23-fewshot",
        prompt_sha256="0" * 64, status=RunStatus.DONE,
        segments_done=[f"{c.id}:a" for c in candidates],
    )  # fmt: skip
    proposals = []
    for c in candidates:
        text = by_id[c.id].text
        for t in c.tags:
            proposals.append(
                Proposal(
                    document_id=c.id, value_id=t.value_id, level_id=LEAF_LEVEL,
                    stance=Stance(t.stance), runs=[CANDIDATES_RUN_ID],
                    evidence=_spans(text, t.quotes), evidence_unresolved=not t.quotes,
                )
            )  # fmt: skip
    fw_dir = Path(paths.framework_dir)
    framework = load_framework(fw_dir / f"{framework_id}.yaml", local_dir=fw_dir / "local")
    labels_path, notes_path = label_paths(labels_dir, labeller)
    return ReviewSession(
        runs=[run],
        proposals=proposals,
        targets=framework.target_set(LEAF_LEVEL),
        provider=ToucheTextProvider([by_id[c.id] for c in candidates]),
        labels=LabelStore(labels_path),
        notes=NoteStore(notes_path),
        labeller=labeller,
    )
