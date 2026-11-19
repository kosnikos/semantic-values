"""Model ids, prices and the budget cap. The only place these live."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

BUDGET_USD = 50.0


class ModelId(StrEnum):
    HAIKU_5_5 = "claude-haiku-5-5"
    SONNET_5_5 = "claude-sonnet-5-5"
    OPUS_5_5 = "claude-opus-5-5"


class Effort(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Price(BaseModel):
    """USD per 1M tokens."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input: float
    output: float
    cache_write: float
    cache_read: float


# Prices cached 2026-11-03: re-check against the provider's price list before large runs.
PRICES: dict[ModelId, Price] = {
    ModelId.HAIKU_5_5: Price(input=0.10, output=0.50, cache_write=0.125, cache_read=0.01),
    ModelId.SONNET_5_5: Price(input=2.0, output=10.0, cache_write=2.50, cache_read=0.10),
    ModelId.OPUS_5_5: Price(input=4.0, output=20.0, cache_write=5.00, cache_read=0.20),
}
# The batch API charges this fraction of every component.
BATCH_FACTOR = 0.5
