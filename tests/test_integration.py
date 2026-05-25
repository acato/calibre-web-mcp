"""Integration tests that hit a real Calibre-Web instance.

Skipped by default. Enable by setting all three:
    CALIBRE_WEB_TEST_URL=http://your-cw:8083
    CALIBRE_WEB_TEST_USER=...
    CALIBRE_WEB_TEST_PASS=...

The suite creates `pytest-cw-mcp-DELETEME` shelves and deletes them on teardown.
It does not modify any pre-existing shelves or books.
"""

from __future__ import annotations

import os
import uuid

import pytest

from calibre_web_mcp.client import CalibreWebClient

pytestmark = pytest.mark.integration

URL = os.environ.get("CALIBRE_WEB_TEST_URL")
USER = os.environ.get("CALIBRE_WEB_TEST_USER")
PASS = os.environ.get("CALIBRE_WEB_TEST_PASS")

if not (URL and USER and PASS):
    pytest.skip(
        "Integration tests require CALIBRE_WEB_TEST_URL/USER/PASS env vars",
        allow_module_level=True,
    )


@pytest.fixture
def client():
    c = CalibreWebClient(URL, USER, PASS)
    c.login()
    yield c
    c.close()


@pytest.fixture
def temp_shelf(client):
    name = f"pytest-cw-mcp-DELETEME-{uuid.uuid4().hex[:6]}"
    sid = client.create_shelf(name, public=False)
    yield sid, name
    # best-effort cleanup
    try:
        client.delete_shelf(sid)
    except Exception:
        pass


def test_list_shelves_works(client):
    shelves = client.list_shelves()
    assert isinstance(shelves, list)
    # Every shelf id should be a positive int and the name a non-empty string
    for s in shelves:
        assert s.id > 0
        assert s.name


def test_shelf_lifecycle(client, temp_shelf):
    sid, name = temp_shelf
    # Must appear in the listing
    assert any(s.id == sid and s.name == name for s in client.list_shelves())
    # Toggle public -> shelf reappears with the Public flag
    client.set_shelf_public(sid, True)
    refreshed = next(s for s in client.list_shelves() if s.id == sid)
    assert refreshed.is_public is True
    assert refreshed.name == name
    # Toggle back
    client.set_shelf_public(sid, False)
    refreshed = next(s for s in client.list_shelves() if s.id == sid)
    assert refreshed.is_public is False


def test_search_returns_books(client):
    # Use a specific term to avoid huge OPDS feeds. CW's `/opds/search/<term>`
    # currently has no server-side limit param, so broad queries can be slow.
    books = client.search_books("calibre", limit=5)
    if not books:
        pytest.skip("library has no 'calibre' matches; nothing to assert")
    assert all(b.id > 0 for b in books)
    assert all(b.title for b in books)
