"""Tagger kinds: each kind registers a factory and the spec fields it needs or accepts.

A new kind is one module that calls ``register_tagger``; the runner builds every tagger
through ``build_tagger``. The built-in kinds (claude, lexicon) register when their modules
are imported, which the query functions here do on first use, so the registry is complete
whenever it is asked.
"""

import importlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from semval.tagging.base import Tagger, TaggerSpec
from semval.tagging.prompt import FewShotExample

# Spec fields a kind may need or accept; the rest (kind, framework, level, prompt) are
# common to all kinds.
SPEC_FIELDS = frozenset({"model", "effort", "unit", "few_shot", "batch", "options"})
_BUILTIN_MODULES = ("semval.tagging.claude", "semval.tagging.lexicon")


@dataclass(frozen=True)
class TaggerContext:
    """What a factory may need beyond the spec: an API client and few-shot examples."""

    client: Any = None
    few_shot: Sequence[FewShotExample] = ()


TaggerFactory = Callable[[TaggerSpec, TaggerContext], Tagger]


@dataclass(frozen=True)
class _Kind:
    factory: TaggerFactory
    needs: frozenset[str]
    allows: frozenset[str]
    baseline: bool


_KINDS: dict[str, _Kind] = {}


def register_tagger(
    kind: str,
    factory: TaggerFactory,
    *,
    needs: frozenset[str] = frozenset(),
    allows: frozenset[str],
    baseline: bool = False,
) -> None:
    """Register ``kind``. ``needs`` and ``allows`` name the spec fields (out of
    ``SPEC_FIELDS``) it requires or accepts; a ``baseline`` kind is a comparison in
    evaluation, never a recommended configuration."""
    if kind in _KINDS:
        raise ValueError(f"tagger kind {kind!r} is already registered")
    if bad := sorted((needs | allows) - SPEC_FIELDS):
        raise ValueError(f"unknown spec fields {bad}; kinds may name {sorted(SPEC_FIELDS)}")
    _KINDS[kind] = _Kind(factory, frozenset(needs), frozenset(allows), baseline)


def _load_builtins() -> None:
    for name in _BUILTIN_MODULES:
        importlib.import_module(name)


def registered_kinds() -> list[str]:
    _load_builtins()
    return sorted(_KINDS)


def _kind(kind: str) -> _Kind:
    _load_builtins()
    if kind not in _KINDS:
        raise ValueError(f"unknown tagger kind {kind!r}; known: {', '.join(sorted(_KINDS))}")
    return _KINDS[kind]


def is_baseline(kind: str) -> bool:
    return _kind(kind).baseline


def _is_set(spec: TaggerSpec, name: str) -> bool:
    value = getattr(spec, name)
    return bool(value) if isinstance(value, bool | dict) else value is not None


def check_spec(spec: TaggerSpec) -> None:
    """Raise ``ValueError`` if the kind is unknown, a needed field is unset, or a field the
    kind does not accept is set."""
    k = _kind(spec.kind)
    if missing := sorted(n for n in k.needs if not _is_set(spec, n)):
        raise ValueError(f"a {spec.kind} tagger spec needs {', '.join(missing)}")
    if extra := sorted(n for n in SPEC_FIELDS - k.needs - k.allows if _is_set(spec, n)):
        raise ValueError(f"a {spec.kind} tagger spec does not take {', '.join(extra)}")


def build_tagger(spec: TaggerSpec, ctx: TaggerContext = TaggerContext()) -> Tagger:
    check_spec(spec)
    return _KINDS[spec.kind].factory(spec, ctx)
