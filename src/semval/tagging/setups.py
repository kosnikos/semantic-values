"""Saved tagger setups: ``data/taggers/<name>.yaml``, one named, reviewable configuration.

A setup holds the choices that make a run (kind, model, effort, level, unit, framework,
prompt, few-shot files, batch, options). ``semval tag --tagger NAME`` starts from one and
applies command-line overrides; ``to_spec`` turns the result into a ``TaggerSpec``, which
the tagger's kind then checks.
"""

import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from semval.config import Effort
from semval.models import ModelId
from semval.tagging.base import TaggerSpec
from semval.tagging.prompt import load_prompt
from semval.tagging.registry import check_spec, registered_kinds
from semval.units import UnitLevel

log = logging.getLogger(__name__)

SETUPS_DIR = Path(__file__).resolve().parents[3] / "data" / "taggers"


class TaggerSetup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = ""
    kind: str
    model: ModelId | None = None
    effort: Effort | None = None
    framework: str
    level: str
    unit: UnitLevel | None = None
    prompt: str = "v1"
    few_shot_files: list[Path] = []
    batch: bool = False
    options: dict[str, str | int | float | bool] = {}


def known_setups(dir: Path = SETUPS_DIR) -> list[str]:
    return sorted(p.stem for p in Path(dir).glob("*.yaml"))


def load_setup(name: str, dir: Path = SETUPS_DIR) -> TaggerSetup:
    """Setup ``name`` from ``dir``; ``ValueError`` if it is unknown or invalid (the message
    names the file)."""
    path = Path(dir) / f"{name}.yaml"
    if not path.is_file():
        raise ValueError(f"unknown tagger setup {name!r}; known: {', '.join(known_setups(dir))}")
    try:
        setup = TaggerSetup.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (ValidationError, yaml.YAMLError) as e:
        raise ValueError(f"invalid tagger setup file {path}: {e}") from None
    if setup.kind not in registered_kinds():
        raise ValueError(
            f"{path}: unknown tagger kind {setup.kind!r}; known: {', '.join(registered_kinds())}"
        )
    return setup


def apply_overrides(setup: TaggerSetup, **overrides: Any) -> TaggerSetup:
    """``setup`` with every override that is not None applied. ``few_shot_files=[]`` makes
    it zero-shot; ``options`` are merged into the setup's, the other fields replaced."""
    changes = {k: v for k, v in overrides.items() if v is not None}
    if "options" in changes:
        changes["options"] = {**setup.options, **changes["options"]}
    return TaggerSetup.model_validate({**setup.model_dump(), **changes})


def skip_missing_few_shot(setup: TaggerSetup) -> TaggerSetup:
    """``setup`` without the few-shot files that do not exist (the owner's local examples
    are not in git), each skipped with a warning; if none is left the run is zero-shot."""
    present = [p for p in setup.few_shot_files if p.is_file()]
    for p in setup.few_shot_files:
        if p not in present:
            log.warning("few-shot file %s not found; skipping it", p)
    if setup.few_shot_files and not present:
        log.warning("no few-shot file found: this run is zero-shot")
    return setup.model_copy(update={"few_shot_files": present})


def to_spec(setup: TaggerSetup) -> TaggerSpec:
    """The spec for ``setup``; ``ValueError`` if its kind does not accept the fields set."""
    _check_ids(setup)
    try:
        spec = _spec(setup)
    except ValidationError as e:
        raise ValueError("; ".join(str(x["msg"]).removeprefix("Value error, ") for x in e.errors()))
    check_spec(spec)
    return spec


def _check_ids(setup: TaggerSetup) -> None:
    """``ValueError`` naming the known ids if the framework, level or prompt does not exist."""
    from semval import values

    fw_dir = Path(values.FRAMEWORK_DIR)
    path = fw_dir / f"{setup.framework}.yaml"
    if not path.is_file():
        known = sorted(p.stem for p in fw_dir.glob("*.yaml"))
        raise ValueError(f"unknown framework {setup.framework!r}; known: {', '.join(known)}")
    level_ids = values.load_framework(path, local_dir=fw_dir / "local").level_ids()
    if setup.level not in level_ids:
        raise ValueError(
            f"unknown level {setup.level!r} in framework {setup.framework}; "
            f"known: {', '.join(level_ids)}"
        )
    load_prompt(setup.prompt)  # an unknown id lists the known ones


def _spec(setup: TaggerSetup) -> TaggerSpec:
    return TaggerSpec(
        kind=setup.kind,
        model=setup.model,
        effort=setup.effort,
        framework_id=setup.framework,
        level_id=setup.level,
        unit=setup.unit,
        few_shot=bool(setup.few_shot_files),
        batch=setup.batch,
        prompt_id=setup.prompt,
        options=dict(setup.options),
    )


def parse_options(items: Iterable[str]) -> dict[str, str | int | float | bool]:
    """``KEY=VALUE`` pairs; a value is a bool for ``true``/``false``, else an int or float if
    it parses as one, else a string."""
    out: dict[str, str | int | float | bool] = {}
    for item in items:
        key, sep, raw = item.partition("=")
        if not sep or not key:
            raise ValueError(f"--option wants KEY=VALUE, got {item!r}")
        out[key] = _scalar(raw)
    return out


def _scalar(raw: str) -> str | int | float | bool:
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    for cast in (int, float):
        try:
            return cast(raw)
        except ValueError:
            pass
    return raw
