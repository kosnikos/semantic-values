"""What an adapter returns for one article page, and how it says "skip this page"."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class Genre(StrEnum):
    """Genres kept in an opinion sample. Any other genre string means "skip"."""

    OPINION = "opinion"
    LETTERS = "letters"
    COLUMNS = "columns"
    EDITORIAL = "editorial"


@dataclass(frozen=True)
class ParsedArticle:
    title: str
    date: date | None
    genre: str  # a Genre value to keep the article; anything else is skipped
    text: str


class ParseError(ValueError):
    """The page is not an article the adapter can read."""


class OutOfScope(ParseError):
    """The page is a readable article, but outside the source's scope (e.g. another edition)."""
