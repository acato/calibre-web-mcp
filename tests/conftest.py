"""Shared pytest fixtures: a routable MockTransport that fakes Calibre-Web."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import httpx
import pytest

from calibre_web_mcp.client import CalibreWebClient

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def mock_cw() -> Callable[..., CalibreWebClient]:
    """Factory that returns a CalibreWebClient backed by a custom MockTransport.

    Each test supplies a `handler(request) -> httpx.Response` to route requests.
    The factory pre-injects a session cookie and skips the real login flow when
    `pre_authed=True` (the common case for tool-level tests).
    """

    def _make(handler: Callable[[httpx.Request], httpx.Response], pre_authed: bool = True) -> CalibreWebClient:
        client = CalibreWebClient("http://cw.test", "alice", "pw", verify_ssl=False)
        # Replace the underlying httpx.Client with one using our mock transport
        client._client.close()
        client._client = httpx.Client(
            base_url="http://cw.test",
            transport=httpx.MockTransport(handler),
            follow_redirects=False,
            timeout=5.0,
        )
        if pre_authed:
            client._session_authed = True
            client._csrf = "TEST_CSRF"
            # plant the cookie the way a real login would
            client._client.cookies.set("session", "fake-session-value")
        return client

    return _make
