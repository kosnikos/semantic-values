"""Evaluation metrics: pure functions over ids and stances, no file access.

Presence quality (per-label and macro F1), stance agreement against the owner's labels,
the language gap, and the decision rule of the tagging-method spec section 5.6.
"""

from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field

from semval.review.labels import LabelRecord
from semval.tagging.base import TaggerKind
from semval.tags import Stance, ValueTag, rollup_tags
from semval.units import document_id_of

Pair = tuple[str, str]  # (document id, value id)

# Decision rule (spec 5.6). Builder's constants; the report states them.
F1_TOLERANCE = 0.02  # "within 0.02 macro-F1 of the best"
FLOAT_SLACK = 1e-9  # so that 0.61 - 0.59 counts as within 0.02
STANCE_GATE_MARGIN = 0.10  # "clearly worse": more than this below the best agreement rate

# Stances that count as "present" in the strict Touché reading (mention does not count).
STRICT_PRESENT = frozenset({Stance.ENDORSE, Stance.REJECT, Stance.CONTESTED})
ANY_PRESENT = frozenset(Stance)


@dataclass(frozen=True)
class LabelScore:
    tp: int
    fp: int
    fn: int
    support: int  # gold positives

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


@dataclass(frozen=True)
class Scores:
    per_label: dict[str, LabelScore]
    labels_used: list[str]  # the labels averaged into macro_f1
    macro_f1: float


def presence_scores(
    pred: Mapping[str, Collection[str]],
    gold: Mapping[str, Collection[str]],
    labels: list[str],
    *,
    ignore_zero_support: bool = False,
) -> Scores:
    """Per-label precision/recall/F1 and macro-F1 over ``labels``.

    The documents are those of ``gold``; a document missing from ``pred`` has no
    predictions. A label with no gold positives scores F1 0 and is averaged in, unless
    ``ignore_zero_support`` (a declared choice) leaves it out of the macro average; it is
    still reported per label.
    """
    per_label = {}
    for label in labels:
        tp = fp = fn = 0
        for doc, g in gold.items():
            in_gold, in_pred = label in g, label in pred.get(doc, ())
            tp += in_gold and in_pred
            fp += in_pred and not in_gold
            fn += in_gold and not in_pred
        per_label[label] = LabelScore(tp, fp, fn, tp + fn)
    used = [x for x in labels if not ignore_zero_support or per_label[x].support > 0]
    macro = sum(per_label[x].f1 for x in used) / len(used) if used else 0.0
    return Scores(per_label, used, macro)


def language_gap(scores_en: Scores, scores_el: Scores) -> float:
    """English minus Greek-proxy macro-F1 on the same items (signed)."""
    return scores_en.macro_f1 - scores_el.macro_f1


# -- stance ----------------------------------------------------------------------------


@dataclass(frozen=True)
class StanceScores:
    co_present: int  # predicted and owner-present
    agree: int  # of those, equal stance (contested never equals an owner stance)
    missed: int  # owner-present, not predicted
    spurious: int  # predicted, owner said not present
    unjudged: int  # predicted, no owner label
    owner_present: int
    predicted: int

    @property
    def agreement(self) -> float | None:
        return self.agree / self.co_present if self.co_present else None


def stance_scores(pred: Mapping[Pair, Stance], owner: Mapping[Pair, Stance | None]) -> StanceScores:
    """Compare predicted stances with the owner's: ``owner[pair]`` is the owner's stance,
    ``None`` for "not present"; a pair absent from ``owner`` is unjudged."""
    owner_present = {p for p, s in owner.items() if s is not None}
    both = [p for p in pred if p in owner_present]
    return StanceScores(
        co_present=len(both),
        agree=sum(pred[p] == owner[p] for p in both),
        missed=len(owner_present - pred.keys()),
        spurious=sum(1 for p in pred if p in owner and owner[p] is None),
        unjudged=sum(1 for p in pred if p not in owner),
        owner_present=len(owner_present),
        predicted=len(pred),
    )


def _owner_tag(doc: str, value: str, stance: Stance) -> ValueTag:
    return ValueTag(segment_id=doc, value_id=value, stance=stance, run_id="owner")


def owner_judgements(
    records: Iterable[LabelRecord],
    rollups: Mapping[str, Mapping[str, str]],
    tagging_level: str,
    proposed: Collection[Pair],
) -> dict[Pair, Stance | None]:
    """The owner's answer per (document, target at the scoring level).

    ``rollups[level_id]`` sends a value of that level to its scoring-level target (the
    identity where the level is the scoring level). Present: any record with a present
    stance, combined with the shared tag rule (endorse + reject is contested); a record at
    a level without a roll-up is skipped. Not present (``None``): only from records at
    ``tagging_level``, and only when every pair in ``proposed`` (the run's own tags at that
    level) under the target is judged not present, so an unjudged tag is never counted as
    spurious. Everything else is unjudged (absent).
    """
    present: dict[str, list[ValueTag]] = defaultdict(list)
    absent: set[Pair] = set()  # (doc, value) judged not present at the tagging level
    for r in records:
        stance = r.present_stance()
        rollup = rollups.get(r.level_id)
        if stance is not None:
            if rollup is not None and r.value_id in rollup:
                present[r.level_id].append(_owner_tag(r.document_id, r.value_id, stance))
        elif r.level_id == tagging_level:
            absent.add((r.document_id, r.value_id))
    combined: list[ValueTag] = []
    for level_id, tags in present.items():
        combined += rollup_tags(tags, dict(rollups[level_id]))
    out: dict[Pair, Stance | None] = {}
    if combined:
        identity = {t.value_id: t.value_id for t in combined}
        for t in rollup_tags(combined, identity):
            out[(t.segment_id, t.value_id)] = t.stance
    tag_roll = rollups.get(tagging_level, {})
    judged_absent: dict[Pair, set[Pair]] = defaultdict(set)
    for doc, value in absent:
        if value in tag_roll:
            judged_absent[(doc, tag_roll[value])].add((doc, value))
    for pair, children in judged_absent.items():
        if pair in out:
            continue
        wanted = {(d, v) for d, v in proposed if (d, tag_roll.get(v)) == pair}
        if wanted <= children:
            out[pair] = None
    return out


def stance_agreement(
    run_tags: list[ValueTag],
    labels: Iterable[LabelRecord],
    rollups: Mapping[str, Mapping[str, str]],
    tagging_level: str,
    proposed: Collection[Pair],
    docs: Collection[str],
) -> StanceScores:
    """Stance agreement of a run's article-level tags (merged, at the scoring level) with the owner's labels, over ``docs`` only (leave out the articles
    that were few-shot sources). ``labels`` is e.g. ``LabelStore.all()``."""
    scope = set(docs)
    pred = {
        (document_id_of(t.segment_id), t.value_id): t.stance
        for t in run_tags
        if document_id_of(t.segment_id) in scope
    }
    records = [r for r in labels if r.document_id in scope]
    owner = owner_judgements(
        records, rollups, tagging_level, {p for p in proposed if p[0] in scope}
    )
    return stance_scores(pred, owner)


# -- configurations and the decision rule -------------------------------------------------


@dataclass(frozen=True)
class ConfigKey:
    kind: TaggerKind
    model: str | None
    effort: str | None
    level_id: str
    few_shot: bool

    @property
    def label(self) -> str:
        if self.kind == TaggerKind.LEXICON:
            return f"lexicon ({self.level_id})"
        shots = "few-shot" if self.few_shot else "zero-shot"
        return f"{self.model} {self.effort} ({self.level_id}, {shots})"


@dataclass(frozen=True)
class InputScore:
    run_id: str
    n_docs: int
    macro_f1: float  # strict presence: endorse, reject or contested
    macro_f1_mention: float  # mention counts as present too
    per_label_f1: dict[str, float] = field(default_factory=dict)
    leaf_macro_f1: float | None = None  # where the run was tagged at leaf
    unsupported: list[str] = field(default_factory=list)  # labels with no gold in this input


@dataclass(frozen=True)
class ConfigResult:
    key: ConfigKey
    en: InputScore | None = None
    el: InputScore | None = None
    en_parallel_f1: float | None = None  # English macro-F1 on the Greek-proxy item ids
    stance: StanceScores | None = None
    owner_docs: int | None = None
    owner_run_id: str | None = None
    # A run that is not done or misses documents is not scored: why, per input.
    en_partial: str | None = None
    el_partial: str | None = None
    owner_partial: str | None = None
    cost_per_1k: float | None = None
    latency: str | None = None  # "batch", "1.23 s/segment", or None

    @property
    def gap(self) -> float | None:
        if self.en_parallel_f1 is None or self.el is None:
            return None
        return self.en_parallel_f1 - self.el.macro_f1

    @property
    def rank_score(self) -> float | None:
        """Mean of the English and Greek-proxy macro-F1 (whichever exist); None if either
        run is partial, so an incomplete configuration is never ranked."""
        if self.en_partial or self.el_partial:
            return None
        vals = [s.macro_f1 for s in (self.en, self.el) if s is not None]
        return sum(vals) / len(vals) if vals else None


@dataclass(frozen=True)
class Recommendation:
    chosen: ConfigKey | None
    best_f1: ConfigKey | None
    best_f1_score: float | None
    reference_f1: float | None  # the best score among the kept configurations
    best_agreement: float | None
    dropped_by_gate: list[ConfigKey]
    within_tolerance: list[ConfigKey]


def recommend(results: list[ConfigResult]) -> Recommendation:
    """Spec 5.6: rank by Touché macro-F1; gate on owner-set stance agreement (drop those
    more than ``STANCE_GATE_MARGIN`` below the best); among the rest take the cheapest within
    ``F1_TOLERANCE`` of the best score. The lexicon baseline is a comparison, never chosen.
    A configuration with no owner stance rate is not gated; one with no cost cannot be the
    cheapest (it is chosen only if nothing has a cost)."""
    cands = [r for r in results if r.key.kind != TaggerKind.LEXICON and r.rank_score is not None]
    if not cands:
        return Recommendation(None, None, None, None, None, [], [])
    rates = [r.stance.agreement for r in cands if r.stance and r.stance.agreement is not None]
    best_rate = max(rates) if rates else None
    dropped = [
        r.key
        for r in cands
        if best_rate is not None
        and r.stance is not None
        and r.stance.agreement is not None
        and best_rate - r.stance.agreement > STANCE_GATE_MARGIN
    ]
    kept = [r for r in cands if r.key not in dropped]
    best = max(kept, key=lambda r: r.rank_score or 0.0)
    best_score = best.rank_score or 0.0
    near = [r for r in kept if best_score - (r.rank_score or 0.0) <= F1_TOLERANCE + FLOAT_SLACK]
    priced = [r for r in near if r.cost_per_1k is not None]
    pool = priced or near
    chosen = min(pool, key=lambda r: (r.cost_per_1k or 0.0, -(r.rank_score or 0.0)))
    overall = max(cands, key=lambda r: r.rank_score or 0.0)
    return Recommendation(
        chosen=chosen.key,
        best_f1=overall.key,
        best_f1_score=overall.rank_score,
        reference_f1=best_score,
        best_agreement=best_rate,
        dropped_by_gate=dropped,
        within_tolerance=[r.key for r in near],
    )
