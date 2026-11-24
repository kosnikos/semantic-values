"""Command-line interface for semval."""

import argparse
import logging
import typing
from datetime import date
from pathlib import Path
from typing import Any

from semval.review.labels import DEFAULT_LABELLER, DEFAULT_LABELS_DIR
from semval.sampling.sample import DEFAULT_RAW_DIR, DEFAULT_SAMPLES_DIR
from semval.sources import (
    EXCLUDED_SOURCE_TYPES,
    JURISDICTION_OPEN_SCOPES,
    JURISDICTION_OVERRIDE_BASIS,
    OPEN_SCOPES,
    OVERRIDE_EXCLUDED_ACCESS_METHODS,
    PERIODS,
    V0_COUNTRIES,
    RestrictionScope,
    Source,
    coverage_matrix,
    load_sources,
)
from semval.tagging.fewshot import DEFAULT_FEWSHOT_PATH
from semval.tagging.label_examples import DEFAULT_LOCAL_PATH as DEFAULT_LOCAL_FEWSHOT_PATH
from semval.tagging.runfiles import DEFAULT_RUNS_DIR

DEFAULT_SOURCES = Path("data/sources/sources.yaml")
DEFAULT_OUT = Path("docs/research/coverage.md")
_TRI_FIELDS = ("llm_api_allowed", "per_text_publish_allowed", "tdm_opt_out")


Matrix = dict[str, dict[str, list[str]]]


def _codes(items: typing.Iterable[str]) -> str:
    """Comma-separated code list in the order given, e.g. "`a`, `b`"."""
    return ", ".join(f"`{i}`" for i in items) or "none"


def _ordered(scopes: typing.AbstractSet[str]) -> list[str]:
    """Scopes in their RestrictionScope declaration order."""
    return [s for s in typing.get_args(RestrictionScope) if s in scopes]


def _excluded_types_note() -> str:
    return (
        f"Source types out of scope for v0 ({_codes(sorted(EXCLUDED_SOURCE_TYPES))}, setting "
        "`EXCLUDED_SOURCE_TYPES`) are left out of both tables; they stay in the registry."
    )


def _free_note() -> str:
    return (
        "Cells show the number of usable (free or free-registration) sources per period. "
        + _excluded_types_note()
    )


def _open_note() -> str:
    """Explanation of the open table, built from the settings in semval.sources."""
    open_known = OPEN_SCOPES - {"unknown"}
    closed = set(typing.get_args(RestrictionScope)) - OPEN_SCOPES
    parts = [
        "As above, minus sources whose restriction scope excludes them.",
        f"Open scopes (setting `OPEN_SCOPES`): {_codes(_ordered(open_known))}.",
    ]
    if "unknown" in OPEN_SCOPES:
        parts.append(
            "`unknown` counts as open but is unverified; such sources are listed under "
            "open questions."
        )
    parts.append(f"Excluding scopes: {_codes(_ordered(closed))}.")
    for country, scopes in JURISDICTION_OPEN_SCOPES.items():
        basis = JURISDICTION_OVERRIDE_BASIS.get(country)
        parts.append(
            f"Jurisdiction override (setting `JURISDICTION_OPEN_SCOPES`): in {country}, "
            f"{_codes(_ordered(scopes))} also count as open"
            + (f" under {basis}" if basis else "")
            + "."
        )
    if JURISDICTION_OPEN_SCOPES and OVERRIDE_EXCLUDED_ACCESS_METHODS:
        parts.append(
            "Overrides do not apply to sources accessed via "
            f"{_codes(sorted(OVERRIDE_EXCLUDED_ACCESS_METHODS))} "
            "(setting `OVERRIDE_EXCLUDED_ACCESS_METHODS`)."
        )
    parts.append(_excluded_types_note())
    return " ".join(parts)


def _table(matrix: Matrix) -> list[str]:
    labels = [label for label, _, _ in PERIODS]
    lines = ["| Country | " + " | ".join(labels) + " |", "|---|" + "---|" * len(labels)]
    for country, row in matrix.items():
        lines.append(f"| {country} | " + " | ".join(str(len(row[lb])) for lb in labels) + " |")
    return lines


def _open_questions(sources: list[Source]) -> list[str]:
    items = []
    for s in sources:
        unknown = [f for f in _TRI_FIELDS if getattr(s, f) == "unknown"]
        if s.restriction_scope == "unknown":
            unknown.append("restriction_scope")
        if unknown:
            items.append(f"- {s.id}: {', '.join(unknown)}")
    return items or ["None."]


def render_coverage_md(
    sources: list[Source],
    current_year: int,
    sources_path: str = DEFAULT_SOURCES.as_posix(),
) -> str:
    matrix = coverage_matrix(sources, V0_COUNTRIES, current_year)
    open_matrix = coverage_matrix(sources, V0_COUNTRIES, current_year, open_only=True)
    lines = [
        "# Source coverage",
        "",
        f"Generated from {sources_path}",
        "",
        "## Usable (free access)",
        "",
        _free_note(),
        "",
        *_table(matrix),
        "",
        "## Usable and not opted out",
        "",
        _open_note(),
        "",
        *_table(open_matrix),
        "",
        "## Open questions",
        "",
        *_open_questions(sources),
    ]
    return "\n".join(lines) + "\n"


def _coverage(args: argparse.Namespace) -> int:
    sources = load_sources(args.sources)
    md = render_coverage_md(sources, args.year, args.sources.as_posix())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md, encoding="utf-8")
    return 0


def _sample(args: argparse.Namespace) -> int:
    from semval.sampling.adapters import ADAPTERS
    from semval.sampling.fetch import PoliteFetcher
    from semval.sampling.sample import collect_sample, sources_for_countries

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    source_ids = args.source or sources_for_countries(
        args.countries, load_sources(args.sources), ADAPTERS
    )
    manifest = collect_sample(
        source_ids,
        args.per_country,
        args.since,
        args.until,
        name=args.name,
        registry_path=args.sources,
        fetcher=PoliteFetcher(max_requests=args.max_requests),
    )
    for sid, counts in manifest.stats.items():
        print(f"{sid}: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    countries = sorted({d.country for d in manifest.documents})
    for c in countries:
        print(f"{c}: {sum(d.country == c for d in manifest.documents)} documents")
    print(f"requests: {manifest.requests}")
    if manifest.stopped_early:
        print(f"stopped early: {manifest.stopped_early}")
    return 0


def _resolve_setup(args: argparse.Namespace) -> tuple[Any, Any, list[Any]]:
    """The saved setup with the command-line overrides applied, its spec, and the local
    few-shot files skipped because they are missing."""
    from semval.tagging.setups import (
        apply_overrides,
        load_setup,
        parse_options,
        skip_missing_few_shot,
        to_spec,
    )

    if args.no_few_shot and args.few_shot_file:
        raise SystemExit("--no-few-shot contradicts --few-shot-file")
    try:
        setup = load_setup(args.tagger)
        files = [] if args.no_few_shot else args.few_shot_file
        skipped: list[Any] = []
        if files is None:  # the setup's own list: a missing local file is skipped
            setup, skipped = skip_missing_few_shot(setup, args.tagger)
        setup = apply_overrides(
            setup,
            model=args.model,
            effort=args.effort,
            level=args.level,
            unit=args.unit,
            framework=args.framework,
            prompt=args.prompt,
            few_shot_files=files,
            batch=args.batch,
            options=parse_options(args.option) or None,
        )
        return setup, to_spec(setup), skipped
    except ValueError as e:
        raise SystemExit(f"error: tagger {args.tagger}: {e}") from None


def _tag(args: argparse.Namespace) -> int:
    from semval.tagging.fewshot import load_fewshot_files
    from semval.tagging.runner import run_tagging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    setup, spec, skipped = _resolve_setup(args)
    files = [f.as_posix() for f in setup.few_shot_files]
    if args.dry_run:
        print(f"setup: {args.tagger}")
        if setup.description:
            print(f"description: {setup.description}")
        print(f"spec: {spec.model_dump_json()}")
        print(f"few-shot files: {', '.join(files) or 'none (zero-shot)'}")
        for p in skipped:
            print(f"skipped (not found): {p.as_posix()}")
        if skipped and not files:
            print("no few-shot file found: this run would be zero-shot")
        return 0
    try:
        few_shot = load_fewshot_files(setup.few_shot_files)
    except (OSError, ValueError) as e:
        raise SystemExit(f"cannot load few-shot examples: {e}") from None
    try:
        m = run_tagging(
            spec,
            args.sample,
            run_id=args.run_id,
            limit=args.limit,
            limit_per_country=args.limit_per_country,
            few_shot=few_shot,
            few_shot_files=files,
            setup_name=args.tagger,
        )
    except (OSError, ValueError) as e:
        raise SystemExit(f"error: {e}") from None
    return _report_run(m)


def _report_run(m: Any) -> int:
    from semval.tagging.base import RunStatus

    u = m.usage_totals
    print(f"run {m.run_id}: {m.status}, {len(m.segments_done)} segments done")
    print(
        f"tokens: in={u.input_tokens} out={u.output_tokens} "
        f"cache_write={u.cache_creation_input_tokens} cache_read={u.cache_read_input_tokens}"
    )
    print(
        f"cost: ${m.cost_usd:.4f}; refused: {len(m.refused_segments)}; "
        f"failed: {len(m.failures)}; served by a fallback model: {len(m.served_by)}"
    )
    exit_codes = {RunStatus.DONE: 0, RunStatus.FAILED: 1, RunStatus.STOPPED_BUDGET: 3}
    return exit_codes.get(m.status, 1)


def _review(args: argparse.Namespace) -> int:
    from semval.review.session import open_session
    from semval.review.texts import ReviewSource

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.source == ReviewSource.TOUCHE23_FEWSHOT:
        return _serve(_fewshot_session(args), args)
    if not args.run:
        raise SystemExit("give at least one --run RUN_ID (repeat it to pool several runs)")
    try:
        session = open_session(args.run, blind=args.blind, labeller=args.labeller)
    except ValueError as e:
        raise SystemExit(str(e)) from None
    return _serve(session, args)


def _serve(session: Any, args: argparse.Namespace) -> int:
    from semval.review.server import serve

    try:
        serve(session, args.port, open_browser=args.open)
    except OSError as e:
        raise SystemExit(f"cannot serve on 127.0.0.1:{args.port}: {e}") from None
    return 0


def _fewshot_session(args: argparse.Namespace) -> Any:
    from semval.datasets.touche23 import DEFAULT_DIR, load_split
    from semval.review.fewshot_session import open_candidate_session
    from semval.tagging.fewshot_candidates import SELECTION_SPLITS, load_candidates

    candidates = load_candidates(DEFAULT_DIR)
    if not candidates:
        raise SystemExit("no candidates yet: run `semval fewshot candidates` first")
    items = [i for s in SELECTION_SPLITS for i in load_split(s, DEFAULT_DIR)]
    return open_candidate_session(candidates, items, labeller=args.labeller)


def _fewshot_candidates(args: argparse.Namespace) -> int:
    from semval.review.fewshot_session import FRAMEWORK_ID
    from semval.tagging.claude import make_client
    from semval.tagging.fewshot_candidates import (
        FewShotDrafter,
        draft_candidates,
        load_candidates,
        select_candidates,
    )
    from semval.tagging.ledger import BudgetExceeded, CostLedger
    from semval.values import FRAMEWORK_DIR, LEAF_LEVEL, load_framework

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ledger = CostLedger()
    ledger.total()  # fail closed on a damaged ledger before spending anything
    before = ledger.total()
    fw = load_framework(FRAMEWORK_DIR / f"{FRAMEWORK_ID}.yaml")
    drafter = FewShotDrafter(make_client(), ledger, fw.target_set(LEAF_LEVEL))
    items = select_candidates(args.n, args.seed, args.dir)
    try:
        path = draft_candidates(drafter, items, args.dir)
    except BudgetExceeded as e:
        print(f"stopped at the budget cap: {e}")
        return 3
    n = len(load_candidates(args.dir))
    print(f"{path}: {n} candidates; cost ${ledger.total() - before:.4f}")
    return 0


def _fewshot_finalize(args: argparse.Namespace) -> int:
    from semval.datasets.touche23 import load_split
    from semval.review.labels import LabelStore, label_paths
    from semval.tagging.fewshot import finalize, stance_counts, write_fewshot
    from semval.tagging.fewshot_candidates import SELECTION_SPLITS, load_candidates

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    candidates = load_candidates(args.dir)
    items = {i.id: i for s in SELECTION_SPLITS for i in load_split(s, args.dir)}
    store = LabelStore(label_paths(args.labels_dir, args.labeller)[0])
    examples = finalize(candidates, items, store.all(), args.labeller)
    if not examples:
        raise SystemExit("no judged candidates: review them first (--source touche23-fewshot)")
    write_fewshot(args.out, examples)
    print(f"{args.out}: {len(examples)} examples of {len(candidates)} candidates")
    print(f"tags by stance: {stance_counts(examples)}")
    return 0


def _fewshot_from_labels(args: argparse.Namespace) -> int:
    from semval.tagging.label_examples import assess, pick, write_local_fewshot
    from semval.tagging.runfiles import RunPaths

    paths = RunPaths(samples_dir=args.samples_dir, raw_dir=args.raw_dir, runs_dir=args.runs_dir)
    try:
        a = assess(args.run, args.labeller, paths=paths, labels_dir=args.labels_dir)
    except (OSError, ValueError) as e:
        raise SystemExit(str(e)) from None
    examples = pick(a.candidates, args.n)
    print(
        f"{len(a.candidates)} qualifying paragraphs of {a.paragraphs_with_reject_or_mention} "
        f"with a reject or mention tag; disqualified by rule: {dict(a.disqualified)}"
    )
    if not examples:
        raise SystemExit("no paragraph qualifies; nothing written")
    docs = write_local_fewshot(args.out, examples, run_id=args.run, labeller=args.labeller)
    from collections import Counter

    langs = Counter(e.language for e in examples)
    stances = Counter(t.stance for e in examples for t in e.tags)
    print(f"{args.out}: {len(examples)} examples (local only, not for commit)")
    print(f"by language: {dict(langs)}; tags by stance: {dict(stances)}")
    print(f"source documents (exclude from scoring): {docs}")
    return 0


def _touche_download(args: argparse.Namespace) -> int:
    from semval.datasets.touche23 import download, load_split

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    download(args.dir)
    for split in ("train", "validation", "test"):
        print(f"{split}: {len(load_split(split, args.dir))} items")
    return 0


def _touche_build_proxy(args: argparse.Namespace) -> int:
    from semval.datasets.touche23 import ClaudeTranslator, build_greek_proxy, load_proxy
    from semval.tagging.claude import make_client
    from semval.tagging.ledger import BudgetExceeded, CostLedger

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ledger = CostLedger()
    ledger.total()  # fail closed on a damaged ledger before spending anything
    before = ledger.total()
    translator = ClaudeTranslator(make_client(), ledger)
    try:
        path = build_greek_proxy(
            translator, n=args.n, seed=args.seed, split=args.split, data_dir=args.dir
        )
    except BudgetExceeded as e:
        print(f"stopped at the budget cap: {e}")
        return 3
    print(f"{path}: {len(load_proxy(args.dir))} items; cost ${ledger.total() - before:.4f}")
    return 0


def _touche_make_sample(args: argparse.Namespace) -> int:
    from semval.datasets.touche23_samples import make_touche_sample
    from semval.tagging.runfiles import load_sample

    path = make_touche_sample(
        args.name, split=args.split, n=args.n, seed=args.seed, proxy=args.proxy, data_dir=args.dir
    )
    sample = load_sample(args.name, path.parent)
    print(f"{path}: {len(sample.documents)} documents")
    return 0


def _touche_gold_for_evaluate(fw: Any, data_dir: Path) -> Any:
    from semval.datasets.touche23_samples import touche_gold

    return lambda sample, level: touche_gold(sample, fw, level, data_dir)


def _evaluate(args: argparse.Namespace) -> int:
    from semval.evaluation.report import EvalSetup, build_results, write_report
    from semval.review.labels import LabelStore, label_paths
    from semval.tagging.runfiles import RunPaths, load_run
    from semval.values import load_framework

    paths = RunPaths(
        samples_dir=args.samples_dir,
        raw_dir=args.raw_dir,
        framework_dir=args.framework_dir,
        runs_dir=args.runs_dir,
    )
    try:
        framework_id = load_run(args.runs_dir, args.run[0]).spec.framework_id
        fw = load_framework(args.framework_dir / f"{framework_id}.yaml")
        setup = EvalSetup(
            framework=fw,
            paths=paths,
            labels=LabelStore(label_paths(args.labels_dir, args.labeller)[0]).all(),
            gold=_touche_gold_for_evaluate(fw, args.touche_dir),
            en_sample=args.en_sample,
            el_sample=args.el_sample,
            owner_sample=args.owner_sample,
            scoring_level=args.scoring_level,
        )
        results = build_results(args.run, setup)
    except (OSError, ValueError) as e:
        raise SystemExit(str(e)) from None
    out = write_report(results, args.out, args.scoring_level)
    print(f"{out}: {len(results)} configurations from {len(args.run)} runs")
    return 0


def _sample_derive(args: argparse.Namespace) -> int:
    from semval.sampling.sample import derive_sample, write_manifest
    from semval.tagging.runfiles import load_sample

    ids = list(args.id)
    if args.ids_file:
        ids += [
            x.strip() for x in args.ids_file.read_text(encoding="utf-8").splitlines() if x.strip()
        ]
    try:
        manifest = derive_sample(load_sample(args.base, DEFAULT_SAMPLES_DIR), args.name, ids)
    except ValueError as e:
        raise SystemExit(str(e)) from e
    print(f"{write_manifest(manifest, DEFAULT_SAMPLES_DIR)}: {len(manifest.documents)} documents")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="semval")
    sub = parser.add_subparsers(dest="command", required=True)
    cov = sub.add_parser("coverage", help="write the source coverage report")
    cov.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    cov.add_argument("--out", type=Path, default=DEFAULT_OUT)
    cov.add_argument(
        "--year",
        type=int,
        default=date.today().year,
        help="year that open-ended sources and the last period run to (default: this year)",
    )
    cov.set_defaults(func=_coverage)

    smp = sub.add_parser("sample", help="collect an opinion sample through the source adapters")
    smp.add_argument("--countries", nargs="+", default=[], help="ISO codes, e.g. GR GB")
    smp.add_argument("--source", nargs="+", default=[], help="source ids (default: by country)")
    smp.add_argument("--per-country", type=int, default=40)
    smp.add_argument("--since", type=date.fromisoformat, required=True)
    smp.add_argument("--until", type=date.fromisoformat, default=date.today())
    smp.add_argument("--name", required=True, help="writes data/samples/<name>.yaml")
    smp.add_argument("--sources", type=Path, default=DEFAULT_SOURCES, help="registry file")
    smp.add_argument("--max-requests", type=int, default=600, help="stop after this many")
    smp.set_defaults(func=_sample)

    from semval.config import Effort
    from semval.models import registry
    from semval.units import UnitLevel

    tag = sub.add_parser(
        "tag",
        help="tag a sample with a saved setup (resumable; see data/runs/)",
        description="Start from a saved setup (data/taggers/NAME.yaml) and override single "
        "fields with the flags. Exit status: 0 done, 1 failed segments or error, "
        "3 stopped at the budget cap.",
    )
    tag.add_argument("--sample", required=True, help="name of data/samples/<name>.yaml")
    tag.add_argument(
        "--tagger", default="sonnet-high", help="saved setup name (default: %(default)s)"
    )
    tag.add_argument("--model", type=str, choices=registry().requestable())
    tag.add_argument("--effort", type=Effort, choices=list(Effort))
    tag.add_argument("--level", help="framework level id, e.g. leaf")
    tag.add_argument("--unit", type=UnitLevel, choices=list(UnitLevel))
    tag.add_argument("--framework", help="framework id")
    tag.add_argument("--prompt", help="prompt id, a file in data/prompts")
    tag.add_argument(
        "--few-shot-file",
        type=Path,
        action="append",
        help="YAML few-shot examples; repeat to concatenate in order (replaces the setup's list)",
    )
    tag.add_argument(
        "--no-few-shot", action="store_true", help="zero-shot, whatever the setup says"
    )
    tag.add_argument(
        "--batch",
        action=argparse.BooleanOptionalAction,
        help="use Message Batches (50%% cost)",
    )
    tag.add_argument(
        "--option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="kind-specific setting, e.g. lexicon_file=PATH; repeatable; true/false, "
        "integers and decimals are read as such",
    )
    tag.add_argument("--limit-per-country", type=int, help="documents per country")
    tag.add_argument("--limit", type=int, help="documents in all")
    tag.add_argument("--run-id", help="resume this run, or name a new one")
    tag.add_argument(
        "--dry-run", action="store_true", help="print the resolved setup and spec; run nothing"
    )
    tag.set_defaults(func=_tag)

    from semval.review.texts import ReviewSource

    rev = sub.add_parser(
        "review",
        help="open the local review page (http://127.0.0.1 only) to judge tags",
        description="Verdicts autosave to data/labels/<labeller>/labels.jsonl.",
    )
    rev.add_argument("--run", action="append", default=[], help="run id; repeat to pool runs")
    rev.add_argument(
        "--blind", action="store_true", help="only unjudged tags, without saying which run"
    )
    rev.add_argument(
        "--labeller", default=DEFAULT_LABELLER, help=f"who is judging (default: {DEFAULT_LABELLER})"
    )
    rev.add_argument("--port", type=int, default=8765, help="0 picks a free port")
    rev.add_argument(
        "--source", type=ReviewSource, choices=list(ReviewSource), default=ReviewSource.RUNS
    )
    rev.add_argument("--open", action="store_true", help="open the page in the browser")
    rev.set_defaults(func=_review)
    from semval.datasets.touche23 import DEFAULT_DIR as TOUCHE_DIR

    fsh = sub.add_parser("fewshot", help="Touché23 few-shot examples: draft, then finalize")
    fsh_sub = fsh.add_subparsers(dest="fewshot_command", required=True)
    cd = fsh_sub.add_parser(
        "candidates",
        help="select items and draft stances with Claude (costs money; resumable)",
        description="Exit status: 0 done, 3 stopped at the budget cap.",
    )
    cd.add_argument("--n", type=int, default=20)
    cd.add_argument("--seed", type=int, default=1)
    cd.add_argument("--dir", type=Path, default=TOUCHE_DIR)
    cd.set_defaults(func=_fewshot_candidates)
    fz = fsh_sub.add_parser("finalize", help="write the owner-confirmed examples to YAML")
    fz.add_argument("--labeller", default=DEFAULT_LABELLER)
    fz.add_argument("--dir", type=Path, default=TOUCHE_DIR)
    fz.add_argument("--labels-dir", type=Path, default=DEFAULT_LABELS_DIR)
    fz.add_argument("--out", type=Path, default=DEFAULT_FEWSHOT_PATH)
    fz.set_defaults(func=_fewshot_finalize)

    fl = fsh_sub.add_parser(
        "from-labels",
        help="local in-domain examples from paragraphs the owner confirmed (never committed)",
    )
    fl.add_argument("--run", required=True, help="paragraph-unit run id")
    fl.add_argument("--labeller", default=DEFAULT_LABELLER)
    fl.add_argument("--n", type=int, default=6)
    fl.add_argument("--out", type=Path, default=DEFAULT_LOCAL_FEWSHOT_PATH)
    fl.add_argument("--labels-dir", type=Path, default=DEFAULT_LABELS_DIR)
    fl.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    fl.add_argument("--samples-dir", type=Path, default=DEFAULT_SAMPLES_DIR)
    fl.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    fl.set_defaults(func=_fewshot_from_labels)

    tou = sub.add_parser("touche23", help="Touché23-ValueEval data and the Greek proxy")
    tou_sub = tou.add_subparsers(dest="touche_command", required=True)
    dl = tou_sub.add_parser("download", help="fetch the raw TSVs (CC BY 4.0) from Zenodo")
    dl.add_argument("--dir", type=Path, default=TOUCHE_DIR)
    dl.set_defaults(func=_touche_download)
    bp = tou_sub.add_parser(
        "build-proxy",
        help="machine-translate a seeded sample into Greek with Claude (costs money)",
        description="Exit status: 0 done, 3 stopped at the budget cap.",
    )
    bp.add_argument("--n", type=int, default=100)
    bp.add_argument("--seed", type=int, default=1)
    bp.add_argument("--split", choices=["train", "validation", "test"], default="test")
    bp.add_argument("--dir", type=Path, default=TOUCHE_DIR)
    bp.set_defaults(func=_touche_build_proxy)
    ms = tou_sub.add_parser(
        "make-sample", help="the split (or the Greek proxy) as a sample for `semval tag`"
    )
    ms.add_argument("--name", required=True)
    ms.add_argument("--split", choices=["train", "validation", "test"], default="test")
    ms.add_argument("--n", type=int, default=300)
    ms.add_argument("--seed", type=int, default=1)
    ms.add_argument("--proxy", action="store_true", help="exactly the Greek proxy items")
    ms.add_argument("--dir", type=Path, default=TOUCHE_DIR)
    ms.set_defaults(func=_touche_make_sample)

    sd = sub.add_parser("sample-derive", help="a new sample of chosen documents of another")
    sd.add_argument("--from", dest="base", required=True, help="name of the base sample")
    sd.add_argument("--name", required=True)
    sd.add_argument("--id", action="append", default=[], help="document id (repeatable)")
    sd.add_argument("--ids-file", type=Path, help="file with one document id per line")
    sd.set_defaults(func=_sample_derive)

    from semval.evaluation.report import (
        DEFAULT_EL_SAMPLE,
        DEFAULT_EN_SAMPLE,
        DEFAULT_OWNER_SAMPLE,
        SCORING_LEVEL,
    )
    from semval.evaluation.report import (
        DEFAULT_OUT as DEFAULT_EVAL_OUT,
    )
    from semval.values import FRAMEWORK_DIR as FW_DIR

    ev = sub.add_parser(
        "evaluate",
        help="score tagging runs and write the evaluation report",
        description="Groups runs into configurations by spec; each input is told by the "
        "run's input_sample.",
    )
    ev.add_argument("--run", action="append", required=True, help="run id; repeat for all runs")
    ev.add_argument("--labeller", default=DEFAULT_LABELLER, help="whose labels are the stance gold")
    ev.add_argument("--out", type=Path, default=DEFAULT_EVAL_OUT)
    ev.add_argument("--scoring-level", default=SCORING_LEVEL)
    ev.add_argument("--en-sample", default=DEFAULT_EN_SAMPLE)
    ev.add_argument("--el-sample", default=DEFAULT_EL_SAMPLE)
    ev.add_argument("--owner-sample", default=DEFAULT_OWNER_SAMPLE)
    ev.add_argument("--labels-dir", type=Path, default=DEFAULT_LABELS_DIR)
    ev.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    ev.add_argument("--samples-dir", type=Path, default=DEFAULT_SAMPLES_DIR)
    ev.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    ev.add_argument("--framework-dir", type=Path, default=FW_DIR)
    ev.add_argument("--touche-dir", type=Path, default=TOUCHE_DIR)
    ev.set_defaults(func=_evaluate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
