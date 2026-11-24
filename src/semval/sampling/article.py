"""What an adapter returns for one article page, and how it says "skip this page"."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Final, Literal


class Genre(StrEnum):
    """Genres kept in an opinion sample."""

    OPINION = "opinion"
    LETTERS = "letters"
    COLUMNS = "columns"
    EDITORIAL = "editorial"


NotSampled = Literal["other"]
# The genre an adapter gives a page outside the sampled genres (news, sport, cartoons...).
NOT_SAMPLED: Final[NotSampled] = "other"


@dataclass(frozen=True)
class ParsedArticle:
    title: str
    date: date | None
    genre: Genre | NotSampled  # NOT_SAMPLED pages are skipped
    text: str


class ParseError(ValueError):
    """The page is not an article the adapter can read."""


class OutOfScope(ParseError):
    """The page is a readable article, but outside the source's scope (e.g. another edition)."""
