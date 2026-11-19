"""Append-only cost ledger enforcing a hard budget cap."""

import datetime
import json
import math
import os
from pathlib import Path

from semval.config import BATCH_FACTOR, BUDGET_USD, PRICES, ModelId, PricedModel
from semval.fsutil import atomic_write_text, exclusive_lock
from semval.tagging.base import Usage


class BudgetExceeded(Exception):
    """Recording a cost pushed the total over the cap. The caller must stop."""


class LedgerCorrupt(Exception):
    """A ledger line cannot be read. Skipping it would undercount spend, so we stop."""


def _valid_cost(cost: float) -> bool:
    return math.isfinite(cost) and cost >= 0


def _parse(line: str, number: int) -> float:
    try:
        cost = float(json.loads(line)["cost_usd"])
    except (ValueError, KeyError, TypeError) as e:
        raise LedgerCorrupt(f"ledger line {number} is unreadable: {e!r}") from e
    if not _valid_cost(cost):
        raise LedgerCorrupt(f"ledger line {number} has an invalid cost_usd {cost!r}")
    return cost


def cost_of(usage: Usage, model: PricedModel, batch: bool) -> float:
    p = PRICES[model]
    usd = (
        usage.input_tokens * p.input
        + usage.output_tokens * p.output
        + usage.cache_creation_input_tokens * p.cache_write
        + usage.cache_read_input_tokens * p.cache_read
    ) / 1_000_000
    return usd * BATCH_FACTOR if batch else usd


class CostLedger:
    """Append-only JSONL spend log with a hard cap, safe across concurrent processes.

    Every read of the total and every append happens under an exclusive lock on the
    sidecar ``<ledger>.lock`` (bounded wait of ``lock_timeout`` seconds, then
    ``TimeoutError``). ``can_spend`` is checked before an API call and ``record`` after,
    and that window is not reserved, so concurrent runs can overshoot the cap by at most
    their in-flight calls.
    """

    def __init__(
        self,
        path: Path = Path("data/runs/ledger.jsonl"),
        cap: float = BUDGET_USD,
        lock_timeout: float = 30.0,
    ):
        self.path = Path(path)
        self.cap = cap
        self.lock_timeout = lock_timeout

    def _lock(self):
        return exclusive_lock(self.path.with_name(self.path.name + ".lock"), self.lock_timeout)

    def estimate(self, model: ModelId, in_tokens: int, out_tokens: int, batch: bool) -> float:
        return cost_of(Usage(input_tokens=in_tokens, output_tokens=out_tokens), model, batch)

    def _lines(self) -> list[str]:
        if not self.path.exists():
            return []
        return self.path.read_text(encoding="utf-8").splitlines()

    def _total(self) -> float:
        return sum(_parse(line, n) for n, line in enumerate(self._lines(), 1) if line.strip())

    def total(self) -> float:
        """Sum of all lines; raises ``LedgerCorrupt`` rather than skip an unreadable one."""
        with self._lock():
            return self._total()

    def repair(self) -> bool:
        """Move an unreadable FINAL line to ``<ledger>.corrupt``; True if one was moved.

        Only the last line is safe to drop (a crash mid-append). Damage anywhere earlier
        still raises ``LedgerCorrupt``.
        """
        with self._lock():
            return self._repair()

    def _repair(self) -> bool:
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
            f.flush()
            os.fsync(f.fileno())
        atomic_write_text(self.path, "".join(line + "\n" for line in lines[:-1]))
        return True

    def can_spend(self, usd: float) -> bool:
        return self.total() + usd <= self.cap

    def record(self, run_id: str, usage: Usage, model: PricedModel, batch: bool) -> float:
        """Append the cost line, then raise ``BudgetExceeded`` if the cap is now passed.

        A non-finite or negative cost (bad usage numbers) raises ``ValueError`` unwritten.
        The append is one binary write under the cross-process lock.
        """
        cost = cost_of(usage, model, batch)
        if not _valid_cost(cost):
            raise ValueError(f"refusing to record invalid cost {cost!r} for run {run_id}")
        line = {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "run_id": run_id,
            "model": str(model),
            "batch": batch,
            "usage": usage.model_dump(),
            "cost_usd": cost,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock():
            # A crash can leave a final line without its newline; never glue onto it.
            existing = self.path.read_bytes() if self.path.exists() else b""
            prefix = "\n" if existing and not existing.endswith(b"\n") else ""
            data = (prefix + json.dumps(line) + "\n").encode("utf-8")
            with self.path.open("ab") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            total = self._total()
        if total > self.cap:
            raise BudgetExceeded(f"total ${total:.2f} exceeds cap ${self.cap:.2f}")
        return cost
