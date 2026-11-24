"""The SourceAdapter protocol. Each adapter module implements it for one source."""

from collections.abc import Iterable
from datetime import date
from typing import Protocol

from semval.sampling.article import Genre, OutOfScope, ParsedArticle, ParseError
from semval.sampling.fetch import PoliteFetcher

__all__ = ["Genre", "OutOfScope", "ParseError", "ParsedArticle", "SourceAdapter"]


class SourceAdapter(Protocol):
    source_id: str

    def list_candidates(
        self, fetcher: PoliteFetcher, since: date, until: date
    ) -> Iterable[str]: ...

    def parse(self, url: str, html: str) -> ParsedArticle: ...
