"""A polite HTTP fetcher: robots.txt, Crawl-delay, honest user-agent, on-disk cache.

Source-agnostic. Rules (parent spec section 3, tagging spec section 5.5): obey robots.txt for
our own user-agent, wait at least ``min_delay_s`` (or the host's Crawl-delay, if longer)
between requests to a host, skip pages whose JSON-LD says ``isAccessibleForFree: false``,
and never retry or work around a bot challenge: a challenged host is not requested again.
"""

import hashlib
import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

from semval.sampling.jsonld import is_not_free
from semval.sampling.robots import RobotsRules, parse_robots

__all__ = [
    "FetchOutcome",
    "FetchResult",
    "PoliteFetcher",
    "RequestBudgetExceeded",
    "Response",
    "is_not_free",
]

log = logging.getLogger(__name__)

USER_AGENT = "semval-research/0.1 (+https://github.com/kosnikos/semantic-values)"
DEFAULT_CACHE_DIR = Path("data/raw/http")
TIMEOUT_S = 30.0

# A bot challenge: one of these statuses plus one of these markers in the body.
CHALLENGE_STATUSES = frozenset({403, 429, 503})
CHALLENGE_MARKERS = (
    "cf-chl", "challenge-platform", "just a moment", "attention required", "captcha",
    "_incapsula_", "datadome", "px-captcha", "perimeterx", "verify you are human",
    "are you a robot", "access denied", "bot detection",
)  # fmt: skip


class FetchOutcome(StrEnum):
    OK = "ok"
    NOT_FREE = "not_free"
    ROBOTS_DISALLOWED = "robots_disallowed"
    HTTP_ERROR = "http_error"
    CHALLENGE = "challenge"


@dataclass(frozen=True)
class Response:
    """What a transport returns. Status 0 means no HTTP response (network error)."""

    status: int
    body: str


@dataclass(frozen=True)
class FetchResult:
    outcome: FetchOutcome
    status: int | None
    html: str | None


class Transport(Protocol):
    def __call__(self, url: str, headers: dict[str, str]) -> Response: ...


class Clock(Protocol):
    def now(self) -> float: ...
    def sleep(self, seconds: float) -> None: ...


class SystemClock:
    def now(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


class RequestBudgetExceeded(RuntimeError):
    """The fetcher's ``max_requests`` is used up."""


def urllib_transport(url: str, headers: dict[str, str]) -> Response:
    """GET with stdlib urllib. HTTP errors come back as a Response, not an exception."""
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as resp:
            return Response(resp.status, _decode(resp.read(), resp.headers.get_content_charset()))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace") if err.fp else ""
        return Response(err.code, body)
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        log.warning("network error for %s: %s", url, err)
        return Response(0, "")


def _decode(raw: bytes, charset: str | None) -> str:
    try:
        return raw.decode(charset or "utf-8", errors="replace")
    except LookupError:  # unknown charset name in the header
        return raw.decode("utf-8", errors="replace")


def looks_like_challenge(response: Response) -> bool:
    if response.status not in CHALLENGE_STATUSES:
        return False
    body = response.body.lower()
    return any(marker in body for marker in CHALLENGE_MARKERS)


def _host(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


class PoliteFetcher:
    def __init__(
        self,
        user_agent: str = USER_AGENT,
        min_delay_s: float = 5.0,
        cache_dir: Path = DEFAULT_CACHE_DIR,
        *,
        transport: Transport = urllib_transport,
        clock: Clock | None = None,
        max_requests: int | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.min_delay_s = min_delay_s
        self.cache_dir = Path(cache_dir)
        self.transport = transport
        self.clock = clock or SystemClock()
        self.max_requests = max_requests
        self.requests = 0
        self._robots: dict[str, RobotsRules] = {}
        self._delay: dict[str, float] = {}
        self._next_ok: dict[str, float] = {}
        self._challenged: set[str] = set()
        self._not_free: set[str] = set()

    # -- public -------------------------------------------------------------------------

    def get(self, url: str) -> FetchResult:
        cached = self._cache_read(url)
        if cached is not None:
            return self._classify_ok(url, 200, cached)
        host = _host(url)
        if host in self._challenged:
            return FetchResult(FetchOutcome.CHALLENGE, None, None)
        if url in self._not_free:
            return FetchResult(FetchOutcome.NOT_FREE, 200, None)
        robots = self._robots_for(host)
        if robots is None:  # robots.txt itself was a challenge
            return FetchResult(FetchOutcome.CHALLENGE, None, None)
        if not robots.can_fetch(url):
            log.info("robots.txt disallows %s", url)
            return FetchResult(FetchOutcome.ROBOTS_DISALLOWED, None, None)
        response = self._request(host, url)
        if looks_like_challenge(response):
            log.warning("bot challenge at %s (status %s); host skipped", url, response.status)
            self._challenged.add(host)
            return FetchResult(FetchOutcome.CHALLENGE, response.status, None)
        if response.status != 200:
            log.info("HTTP %s for %s", response.status, url)
            return FetchResult(FetchOutcome.HTTP_ERROR, response.status or None, None)
        result = self._classify_ok(url, 200, response.body)
        if result.outcome is FetchOutcome.OK:
            self._cache_write(url, response.body)
        return result

    # -- internals ----------------------------------------------------------------------

    def _classify_ok(self, url: str, status: int, body: str) -> FetchResult:
        if is_not_free(body):
            log.info("not free (JSON-LD isAccessibleForFree false): %s", url)
            self._not_free.add(url)
            return FetchResult(FetchOutcome.NOT_FREE, status, None)
        return FetchResult(FetchOutcome.OK, status, body)

    def _request(self, host: str, url: str) -> Response:
        if self.max_requests is not None and self.requests >= self.max_requests:
            raise RequestBudgetExceeded(f"request budget of {self.max_requests} used up")
        wait = self._next_ok.get(host, 0.0) - self.clock.now()
        if wait > 0:
            self.clock.sleep(wait)
        self.requests += 1
        response = self.transport(url, {"User-Agent": self.user_agent})
        delay = self._delay.get(host, self.min_delay_s)
        self._next_ok[host] = self.clock.now() + delay
        return response

    def _robots_for(self, host: str) -> RobotsRules | None:
        if host in self._robots:
            return self._robots[host]
        response = self._request(host, f"{host}/robots.txt")
        if looks_like_challenge(response):
            log.warning("bot challenge on %s/robots.txt; host skipped", host)
            self._challenged.add(host)
            return None
        if response.status == 200:
            rules = parse_robots(response.body, self.user_agent)
        elif response.status in (401, 403) or response.status >= 500 or response.status == 0:
            rules = RobotsRules(disallow_all=True)  # forbidden or unreachable: full disallow
        else:
            rules = RobotsRules()  # 4xx such as 404: no rules
        delay = max(self.min_delay_s, rules.crawl_delay or 0.0)
        self._delay[host] = delay
        self._next_ok[host] = self.clock.now() + delay
        self._robots[host] = rules
        return rules

    def _cache_path(self, url: str) -> Path:
        return self.cache_dir / f"{hashlib.sha256(url.encode('utf-8')).hexdigest()}.html"

    def _cache_read(self, url: str) -> str | None:
        path = self._cache_path(url)
        return path.read_text(encoding="utf-8") if path.exists() else None

    def _cache_write(self, url: str, body: str) -> None:
        path = self._cache_path(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        meta = {"url": url, "fetched": time.strftime("%Y-%m-%dT%H:%M:%S")}
        path.with_suffix(".json").write_text(json.dumps(meta), encoding="utf-8")
