import json
from pathlib import Path

import pytest

from fake_anthropic import FakeClient, message
from semval.config import Effort, ModelId
from semval.datasets import touche23 as t
from semval.review.texts import TextProvider, TextUnavailable
from semval.tagging.ledger import BudgetExceeded, CostLedger
from semval.values import FRAMEWORK_DIR, LEAF_LEVEL, load_framework

FIXTURES = Path(__file__).parent / "fixtures" / "touche23"
FW = load_framework(FRAMEWORK_DIR / "schwartz19.yaml", local_dir=None)


def test_category_map_covers_20() -> None:
    assert len(t.TOUCHE23_CATEGORIES) == 20
    leaves = {v.id for v in FW.leaves()}
    mapped = [v for v in t.TOUCHE23_CATEGORIES.values() if v is not None]
    assert len(mapped) == 19
    assert set(mapped) == leaves
    assert t.TOUCHE23_CATEGORIES["Universalism: objectivity"] is None


def test_objectivity_maps_to_universalism_at_basic10_and_dropped_at_leaf() -> None:
    assert t.OBJECTIVITY_TARGET == {"basic10": "universalism"}
    item = t.ToucheItem(
        id="x", conclusion="c", stance="against", premise="p", labels={t.OBJECTIVITY_FLAG}
    )
    assert t.gold_at_level(item, FW, "basic10") == {"universalism"}
    assert t.gold_at_level(item, FW, LEAF_LEVEL) == set()
    assert t.gold_at_level(item, FW, "group4") == set()


def test_parse_fixture_rows() -> None:
    items = t.load_split("train", FIXTURES)
    assert [i.id for i in items] == ["A1", "A2", "A3"]
    assert items[0].labels == {"security_personal", t.OBJECTIVITY_FLAG}
    assert items[1].labels == {"tradition", "universalism_concern"}
    assert items[2].labels == set()
    assert items[0].premise == 'X harms "people" a lot.'
    assert items[0].text == (
        'Conclusion: We should ban X\nStance: in favor of\nPremise: X harms "people" a lot.'
    )


def test_gold_at_level_rolls_up() -> None:
    a1, a2, _ = t.load_split("train", FIXTURES)
    rollup = FW.rollup_map("basic10")
    assert t.gold_at_level(a1, FW, LEAF_LEVEL) == {"security_personal"}
    assert t.gold_at_level(a1, FW, "basic10") == {rollup["security_personal"], "universalism"}
    assert t.gold_at_level(a2, FW, "basic10") == {
        rollup["tradition"],
        rollup["universalism_concern"],
    }


class FakeTranslator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def __call__(self, conclusion: str, premise: str) -> tuple[str, str]:
        self.calls.append((conclusion, premise))
        return f"EL {conclusion}", f"EL {premise}"


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    for f in FIXTURES.glob("*.tsv"):
        (tmp_path / f.name.replace("training", "test")).write_bytes(f.read_bytes())
    return tmp_path


def test_proxy_keeps_ids_and_labels(data_dir: Path) -> None:
    tr = FakeTranslator()
    path = t.build_greek_proxy(tr, n=2, seed=1, data_dir=data_dir)
    assert path == data_dir / "proxy_el.jsonl"
    proxy = t.load_proxy(data_dir)
    english = {i.id: i for i in t.load_split("test", data_dir)}
    assert len(proxy) == 2 and len(tr.calls) == 2
    for p in proxy:
        assert p.language == "el"
        assert p.labels == english[p.id].labels and p.stance == english[p.id].stance
        assert p.conclusion == "EL " + english[p.id].conclusion
        assert "Στάση: " in p.text and ("υπέρ" in p.text or "κατά" in p.text)
    again = t.build_greek_proxy(tr, n=2, seed=1, data_dir=data_dir)  # resumes: no new calls
    assert again == path and len(tr.calls) == 2


def test_text_provider(data_dir: Path) -> None:
    english = t.load_split("test", data_dir)
    t.build_greek_proxy(FakeTranslator(), n=1, seed=1, data_dir=data_dir)
    provider = t.ToucheTextProvider(english, t.load_proxy(data_dir))
    assert isinstance(provider, TextProvider)
    assert provider.text("A1") == english[0].text
    info = provider.info("A1")
    assert info.title == "We should ban X" and info.language == "en"
    el_id = t.PROXY_ID_PREFIX + t.load_proxy(data_dir)[0].id
    assert provider.info(el_id).language == "el"
    with pytest.raises(TextUnavailable):
        provider.text("nope")


def _answer(text: str = '{"conclusion": "γ", "premise": "π"}', stop: str = "end_turn"):
    msg = message([], stop=stop)
    msg.content[1].text = text
    return msg


def test_claude_translator_records_and_guards(tmp_path: Path) -> None:
    ledger = CostLedger(tmp_path / "ledger.jsonl")
    client = FakeClient(sync_responses=[_answer()])
    assert t.ClaudeTranslator(client, ledger)("c", "p") == ("γ", "π")
    req = client.sync_calls[0]
    assert req["model"] == str(ModelId.SONNET_5_5)
    assert req["output_config"]["effort"] == str(Effort.LOW)
    assert req["output_config"]["format"]["type"] == "json_schema"
    assert req["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "thinking" not in req and "temperature" not in req
    assert ledger.total() > 0
    lines = (tmp_path / "ledger.jsonl").read_text().splitlines()
    assert json.loads(lines[0])["run_id"] == t.PROXY_RUN_ID

    broke = CostLedger(tmp_path / "other.jsonl", cap=0.0)
    with pytest.raises(BudgetExceeded):
        t.ClaudeTranslator(FakeClient(), broke)("c", "p")  # no API call is made

    bad = FakeClient(sync_responses=[_answer("not json")])
    with pytest.raises(t.TranslationFailed):
        t.ClaudeTranslator(bad, ledger)("c", "p")
    assert len((tmp_path / "ledger.jsonl").read_text().splitlines()) == 2  # still recorded


def test_cli_parses_touche_subcommands() -> None:
    from semval.cli import build_parser

    a = build_parser().parse_args(["touche23", "build-proxy", "--n", "5"])
    assert (a.n, a.seed, a.split) == (5, 1, "test")
    assert build_parser().parse_args(["touche23", "download"]).func.__name__ == "_touche_download"
