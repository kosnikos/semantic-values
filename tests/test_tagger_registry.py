import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from semval.config import HAIKU_5_5, Effort
from semval.tagging import lexicon, registry
from semval.tagging.base import (
    PromptInfo,
    RawTag,
    RunManifest,
    RunStatus,
    TagBatchResult,
    TaggerSpec,
)
from semval.tagging.ledger import CostLedger
from semval.tagging.registry import TaggerContext, build_tagger, register_tagger
from semval.tagging.runner import run_tagging
from semval.tags import Stance
from semval.units import UnitLevel
from test_runner import setup, tags_of

FIXTURE = Path(__file__).parent / "fixtures" / "runs" / "old_lexicon_manifest.json"
RUNS = Path("data/runs")
ALL_FIELDS = {"model", "effort", "unit", "few_shot", "batch", "options"}


@pytest.fixture
def scratch_registry(monkeypatch):
    """Registrations made in a test vanish after it."""
    registry.registered_kinds()  # built-ins in first, so the copy has them
    monkeypatch.setattr(registry, "_KINDS", dict(registry._KINDS))


class EchoTagger:
    """Tags every segment with one fixed value."""

    def __init__(self, spec: TaggerSpec):
        self.spec = spec

    def prompt_info(self, targets) -> PromptInfo:
        return PromptInfo(prompt_sha256="e" * 64)

    def tag(self, segments, texts, targets, documents) -> TagBatchResult:
        value = str(self.spec.options["value"])
        return TagBatchResult(
            tags_by_segment={
                s.id: [RawTag(value_id=value, stance=Stance.MENTION)] for s in segments
            }
        )


def test_builtins_registered_on_import():
    assert {"claude", "lexicon"} <= set(registry.registered_kinds())


def test_unknown_kind_lists_registered():
    with pytest.raises(ValidationError, match=r"unknown tagger kind 'nope'.*claude.*lexicon"):
        TaggerSpec(kind="nope", framework_id="toy", level_id="leaf")


def test_fake_kind_runs_end_to_end(tmp_path, scratch_registry):
    register_tagger(
        "echo", lambda spec, ctx: EchoTagger(spec), needs=frozenset({"options"}),
        allows=frozenset({"unit"}),
    )  # fmt: skip
    paths = setup(tmp_path)
    spec = TaggerSpec(kind="echo", framework_id="toy", level_id="leaf",
                      unit=UnitLevel.ARTICLE, options={"value": "alpha"})  # fmt: skip
    ledger = CostLedger(tmp_path / "ledger.jsonl")
    m = run_tagging(spec, "toy-sample", run_id="e1", ledger=ledger, paths=paths)
    assert m.status == RunStatus.DONE and len(m.segments_done) == 3
    on_disk = RunManifest.model_validate_json((paths.runs_dir / "e1" / "manifest.json").read_text())
    assert on_disk.spec.kind == "echo" and on_disk.spec.options == {"value": "alpha"}
    assert {t.value_id for t in tags_of(paths.runs_dir / "e1")} == {"alpha"}


def test_claude_spec_missing_effort_rejected():
    with pytest.raises(ValidationError, match="needs effort"):
        TaggerSpec(kind="claude", model=HAIKU_5_5, framework_id="toy", level_id="leaf",
                   unit=UnitLevel.ARTICLE)  # fmt: skip


def test_lexicon_rejects_model():
    with pytest.raises(ValidationError, match="does not take model"):
        TaggerSpec(kind="lexicon", model=HAIKU_5_5, framework_id="toy", level_id="leaf")


def test_claude_rejects_options():
    with pytest.raises(ValidationError, match="does not take options"):
        TaggerSpec(kind="claude", model=HAIKU_5_5, effort=Effort.LOW, framework_id="toy",
                   level_id="leaf", unit=UnitLevel.ARTICLE, options={"x": 1})  # fmt: skip


def test_double_registration_rejected(scratch_registry):
    with pytest.raises(ValueError, match="already registered"):
        register_tagger("lexicon", lambda spec, ctx: None, allows=frozenset())


def test_register_rejects_unknown_field_names(scratch_registry):
    with pytest.raises(ValueError, match="framework_id"):
        register_tagger("odd", lambda spec, ctx: None, allows=frozenset({"framework_id"}))


def test_is_baseline_from_registry(scratch_registry):
    lex = TaggerSpec(kind="lexicon", framework_id="toy", level_id="leaf")
    claude = TaggerSpec(kind="claude", model=HAIKU_5_5, effort=Effort.LOW, framework_id="toy",
                        level_id="leaf", unit=UnitLevel.ARTICLE)  # fmt: skip
    assert lex.is_baseline and not claude.is_baseline


def _lex_file(tmp_path: Path) -> Path:
    p = tmp_path / "lex.yaml"
    p.write_text("framework_id: toy\nlevel_id: leaf\ntargets:\n  alpha: [alpha]\n  beta: [beta]\n",
                 encoding="utf-8")  # fmt: skip
    return p


def test_lexicon_factory_reads_option_and_default(tmp_path, monkeypatch):
    lex = _lex_file(tmp_path)
    spec = TaggerSpec(kind="lexicon", framework_id="toy", level_id="leaf",
                      options={"lexicon_file": str(lex)})  # fmt: skip
    tagger = build_tagger(spec)
    assert tagger.spec == spec and tagger.stems == {"alpha": ["alpha"], "beta": ["beta"]}
    monkeypatch.setattr(lexicon, "DEFAULT_LEXICON_PATH", lex)
    plain = TaggerSpec(kind="lexicon", framework_id="toy", level_id="leaf")
    assert build_tagger(plain, TaggerContext()).spec == plain
    with pytest.raises(ValueError, match="spec for toy/other"):
        build_tagger(plain.model_copy(update={"level_id": "other"}))
    with pytest.raises(ValueError, match="bogus"):
        build_tagger(TaggerSpec(kind="lexicon", framework_id="toy", level_id="leaf",
                                options={"bogus": 1}))  # fmt: skip


def test_old_manifest_loads_and_defaults():
    m = RunManifest.model_validate_json(FIXTURE.read_text(encoding="utf-8"))
    assert m.spec.prompt_id == "v1" and m.spec.options == {}
    if not RUNS.is_dir():
        pytest.skip("no data/runs")
    found = sorted(RUNS.glob("*/manifest.json"))
    assert found
    for path in found:
        m = RunManifest.model_validate_json(path.read_text(encoding="utf-8"))
        assert m.spec.prompt_id == "v1" and m.spec.options == {}, path


def test_old_lexicon_run_prompt_hash_unchanged():
    """The default word list still hashes to what the stored lexicon runs recorded."""
    paths = sorted(RUNS.glob("*/manifest.json")) if RUNS.is_dir() else []
    lex_runs = [
        m for p in paths if (m := RunManifest.model_validate_json(p.read_text())).spec.is_baseline
    ]
    if not lex_runs:
        pytest.skip("no stored lexicon runs")
    from semval.values import FRAMEWORK_DIR, load_framework

    for m in lex_runs:
        tagger = build_tagger(m.spec.model_copy(update={"unit": None}))
        fw = load_framework(FRAMEWORK_DIR / f"{m.spec.framework_id}.yaml",
                            local_dir=FRAMEWORK_DIR / "local")  # fmt: skip
        assert tagger.prompt_info(fw.target_set(m.spec.level_id)).prompt_sha256 == m.prompt_sha256


def test_old_format_manifest_resumes_with_equivalent_spec(tmp_path, monkeypatch):
    paths = setup(tmp_path)
    run_dir = paths.runs_dir / "old-lex"
    run_dir.mkdir(parents=True)
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert "options" not in raw["spec"] and "prompt_id" not in raw["spec"]
    (run_dir / "manifest.json").write_text(json.dumps(raw), encoding="utf-8")
    monkeypatch.setattr(lexicon, "DEFAULT_LEXICON_PATH", _lex_file(tmp_path))
    spec = TaggerSpec(kind="lexicon", framework_id="toy", level_id="leaf")
    m = run_tagging(spec, "toy-sample", run_id="old-lex", unit=UnitLevel.SENTENCE,
                    ledger=CostLedger(tmp_path / "ledger.jsonl"), paths=paths)  # fmt: skip
    assert m.status == RunStatus.DONE and m.started == RunManifest.model_validate(raw).started
    assert {t.value_id for t in tags_of(run_dir)} == {"alpha", "beta"}


def test_check_spec_fields_are_spec_fields():
    assert ALL_FIELDS <= set(TaggerSpec.model_fields)
    assert registry.SPEC_FIELDS == ALL_FIELDS
