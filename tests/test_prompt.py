import json

import pytest

from semval.tagging.base import DefinitionWording, RawTag
from semval.tagging.prompt import FewShotExample, build_prompt, prompt_sha256
from semval.targets import OfficialDefinition, TargetDef, TargetSet


def targets() -> TargetSet:
    return TargetSet(
        framework_id="toy",
        level_id="leaf",
        targets=[
            TargetDef(
                id="alpha",
                name="Alpha",
                definition="Our own alpha wording.",
                official=OfficialDefinition(
                    citation="Someone (2012)", page="p. 1", text="The official alpha text."
                ),
                examples_endorse=["Alpha matters."],
                examples_reject=["Alpha is overrated."],
            ),
            TargetDef(
                id="beta",
                name="Beta",
                definition="Our own beta wording.",
                official=OfficialDefinition(
                    citation="Someone (2012)", page="p. 2", local_only=True
                ),
            ),
            TargetDef(id="gamma", name="Gamma", definition="Our own gamma wording."),
        ],
    )


def test_schema_restricts_value_ids():
    schema = build_prompt(targets(), []).schema
    item = schema["properties"]["tags"]["items"]
    assert item["properties"]["value_id"]["enum"] == ["alpha", "beta", "gamma"]
    assert item["properties"]["stance"]["enum"] == ["endorse", "reject", "mention"]
    assert schema["required"] == ["tags"]
    assert schema["additionalProperties"] is False and item["additionalProperties"] is False
    assert set(item["required"]) == {"value_id", "stance", "quotes", "confidence"}
    assert item["properties"]["quotes"]["minItems"] == 1
    # an empty tag list is allowed: no minItems on the outer list
    assert "minItems" not in schema["properties"]["tags"]
    json.dumps(schema)  # serialisable


def test_prompt_uses_official_definition_when_present():
    parts = build_prompt(targets(), [])
    assert "The official alpha text." in parts.system
    assert "Our own alpha wording." not in parts.system
    # beta's official text is local-only and missing here, gamma has none: our wording
    assert "Our own beta wording." in parts.system
    assert "Our own gamma wording." in parts.system
    assert parts.definition_wording == {
        DefinitionWording.OFFICIAL.value: 1,
        DefinitionWording.FALLBACK.value: 2,
    }
    assert "Alpha matters." in parts.system and "Alpha is overrated." in parts.system
    for word in ("endorse", "reject", "mention", "verbatim"):
        assert word in parts.system


def test_prompt_includes_few_shot_with_attribution():
    ex = FewShotExample(
        id="ex1",
        text="We must protect alpha.",
        language="en",
        tags=[RawTag(value_id="alpha", stance="endorse", quotes=["protect alpha"])],
        source="Touché23-ValueEval (CC BY 4.0), item A01",
    )
    parts = build_prompt(targets(), [ex])
    assert "We must protect alpha." in parts.system
    assert "Touché23-ValueEval (CC BY 4.0), item A01" in parts.system
    assert '"protect alpha"' in parts.system
    assert parts.system != build_prompt(targets(), []).system


def test_few_shot_with_unknown_value_is_rejected():
    ex = FewShotExample(
        id="ex1", text="t", language="en", source="s",
        tags=[RawTag(value_id="delta", stance="mention", quotes=["t"])],
    )  # fmt: skip
    with pytest.raises(ValueError, match="delta"):
        build_prompt(targets(), [ex])


def test_prompt_is_stable_and_hash_covers_schema():
    a, b = build_prompt(targets(), []), build_prompt(targets(), [])
    assert a.system == b.system and prompt_sha256(a) == prompt_sha256(b)
    fewer = TargetSet(framework_id="toy", level_id="leaf", targets=targets().targets[:2])
    assert prompt_sha256(build_prompt(fewer, [])) != prompt_sha256(a)


def test_hash_covers_user_message_template():
    from semval.tagging.prompt import load_prompt

    v1 = load_prompt("v1")
    parts = build_prompt(targets(), [], v1)
    changed = v1.model_copy(update={"user_template": v1.user_template.replace("Genre", "Kind")})
    assert prompt_sha256(parts, changed) != prompt_sha256(parts, v1)
