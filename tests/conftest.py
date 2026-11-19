"""Shared test helpers. pytest puts this directory on sys.path, so tests import from it."""


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
        "year_start_basis": "verified",
        "year_end_basis": "verified",
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
