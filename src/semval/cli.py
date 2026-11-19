"""Command-line interface for semval."""

import argparse
import logging
import typing
from datetime import date
from pathlib import Path

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


def _default_framework() -> str | None:
    """The framework id when exactly one framework file exists, else None."""
    from semval.values import FRAMEWORK_DIR

    files = sorted(FRAMEWORK_DIR.glob("*.yaml"))
    return files[0].stem if len(files) == 1 else None


def _tag(args: argparse.Namespace) -> int:
    from semval.tagging.base import RunStatus, TaggerKind, TaggerSpec
    from semval.tagging.claude import make_client
    from semval.tagging.runner import load_few_shot, run_tagging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    few_shot = []
    if args.few_shot == "on":
        if args.few_shot_file is None:
            raise SystemExit("--few-shot on needs --few-shot-file PATH (no default file yet)")
        few_shot = load_few_shot(args.few_shot_file)
    framework = args.framework or _default_framework()
    if framework is None:
        raise SystemExit("several framework files exist: pass --framework ID")
    spec = TaggerSpec(
        kind=TaggerKind.CLAUDE,
        model=args.model,
        effort=args.effort,
        framework_id=framework,
        level_id=args.level,
        unit=args.unit,
        few_shot=args.few_shot == "on",
        batch=args.batch,
    )
    m = run_tagging(
        spec,
        args.sample,
        run_id=args.run_id,
        limit=args.limit,
        limit_per_country=args.limit_per_country,
        client=make_client(),
        few_shot=few_shot,
    )
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
    from semval.review.server import serve
    from semval.review.session import open_session
    from semval.review.texts import ReviewSource

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.source == ReviewSource.TOUCHE23_FEWSHOT:
        raise SystemExit(
            "--source touche23-fewshot is not available yet: it needs the Touché23 loader"
        )
    if not args.run:
        raise SystemExit("give at least one --run RUN_ID (repeat it to pool several runs)")
    try:
        session = open_session(args.run, blind=args.blind, labeller=args.labeller)
    except ValueError as e:
        raise SystemExit(str(e)) from None
    try:
        serve(session, args.port, open_browser=args.open)
    except OSError as e:
        raise SystemExit(f"cannot serve on 127.0.0.1:{args.port}: {e}") from None
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

    from semval.config import Effort, ModelId
    from semval.units import UnitLevel

    tag = sub.add_parser(
        "tag",
        help="tag a sample with Claude (resumable; see data/runs/)",
        description="Exit status: 0 done, 1 failed segments or error, 3 stopped at the budget cap.",
    )
    tag.add_argument("--sample", required=True, help="name of data/samples/<name>.yaml")
    tag.add_argument("--model", type=ModelId, choices=list(ModelId), required=True)
    tag.add_argument("--effort", type=Effort, choices=list(Effort), required=True)
    tag.add_argument("--level", required=True, help="framework level id, e.g. leaf")
    tag.add_argument("--unit", type=UnitLevel, choices=list(UnitLevel), required=True)
    tag.add_argument("--framework", help="framework id (default: the only framework file)")
    tag.add_argument("--few-shot", choices=["on", "off"], default="off")
    tag.add_argument("--few-shot-file", type=Path, help="YAML few-shot examples")
    tag.add_argument("--batch", action="store_true", help="use Message Batches (50%% cost)")
    tag.add_argument("--limit-per-country", type=int, help="documents per country")
    tag.add_argument("--limit", type=int, help="documents in all")
    tag.add_argument("--run-id", help="resume this run, or name a new one")
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
    rev.add_argument("--labeller", default="owner", help="who is judging (default: owner)")
    rev.add_argument("--port", type=int, default=8765, help="0 picks a free port")
    rev.add_argument(
        "--source", type=ReviewSource, choices=list(ReviewSource), default=ReviewSource.RUNS
    )
    rev.add_argument("--open", action="store_true", help="open the page in the browser")
    rev.set_defaults(func=_review)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
