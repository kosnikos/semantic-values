"""Pool the tags of several runs for review.

A pooled ``Proposal`` is one distinct (document, value, stance) that at least one run
proposed, with the union of its evidence and the runs that proposed it. A verdict is keyed
by (document, value) at the runs' level, so one verdict settles every stance proposed for
that value. ``pool_unjudged`` gives the proposals with no verdict yet as ``ReviewItem``s,
which carry no run identity (the blind pass).
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from semval.review.labels import LabelStore
from semval.tagging.base import RunManifest
from semval.tagging.runfiles import DEFAULT_RUNS_DIR, load_run_tags
from semval.tags import EvidenceSpan, Stance, ValueTag
from semval.units import document_id_of

STANCE_ORDER = list(Stance)


class ReviewItem(BaseModel):
    """A proposed (value, stance) for a document, with nothing that names a run."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    value_id: str
    level_id: str
    stance: Stance
    evidence: list[EvidenceSpan] = Field(default_factory=list)
    evidence_unresolved: bool = False


class Proposal(ReviewItem):
    """A ``ReviewItem`` plus the runs that proposed it. Server-side only."""

    runs: list[str]

    def item(self) -> ReviewItem:
        return ReviewItem.model_validate(self.model_dump(exclude={"runs"}))


def shared_target(runs: Sequence[RunManifest]) -> tuple[str, str]:
    """The (framework id, level id) every run tagged at; ValueError if they differ."""
    if not runs:
        raise ValueError("no runs to review")
    targets = {(r.spec.framework_id, r.spec.level_id) for r in runs}
    if len(targets) > 1:
        raise ValueError(f"runs must share framework and level, got {sorted(targets)}")
    return targets.pop()


def run_documents(runs: Sequence[RunManifest]) -> list[str]:
    """Documents the runs finished, in first-seen order (first run first)."""
    return list(dict.fromkeys(document_id_of(s) for r in runs for s in r.segments_done))


def pool_proposals(
    runs: Sequence[RunManifest], tags_by_run: Mapping[str, list[ValueTag]]
) -> list[Proposal]:
    """Every distinct (document, value, stance) the runs proposed, in first-proposed order
    (run order, then file order), with evidence unioned over the runs and segments."""
    _, level_id = shared_target(runs)
    pooled: dict[tuple[str, str, Stance], Proposal] = {}
    for run in runs:
        for t in tags_by_run.get(run.run_id, []):
            key = (document_id_of(t.segment_id), t.value_id, t.stance)
            p = pooled.get(key)
            if p is None:
                p = pooled[key] = Proposal(
                    document_id=key[0], value_id=t.value_id, level_id=level_id,
                    stance=t.stance, runs=[],
                )  # fmt: skip
            if run.run_id not in p.runs:
                p.runs.append(run.run_id)
            spans = set(p.evidence) | set(t.evidence)
            p.evidence = sorted(spans, key=lambda e: (e.start, e.end))
            p.evidence_unresolved = p.evidence_unresolved or t.evidence_unresolved
    return list(pooled.values())


def blind_order(proposals: Sequence[Proposal], documents: Sequence[str]) -> list[Proposal]:
    """Sort by document, then value id, then stance: nothing follows the run order."""
    doc_rank = {d: i for i, d in enumerate(documents)}
    return sorted(
        proposals,
        key=lambda p: (doc_rank.get(p.document_id, len(doc_rank)), p.value_id,
                       STANCE_ORDER.index(p.stance)),
    )  # fmt: skip


def judged_keys(store: LabelStore, labeller: str, level_id: str) -> set[tuple[str, str]]:
    """(document, value) pairs this labeller has a verdict on at this level."""
    return {
        (r.document_id, r.value_id)
        for r in store.all()
        if r.labeller == labeller and r.level_id == level_id
    }


def pool_unjudged(
    runs: list[RunManifest],
    store: LabelStore,
    labeller: str,
    *,
    runs_dir: Path = DEFAULT_RUNS_DIR,
) -> list[ReviewItem]:
    """The union of the runs' tags that ``labeller`` has no verdict on, one item per distinct
    proposed (value, stance), with run identity removed."""
    _, level_id = shared_target(runs)
    tags = {r.run_id: load_run_tags(runs_dir, r.run_id) for r in runs}
    judged = judged_keys(store, labeller, level_id)
    return [p.item() for p in unjudged(pool_proposals(runs, tags), judged, run_documents(runs))]


def unjudged(
    proposals: Sequence[Proposal], judged: set[tuple[str, str]], documents: Sequence[str]
) -> list[Proposal]:
    """Proposals whose (document, value) has no verdict, in blind order."""
    open_ = [p for p in proposals if (p.document_id, p.value_id) not in judged]
    return blind_order(open_, documents)
