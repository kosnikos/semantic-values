"""Value tags and their combination, framework-agnostic.

``merge`` lifts tags to a coarser text level; ``rollup_tags`` lifts them to a coarser
value level. Both group tags and combine each group with one shared rule.
"""

from collections.abc import Iterable
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from semval.units import Segment, UnitLevel


class Stance(StrEnum):
    ENDORSE = "endorse"
    REJECT = "reject"
    MENTION = "mention"
    CONTESTED = "contested"  # only ever produced by combining tags


class EvidenceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    start: int
    end: int


class ValueTag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_id: str
    value_id: str
    stance: Stance
    evidence: list[EvidenceSpan] = Field(default_factory=list)
    evidence_unresolved: bool = False
    confidence: float | None = None
    run_id: str


def _combine(segment_id: str, value_id: str, group: list[ValueTag]) -> ValueTag:
    """The one combination rule: contested if any endorse and any reject, else the
    strongest of endorse > reject > mention; evidence unioned, confidence the max."""
    stances = {t.stance for t in group}
    if Stance.CONTESTED in stances or {Stance.ENDORSE, Stance.REJECT} <= stances:
        stance = Stance.CONTESTED
    else:
        stance = next(s for s in (Stance.ENDORSE, Stance.REJECT, Stance.MENTION) if s in stances)
    evidence = sorted({e for t in group for e in t.evidence}, key=lambda e: (e.start, e.end))
    confs = [t.confidence for t in group if t.confidence is not None]
    return ValueTag(
        segment_id=segment_id,
        value_id=value_id,
        stance=stance,
        evidence=list(evidence),
        evidence_unresolved=any(t.evidence_unresolved for t in group),
        confidence=max(confs) if confs else None,
        run_id=group[0].run_id,
    )


def _check_single_run(tags: list[ValueTag]) -> None:
    run_ids = {t.run_id for t in tags}
    if len(run_ids) > 1:
        raise ValueError(f"cannot combine tags from different run_id values: {sorted(run_ids)}")


def _combine_groups(keyed: Iterable[tuple[tuple[str, str], ValueTag]]) -> list[ValueTag]:
    groups: dict[tuple[str, str], list[ValueTag]] = {}
    for key, tag in keyed:
        groups.setdefault(key, []).append(tag)
    return [_combine(seg, val, g) for (seg, val), g in groups.items()]


def merge(tags: list[ValueTag], segments: list[Segment], to_level: UnitLevel) -> list[ValueTag]:
    """Lift tags to their ancestor segment at ``to_level`` and combine per (segment, value)."""
    _check_single_run(tags)
    by_id = {s.id: s for s in segments}

    def ancestor(segment_id: str) -> str:
        seg = by_id.get(segment_id)
        if seg is None:
            raise ValueError(f"unknown segment id {segment_id!r}")
        if seg.level.rank < to_level.rank:
            raise ValueError(f"cannot merge to {to_level}: it is finer than the tag's {seg.level}")
        while seg.level != to_level:
            if seg.parent_id is None or seg.parent_id not in by_id:
                raise ValueError(f"segment {seg.id!r} has no ancestor at {to_level}")
            seg = by_id[seg.parent_id]
        return seg.id

    return _combine_groups(((ancestor(t.segment_id), t.value_id), t) for t in tags)


def rollup_tags(tags: list[ValueTag], rollup_map: dict[str, str]) -> list[ValueTag]:
    """Map each tag's value id through ``rollup_map`` and combine per (segment, target)."""
    _check_single_run(tags)
    keyed = []
    for t in tags:
        if t.value_id not in rollup_map:
            raise ValueError(f"unknown value id {t.value_id!r} in roll-up")
        keyed.append(((t.segment_id, rollup_map[t.value_id]), t))
    return _combine_groups(keyed)
