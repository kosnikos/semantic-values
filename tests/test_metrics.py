import pytest

from semval.evaluation.metrics import (
    ConfigKey,
    ConfigResult,
    InputScore,
    StanceScores,
    language_gap,
    owner_judgements,
    presence_scores,
    recommend,
    stance_agreement,
    stance_scores,
)
from semval.review.labels import LabelRecord, Verdict
from semval.tagging.base import TaggerKind
from semval.tags import Stance, ValueTag

GOLD = {"d1": {"a", "b"}, "d2": {"a"}, "d3": {"c"}}
PRED = {"d1": {"a"}, "d2": {"a", "b"}, "d3": set()}


def test_presence_scores_hand_computed():
    s = presence_scores(PRED, GOLD, ["a", "b", "c"])
    assert (s.per_label["a"].precision, s.per_label["a"].recall, s.per_label["a"].f1) == (1, 1, 1)
    b = s.per_label["b"]
    assert (b.tp, b.fp, b.fn, b.f1) == (0, 1, 1, 0)
    c = s.per_label["c"]
    assert (c.precision, c.recall, c.f1, c.support) == (0, 0, 0, 1)
    assert s.per_label["a"].support == 2
    assert s.macro_f1 == pytest.approx(1 / 3)
    assert s.labels_used == ["a", "b", "c"]


def test_precision_recall_fractions():
    # label x: pred on d1,d2; gold on d2,d3 -> tp1 fp1 fn1 -> P=R=F1=0.5
    s = presence_scores(
        {"d1": {"x"}, "d2": {"x"}, "d3": set()}, {"d1": set(), "d2": {"x"}, "d3": {"x"}}, ["x"]
    )
    assert (s.per_label["x"].precision, s.per_label["x"].recall, s.macro_f1) == (0.5, 0.5, 0.5)


def test_macro_f1_ignores_zero_support_only_when_declared():
    labels = ["a", "b", "c", "d"]  # d has no gold at all
    kept = presence_scores(PRED, GOLD, labels)
    assert kept.macro_f1 == pytest.approx(0.25) and "d" in kept.labels_used
    dropped = presence_scores(PRED, GOLD, labels, ignore_zero_support=True)
    assert dropped.macro_f1 == pytest.approx(1 / 3) and "d" not in dropped.labels_used
    assert "d" in dropped.per_label  # still reported per label, just not averaged


def test_presence_scores_missing_pred_doc_counts_as_empty():
    s = presence_scores({}, {"d1": {"a"}}, ["a"])
    assert s.per_label["a"].fn == 1 and s.macro_f1 == 0


def test_language_gap_is_signed():
    en = presence_scores({"d": {"a"}}, {"d": {"a"}}, ["a"])
    el = presence_scores({"d": set()}, {"d": {"a"}}, ["a"])
    assert language_gap(en, el) == 1.0
    assert language_gap(el, en) == -1.0


def tag(doc, value, stance):
    return ValueTag(segment_id=f"{doc}:a", value_id=value, stance=stance, run_id="r")


def test_stance_scores_counts():
    pred = {
        ("d1", "a"): Stance.ENDORSE,
        ("d1", "b"): Stance.REJECT,
        ("d2", "a"): Stance.MENTION,
        ("d2", "b"): Stance.ENDORSE,
        ("d3", "a"): Stance.CONTESTED,
    }
    owner = {
        ("d1", "a"): Stance.ENDORSE,  # agree
        ("d1", "b"): None,  # spurious
        ("d2", "a"): Stance.REJECT,  # disagree
        ("d2", "c"): Stance.MENTION,  # missed
        ("d3", "a"): Stance.REJECT,  # contested vs reject: disagreement
    }
    s = stance_scores(pred, owner)
    assert isinstance(s, StanceScores)
    assert (s.co_present, s.agree, s.missed, s.spurious, s.unjudged) == (3, 1, 1, 1, 1)
    assert s.agreement == pytest.approx(1 / 3)
    assert s.owner_present == 4 and s.predicted == 5


def test_stance_scores_no_co_present_has_no_rate():
    assert stance_scores({}, {}).agreement is None


def test_owner_judgements_rolls_up_and_wrong_call_uses_corrected_stance():
    rollups = {"leaf": {"alpha": "ga", "alpha2": "ga", "beta": "gb"}}

    def rec(doc, value, verdict, model=None, corrected=None):
        return LabelRecord(
            labeller="owner", document_id=doc, value_id=value, level_id="leaf",
            model_stance=model, verdict=verdict, corrected_stance=corrected,
        )  # fmt: skip

    records = [
        rec("d1", "alpha", Verdict.CORRECT, Stance.ENDORSE),
        rec("d1", "alpha2", Verdict.WRONG_CALL, Stance.ENDORSE, Stance.REJECT),
        rec("d1", "beta", Verdict.NOT_PRESENT, Stance.MENTION),
        rec("d2", "beta", Verdict.ADDED, None, Stance.MENTION),
        rec("d3", "alpha", Verdict.NOT_PRESENT, Stance.ENDORSE),
        rec("d3", "alpha2", Verdict.NOT_PRESENT, Stance.ENDORSE),
    ]
    proposed = {
        ("d1", "alpha"),
        ("d1", "alpha2"),
        ("d1", "beta"),
        ("d3", "alpha"),
        ("d3", "alpha2"),
    }
    j = owner_judgements(records, rollups, "leaf", proposed)
    assert j[("d1", "ga")] == Stance.CONTESTED  # endorse + reject
    assert j[("d1", "gb")] is None and j[("d2", "gb")] == Stance.MENTION
    assert j[("d3", "ga")] is None  # both proposed children judged absent
    # an unjudged proposed child keeps the target unjudged
    j = owner_judgements(records[-2:-1], rollups, "leaf", proposed)
    assert ("d3", "ga") not in j


def test_stance_agreement_end_to_end_with_excluded_docs():
    rollups = {"leaf": {"alpha": "ga", "beta": "gb"}}
    recs = [
        LabelRecord(
            labeller="owner", document_id="d1", value_id="alpha", level_id="leaf",
            model_stance=Stance.ENDORSE, verdict=Verdict.CORRECT,
        ),
        LabelRecord(
            labeller="owner", document_id="d9", value_id="beta", level_id="leaf",
            model_stance=None, verdict=Verdict.ADDED, corrected_stance=Stance.REJECT,
        ),
    ]  # fmt: skip
    tags = [tag("d1", "ga", Stance.ENDORSE), tag("d9", "gb", Stance.REJECT)]
    s = stance_agreement(tags, recs, rollups, "leaf", {("d1", "alpha")}, docs={"d1", "d2"})
    assert (s.co_present, s.agree, s.missed, s.predicted) == (1, 1, 0, 1)  # d9 out of scope


def result(label, en, el, agree, cost, kind=TaggerKind.CLAUDE):
    key = ConfigKey(kind=kind, model=label, effort="low", level_id="leaf", few_shot=False)
    return ConfigResult(
        key=key,
        en=InputScore(run_id="r", n_docs=300, macro_f1=en, macro_f1_mention=en) if en is not None else None,
        el=InputScore(run_id="r", n_docs=100, macro_f1=el, macro_f1_mention=el) if el is not None else None,
        stance=StanceScores(co_present=10, agree=round(agree * 10), missed=0, spurious=0,
                            unjudged=0, owner_present=10, predicted=10) if agree is not None else None,
        cost_per_1k=cost,
    )  # fmt: skip


def test_recommend_gate_then_cheapest_within_tolerance():
    best = result("best", 0.60, 0.58, 0.9, 100.0)  # score 0.59
    cheap = result("cheap", 0.59, 0.57, 0.9, 10.0)  # 0.58, within 0.02, cheaper
    cheaper_bad_stance = result("cheaper-bad", 0.59, 0.58, 0.5, 1.0)  # gated out
    far = result("far", 0.40, 0.40, 0.9, 0.5)  # too far in F1
    lex = result("lex", 0.59, 0.59, None, 0.0, kind=TaggerKind.LEXICON)  # baseline never chosen
    rec = recommend([best, cheap, cheaper_bad_stance, far, lex])
    assert rec.chosen == cheap.key
    assert rec.best_f1 == best.key
    assert cheaper_bad_stance.key in rec.dropped_by_gate
