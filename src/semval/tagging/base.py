"""Shared tagger types: the spec, the result, the run manifest and the Tagger protocol.

Nothing here knows a framework, a source or a model; taggers receive a ``TargetSet``.
"""

import datetime
from collections.abc import Mapping
from enum import StrEnum
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from semval.config import Effort, ModelId
from semval.targets import TargetSet
from semval.units import DocumentMeta, Segment, UnitLevel


class TaggerKind(StrEnum):
    CLAUDE = "claude"
    LEXICON = "lexicon"


class RunStatus(StrEnum):
    RUNNING = "running"
    DONE = "done"
    STOPPED_BUDGET = "stopped_budget"
    FAILED = "failed"


class DefinitionWording(StrEnum):
    """Which wording of a target definition a prompt used."""

    OFFICIAL = "official"
    FALLBACK = "fallback"


class CallPath(StrEnum):
    """How a request reached the API."""

    SYNC = "sync"
    BATCH = "batch"


class Usage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(**{k: getattr(self, k) + getattr(other, k) for k in Usage.model_fields})


class TaggerSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: TaggerKind
    model: ModelId | None = None
    effort: Effort | None = None
    framework_id: str
    level_id: str
    unit: UnitLevel | None = None  # None: the tagger works at any level (lexicon)
    few_shot: bool = False
    batch: bool = False

    @model_validator(mode="after")
    def _claude_needs_settings(self) -> "TaggerSpec":
        if self.kind == TaggerKind.CLAUDE:
            missing = [f for f in ("model", "effort", "unit") if getattr(self, f) is None]
            if missing:
                raise ValueError(f"a claude tagger spec needs {', '.join(missing)}")
        return self


class RawTag(BaseModel):
    """A tag as a tagger reports it: quotes are text, not yet resolved to spans."""

    model_config = ConfigDict(extra="forbid")

    value_id: str
    # Kept equal to Stance minus CONTESTED by a test.
    stance: Literal["endorse", "reject", "mention"]
    quotes: list[str] = Field(default_factory=list)
    confidence: float | None = None


class CallRecord(BaseModel):
    """One billed model attempt. ``model`` is the model that ran, as the API named it: with
    a server-side fallback one request yields a record per model."""

    model_config = ConfigDict(extra="forbid")

    segment_id: str
    model: str
    usage: Usage
    path: CallPath
    refused: bool = False
    refusal_category: str | None = None


class RefusalEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_id: str
    path: CallPath
    category: str | None = None
    # The fallback model that answered after this decline; None if nothing did.
    served_by: str | None = None


class TagBatchResult(BaseModel):
    """What a tagger did with a list of segments. Every segment it was given lands in
    exactly one of ``tags_by_segment`` (an empty list is a valid result), ``refused``,
    ``failed`` (retry later) or ``skipped`` (not attempted: the spend guard said no)."""

    model_config = ConfigDict(extra="forbid")

    tags_by_segment: dict[str, list[RawTag]]
    usage: Usage = Field(default_factory=Usage)
    calls: list[CallRecord] = Field(default_factory=list)
    refusals: list[RefusalEvent] = Field(default_factory=list)
    refused: list[str] = Field(default_factory=list)
    failed: dict[str, str] = Field(default_factory=dict)
    skipped: list[str] = Field(default_factory=list)
    # Segments whose answer hit max_tokens, with the cap that request used.
    truncated: dict[str, int] = Field(default_factory=dict)
    # Segments answered by a fallback model instead of the requested one.
    served_by: dict[str, str] = Field(default_factory=dict)


class PromptInfo(BaseModel):
    """What a run manifest records about a tagger's prompt for one target set."""

    model_config = ConfigDict(extra="forbid")

    prompt_sha256: str
    definition_wording: dict[str, int] = Field(default_factory=dict)


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    spec: TaggerSpec
    input_sample: str
    prompt_sha256: str
    status: RunStatus
    segments_done: list[str] = Field(default_factory=list)
    usage_totals: Usage = Field(default_factory=Usage)
    cost_usd: float = 0.0
    # Count of targets whose prompt used each DefinitionWording value.
    definition_wording: dict[str, int] = Field(default_factory=dict)
    # Few-shot files the prompt's examples came from, in order (empty: none, or an old run).
    few_shot_files: list[str] = Field(default_factory=list)

    @field_validator("definition_wording")
    @classmethod
    def _wording_keys(cls, v: dict[str, int]) -> dict[str, int]:
        bad = set(v) - {w.value for w in DefinitionWording}
        if bad:
            raise ValueError(f"unknown definition wording keys {sorted(bad)}")
        return v

    started: datetime.datetime | None = None
    finished: datetime.datetime | None = None
    # Every refusal seen; ``refused_segments`` are those whose final answer was a refusal
    # (done, with no tags).
    refusals: list[RefusalEvent] = Field(default_factory=list)
    refused_segments: list[str] = Field(default_factory=list)
    # Segments that got no usable answer (e.g. truncated output); a resume retries them.
    failures: dict[str, str] = Field(default_factory=dict)
    # Segments whose last answer hit max_tokens, with the cap used. A resume retries each
    # once at the raised cap (config.retry_max_tokens), then gives up.
    truncated: dict[str, int] = Field(default_factory=dict)
    # Segments answered by a fallback model (server-side refusal fallback), and which.
    served_by: dict[str, str] = Field(default_factory=dict)
    # A submitted message batch whose results are not yet stored, and its segments
    # (segment id -> document id, in submission order). A resume fetches exactly that set.
    pending_batch_id: str | None = None
    pending_batch_segments: dict[str, str] = Field(default_factory=dict)


@runtime_checkable
class Tagger(Protocol):
    spec: TaggerSpec

    def prompt_info(self, targets: TargetSet) -> PromptInfo: ...

    def tag(
        self,
        segments: list[Segment],
        texts: dict[str, str],
        targets: TargetSet,
        documents: Mapping[str, DocumentMeta],
    ) -> TagBatchResult: ...
