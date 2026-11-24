"""Ta Nea (tanea.gr): the "Απόψεις" opinion category."""

import re
from collections.abc import Iterator
from datetime import date

from bs4 import BeautifulSoup

from semval.sampling.article import NOT_SAMPLED, Genre, NotSampled, ParsedArticle
from semval.sampling.fetch import PoliteFetcher
from semval.sampling.jsonld import find_typed, objects
from semval.sampling.listing import Item, paged_spread
from semval.sampling.parsing import clean, iso_date, paragraphs, soup, text_of, url_date

BASE = "https://www.tanea.gr"
LISTING = f"{BASE}/category/opinions/"
N_PAGES = 8
_SECTION = re.compile(r"^https://www\.tanea\.gr/(?:print/)?\d{4}/\d{2}/\d{2}/(opinions|stiles)/")
_GENRES = {"opinions": Genre.OPINION, "stiles": Genre.COLUMNS}


def genre_of(url: str) -> Genre | NotSampled:
    m = _SECTION.match(url)
    return _GENRES[m.group(1)] if m else NOT_SAMPLED


def page_items(page: BeautifulSoup) -> list[Item]:
    """Items of the listing's JSON-LD ItemList (the main list, not the side boxes)."""
    items = []
    for obj in objects(str(page)):
        url = obj.get("url")
        if obj.get("@type") == "ListItem" and isinstance(url, str) and genre_of(url) in set(Genre):
            items.append((url, url_date(url)))
    return items


def page_url(n: int) -> str:
    return LISTING if n == 1 else f"{LISTING}page/{n}/"


class TaNea:
    source_id = "gr-tanea-website"

    def list_candidates(self, fetcher: PoliteFetcher, since: date, until: date) -> Iterator[str]:
        return paged_spread(fetcher, page_url, page_items, since, until, N_PAGES)

    def parse(self, url: str, html: str) -> ParsedArticle:
        page = soup(html)
        art = find_typed(html, {"OpinionNewsArticle", "NewsArticle", "Article"}) or {}
        return ParsedArticle(
            title=clean(str(art.get("headline") or text_of(page, "h1") or "")),
            date=iso_date(art.get("datePublished")) or url_date(url),
            genre=genre_of(url),
            text=paragraphs(page.select_one("div.post__body"), drop="script, style"),
        )
