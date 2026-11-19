"""Owner verdicts on value tags, stored append-only as JSONL with ids and stances only.

One file per labeller: ``data/labels/<labeller>/labels.jsonl`` (verdicts) and
``notes.jsonl`` (per-article notes). Every save appends a line; reading resolves the last
write per key, so re-clicks and reloads are harmless. No article text is ever stored.
"""

import datetime
import json
import logging
import os
import threading
from collections.abc import Callable, Hashable
from enum import StrEnum
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from semval.checks import slug_id
from semval.tags import Stance

log = logging.getLogger(__name__)

DEFAULT_LABELS_DIR = Path("data/labels")
LABELS_FILE = "labels.jsonl"
NOTES_FILE = "notes.jsonl"


class Verdict(StrEnum):
    CORRECT = "correct"  # the value is there, with the model's stance
    NOT_PRESENT = "not_present"  # the value is not there
    WRONG_CALL = "wrong_call"  # the value is there, with another stance
    ADDED = "added"  # the model missed it; the owner adds it


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class LabelRecord(BaseModel):
    """One verdict on (document, value) at one framework level.

    ``model_stance`` is the stance the verdict was given on; ``None`` for ADDED, and for a
    NOT_PRESENT that withdraws a value the owner added. ``source_runs`` are the runs that
    proposed that stance (empty for ADDED).
    """

    model_config = ConfigDict(extra="forbid")

    labeller: str
    document_id: str
    value_id: str
    level_id: str
    model_stance: Stance | None
    verdict: Verdict
    corrected_stance: Stance | None = None
    note: str = ""
    source_runs: list[str] = Field(default_factory=list)
    updated: datetime.datetime = Field(default_factory=_now)

    @field_validator("labeller")
    @classmethod
    def _labeller(cls, v: str) -> str:
        return slug_id(v)

    @model_validator(mode="after")
    def _consistent(self) -> "LabelRecord":
        needs_corrected = self.verdict in (Verdict.WRONG_CALL, Verdict.ADDED)
        if needs_corrected and self.corrected_stance is None:
            raise ValueError(f"a {self.verdict} verdict needs a corrected_stance")
        if not needs_corrected and self.corrected_stance is not None:
            raise ValueError(f"a {self.verdict} verdict takes no corrected_stance")
        if self.corrected_stance == Stance.CONTESTED:
            raise ValueError(
                "corrected_stance cannot be contested; pick endorse, reject or mention"
            )
        if self.verdict == Verdict.ADDED and self.model_stance is not None:
            raise ValueError("an added value has no model_stance")
        if self.verdict in (Verdict.CORRECT, Verdict.WRONG_CALL) and self.model_stance is None:
            raise ValueError(f"a {self.verdict} verdict needs the model_stance it judges")
        if self.verdict == Verdict.WRONG_CALL and self.corrected_stance == self.model_stance:
            raise ValueError("a wrong call's corrected_stance must differ from the model_stance")
        return self

    def key(self) -> tuple[str, str, str, str]:
        return (self.labeller, self.document_id, self.value_id, self.level_id)

    def present_stance(self) -> Stance | None:
        """The owner's answer: the value's stance in the text, or None if it is absent."""
        if self.verdict == Verdict.CORRECT:
            return self.model_stance
        if self.verdict == Verdict.NOT_PRESENT:
            return None
        return self.corrected_stance


class ArticleNote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    labeller: str
    document_id: str
    note: str
    updated: datetime.datetime = Field(default_factory=_now)

    @field_validator("labeller")
    @classmethod
    def _labeller(cls, v: str) -> str:
        return slug_id(v)


M = TypeVar("M", bound=BaseModel)


class _AppendOnlyStore(Generic[M]):
    """JSONL records, appended and fsynced; reads keep the last record per key."""

    def __init__(self, path: Path, model: type[M], key: Callable[[M], Hashable]):
        self.path = Path(path)
        self._model, self._key = model, key
        self._lock = threading.Lock()

    def _append(self, rec: M) -> None:
        line = rec.model_dump_json() + "\n"
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a+b") as f:
                # a crash mid-write leaves a torn last line: start a fresh one after it
                size = f.seek(0, os.SEEK_END)
                if size:
                    f.seek(size - 1)
                    if f.read(1) != b"\n":
                        line = "\n" + line
                f.write(line.encode("utf-8"))
                f.flush()
                os.fsync(f.fileno())

    def _latest(self) -> dict[Hashable, M]:
        if not self.path.exists():
            return {}
        with self._lock:
            lines = self.path.read_text(encoding="utf-8").split("\n")
        out: dict[Hashable, M] = {}
        for i, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                # only a write cut short by a crash leaves broken JSON; it was never saved
                log.warning("%s: skipping torn line %d", self.path, i)
                continue
            try:
                rec = self._model.model_validate(data)
            except ValidationError as e:
                raise ValueError(f"{self.path}: line {i} is not a valid record: {e}") from None
            out.pop(self._key(rec), None)  # keep the order of the latest writes
            out[self._key(rec)] = rec
        return out


class LabelStore(_AppendOnlyStore[LabelRecord]):
    """Verdicts; the key is (labeller, document_id, value_id, level_id)."""

    def __init__(self, path: Path):
        super().__init__(path, LabelRecord, LabelRecord.key)

    def upsert(self, rec: LabelRecord) -> None:
        self._append(rec)

    def all(self) -> list[LabelRecord]:
        """The latest record per key, in the order they were last written."""
        return list(self._latest().values())


class NoteStore(_AppendOnlyStore[ArticleNote]):
    """Per-article notes; the key is (labeller, document_id)."""

    def __init__(self, path: Path):
        super().__init__(path, ArticleNote, lambda n: (n.labeller, n.document_id))

    def set(self, labeller: str, document_id: str, note: str) -> None:
        self._append(ArticleNote(labeller=labeller, document_id=document_id, note=note))

    def get(self, labeller: str, document_id: str) -> str:
        rec = self._latest().get((labeller, document_id))
        return rec.note if rec else ""


def label_paths(labels_dir: Path, labeller: str) -> tuple[Path, Path]:
    """The verdict and note files of one labeller."""
    base = Path(labels_dir) / slug_id(labeller)
    return base / LABELS_FILE, base / NOTES_FILE
