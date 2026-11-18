"""Value-framework registry.

Framework-agnostic: every value framework is described by data (YAML), not code.
A framework file lists its values; higher-order groups are values too (usually with
``parent: null``), so ``parent`` and ``opposes`` always point at ids in the same file.
"""

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

FRAMEWORK_DIR = Path("data/framework")

SLUG = re.compile(r"^[a-z][a-z0-9_]*$")
_SENTENCE_END = re.compile(r"[.!?]")


def _slug(v: str) -> str:
    if not SLUG.fullmatch(v):
        raise ValueError(f"id must be a lowercase slug (a-z, 0-9, _), got {v!r}")
    return v


class ValueDef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1)
    definition: str
    framework: str
    parent: str | None = None
    opposes: list[str] = Field(default_factory=list)
    survey_items: list[str] = Field(default_factory=list)
    examples_endorse: list[str] = Field(default_factory=list)
    examples_reject: list[str] = Field(default_factory=list)

    @field_validator("id", "framework")
    @classmethod
    def _ids(cls, v: str) -> str:
        return _slug(v)

    @field_validator("definition")
    @classmethod
    def _definition(cls, v: str) -> str:
        text = v.strip()
        if not text or not _SENTENCE_END.search(text):
            raise ValueError("definition must be at least one full sentence")
        return text


class Framework(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1)
    citation: str = Field(min_length=1)
    values: list[ValueDef] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        return _slug(v)

    @model_validator(mode="after")
    def _integrity(self) -> "Framework":
        ids: set[str] = set()
        for v in self.values:
            if v.id in ids:
                raise ValueError(f"duplicate value id: {v.id}")
            ids.add(v.id)
            if v.framework != self.id:
                raise ValueError(f"{v.id}: framework {v.framework!r} != file id {self.id!r}")
        by_id = {v.id: v for v in self.values}
        for v in self.values:
            refs = ([v.parent] if v.parent is not None else []) + v.opposes
            for ref in refs:
                if ref not in ids:
                    raise ValueError(f"{v.id}: reference to unknown value id {ref!r}")
                if ref == v.id:
                    raise ValueError(f"{v.id}: refers to itself")
            for other in v.opposes:
                if v.id not in by_id[other].opposes:
                    raise ValueError(f"opposes must be symmetric: {v.id} -> {other}, not back")
        for v in self.values:
            seen = {v.id}
            node = v
            while node.parent is not None:
                if node.parent in seen:
                    raise ValueError(f"parent cycle through {v.id}")
                seen.add(node.parent)
                node = by_id[node.parent]
        return self

    def get(self, value_id: str) -> ValueDef:
        for v in self.values:
            if v.id == value_id:
                return v
        raise KeyError(value_id)

    def groups(self) -> list[ValueDef]:
        """Values that are another value's parent (higher-order groups), in file order."""
        parents = {v.parent for v in self.values}
        return [v for v in self.values if v.id in parents]

    def leaves(self) -> list[ValueDef]:
        """Values that no other value names as parent: the ones a text is tagged with."""
        parents = {v.parent for v in self.values}
        return [v for v in self.values if v.id not in parents]


def load_framework(path: Path) -> Framework:
    """Load and validate one framework file. Each value's ``framework`` defaults to the file id."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        # ValueError, not TypeError: a malformed file is bad data, same contract as below.
        raise ValueError(f"{path}: expected a mapping with id, name, citation, values")  # noqa: TRY004
    for entry in raw.get("values") or []:
        if isinstance(entry, dict):
            entry.setdefault("framework", raw.get("id"))
    return Framework(**raw)
