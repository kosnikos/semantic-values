"""Read schema.org JSON-LD blocks out of an HTML page. Source-agnostic."""

import json
import re
from collections.abc import Iterator
from typing import Any

_JSON_LD = re.compile(
    r"<script[^>]*type\s*=\s*[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)


def json_ld_blocks(html: str) -> list[Any]:
    """Parsed JSON-LD blocks; blocks that are not valid JSON are skipped."""
    blocks = []
    for m in _JSON_LD.finditer(html):
        try:
            blocks.append(json.loads(m.group(1)))
        except json.JSONDecodeError:
            continue
    return blocks


def walk(node: Any) -> Iterator[dict[str, Any]]:
    """Every JSON object inside ``node``, depth first (lists and @graph included)."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


def objects(html: str) -> list[dict[str, Any]]:
    """Every JSON object in every JSON-LD block of the page."""
    return [obj for block in json_ld_blocks(html) for obj in walk(block)]


def _is_false(value: Any) -> bool:
    return value is False or (isinstance(value, str) and value.strip().lower() == "false")


def is_not_free(html: str) -> bool:
    """True if any JSON-LD object says ``"isAccessibleForFree": false``."""
    return any(_is_false(obj.get("isAccessibleForFree")) for obj in objects(html))


def find_typed(html: str, types: set[str]) -> dict[str, Any] | None:
    """The first JSON-LD object whose @type is (or includes) one of ``types``."""
    for obj in objects(html):
        kind = obj.get("@type")
        kinds = set(kind) if isinstance(kind, list) else {kind}
        if kinds & types:
            return obj
    return None
