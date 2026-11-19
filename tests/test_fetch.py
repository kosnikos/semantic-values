"""PoliteFetcher against a fake transport and a fake clock (no network)."""

from pathlib import Path

import pytest

from semval.sampling.fetch import (
    FetchOutcome,
    PoliteFetcher,
    RequestBudgetExceeded,
    Response,
    is_not_free,
)

UA = "semval-research/0.1 (+https://example.org/semval)"
FREE_PAGE = (
    '<html><head><script type="application/ld+json">'
    '{"@type": "NewsArticle", "isAccessibleForFree": true}</script></head>'
    "<body><p>Open text.</p></body></html>"
)
PAID_PAGE = (
    '<html><head><script type="application/ld+json">'
    '{"@graph": [{"@type": "WebPage"}, {"@type": "NewsArticle", "isAccessibleForFree": false}]}'
    "</script></head><body><p>Full text that is still behind a paywall.</p></body></html>"
)
CHALLENGE_PAGE = "<html><title>Just a moment...</title><div id='cf-chl-widget'></div></html>"


class FakeClock:
    def __init__(self) -> None:
        self.t = 1000.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.t += seconds


class FakeTransport:
    def __init__(self, pages: dict[str, Response], clock: FakeClock | None = None) -> None:
        self.pages = pages
        self.calls: list[str] = []
        self.request_times: list[float] = []
        self.clock = clock
        self.headers: list[dict[str, str]] = []

    def __call__(self, url: str, headers: dict[str, str]) -> Response:
        self.calls.append(url)
        self.headers.append(headers)
        if self.clock:
            self.request_times.append(self.clock.now())
        return self.pages.get(url, Response(404, ""))


def robots(body: str) -> Response:
    return Response(200, body)


def make(pages: dict[str, Response], tmp_path: Path, **kw) -> tuple[PoliteFetcher, FakeTransport]:
    clock = kw.pop("clock", FakeClock())
    transport = FakeTransport(pages, clock)
    fetcher = PoliteFetcher(UA, cache_dir=tmp_path / "http", transport=transport, clock=clock, **kw)
    return fetcher, transport


def test_ok_sends_honest_user_agent(tmp_path: Path) -> None:
    fetcher, transport = make(
        {
            "https://a.test/robots.txt": robots("User-agent: *\nDisallow:\n"),
            "https://a.test/x": Response(200, FREE_PAGE),
        },
        tmp_path,
    )
    result = fetcher.get("https://a.test/x")
    assert result.outcome is FetchOutcome.OK
    assert result.status == 200
    assert result.html == FREE_PAGE
    assert all(h["User-Agent"] == UA for h in transport.headers)


def test_skips_not_free_and_disallowed(tmp_path: Path) -> None:
    fetcher, transport = make(
        {
            "https://a.test/robots.txt": robots(
                "User-agent: semval-research\nDisallow: /private/\n\nUser-agent: *\nDisallow:\n"
            ),
            "https://a.test/paid": Response(200, PAID_PAGE),
            "https://a.test/private/x": Response(200, FREE_PAGE),
        },
        tmp_path,
    )
    paid = fetcher.get("https://a.test/paid")
    assert paid.outcome is FetchOutcome.NOT_FREE
    assert paid.html is None
    blocked = fetcher.get("https://a.test/private/x")
    assert blocked.outcome is FetchOutcome.ROBOTS_DISALLOWED
    assert blocked.html is None
    assert "https://a.test/private/x" not in transport.calls


def test_disallow_all_for_our_agent(tmp_path: Path) -> None:
    fetcher, transport = make(
        {
            "https://a.test/robots.txt": robots("User-agent: semval-research\nDisallow: /\n"),
            "https://a.test/x": Response(200, FREE_PAGE),
        },
        tmp_path,
    )
    assert fetcher.get("https://a.test/x").outcome is FetchOutcome.ROBOTS_DISALLOWED
    assert transport.calls == ["https://a.test/robots.txt"]


def test_respects_crawl_delay(tmp_path: Path) -> None:
    clock = FakeClock()
    fetcher, transport = make(
        {
            "https://a.test/robots.txt": robots("User-agent: *\nCrawl-delay: 12\nDisallow:\n"),
            "https://a.test/1": Response(200, FREE_PAGE),
            "https://a.test/2": Response(200, FREE_PAGE),
            "https://b.test/robots.txt": Response(404, ""),
            "https://b.test/1": Response(200, FREE_PAGE),
            "https://b.test/2": Response(200, FREE_PAGE),
        },
        tmp_path,
        clock=clock,
    )
    for url in ["https://a.test/1", "https://a.test/2", "https://b.test/1", "https://b.test/2"]:
        assert fetcher.get(url).outcome is FetchOutcome.OK
    times = dict(zip(transport.calls, transport.request_times, strict=True))
    # Crawl-delay 12 on a.test; the default minimum 5 s on b.test (robots.txt 404 = allow all).
    assert times["https://a.test/1"] - times["https://a.test/robots.txt"] >= 12
    assert times["https://a.test/2"] - times["https://a.test/1"] >= 12
    assert times["https://b.test/1"] - times["https://b.test/robots.txt"] >= 5
    assert times["https://b.test/2"] - times["https://b.test/1"] >= 5
    assert times["https://b.test/2"] - times["https://b.test/1"] < 12


def test_min_delay_floor_beats_smaller_crawl_delay(tmp_path: Path) -> None:
    clock = FakeClock()
    fetcher, transport = make(
        {
            "https://a.test/robots.txt": robots("User-agent: *\nCrawl-delay: 1\n"),
            "https://a.test/1": Response(200, FREE_PAGE),
        },
        tmp_path,
        clock=clock,
    )
    fetcher.get("https://a.test/1")
    assert transport.request_times[1] - transport.request_times[0] >= 5


def test_challenge_not_retried(tmp_path: Path) -> None:
    fetcher, transport = make(
        {
            "https://a.test/robots.txt": robots("User-agent: *\nDisallow:\n"),
            "https://a.test/x": Response(403, CHALLENGE_PAGE),
            "https://a.test/y": Response(200, FREE_PAGE),
        },
        tmp_path,
    )
    first = fetcher.get("https://a.test/x")
    assert first.outcome is FetchOutcome.CHALLENGE
    assert first.status == 403
    assert first.html is None
    # Neither the same URL nor another URL on the challenged host is requested again.
    assert fetcher.get("https://a.test/x").outcome is FetchOutcome.CHALLENGE
    assert fetcher.get("https://a.test/y").outcome is FetchOutcome.CHALLENGE
    assert transport.calls == ["https://a.test/robots.txt", "https://a.test/x"]


def test_plain_http_error_is_not_challenge(tmp_path: Path) -> None:
    fetcher, _ = make(
        {
            "https://a.test/robots.txt": robots("User-agent: *\nDisallow:\n"),
            "https://a.test/gone": Response(410, "<html>Gone</html>"),
        },
        tmp_path,
    )
    result = fetcher.get("https://a.test/gone")
    assert result.outcome is FetchOutcome.HTTP_ERROR
    assert result.status == 410


def test_cache_hit_no_second_request(tmp_path: Path) -> None:
    pages = {
        "https://a.test/robots.txt": robots("User-agent: *\nDisallow:\n"),
        "https://a.test/x": Response(200, FREE_PAGE),
    }
    fetcher, transport = make(pages, tmp_path)
    assert fetcher.get("https://a.test/x").outcome is FetchOutcome.OK
    assert fetcher.get("https://a.test/x").html == FREE_PAGE
    assert transport.calls.count("https://a.test/x") == 1
    # A new fetcher on the same cache directory makes no request at all.
    again, transport2 = make(pages, tmp_path)
    assert again.get("https://a.test/x").html == FREE_PAGE
    assert transport2.calls == []
    assert again.requests == 0


def test_request_budget(tmp_path: Path) -> None:
    fetcher, transport = make(
        {
            "https://a.test/robots.txt": robots("User-agent: *\nDisallow:\n"),
            "https://a.test/1": Response(200, FREE_PAGE),
            "https://a.test/2": Response(200, FREE_PAGE),
        },
        tmp_path,
        max_requests=2,
    )
    fetcher.get("https://a.test/1")
    with pytest.raises(RequestBudgetExceeded):
        fetcher.get("https://a.test/2")
    assert len(transport.calls) == 2


@pytest.mark.parametrize(
    ("page", "expected"),
    [
        (FREE_PAGE, False),
        (PAID_PAGE, True),
        ('<script type="application/ld+json">[{"isAccessibleForFree": "False"}]</script>', True),
        ('<script type="application/ld+json">{not json</script>', False),
        ("<p>No JSON-LD at all.</p>", False),
    ],
)
def test_is_not_free(page: str, expected: bool) -> None:
    assert is_not_free(page) is expected
