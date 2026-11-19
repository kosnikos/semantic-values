"""Generic text units: a document is cut into article, paragraph and sentence segments.

Segments are character spans of the document text, linked to their parent by id. Nothing
here knows about a source or a value framework.
"""

import datetime
import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator


class UnitLevel(StrEnum):
    ARTICLE = "article"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"

    @property
    def rank(self) -> int:
        """0 for the coarsest level (article); a higher rank is finer."""
        return list(UnitLevel).index(self)


class DocumentMeta(BaseModel):
    """What a tagger may know about a segment's document."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    language: str
    genre: str


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_id: str
    country: str
    language: str
    date: datetime.date | None = None
    genre: str
    url: str | None = None
    title: str | None = None
    # Committed samples carry only a hash of the title; the title itself stays in data/raw.
    title_sha256: str | None = None
    text_sha256: str

    def meta(self) -> DocumentMeta:
        return DocumentMeta(language=self.language, genre=self.genre)


class Segment(BaseModel):
    """A span ``text[start:end]`` of a document, at one level, inside an optional parent."""

    model_config = ConfigDict(extra="forbid")

    id: str
    document_id: str
    level: UnitLevel
    parent_id: str | None = None
    start: int
    end: int

    @model_validator(mode="after")
    def _span(self) -> "Segment":
        if not 0 <= self.start < self.end:
            raise ValueError(f"bad span {self.start}:{self.end} for segment {self.id}")
        return self


_PARAGRAPH_BREAK = re.compile(r"\n[^\S\n]*\n\s*")
# Sentence end punctuation (incl. the Greek question mark) + whitespace, then an uppercase
# Latin or Greek letter. Limits: a lowercase start, a digit or a quote after the full stop
# does not split, and an uppercase abbreviation ("Mr. Smith") does.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?;\u037e])\s+(?=[A-ZΆΈΉΊΌΎΏΑ-ΩΪΫ])")


def _trimmed(text: str, start: int, end: int) -> tuple[int, int] | None:
    piece = text[start:end]
    lead = len(piece) - len(piece.lstrip())
    stripped = piece.strip()
    if not stripped:
        return None
    return start + lead, start + lead + len(stripped)


def _split(text: str, start: int, end: int, pattern: re.Pattern[str]) -> list[tuple[int, int]]:
    """Cut ``text[start:end]`` at ``pattern`` matches into trimmed, non-empty spans."""
    spans, pos = [], start
    for m in pattern.finditer(text, start, end):
        spans.append(_trimmed(text, pos, m.start()))
        pos = m.end()
    spans.append(_trimmed(text, pos, end))
    return [s for s in spans if s]


def segment(doc_id: str, text: str, level: UnitLevel) -> list[Segment]:
    """Segments down to ``level``, coarse to fine, so every parent id resolves.

    Ids are ``{doc}:a``, ``{doc}:p{i}`` and ``{doc}:p{i}:s{j}``. Paragraphs split on blank
    lines; sentences by ``_SENTENCE_BREAK``. Blank text gives no segments.
    """
    article = _trimmed(text, 0, len(text))
    if article is None:
        return []
    art_id = f"{doc_id}:a"
    out = [
        Segment(
            id=art_id, document_id=doc_id, level=UnitLevel.ARTICLE, start=article[0], end=article[1]
        )
    ]
    if level.rank < UnitLevel.PARAGRAPH.rank:
        return out
    for i, (ps, pe) in enumerate(_split(text, *article, _PARAGRAPH_BREAK)):
        pid = f"{doc_id}:p{i}"
        out.append(
            Segment(
                id=pid,
                document_id=doc_id,
                level=UnitLevel.PARAGRAPH,
                parent_id=art_id,
                start=ps,
                end=pe,
            )
        )
        if level.rank < UnitLevel.SENTENCE.rank:
            continue
        for j, (ss, se) in enumerate(_split(text, ps, pe, _SENTENCE_BREAK)):
            out.append(
                Segment(
                    id=f"{pid}:s{j}",
                    document_id=doc_id,
                    level=UnitLevel.SENTENCE,
                    parent_id=pid,
                    start=ss,
                    end=se,
                )
            )
    return out
