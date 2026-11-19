import pytest

from semval.tags import EvidenceSpan, Stance, ValueTag, merge, rollup_tags
from semval.units import Segment, UnitLevel


def _seg(id_, level, parent):
    return Segment(id=id_, document_id="d", level=level, parent_id=parent, start=0, end=1)


SEGS = [
    _seg("d:a", UnitLevel.ARTICLE, None),
    _seg("d:p0", UnitLevel.PARAGRAPH, "d:a"),
    _seg("d:p0:s0", UnitLevel.SENTENCE, "d:p0"),
    _seg("d:p0:s1", UnitLevel.SENTENCE, "d:p0"),
]


def _tag(seg, stance, value="v", ev=(), conf=None, run="r1", unresolved=False):
    return ValueTag(
        segment_id=seg,
        value_id=value,
        stance=stance,
        evidence=[EvidenceSpan(start=a, end=b) for a, b in ev],
        evidence_unresolved=unresolved,
        confidence=conf,
        run_id=run,
    )


def _one(tags, to=UnitLevel.PARAGRAPH):
    (t,) = merge(tags, SEGS, to)
    return t


@pytest.mark.parametrize(
    ("stances", "expected"),
    [
        ([Stance.ENDORSE, Stance.REJECT], Stance.CONTESTED),
        ([Stance.ENDORSE, Stance.MENTION], Stance.ENDORSE),
        ([Stance.REJECT, Stance.MENTION], Stance.REJECT),
        ([Stance.REJECT], Stance.REJECT),
        ([Stance.MENTION, Stance.MENTION], Stance.MENTION),
    ],
)
def test_merge_branches(stances, expected):
    tags = [_tag(f"d:p0:s{i}", s) for i, s in enumerate(stances)]
    assert _one(tags).stance is expected


def test_merge_evidence_confidence_unresolved():
    tags = [
        _tag("d:p0:s0", Stance.ENDORSE, ev=[(0, 3)], conf=0.4),
        _tag("d:p0:s1", Stance.MENTION, ev=[(5, 8), (0, 3)], conf=0.9, unresolved=True),
    ]
    t = _one(tags)
    assert t.segment_id == "d:p0"
    assert sorted((e.start, e.end) for e in t.evidence) == [(0, 3), (5, 8)]
    assert t.confidence == 0.9
    assert t.evidence_unresolved is True
    assert _one([_tag("d:p0:s0", Stance.MENTION)]).confidence is None


def test_merge_passthrough_and_combine_at_target_level():
    tags = [_tag("d:p0", Stance.REJECT), _tag("d:p0:s0", Stance.ENDORSE)]
    assert _one(tags).stance is Stance.CONTESTED


def test_merge_to_article_and_separate_values():
    tags = [_tag("d:p0:s0", Stance.ENDORSE, "a"), _tag("d:p0:s1", Stance.REJECT, "b")]
    out = merge(tags, SEGS, UnitLevel.ARTICLE)
    assert {(t.segment_id, t.value_id, t.stance) for t in out} == {
        ("d:a", "a", Stance.ENDORSE),
        ("d:a", "b", Stance.REJECT),
    }


def test_merge_finer_raises():
    with pytest.raises(ValueError, match="finer"):
        merge([_tag("d:p0", Stance.ENDORSE)], SEGS, UnitLevel.SENTENCE)


def test_merge_run_id_mismatch_raises():
    tags = [_tag("d:p0:s0", Stance.ENDORSE), _tag("d:p0:s1", Stance.ENDORSE, run="r2")]
    with pytest.raises(ValueError, match="run_id"):
        merge(tags, SEGS, UnitLevel.PARAGRAPH)


def test_rollup_contested():
    tags = [
        _tag("d:a", Stance.ENDORSE, "self_direction_thought"),
        _tag("d:a", Stance.REJECT, "self_direction_action"),
        _tag("d:a", Stance.MENTION, "power"),
    ]
    m = {"self_direction_thought": "self_direction", "self_direction_action": "self_direction"}
    m["power"] = "power"
    out = {t.value_id: t for t in rollup_tags(tags, m)}
    assert out["self_direction"].stance is Stance.CONTESTED
    assert out["power"].stance is Stance.MENTION


def test_rollup_unknown_value_raises():
    with pytest.raises(ValueError, match="unknown"):
        rollup_tags([_tag("d:a", Stance.ENDORSE, "zzz")], {"a": "b"})
