import random
from collections import Counter
from pathlib import Path

import pytest
import yaml

from fake_anthropic import FakeClient, message
from semval.config import Effort, ModelId
from semval.datasets import touche23 as t
from semval.review.labels import LabelRecord, LabelStore, Verdict, label_paths
from semval.review.session import RowKind
from semval.review.texts import ReviewSource
from semval.tagging import fewshot as fs
from semval.tagging import fewshot_candidates as fc
from semval.tagging.base import RawTag
from semval.tagging.ledger import BudgetExceeded, CostLedger
from semval.tagging.prompt import FewShotExample, build_prompt
from semval.tags import EvidenceSpan, Stance
from semval.values import FRAMEWORK_DIR, LEAF_LEVEL, load_framework

FW = load_framework(FRAMEWORK_DIR / "schwartz19.yaml", local_dir=None)
LEAVES = sorted(v.id for v in FW.leaves())
COLUMNS = list(t.TOUCHE23_CATEGORIES)


def _write_split(d: Path, stem: str, prefix: str, rows: list[set[str]]) -> None:
    leaf_to_col = {v: k for k, v in t.TOUCHE23_CATEGORIES.items() if v}
    leaf_to_col[t.OBJECTIVITY_FLAG] = "Universalism: objectivity"
    arg = ["Argument ID\tConclusion\tStance\tPremise"]
    lab = ["Argument ID\t" + "\t".join(COLUMNS)]
    for i, labels in enumerate(rows):
        aid = f"{prefix}{i:03d}"
        arg.append(f"{aid}\tConclusion {aid}\tin favor of\tPremise text of {aid}, with a clause.")
        cols = {leaf_to_col[v] for v in labels}
        lab.append(aid + "\t" + "\t".join("1" if c in cols else "0" for c in COLUMNS))
    (d / f"arguments-{stem}.tsv").write_text("\n".join(arg) + "\n", encoding="utf-8")
    (d / f"labels-{stem}.tsv").write_text("\n".join(lab) + "\n", encoding="utf-8")


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    rng = random.Random(7)
    pool = [*LEAVES]

    def rows(n: int) -> list[set[str]]:
        out = [{LEAVES[i % 19]} for i in range(n)]
        for r in out[::3]:
            r.add(rng.choice(pool))
        return out

    train = [*rows(40), {t.OBJECTIVITY_FLAG}, set()]
    _write_split(tmp_path, "training", "TR", train)
    _write_split(tmp_path, "validation", "VA", rows(19))
    _write_split(tmp_path, "test", "TE", rows(19))
    return tmp_path


def test_candidates_never_from_test_split(data_dir: Path) -> None:
    test_ids = {i.id for i in t.load_split("test", data_dir)}
    chosen = fc.select_candidates(n=20, seed=1, data_dir=data_dir)
    assert len(chosen) == 20
    assert not test_ids & {i.id for i in chosen}
    # and with the test file gone the selection is the same
    (data_dir / "arguments-test.tsv").unlink()
    (data_dir / "labels-test.tsv").unlink()
    assert [i.id for i in fc.select_candidates(20, 1, data_dir)] == [i.id for i in chosen]


def test_selection_deterministic_balanced_skips_objectivity_only(data_dir: Path) -> None:
    a = fc.select_candidates(20, 1, data_dir)
    b = fc.select_candidates(20, 1, data_dir)
    assert [i.id for i in a] == [i.id for i in b]
    counts = Counter(v for i in a for v in i.labels if v in LEAVES)
    assert set(counts) == set(LEAVES)  # all 19 leaves covered
    assert max(counts.values()) - min(counts.values()) <= 2
    assert all(i.labels & set(LEAVES) for i in a)  # no objectivity-only or empty items
    assert len({i.id for i in a}) == 20
    other = fc.select_candidates(20, 2, data_dir)
    assert [i.id for i in other] != [i.id for i in a]


def _answer(tags: list[dict]):
    return message(tags)


def _tag(value: str, stance: str, quotes: list[str]) -> dict:
    return {"value_id": value, "stance": stance, "quotes": quotes, "confidence": 0.8}


def _item(labels: set[str]) -> t.ToucheItem:
    return t.ToucheItem(
        id="X1", conclusion="We should act", stance="against",
        premise="Tradition matters. Nothing else does.", labels=labels,
    )  # fmt: skip


def test_drafter_request_billing_and_quote_check(tmp_path: Path, caplog) -> None:
    ledger = CostLedger(tmp_path / "ledger.jsonl")
    targets = FW.target_set(LEAF_LEVEL)
    answer = _answer(
        [
            _tag("tradition", "endorse", ["Tradition matters.", "made up quote"]),
            _tag("humility", "reject", ["not in the text"]),  # not a gold value: ignored
            _tag("universalism_concern", "mention", ["Nothing else does."]),
        ]
    )
    client = FakeClient(sync_responses=[answer])
    item = _item({"tradition", "universalism_concern"})
    with caplog.at_level("WARNING"):
        tags = fc.FewShotDrafter(client, ledger, targets)(item)
    assert [(x.value_id, x.stance, x.quotes) for x in tags] == [
        ("tradition", "endorse", ["Tradition matters."]),
        ("universalism_concern", "mention", ["Nothing else does."]),
    ]
    assert "made up quote" in caplog.text
    req = client.sync_calls[0]
    assert req["model"] == str(ModelId.OPUS_5_5)
    assert req["output_config"]["effort"] == str(Effort.MEDIUM)
    assert req["output_config"]["format"]["type"] == "json_schema"
    assert req["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "thinking" not in req and "temperature" not in req
    assert req["betas"] and req["fallbacks"] == "default"
    # the definitions are the tagging prompt's own
    assert build_prompt(targets, []).system in req["system"][0]["text"]
    assert "tradition" in req["messages"][0]["content"]
    assert "Premise: Tradition matters." in req["messages"][0]["content"]
    assert ledger.total() > 0

    broke = CostLedger(tmp_path / "other.jsonl", cap=0.0)
    with pytest.raises(BudgetExceeded):
        fc.FewShotDrafter(FakeClient(), broke, targets)(item)  # no call is made


def test_tag_without_valid_quote_is_kept_without_quotes(tmp_path: Path) -> None:
    client = FakeClient(sync_responses=[_answer([_tag("tradition", "endorse", ["nope"])])])
    drafter = fc.FewShotDrafter(client, CostLedger(tmp_path / "l.jsonl"), FW.target_set("leaf"))
    tags = drafter(_item({"tradition"}))
    assert [(x.value_id, x.quotes) for x in tags] == [("tradition", [])]


def test_draft_candidates_resumable(data_dir: Path, tmp_path: Path) -> None:
    items = fc.select_candidates(3, 1, data_dir)

    class Drafter:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def __call__(self, item: t.ToucheItem) -> list[RawTag]:
            self.calls.append(item.id)
            if item.id == items[1].id:
                raise fc.DraftFailed("refused")
            v = min(item.labels & set(LEAVES))
            return [RawTag(value_id=v, stance="endorse", quotes=[])]

    d = Drafter()
    path = fc.draft_candidates(d, items, data_dir)
    assert path == data_dir / fc.CANDIDATES_FILE
    got = fc.load_candidates(data_dir)
    assert [c.id for c in got] == [items[0].id, items[2].id]
    d2 = Drafter()
    fc.draft_candidates(d2, items, data_dir)
    assert d2.calls == [items[1].id]  # only the failed one is retried


# -- yaml ---------------------------------------------------------------------------------


def _example(eid: str, *tags: RawTag, text: str = "Tradition matters.") -> FewShotExample:
    return FewShotExample(id=eid, text=text, language="en", tags=list(tags), source="src")


def test_fewshot_yaml_has_attribution(tmp_path: Path) -> None:
    ex = _example("A1", RawTag(value_id="tradition", stance="endorse", quotes=["Tradition"]))
    path = tmp_path / "touche23.yaml"
    fs.write_fewshot(path, [ex])
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    head = raw["attribution"]
    assert "Touché23-ValueEval" in head["dataset"]
    assert head["licence"] == "CC BY 4.0"
    assert "zenodo.org/record/7879430" in head["url"]
    assert "Kiesel" in head["citation"]
    assert "Claude Opus 5.5" in head["stances"] and "project owner" in head["stances"]
    assert fs.load_fewshot(path) == [ex]
    # a plain list still loads
    plain = tmp_path / "plain.yaml"
    plain.write_text(yaml.safe_dump([ex.model_dump()]), encoding="utf-8")
    assert fs.load_fewshot(plain) == [ex]
    (tmp_path / "empty.yaml").write_text("examples: []", encoding="utf-8")
    with pytest.raises(ValueError):
        fs.load_fewshot(tmp_path / "empty.yaml")


# -- finalize -----------------------------------------------------------------------------

TEXT = "Conclusion: We should act\nStance: against\nPremise: Tradition matters. Nothing else does."


def _cand(cid: str, *tags: RawTag) -> fc.Candidate:
    return fc.Candidate(id=cid, split="train", tags=list(tags))


def _label(cid: str, value: str, verdict: Verdict, **kw) -> LabelRecord:
    return LabelRecord(
        labeller="owner", document_id=cid, value_id=value, level_id=LEAF_LEVEL,
        verdict=verdict, **{"model_stance": None, **kw},
    )  # fmt: skip


def _span(quote: str) -> EvidenceSpan:
    s = TEXT.index(quote)
    return EvidenceSpan(start=s, end=s + len(quote))


def test_finalize_applies_each_verdict_kind() -> None:
    items = {
        i: t.ToucheItem(
            id=i,
            conclusion="We should act",
            stance="against",
            premise="Tradition matters. Nothing else does.",
            labels=set(),
        )
        for i in ("C1", "C2", "C3", "C4")
    }
    tm = RawTag(value_id="tradition", stance="endorse", quotes=["Tradition matters."])
    hu = RawTag(value_id="humility", stance="endorse", quotes=["Nothing else does."])
    cands = [
        _cand("C1", tm, hu),
        _cand("C2", tm),
        _cand("C3", tm),
        _cand("C4", tm),  # never judged: dropped
    ]
    labels = [
        _label("C1", "tradition", Verdict.CORRECT, model_stance=Stance.ENDORSE),
        _label("C1", "humility", Verdict.WRONG_CALL, model_stance=Stance.ENDORSE,
               corrected_stance=Stance.REJECT),
        _label("C1", "face", Verdict.ADDED, corrected_stance=Stance.MENTION,
               owner_evidence=[_span("Nothing else does.")]),
        _label("C2", "tradition", Verdict.NOT_PRESENT, model_stance=Stance.ENDORSE),
        _label("C3", "tradition", Verdict.CORRECT, model_stance=Stance.ENDORSE),
        _label("C3", "stimulation", Verdict.ADDED, corrected_stance=Stance.REJECT),
    ]  # fmt: skip
    out = {e.id: e for e in fs.finalize(cands, items, labels, "owner")}
    assert list(out) == ["C1", "C2", "C3"]
    c1 = {x.value_id: x for x in out["C1"].tags}
    assert c1["tradition"].stance == "endorse" and c1["tradition"].quotes == ["Tradition matters."]
    assert c1["humility"].stance == "reject"
    assert c1["face"].stance == "mention" and c1["face"].quotes == ["Nothing else does."]
    assert out["C2"].tags == []  # judged, nothing left: a valid empty answer
    c3 = {x.value_id: x for x in out["C3"].tags}
    assert c3["stimulation"].quotes == []  # added without evidence
    assert out["C1"].text == items["C1"].text
    assert out["C1"].language == "en" and "CC BY 4.0" in out["C1"].source
    assert fs.stance_counts(list(out.values())) == {"endorse": 2, "reject": 2, "mention": 1}


def test_finalize_uses_latest_labeller_verdicts(tmp_path: Path) -> None:
    items = {"C1": _item(set()).model_copy(update={"id": "C1"})}
    cands = [_cand("C1", RawTag(value_id="tradition", stance="endorse", quotes=[]))]
    store = LabelStore(label_paths(tmp_path, "owner")[0])
    store.upsert(_label("C1", "tradition", Verdict.NOT_PRESENT, model_stance=Stance.ENDORSE))
    store.upsert(_label("C1", "tradition", Verdict.CORRECT, model_stance=Stance.ENDORSE))
    out = fs.finalize(cands, items, store.all(), "owner")
    assert [x.value_id for x in out[0].tags] == ["tradition"]
    assert fs.finalize(cands, items, store.all(), "someone-else") == []


# -- level roll-up ------------------------------------------------------------------------


def test_fewshot_at_level_rolls_up_and_drops_conflicts() -> None:
    roll = FW.rollup_map("basic10")
    text = "Tradition matters. Nothing else does."
    both = _example(
        "E1",
        RawTag(value_id="power_dominance", stance="endorse", quotes=["Tradition matters."]),
        RawTag(value_id="power_resources", stance="reject", quotes=["Nothing else does."]),
        RawTag(value_id="humility", stance="mention", quotes=[]),
        text=text,
    )
    strong = _example(
        "E2",
        RawTag(value_id="power_dominance", stance="mention", quotes=["Tradition matters."]),
        RawTag(
            value_id="power_resources",
            stance="endorse",
            quotes=["Nothing else does."],
            confidence=0.9,
        ),
        text=text,
    )
    assert fs.fewshot_at_level([both], FW, LEAF_LEVEL) == [both]
    got_both, got_strong = fs.fewshot_at_level([both, strong], FW, "basic10")
    assert [x.value_id for x in got_both.tags] == [roll["humility"]]  # endorse+reject dropped
    (tag,) = got_strong.tags
    assert tag.value_id == "power" and tag.stance == "endorse"
    assert tag.quotes == ["Tradition matters.", "Nothing else does."]
    build_prompt(FW.target_set("basic10"), [got_both, got_strong])  # a valid prompt


# -- review session -----------------------------------------------------------------------


def test_review_session_over_candidates(data_dir: Path, tmp_path: Path) -> None:
    from semval.review.fewshot_session import open_candidate_session

    items = fc.select_candidates(2, 1, data_dir)
    quote = "Premise text"
    cands = [
        fc.Candidate(
            id=i.id, split="train",
            tags=[RawTag(value_id=min(i.labels & set(LEAVES)), stance="endorse",
                         quotes=[quote])],
        )
        for i in items
    ]  # fmt: skip
    session = open_candidate_session(cands, items, labeller="owner", labels_dir=tmp_path / "labels")
    assert session.documents == [i.id for i in items]
    assert session.level_id == LEAF_LEVEL
    doc = session.doc_payload(items[0].id)
    assert "".join(p["t"] for p in doc["pieces"]) == items[0].text
    assert doc["meta"]["title"] == items[0].conclusion
    (row,) = [r for r in doc["rows"] if r["kind"] == RowKind.MODEL]
    assert row["stance"] == "endorse" and row["spans"] == 1
    assert row["source_runs"] == [fc.CANDIDATES_RUN_ID]
    v = cands[0].tags[0].value_id
    session.save_verdict(
        {"document_id": items[0].id, "value_id": v, "verdict": "correct", "model_stance": "endorse"}
    )
    (rec,) = LabelStore(label_paths(tmp_path / "labels", "owner")[0]).all()
    assert rec.source_runs == [fc.CANDIDATES_RUN_ID] and rec.model_evidence


def test_cli_parses_fewshot_and_defaults() -> None:
    from semval.cli import build_parser

    p = build_parser()
    a = p.parse_args(["fewshot", "candidates", "--n", "5"])
    assert (a.n, a.seed) == (5, 1)
    f = p.parse_args(["fewshot", "finalize"])
    assert f.labeller == "owner"
    tag = p.parse_args(
        ["tag", "--sample", "s", "--model", "claude-haiku-5-5", "--effort", "low",
         "--level", "leaf", "--unit", "paragraph"]
    )  # fmt: skip
    assert tag.few_shot_file is None  # _tag falls back to [DEFAULT_FEWSHOT_PATH]
    assert ReviewSource.TOUCHE23_FEWSHOT == "touche23-fewshot"
