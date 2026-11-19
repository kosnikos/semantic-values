import hashlib
import json
import re
from datetime import date
from pathlib import Path

import pytest

from conftest import toy_values, write_framework
from fake_anthropic import FakeClient, message, usage
from semval.config import Effort, ModelId
from semval.sampling.sample import SampleManifest, doc_text_path, write_manifest
from semval.tagging.base import RunManifest, RunStatus, TaggerKind, TaggerSpec
from semval.tagging.claude import ClaudeTagger
from semval.tagging.ledger import CostLedger
from semval.tagging.lexicon import LexiconTagger
from semval.tagging.runner import RunPaths, make_run_id, run_tagging
from semval.tags import ValueTag
from semval.units import Document, UnitLevel

TEXTS = {
    "src-gb:000000000001": "Alpha must be defended. It is under threat.",
    "src-gb:000000000002": "Beta is overrated, the author says.",
    "src-gr:000000000003": "Κείμενο χωρίς αξίες.",
}
QUOTES = {
    "src-gb:000000000001": "Alpha must be defended",
    "src-gb:000000000002": "Beta is overrated",
}


def setup(tmp_path: Path) -> RunPaths:
    paths = RunPaths(
        samples_dir=tmp_path / "samples",
        raw_dir=tmp_path / "raw",
        framework_dir=tmp_path / "fw",
        runs_dir=tmp_path / "runs",
    )
    paths.framework_dir.mkdir()
    write_framework(paths.framework_dir, toy_values())
    docs = []
    for doc_id, text in TEXTS.items():
        p = doc_text_path(paths.raw_dir, doc_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = text.encode("utf-8")
        p.write_bytes(data)
        gr = doc_id.startswith("src-gr")
        docs.append(
            Document(
                id=doc_id,
                source_id=doc_id.split(":")[0],
                country="GR" if gr else "GB",
                language="el" if gr else "en",
                genre="opinion",
                text_sha256=hashlib.sha256(data).hexdigest(),
            )
        )
    manifest = SampleManifest(
        name="toy-sample", since=date(2026, 1, 1), until=date(2026, 2, 1), per_country=2,
        requests=0, stats={}, documents=docs,
    )  # fmt: skip
    write_manifest(manifest, paths.samples_dir)
    return paths


def spec(**kw) -> TaggerSpec:
    base = {
        "kind": TaggerKind.CLAUDE, "model": ModelId.SONNET_5_5, "effort": Effort.MEDIUM,
        "framework_id": "toy", "level_id": "leaf", "unit": UnitLevel.ARTICLE,
    }  # fmt: skip
    base.update(kw)
    return TaggerSpec(**base)


def answer(kw: dict):
    """Fake model: tags alpha or beta when the text has it, quoting it verbatim."""
    user = kw["messages"][0]["content"]
    tags = [
        {"value_id": vid, "stance": stance, "quotes": [q], "confidence": 0.8}
        for doc, q in QUOTES.items()
        if q in user
        for vid, stance in [("alpha", "endorse") if "Alpha" in q else ("beta", "reject")]
    ]
    return message(tags)


def tags_of(run_dir: Path) -> list[ValueTag]:
    lines = (run_dir / "tags.jsonl").read_text(encoding="utf-8").splitlines()
    return [ValueTag.model_validate_json(line) for line in lines if line.strip()]


def test_run_id_format():
    rid = make_run_id(spec(), now=__import__("datetime").datetime(2026, 11, 19, 8, 30, 5))
    assert rid == "20261119T083005-claude-claude-sonnet-5-5-medium-leaf-article-fs0"
    lex = TaggerSpec(kind=TaggerKind.LEXICON, framework_id="toy", level_id="leaf")
    rid = make_run_id(lex, unit=UnitLevel.SENTENCE)
    assert re.fullmatch(r"\d{8}T\d{6}-lexicon-none-none-leaf-sentence-fs0", rid)


def test_run_writes_manifest_and_tags(tmp_path):
    paths = setup(tmp_path)
    client = FakeClient([answer] * 3)
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    tagger = ClaudeTagger(spec(), client)
    m = run_tagging(spec(), "toy-sample", run_id="r1", tagger=tagger, ledger=ledger, paths=paths)
    assert m.status == RunStatus.DONE and len(m.segments_done) == 3
    on_disk = RunManifest.model_validate_json((paths.runs_dir / "r1" / "manifest.json").read_text())
    assert on_disk == m
    assert len(m.prompt_sha256) == 64 and m.definition_wording == {"fallback": 2}
    assert m.cost_usd == pytest.approx(ledger.total()) and m.cost_usd > 0
    assert m.usage_totals.input_tokens == 3000
    tags = tags_of(paths.runs_dir / "r1")
    assert {(t.segment_id, t.value_id, t.stance.value) for t in tags} == {
        ("src-gb:000000000001:a", "alpha", "endorse"),
        ("src-gb:000000000002:a", "beta", "reject"),
    }
    for t in tags:
        text = TEXTS[t.segment_id.rsplit(":", 1)[0]]
        assert not t.evidence_unresolved and t.run_id == "r1"
        assert text[t.evidence[0].start : t.evidence[0].end] in QUOTES.values()


def test_tags_jsonl_has_no_text(tmp_path):
    paths = setup(tmp_path)
    tagger = ClaudeTagger(spec(), FakeClient([answer] * 3))
    ledger = CostLedger(tmp_path / "ledger.jsonl")
    run_tagging(spec(), "toy-sample", run_id="r1", tagger=tagger, ledger=ledger, paths=paths)
    run_dir = paths.runs_dir / "r1"
    raw = (run_dir / "tags.jsonl").read_text(encoding="utf-8")
    assert raw.strip()
    for line in raw.splitlines():
        assert set(json.loads(line)) <= set(ValueTag.model_fields)
    for f in run_dir.iterdir():
        content = f.read_text(encoding="utf-8")
        for q in QUOTES.values():
            assert q not in content
        for text in TEXTS.values():
            assert text[:15] not in content


def test_ledger_refuses_over_cap(tmp_path):
    paths = setup(tmp_path)
    client = FakeClient([answer] * 3)
    # an estimate is 1000 in + 600 out = $0.008; a call records 1000 in + 200 out = $0.004
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=0.010)
    tagger = ClaudeTagger(spec(), client)
    m = run_tagging(spec(), "toy-sample", run_id="r1", tagger=tagger, ledger=ledger, paths=paths)
    assert m.status == RunStatus.STOPPED_BUDGET
    assert len(client.sync_calls) == 1 and len(m.segments_done) == 1
    assert ledger.total() <= 0.010
    saved = RunManifest.model_validate_json((paths.runs_dir / "r1" / "manifest.json").read_text())
    assert saved.status == RunStatus.STOPPED_BUDGET


def test_budget_exceeded_on_record_stops_cleanly(tmp_path):
    paths = setup(tmp_path)
    big = message([], u=usage(inp=10_000_000, out=0))  # $20 at Sonnet prices
    client = FakeClient([big, answer, answer])
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=5.0)
    tagger = ClaudeTagger(spec(), client)
    m = run_tagging(spec(), "toy-sample", run_id="r1", tagger=tagger, ledger=ledger, paths=paths)
    assert m.status == RunStatus.STOPPED_BUDGET and len(client.sync_calls) == 1
    assert m.cost_usd == pytest.approx(20.0)  # the money was spent and is counted
    assert len(m.segments_done) == 1


def test_run_resumes_without_retagging(tmp_path):
    paths = setup(tmp_path)
    client = FakeClient([answer] * 3)
    tagger = ClaudeTagger(spec(), client)
    small = CostLedger(tmp_path / "ledger.jsonl", cap=0.010)
    m1 = run_tagging(spec(), "toy-sample", run_id="r1", tagger=tagger, ledger=small, paths=paths)
    assert m1.status == RunStatus.STOPPED_BUDGET
    done_first = list(m1.segments_done)
    big = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    m2 = run_tagging(spec(), "toy-sample", run_id="r1", tagger=tagger, ledger=big, paths=paths)
    assert m2.status == RunStatus.DONE and len(m2.segments_done) == 3
    assert len(client.sync_calls) == 3  # one in the first run, two on resume
    tagged = [c["messages"][0]["content"] for c in client.sync_calls[1:]]
    first_text = TEXTS[done_first[0].rsplit(":", 1)[0]]
    assert all(first_text not in u for u in tagged)
    tags = tags_of(paths.runs_dir / "r1")
    keys = [(t.segment_id, t.value_id) for t in tags]
    assert len(keys) == len(set(keys)) == 2
    assert m2.cost_usd == pytest.approx(big.total())
    assert m2.started == m1.started


def test_resume_drops_tags_of_unfinished_segments(tmp_path):
    """A crash between appending tags and saving the manifest must not duplicate tags."""
    paths = setup(tmp_path)
    tagger = ClaudeTagger(spec(), FakeClient([answer] * 3))
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    run_tagging(spec(), "toy-sample", run_id="r1", tagger=tagger, ledger=ledger, paths=paths)
    run_dir = paths.runs_dir / "r1"
    m = RunManifest.model_validate_json((run_dir / "manifest.json").read_text())
    m.segments_done = [s for s in m.segments_done if not s.startswith("src-gb:000000000002")]
    m.status = RunStatus.RUNNING
    (run_dir / "manifest.json").write_text(m.model_dump_json())
    tagger = ClaudeTagger(spec(), FakeClient([answer]))
    run_tagging(spec(), "toy-sample", run_id="r1", tagger=tagger, ledger=ledger, paths=paths)
    keys = [(t.segment_id, t.value_id) for t in tags_of(run_dir)]
    assert len(keys) == len(set(keys)) == 2


def test_resume_refuses_a_different_spec(tmp_path):
    paths = setup(tmp_path)
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    tagger = ClaudeTagger(spec(), FakeClient([answer] * 3))
    run_tagging(spec(), "toy-sample", run_id="r1", tagger=tagger, ledger=ledger, paths=paths)
    other = spec(effort=Effort.HIGH)
    with pytest.raises(ValueError, match="r1"):
        run_tagging(other, "toy-sample", run_id="r1", tagger=ClaudeTagger(other, FakeClient()),
                    ledger=ledger, paths=paths)  # fmt: skip


def test_limits(tmp_path):
    paths = setup(tmp_path)
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    tagger = ClaudeTagger(spec(), FakeClient([answer] * 3))
    m = run_tagging(spec(), "toy-sample", run_id="r1", tagger=tagger, ledger=ledger, paths=paths,
                    limit_per_country=1)  # fmt: skip
    assert sorted(s.split(":")[0] for s in m.segments_done) == ["src-gb", "src-gr"]
    tagger = ClaudeTagger(spec(), FakeClient([answer] * 3))
    m = run_tagging(spec(), "toy-sample", run_id="r2", limit=1, tagger=tagger, ledger=ledger,
                    paths=paths)  # fmt: skip
    assert len(m.segments_done) == 1


def test_refusals_land_in_manifest(tmp_path):
    paths = setup(tmp_path)
    client = FakeClient([message(stop="refusal", category="cyber"), answer, answer])
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    m = run_tagging(spec(), "toy-sample", run_id="r1", tagger=ClaudeTagger(spec(), client),
                    ledger=ledger, paths=paths)  # fmt: skip
    assert m.status == RunStatus.DONE
    assert [r.category for r in m.refusals] == ["cyber"]
    assert m.refused_segments == [m.refusals[0].segment_id]
    assert len(ledger.path.read_text().splitlines()) == 3  # the refusal was recorded too


def test_batch_run_records_every_call(tmp_path):
    paths = setup(tmp_path)

    def batch_result(req):
        if "Alpha must" in req["params"]["messages"][0]["content"]:
            return message(stop="refusal")
        return answer(req["params"])

    client = FakeClient([answer], batch_result_for=batch_result)
    s = spec(batch=True)
    tagger = ClaudeTagger(s, client)
    tagger.sleep = lambda x: None
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    m = run_tagging(s, "toy-sample", run_id="b1", tagger=tagger, ledger=ledger, paths=paths)
    assert m.status == RunStatus.DONE and len(m.segments_done) == 3
    lines = [json.loads(x) for x in ledger.path.read_text().splitlines()]
    assert sorted(x["batch"] for x in lines) == [False, True, True, True]
    assert m.pending_batch_id is None
    assert len(tags_of(paths.runs_dir / "b1")) == 2


def test_lexicon_runs_through_runner(tmp_path):
    paths = setup(tmp_path)
    lex = tmp_path / "lex.yaml"
    lex.write_text(
        "framework_id: toy\nlevel_id: leaf\ntargets:\n  alpha: [alpha]\n  beta: [beta]\n",
        encoding="utf-8",
    )
    tagger = LexiconTagger(lex)
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    m = run_tagging(tagger.spec, "toy-sample", run_id="lex1", tagger=tagger, ledger=ledger,
                    paths=paths, unit=UnitLevel.SENTENCE)  # fmt: skip
    assert m.status == RunStatus.DONE and m.spec.unit == UnitLevel.SENTENCE
    assert m.cost_usd == 0 and not ledger.path.exists()
    tags = tags_of(paths.runs_dir / "lex1")
    assert {t.value_id for t in tags} == {"alpha", "beta"}
    assert all(t.stance.value == "mention" and t.evidence for t in tags)


def test_cli_few_shot_on_needs_a_file():
    from semval.cli import build_parser, main

    argv = ["tag", "--sample", "x", "--model", "claude-haiku-5-5", "--effort", "low",
            "--level", "leaf", "--unit", "article"]  # fmt: skip
    args = build_parser().parse_args([*argv, "--batch", "--limit-per-country", "2"])
    assert args.model == ModelId.HAIKU_5_5 and args.unit == UnitLevel.ARTICLE and args.batch
    assert args.few_shot == "off" and args.limit_per_country == 2
    with pytest.raises(SystemExit, match="few-shot-file"):
        main([*argv, "--few-shot", "on"])


def truncated(kw):
    msg = message([])
    msg.stop_reason = "max_tokens"
    return msg


def test_truncated_answer_retried_once_at_raised_cap(tmp_path):
    paths = setup(tmp_path)
    s = spec(effort=Effort.LOW)
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    client = FakeClient([truncated])
    m = run_tagging(s, "toy-sample", run_id="r1", limit=1, tagger=ClaudeTagger(s, client),
                    ledger=ledger, paths=paths)  # fmt: skip
    sid = "src-gb:000000000001:a"
    assert m.status == RunStatus.FAILED and m.truncated == {sid: 8000} and sid in m.failures
    assert client.sync_calls[0]["max_tokens"] == 8000

    client = FakeClient([truncated])  # the resume retries at 1.5x and is truncated again
    m = run_tagging(s, "toy-sample", run_id="r1", limit=1, tagger=ClaudeTagger(s, client),
                    ledger=ledger, paths=paths)  # fmt: skip
    assert client.sync_calls[0]["max_tokens"] == 12000 and m.truncated == {sid: 12000}

    client = FakeClient()  # a third attempt is not made
    m = run_tagging(s, "toy-sample", run_id="r1", limit=1, tagger=ClaudeTagger(s, client),
                    ledger=ledger, paths=paths)  # fmt: skip
    assert not client.sync_calls and m.status == RunStatus.FAILED and sid in m.failures
    assert len(ledger.path.read_text().splitlines()) == 2  # both truncated answers were paid


def test_truncated_retry_success_clears_the_flag(tmp_path):
    paths = setup(tmp_path)
    s = spec(effort=Effort.HIGH)
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    run_tagging(s, "toy-sample", run_id="r1", limit=1,
                tagger=ClaudeTagger(s, FakeClient([truncated])), ledger=ledger, paths=paths)  # fmt: skip
    client = FakeClient([answer])
    m = run_tagging(s, "toy-sample", run_id="r1", limit=1, tagger=ClaudeTagger(s, client),
                    ledger=ledger, paths=paths)  # fmt: skip
    assert client.sync_calls[0]["max_tokens"] == 20000  # 1.5 x 16000, capped
    assert m.status == RunStatus.DONE and not m.truncated and not m.failures


def test_batch_resume_fetches_the_submitted_set_whatever_the_limit(tmp_path):
    paths = setup(tmp_path)
    s = spec(batch=True)
    client = FakeClient(batch_result_for=lambda req: answer(req["params"]))
    real_retrieve = client.messages.batches.retrieve
    crashes = [RuntimeError("connection lost while polling")]

    def flaky(batch_id):
        if crashes:
            raise crashes.pop()
        return real_retrieve(batch_id)

    client.messages.batches.retrieve = flaky
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    tagger = ClaudeTagger(s, client)
    tagger.sleep = lambda x: None
    with pytest.raises(RuntimeError):
        run_tagging(s, "toy-sample", run_id="b1", tagger=tagger, ledger=ledger, paths=paths)
    saved = RunManifest.model_validate_json((paths.runs_dir / "b1" / "manifest.json").read_text())
    assert saved.status == RunStatus.FAILED and saved.pending_batch_id == "batch-1"
    assert len(saved.pending_batch_segments) == 3
    assert saved.pending_batch_segments["src-gr:000000000003:a"] == "src-gr:000000000003"

    tagger = ClaudeTagger(s, client)
    tagger.sleep = lambda x: None
    m = run_tagging(s, "toy-sample", run_id="b1", limit=1, tagger=tagger, ledger=ledger,
                    paths=paths)  # fmt: skip
    assert len(client.batch_requests) == 1  # fetched, not resubmitted
    assert m.status == RunStatus.DONE and len(m.segments_done) == 3
    assert m.pending_batch_id is None and m.pending_batch_segments == {}
    assert len(ledger.path.read_text().splitlines()) == 3  # every paid result recorded


def test_fallback_served_segments_in_manifest(tmp_path):
    from types import SimpleNamespace

    paths = setup(tmp_path)
    s = spec(model=ModelId.OPUS_5_5)
    its = [
        SimpleNamespace(type="message", model=None, input_tokens=900, output_tokens=0,
                        cache_creation_input_tokens=0, cache_read_input_tokens=0),
        SimpleNamespace(type="fallback_message", model="claude-opus-4-8", input_tokens=950,
                        output_tokens=300, cache_creation_input_tokens=0, cache_read_input_tokens=0),
    ]  # fmt: skip
    served = message([], u=usage(950, 300, iterations=its), model="claude-opus-4-8")
    ledger = CostLedger(tmp_path / "ledger.jsonl", cap=10.0)
    m = run_tagging(s, "toy-sample", run_id="r1", limit=1,
                    tagger=ClaudeTagger(s, FakeClient([served])), ledger=ledger, paths=paths)  # fmt: skip
    sid = "src-gb:000000000001:a"
    assert m.served_by == {sid: "claude-opus-4-8"}
    assert [(r.segment_id, r.served_by) for r in m.refusals] == [(sid, "claude-opus-4-8")]
    lines = [json.loads(x) for x in ledger.path.read_text().splitlines()]
    assert [x["model"] for x in lines] == ["claude-opus-5-5", "claude-opus-4-8"]


@pytest.mark.parametrize(
    ("status", "code"),
    [(RunStatus.DONE, 0), (RunStatus.FAILED, 1), (RunStatus.STOPPED_BUDGET, 3)],
)
def test_cli_exit_code_follows_status(monkeypatch, status, code):
    from semval.cli import main
    from semval.tagging import claude, runner

    def fake_run(spec, sample, **kw):
        assert kw["client"] == "client"
        return RunManifest(run_id="r", spec=spec, input_sample=sample, prompt_sha256="x",
                           status=status)  # fmt: skip

    monkeypatch.setattr(claude, "make_client", lambda: "client")
    monkeypatch.setattr(runner, "run_tagging", fake_run)
    argv = ["tag", "--sample", "x", "--model", "claude-haiku-5-5", "--effort", "low",
            "--level", "leaf", "--unit", "article", "--framework", "toy"]  # fmt: skip
    assert main(argv) == code
