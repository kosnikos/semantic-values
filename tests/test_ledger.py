import pytest

from semval.config import PRICES, ModelId
from semval.tagging.base import Usage
from semval.tagging.ledger import BudgetExceeded, CostLedger

ONE_M = Usage(input_tokens=1_000_000, output_tokens=1_000_000)


def test_prices_cover_all_models():
    assert set(PRICES) == set(ModelId)
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
