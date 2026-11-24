"""Read schema.org JSON-LD blocks out of an HTML page. Source-agnostic."""

import json
import re
from collections.abc import Iterator
from typing import Any

# The type attribute may be double-quoted, single-quoted or bare (type=application/ld+json).
_JSON_LD = re.compile(
    r"<script\b[^>]*\btype\s*=\s*[\"']?\s*application/ld\+json\s*[\"']?[^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
# Backstop for blocks that are not valid JSON even with strict=False.
_NOT_FREE_TEXT = re.compile(r"\"isAccessibleForFree\"\s*:\s*\"?false", re.IGNORECASE)


def raw_json_ld(html: str) -> list[str]:
    """The text of every JSON-LD script block, parsed or not."""
    return [m.group(1) for m in _JSON_LD.finditer(html)]


def json_ld_blocks(html: str) -> list[Any]:
    """Parsed JSON-LD blocks.

    Raw control characters inside strings are tolerated (``strict=False``); blocks that are
    still not valid JSON are skipped.
    """
    blocks = []
    for text in raw_json_ld(html):
        try:
            blocks.append(json.loads(text, strict=False))
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
    """True if any JSON-LD object says ``"isAccessibleForFree": false``.

    Errs towards "not free": a block that does not parse still counts if its text matches
    ``"isAccessibleForFree": false``.
    """
    if any(_is_false(obj.get("isAccessibleForFree")) for obj in objects(html)):
        return True
    return any(_NOT_FREE_TEXT.search(text) for text in raw_json_ld(html))


def find_typed(html: str, types: set[str]) -> dict[str, Any] | None:
    """The first JSON-LD object whose @type is (or includes) one of ``types``."""
    for obj in objects(html):
        kind = obj.get("@type")
        kinds = set(kind) if isinstance(kind, list) else {kind}
        if kinds & types:
            return obj
    return None
