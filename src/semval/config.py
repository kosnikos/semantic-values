"""Model ids, prices and the budget cap. The only place these live."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

BUDGET_USD = 50.0


class ModelId(StrEnum):
    HAIKU_5_5 = "claude-haiku-5-5"
    SONNET_5_5 = "claude-sonnet-5-5"
    OPUS_5_5 = "claude-opus-5-5"


class FallbackModelId(StrEnum):
    """Models the API may switch to when a request is refused (server-side fallbacks).

    Never requested directly; listed so their tokens can be priced.
    """

    SONNET_5 = "claude-sonnet-5"
    OPUS_5 = "claude-opus-5"
    OPUS_4_8 = "claude-opus-4-8"


PricedModel = ModelId | FallbackModelId

# Requested models that accept server-side refusal fallbacks (Haiku 5.5 has none).
SERVER_FALLBACK_MODELS: frozenset[ModelId] = frozenset({ModelId.SONNET_5_5, ModelId.OPUS_5_5})


class Effort(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Output cap per request. Thinking counts toward it, so it grows with effort; 16000 is the
# SDK's non-streaming default. A truncated answer is retried once (on resume) at
# MAX_TOKENS_RETRY_FACTOR x the cap, but never above MAX_TOKENS_CEILING (non-streaming
# requests must stay under the SDK's 10-minute limit, about 21K tokens).
MAX_TOKENS_BY_EFFORT: dict[Effort, int] = {
    Effort.LOW: 8000,
    Effort.MEDIUM: 12000,
    Effort.HIGH: 16000,
}
MAX_TOKENS_RETRY_FACTOR = 1.5
MAX_TOKENS_CEILING = 20000


def retry_max_tokens(effort: Effort) -> int:
    """The raised cap for the one retry of a truncated answer."""
    base = MAX_TOKENS_BY_EFFORT[effort]
    return min(int(base * MAX_TOKENS_RETRY_FACTOR), MAX_TOKENS_CEILING)


# Environment variables holding an API key, first match wins. If none is set, the SDK's own
# resolution (auth token, profile) applies.
API_KEY_ENV_VARS: tuple[str, ...] = ("ANTHROPIC_API_KEY_SEMANTIC_VALUES", "ANTHROPIC_API_KEY")


class Price(BaseModel):
    """USD per 1M tokens."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input: float
    output: float
    cache_write: float
    cache_read: float


# Prices cached 2026-11-03: re-check against the provider's price list before large runs.
# Haiku 5.5 has a second, dearer card for prompts over 100K tokens; our prompts stay far
# below that. Fallback-model cache prices assume the usual 1.25x write / 0.1x read.
PRICES: dict[PricedModel, Price] = {
    ModelId.HAIKU_5_5: Price(input=0.10, output=0.50, cache_write=0.125, cache_read=0.01),
    ModelId.SONNET_5_5: Price(input=2.0, output=10.0, cache_write=2.50, cache_read=0.10),
    ModelId.OPUS_5_5: Price(input=4.0, output=20.0, cache_write=5.00, cache_read=0.20),
    FallbackModelId.SONNET_5: Price(input=2.0, output=10.0, cache_write=2.50, cache_read=0.20),
    FallbackModelId.OPUS_5: Price(input=5.0, output=25.0, cache_write=6.25, cache_read=0.50),
    FallbackModelId.OPUS_4_8: Price(input=5.0, output=25.0, cache_write=6.25, cache_read=0.50),
}
# The batch API charges this fraction of every component.
BATCH_FACTOR = 0.5


def priced_model(name: str) -> PricedModel:
    """The price-table entry for a model name the API reported.

    A name we have no price for is charged as the dearest model we know: the money was
    spent, so it must be counted, and over-counting is the safe side of the budget cap.
    """
    for enum in (ModelId, FallbackModelId):
        try:
            return enum(name)
        except ValueError:
            pass
    return max(PRICES, key=lambda m: (PRICES[m].output, PRICES[m].input))
