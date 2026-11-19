"""Command-line interface for semval."""

import argparse
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
