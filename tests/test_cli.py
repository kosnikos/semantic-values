from pathlib import Path

import yaml
from tests.test_sources import make_source

from semval.cli import main, render_coverage_md
from semval.sources import PERIODS, V0_COUNTRIES, Source, coverage_matrix


def build(entries: list[dict]) -> tuple[dict, list[Source]]:
    sources = [Source(**e) for e in entries]
    return coverage_matrix(sources, V0_COUNTRIES, 2026), sources


def test_render_has_table() -> None:
    matrix, sources = build([])
    md = render_coverage_md(matrix, sources)
    assert "| Country | 1940-1969 | 1970-1989 | 1990-2004 | 2005-now |" in md
    for c in V0_COUNTRIES:
        assert f"| {c} | 0 | 0 | 0 | 0 |" in md
    assert [p[0] for p in PERIODS] == ["1940-1969", "1970-1989", "1990-2004", "2005-now"]


def test_render_counts_usable_sources() -> None:
    matrix, sources = build([make_source(country="GR", year_start=1950, year_end=1975)])
    md = render_coverage_md(matrix, sources)
    assert "| GR | 1 | 1 | 0 | 0 |" in md


def test_render_lists_open_questions() -> None:
    matrix, sources = build([make_source(id="gr-x", llm_api_allowed="unknown")])
    md = render_coverage_md(matrix, sources)
    assert "## Open questions" in md
    tail = md.split("## Open questions")[1]
    assert "gr-x" in tail
    assert "llm_api_allowed" in tail


def test_render_no_open_questions() -> None:
    matrix, sources = build([make_source(llm_api_allowed="yes", per_text_publish_allowed="no")])
    md = render_coverage_md(matrix, sources)
    assert md.split("## Open questions")[1].strip() == "None."


def test_cli_writes_file(tmp_path: Path) -> None:
    src = tmp_path / "sources.yaml"
    src.write_text(yaml.safe_dump([make_source()]), encoding="utf-8")
    out = tmp_path / "sub" / "coverage.md"
    assert main(["coverage", "--sources", str(src), "--out", str(out)]) == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# Source coverage"
    assert lines[1] == ""
    assert lines[2] == f"Generated from {src.as_posix()}"
