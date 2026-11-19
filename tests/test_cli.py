from pathlib import Path

import yaml

from conftest import make_source
from semval.cli import main, render_coverage_md
from semval.sources import (
    EXCLUDED_SOURCE_TYPES,
    JURISDICTION_OPEN_SCOPES,
    OPEN_SCOPES,
    OVERRIDE_EXCLUDED_ACCESS_METHODS,
    PERIODS,
    V0_COUNTRIES,
    Source,
    load_sources,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "sources" / "sources.yaml"
COVERAGE_MD = ROOT / "docs" / "research" / "coverage.md"
COVERAGE_YEAR = 2026  # year docs/research/coverage.md was generated for


def render(entries: list[dict]) -> str:
    return render_coverage_md([Source(**e) for e in entries], 2026)


def open_note(md: str) -> str:
    return md.split("## Usable and not opted out")[1].split("| Country |")[0]


def test_render_has_table() -> None:
    md = render([])
    assert "| Country | 1940-1969 | 1970-1989 | 1990-2004 | 2005-now |" in md
    for c in V0_COUNTRIES:
        assert f"| {c} | 0 | 0 | 0 | 0 |" in md
    assert [p[0] for p in PERIODS] == ["1940-1969", "1970-1989", "1990-2004", "2005-now"]


def test_render_counts_usable_sources() -> None:
    md = render([make_source(country="GR", year_start=1950, year_end=1975)])
    assert "| GR | 1 | 1 | 0 | 0 |" in md


def test_render_lists_open_questions() -> None:
    md = render([make_source(id="gr-x", llm_api_allowed="unknown")])
    assert "## Open questions" in md
    tail = md.split("## Open questions")[1]
    assert "gr-x" in tail
    assert "llm_api_allowed" in tail


def test_render_no_open_questions() -> None:
    md = render([make_source(llm_api_allowed="yes", per_text_publish_allowed="no")])
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


def test_render_has_two_tables() -> None:
    md = render([make_source(country="FR", restriction_scope="tdm_all", year_start=2010,
                             year_end=None)])  # fmt: skip
    assert "## Usable (free access)" in md
    assert "## Usable and not opted out" in md
    free, rest = md.split("## Usable (free access)")[1].split("## Usable and not opted out")
    opened = rest.split("## Open questions")[0]
    assert "| FR | 0 | 0 | 0 | 1 |" in free
    assert "| FR | 0 | 0 | 0 | 0 |" in opened
    assert "s.29A" in opened


def test_render_lists_unknown_restriction_scope() -> None:
    md = render([make_source(id="gr-u", llm_api_allowed="yes", per_text_publish_allowed="yes",
                             restriction_scope="unknown")])  # fmt: skip
    tail = md.split("## Open questions")[1]
    assert "- gr-u: restriction_scope" in tail


def test_open_note_generated_from_constants() -> None:
    note = open_note(render([]))
    for scope in OPEN_SCOPES - {"unknown"}:
        assert f"`{scope}`" in note
    assert "`unknown` counts as open but is unverified" in note
    for country, scopes in JURISDICTION_OPEN_SCOPES.items():
        assert country in note
        for scope in scopes:
            assert f"`{scope}`" in note
    for method in OVERRIDE_EXCLUDED_ACCESS_METHODS:
        assert f"`{method}`" in note
    for source_type in EXCLUDED_SOURCE_TYPES:
        assert f"`{source_type}`" in note


def test_cli_year_option(tmp_path: Path) -> None:
    src = tmp_path / "sources.yaml"
    src.write_text(yaml.safe_dump([make_source(country="GR", year_start=2020, year_end=None)]),
                   encoding="utf-8")  # fmt: skip
    out = tmp_path / "coverage.md"
    assert main(["coverage", "--sources", str(src), "--out", str(out), "--year", "2010"]) == 0
    assert "| GR | 0 | 0 | 0 | 0 |" in out.read_text(encoding="utf-8")
    assert main(["coverage", "--sources", str(src), "--out", str(out), "--year", "2026"]) == 0
    assert "| GR | 0 | 0 | 0 | 1 |" in out.read_text(encoding="utf-8")


def test_coverage_md_is_fresh() -> None:
    """docs/research/coverage.md matches the registry; regenerate with
    `python -m semval coverage --year 2026` if this fails."""

    def body(md: str) -> list[str]:
        return [ln for ln in md.splitlines() if not ln.startswith("Generated from ")]

    expected = render_coverage_md(load_sources(REGISTRY), COVERAGE_YEAR)
    assert body(COVERAGE_MD.read_text(encoding="utf-8")) == body(expected)
