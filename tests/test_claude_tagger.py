from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from fake_anthropic import FakeClient, message, usage
from semval.config import Effort, ModelId
from semval.tagging.base import CallPath, Tagger, TaggerKind, TaggerSpec
from semval.tagging.claude import ClaudeTagger
from semval.tagging.quotes import resolve_quotes
from semval.targets import TargetDef, TargetSet
from semval.units import DocumentMeta, Segment, UnitLevel

TEXT1 = "We must defend alpha.\n\nBeta is   overrated,\nsays the author."
TEXT2 = "Nothing to see here."
TARGETS = TargetSet(
    framework_id="toy",
    level_id="leaf",
    targets=[
        TargetDef(id="alpha", name="Alpha", definition="Wanting alpha things."),
        TargetDef(id="beta", name="Beta", definition="Wanting beta things."),
    ],
)
DOCS = {"d1": DocumentMeta(language="en", genre="opinion"), "d2": DocumentMeta(language="el", genre="opinion")}  # fmt: skip
SEGS = [
    Segment(id="d1:a", document_id="d1", level=UnitLevel.ARTICLE, start=0, end=len(TEXT1)),
    Segment(id="d2:a", document_id="d2", level=UnitLevel.ARTICLE, start=0, end=len(TEXT2)),
]
TEXTS = {"d1:a": TEXT1, "d2:a": TEXT2}
ALPHA = {"value_id": "alpha", "stance": "endorse", "quotes": ["defend alpha"], "confidence": 0.9}


def spec(model=ModelId.SONNET_5_5, effort=Effort.MEDIUM, batch=False) -> TaggerSpec:
    return TaggerSpec(
        kind=TaggerKind.CLAUDE, model=model, effort=effort, framework_id="toy",
        level_id="leaf", unit=UnitLevel.ARTICLE, batch=batch,
    )  # fmt: skip


def run(tagger, segs=SEGS):
    return tagger.tag(segs, {s.id: TEXTS[s.id] for s in segs}, TARGETS, DOCS)


def test_claude_spec_requires_model_effort_unit():
    for missing in ("model", "effort", "unit"):
        kw = {"kind": TaggerKind.CLAUDE, "model": ModelId.HAIKU_5_5, "effort": Effort.LOW,
              "framework_id": "toy", "level_id": "leaf", "unit": UnitLevel.ARTICLE}  # fmt: skip
        kw[missing] = None
        with pytest.raises(ValidationError, match=missing):
            TaggerSpec(**kw)


def test_request_has_effort_cache_and_no_thinking_params():
    client = FakeClient([message([ALPHA])])
    tagger = ClaudeTagger(spec(effort=Effort.LOW), client)
    assert isinstance(tagger, Tagger)
    run(tagger, SEGS[:1])
    (req,) = client.sync_calls
    assert req["model"] == "claude-sonnet-5-5"
    assert req["output_config"]["effort"] == "low"
    fmt = req["output_config"]["format"]
    assert fmt["type"] == "json_schema"
    assert fmt["schema"]["properties"]["tags"]["items"]["properties"]["value_id"]["enum"] == [
        "alpha",
        "beta",
    ]
    (block,) = req["system"]
    assert block["type"] == "text" and block["cache_control"] == {"type": "ephemeral"}
    assert "Wanting alpha things." in block["text"]
    for banned in ("thinking", "temperature", "top_p", "top_k"):
        assert banned not in req
    assert 1000 <= req["max_tokens"] <= 16000
    (msg,) = req["messages"]
    assert msg["role"] == "user"
    user = msg["content"]
    assert "en" in user and "opinion" in user and TEXT1 in user
    # the per-document part stays out of the cached prefix
    assert TEXT1 not in block["text"]


def test_fallbacks_only_on_sync_sonnet_opus():
    for model, expect in [
        (ModelId.HAIKU_5_5, False),
        (ModelId.SONNET_5_5, True),
        (ModelId.OPUS_5_5, True),
    ]:
        client = FakeClient([message([])])
        run(ClaudeTagger(spec(model=model), client), SEGS[:1])
        (req,) = client.sync_calls
        if expect:
            assert req["fallbacks"] == "default"
            assert req["betas"] == ["server-side-fallback-2026-07-01"]
        else:
            assert "fallbacks" not in req and "server-side-fallback-2026-07-01" not in req.get(
                "betas", []
            )
    client = FakeClient()
    run(ClaudeTagger(spec(model=ModelId.OPUS_5_5, batch=True), client))
    (reqs,) = client.batch_requests
    for r in reqs:
        assert "fallbacks" not in r["params"] and "betas" not in r["params"]
        assert r["params"]["output_config"]["effort"] == "medium"
        assert r["params"]["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_empty_tag_list_is_valid():
    client = FakeClient([message([]), message([ALPHA])])
    res = run(ClaudeTagger(spec(), client))
    assert res.tags_by_segment["d1:a"] == []
    assert res.tags_by_segment["d2:a"][0].value_id == "alpha"
    assert not res.failed and not res.refused and not res.skipped
    assert len(client.sync_calls) == 2  # an empty result is not retried
    assert len(res.calls) == 2 and all(c.path == CallPath.SYNC for c in res.calls)


def test_unresolved_quote_keeps_tag_flagged():
    seg = SEGS[0]
    spans, unresolved = resolve_quotes(TEXT1, seg, ["defend alpha"])
    assert not unresolved and TEXT1[spans[0].start : spans[0].end] == "defend alpha"
    # whitespace-normalised match maps back to the original span
    spans, unresolved = resolve_quotes(TEXT1, seg, ["Beta is overrated, says"])
    assert not unresolved
    assert TEXT1[spans[0].start : spans[0].end] == "Beta is   overrated,\nsays"
    spans, unresolved = resolve_quotes(TEXT1, seg, ["defend alpha", "not in the text"])
    assert unresolved and len(spans) == 1
    # offsets are document offsets, and the search stays inside the segment
    doc = "xx defend alpha yy defend alpha"
    inner = Segment(id="d:p1", document_id="d", level=UnitLevel.PARAGRAPH, start=19, end=len(doc))
    spans, unresolved = resolve_quotes(doc, inner, ["defend alpha"])
    assert not unresolved and spans[0].start == 19
    _, unresolved = resolve_quotes(doc, inner, ["xx"])
    assert unresolved


def test_quotes_and_confidence_are_cleaned():
    many = {**ALPHA, "quotes": ["a", "b", "c", "d"], "confidence": 1.7}
    res = run(ClaudeTagger(spec(), FakeClient([message([many])])), SEGS[:1])
    (tag,) = res.tags_by_segment["d1:a"]
    assert tag.quotes == ["a", "b", "c"] and tag.confidence == 1.0


def test_refusal_recorded_and_retried_once():
    def batch_result(req):
        user = req["params"]["messages"][0]["content"]
        return message(stop="refusal", category="cyber") if "defend" in user else message([])

    # the batch refuses d1; the one sync retry succeeds
    client = FakeClient([message([ALPHA])], batch_result_for=batch_result)
    tagger = ClaudeTagger(spec(batch=True), client)
    tagger.sleep = lambda s: None
    res = run(tagger)
    assert len(client.batch_requests) == 1 and len(client.sync_calls) == 1
    assert client.sync_calls[0]["fallbacks"] == "default"
    assert res.tags_by_segment["d1:a"][0].value_id == "alpha"
    assert res.refused == []
    assert [(e.segment_id, e.path, e.category) for e in res.refusals] == [
        ("d1:a", CallPath.BATCH, "cyber")
    ]
    paths = sorted((c.segment_id, c.path, c.refused) for c in res.calls)
    assert paths == [
        ("d1:a", CallPath.BATCH, True),
        ("d1:a", CallPath.SYNC, False),
        ("d2:a", CallPath.BATCH, False),
    ]

    # the retry refuses too: no third attempt, the segment is reported refused
    client = FakeClient([message(stop="refusal", category=None)], batch_result_for=batch_result)
    tagger = ClaudeTagger(spec(batch=True), client)
    tagger.sleep = lambda s: None
    res = run(tagger)
    assert len(client.sync_calls) == 1
    assert res.refused == ["d1:a"] and "d1:a" not in res.tags_by_segment
    assert [e.path for e in res.refusals] == [CallPath.BATCH, CallPath.SYNC]
    assert len(res.calls) == 3


def test_sync_refusal_is_final():
    client = FakeClient([message(stop="refusal", category="bio")])
    res = run(ClaudeTagger(spec(model=ModelId.HAIKU_5_5), client), SEGS[:1])
    assert res.refused == ["d1:a"] and len(client.sync_calls) == 1
    assert res.calls[0].refused and res.calls[0].refusal_category == "bio"


def test_fallback_iterations_are_costed_per_model():
    its = [
        SimpleNamespace(type="message", model="claude-opus-5-5", input_tokens=900,
                        output_tokens=0, cache_creation_input_tokens=0, cache_read_input_tokens=0),
        SimpleNamespace(type="fallback_message", model="claude-opus-4-8", input_tokens=950,
                        output_tokens=300, cache_creation_input_tokens=0, cache_read_input_tokens=0),
    ]  # fmt: skip
    msg = message([ALPHA], u=usage(950, 300, iterations=its), model="claude-opus-4-8")
    res = run(ClaudeTagger(spec(model=ModelId.OPUS_5_5), FakeClient([msg])), SEGS[:1])
    assert [(c.model, c.usage.input_tokens) for c in res.calls] == [
        ("claude-opus-5-5", 900),
        ("claude-opus-4-8", 950),
    ]
    assert res.usage.input_tokens == 1850 and res.usage.output_tokens == 300


def test_truncated_output_is_a_failure_not_a_result():
    msg = message([ALPHA])
    msg.stop_reason = "max_tokens"
    msg.content[-1].text = '{"tags": [{"value_id": "al'
    res = run(ClaudeTagger(spec(), FakeClient([msg])), SEGS[:1])
    assert "d1:a" in res.failed and "d1:a" not in res.tags_by_segment
    assert len(res.calls) == 1  # still paid for


def test_spend_guard_blocks_calls():
    client = FakeClient([message([])])
    tagger = ClaudeTagger(spec(), client)
    seen = []
    tagger.spend_guard = lambda usd: seen.append(usd) or False
    res = run(tagger)
    assert res.skipped == ["d1:a", "d2:a"] and not client.sync_calls
    assert seen and seen[0] > 0
    client = FakeClient()
    tagger = ClaudeTagger(spec(batch=True), client)
    tagger.spend_guard = lambda usd: False
    assert run(tagger).skipped == ["d1:a", "d2:a"] and not client.batch_requests


def test_batch_custom_ids_are_api_safe_and_map_back():
    client = FakeClient(batch_result_for=lambda req: message([ALPHA]))
    tagger = ClaudeTagger(spec(batch=True), client)
    tagger.sleep = lambda s: None
    submitted = []
    tagger.on_batch_submitted = submitted.append
    res = run(tagger)
    ids = [r["custom_id"] for r in client.batch_requests[0]]
    assert all(len(i) <= 64 and all(ch.isalnum() or ch in "_-" for ch in i) for i in ids)
    assert len(set(ids)) == 2
    assert set(res.tags_by_segment) == {"d1:a", "d2:a"}
    assert submitted == ["batch-1"]
    assert all(c.path == CallPath.BATCH for c in res.calls)


def test_batch_resume_fetches_instead_of_resubmitting():
    client = FakeClient(batch_result_for=lambda req: message([]))
    first = ClaudeTagger(spec(batch=True), client)
    first.sleep = lambda s: None
    run(first)
    again = ClaudeTagger(spec(batch=True), client)
    again.sleep = lambda s: None
    again.resume_batch_id = "batch-1"
    res = run(again)
    assert len(client.batch_requests) == 1 and client.retrieved[-1] == "batch-1"
    assert set(res.tags_by_segment) == {"d1:a", "d2:a"}


def test_count_tokens_used_for_estimate_with_char_fallback():
    client = FakeClient([message([])], counted_tokens=1234)
    tagger = ClaudeTagger(spec(), client)
    seen = []
    tagger.spend_guard = lambda usd: seen.append(usd) or True
    run(tagger, SEGS[:1])
    assert client.count_calls and client.count_calls[0]["model"] == "claude-sonnet-5-5"
    # 1234 input + 600 output at Sonnet 5.5 prices
    assert seen[0] == pytest.approx((1234 * 2.0 + 600 * 10.0) / 1e6)

    client = FakeClient([message([])])
    client.messages = SimpleNamespace(batches=client.messages.batches)  # no count_tokens
    tagger = ClaudeTagger(spec(), client)
    seen.clear()
    tagger.spend_guard = lambda usd: seen.append(usd) or True
    run(tagger, SEGS[:1])
    assert seen[0] > 600 * 10.0 / 1e6


def test_failed_sync_retry_keeps_batch_calls():
    import anthropic
    import httpx2

    def boom(kw):
        raise anthropic.APIConnectionError(request=httpx2.Request("POST", "https://example.org"))

    def batch_result(req):
        user = req["params"]["messages"][0]["content"]
        return message(stop="refusal") if "defend" in user else message([])

    tagger = ClaudeTagger(spec(batch=True), FakeClient([boom], batch_result_for=batch_result))
    tagger.sleep = lambda s: None
    res = run(tagger)
    assert "d1:a" in res.failed and res.tags_by_segment == {"d2:a": []}
    assert len(res.calls) == 2  # both batch items are still reported for the ledger
