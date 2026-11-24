"""Append-only cost ledger enforcing a hard budget cap."""

import datetime
import json
import math
import os
from collections.abc import Iterable
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


def _parse_row(line: str, number: int) -> tuple[float, tuple[str, str] | None]:
    """A line's cost and its (run_id, call_key), None for a row without a key (sync calls,
    and every row written before keys existed)."""
    try:
        row = json.loads(line)
        cost = float(row["cost_usd"])
        key = row.get("call_key")
        ident = None if key is None else (str(row["run_id"]), str(key))
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        raise LedgerCorrupt(f"ledger line {number} is unreadable: {e!r}") from e
    if not _valid_cost(cost):
        raise LedgerCorrupt(f"ledger line {number} has an invalid cost_usd {cost!r}")
    return cost, ident


def _parse(line: str, number: int) -> float:
    return _parse_row(line, number)[0]


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

    def _keys(self) -> set[tuple[str, str]]:
        rows = (_parse_row(line, n) for n, line in enumerate(self._lines(), 1) if line.strip())
        return {ident for _, ident in rows if ident is not None}

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

    def record(
        self,
        run_id: str,
        usage: Usage,
        model: PricedModel,
        batch: bool,
        call_key: str | None = None,
    ) -> float:
        """Append the cost line, then raise ``BudgetExceeded`` if the cap is now passed.

        A non-finite or negative cost (bad usage numbers) raises ``ValueError`` unwritten.
        The append is one binary write under the cross-process lock.

        ``call_key`` makes the record idempotent: a call that can be reported again (a
        submitted batch's results, fetched again on resume) carries a key unique within its
        run, and a key already in the ledger for ``run_id`` is not written again. Returns
        the cost written, 0.0 for such a duplicate; the cap is checked either way.
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
        if call_key is not None:
            line["call_key"] = call_key
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock():
            if call_key is not None and (run_id, call_key) in self._keys():
                cost = 0.0  # already recorded: the money is counted once
            else:
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

    def record_all(
        self, run_id: str, pairs: Iterable[tuple[PricedModel, Usage]], batch: bool
    ) -> float:
        """Record every (model, usage) pair of one message, then raise ``BudgetExceeded``
        if any record passed the cap: stopping at the first would leave later billed
        attempts (fallback iterations) uncounted."""
        spent, exceeded = 0.0, None
        for model, usage in pairs:
            try:
                spent += self.record(run_id, usage, model, batch)
            except BudgetExceeded as e:
                exceeded = e
        if exceeded is not None:
            raise exceeded
        return spent
