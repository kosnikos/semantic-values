import logging
from pathlib import Path

import pytest
import yaml

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
    assert spec.options == {"lexicon_file": "data/lexicon/basic10_seed.yaml"}


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
    assert merged.options == {"lexicon_file": "data/lexicon/basic10_seed.yaml", "x": 1}


def test_no_few_shot_gives_zero_shot_spec() -> None:
    s = apply_overrides(load_setup("sonnet-high"), few_shot_files=[])
    assert s.few_shot_files == [] and not to_spec(s).few_shot


def test_override_not_valid_for_kind(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as e:
        main(["tag", "--sample", "x", "--tagger", "lexicon", "--model", "claude-opus-5-5"])
    assert e.value.code not in (0, None)
    assert "does not take model" in str(e.value)


def test_no_few_shot_with_few_shot_file_is_an_error() -> None:
    with pytest.raises(SystemExit, match="--no-few-shot"):
        main(["tag", "--sample", "x", "--no-few-shot", "--few-shot-file", "a.yaml"])


def test_missing_local_fewshot_file_skipped_and_recorded(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    here = tmp_path / "here.yaml"
    here.write_text("examples: []\n", encoding="utf-8")
    gone = tmp_path / "gone.yaml"
    s = apply_overrides(load_setup("sonnet-high"), few_shot_files=[here, gone])
    with caplog.at_level(logging.WARNING):
        kept = skip_missing_few_shot(s)
    assert kept.few_shot_files == [here] and "gone.yaml" in caplog.text
    assert to_spec(kept).few_shot
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        none_left = skip_missing_few_shot(apply_overrides(s, few_shot_files=[gone]))
    assert not to_spec(none_left).few_shot and "zero-shot" in caplog.text


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
    assert yaml.safe_load("a: 1")  # yaml import used for the typo test above
