"""The urllib transport does not follow redirects (checked against a loopback server)."""

import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from semval.sampling.transport import urllib_transport


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/moved":
            self.send_response(301)
            self.send_header("Location", "/target")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"page {self.path}".encode())

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture
def server() -> Iterator[str]:
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def test_redirect_is_returned_not_followed(server: str) -> None:
    response = urllib_transport(f"{server}/moved", {"User-Agent": "test/0"})
    assert response.status == 301
    assert response.location == "/target"


def test_plain_get(server: str) -> None:
    response = urllib_transport(f"{server}/x", {"User-Agent": "test/0"})
    assert (response.status, response.body, response.location) == (200, "page /x", None)
