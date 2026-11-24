"""Shared test helpers. pytest puts this directory on sys.path, so tests import from it."""

from pathlib import Path

import yaml


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


def make_value(**overrides) -> dict:
    base = {
        "id": "alpha",
        "name": "Alpha",
        "definition": "Wanting alpha things.",
        "opposes": [],
        "examples_endorse": ["Alpha is good."],
        "examples_reject": ["Alpha is overrated."],
    }
    base.update(overrides)
    return base


def toy_values() -> list[dict]:
    return [
        make_value(id="group_a", name="Group A", definition="The A side."),
        make_value(id="group_b", name="Group B", definition="The B side."),
        make_value(id="alpha", parent="group_a", opposes=["beta"]),
        make_value(id="beta", name="Beta", parent="group_b", opposes=["alpha"]),
    ]


def write_framework(
    tmp_path: Path, values: list[dict], fid: str = "toy", levels: list[dict] | None = None
) -> Path:
    path = tmp_path / f"{fid}.yaml"
    doc: dict = {"id": fid, "name": "Toy framework", "citation": "Nobody (2026).", "values": values}
    if levels is not None:
        doc["levels"] = levels
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return path
