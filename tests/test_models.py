import pydantic
import pytest

from semval.models import ModelId, Price, load_registry, registry
from semval.tagging.base import Usage
from semval.tagging.ledger import cost_of

OLD = {
    "claude-haiku-5-5": Price(input=0.10, output=0.50, cache_write=0.125, cache_read=0.01),
    "claude-sonnet-5-5": Price(input=2.0, output=10.0, cache_write=2.50, cache_read=0.10),
    "claude-opus-5-5": Price(input=4.0, output=20.0, cache_write=5.00, cache_read=0.20),
    "claude-sonnet-5": Price(input=2.0, output=10.0, cache_write=2.50, cache_read=0.20),
    "claude-opus-5": Price(input=5.0, output=25.0, cache_write=6.25, cache_read=0.50),
    "claude-opus-4-8": Price(input=5.0, output=25.0, cache_write=6.25, cache_read=0.50),
}


def row(id, with_output=True):
    out = "output: 10.0, " if with_output else ""
    return (
        f"  - id: {id}\n    provider: anthropic\n"
        f"    prices: {{input: 1.0, {out}cache_write: 1.0, cache_read: 0.1}}\n"
        "    requestable: true\n    server_fallbacks: false\n"
    )


def write(tmp_path, *rows):
    p = tmp_path / "models.yaml"
    p.write_text("batch_factor: 0.5\nmodels:\n" + "".join(rows), encoding="utf-8")
    return p


def test_registry_matches_previous_prices():
    reg = registry()
    assert set(OLD) <= set(reg.ids())
    for id, price in OLD.items():
        assert reg.price(id) == price
    assert reg.batch_factor == 0.5


def test_requestable_and_fallback_flags():
    reg = registry()
    live = {"claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"}
    assert live <= set(reg.requestable())
    assert {"claude-sonnet-5", "claude-opus-5", "claude-opus-4-8"}.isdisjoint(reg.requestable())
    flagged = {i for i in reg.ids() if reg.get(i).server_fallbacks}
    assert {"claude-sonnet-5-5", "claude-opus-5-5"} <= flagged
    assert "claude-haiku-5-5" not in flagged


def test_unknown_reported_model_priced_dearest():
    reg = registry()
    dearest = max(OLD, key=lambda i: (OLD[i].output, OLD[i].input))
    assert reg.priced("claude-future-9") == dearest
    assert reg.priced("claude-haiku-5-5") == "claude-haiku-5-5"
    usage = Usage(input_tokens=1000, output_tokens=1000)
    assert cost_of(usage, "claude-future-9", False) > 0


def test_model_id_validation_lists_known():
    class M(pydantic.BaseModel):
        model: ModelId

    assert M(model="claude-sonnet-5-5").model == "claude-sonnet-5-5"
    with pytest.raises(pydantic.ValidationError, match="claude-sonnet-5-5"):
        M(model="gpt-x")


def test_registry_rejects_duplicate_and_missing_fields(tmp_path):
    with pytest.raises(ValueError, match="dup-model"):
        load_registry(write(tmp_path, row("dup-model"), row("dup-model")))
    with pytest.raises(ValueError, match="no-output"):
        load_registry(write(tmp_path, row("no-output", with_output=False)))


def test_new_row_needs_no_code_change(tmp_path):
    reg = load_registry(write(tmp_path, row("claude-sonnet-5-5"), row("brand-new-1")))
    assert "brand-new-1" in reg.requestable()
    assert reg.price("brand-new-1").input == 1.0


def _file(tmp_path, text):
    p = tmp_path / "models.yaml"
    p.write_text(text, encoding="utf-8")
    return p


@pytest.mark.parametrize(
    "prices",
    [
        "{input: '1.0', output: 10.0, cache_write: 1.0, cache_read: 0.1}",
        "{input: .nan, output: 10.0, cache_write: 1.0, cache_read: 0.1}",
        "{input: .inf, output: 10.0, cache_write: 1.0, cache_read: 0.1}",
        "{input: -1.0, output: 10.0, cache_write: 1.0, cache_read: 0.1}",
        "{input: 0, output: 10.0, cache_write: 1.0, cache_read: 0.1}",
        "{input: 1.0, output: 0.0, cache_write: 1.0, cache_read: 0.1}",
        "{input: 1.0, output: 10.0, cache_write: -1.0, cache_read: 0.1}",
        "{input: 1.0, output: 10.0, cache_write: 1.0, cache_read: .nan}",
    ],
)
def test_registry_rejects_bad_prices(tmp_path, prices):
    text = (
        "batch_factor: 0.5\nmodels:\n  - id: bad-row\n    provider: anthropic\n"
        f"    prices: {prices}\n    requestable: true\n    server_fallbacks: false\n"
    )
    with pytest.raises(ValueError, match="bad-row"):
        load_registry(_file(tmp_path, text))


@pytest.mark.parametrize("factor", ["0", "-0.5", ".nan", ".inf", "1.5", "'half'", "~"])
def test_registry_rejects_bad_batch_factor(tmp_path, factor):
    text = f"batch_factor: {factor}\nmodels:\n" + row("m1")
    with pytest.raises(ValueError, match="batch_factor"):
        load_registry(_file(tmp_path, text))


def test_registry_accepts_batch_factor_one(tmp_path):
    text = "batch_factor: 1\nmodels:\n" + row("m1")
    assert load_registry(_file(tmp_path, text)).batch_factor == 1.0


@pytest.mark.parametrize("text", ["- a\n- b\n", "just a string\n"])
def test_registry_rejects_non_mapping_top_level(tmp_path, text):
    with pytest.raises(ValueError, match="models.yaml"):
        load_registry(_file(tmp_path, text))
