"""To Vima (tovima.gr): the "Γνώμες" opinion category and its columns."""

import re
from collections.abc import Iterator
from datetime import date

from bs4 import BeautifulSoup

from semval.sampling.article import NOT_SAMPLED, Genre, NotSampled, ParsedArticle
from semval.sampling.fetch import PoliteFetcher
from semval.sampling.jsonld import find_typed
from semval.sampling.listing import Item, paged_spread
from semval.sampling.parsing import clean, dmy_date, iso_date, paragraphs, soup, text_of, url_date

BASE = "https://www.tovima.gr"
LISTING = f"{BASE}/category/opinions/"
N_PAGES = 8
_SECTION = re.compile(r"^https://www\.tovima\.gr/(?:\d{4}/\d{2}/\d{2}/|print/)(opinions|stiles)/")
_GENRES = {"opinions": Genre.OPINION, "stiles": Genre.COLUMNS}
_DROP = ".whsk_parent__div, .google-preferred-source, script, style"


def genre_of(url: str) -> Genre | NotSampled:
    m = _SECTION.match(url)
    return _GENRES[m.group(1)] if m else NOT_SAMPLED


def page_items(page: BeautifulSoup) -> list[Item]:
    """The listing's schema.org ItemList rows: URL and the date shown on the row."""
    items = []
    for row in page.select('[itemprop="itemListElement"]'):
        loc = row.select_one('meta[itemprop="url"]')
        url = str(loc.get("content", "")) if loc else ""
        if genre_of(url) not in set(Genre):
            continue
        stamp = row.select_one("time")
        items.append((url, dmy_date(stamp.get_text()) if stamp else url_date(url)))
    return items


def page_url(n: int) -> str:
    return LISTING if n == 1 else f"{LISTING}page/{n}/"


class ToVima:
    source_id = "gr-tovima-website"

    def list_candidates(self, fetcher: PoliteFetcher, since: date, until: date) -> Iterator[str]:
        return paged_spread(fetcher, page_url, page_items, since, until, N_PAGES)

    def parse(self, url: str, html: str) -> ParsedArticle:
        page = soup(html)
        art = find_typed(html, {"NewsArticle", "OpinionNewsArticle", "Article"}) or {}
        return ParsedArticle(
            title=clean(str(art.get("headline") or text_of(page, "h1") or "")),
            date=iso_date(art.get("datePublished")) or url_date(url),
            genre=genre_of(url),
            text=paragraphs(page.select_one("div.post-body.main-content"), drop=_DROP),
        )
