from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from semval.sources import (
    PERIODS,
    V0_COUNTRIES,
    Source,
    coverage_matrix,
    is_open,
    load_sources,
)


def make_source(**overrides) -> dict:
    base = {
        "id": "src-1",
        "name": "Test Source",
        "country": "GR",
        "source_type": "newspaper_archive",
        "url": "https://example.org/",
        "access": "free",
        "year_start": 1950,
        "year_end": 2000,
        "languages": ["el"],
        "genres": ["opinion"],
        "access_method": "bulk",
        "licence": "CC-BY",
        "tdm_opt_out": "no",
        "restriction_scope": "none",
        "llm_api_allowed": "unknown",
        "per_text_publish_allowed": "unknown",
        "text_quality": "ocr_good",
        "volume_estimate": "1M pages",
        "verified_on": "2026-11-18",
        "evidence_urls": ["https://example.org/terms"],
    }
    base.update(overrides)
    return base


def write(tmp_path: Path, entries: list[dict]) -> Path:
    p = tmp_path / "sources.yaml"
    p.write_text(yaml.safe_dump(entries), encoding="utf-8")
    return p


def test_valid_source_loads(tmp_path):
    out = load_sources(write(tmp_path, [make_source()]))
    assert len(out) == 1
    assert out[0].country == "GR"


def test_empty_file_loads(tmp_path):
    assert load_sources(write(tmp_path, [])) == []


def test_country_code_normalisation():
    assert Source(**make_source(country="gb")).country == "GB"
    with pytest.raises(ValidationError, match="GB"):
        Source(**make_source(country="UK"))
    with pytest.raises(ValidationError):
        Source(**make_source(country="XX"))


def test_year_order():
    with pytest.raises(ValidationError):
        Source(**make_source(year_start=2010, year_end=2005))


def test_unknown_enum_rejected():
    with pytest.raises(ValidationError):
        Source(**make_source(access="maybe"))


def test_duplicate_ids_rejected(tmp_path):
    p = write(tmp_path, [make_source(id="guardian"), make_source(id="guardian")])
    with pytest.raises(ValueError, match="guardian"):
        load_sources(p)


def src(**kw) -> Source:
    return Source(**make_source(**kw))


def test_partial_overlap_counts():
    s = src(id="a", country="GB", year_start=2010, year_end=2015)
    m = coverage_matrix([s], V0_COUNTRIES, 2026)
    assert m["GB"]["2005-now"] == ["a"]
    assert m["GB"]["1990-2004"] == []


def test_open_ended_source_counts_in_latest_period():
    s = src(id="a", country="GB", year_start=1999, year_end=None)
    m = coverage_matrix([s], V0_COUNTRIES, 2026)
    assert m["GB"]["1990-2004"] == ["a"]
    assert m["GB"]["2005-now"] == ["a"]


def test_paywalled_not_counted():
    s = src(id="a", country="GB", access="paywall", year_start=1940, year_end=None)
    m = coverage_matrix([s], V0_COUNTRIES, 2026)
    assert all(m["GB"][label] == [] for label, _, _ in PERIODS)


def test_input_order_preserved():
    a = src(id="b", country="GB", year_start=2000, year_end=2010)
    b = src(id="a", country="GB", year_start=2000, year_end=2010)
    assert coverage_matrix([a, b], ["GB"], 2026)["GB"]["2005-now"] == ["b", "a"]


def test_all_countries_present():
    m = coverage_matrix([], V0_COUNTRIES, 2026)
    assert set(m) == set(V0_COUNTRIES)
    for c in V0_COUNTRIES:
        assert m[c] == {label: [] for label, _, _ in PERIODS}


def test_restriction_scope_required():
    entry = make_source()
    del entry["restriction_scope"]
    with pytest.raises(ValidationError, match="restriction_scope"):
        Source(**entry)
    with pytest.raises(ValidationError):
        Source(**make_source(restriction_scope="maybe"))


def test_open_only_excludes_tdm_all():
    s = src(id="fr-x", country="FR", access="free", restriction_scope="tdm_all",
            year_start=2010, year_end=None)  # fmt: skip
    assert coverage_matrix([s], V0_COUNTRIES, 2026)["FR"]["2005-now"] == ["fr-x"]
    assert coverage_matrix([s], V0_COUNTRIES, 2026, open_only=True)["FR"]["2005-now"] == []


def test_gb_tdm_all_open_under_s29a():
    a = src(id="gb-tdm", country="GB", restriction_scope="tdm_all", year_start=2010, year_end=None)
    b = src(id="gb-reuse", country="GB", restriction_scope="all_reuse", year_start=2010,
            year_end=None)  # fmt: skip
    assert is_open(a) and not is_open(b)
    m = coverage_matrix([a, b], V0_COUNTRIES, 2026, open_only=True)
    assert m["GB"]["2005-now"] == ["gb-tdm"]
