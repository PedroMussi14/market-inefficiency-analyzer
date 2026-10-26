"""Shared pytest fixtures for the analyzer test suite."""

import pytest

from factories import make_book, make_event, make_outcome


@pytest.fixture
def two_way_arb_event() -> dict:
    """Each side is +110 (2.10) at a different book: implied sum 0.9524."""
    return make_event([
        make_book("Book A", "h2h", [make_outcome("Home", 110), make_outcome("Away", -150)]),
        make_book("Book B", "h2h", [make_outcome("Home", -150), make_outcome("Away", 110)]),
    ])
