"""Shared, source-agnostic helpers for reading article pages."""

import re
from datetime import date, datetime

from bs4 import BeautifulSoup, NavigableString, Tag

from semval.sampling.article import ParseError

_SPACE = re.compile(r"\s+")


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def clean(text: str) -> str:
    return _SPACE.sub(" ", text).strip()


def own_text(el: Tag) -> str:
    """Text of ``el`` without text inside nested elements of the same tag, scripts or styles.

    html.parser does not close an unclosed ``<p>`` at the next ``<p>``, so paragraphs can
    nest; taking each paragraph's own text avoids repeating text.
    """
    parts = []
    for node in el.find_all(string=True):
        if type(node) is not NavigableString:  # comments, script and style contents
            continue
        if node.find_parent(el.name) is el and not node.find_parent(["script", "style"]):
            parts.append(str(node))
    return clean("".join(parts))


def paragraphs(container: Tag | None, selector: str = "p", drop: str | None = None) -> str:
    """Text of the ``selector`` elements in ``container``, one paragraph per blank line.

    ``drop`` is a CSS selector for elements (ads, share boxes) removed first.
    """
    if container is None:
        raise ParseError("article body not found")
    if drop:
        for el in container.select(drop):
            el.decompose()
    parts = [own_text(el) for el in container.select(selector)]
    text = "\n\n".join(p for p in parts if p)
    if not text:
        raise ParseError("article body is empty")
    return text


def meta(page: BeautifulSoup, prop: str) -> str | None:
    """Content of ``<meta property=prop>`` or ``<meta name=prop>``."""
    tag = page.find("meta", attrs={"property": prop}) or page.find("meta", attrs={"name": prop})
    content = tag.get("content") if isinstance(tag, Tag) else None
    return clean(str(content)) if content else None


def iso_date(value: object) -> date | None:
    """The date part of an ISO 8601 date or timestamp, or None."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip()).date()
    except ValueError:
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None


def dmy_date(text: str | None) -> date | None:
    """The first ``dd.mm.yyyy`` or ``dd/mm/yyyy`` date in ``text``, or None."""
    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", text or "")
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def url_date(url: str) -> date | None:
    """A ``/yyyy/mm/dd/`` date in a URL path, or None."""
    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def text_of(page: BeautifulSoup, selector: str) -> str | None:
    el = page.select_one(selector)
    return clean(el.get_text(" ")) if el else None
