"""Shared tagger types: the spec, the result, the run manifest and the Tagger protocol.

Nothing here knows a framework, a source or a model; taggers receive a ``TargetSet``.
"""

import datetime
from enum import StrEnum
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from semval.config import Effort, ModelId
from semval.targets import TargetSet
from semval.units import Segment, UnitLevel


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


class Usage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


class TaggerSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: TaggerKind
    model: ModelId | None = None
    effort: Effort | None = None
    framework_id: str
    level_id: str
    unit: UnitLevel
    few_shot: bool = False
    batch: bool = False


class RawTag(BaseModel):
    """A tag as a tagger reports it: quotes are text, not yet resolved to spans."""

    model_config = ConfigDict(extra="forbid")

    value_id: str
    stance: Literal["endorse", "reject", "mention"]
    quotes: list[str] = Field(default_factory=list)
    confidence: float | None = None


class TagBatchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tags_by_segment: dict[str, list[RawTag]]
    usage: Usage = Field(default_factory=Usage)


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
    started: datetime.datetime | None = None
    finished: datetime.datetime | None = None


@runtime_checkable
class Tagger(Protocol):
    spec: TaggerSpec

    def tag(
        self, segments: list[Segment], texts: dict[str, str], targets: TargetSet
    ) -> TagBatchResult: ...
