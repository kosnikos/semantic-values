"""Claude implementation of the ``Tagger`` protocol.

Sync path: ``client.beta.messages.create`` with structured output, the effort setting, a
cached system prompt and (Sonnet, Opus) server-side refusal fallbacks. Batch path: Message
Batches, which reject ``fallbacks``, so a refused batch item is retried once on the sync
path. The tagger never touches the ledger: it reports every billed attempt in
``TagBatchResult.calls`` and the caller records them. Before each request it asks the
optional ``spend_guard`` whether the estimated cost (plus what it has already spent and
not yet reported) may be spent.
"""

import hashlib
import json
import logging
import math
import os
import re
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from semval.config import (
    API_KEY_ENV_VARS,
    MAX_TOKENS_BY_EFFORT,
    ModelId,
)
from semval.models import registry
from semval.tagging.base import (
    CallPath,
    CallRecord,
    PromptInfo,
    RawTag,
    RefusalEvent,
    TagBatchResult,
    TaggerKind,
    TaggerSpec,
    Usage,
)
from semval.tagging.ledger import cost_of
from semval.tagging.prompt import (
    MAX_QUOTES,
    FewShotExample,
    PromptParts,
    build_prompt,
    prompt_sha256,
    user_message,
)
from semval.targets import TargetSet
from semval.units import DocumentMeta, Segment

log = logging.getLogger(__name__)

FALLBACK_BETA = "server-side-fallback-2026-07-01"
EST_OUTPUT_TOKENS = 600  # per segment, for the pre-call budget check
CHARS_PER_TOKEN = 3.5  # estimate when count_tokens is unavailable
POLL_SECONDS = 30.0
_CUSTOM_ID_OK = re.compile(r"[A-Za-z0-9_-]{1,64}")
UNKNOWN_SEGMENT = "unknown-custom-id:"  # segment_id prefix for a result we cannot place


def make_client() -> anthropic.Anthropic:
    """A client keyed from the first set variable in ``API_KEY_ENV_VARS``; with none set,
    the SDK resolves credentials itself (auth token, profile). The key is never logged."""
    for name in API_KEY_ENV_VARS:
        key = os.environ.get(name)
        if key:
            log.info("using the API key from $%s", name)
            return anthropic.Anthropic(api_key=key)
    return anthropic.Anthropic()


def custom_ids(segment_ids: Sequence[str]) -> dict[str, str]:
    """Batch ``custom_id`` per segment id. The API allows only ``[A-Za-z0-9_-]{1,64}``, and
    segment ids contain ``:``. Deterministic, so a resumed run maps results back."""
    out: dict[str, str] = {}
    used: set[str] = set()
    for sid in segment_ids:
        cid = re.sub(r"[^A-Za-z0-9_-]", "_", sid)
        if not _CUSTOM_ID_OK.fullmatch(cid) or cid in used:
            cid = "h" + hashlib.sha256(sid.encode("utf-8")).hexdigest()[:40]
        if cid in used:
            raise ValueError(f"duplicate segment id {sid!r}")
        used.add(cid)
        out[sid] = cid
    return out


def _usage(u: Any) -> Usage:
    return Usage(
        input_tokens=u.input_tokens or 0,
        output_tokens=u.output_tokens or 0,
        cache_creation_input_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
        cache_read_input_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
    )


def _clean_tag(raw: dict[str, Any], ids: set[str]) -> RawTag:
    if raw["value_id"] not in ids:
        raise ValueError(f"value id {raw['value_id']!r} is not a target")
    quotes = [q for q in raw.get("quotes") or [] if isinstance(q, str) and q.strip()]
    conf = raw.get("confidence")
    return RawTag(
        value_id=raw["value_id"],
        stance=raw["stance"],
        quotes=quotes[:MAX_QUOTES],
        confidence=None if conf is None else min(1.0, max(0.0, float(conf))),
    )


def parse_answer(msg: Any, ids: set[str]) -> tuple[list[RawTag] | None, str | None]:
    """The tags of a non-refused response, or ``(None, reason)`` if it is unusable."""
    if msg.stop_reason == "max_tokens":
        return None, "output truncated (max_tokens)"
    text = next((b.text for b in msg.content if b.type == "text"), None)
    if text is None:
        return None, f"no text block (stop_reason {msg.stop_reason})"
    try:
        data = json.loads(text)
        return [_clean_tag(t, ids) for t in data["tags"]], None
    except (ValueError, KeyError, TypeError) as e:
        return None, f"unusable answer: {e!r}"


@dataclass
class _Collector:
    model: ModelId
    tags: dict[str, list[RawTag]] = field(default_factory=dict)
    calls: list[CallRecord] = field(default_factory=list)
    refusals: list[RefusalEvent] = field(default_factory=list)
    refused: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    skipped: list[str] = field(default_factory=list)
    truncated: dict[str, int] = field(default_factory=dict)
    served_by: dict[str, str] = field(default_factory=dict)

    def spent_usd(self) -> float:
        return sum(
            cost_of(c.usage, registry().priced(c.model), c.path == CallPath.BATCH)
            for c in self.calls
        )

    def result(self) -> TagBatchResult:
        total = Usage()
        for c in self.calls:
            total = total + c.usage
        return TagBatchResult(
            tags_by_segment=self.tags,
            usage=total,
            calls=self.calls,
            refusals=self.refusals,
            refused=self.refused,
            failed=self.failed,
            skipped=self.skipped,
            truncated=self.truncated,
            served_by=self.served_by,
        )


class ClaudeTagger:
    def __init__(
        self, spec: TaggerSpec, client: Any, few_shot: Sequence[FewShotExample] = ()
    ) -> None:
        if spec.kind != TaggerKind.CLAUDE or spec.model is None or spec.effort is None:
            raise ValueError("ClaudeTagger needs a claude spec with model and effort")
        if spec.few_shot != bool(few_shot):
            raise ValueError(
                f"spec.few_shot is {spec.few_shot} but {len(few_shot)} examples were given"
            )
        self.spec = spec
        self.model: ModelId = spec.model
        self.client = client
        self.few_shot = list(few_shot)
        self.spend_guard: Callable[[float], bool] | None = None
        # Called with the batch id and its segment ids (submission order) right after submit.
        self.on_batch_submitted: Callable[[str, list[str]], None] | None = None
        # Fetch this submitted batch instead of submitting; used once, then cleared.
        self.resume_batch_id: str | None = None
        # Per-segment max_tokens overrides (the raised cap for a truncated answer's retry).
        self.max_tokens_for: dict[str, int] = {}
        self.sleep: Callable[[float], None] = time.sleep
        self.poll_seconds = POLL_SECONDS

    # -- prompt ---------------------------------------------------------------------------

    def _prompt(self, targets: TargetSet) -> PromptParts:
        return build_prompt(targets, self.few_shot)

    def prompt_info(self, targets: TargetSet) -> PromptInfo:
        parts = self._prompt(targets)
        return PromptInfo(
            prompt_sha256=prompt_sha256(parts), definition_wording=parts.definition_wording
        )

    def _params(
        self, parts: PromptParts, text: str, meta: DocumentMeta, max_tokens: int
    ) -> dict[str, Any]:
        """Request body shared by both paths. No thinking or sampling parameters."""
        return {
            "model": str(self.model),
            "max_tokens": max_tokens,
            "system": [
                {"type": "text", "text": parts.system, "cache_control": {"type": "ephemeral"}}
            ],
            "messages": [{"role": "user", "content": user_message(text, meta)}],
            "output_config": {
                "effort": str(self.spec.effort),
                "format": {"type": "json_schema", "schema": parts.schema},
            },
        }

    def _sync_params(self, params: dict[str, Any]) -> dict[str, Any]:
        if registry().get(self.model).server_fallbacks:
            return {**params, "betas": [FALLBACK_BETA], "fallbacks": "default"}
        return params

    # -- budget ---------------------------------------------------------------------------

    def _input_tokens(self, params: dict[str, Any]) -> int:
        try:
            counted = self.client.messages.count_tokens(
                model=params["model"],
                system=params["system"],
                messages=params["messages"],
                output_config=params["output_config"],
            )
            return int(counted.input_tokens)
        except (AttributeError, anthropic.APIError) as e:
            log.debug("count_tokens unavailable (%r); estimating from characters", e)
            chars = len(params["system"][0]["text"]) + len(params["messages"][0]["content"])
            return math.ceil(chars / CHARS_PER_TOKEN)

    def _estimate_usd(self, params: dict[str, Any], batch: bool) -> float:
        usage = Usage(input_tokens=self._input_tokens(params), output_tokens=EST_OUTPUT_TOKENS)
        return cost_of(usage, self.model, batch)

    def _allowed(self, usd: float, out: _Collector) -> bool:
        return self.spend_guard is None or self.spend_guard(out.spent_usd() + usd)

    # -- responses ------------------------------------------------------------------------

    def _records(self, sid: str, msg: Any, path: CallPath) -> list[CallRecord]:
        """One record per billed attempt: ``usage.iterations`` when present (fallbacks bill
        each model at its own rates), else the top-level usage."""
        refused = msg.stop_reason == "refusal"
        category = getattr(msg.stop_details, "category", None) if refused else None
        iterations = getattr(msg.usage, "iterations", None)
        if iterations:
            # An iteration without a model ran on the requested model.
            pairs = [(getattr(it, "model", None) or str(self.model), it) for it in iterations]
        else:  # top-level usage is the attempt that produced the message
            model = msg.model if isinstance(msg.model, str) else str(self.model)
            pairs = [(model, msg.usage)]
        return [
            CallRecord(
                segment_id=sid,
                model=str(model),
                usage=_usage(it),
                path=path,
                refused=refused,
                refusal_category=category,
            )
            for model, it in pairs
        ]

    def _fallback(self, sid: str, msg: Any, path: CallPath, out: _Collector) -> None:
        """Note a fallback-served answer: ``served_by`` plus a refusal event per decline.

        Served-by comes from a ``fallback_message`` usage iteration; each ``fallback``
        content block marks one decline (sticky-routed turns have none: one event, no
        category)."""
        iterations = getattr(msg.usage, "iterations", None) or []
        served = [it for it in iterations if getattr(it, "type", None) == "fallback_message"]
        if not served:
            return
        model = str(served[-1].model)
        out.served_by[sid] = model
        blocks = [b for b in msg.content if getattr(b, "type", None) == "fallback"]
        categories = [getattr(getattr(b, "trigger", None), "category", None) for b in blocks]
        for category in categories or [None]:
            out.refusals.append(
                RefusalEvent(segment_id=sid, path=path, category=category, served_by=model)
            )

    def _handle(
        self, sid: str, msg: Any, path: CallPath, ids: set[str], out: _Collector, max_tokens: int
    ) -> bool:
        """Store one response; True if it was a refusal (the caller decides what next)."""
        records = self._records(sid, msg, path)
        out.calls.extend(records)
        u = sum((r.usage for r in records), Usage())
        log.info(
            "%s %s: stop=%s in=%d out=%d cache_write=%d cache_read=%d",
            path, sid, msg.stop_reason, u.input_tokens, u.output_tokens,
            u.cache_creation_input_tokens, u.cache_read_input_tokens,
        )  # fmt: skip
        if msg.stop_reason == "refusal":
            out.refusals.append(
                RefusalEvent(segment_id=sid, path=path, category=records[0].refusal_category)
            )
            return True
        self._fallback(sid, msg, path, out)
        if msg.stop_reason == "max_tokens":
            out.truncated[sid] = max_tokens
        tags, error = parse_answer(msg, ids)
        if tags is None:
            out.failed[sid] = error or "unusable answer"
        else:
            out.tags[sid] = tags
        return False

    # -- paths ----------------------------------------------------------------------------

    def _sync(self, sid: str, params: dict[str, Any], ids: set[str], out: _Collector) -> None:
        if not self._allowed(self._estimate_usd(params, batch=False), out):
            out.skipped.append(sid)
            return
        msg = self.client.beta.messages.create(**self._sync_params(params))
        if self._handle(sid, msg, CallPath.SYNC, ids, out, params["max_tokens"]):
            out.refused.append(sid)

    def _submit(self, requests: dict[str, dict[str, Any]], cids: dict[str, str]) -> str:
        batch = self.client.messages.batches.create(
            requests=[
                Request(custom_id=cids[sid], params=MessageCreateParamsNonStreaming(**params))
                for sid, params in requests.items()
            ]
        )
        log.info("submitted batch %s with %d requests", batch.id, len(requests))
        if self.on_batch_submitted is not None:
            self.on_batch_submitted(batch.id, list(requests))
        return batch.id

    def _batch(self, requests: dict[str, dict[str, Any]], ids: set[str], out: _Collector) -> None:
        cids = custom_ids(list(requests))
        batch_id = self.resume_batch_id
        if batch_id is None:
            est = sum(self._estimate_usd(p, batch=True) for p in requests.values())
            if not self._allowed(est, out):
                out.skipped.extend(requests)
                return
            batch_id = self._submit(requests, cids)
        else:
            log.info("fetching results of submitted batch %s", batch_id)
            self.resume_batch_id = None
        while self.client.messages.batches.retrieve(batch_id).processing_status != "ended":
            self.sleep(self.poll_seconds)
        by_cid = {cid: sid for sid, cid in cids.items()}
        seen: set[str] = set()
        retry: list[str] = []
        for item in self.client.messages.batches.results(batch_id):
            sid = by_cid.get(item.custom_id)
            if sid is None:
                # should not happen (a resume rebuilds the submitted set), but it was paid for
                log.warning("batch %s: unknown custom_id %s", batch_id, item.custom_id)
                if item.result.type == "succeeded":
                    unknown = UNKNOWN_SEGMENT + item.custom_id
                    out.calls.extend(self._records(unknown, item.result.message, CallPath.BATCH))
                continue
            seen.add(sid)
            limit = requests[sid]["max_tokens"]
            if item.result.type != "succeeded":
                out.failed[sid] = f"batch result {item.result.type}"
            elif self._handle(sid, item.result.message, CallPath.BATCH, ids, out, limit):
                retry.append(sid)
        for c in out.calls:  # this call's batch-path records all came from this batch
            if c.path == CallPath.BATCH:
                c.batch_id = batch_id
        for sid in requests:
            if sid not in seen:
                out.failed[sid] = "missing from batch results"
        for sid in retry:  # batches take no fallbacks: one sync attempt, which has them
            try:
                self._sync(sid, requests[sid], ids, out)
            except anthropic.APIError as e:
                # keep the batch's billed calls: raising here would lose them from the result
                log.warning("sync retry of %s failed: %r", sid, e)
                out.failed[sid] = f"sync retry failed: {type(e).__name__}"

    def tag(
        self,
        segments: list[Segment],
        texts: dict[str, str],
        targets: TargetSet,
        documents: Mapping[str, DocumentMeta],
    ) -> TagBatchResult:
        parts = self._prompt(targets)
        ids = set(targets.ids())
        requests: dict[str, dict[str, Any]] = {}
        for seg in segments:
            meta = documents.get(seg.document_id)
            if meta is None:
                raise ValueError(f"no document metadata for {seg.document_id!r}")
            limit = self.max_tokens_for.get(seg.id, MAX_TOKENS_BY_EFFORT[self.spec.effort])
            requests[seg.id] = self._params(parts, texts[seg.id], meta, limit)
        out = _Collector(model=self.model)
        if self.spec.batch:
            self._batch(requests, ids, out)
        else:
            for sid, params in requests.items():
                self._sync(sid, params, ids, out)
        return out.result()
