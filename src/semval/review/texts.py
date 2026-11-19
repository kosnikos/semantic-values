"""Where the review page gets article texts from. The server never reads files itself.

``RawDocsProvider`` serves sample documents from the git-ignored raw cache. Other sources
(the Touché23 few-shot candidates) implement the same protocol.
"""

import json
from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from semval.sampling.sample import DEFAULT_RAW_DIR, DEFAULT_SAMPLES_DIR, doc_meta_path
from semval.tagging.runfiles import load_sample, read_text
from semval.units import Document


class ReviewSource(StrEnum):
    """What the review page shows: tagging runs over sample documents, or the Touché23
    few-shot candidates."""

    RUNS = "runs"
    TOUCHE23_FEWSHOT = "touche23-fewshot"


class TextUnavailable(Exception):
    """The provider has no usable text for a document."""


class DocInfo(BaseModel):
    """What the page header shows about a document. Every field is optional."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    country: str | None = None
    source_id: str | None = None
    genre: str | None = None
    language: str | None = None
    date: str | None = None
    url: str | None = None


@runtime_checkable
class TextProvider(Protocol):
    """Texts and header details of the documents under review. Neither method writes.

    ``text(document_id)`` returns the exact text that tag offsets index into, or raises
    ``TextUnavailable`` (the page shows the error; the table still works).

    ``info(document_id)`` returns the header details as a ``DocInfo``: fill what the source
    knows (title, country, source_id, genre, language, date, url) and leave the rest
    ``None``. It may raise ``TextUnavailable``; the header is then empty.
    """

    def text(self, document_id: str) -> str: ...

    def info(self, document_id: str) -> DocInfo: ...


class RawDocsProvider:
    """Sample documents: text from the raw cache (checked against its hash), the title from
    the ``.meta.json`` beside it."""

    def __init__(self, documents: Iterable[Document], raw_dir: Path = DEFAULT_RAW_DIR):
        self._docs = {d.id: d for d in documents}
        self._raw_dir = Path(raw_dir)

    @classmethod
    def from_samples(
        cls,
        sample_names: Iterable[str],
        samples_dir: Path = DEFAULT_SAMPLES_DIR,
        raw_dir: Path = DEFAULT_RAW_DIR,
    ) -> "RawDocsProvider":
        names = dict.fromkeys(sample_names)
        return cls((d for n in names for d in load_sample(n, samples_dir).documents), raw_dir)

    def _doc(self, document_id: str) -> Document:
        doc = self._docs.get(document_id)
        if doc is None:
            raise TextUnavailable(f"{document_id} is not in the run samples")
        return doc

    def text(self, document_id: str) -> str:
        doc = self._doc(document_id)
        try:
            return read_text(self._raw_dir, doc)
        except FileNotFoundError:
            raise TextUnavailable(f"{document_id}: no cached text in {self._raw_dir}") from None
        except ValueError as e:
            raise TextUnavailable(str(e)) from None

    def info(self, document_id: str) -> DocInfo:
        doc = self._doc(document_id)
        title = doc.title
        meta = doc_meta_path(self._raw_dir, document_id)
        if meta.exists():
            title = json.loads(meta.read_text(encoding="utf-8")).get("title") or title
        return DocInfo(
            title=title, country=doc.country, source_id=doc.source_id, genre=doc.genre,
            language=doc.language, date=doc.date.isoformat() if doc.date else None, url=doc.url,
        )  # fmt: skip
