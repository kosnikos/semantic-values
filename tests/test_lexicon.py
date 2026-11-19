from pathlib import Path

import pytest

from semval.config import BUDGET_USD
from semval.tagging.base import RunManifest, RunStatus, Tagger, TaggerKind, Usage
from semval.tagging.lexicon import LexiconTagger
from semval.tags import Stance
from semval.targets import TargetDef, TargetSet
from semval.units import Segment, UnitLevel

LEX = Path(__file__).parent.parent / "data" / "lexicon" / "basic10_seed.yaml"
IDS = ["self_direction", "stimulation", "hedonism", "achievement", "power", "security",
       "conformity", "tradition", "benevolence", "universalism"]  # fmt: skip


def targets(level="basic10") -> TargetSet:
    return TargetSet(
        framework_id="schwartz19",
        level_id=level,
        targets=[TargetDef(id=i, name=i, definition="A value.") for i in IDS],
    )


def seg(i: str, doc: str = "d1") -> Segment:
    return Segment(id=i, document_id=doc, level=UnitLevel.SENTENCE, start=0, end=5)


def tagger(languages=None) -> LexiconTagger:
    return LexiconTagger(LEX, languages or {"d1": "en", "d2": "el"}, unit=UnitLevel.SENTENCE)


def test_lexicon_emits_mention_only():
    res = tagger().tag(
        [seg("s1")], {"s1": "We must protect our families and defend the traditions."}, targets()
    )
    tags = res.tags_by_segment["s1"]
    assert {t.value_id for t in tags} >= {"security", "tradition"}
    assert all(t.stance == Stance.MENTION for t in tags)
    assert all(t.quotes for t in tags)
    assert res.usage == Usage()
    assert tagger().spec.kind == TaggerKind.LEXICON
    assert isinstance(tagger(), Tagger)


def test_lexicon_ignores_non_english():
    res = tagger().tag([seg("s1", "d2")], {"s1": "protect our traditions"}, targets())
    assert res.tags_by_segment == {"s1": []}


def test_lexicon_no_match_gives_empty():
    res = tagger().tag([seg("s1")], {"s1": "Nothing relevant here."}, targets())
    assert res.tags_by_segment["s1"] == []


def test_lexicon_level_mismatch_raises():
    with pytest.raises(ValueError):
        tagger().tag([seg("s1")], {"s1": "x"}, targets("group4"))


def test_manifest_records_definition_wording():
    m = RunManifest(
        run_id="r",
        spec=tagger().spec,
        input_sample="s",
        prompt_sha256="0" * 64,
        status=RunStatus.RUNNING,
        definition_wording={"official": 3, "fallback": 7},
    )
    assert m.definition_wording["fallback"] == 7
    assert BUDGET_USD == 50.0
