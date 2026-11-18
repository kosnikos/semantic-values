"""Source registry model and coverage matrix.

Source-agnostic: every archive is described by data (YAML), not code.
"""

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

USABLE_ACCESS = {"free", "free_registration"}

PERIODS: list[tuple[str, int, int | None]] = [
    ("1940-1969", 1940, 1969),
    ("1970-1989", 1970, 1989),
    ("1990-2004", 1990, 2004),
    ("2005-now", 2005, None),
]

V0_COUNTRIES = ["FR", "NL", "BE", "LU", "DE", "AT", "CH", "IT", "GR", "ES", "PT", "GB"]

# ISO 3166-1 alpha-2 codes for Europe, plus US.
ISO_COUNTRIES = frozenset(
    ["AD", "AL", "AM", "AT", "AZ", "BA", "BE", "BG", "BY", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FO", "FR", "GB", "GE", "GI", "GR", "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV", "MC", "MD", "ME", "MK", "MT", "NL", "NO", "PL", "PT", "RO", "RS", "RU", "SE", "SI", "SK", "SM", "TR", "UA", "VA", "XK", "US"]
)

Tri = Literal["yes", "no", "unknown"]

RestrictionScope = Literal[
    "none", "ai_training_only", "crawler_block_only", "tdm_all", "all_reuse", "unknown"
]

# Scopes that do not exclude a source under the source-use rule (spec section 3).
OPEN_SCOPES: set[str] = {"none", "ai_training_only", "crawler_block_only", "unknown"}

# Extra scopes treated as open in a given jurisdiction. UK CDPA s.29A: contract terms
# restricting non-commercial research TDM are unenforceable; all_reuse stays closed.
JURISDICTION_OPEN_SCOPES: dict[str, set[str]] = {"GB": {"tdm_all"}}


class Source(BaseModel):
    id: str
    name: str
    country: str
    source_type: Literal[
        "newspaper_archive", "national_library", "web_archive", "news_api",
        "forum", "book_archive", "other",
    ]  # fmt: skip
    url: HttpUrl
    access: Literal["free", "free_registration", "partial_paywall", "paywall"]
    year_start: int
    year_end: int | None
    languages: list[str]
    genres: list[Literal["opinion", "letters", "columns", "news", "forum", "books", "other"]]
    access_method: Literal["api", "bulk", "scrape", "manual"]
    licence: str
    tdm_opt_out: Tri
    restriction_scope: RestrictionScope
    llm_api_allowed: Tri
    per_text_publish_allowed: Tri
    text_quality: Literal["born_digital", "ocr_good", "ocr_poor", "unknown"]
    volume_estimate: str
    verified_on: date
    evidence_urls: list[HttpUrl] = Field(min_length=1)
    notes: str = ""

    @field_validator("country")
    @classmethod
    def _country(cls, v: str) -> str:
        code = v.strip().upper()
        if code == "UK":
            raise ValueError("use GB for the United Kingdom")
        if code not in ISO_COUNTRIES:
            raise ValueError(f"unknown ISO 3166-1 alpha-2 country code: {v!r}")
        return code

    @model_validator(mode="after")
    def _years(self) -> "Source":
        if self.year_end is not None and self.year_end < self.year_start:
            raise ValueError("year_end must be >= year_start")
        return self


def load_sources(path: Path) -> list[Source]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    sources = [Source(**entry) for entry in raw]
    seen: set[str] = set()
    for s in sources:
        if s.id in seen:
            raise ValueError(f"duplicate source id: {s.id}")
        seen.add(s.id)
    return sources


def is_open(source: Source) -> bool:
    """True if the source's restriction scope does not exclude it in its jurisdiction."""
    allowed = OPEN_SCOPES | JURISDICTION_OPEN_SCOPES.get(source.country, set())
    return source.restriction_scope in allowed


def coverage_matrix(
    sources: list[Source], countries: list[str], current_year: int, open_only: bool = False
) -> dict[str, dict[str, list[str]]]:
    """Country -> period label -> ids of usable sources overlapping that period.

    With open_only, sources whose restriction scope excludes them are dropped too.
    """
    matrix: dict[str, dict[str, list[str]]] = {
        c: {label: [] for label, _, _ in PERIODS} for c in countries
    }
    for s in sources:
        if s.access not in USABLE_ACCESS or s.country not in matrix:
            continue
        if open_only and not is_open(s):
            continue
        s_end = current_year if s.year_end is None else s.year_end
        for label, p_start, p_end in PERIODS:
            end = current_year if p_end is None else p_end
            if s.year_start <= end and s_end >= p_start:
                matrix[s.country][label].append(s.id)
    return matrix
