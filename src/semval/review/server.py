"""Stdlib HTTP server for the review page, on 127.0.0.1 only.

Routes: ``/`` and ``/static/*`` (the page), ``GET /api/items``, ``GET /api/doc/<id>``,
``POST /api/verdict`` and ``POST /api/note``. Requests must name this server in their
``Host`` header (no DNS rebinding) and POSTs must be JSON (no cross-site form posts).
"""

import json
import logging
import urllib.parse
import webbrowser
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from semval.review.session import NotFound, ReviewSession, SessionError

log = logging.getLogger(__name__)

HOST = "127.0.0.1"
DEFAULT_PORT = 8765
STATIC_DIR = Path(__file__).parent / "static"
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/static/review.js": ("review.js", "text/javascript; charset=utf-8"),
    "/static/review.css": ("review.css", "text/css; charset=utf-8"),
}
MAX_BODY = 64 * 1024
DOC_PREFIX = "/api/doc/"


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    session: ReviewSession

    def allowed_hosts(self) -> set[str]:
        port = self.server_address[1]
        return {f"{HOST}:{port}", f"localhost:{port}"}


class _Handler(BaseHTTPRequestHandler):
    server: _Server

    def log_message(self, format: str, *args: Any) -> None:
        log.debug("%s - " + format, self.address_string(), *args)

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _error(self, status: HTTPStatus, message: str) -> None:
        self._json(status, {"error": message})

    def _host_ok(self) -> bool:
        if self.headers.get("Host") in self.server.allowed_hosts():
            return True
        self._error(HTTPStatus.FORBIDDEN, "unexpected Host header")
        return False

    def do_GET(self) -> None:
        self._guarded(self._get)

    def do_POST(self) -> None:
        # Read the body before any answer: replying with it unread resets the connection.
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        body = self.rfile.read(length) if 0 < length <= MAX_BODY else None
        if body is None:
            self.close_connection = True
        self._guarded(lambda: self._post(body))

    def _guarded(self, handle: Callable[[], None]) -> None:
        if not self._host_ok():
            return
        try:
            handle()
        except Exception:
            log.exception("review server error on %s %s", self.command, self.path)
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "server error; see the terminal")

    def _get(self) -> None:
        path = urllib.parse.urlsplit(self.path).path
        session = self.server.session
        if path in STATIC:
            name, content_type = STATIC[path]
            self._send(HTTPStatus.OK, (STATIC_DIR / name).read_bytes(), content_type)
        elif path == "/api/items":
            self._json(HTTPStatus.OK, session.items_payload())
        elif path.startswith(DOC_PREFIX):
            doc_id = urllib.parse.unquote(path[len(DOC_PREFIX) :])
            try:
                self._json(HTTPStatus.OK, session.doc_payload(doc_id))
            except NotFound:
                self._error(HTTPStatus.NOT_FOUND, f"unknown document {doc_id!r}")
        else:
            self._error(HTTPStatus.NOT_FOUND, "not found")

    def _post(self, raw: bytes | None) -> None:
        session = self.server.session
        actions = {"/api/verdict": session.save_verdict, "/api/note": session.save_note}
        action = actions.get(urllib.parse.urlsplit(self.path).path)
        if action is None:
            self._error(HTTPStatus.NOT_FOUND, "not found")
            return
        content_type = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if content_type != "application/json":
            self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "send application/json")
            return
        if raw is None:
            self._error(HTTPStatus.BAD_REQUEST, "missing or oversized body")
            return
        try:
            body = json.loads(raw)
            self._json(HTTPStatus.OK, action(body))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._error(HTTPStatus.BAD_REQUEST, "body is not JSON")
        except ValidationError as e:
            msgs = "; ".join(err["msg"] for err in e.errors())
            self._error(HTTPStatus.BAD_REQUEST, msgs)
        except SessionError as e:
            self._error(HTTPStatus.BAD_REQUEST, str(e))


def make_server(session: ReviewSession, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """A server for ``session`` on 127.0.0.1:``port`` (0 picks a free port); not started."""
    server = _Server((HOST, port), _Handler)
    server.session = session
    return server


def serve(session: ReviewSession, port: int = DEFAULT_PORT, open_browser: bool = False) -> None:
    """Serve until Ctrl+C."""
    server = make_server(session, port)
    url = f"http://{HOST}:{server.server_address[1]}/"
    mode = "blind pass" if session.blind else "review"
    print(f"{mode}: {len(session.documents)} articles, labeller {session.labeller}")
    print(f"open {url}  (Ctrl+C to stop)", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
