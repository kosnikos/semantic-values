"""Scoring tagging runs and writing ``docs/research/tagging-evaluation.md``.

The IO half of evaluation: reads run files, samples, cached texts and owner labels, turns
them into ids and stances, and hands those to the pure functions in ``metrics``.

Per run: paragraph tags are merged to articles first, then rolled up to the scoring level.
A leaf-level run is also scored at leaf. Runs are grouped into configurations by spec (kind,
model, effort, level, few-shot) and told apart by their ``input_sample``.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from semval.datasets.touche23_samples import EN_PREFIX
from semval.evaluation.metrics import (
    ANY_PRESENT,
    F1_TOLERANCE,
    STANCE_GATE_MARGIN,
    STRICT_PRESENT,
    ConfigKey,
    ConfigResult,
    InputScore,
    Pair,
    Scores,
    StanceScores,
    presence_scores,
    recommend,
    stance_agreement,
)
from semval.review.labels import LabelRecord
from semval.sampling.sample import SampleManifest
from semval.tagging.base import RunManifest, RunStatus
from semval.tagging.label_examples import excluded_documents
from semval.tagging.runfiles import RunPaths, load_run, load_run_tags, load_sample, read_text
from semval.tags import Stance, ValueTag, merge, rollup_tags
from semval.units import Segment, UnitLevel, document_id_of, segment
from semval.values import LEAF_LEVEL, Framework

DEFAULT_OUT: Final = Path("docs/research/tagging-evaluation.md")
SCORING_LEVEL: Final = "basic10"
DEFAULT_EN_SAMPLE: Final = "touche23-test-en-300"
DEFAULT_EL_SAMPLE: Final = "touche23-proxy-el-100"
DEFAULT_OWNER_SAMPLE: Final = "owner-set-v0"
EMPTY: Final = "—"
BATCH: Final = "batch"
PER_1000: Final = 1000

GoldFn = Callable[[SampleManifest, str], dict[str, set[str]]]


@dataclass(frozen=True)
class EvalSetup:
    framework: Framework
    paths: RunPaths
    labels: list[LabelRecord]  # the labeller's records (e.g. ``LabelStore.all()``)
    gold: GoldFn  # (sample, level id) -> document id -> gold value ids
    en_sample: str = DEFAULT_EN_SAMPLE
    el_sample: str = DEFAULT_EL_SAMPLE
    owner_sample: str = DEFAULT_OWNER_SAMPLE
    scoring_level: str = SCORING_LEVEL


def _item_id(doc_id: str) -> str:
    return doc_id.split(":", 1)[1]


def config_key(m: RunManifest) -> ConfigKey:
    s = m.spec
    return ConfigKey(
        kind=s.kind,
        model=s.model.value if s.model else None,
        effort=s.effort.value if s.effort else None,
        level_id=s.level_id,
        few_shot=s.few_shot,
    )


# -- one run ---------------------------------------------------------------------------


@dataclass
class _Run:
    manifest: RunManifest
    sample: SampleManifest
    docs: set[str]  # every document of the sample: the denominator of every score
    covered: int  # documents all of whose segments are finished
    merged: list[ValueTag]  # article-level tags at the tagging level

    @property
    def complete(self) -> bool:
        return self.manifest.status == RunStatus.DONE and self.covered == len(self.docs)

    @property
    def partial(self) -> str:
        """Why the run is not scored, e.g. ``partial 200/300 (stopped_budget)``."""
        status = "" if self.manifest.status == RunStatus.DONE else f" ({self.manifest.status})"
        return f"partial {self.covered}/{len(self.docs)}{status}"


def _load(setup: EvalSetup, run_id: str) -> _Run:
    paths = setup.paths
    m = load_run(paths.runs_dir, run_id)
    sample = load_sample(m.input_sample, paths.samples_dir)
    tags = load_run_tags(paths.runs_dir, run_id)
    unit = m.spec.unit or UnitLevel.PARAGRAPH
    done = set(m.segments_done)
    segments: list[Segment] = []
    covered = 0
    for d in sample.documents:
        segs = segment(d.id, read_text(paths.raw_dir, d), unit)
        segments += segs
        covered += all(x.id in done for x in segs if x.level == unit)
    docs = {d.id for d in sample.documents}
    return _Run(m, sample, docs, covered, merge(tags, segments, UnitLevel.ARTICLE))


def _rollup_to(setup: EvalSetup, tag_level: str) -> dict[str, str] | None:
    """The map from the tagging level's values to the scoring level, None if they coincide."""
    if tag_level == setup.scoring_level:
        return None
    if tag_level == LEAF_LEVEL:
        return setup.framework.rollup_map(setup.scoring_level)
    raise ValueError(
        f"cannot score a run tagged at {tag_level!r}: only {LEAF_LEVEL!r} or "
        f"{setup.scoring_level!r} can be scored at {setup.scoring_level!r}"
    )


def _rolled(run: _Run, setup: EvalSetup) -> list[ValueTag]:
    rollup = _rollup_to(setup, run.manifest.spec.level_id)
    return run.merged if rollup is None else rollup_tags(run.merged, rollup)


def _sets(tags: list[ValueTag], stances: frozenset[Stance]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for t in tags:
        if t.stance in stances:
            out.setdefault(document_id_of(t.segment_id), set()).add(t.value_id)
    return out


def _labels_of(setup: EvalSetup, level_id: str) -> list[str]:
    return [t.id for t in setup.framework.target_set(level_id).targets]


@dataclass
class _Presence:
    score: InputScore
    pred: dict[str, set[str]]  # strict
    gold: dict[str, set[str]]
    scores: Scores


def _presence(run: _Run, setup: EvalSetup) -> _Presence:
    level = setup.scoring_level
    gold = {d: g for d, g in setup.gold(run.sample, level).items() if d in run.docs}
    tags = _rolled(run, setup)
    labels = _labels_of(setup, level)

    def score(stances: frozenset[Stance]) -> Scores:
        return presence_scores(_sets(tags, stances), gold, labels, ignore_zero_support=True)

    strict = score(STRICT_PRESENT)
    leaf_f1 = None
    if run.manifest.spec.level_id == LEAF_LEVEL:
        leaf_gold = {d: g for d, g in setup.gold(run.sample, LEAF_LEVEL).items() if d in run.docs}
        leaf_f1 = presence_scores(
            _sets(run.merged, STRICT_PRESENT),
            leaf_gold,
            _labels_of(setup, LEAF_LEVEL),
            ignore_zero_support=True,
        ).macro_f1
    return _Presence(
        score=InputScore(
            run_id=run.manifest.run_id,
            n_docs=len(gold),
            macro_f1=strict.macro_f1,
            macro_f1_mention=score(ANY_PRESENT).macro_f1,
            per_label_f1={x: s.f1 for x, s in strict.per_label.items()},
            unsupported=[x for x, s in strict.per_label.items() if s.support == 0],
            leaf_macro_f1=leaf_f1,
        ),
        pred=_sets(tags, STRICT_PRESENT),
        gold=gold,
        scores=strict,
    )


def _stance(run: _Run, setup: EvalSetup) -> tuple[StanceScores, int]:
    """Stance scores on the owner set and the number of articles scored."""
    m = run.manifest
    tag_level = m.spec.level_id
    _rollup_to(setup, tag_level)  # refuse levels that cannot be scored
    scoring_ids = _labels_of(setup, setup.scoring_level)
    rollups: dict[str, Mapping[str, str]] = {setup.scoring_level: {x: x for x in scoring_ids}}
    if setup.scoring_level != LEAF_LEVEL:
        rollups[LEAF_LEVEL] = setup.framework.rollup_map(setup.scoring_level)
    excluded = excluded_documents(Path(f) for f in m.few_shot_files)
    docs = run.docs - excluded
    proposed: set[Pair] = {(document_id_of(t.segment_id), t.value_id) for t in run.merged}
    scores = stance_agreement(_rolled(run, setup), setup.labels, rollups, tag_level, proposed, docs)
    return scores, len(docs)


def _latency(m: RunManifest) -> str | None:
    if m.spec.batch:
        return BATCH
    if m.started is None or m.finished is None or not m.segments_done:
        return None
    seconds = (m.finished - m.started).total_seconds() / len(m.segments_done)
    return f"{seconds:.2f} s/segment"


# -- configurations ---------------------------------------------------------------------


@dataclass
class _Group:
    runs: dict[str, _Run] = field(default_factory=dict)  # sample name -> run


def build_results(run_ids: list[str], setup: EvalSetup) -> list[ConfigResult]:
    """Group runs into configurations and score each; ValueError on an unknown input
    sample, two runs of one configuration on one input, or an unscorable level."""
    wanted = {setup.en_sample, setup.el_sample, setup.owner_sample}
    groups: dict[ConfigKey, _Group] = {}
    for run_id in run_ids:
        run = _load(setup, run_id)
        sample = run.manifest.input_sample
        if sample not in wanted:
            raise ValueError(
                f"run {run_id!r} was tagged on {sample!r}, not one of {sorted(wanted)}"
            )
        _rollup_to(setup, run.manifest.spec.level_id)  # refuse levels that cannot be scored
        group = groups.setdefault(config_key(run.manifest), _Group())
        if sample in group.runs:
            other = group.runs[sample].manifest.run_id
            raise ValueError(
                f"two runs of {config_key(run.manifest).label} on {sample!r}: {other!r}, {run_id!r}"
            )
        group.runs[sample] = run
    return [_result(key, g, setup) for key, g in groups.items()]


def _result(key: ConfigKey, g: _Group, setup: EvalSetup) -> ConfigResult:
    en_run, el_run = g.runs.get(setup.en_sample), g.runs.get(setup.el_sample)
    owner_run = g.runs.get(setup.owner_sample)
    en_run_ok = en_run if en_run and en_run.complete else None
    el_run_ok = el_run if el_run and el_run.complete else None
    en = _presence(en_run_ok, setup) if en_run_ok else None
    el = _presence(el_run_ok, setup) if el_run_ok else None
    en_parallel = None
    if en and el:
        wanted = {f"{EN_PREFIX}:{_item_id(d)}" for d in el.gold}
        common = {d: g_ for d, g_ in en.gold.items() if d in wanted}
        if len(common) == len(el.gold):  # the same items on both sides, else no gap
            labels = _labels_of(setup, setup.scoring_level)
            en_parallel = presence_scores(
                en.pred, common, labels, ignore_zero_support=True
            ).macro_f1
    stance = owner_docs = cost = None
    if owner_run and owner_run.complete:
        stance, owner_docs = _stance(owner_run, setup)
        n_done = len(owner_run.docs)
        cost = owner_run.manifest.cost_usd / n_done * PER_1000 if n_done else None
    timed = owner_run or en_run or el_run
    return ConfigResult(
        key=key,
        en=en.score if en else None,
        el=el.score if el else None,
        en_parallel_f1=en_parallel,
        stance=stance,
        owner_docs=owner_docs,
        en_partial=en_run.partial if en_run and not en_run.complete else None,
        el_partial=el_run.partial if el_run and not el_run.complete else None,
        owner_partial=owner_run.partial if owner_run and not owner_run.complete else None,
        owner_run_id=owner_run.manifest.run_id if owner_run else None,
        cost_per_1k=cost,
        latency=_latency(timed.manifest) if timed else None,
    )


# -- the report ---------------------------------------------------------------------------


def _f(x: float | None) -> str:
    return EMPTY if x is None else f"{x:.3f}"


def _cell(value: float | None, partial: str | None, fmt: Callable[[float], str] = str) -> str:
    """A number, else why there is none: a partial run is flagged, never shown as a score."""
    if value is not None:
        return fmt(value)
    return partial or EMPTY


def _per_label(score: InputScore | None, label: str) -> str:
    if score is None or label not in score.per_label_f1:
        return EMPTY
    return "no gold" if label in score.unsupported else _f(score.per_label_f1[label])


def _signed(x: float | None) -> str:
    return EMPTY if x is None else f"{x:+.3f}"


def _agreement(s: StanceScores | None) -> str:
    if s is None:
        return EMPTY
    rate = EMPTY if s.agreement is None else f" ({s.agreement:.0%})"
    return f"{s.agree}/{s.co_present}{rate}"


def _count(s: StanceScores | None, name: str) -> str:
    return EMPTY if s is None else str(getattr(s, name))


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    return [_row(header), _row(["---"] * len(header)), *(_row(r) for r in rows)]


def render_report(results: list[ConfigResult], scoring_level: str = SCORING_LEVEL) -> str:
    L: list[str] = []
    L += [
        "# Tagging evaluation",
        "",
        (
            f"Value-presence quality is scored at `{scoring_level}` (paragraph tags are merged to "
            "the article first, then rolled up). Touché23-ValueEval (Kiesel et al. 2023, CC BY 4.0) "
            "is the English test split plus a machine-translated Greek proxy; stance is scored on "
            "the owner's corrected newspaper articles. Generated by `semval evaluate`."
        ),
        "",
        "## Results",
        "",
    ]
    header = [
        "Configuration", "n EN", "Macro-F1 EN", "Macro-F1 EN +mention", "n EL",
        "Macro-F1 EL proxy", "Macro-F1 EL +mention", "Gap EN-EL", "n owner",
        "Stance agreement", "Missed", "Spurious", "Unjudged",
        "Cost / 1,000 articles (USD)", "Latency",
    ]  # fmt: skip
    rows = [
        [
            r.key.label,
            _cell(r.en and r.en.n_docs, r.en_partial),
            _cell(r.en and r.en.macro_f1, r.en_partial, _f),
            _cell(r.en and r.en.macro_f1_mention, r.en_partial, _f),
            _cell(r.el and r.el.n_docs, r.el_partial),
            _cell(r.el and r.el.macro_f1, r.el_partial, _f),
            _cell(r.el and r.el.macro_f1_mention, r.el_partial, _f),
            _signed(r.gap),
            _cell(r.owner_docs, r.owner_partial),
            r.owner_partial or _agreement(r.stance),
            _count(r.stance, "missed"),
            _count(r.stance, "spurious"),
            _count(r.stance, "unjudged"),
            EMPTY if r.cost_per_1k is None else f"{r.cost_per_1k:.2f}",
            r.latency or EMPTY,
        ]
        for r in results
    ]
    L += _table(header, rows)
    L += [
        "",
        "How to read the columns:",
        "",
        (
            "- **Macro-F1 EN / EL proxy**: a value counts as predicted when its merged stance is "
            "endorse, reject or contested; *mention* does not count (Touché labels say a value is "
            "behind the argument, not that it is merely named). *+mention* is the same with mention "
            "counted. Labels with no gold support in the set are left out of the average (declared), "
            "and appear in the per-value table marked `no gold`. `n` is the number of items "
            "(owner: articles) behind each score; a run that is not done or does not cover "
            "every document is shown as `partial n/N`, is not scored and is not ranked."
        ),
        (
            "- **Gap EN-EL**: English macro-F1 on the parallel items minus Greek-proxy macro-F1, "
            "signed; both sides are the same items."
        ),
        (
            "- **Stance agreement**: agreeing / co-present (value present for both the run and the "
            "owner), then the rate. *Contested* counts as a disagreement unless the owner's stance "
            "is contested. **Missed**: owner-present, not predicted. **Spurious**: predicted, owner "
            "said not present. **Unjudged**: predicted, no owner label yet (the blind pass fills "
            "these). Counts, not only rates: the owner set is small."
        ),
        (
            "- **Cost / 1,000 articles**: owner-set run cost / owner articles x 1,000. It is the "
            "cost of *paragraph-unit* tagging of *news articles*, not of arguments."
        ),
        (
            "- **Latency**: (finished - started) / segments for synchronous runs; message-batch "
            "runs show `batch`. A resumed run includes the time it sat stopped."
        ),
        (
            "- The lexicon baseline emits only *mention* (spec 5.3), so its strict macro-F1 is "
            "always 0: the **+mention** column is its meaningful figure."
        ),
        f"- {EMPTY}: the configuration has no run on that input.",
        "",
    ]
    scored = [r for r in results if r.owner_docs is not None]
    if scored:
        L += [
            "Owner articles scored: "
            + ", ".join(f"{r.key.label}: {r.owner_docs}" for r in scored)
            + " (articles that were few-shot sources of a run are left out of that run's score).",
            "",
        ]
    leaf = [r for r in results if r.en and r.en.leaf_macro_f1 is not None]
    leaf_el = [r for r in results if r.el and r.el.leaf_macro_f1 is not None]
    if leaf or leaf_el:
        L += ["## Leaf level (runs tagged at leaf)", ""]
        L += _table(
            ["Configuration", "Leaf macro-F1 EN", "Leaf macro-F1 EL proxy"],
            [
                [
                    r.key.label,
                    _f(r.en.leaf_macro_f1 if r.en else None),
                    _f(r.el.leaf_macro_f1 if r.el else None),
                ]
                for r in results
                if (r.en and r.en.leaf_macro_f1 is not None)
                or (r.el and r.el.leaf_macro_f1 is not None)
            ],
        )
        L += [""]
    with_labels = [r for r in results if r.en and r.en.per_label_f1]
    if with_labels:
        L += ["## Per-value F1 (English)", ""]
        values = sorted({v for r in with_labels for v in r.en.per_label_f1})  # type: ignore[union-attr]
        L += _table(
            ["Value", *(r.key.label for r in with_labels)],
            [
                [v, *(_per_label(r.en, v) for r in with_labels)]  # type: ignore[union-attr]
                for v in values
            ],
        )
        L += [""]
    L += [
        "## Decision rule",
        "",
        (
            "From the tagging-method spec, section 5.6. Touché23 macro-F1 (English and Greek "
            "proxy, averaged) ranks the configurations; the owner set is a gate: a configuration "
            "whose stance agreement on the owner set is clearly worse than the best is dropped; "
            f"among the rest, prefer the cheapest within {F1_TOLERANCE:.2f} macro-F1 of the best. "
            "Twenty articles cannot rank eight configurations on stance alone."
        ),
        "",
        (
            f'Builder\'s choices where the spec is open: "clearly worse" means more than '
            f"{STANCE_GATE_MARGIN:.2f} below the best agreement rate; a configuration with no owner "
            "run is not gated; the lexicon baseline is a comparison and is never recommended; a "
            "configuration missing the Greek-proxy run is ranked on English alone."
        ),
        "",
        "## Caveats",
        "",
        (
            "- Touché23 items are short arguments, not news, so absolute scores flatter every "
            "model. Use them to rank configurations, not as accuracy on newspapers."
        ),
        (
            "- The Greek text is a machine-translated proxy of the English items, not Greek "
            "newspaper prose; the gap measures sensitivity to the language of the same items."
        ),
        (
            "- The owner set is small (about 20 articles): read the counts, not the percentages, "
            "and do not expect it to separate close configurations."
        ),
        "- Touché23 labels presence only; stance is measured on the owner set alone.",
        (
            "- Cost and latency are for paragraph-unit tagging of news articles, taken from the "
            "owner-set run."
        ),
        "",
        "## Recommendation (draft: the owner decides)",
        "",
    ]
    rec = recommend(results)
    if rec.chosen is None:
        L += ["No configuration with Touché scores yet, so no recommendation."]
    else:
        chosen = next(r for r in results if r.key == rec.chosen)
        L += [
            (
                f"By the rule above the draft pick is **{rec.chosen.label}**: ranking score "
                f"{_f(chosen.rank_score)} against {_f(rec.reference_f1)}, the best among the configurations the gate kept (the overall best is {_f(rec.best_f1_score)}), cost per "
                f"1,000 articles {EMPTY if chosen.cost_per_1k is None else f'{chosen.cost_per_1k:.2f}'}, "
                f"stance agreement {_agreement(chosen.stance)}."
            ),
            "",
            "Within the macro-F1 tolerance: "
            + (", ".join(k.label for k in rec.within_tolerance) or "none")
            + ".",
            "",
            "Dropped by the stance gate: "
            + (", ".join(k.label for k in rec.dropped_by_gate) or "none")
            + ".",
        ]
    L += ["", "**Draft: the owner decides.**", ""]
    return "\n".join(L)


def write_report(
    results: list[ConfigResult], path: Path = DEFAULT_OUT, scoring_level: str = SCORING_LEVEL
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(results, scoring_level), encoding="utf-8")
    return path
