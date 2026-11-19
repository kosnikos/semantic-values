"""A polite HTTP fetcher: robots.txt, Crawl-delay, honest user-agent, on-disk cache.

Source-agnostic. Rules (parent spec section 3, tagging spec section 5.5): obey robots.txt for
our own user-agent, wait at least ``MIN_DELAY_FLOOR_S`` (or the host's Crawl-delay, if
longer) between requests to a host, skip pages whose JSON-LD says
``isAccessibleForFree: false``, and never retry or work around a bot challenge: a
challenged host is not requested again. Redirects are followed by hand (at most
``MAX_REDIRECTS``), and each target passes the same robots and delay rules.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol
from urllib.parse import urljoin, urlsplit

from semval.sampling.jsonld import is_not_free
from semval.sampling.robots import RobotsRules, parse_robots
from semval.sampling.transport import REDIRECT_STATUSES, Response, Transport, urllib_transport

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
MIN_DELAY_FLOOR_S = 5.0
MAX_REDIRECTS = 5

# A bot challenge: one of these statuses plus one of these markers in the body.
CHALLENGE_STATUSES = frozenset({403, 429, 503})
CHALLENGE_MARKERS = (
    "cf-chl", "challenge-platform", "just a moment", "attention required", "captcha",
    "_incapsula_", "datadome", "px-captcha", "perimeterx", "verify you are human",
    "are you a robot", "access denied", "bot detection",
)  # fmt: skip
# robots.txt statuses that mean "assume everything is disallowed": forbidden, rate limited,
# server error, no response, or a redirect chain that did not end.
_ROBOTS_DISALLOW_ALL = frozenset({401, 403, 429}) | REDIRECT_STATUSES


class FetchOutcome(StrEnum):
    OK = "ok"
    NOT_FREE = "not_free"
    ROBOTS_DISALLOWED = "robots_disallowed"
    HTTP_ERROR = "http_error"
    CHALLENGE = "challenge"


@dataclass(frozen=True)
class FetchResult:
    outcome: FetchOutcome
    status: int | None
    html: str | None


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


def looks_like_challenge(response: Response) -> bool:
    if response.status not in CHALLENGE_STATUSES:
        return False
    body = response.body.lower()
    return any(marker in body for marker in CHALLENGE_MARKERS)


def _host(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def _redirect_target(url: str, response: Response) -> str | None:
    if response.status in REDIRECT_STATUSES and response.location:
        return urljoin(url, response.location)
    return None


class PoliteFetcher:
    def __init__(
        self,
        user_agent: str = USER_AGENT,
        min_delay_s: float = MIN_DELAY_FLOOR_S,
        cache_dir: Path = DEFAULT_CACHE_DIR,
        *,
        transport: Transport = urllib_transport,
        clock: Clock | None = None,
        max_requests: int | None = None,
        _allow_below_floor_for_tests: bool = False,
    ) -> None:
        self.user_agent = user_agent
        floor = 0.0 if _allow_below_floor_for_tests else MIN_DELAY_FLOOR_S
        self.min_delay_s = max(min_delay_s, floor)
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
        if url in self._not_free:
            return FetchResult(FetchOutcome.NOT_FREE, 200, None)
        current = url
        for _ in range(MAX_REDIRECTS + 1):
            blocked = self._precheck(current)
            if blocked is not None:
                return blocked
            response = self._request(_host(current), current)
            if looks_like_challenge(response):
                log.warning(
                    "bot challenge at %s (status %s); host skipped", current, response.status
                )
                self._challenged.add(_host(current))
                return FetchResult(FetchOutcome.CHALLENGE, response.status, None)
            target = _redirect_target(current, response)
            if target is None:
                break
            log.info("redirect %s -> %s", current, target)
            current = target
        else:
            log.info("more than %d redirects from %s", MAX_REDIRECTS, url)
            return FetchResult(FetchOutcome.HTTP_ERROR, response.status, None)
        if response.status != 200:
            log.info("HTTP %s for %s", response.status, current)
            return FetchResult(FetchOutcome.HTTP_ERROR, response.status or None, None)
        result = self._classify_ok(url, 200, response.body)
        if result.outcome is FetchOutcome.OK:
            self._cache_write(url, response.body)
        return result

    # -- internals ----------------------------------------------------------------------

    def _precheck(self, url: str) -> FetchResult | None:
        """A result if ``url`` must not be requested (challenged host or robots.txt)."""
        host = _host(url)
        if host in self._challenged:
            return FetchResult(FetchOutcome.CHALLENGE, None, None)
        robots = self._robots_for(host)
        if robots is None:  # robots.txt itself was a challenge
            return FetchResult(FetchOutcome.CHALLENGE, None, None)
        if not robots.can_fetch(url):
            log.info("robots.txt disallows %s", url)
            return FetchResult(FetchOutcome.ROBOTS_DISALLOWED, None, None)
        return None

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

    def _fetch_robots(self, host: str) -> Response:
        """GET robots.txt, following at most MAX_REDIRECTS redirects (RFC 9309)."""
        url = f"{host}/robots.txt"
        response = self._request(host, url)
        for _ in range(MAX_REDIRECTS):
            target = _redirect_target(url, response)
            if target is None or looks_like_challenge(response):
                break
            url = target
            response = self._request(_host(url), url)
        return response

    def _robots_for(self, host: str) -> RobotsRules | None:
        if host in self._robots:
            return self._robots[host]
        response = self._fetch_robots(host)
        if looks_like_challenge(response):
            log.warning("bot challenge on %s/robots.txt; host skipped", host)
            self._challenged.add(host)
            return None
        status = response.status
        if status == 200:
            rules = parse_robots(response.body, self.user_agent)
        elif status in _ROBOTS_DISALLOW_ALL or status >= 500 or status == 0:
            log.info("robots.txt for %s gave %s: assuming full disallow", host, status)
            rules = RobotsRules(disallow_all=True)
        else:
            rules = RobotsRules()  # other 4xx, such as 404: no rules
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
