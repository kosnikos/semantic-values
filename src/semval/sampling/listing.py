"""Spread candidate URLs across a date range from a site's listing pages. Source-agnostic.

Two listing shapes are covered:

- ``dated_spread``: one listing page per day (``/archive/2024-01-15``); pages are taken on
  evenly spaced days.
- ``paged_spread``: a newest-first paginated listing (``/category/x/page/7/``). Pages are
  probed at 1, 2, 4, 8, ... until one is older than ``since`` (or the listing ends); then,
  for evenly spaced target dates, the page is estimated by linear interpolation between the
  probed pages.

Both interleave the pages (one URL per page in turn) so the sample spreads over the range,
and take a page's URLs in a fixed pseudo-random order (by hash), not in page order, so the
top slots of a page (often the paper's own editorials) are not over-sampled.
"""

import hashlib
from collections.abc import Callable, Iterable, Iterator
from datetime import date, timedelta
from itertools import pairwise

from bs4 import BeautifulSoup

from semval.sampling.fetch import FetchOutcome, PoliteFetcher
from semval.sampling.parsing import soup

Item = tuple[str, date | None]
PageItems = Callable[[BeautifulSoup], list[Item]]
MAX_PAGE = 4096


def fetch_soup(fetcher: PoliteFetcher, url: str) -> BeautifulSoup | None:
    """A listing page as a soup, or None if it could not be fetched."""
    result = fetcher.get(url)
    if result.outcome is not FetchOutcome.OK or result.html is None:
        return None
    return soup(result.html)


def spaced_dates(since: date, until: date, n: int) -> list[date]:
    """``n`` dates spread evenly from ``until`` back to ``since``, newest first."""
    if n <= 1:
        return [until]
    span = (until - since).days
    return [until - timedelta(days=round(i * span / (n - 1))) for i in range(n)]


def hash_order(urls: Iterable[str]) -> list[str]:
    """URLs in a reproducible pseudo-random order."""
    return sorted(urls, key=lambda u: hashlib.sha1(u.encode("utf-8")).hexdigest())


def round_robin(groups: Iterable[Iterable[str]]) -> Iterator[str]:
    """Interleave URL streams (one from each in turn) and drop repeats."""
    iters = [iter(g) for g in groups]
    seen: set[str] = set()
    while iters:
        alive = []
        for it in iters:
            item = next(it, None)
            if item is None:
                continue
            alive.append(it)
            if item not in seen:
                seen.add(item)
                yield item
        iters = alive


def dated_spread(
    fetcher: PoliteFetcher,
    day_url: Callable[[date], str],
    day_items: Callable[[BeautifulSoup], list[str]],
    since: date,
    until: date,
    n_days: int,
) -> Iterator[str]:
    def one_day(day: date) -> Iterator[str]:
        page = fetch_soup(fetcher, day_url(day))
        yield from hash_order(day_items(page)) if page is not None else []

    return round_robin(one_day(d) for d in spaced_dates(since, until, n_days))


class _Pages:
    """Lazily fetched listing pages and the date range each one covers."""

    def __init__(self, fetcher: PoliteFetcher, page_url: Callable[[int], str], items: PageItems):
        self.fetcher, self.page_url, self.items = fetcher, page_url, items
        self.cache: dict[int, list[Item]] = {}

    def get(self, n: int) -> list[Item]:
        """Items of page ``n``; empty if missing, or a copy of page 1 (page number ignored)."""
        if n not in self.cache:
            page = fetch_soup(self.fetcher, self.page_url(n))
            items = self.items(page) if page is not None else []
            if n > 1 and items and items == self.get(1):
                items = []
            self.cache[n] = items
        return self.cache[n]

    def day(self, n: int) -> date | None:
        """The page's median item date: robust to a few pinned or evergreen items."""
        dates = sorted(d for _, d in self.get(n) if d is not None)
        return dates[len(dates) // 2] if dates else None

    def dated(self) -> list[tuple[int, date]]:
        """Probed pages with a known date, by page number."""
        out = []
        for n in sorted(self.cache):
            day = self.day(n)
            if day is not None:
                out.append((n, day))
        return out

    def estimate(self, target: date) -> int:
        """Page number expected to hold ``target``, interpolated between probed pages."""
        points = self.dated()
        if not points:
            return 1
        for (p1, d1), (p2, d2) in pairwise(points):
            if d1 >= target >= d2 and p2 > p1:
                span = (d1 - d2).days or 1
                return p1 + round((p2 - p1) * (d1 - target).days / span)
        return points[0][0] if target > points[0][1] else points[-1][0]


def paged_spread(
    fetcher: PoliteFetcher,
    page_url: Callable[[int], str],
    page_items: PageItems,
    since: date,
    until: date,
    n_pages: int,
) -> Iterator[str]:
    """Candidate URLs from ``n_pages`` listing pages spread over ``since``..``until``.

    ``page_items`` returns the (url, date) items of a page, newest first; the date may be an
    estimate or None (the article's own date is checked later). If the listing ends (an
    empty or missing page) before ``since``, its last page is found by bisection and the
    targets are spread over the range the listing does reach.
    """
    pages = _Pages(fetcher, page_url, page_items)
    n, last_full, first_empty = 1, 0, 0
    while n <= MAX_PAGE:
        if not pages.get(n):
            first_empty = n
            break
        last_full = n
        day = pages.day(n)
        if day is not None and day < since:
            break
        n *= 2
    start = since
    if first_empty and last_full:
        lo, hi = last_full, first_empty
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (mid, hi) if pages.get(mid) else (lo, mid)
        reach = pages.day(lo)
        start = max(since, reach) if reach else since

    def one_target(target: date) -> Iterator[str]:
        items = dict(pages.get(pages.estimate(target)))
        for url in hash_order(items):
            day = items[url]
            if day is None or since <= day <= until:
                yield url

    return round_robin(one_target(t) for t in spaced_dates(start, until, n_pages))
