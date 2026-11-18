"""Command-line interface for semval."""

import argparse
from datetime import date
from pathlib import Path

from semval.sources import PERIODS, V0_COUNTRIES, Source, coverage_matrix, load_sources

DEFAULT_SOURCES = Path("data/sources/sources.yaml")
DEFAULT_OUT = Path("docs/research/coverage.md")
_TRI_FIELDS = ("llm_api_allowed", "per_text_publish_allowed", "tdm_opt_out")


def render_coverage_md(
    matrix: dict[str, dict[str, list[str]]],
    sources: list[Source],
    sources_path: str = DEFAULT_SOURCES.as_posix(),
) -> str:
    labels = [label for label, _, _ in PERIODS]
    lines = [
        "# Source coverage",
        "",
        f"Generated from {sources_path}",
        "",
        "Cells show the number of usable (free or free-registration) sources per period.",
        "",
        "| Country | " + " | ".join(labels) + " |",
        "|---|" + "---|" * len(labels),
    ]
    for country, row in matrix.items():
        lines.append(f"| {country} | " + " | ".join(str(len(row[lb])) for lb in labels) + " |")
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
    matrix = coverage_matrix(sources, V0_COUNTRIES, date.today().year)
    md = render_coverage_md(matrix, sources, args.sources.as_posix())
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
