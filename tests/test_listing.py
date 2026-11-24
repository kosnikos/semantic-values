"""Spreading candidates over a date range, against a fake paginated site (no network)."""

from datetime import date, timedelta

from bs4 import BeautifulSoup

from semval.sampling.listing import dated_spread, paged_spread, round_robin, spaced_dates

SINCE, UNTIL = date(2024, 1, 1), date(2026, 11, 19)


class FakeFetcher:
    """Serves a newest-first listing: page n holds 10 items, one per day, from UNTIL back."""

    def __init__(self, pages: int = 200) -> None:
        self.pages = pages
        self.urls: list[str] = []

    def get(self, url: str):
        from semval.sampling.fetch import FetchOutcome, FetchResult

        self.urls.append(url)
        n = int(url.rsplit("/", 1)[1])
        if n > self.pages:
            return FetchResult(FetchOutcome.HTTP_ERROR, 404, None)
        days = [UNTIL - timedelta(days=(n - 1) * 10 + i) for i in range(10)]
        rows = "".join(f'<a href="https://x.test/{d.isoformat()}">{d}</a>' for d in days)
        return FetchResult(FetchOutcome.OK, 200, f"<html>{rows}</html>")


def items(page: BeautifulSoup) -> list[tuple[str, date | None]]:
    return [(str(a["href"]), date.fromisoformat(a.get_text())) for a in page.select("a")]


def test_spaced_dates() -> None:
    days = spaced_dates(SINCE, UNTIL, 5)
    assert days[0] == UNTIL and days[-1] == SINCE
    assert days == sorted(days, reverse=True)
    assert spaced_dates(SINCE, UNTIL, 1) == [UNTIL]


def test_round_robin_interleaves_and_dedupes() -> None:
    assert list(round_robin([["a", "b", "c"], ["d", "a"], ["e"]])) == ["a", "d", "e", "b", "c"]


def test_paged_spread_covers_range_with_few_requests() -> None:
    fetcher = FakeFetcher()
    urls = list(paged_spread(fetcher, lambda n: f"https://x.test/page/{n}", items, SINCE, UNTIL, 8))
    days = sorted(date.fromisoformat(u.rsplit("/", 1)[1]) for u in urls)
    assert all(SINCE <= d <= UNTIL for d in days)
    # One page per target date, so the dates spread over the whole range...
    first_per_page = [date.fromisoformat(u.rsplit("/", 1)[1]) for u in urls[:8]]
    assert max(first_per_page) >= UNTIL - timedelta(days=30)
    assert min(first_per_page) <= SINCE + timedelta(days=60)
    # ...for a handful of listing requests (exponential probe + one page per target).
    assert len(set(fetcher.urls)) <= 8 + 9


def test_paged_spread_short_listing() -> None:
    """A listing that ends before ``since`` still yields what it has, without looping."""
    fetcher = FakeFetcher(pages=5)
    urls = list(paged_spread(fetcher, lambda n: f"https://x.test/page/{n}", items, SINCE, UNTIL, 4))
    # Targets are spread over what the listing reaches (pages 1-5), not piled on its end.
    first_per_page = [date.fromisoformat(u.rsplit("/", 1)[1]) for u in urls[:4]]
    oldest_listed = UNTIL - timedelta(days=49)
    assert min(first_per_page) - oldest_listed < timedelta(days=10)
    assert max(first_per_page) > UNTIL - timedelta(days=10)
    assert len(set(fetcher.urls)) <= 4 + 2 + 4  # probe 1,2,4,8; bisect 6,5; targets


def test_dated_spread_one_page_per_day() -> None:
    seen: list[date] = []

    class DayFetcher:
        def get(self, url: str):
            from semval.sampling.fetch import FetchOutcome, FetchResult

            day = date.fromisoformat(url.rsplit("/", 1)[1])
            seen.append(day)
            links = "".join(f'<a href="https://x.test/{day}/{i}">x</a>' for i in range(3))
            return FetchResult(FetchOutcome.OK, 200, f"<html>{links}</html>")

    def day_items(page: BeautifulSoup) -> list[str]:
        return [str(a["href"]) for a in page.select("a")]

    urls = list(
        dated_spread(DayFetcher(), lambda d: f"https://x.test/{d}", day_items, SINCE, UNTIL, 4)
    )
    assert seen == spaced_dates(SINCE, UNTIL, 4)
    assert len(urls) == 12
    assert {u.split("/")[3] for u in urls[:4]} == {d.isoformat() for d in seen}


def test_paged_spread_stops_when_page_number_is_ignored() -> None:
    class SamePage(FakeFetcher):
        def get(self, url: str):
            return super().get(url.rsplit("/", 1)[0] + "/1")

    fetcher = SamePage()
    urls = list(paged_spread(fetcher, lambda n: f"https://x.test/page/{n}", items, SINCE, UNTIL, 4))
    assert len(urls) == 10  # page 1 only, once
    assert len(fetcher.urls) <= 3  # 1, 2 (same as 1: end), bisection has nothing to do
