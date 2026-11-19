"""The Guardian website (theguardian.com): Comment is free, one day listing at a time."""

import re
from collections.abc import Iterator
from datetime import date

from bs4 import BeautifulSoup

from semval.sampling.article import Genre, ParsedArticle
from semval.sampling.fetch import PoliteFetcher
from semval.sampling.jsonld import find_typed
from semval.sampling.listing import dated_spread
from semval.sampling.parsing import clean, iso_date, paragraphs, soup, text_of

BASE = "https://www.theguardian.com"
N_DAYS = 10
# /commentisfree/2024/jan/15/slug; cartoons (/picture/), video and audio have extra segments.
_ARTICLE = re.compile(r"^https://www\.theguardian\.com/commentisfree/\d{4}/[a-z]{3}/\d{2}/[^/]+$")
_NOT_ARTICLES = ("/all", "/altdate")
EDITORIAL_PREFIX = "the-guardian-view"


def day_url(day: date) -> str:
    return f"{BASE}/commentisfree/{day.year}/{day.strftime('%b').lower()}/{day.day:02d}/all"


def genre_of(url: str) -> str:
    if not _ARTICLE.match(url) or url.endswith(_NOT_ARTICLES):
        return "other"
    slug = url.rsplit("/", 1)[1]
    return Genre.EDITORIAL if slug.startswith(EDITORIAL_PREFIX) else Genre.OPINION


def day_items(page: BeautifulSoup) -> list[str]:
    urls: list[str] = []
    for link in page.select("a[href]"):
        url = str(link["href"])
        if genre_of(url) in set(Genre) and url not in urls:
            urls.append(url)
    return urls


class Guardian:
    source_id = "gb-guardian-website"

    def list_candidates(self, fetcher: PoliteFetcher, since: date, until: date) -> Iterator[str]:
        return dated_spread(fetcher, day_url, day_items, since, until, N_DAYS)

    def parse(self, url: str, html: str) -> ParsedArticle:
        page = soup(html)
        art = find_typed(html, {"NewsArticle", "OpinionNewsArticle", "Article"}) or {}
        body = page.select_one("div.article-body-commercial-selector")
        return ParsedArticle(
            title=clean(str(art.get("headline") or text_of(page, "h1") or "")),
            date=iso_date(art.get("datePublished")),
            genre=genre_of(url),
            text=paragraphs(body, "p", drop="aside, figure, script, style"),
        )
