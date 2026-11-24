from pathlib import Path
from typing import get_args

import pytest

from semval.config import BUDGET_USD
from semval.tagging.base import RawTag, RunManifest, RunStatus, Tagger, TaggerKind, Usage
from semval.tagging.lexicon import LexiconTagger
from semval.tags import Stance
from semval.targets import TargetDef, TargetSet
from semval.units import DocumentMeta, Segment, UnitLevel

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


DOCS = {
    "d1": DocumentMeta(language="en", genre="opinion"),
    "d2": DocumentMeta(language="el", genre="opinion"),
}


def tagger() -> LexiconTagger:
    return LexiconTagger(LEX)


def test_lexicon_emits_mention_only():
    res = tagger().tag(
        [seg("s1")],
        {"s1": "We must protect our families and defend the traditions."},
        targets(),
        DOCS,
    )
    tags = res.tags_by_segment["s1"]
    assert {t.value_id for t in tags} >= {"security", "tradition"}
    assert all(t.stance == Stance.MENTION for t in tags)
    assert all(t.quotes for t in tags)
    assert res.usage == Usage()
    assert tagger().spec.kind == TaggerKind.LEXICON
    assert isinstance(tagger(), Tagger)


def test_lexicon_ignores_non_english():
    res = tagger().tag([seg("s1", "d2")], {"s1": "protect our traditions"}, targets(), DOCS)
    assert res.tags_by_segment == {"s1": []}


def test_lexicon_no_match_gives_empty():
    res = tagger().tag([seg("s1")], {"s1": "Nothing relevant here."}, targets(), DOCS)
    assert res.tags_by_segment["s1"] == []


def test_lexicon_level_mismatch_raises():
    with pytest.raises(ValueError):
        tagger().tag([seg("s1")], {"s1": "x"}, targets("group4"), DOCS)


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


def test_lexicon_missing_document_raises():
    with pytest.raises(ValueError, match="d9"):
        tagger().tag([seg("s1", "d9")], {"s1": "protect"}, targets(), DOCS)


def test_raw_tag_stance_matches_stance_enum():
    literal = set(get_args(RawTag.model_fields["stance"].annotation))
    assert literal == {s.value for s in Stance} - {Stance.CONTESTED.value}


def test_manifest_rejects_unknown_wording_key():
    with pytest.raises(ValueError):
        RunManifest(
            run_id="r",
            spec=tagger().spec,
            input_sample="s",
            prompt_sha256="0" * 64,
            status=RunStatus.RUNNING,
            definition_wording={"oficial": 1},
        )
