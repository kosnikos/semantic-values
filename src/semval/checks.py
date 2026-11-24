"""Small shared checks for registry data: slug ids, full-sentence text, strict YAML."""

import re
from pathlib import Path
from typing import Any

import yaml

SLUG = re.compile(r"^[a-z][a-z0-9_]*$")
_SENTENCE_END = re.compile(r"[.!?]")


def slug_id(v: str) -> str:
    if not SLUG.fullmatch(v):
        raise ValueError(f"id must be a lowercase slug (a-z, 0-9, _), got {v!r}")
    return v


def full_sentence(v: str) -> str:
    text = v.strip()
    if not text or not _SENTENCE_END.search(text):
        raise ValueError("definition must be at least one full sentence")
    return text


def no_duplicates(items: list[str], what: str) -> list[str]:
    seen: set[str] = set()
    for item in items:
        if item in seen:
            raise ValueError(f"duplicate {what} {item!r}")
        seen.add(item)
    return items


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that rejects a mapping key given twice (PyYAML keeps the last silently)."""


def _mapping_without_duplicates(loader: _StrictLoader, node: yaml.MappingNode) -> dict:
    keys = [loader.construct_object(key_node, deep=True) for key_node, _ in node.value]
    for i, key in enumerate(keys):
        if key in keys[:i]:
            line = node.value[i][0].start_mark.line + 1
            raise ValueError(f"duplicate key {key!r} at line {line}")
    return loader.construct_mapping(node, deep=True)


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping_without_duplicates
)


def load_yaml(path: Path) -> Any:
    """Parse a YAML file safely, failing on duplicate mapping keys."""
    return yaml.load(Path(path).read_text(encoding="utf-8"), Loader=_StrictLoader)
