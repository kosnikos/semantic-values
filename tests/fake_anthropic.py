"""A stand-in for ``anthropic.Anthropic`` with no network: it records requests and replays
canned responses shaped like the SDK's (only the attributes the tagger reads)."""

import json
from types import SimpleNamespace


def usage(inp=1000, out=200, cw=0, cr=0, iterations=None) -> SimpleNamespace:
    return SimpleNamespace(
        input_tokens=inp,
        output_tokens=out,
        cache_creation_input_tokens=cw,
        cache_read_input_tokens=cr,
        iterations=iterations,
    )


def message(tags: list[dict] | None = None, *, stop="end_turn", category=None, u=None, model=None):
    content = (
        []
        if stop == "refusal"
        else [
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text=json.dumps({"tags": tags or []})),
        ]
    )
    details = SimpleNamespace(type="refusal", category=category) if stop == "refusal" else None
    return SimpleNamespace(
        content=content,
        stop_reason=stop,
        stop_details=details,
        usage=u or usage(),
        model=model,
    )


class _Messages:
    def __init__(self, client: "FakeClient"):
        self.client = client

    def create(self, **kw):
        self.client.sync_calls.append(kw)
        if not self.client.sync_responses:
            raise AssertionError("unexpected sync call")
        r = self.client.sync_responses.pop(0)
        return r(kw) if callable(r) else r


class _Batches:
    def __init__(self, client: "FakeClient"):
        self.client = client

    def create(self, requests):
        self.client.batch_requests.append(list(requests))
        return SimpleNamespace(
            id=f"batch-{len(self.client.batch_requests)}", processing_status="in_progress"
        )

    def retrieve(self, batch_id):
        self.client.retrieved.append(batch_id)
        return SimpleNamespace(id=batch_id, processing_status="ended")

    def results(self, batch_id):
        reqs = self.client.batch_requests[-1] if self.client.batch_requests else []
        out = []
        for req in reqs:
            msg = self.client.batch_result_for(req)
            if msg is None:
                out.append(
                    SimpleNamespace(
                        custom_id=req["custom_id"], result=SimpleNamespace(type="errored")
                    )
                )
            else:
                out.append(
                    SimpleNamespace(
                        custom_id=req["custom_id"],
                        result=SimpleNamespace(type="succeeded", message=msg),
                    )
                )
        return out


class _Counter:
    def __init__(self, client: "FakeClient"):
        self.client = client

    def count_tokens(self, **kw):
        self.client.count_calls.append(kw)
        return SimpleNamespace(input_tokens=self.client.counted_tokens)


class FakeClient:
    def __init__(self, sync_responses=(), batch_result_for=None, counted_tokens=1000):
        self.sync_responses = list(sync_responses)
        self.sync_calls: list[dict] = []
        self.batch_requests: list[list[dict]] = []
        self.retrieved: list[str] = []
        self.count_calls: list[dict] = []
        self.counted_tokens = counted_tokens
        self.batch_result_for = batch_result_for or (lambda req: message([]))
        self.beta = SimpleNamespace(messages=_Messages(self))
        counter = _Counter(self)
        self.messages = SimpleNamespace(count_tokens=counter.count_tokens, batches=_Batches(self))
