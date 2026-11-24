"""The budget cap, effort levels and token limits. Model ids and prices: semval.models."""

from enum import StrEnum

from semval.models import ModelId, Price

# ModelId and Price are re-exported: callers import them from here.
__all__ = ["BUDGET_USD", "HAIKU_5_5", "OPUS_5_5", "SONNET_5_5", "ModelId", "Price"]

BUDGET_USD = 50.0

# Defaults only (proxy and draft models, tests); the registry in data/models.yaml is the
# single source of ids and prices.
HAIKU_5_5 = "claude-haiku-5-5"
SONNET_5_5 = "claude-sonnet-5-5"
OPUS_5_5 = "claude-opus-5-5"


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
