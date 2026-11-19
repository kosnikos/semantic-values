"""The Standard (standard.co.uk, formerly the Evening Standard): Comment, via the day archive."""

import re
from collections.abc import Iterator
from datetime import date

from bs4 import BeautifulSoup

from semval.sampling.article import Genre, ParsedArticle
from semval.sampling.fetch import PoliteFetcher
from semval.sampling.jsonld import find_typed
from semval.sampling.listing import dated_spread
from semval.sampling.parsing import clean, iso_date, paragraphs, soup, text_of

BASE = "https://www.standard.co.uk"
N_DAYS = 30  # many days, weekends especially, have no Comment piece
_ARTICLE = re.compile(r"^/comment/[a-z0-9-]+-[a-z]\d+\.html$")  # not /comment/podcasts/...
EDITORIAL_PREFIX = "The Standard View"
# Body paragraphs are the only <p> without a class inside #main (a styled-components page).
_BODY_P = "p:not([class])"


def day_url(day: date) -> str:
    return f"{BASE}/archive/{day.isoformat()}"


def day_items(page: BeautifulSoup) -> list[str]:
    urls: list[str] = []
    for link in page.select("a[href]"):
        path = str(link["href"]).removeprefix(BASE)
        if _ARTICLE.match(path) and BASE + path not in urls:
            urls.append(BASE + path)
    return urls


class Standard:
    source_id = "gb-evening-standard"

    def list_candidates(self, fetcher: PoliteFetcher, since: date, until: date) -> Iterator[str]:
        return dated_spread(fetcher, day_url, day_items, since, until, N_DAYS)

    def parse(self, url: str, html: str) -> ParsedArticle:
        page = soup(html)
        art = find_typed(html, {"NewsArticle", "OpinionNewsArticle", "Article"}) or {}
        title = text_of(page, "h1") or clean(str(art.get("headline") or ""))
        if not _ARTICLE.match(url.removeprefix(BASE)):
            genre: str = "other"
        else:
            genre = Genre.EDITORIAL if title.startswith(EDITORIAL_PREFIX) else Genre.OPINION
        return ParsedArticle(
            title=title,
            date=iso_date(art.get("datePublished")),
            genre=genre,
            text=paragraphs(page.select_one("#main"), _BODY_P),
        )
