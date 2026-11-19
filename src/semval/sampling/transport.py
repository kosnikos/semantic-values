"""The HTTP transport under PoliteFetcher: one GET, no automatic redirects. Source-agnostic.

Redirects are not followed here, so the fetcher can check each redirect target against
robots.txt and the per-host delay before requesting it.
"""

import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from email.message import Message
from typing import Protocol

log = logging.getLogger(__name__)

TIMEOUT_S = 30.0
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


@dataclass(frozen=True)
class Response:
    """What a transport returns. Status 0 means no HTTP response (network error).

    ``location`` is the Location header of a redirect, unresolved.
    """

    status: int
    body: str
    location: str | None = None


class Transport(Protocol):
    def __call__(self, url: str, headers: dict[str, str]) -> Response: ...


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Make urllib return a 3xx as an HTTPError instead of following it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect())


def _decode(raw: bytes, charset: str | None) -> str:
    try:
        return raw.decode(charset or "utf-8", errors="replace")
    except LookupError:  # unknown charset name in the header
        return raw.decode("utf-8", errors="replace")


def _location(headers: Message | None) -> str | None:
    return headers.get("Location") if headers is not None else None


def urllib_transport(url: str, headers: dict[str, str]) -> Response:
    """GET with stdlib urllib. HTTP errors and redirects come back as a Response."""
    request = urllib.request.Request(url, headers=headers)
    try:
        with _OPENER.open(request, timeout=TIMEOUT_S) as resp:
            return Response(resp.status, _decode(resp.read(), resp.headers.get_content_charset()))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace") if err.fp else ""
        return Response(err.code, body, _location(err.headers))
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        log.warning("network error for %s: %s", url, err)
        return Response(0, "")
