"""Command-line interface for semval."""

import argparse
from datetime import date
from pathlib import Path

from semval.sources import PERIODS, V0_COUNTRIES, Source, coverage_matrix, is_open, load_sources

DEFAULT_SOURCES = Path("data/sources/sources.yaml")
DEFAULT_OUT = Path("docs/research/coverage.md")
_TRI_FIELDS = ("llm_api_allowed", "per_text_publish_allowed", "tdm_opt_out")


Matrix = dict[str, dict[str, list[str]]]

_FREE_NOTE = "Cells show the number of usable (free or free-registration) sources per period."
_OPEN_NOTE = (
    "As above, minus sources whose terms or an Art. 4(3) reservation forbid all TDM "
    "(`tdm_all`) or any reuse without licence (`all_reuse`); GB `tdm_all` and `all_reuse` "
    "count as open under CDPA s.29A. `copyright_boilerplate` (generic anti-republication "
    "wording) counts as open; this is an owner-adjustable setting (`OPEN_SCOPES`)."
)


def _table(matrix: Matrix) -> list[str]:
    labels = [label for label, _, _ in PERIODS]
    lines = ["| Country | " + " | ".join(labels) + " |", "|---|" + "---|" * len(labels)]
    for country, row in matrix.items():
        lines.append(f"| {country} | " + " | ".join(str(len(row[lb])) for lb in labels) + " |")
    return lines


def _filter_open(matrix: Matrix, sources: list[Source]) -> Matrix:
    open_ids = {s.id for s in sources if is_open(s)}
    return {c: {lb: [i for i in ids if i in open_ids] for lb, ids in row.items()}
            for c, row in matrix.items()}  # fmt: skip


def render_coverage_md(
    matrix: Matrix,
    sources: list[Source],
    sources_path: str = DEFAULT_SOURCES.as_posix(),
    open_matrix: Matrix | None = None,
) -> str:
    if open_matrix is None:
        open_matrix = _filter_open(matrix, sources)
    lines = [
        "# Source coverage",
        "",
        f"Generated from {sources_path}",
        "",
        "## Usable (free access)",
        "",
        _FREE_NOTE,
        "",
        *_table(matrix),
        "",
        "## Usable and not opted out",
        "",
        _OPEN_NOTE,
        "",
        *_table(open_matrix),
    ]
    lines += ["", "## Open questions", ""]
    open_items = []
    for s in sources:
        unknown = [f for f in _TRI_FIELDS if getattr(s, f) == "unknown"]
        if unknown:
            open_items.append(f"- {s.id}: {', '.join(unknown)}")
    lines += open_items or ["None."]
    return "\n".join(lines) + "\n"


def _coverage(args: argparse.Namespace) -> int:
    sources = load_sources(args.sources)
    year = date.today().year
    matrix = coverage_matrix(sources, V0_COUNTRIES, year)
    open_matrix = coverage_matrix(sources, V0_COUNTRIES, year, open_only=True)
    md = render_coverage_md(matrix, sources, args.sources.as_posix(), open_matrix)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md, encoding="utf-8")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="semval")
    sub = parser.add_subparsers(dest="command", required=True)
    cov = sub.add_parser("coverage", help="write the source coverage report")
    cov.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    cov.add_argument("--out", type=Path, default=DEFAULT_OUT)
    cov.set_defaults(func=_coverage)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
