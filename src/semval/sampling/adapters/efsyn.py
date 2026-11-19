"""Efimerida ton Syntakton (efsyn.gr): "Απόψεις" (opinion), in the "Στήλες" section.

The /stiles/ listing pages stop at about page 100 (some six months back), so the sample
uses the deeper /stiles/apopseis/ listing.
"""

import re
from collections.abc import Iterator
from datetime import date

from bs4 import BeautifulSoup

from semval.sampling.article import Genre, ParsedArticle
from semval.sampling.fetch import PoliteFetcher
from semval.sampling.jsonld import find_typed
from semval.sampling.listing import Item, paged_spread
from semval.sampling.parsing import clean, dmy_date, iso_date, paragraphs, soup, text_of

BASE = "https://www.efsyn.gr"
LISTING = f"{BASE}/stiles/apopseis/"
N_PAGES = 8
# New-style /stiles/1512727/slug/ and old-style /stiles/apopseis/503905_slug/ article URLs.
_ARTICLE = re.compile(r"^https://www\.efsyn\.gr/stiles/(?:\d+/[^/]+|[a-z-]+/\d+_[^/]+)/$")
EDITORIAL_SECTION = "Η άποψη της"  # "Η άποψη της ΕφΣυν": the paper's own view
OPINION_SECTION = "Απόψεις"


def genre_of(url: str, section: str) -> str:
    if not _ARTICLE.match(url):
        return "other"
    if EDITORIAL_SECTION in section:
        return Genre.EDITORIAL
    return Genre.OPINION if OPINION_SECTION in section else Genre.COLUMNS


def page_items(page: BeautifulSoup) -> list[Item]:
    items = []
    for card in page.select("article.post"):
        link = card.select_one(".post-title a[href]")
        url = str(link.get("href", "")) if link else ""
        if _ARTICLE.match(url):
            stamp = card.select_one("time")
            items.append((url, dmy_date(stamp.get_text()) if stamp else None))
    return items


def page_url(n: int) -> str:
    return LISTING if n == 1 else f"{LISTING}page/{n}/"


class Efsyn:
    source_id = "gr-efsyn-website"

    def list_candidates(self, fetcher: PoliteFetcher, since: date, until: date) -> Iterator[str]:
        return paged_spread(fetcher, page_url, page_items, since, until, N_PAGES)

    def parse(self, url: str, html: str) -> ParsedArticle:
        page = soup(html)
        art = find_typed(html, {"NewsArticle", "OpinionNewsArticle", "Article"}) or {}
        return ParsedArticle(
            title=clean(str(art.get("headline") or text_of(page, "h1") or "")),
            date=iso_date(art.get("datePublished")),
            genre=genre_of(url, str(art.get("articleSection") or "")),
            text=paragraphs(page.select_one("div.article-body"), "div.article-sub.prose p"),
        )
