"""OPDS Atom-feed parsing tests."""

from __future__ import annotations

import httpx

from .conftest import fixture


def _opds_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/opds/shelfindex":
        return httpx.Response(200, text=fixture("shelfindex.xml"))
    if request.url.path == "/opds/shelf/1":
        return httpx.Response(200, text=fixture("shelf_contents.xml"))
    if request.url.path.startswith("/opds/search/"):
        return httpx.Response(200, text=fixture("shelf_contents.xml"))
    return httpx.Response(404)


def test_list_shelves_parses_atom_and_detects_public(mock_cw):
    c = mock_cw(_opds_handler)
    shelves = c.list_shelves()
    assert [s.id for s in shelves] == [1, 7, 25]
    assert [s.name for s in shelves] == ["Accounting", "Personal Notes", "Comics-Eros"]
    # Only the first shelf has " (Public)" in its OPDS title
    assert [s.is_public for s in shelves] == [True, False, False]


def test_get_shelf_returns_books_with_metadata(mock_cw):
    c = mock_cw(_opds_handler)
    s = c.get_shelf(1)
    assert s["id"] == 1
    assert s["count"] == 2
    book = s["books"][0]
    assert book["id"] == 100
    assert book["title"] == "Sample Book One"
    assert book["authors"] == ["Doe, Jane", "Roe, John"]
    assert book["publisher"] == "Acme Press"
    assert book["language"] == "eng"
    assert set(book["formats"]) == {"epub", "pdf"}
    assert book["has_cover"] is True
    assert "Fiction" in book["tags"]


def test_get_shelf_handles_book_with_no_cover_or_formats(mock_cw):
    c = mock_cw(_opds_handler)
    s = c.get_shelf(1)
    sparse = s["books"][1]
    assert sparse["title"].startswith("Sample Book Two")
    assert sparse["formats"] == []
    assert sparse["has_cover"] is False
    # No book id derivable when no download/cover links present
    assert sparse["id"] == 0


def test_search_books_returns_book_objects(mock_cw):
    c = mock_cw(_opds_handler)
    books = c.search_books("anything", limit=10)
    assert len(books) == 2
    assert books[0].title == "Sample Book One"
    assert books[0].id == 100
    assert books[0].has_cover is True


def test_search_books_respects_limit(mock_cw):
    c = mock_cw(_opds_handler)
    assert len(c.search_books("anything", limit=1)) == 1


def test_search_books_rejects_empty_query(mock_cw):
    import pytest
    c = mock_cw(_opds_handler)
    with pytest.raises(ValueError, match="non-empty"):
        c.search_books("")
    with pytest.raises(ValueError, match="non-empty"):
        c.search_books("   ")
