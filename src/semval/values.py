"""Value-framework registry.

Framework-agnostic: every value framework is described by data (YAML), not code.
A framework file lists its values; higher-order groups are values too (usually with
``parent: null``), so ``parent`` and ``opposes`` always point at ids in the same file.

A file may also declare named ``levels``: target sets other than the leaves, each with a
roll-up ``map`` from every leaf to one of its targets. Roll-ups are data, so a new level, or
a validation-only variant of one, is added in YAML, not in code. ``LEAF_LEVEL`` names the
leaves themselves.
"""

from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from semval.checks import full_sentence, load_yaml, no_duplicates, slug_id
from semval.targets import OfficialDefinition, TargetDef, TargetSet

__all__ = [
    "FRAMEWORK_DIR",
    "LEAF_LEVEL",
    "Framework",
    "LevelDef",
    "OfficialDefinition",
    "TargetDef",
    "TargetSet",
    "ValueDef",
    "load_framework",
]

FRAMEWORK_DIR = Path("data/framework")
LEAF_LEVEL: Final = "leaf"


class ValueDef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1)
    definition: str
    framework: str
    parent: str | None = None
    opposes: list[str] = Field(default_factory=list)
    official: OfficialDefinition | None = None
    survey_items: list[str] = Field(default_factory=list)
    examples_endorse: list[str] = Field(default_factory=list)
    examples_reject: list[str] = Field(default_factory=list)

    @field_validator("id", "framework")
    @classmethod
    def _ids(cls, v: str) -> str:
        return slug_id(v)

    @field_validator("definition")
    @classmethod
    def _definition(cls, v: str) -> str:
        return full_sentence(v)

    @field_validator("opposes")
    @classmethod
    def _opposes(cls, v: list[str]) -> list[str]:
        return no_duplicates(v, "opposes entry")

    def as_target(self) -> TargetDef:
        """This value as a tagging target (a copy: changing it does not change the value)."""
        return TargetDef(
            id=self.id,
            name=self.name,
            definition=self.definition,
            official=self.official.model_copy() if self.official else None,
            examples_endorse=list(self.examples_endorse),
            examples_reject=list(self.examples_reject),
        )


class LevelDef(BaseModel):
    """A named level to tag or report at, with the roll-up from the leaves to it.

    Its targets come from exactly one of:

    - ``targets``: written out in the file;
    - ``targets_from``: another level's own targets (same targets, a different ``map``,
      e.g. a validation-only variant);
    - ``value_targets``: values of this framework (e.g. its higher-order groups), used as
      targets with their own definitions.

    ``map`` sends every leaf to exactly one target of this level.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    targets_from: str | None = None
    targets: list[TargetDef] = Field(default_factory=list)
    value_targets: list[str] = Field(default_factory=list)
    map: dict[str, str]

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if v == LEAF_LEVEL:
            raise ValueError(f"level id {LEAF_LEVEL!r} is reserved for the leaves")
        return slug_id(v)

    @model_validator(mode="after")
    def _one_source(self) -> "LevelDef":
        sources = [self.targets_from is not None, bool(self.targets), bool(self.value_targets)]
        if sum(sources) != 1:
            raise ValueError(
                f"level {self.id!r}: give exactly one of targets, targets_from, value_targets"
            )
        no_duplicates([t.id for t in self.targets] + self.value_targets, "target id")
        return self


class Framework(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1)
    citation: str = Field(min_length=1)
    values: list[ValueDef] = Field(min_length=1)
    levels: list[LevelDef] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        return slug_id(v)

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
        self._check_levels(ids)
        return self

    def _check_levels(self, value_ids: set[str]) -> None:
        no_duplicates([level.id for level in self.levels], "level id")
        leaf_ids = {v.id for v in self.leaves()}
        level_by_id = {level.id: level for level in self.levels}
        for level in self.levels:
            where = f"level {level.id!r}"
            for vid in level.value_targets:
                if vid not in value_ids:
                    raise ValueError(f"{where}: value_targets names unknown value id {vid!r}")
            if level.targets_from is not None:
                source = level_by_id.get(level.targets_from)
                if source is None:
                    raise ValueError(
                        f"{where}: targets_from names unknown level {level.targets_from!r}"
                    )
                if source.targets_from is not None:
                    raise ValueError(
                        f"{where}: targets_from must name a level with its own targets, "
                        f"not {source.id!r}"
                    )
            target_ids = {t.id for t in self._level_targets(level)}
            if extra := sorted(set(level.map) - leaf_ids):
                raise ValueError(f"{where}: map keys that are not leaves: {extra}")
            if missing := sorted(leaf_ids - set(level.map)):
                raise ValueError(f"{where}: map misses leaves: {missing}")
            if unknown := sorted(set(level.map.values()) - target_ids):
                raise ValueError(f"{where}: map values that are not its targets: {unknown}")

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
        """Values that no other value names as parent: the ones a text is tagged with.

        Leaves are decided by structure, not intent: a value with no children is a leaf,
        even one the file meant as a group (``parent: null`` and no members yet).
        """
        parents = {v.parent for v in self.values}
        return [v for v in self.values if v.id not in parents]

    def level_ids(self) -> list[str]:
        """``LEAF_LEVEL`` first, then the declared levels in file order."""
        return [LEAF_LEVEL, *(level.id for level in self.levels)]

    def _level(self, level_id: str) -> LevelDef:
        for level in self.levels:
            if level.id == level_id:
                return level
        raise KeyError(level_id)

    def _level_targets(self, level: LevelDef) -> list[TargetDef]:
        if level.targets_from is not None:
            level = self._level(level.targets_from)
        if level.value_targets:
            return [self.get(vid).as_target() for vid in level.value_targets]
        return level.targets

    def target_set(self, level_id: str) -> TargetSet:
        """The targets of one level, copied so that a tagger cannot change the framework."""
        if level_id == LEAF_LEVEL:
            targets = [v.as_target() for v in self.leaves()]
        else:
            targets = [t.model_copy(deep=True) for t in self._level_targets(self._level(level_id))]
        return TargetSet(framework_id=self.id, level_id=level_id, targets=targets)

    def rollup_map(self, level_id: str) -> dict[str, str]:
        """Leaf id -> target id at ``level_id``. The identity for ``LEAF_LEVEL``."""
        if level_id == LEAF_LEVEL:
            return {v.id: v.id for v in self.leaves()}
        return dict(self._level(level_id).map)


class _LocalOfficial(BaseModel):
    """Verbatim official texts kept out of the public repo, keyed like the public file:
    ``values: {value_id: text}`` and ``levels: {level_id: {target_id: text}}``."""

    model_config = ConfigDict(extra="forbid")

    values: dict[str, str] = Field(default_factory=dict)
    levels: dict[str, dict[str, str]] = Field(default_factory=dict)


def _set_local_text(holder: ValueDef | TargetDef, text: str, where: str) -> None:
    official = holder.official
    if official is None or not official.local_only:
        raise ValueError(
            f"{where}: local text given, but its official definition is not local_only"
        )
    holder.official = OfficialDefinition(
        citation=official.citation, page=official.page, text=text, local_only=True
    )


def _merge_local_official(fw: Framework, path: Path) -> None:
    local = _LocalOfficial.model_validate(load_yaml(path) or {})
    for value_id, text in local.values.items():
        try:
            value = fw.get(value_id)
        except KeyError:
            raise ValueError(f"{path}: unknown value id {value_id!r}") from None
        _set_local_text(value, text, f"{path}: value {value_id!r}")
    for level_id, texts in local.levels.items():
        level = next((x for x in fw.levels if x.id == level_id), None)
        if level is None or not level.targets:
            raise ValueError(f"{path}: level {level_id!r} has no targets written in the file")
        by_id = {t.id: t for t in level.targets}
        for target_id, text in texts.items():
            if target_id not in by_id:
                raise ValueError(f"{path}: level {level_id!r} has no target {target_id!r}")
            _set_local_text(by_id[target_id], text, f"{path}: target {level_id}.{target_id}")


def load_framework(path: Path, local_dir: Path | None = FRAMEWORK_DIR / "local") -> Framework:
    """Load and validate one framework file. Each value's ``framework`` defaults to the file id.

    If ``local_dir/<framework id>.official.yaml`` exists, its verbatim official texts are
    merged into the ``official`` blocks marked ``local_only``. ``local_dir=None`` skips this.
    """
    raw = load_yaml(path)
    if not isinstance(raw, dict):
        # ValueError, not TypeError: a malformed file is bad data, same contract as below.
        raise ValueError(f"{path}: expected a mapping with id, name, citation, values")  # noqa: TRY004
    for entry in raw.get("values") or []:
        if isinstance(entry, dict):
            entry.setdefault("framework", raw.get("id"))
    fw = Framework(**raw)
    if local_dir is not None:
        local = Path(local_dir) / f"{fw.id}.official.yaml"
        if local.exists():
            _merge_local_official(fw, local)
    return fw
