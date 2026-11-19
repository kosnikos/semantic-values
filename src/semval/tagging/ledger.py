"""Append-only cost ledger enforcing a hard budget cap."""

import datetime
import json
import os
from pathlib import Path

from semval.config import BATCH_FACTOR, BUDGET_USD, PRICES, ModelId
from semval.tagging.base import Usage


class BudgetExceeded(Exception):
    """Recording a cost pushed the total over the cap. The caller must stop."""


class LedgerCorrupt(Exception):
    """A ledger line cannot be read. Skipping it would undercount spend, so we stop."""


def _parse(line: str, number: int) -> float:
    try:
        return float(json.loads(line)["cost_usd"])
    except (ValueError, KeyError, TypeError) as e:
        raise LedgerCorrupt(f"ledger line {number} is unreadable: {e!r}") from e


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

    def _lines(self) -> list[str]:
        if not self.path.exists():
            return []
        return self.path.read_text(encoding="utf-8").splitlines()

    def total(self) -> float:
        """Sum of all lines; raises ``LedgerCorrupt`` rather than skip an unreadable one."""
        return sum(_parse(line, n) for n, line in enumerate(self._lines(), 1) if line.strip())

    def repair(self) -> bool:
        """Move an unreadable FINAL line to ``<ledger>.corrupt``; True if one was moved.

        Only the last line is safe to drop (a crash mid-append). Damage anywhere earlier
        still raises ``LedgerCorrupt``.
        """
        lines = self._lines()
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines:
            return False
        for n, line in enumerate(lines[:-1], 1):
            if line.strip():
                _parse(line, n)
        try:
            _parse(lines[-1], len(lines))
            return False
        except LedgerCorrupt:
            pass
        side = self.path.with_name(self.path.name + ".corrupt")
        with side.open("a", encoding="utf-8") as f:
            f.write(lines[-1] + "\n")
        self.path.write_text("".join(line + "\n" for line in lines[:-1]), encoding="utf-8")
        return True

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
        # A crash can leave a final line without its newline; never glue onto it.
        existing = self.path.read_bytes() if self.path.exists() else b""
        prefix = "\n" if existing and not existing.endswith(b"\n") else ""
        with self.path.open("a", encoding="utf-8") as f:
            f.write(prefix + json.dumps(line) + "\n")
            f.flush()
            os.fsync(f.fileno())
        total = self.total()
        if total > self.cap:
            raise BudgetExceeded(f"total ${total:.2f} exceeds cap ${self.cap:.2f}")
        return cost
