import os
from pathlib import Path

import pytest

from semval.config import PRICES, FallbackModelId, ModelId, priced_model
from semval.tagging.base import Usage
from semval.tagging.ledger import BudgetExceeded, CostLedger, LedgerCorrupt

ONE_M = Usage(input_tokens=1_000_000, output_tokens=1_000_000)


def test_prices_cover_all_models():
    assert set(PRICES) == set(ModelId) | set(FallbackModelId)
    for p in PRICES.values():
        assert p.input > 0 and p.output > 0 and p.cache_read > 0 and p.cache_write > 0


def test_ledger_refuses_over_cap(tmp_path):
    ledger = CostLedger(tmp_path / "l.jsonl", cap=5.0)
    assert ledger.can_spend(5.0) and not ledger.can_spend(5.01)
    with pytest.raises(BudgetExceeded):
        ledger.record("r1", ONE_M, ModelId.SONNET_5_5, batch=False)  # 12 USD
    # the money was spent, so the line is still written
    assert ledger.total() == pytest.approx(12.0)
    assert not ledger.can_spend(0.01)


def test_ledger_batch_halves_cost(tmp_path):
    ledger = CostLedger(tmp_path / "l.jsonl", cap=100.0)
    full = ledger.record("r1", ONE_M, ModelId.SONNET_5_5, batch=False)
    half = ledger.record("r2", ONE_M, ModelId.SONNET_5_5, batch=True)
    assert half == pytest.approx(full / 2)
    est = ledger.estimate(ModelId.SONNET_5_5, 1_000_000, 1_000_000, batch=True)
    assert est == pytest.approx(half)


def test_ledger_cache_tokens_priced(tmp_path):
    ledger = CostLedger(tmp_path / "l.jsonl", cap=100.0)
    u = Usage(cache_creation_input_tokens=1_000_000, cache_read_input_tokens=1_000_000)
    assert ledger.record("r", u, ModelId.HAIKU_5_5, batch=False) == pytest.approx(0.135)


def test_ledger_persists_across_instances(tmp_path):
    path = tmp_path / "sub" / "l.jsonl"
    CostLedger(path, cap=100.0).record("r1", ONE_M, ModelId.HAIKU_5_5, batch=False)
    again = CostLedger(path, cap=100.0)
    assert again.total() == pytest.approx(0.6)
    again.record("r2", ONE_M, ModelId.HAIKU_5_5, batch=False)
    assert CostLedger(path, cap=100.0).total() == pytest.approx(1.2)
    assert len(path.read_text().splitlines()) == 2


def test_ledger_exact_cap_is_allowed(tmp_path):
    ledger = CostLedger(tmp_path / "l.jsonl", cap=12.0)
    assert ledger.can_spend(12.0)
    ledger.record("r1", ONE_M, ModelId.SONNET_5_5, batch=False)  # exactly 12 USD
    assert ledger.total() == pytest.approx(12.0)
    assert not ledger.can_spend(0.01)


def _truncated(tmp_path):
    path = tmp_path / "l.jsonl"
    ledger = CostLedger(path, cap=100.0)
    ledger.record("r1", ONE_M, ModelId.HAIKU_5_5, batch=False)
    with path.open("a", encoding="utf-8") as f:
        f.write('{"run_id": "r2", "cost_u')
    return path, ledger


def test_ledger_corrupt_line_fails_closed(tmp_path):
    _, ledger = _truncated(tmp_path)
    with pytest.raises(LedgerCorrupt, match="line 2"):
        ledger.total()
    with pytest.raises(LedgerCorrupt):
        ledger.can_spend(1.0)


def test_ledger_repair_moves_truncated_final_line(tmp_path):
    path, ledger = _truncated(tmp_path)
    assert ledger.repair() is True
    assert ledger.total() == pytest.approx(0.6)
    assert path.with_name("l.jsonl.corrupt").read_text().startswith('{"run_id": "r2"')
    assert ledger.repair() is False
    ledger.record("r3", ONE_M, ModelId.HAIKU_5_5, batch=False)
    assert ledger.total() == pytest.approx(1.2)


def test_ledger_repair_refuses_mid_file_damage(tmp_path):
    path = tmp_path / "l.jsonl"
    good = '{"cost_usd": 1.0}'
    path.write_text(f"{good}\nnot json\n{good}\n", encoding="utf-8")
    with pytest.raises(LedgerCorrupt, match="line 2"):
        CostLedger(path, cap=100.0).repair()
    assert not path.with_name("l.jsonl.corrupt").exists()


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity", "-0.5"])
def test_ledger_rejects_non_finite_or_negative_lines(tmp_path, bad):
    path = tmp_path / "l.jsonl"
    path.write_text('{"cost_usd": 1.0}\n{"cost_usd": ' + bad + "}\n", encoding="utf-8")
    with pytest.raises(LedgerCorrupt, match="line 2"):
        CostLedger(path, cap=100.0).total()


def test_ledger_record_rejects_negative_cost(tmp_path):
    ledger = CostLedger(tmp_path / "l.jsonl", cap=100.0)
    with pytest.raises(ValueError, match="cost"):
        ledger.record("r", Usage(input_tokens=-5), ModelId.HAIKU_5_5, batch=False)
    assert not ledger.path.exists()


def test_ledger_prices_fallback_models(tmp_path):
    ledger = CostLedger(tmp_path / "l.jsonl", cap=100.0)
    cost = ledger.record("r", ONE_M, FallbackModelId.OPUS_4_8, batch=False)
    assert cost == pytest.approx(30.0)
    assert priced_model("claude-opus-4-8") is FallbackModelId.OPUS_4_8
    assert priced_model("claude-haiku-5-5") is ModelId.HAIKU_5_5
    # an unknown model is priced as the dearest one rather than not at all
    assert PRICES[priced_model("claude-unknown-9")] == max(PRICES.values(), key=lambda p: p.output)


def test_ledger_repair_replaces_atomically(tmp_path, monkeypatch):
    path, ledger = _truncated(tmp_path)
    replaced = []
    real = os.replace
    monkeypatch.setattr(
        os, "replace", lambda a, b: (replaced.append((Path(a), Path(b))), real(a, b))
    )
    assert ledger.repair() is True
    ((src, dst),) = replaced
    assert dst == path and src != path and not src.exists()
    assert ledger.total() == pytest.approx(0.6)
