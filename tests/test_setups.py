import logging
from pathlib import Path

import pytest

from semval.cli import main
from semval.config import Effort
from semval.tagging.setups import (
    SETUPS_DIR,
    apply_overrides,
    load_setup,
    parse_options,
    skip_missing_few_shot,
    to_spec,
)
from semval.units import UnitLevel

ROOT = Path(__file__).resolve().parents[1]
_orig_load = load_setup


def test_sonnet_high_setup_matches_decision() -> None:
    s = load_setup("sonnet-high")
    assert (s.kind, s.model, s.effort) == ("claude", "claude-sonnet-5-5", Effort.HIGH)
    assert (s.level, s.unit, s.framework, s.prompt) == ("leaf", "paragraph", "schwartz19", "v1")
    assert s.batch
    assert s.few_shot_files == [
        Path("data/fewshot/touche23.yaml"),
        Path("data/fewshot/local/articles.yaml"),
    ]
    spec = to_spec(s)
    assert spec.few_shot and spec.batch and spec.unit == UnitLevel.PARAGRAPH


def test_lexicon_setup_is_a_baseline_with_its_file() -> None:
    spec = to_spec(load_setup("lexicon"))
    assert spec.is_baseline and spec.model is None and not spec.few_shot
    assert spec.options == {}  # the factory default is the same path; old runs have {}
    from semval.tagging.lexicon import DEFAULT_LEXICON_PATH

    assert DEFAULT_LEXICON_PATH == Path("data/lexicon/basic10_seed.yaml")


def test_lexicon_setup_spec_equals_old_lexicon_manifests() -> None:
    import json

    from semval.tagging.base import RunManifest

    spec = to_spec(apply_overrides(load_setup("lexicon"), unit="paragraph"))
    for path in sorted((ROOT / "data" / "runs").glob("grid-lexicon-basic10-*/manifest.json")):
        old = RunManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))
        assert old.spec == spec, path


def test_unknown_setup_name_lists_known() -> None:
    with pytest.raises(ValueError, match=r"nope.*known: lexicon, sonnet-high"):
        load_setup("nope")


def test_setup_rejects_unknown_field(tmp_path: Path) -> None:
    text = (SETUPS_DIR / "sonnet-high.yaml").read_text(encoding="utf-8")
    (tmp_path / "typo.yaml").write_text(text.replace("effort:", "efort:"), encoding="utf-8")
    with pytest.raises(ValueError, match=r"typo\.yaml") as e:
        load_setup("typo", tmp_path)
    assert "efort" in str(e.value)


def test_overrides_replace_single_fields() -> None:
    base = load_setup("sonnet-high")
    s = apply_overrides(base, model="claude-opus-5-5", effort=None, batch=False)
    assert s.model == "claude-opus-5-5" and not s.batch
    assert s.effort == base.effort and s.few_shot_files == base.few_shot_files
    merged = apply_overrides(load_setup("lexicon"), options={"x": 1})
    assert merged.options == {"x": 1}


def test_no_few_shot_gives_zero_shot_spec() -> None:
    s = apply_overrides(load_setup("sonnet-high"), few_shot_files=[])
    assert s.few_shot_files == [] and not to_spec(s).few_shot


def test_override_not_valid_for_kind(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as e:
        main(["tag", "--sample", "x", "--tagger", "lexicon", "--model", "claude-opus-5-5"])
    assert e.value.code not in (0, None)
    msg = str(e.value)
    assert "tagger lexicon" in msg and "does not take model" in msg
    assert "validation error" not in msg and "pydantic" not in msg


def test_no_few_shot_with_few_shot_file_is_an_error() -> None:
    with pytest.raises(SystemExit, match="--no-few-shot"):
        main(["tag", "--sample", "x", "--no-few-shot", "--few-shot-file", "a.yaml"])


def _setup_with(files: list[Path]):
    return apply_overrides(load_setup("sonnet-high"), few_shot_files=files)


def test_missing_local_fewshot_file_skipped_and_reported(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    here = tmp_path / "here.yaml"
    here.write_text("examples: []\n", encoding="utf-8")
    gone = Path("data/fewshot/local/gone.yaml")
    with caplog.at_level(logging.WARNING):
        kept, skipped = skip_missing_few_shot(_setup_with([here, gone]), "sonnet-high")
    assert kept.few_shot_files == [here] and skipped == [gone]
    assert "gone.yaml" in caplog.text and to_spec(kept).few_shot
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        none_left, skipped = skip_missing_few_shot(_setup_with([gone]), "sonnet-high")
    assert skipped == [gone] and not to_spec(none_left).few_shot
    assert "zero-shot" in caplog.text


def test_missing_committed_fewshot_file_is_an_error_naming_file_and_setup() -> None:
    typo = Path("data/fewshot/touche32.yaml")
    with pytest.raises(ValueError, match=r"touche32\.yaml.*sonnet-high") as e:
        skip_missing_few_shot(_setup_with([typo]), "sonnet-high")
    assert "data/fewshot/local" in str(e.value)


def test_missing_non_local_file_is_an_error_even_beside_a_local_one() -> None:
    files = [Path("data/fewshot/local/a.yaml"), Path("nowhere/b.yaml")]
    with pytest.raises(ValueError, match=r"b\.yaml"):
        skip_missing_few_shot(_setup_with(files), "sonnet-high")


def test_local_prefix_does_not_cover_a_dotdot_escape() -> None:
    sneaky = Path("data/fewshot/local/../touche99.yaml")
    with pytest.raises(ValueError, match="touche99"):
        skip_missing_few_shot(_setup_with([sneaky]), "sonnet-high")


def _install_setup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str, text: str) -> None:
    """Make ``semval tag --tagger NAME`` read ``text`` as that setup (cwd is the repo root)."""
    monkeypatch.chdir(ROOT)
    (tmp_path / f"{name}.yaml").write_text(text, encoding="utf-8")
    monkeypatch.setattr(
        "semval.tagging.setups.load_setup", lambda n, dir=tmp_path: _orig_load(n, dir)
    )


SONNET = (ROOT / "data/taggers/sonnet-high.yaml").read_text(encoding="utf-8")
LOCAL = "data/fewshot/local/articles.yaml"
ABSENT = "data/fewshot/local/absent-for-test.yaml"


def test_cli_missing_committed_file_in_setup_stops(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_setup(monkeypatch, tmp_path, "typo", SONNET.replace("touche23", "touche32"))
    with pytest.raises(SystemExit, match=r"touche32\.yaml.*setup typo"):
        main(["tag", "--sample", "x", "--tagger", "typo", "--dry-run"])


def test_cli_dry_run_shows_skipped_local_file(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    _install_setup(monkeypatch, tmp_path, "gap", SONNET.replace(LOCAL, ABSENT))
    assert main(["tag", "--sample", "x", "--tagger", "gap", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert f"skipped (not found): {ABSENT}" in out
    assert "few-shot files: data/fewshot/touche23.yaml\n" in out
    assert "zero-shot" not in out


def test_cli_dry_run_all_local_missing_says_zero_shot(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    text = SONNET.replace(LOCAL, ABSENT).replace("  - data/fewshot/touche23.yaml\n", "")
    _install_setup(monkeypatch, tmp_path, "localonly", text)
    assert main(["tag", "--sample", "x", "--tagger", "localonly", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert f"skipped (not found): {ABSENT}" in out
    assert "this run would be zero-shot" in out


def test_setup_with_unrequestable_model_is_rejected() -> None:
    s = apply_overrides(load_setup("sonnet-high"), model="claude-opus-4-8")
    with pytest.raises(ValueError, match=r"claude-opus-4-8.*requestable.*claude-haiku-5-5"):
        to_spec(s)


def test_option_values_parse_as_scalars() -> None:
    assert parse_options(["a=1", "b=2.5", "c=true", "d=False", "e=x=y", "f=007x"]) == {
        "a": 1, "b": 2.5, "c": True, "d": False, "e": "x=y", "f": "007x",
    }  # fmt: skip
    with pytest.raises(ValueError, match="KEY=VALUE"):
        parse_options(["novalue"])


def test_cli_dry_run_prints_resolved_spec(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(
        "semval.tagging.claude.make_client", lambda: pytest.fail("a dry run makes no client")
    )
    assert main(["tag", "--sample", "x", "--dry-run", "--effort", "low"]) == 0
    out = capsys.readouterr().out
    assert "claude-sonnet-5-5" in out and '"effort":"low"' in out
    assert "data/fewshot/touche23.yaml" in out


def test_cli_dry_run_lexicon_option(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(ROOT)
    argv = ["tag", "--sample", "x", "--tagger", "lexicon", "--option", "lexicon_file=other.yaml"]
    assert main([*argv, "--unit", "paragraph", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "other.yaml" in out and "zero-shot" in out


@pytest.mark.parametrize(
    ("flag", "value", "known"),
    [
        ("--level", "nope", "known: leaf"),
        ("--framework", "nope", "known: schwartz19"),
        ("--prompt", "nope", "known: v1"),
    ],
)
def test_unknown_level_framework_prompt_name_the_known_ids(
    monkeypatch: pytest.MonkeyPatch, flag: str, value: str, known: str
) -> None:
    monkeypatch.chdir(ROOT)
    with pytest.raises(SystemExit) as e:
        main(["tag", "--sample", "x", "--dry-run", flag, value])
    assert e.value.code not in (0, None)
    assert "nope" in str(e.value) and known in str(e.value)


def test_unknown_kind_in_setup_file_names_the_file(tmp_path: Path) -> None:
    text = (SETUPS_DIR / "lexicon.yaml").read_text(encoding="utf-8")
    (tmp_path / "odd.yaml").write_text(
        text.replace("kind: lexicon", "kind: magic"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match=r"odd\.yaml.*magic.*known: claude, lexicon"):
        load_setup("odd", tmp_path)
