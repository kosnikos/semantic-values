from pathlib import Path

import pytest
import yaml

from fake_anthropic import FakeClient, message
from semval.config import SONNET_5_5, Effort
from semval.tagging.base import RunManifest, TaggerKind, TaggerSpec
from semval.tagging.claude import ClaudeTagger
from semval.tagging.fewshot import fewshot_at_level, load_fewshot_files
from semval.tagging.prompt import (
    MAX_QUOTES,
    build_prompt,
    load_prompt,
    prompt_sha256,
    user_message,
)
from semval.units import DocumentMeta, Segment, UnitLevel
from semval.values import FRAMEWORK_DIR, load_framework

ROOT = Path(__file__).resolve().parents[1]
FEWSHOT = ROOT / "data" / "fewshot" / "touche23.yaml"
RUNS = ROOT / "data" / "runs"

# Computed with the constants-based prompt.py, before it was moved to data/prompts/v1.yaml:
#   framework schwartz19, prompt_sha256(build_prompt(target_set(level), examples)), examples
#   = fewshot_at_level(load_fewshot(touche23.yaml), framework, level) or [].
V1_HASHES = {
    ("leaf", False): "5022d5abe90890432aaabf0db5542721c0503abf8e15e024e448c825dfe79229",
    ("leaf", True): "f7d65fed952eef1754e4c7bfd45d8a16b73b643051f912c2dfcb75c374af576d",
    ("basic10", False): "9cf10e73a9e7d5ded0b4dba14fb1579eb6a33618b8d11476e24a708c50b127e5",
    ("basic10", True): "5a9e47b10462fb521d7c562b2547fd0c9c4836d591727e77b243c61bbd9017d2",
}

OLD_INSTRUCTIONS = f"""\
You tag newspaper opinion texts with human values.

For each value listed below that the text engages with, report the author's stance:
- endorse: the author promotes or defends the value. This includes lamenting that it is \
threatened or neglected.
- reject: the author opposes or dismisses the value.
- mention: the value is discussed without a clear authorial stance.

The stance is the author's own. A view the author only reports or quotes is a mention, \
unless the author takes it up.

Tag only values the text actually engages with. A text may engage with none; then return \
an empty "tags" list.

For each tag give 1 to {MAX_QUOTES} quotes that show the stance. Every quote must be copied \
verbatim from the text: an exact substring, in the text's own language, not translated, \
not shortened with ellipses. Keep quotes short (a clause or a sentence).

Give each tag a confidence between 0 and 1.

The value definitions are in English; the texts may be in any language."""
OLD_USER_TEMPLATE = "Language: {language}\nGenre: {genre}\n\n<text>\n{text}\n</text>"


def _framework():
    return load_framework(FRAMEWORK_DIR / "schwartz19.yaml")


@pytest.mark.parametrize(("level", "few_shot"), list(V1_HASHES))
def test_v1_prompt_hash_unchanged(level, few_shot):
    fw = _framework()
    examples = fewshot_at_level(load_fewshot_files([FEWSHOT]), fw, level) if few_shot else []
    parts = build_prompt(fw.target_set(level), examples)
    assert prompt_sha256(parts) == V1_HASHES[(level, few_shot)]


def test_v1_text_equals_previous_constants():
    v1 = load_prompt("v1")
    assert v1.rendered_instructions() == OLD_INSTRUCTIONS
    assert v1.user_template == OLD_USER_TEMPLATE


def test_unknown_prompt_id_lists_known():
    with pytest.raises(ValueError, match="nope") as e:
        load_prompt("nope")
    assert "v1" in str(e.value)


def test_prompt_id_must_match_file_name(tmp_path):
    (tmp_path / "a.yaml").write_text("id: b\ninstructions: x\nuser_template: y\n")
    with pytest.raises(ValueError, match="does not match"):
        load_prompt("a", tmp_path)


def test_spec_prompt_id_defaults_to_v1():
    spec = TaggerSpec(
        kind=TaggerKind.CLAUDE, model=SONNET_5_5, effort=Effort.LOW, framework_id="toy",
        level_id="leaf", unit=UnitLevel.ARTICLE,
    )  # fmt: skip
    assert spec.prompt_id == "v1"


def test_new_prompt_file_changes_hash_and_is_used(tmp_path, monkeypatch):
    from semval.tagging import claude

    v1 = load_prompt("v1")
    (tmp_path / "v2.yaml").write_text(
        yaml.safe_dump({
            "id": "v2",
            "instructions": "Tag values. Up to {max_quotes} quotes.",
            "user_template": "Doc ({language}): {text}",
        })
    )  # fmt: skip
    v2 = load_prompt("v2", tmp_path)
    fw = _framework()
    targets = fw.target_set("basic10")
    assert prompt_sha256(build_prompt(targets, [], v2), v2) != prompt_sha256(
        build_prompt(targets, [], v1), v1
    )

    monkeypatch.setattr(claude, "load_prompt", lambda pid: load_prompt(pid, tmp_path))
    spec = TaggerSpec(
        kind=TaggerKind.CLAUDE, model=SONNET_5_5, effort=Effort.LOW, framework_id="schwartz19",
        level_id="basic10", unit=UnitLevel.ARTICLE, prompt_id="v2",
    )  # fmt: skip
    client = FakeClient([message([])])
    tagger = ClaudeTagger(spec, client)
    text = "Some text."
    seg = Segment(id="d:a", document_id="d", level=UnitLevel.ARTICLE, start=0, end=len(text))
    docs = {"d": DocumentMeta(language="en", genre="opinion")}
    tagger.tag([seg], {"d:a": text}, targets, docs)
    (req,) = client.sync_calls
    assert req["system"][0]["text"].startswith("Tag values. Up to 3 quotes.")
    assert req["messages"][0]["content"] == "Doc (en): Some text."
    assert user_message(text, docs["d"], v2) == "Doc (en): Some text."


def test_grid_manifest_hashes_unchanged():
    """Rebuild each recorded grid run's prompt as the runner did; it must equal the stored
    hash, so existing runs still resume."""
    manifests = sorted(RUNS.glob("grid-*/manifest.json")) if RUNS.is_dir() else []
    if not manifests:
        pytest.skip("no data/runs/grid-* manifests")
    checked = 0
    for path in manifests:
        m = RunManifest.model_validate_json(path.read_text(encoding="utf-8"))
        if m.spec.kind != TaggerKind.CLAUDE:
            continue
        files = [ROOT / f for f in m.few_shot_files]
        if any(not f.is_file() for f in files):
            continue
        fw = _framework() if m.spec.framework_id == "schwartz19" else None
        assert fw is not None, m.spec.framework_id
        examples = fewshot_at_level(load_fewshot_files(files), fw, m.spec.level_id) if files else []
        parts = build_prompt(fw.target_set(m.spec.level_id), examples)
        assert prompt_sha256(parts) == m.prompt_sha256, path.parent.name
        checked += 1
    if not checked:
        pytest.skip("no runs with their few-shot files on disk")
