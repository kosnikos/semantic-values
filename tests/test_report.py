import datetime
import hashlib
from pathlib import Path

import pytest
import yaml

from conftest import toy_values, write_framework
from semval.cli import main
from semval.config import SONNET_5_5, Effort
from semval.datasets.touche23_samples import EL_PREFIX, EN_PREFIX
from semval.evaluation.report import EvalSetup, build_results, render_report, write_report
from semval.review.labels import LabelRecord, Verdict
from semval.sampling.sample import SampleManifest, doc_text_path, write_manifest
from semval.tagging.base import RunManifest, RunStatus, TaggerKind, TaggerSpec
from semval.tagging.runfiles import RunPaths
from semval.tags import Stance, ValueTag
from semval.units import Document
from semval.values import load_framework

LEVELS = [
    {
        "id": "coarse",
        "value_targets": ["group_a", "group_b"],
        "map": {"alpha": "group_a", "beta": "group_b"},
    }
]
EN_SAMPLE, EL_SAMPLE, OWNER_SAMPLE = "en-sample", "el-sample", "owner-sample"
T0 = datetime.datetime(2026, 11, 19, 10, 0, 0)


def make_paths(tmp_path: Path) -> RunPaths:
    paths = RunPaths(
        samples_dir=tmp_path / "samples",
        raw_dir=tmp_path / "raw",
        framework_dir=tmp_path / "fw",
        runs_dir=tmp_path / "runs",
    )
    paths.framework_dir.mkdir()
    write_framework(paths.framework_dir, toy_values(), levels=LEVELS)
    return paths


def make_sample(paths: RunPaths, name: str, doc_ids: list[str], language: str) -> None:
    docs = []
    for doc_id in doc_ids:
        data = f"Text of {doc_id}.".encode()
        p = doc_text_path(paths.raw_dir, doc_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        docs.append(
            Document(
                id=doc_id, source_id=doc_id.split(":")[0], country="ZZ", language=language,
                genre="x", text_sha256=hashlib.sha256(data).hexdigest(),
            )
        )  # fmt: skip
    write_manifest(SampleManifest(name=name, stats={}, documents=docs), paths.samples_dir)


def make_run(
    paths: RunPaths,
    run_id: str,
    sample: str,
    tags: dict[str, list[tuple[str, Stance]]],  # doc -> [(value, stance)] on paragraph p0
    *,
    spec: TaggerSpec,
    cost: float = 0.0,
    seconds: int = 10,
    few_shot_files: list[str] | None = None,
    status: RunStatus = RunStatus.DONE,
) -> None:
    run_dir = paths.runs_dir / run_id
    run_dir.mkdir(parents=True)
    segs = [f"{d}:p0" for d in tags]
    m = RunManifest(
        run_id=run_id, spec=spec, input_sample=sample, prompt_sha256="0" * 64,
        status=status, segments_done=segs, cost_usd=cost, started=T0,
        finished=T0 + datetime.timedelta(seconds=seconds), few_shot_files=few_shot_files or [],
    )  # fmt: skip
    (run_dir / "manifest.json").write_text(m.model_dump_json(), encoding="utf-8")
    lines = [
        ValueTag(segment_id=f"{d}:p0", value_id=v, stance=s, run_id=run_id).model_dump_json()
        for d, ts in tags.items()
        for v, s in ts
    ]
    (run_dir / "tags.jsonl").write_text("\n".join(lines), encoding="utf-8")


def claude(**kw) -> TaggerSpec:
    base = {
        "kind": TaggerKind.CLAUDE, "model": SONNET_5_5, "effort": Effort.LOW,
        "framework_id": "toy", "level_id": "leaf", "unit": "paragraph",
    }  # fmt: skip
    base.update(kw)
    return TaggerSpec(**base)


GOLD = {
    f"{EN_PREFIX}:i1": {"group_a"},
    f"{EN_PREFIX}:i2": {"group_b"},
    f"{EL_PREFIX}:i1": {"group_a"},
}
OWNER_DOCS = ["src-gb:o1", "src-gb:o2"]


def label(doc, value, verdict, model=None, corrected=None):
    return LabelRecord(
        labeller="owner", document_id=doc, value_id=value, level_id="leaf",
        model_stance=model, verdict=verdict, corrected_stance=corrected,
    )  # fmt: skip


@pytest.fixture
def world(tmp_path):
    paths = make_paths(tmp_path)
    en_docs = [f"{EN_PREFIX}:i1", f"{EN_PREFIX}:i2"]
    make_sample(paths, EN_SAMPLE, en_docs, "en")
    make_sample(paths, EL_SAMPLE, [f"{EL_PREFIX}:i1"], "el")
    make_sample(paths, OWNER_SAMPLE, OWNER_DOCS, "en")
    en, el, ow = en_docs, f"{EL_PREFIX}:i1", OWNER_DOCS
    make_run(paths, "a-en", EN_SAMPLE, {en[0]: [("alpha", Stance.ENDORSE)],
                                         en[1]: [("beta", Stance.MENTION)]}, spec=claude())  # fmt: skip
    make_run(paths, "a-el", EL_SAMPLE, {el: [("beta", Stance.ENDORSE)]}, spec=claude())
    make_run(paths, "a-ow", OWNER_SAMPLE,
             {ow[0]: [("alpha", Stance.ENDORSE)], ow[1]: [("beta", Stance.MENTION)]},
             spec=claude(), cost=0.04, seconds=10)  # fmt: skip
    make_run(paths, "lex-en", EN_SAMPLE, {en[0]: [("alpha", Stance.MENTION)], en[1]: []},
             spec=TaggerSpec(kind=TaggerKind.LEXICON, framework_id="toy", level_id="leaf",
                             unit="paragraph"))  # fmt: skip
    labels = [
        label(ow[0], "alpha", Verdict.CORRECT, Stance.ENDORSE),
        label(ow[1], "alpha", Verdict.ADDED, corrected=Stance.REJECT),
    ]
    setup = EvalSetup(
        framework=load_framework(paths.framework_dir / "toy.yaml", local_dir=None),
        paths=paths, labels=labels, en_sample=EN_SAMPLE, el_sample=EL_SAMPLE,
        owner_sample=OWNER_SAMPLE, scoring_level="coarse",
        gold=lambda sample, level: {d.id: GOLD[d.id] for d in sample.documents},
    )  # fmt: skip
    return setup, ["a-en", "a-el", "a-ow", "lex-en"]


def by_label(results, needle):
    return next(r for r in results if needle in r.key.label)


def test_build_results_groups_runs_and_scores(world):
    setup, run_ids = world
    results = build_results(run_ids, setup)
    assert len(results) == 2
    a, lex = by_label(results, "sonnet"), by_label(results, "lexicon")
    # EN: group_a found, group_b only mentioned -> strict macro (1 + 0) / 2
    assert a.en.macro_f1 == pytest.approx(0.5) and a.en.macro_f1_mention == pytest.approx(1.0)
    # EL: wrong value; group_b has no gold on the proxy item so it is not averaged: F1(group_a)=0
    assert a.el.macro_f1 == 0.0
    # EN on the parallel item i1 only: group_a right, group_b unsupported -> 1.0; gap +1.0
    assert a.en_parallel_f1 == pytest.approx(1.0) and a.gap == pytest.approx(1.0)
    assert a.en.leaf_macro_f1 is None or a.en.leaf_macro_f1 >= 0
    # owner: o1 agree; o2 beta mention predicted at group_b, owner has alpha reject at group_a
    s = a.stance
    assert (s.co_present, s.agree, s.missed, s.unjudged, s.spurious) == (1, 1, 1, 1, 0)
    assert a.owner_docs == 2 and a.cost_per_1k == pytest.approx(20.0)
    assert a.latency == "5.00 s/segment"
    # the lexicon run only has an English run: other cells are empty
    assert lex.el is None and lex.stance is None and lex.cost_per_1k is None and lex.gap is None


def test_batch_runs_show_batch_not_latency(world, tmp_path):
    setup, _ = world
    ow = OWNER_DOCS
    make_run(setup.paths, "b-ow", OWNER_SAMPLE, {ow[0]: [("alpha", Stance.ENDORSE)]},
             spec=claude(effort=Effort.HIGH, batch=True), cost=0.01)  # fmt: skip
    (b,) = build_results(["b-ow"], setup)
    assert b.latency == "batch"


def test_few_shot_source_documents_are_excluded_from_owner_scoring(world, tmp_path):
    setup, _ = world
    fs = tmp_path / "fs.yaml"
    fs.write_text(yaml.safe_dump({"source_documents": [OWNER_DOCS[0]], "examples": []}))
    make_run(setup.paths, "f-ow", OWNER_SAMPLE,
             {OWNER_DOCS[0]: [("alpha", Stance.ENDORSE)], OWNER_DOCS[1]: [("beta", Stance.MENTION)]},
             spec=claude(few_shot=True), cost=0.04, few_shot_files=[str(fs)])  # fmt: skip
    (f,) = build_results(["f-ow"], setup)
    assert f.owner_docs == 1  # only o2 is scored
    assert f.stance.co_present == 0 and f.stance.missed == 1


def test_duplicate_runs_for_one_input_are_refused(world):
    setup, run_ids = world
    make_run(setup.paths, "a-en2", EN_SAMPLE, {f"{EN_PREFIX}:i1": []}, spec=claude())
    with pytest.raises(ValueError, match="two runs"):
        build_results([*run_ids, "a-en2"], setup)


def test_unknown_tagging_level_refused(world):
    setup, _ = world
    make_run(setup.paths, "x-en", EN_SAMPLE, {f"{EN_PREFIX}:i1": []}, spec=claude(level_id="other"))
    with pytest.raises(ValueError, match="other"):
        build_results(["x-en"], setup)


def test_report_contains_caveats_and_rule(world, tmp_path):
    setup, run_ids = world
    out = tmp_path / "out" / "tagging-evaluation.md"
    write_report(build_results(run_ids, setup), out, scoring_level="coarse")
    md = out.read_text(encoding="utf-8")
    assert "0.02" in md and "gate" in md.lower() and "cheapest" in md
    assert "not news" in md and "proxy" in md and "small" in md.lower()
    assert "Draft" in md and "the owner decides" in md
    assert "sonnet" in md and "lexicon" in md and "—" in md
    assert "20.00" in md and "5.00 s/segment" in md


def test_render_reports_counts_and_is_text_free(world):
    setup, run_ids = world
    md = render_report(build_results(run_ids, setup), scoring_level="coarse")
    assert "1/1" in md  # agreement as count, not only a rate
    assert "Text of" not in md


def test_cli_evaluate(world, tmp_path, monkeypatch):
    setup, run_ids = world
    # labels file in the real layout, framework file where the CLI looks for it
    lp = tmp_path / "labels" / "owner" / "labels.jsonl"
    lp.parent.mkdir(parents=True)
    lp.write_text("\n".join(r.model_dump_json() for r in setup.labels), encoding="utf-8")
    out = tmp_path / "report.md"
    args = ["evaluate"]
    for r in run_ids:
        args += ["--run", r]
    args += [
        "--runs-dir", str(setup.paths.runs_dir), "--samples-dir", str(setup.paths.samples_dir),
        "--raw-dir", str(setup.paths.raw_dir), "--labels-dir", str(tmp_path / "labels"),
        "--framework-dir", str(setup.paths.framework_dir), "--scoring-level", "coarse",
        "--en-sample", EN_SAMPLE, "--el-sample", EL_SAMPLE, "--owner-sample", OWNER_SAMPLE,
        "--out", str(out),
    ]  # fmt: skip
    monkeypatch.setattr("semval.cli._touche_gold_for_evaluate", lambda fw, data_dir: (
        lambda sample, level: {d.id: GOLD[d.id] for d in sample.documents}))  # fmt: skip
    assert main(args) == 0
    assert "sonnet" in out.read_text(encoding="utf-8")


def test_stopped_run_and_run_missing_a_document_are_flagged_and_not_ranked(world):
    setup, run_ids = world
    en = [f"{EN_PREFIX}:i1", f"{EN_PREFIX}:i2"]
    # same config as a-en/a-el but another effort: EN stopped at budget, EL complete
    make_run(setup.paths, "s-en", EN_SAMPLE, {en[0]: [("alpha", Stance.ENDORSE)],
             en[1]: [("beta", Stance.ENDORSE)]}, spec=claude(effort=Effort.HIGH),
             status=RunStatus.STOPPED_BUDGET)  # fmt: skip
    make_run(setup.paths, "s-el", EL_SAMPLE, {f"{EL_PREFIX}:i1": [("alpha", Stance.ENDORSE)]},
             spec=claude(effort=Effort.HIGH))  # fmt: skip
    # owner run that never reached the second article
    make_run(setup.paths, "s-ow", OWNER_SAMPLE, {OWNER_DOCS[0]: [("alpha", Stance.ENDORSE)]},
             spec=claude(effort=Effort.HIGH), cost=0.02)  # fmt: skip
    results = build_results([*run_ids, "s-en", "s-el", "s-ow"], setup)
    s = by_label(results, "high")
    assert s.en is None and s.en_partial == "partial 2/2 (stopped_budget)"
    assert s.owner_partial == "partial 1/2" and s.stance is None and s.cost_per_1k is None
    assert s.rank_score is None
    md = render_report(results, scoring_level="coarse")
    assert "partial 2/2 (stopped_budget)" in md and "partial 1/2" in md
    from semval.evaluation.metrics import recommend

    rec = recommend(results)
    assert rec.chosen is not None and "high" not in rec.chosen.label


def test_zero_tag_documents_count_as_negatives_over_the_whole_sample(world):
    setup, _ = world
    en = [f"{EN_PREFIX}:i1", f"{EN_PREFIX}:i2"]
    make_run(setup.paths, "z-en", EN_SAMPLE, {en[0]: [("alpha", Stance.ENDORSE)], en[1]: []},
             spec=claude(effort=Effort.HIGH))  # fmt: skip
    (z,) = build_results(["z-en"], setup)
    # i2 has gold group_b and no tags: a miss (F1 0), not a dropped document
    assert z.en.n_docs == 2 and z.en.macro_f1 == pytest.approx(0.5)


def test_report_shows_n_el_mention_and_flags(world):
    setup, run_ids = world
    import dataclasses

    only_a = dataclasses.replace(
        setup, gold=lambda sample, level: {d.id: {"group_a"} for d in sample.documents}
    )
    md = render_report(build_results(run_ids, only_a), scoring_level="coarse")
    assert "Macro-F1 EL +mention" in md and "n EN" in md and "n owner" in md
    assert "meaningful figure" in md  # lexicon baseline note
    assert "marked `no gold`" in md and "no gold |" in md
    assert "the best among the configurations the gate kept" in md
