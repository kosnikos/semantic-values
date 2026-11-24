"""The model registry: ids, providers and prices live in data/models.yaml, not in code."""

from enum import StrEnum
from functools import cache
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import AfterValidator, BaseModel, ConfigDict, ValidationError

MODELS_PATH = Path(__file__).resolve().parents[2] / "data" / "models.yaml"


class Provider(StrEnum):
    ANTHROPIC = "anthropic"


class Price(BaseModel):
    """USD per 1M tokens."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input: float
    output: float
    cache_write: float
    cache_read: float


class ModelInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    provider: Provider
    prices: Price
    requestable: bool
    server_fallbacks: bool


class ModelRegistry:
    def __init__(self, models: list[ModelInfo], batch_factor: float) -> None:
        if not models:
            raise ValueError("the model registry is empty")
        self._models: dict[str, ModelInfo] = {}
        for m in models:
            if m.id in self._models:
                raise ValueError(f"duplicate model id {m.id!r}")
            self._models[m.id] = m
        self.batch_factor = batch_factor

    def ids(self) -> list[str]:
        return list(self._models)

    def get(self, id: str) -> ModelInfo:
        try:
            return self._models[id]
        except KeyError:
            raise ValueError(f"unknown model {id!r}; known: {', '.join(self._models)}") from None

    def requestable(self) -> list[str]:
        return [m.id for m in self._models.values() if m.requestable]

    def price(self, id: str) -> Price:
        return self.get(id).prices

    def priced(self, name: str) -> str:
        """The registry id to charge for a model name the API reported.

        A name we have no price for is charged as the dearest model we know: the money was
        spent, so it must be counted, and over-counting is the safe side of the budget cap.
        """
        if name in self._models:
            return name
        return max(self._models, key=lambda i: (self.price(i).output, self.price(i).input))


def load_registry(path: Path = MODELS_PATH) -> ModelRegistry:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    models = []
    for n, row in enumerate(raw.get("models") or [], 1):
        label = row.get("id", f"row {n}") if isinstance(row, dict) else f"row {n}"
        try:
            models.append(ModelInfo.model_validate(row))
        except ValidationError as e:
            raise ValueError(f"model {label!r} in {path}: {e}") from e
    if "batch_factor" not in raw:
        raise ValueError(f"{path}: batch_factor missing")
    return ModelRegistry(models, float(raw["batch_factor"]))


@cache
def registry() -> ModelRegistry:
    return load_registry()


def check_model(id: str) -> str:
    registry().get(id)  # raises ValueError listing the known ids
    return id


ModelId = Annotated[str, AfterValidator(check_model)]
