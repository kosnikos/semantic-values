"""The Conversation, UK edition (theconversation.com/uk): the Politics section listing."""

import re
from collections.abc import Iterator
from datetime import date

from bs4 import BeautifulSoup

from semval.sampling.article import NOT_SAMPLED, Genre, OutOfScope, ParsedArticle
from semval.sampling.fetch import PoliteFetcher
from semval.sampling.listing import Item, paged_spread
from semval.sampling.parsing import iso_date, meta, paragraphs, soup, text_of

BASE = "https://theconversation.com"
# /uk/politics ignores ?page=N (every page is the front); /uk/politics/articles pages.
LISTING = f"{BASE}/uk/politics/articles"
N_PAGES = 8
EDITION = "uk"
_ARTICLE = re.compile(r"^https://theconversation\.com/[a-z0-9-]+-\d+$")
# Listing cards carry no date; the image file name ("file-20261117-...") is a close estimate.
# It only steers the page search; the article's own date is the one kept and checked.
_IMAGE_DAY = re.compile(r"/file-(\d{4})(\d{2})(\d{2})-")


def _image_day(src: str) -> date | None:
    m = _IMAGE_DAY.search(src)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def page_items(page: BeautifulSoup) -> list[Item]:
    items = []
    for card in page.select("article"):
        link = card.select_one("h2 a[href]") or card.select_one("a[href]")
        href = str(link.get("href", "")) if link else ""
        url = BASE + href if href.startswith("/") else href
        if _ARTICLE.match(url):
            img = card.select_one("img")
            src = str(img.get("data-src") or img.get("src") or "") if img else ""
            items.append((url, _image_day(src)))
    return items


def page_url(n: int) -> str:
    return LISTING if n == 1 else f"{LISTING}?page={n}"


class Conversation:
    source_id = "gb-conversation-uk"

    def list_candidates(self, fetcher: PoliteFetcher, since: date, until: date) -> Iterator[str]:
        return paged_spread(fetcher, page_url, page_items, since, until, N_PAGES)

    def parse(self, url: str, html: str) -> ParsedArticle:
        page = soup(html)
        region = meta(page, "commissioning-region")
        if region != EDITION:
            raise OutOfScope(f"commissioned by edition {region!r}, not {EDITION!r}")
        stamp = page.select_one("time[datetime]")
        return ParsedArticle(
            title=text_of(page, "h1") or "",
            date=iso_date(stamp.get("datetime") if stamp else None),
            genre=Genre.OPINION if _ARTICLE.match(url) else NOT_SAMPLED,
            text=paragraphs(page.select_one('[itemprop="articleBody"]'), "p", drop="figure"),
        )
