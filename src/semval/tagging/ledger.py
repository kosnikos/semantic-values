"""Append-only cost ledger enforcing a hard budget cap."""

import datetime
import json
from pathlib import Path

from semval.config import BATCH_FACTOR, BUDGET_USD, PRICES, ModelId
from semval.tagging.base import Usage


class BudgetExceeded(Exception):
    """Recording a cost pushed the total over the cap. The caller must stop."""


def cost_of(usage: Usage, model: ModelId, batch: bool) -> float:
    p = PRICES[model]
    usd = (
        usage.input_tokens * p.input
        + usage.output_tokens * p.output
        + usage.cache_creation_input_tokens * p.cache_write
        + usage.cache_read_input_tokens * p.cache_read
    ) / 1_000_000
    return usd * BATCH_FACTOR if batch else usd


class CostLedger:
    def __init__(self, path: Path = Path("data/runs/ledger.jsonl"), cap: float = BUDGET_USD):
        self.path = Path(path)
        self.cap = cap

    def estimate(self, model: ModelId, in_tokens: int, out_tokens: int, batch: bool) -> float:
        return cost_of(Usage(input_tokens=in_tokens, output_tokens=out_tokens), model, batch)

    def total(self) -> float:
        if not self.path.exists():
            return 0.0
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return sum(json.loads(line)["cost_usd"] for line in lines if line.strip())

    def can_spend(self, usd: float) -> bool:
        return self.total() + usd <= self.cap

    def record(self, run_id: str, usage: Usage, model: ModelId, batch: bool) -> float:
        """Append the cost line, then raise ``BudgetExceeded`` if the cap is now passed."""
        cost = cost_of(usage, model, batch)
        line = {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "run_id": run_id,
            "model": str(model),
            "batch": batch,
            "usage": usage.model_dump(),
            "cost_usd": cost,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
        total = self.total()
        if total > self.cap:
            raise BudgetExceeded(f"total ${total:.2f} exceeds cap ${self.cap:.2f}")
        return cost
