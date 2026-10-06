"""Search tests."""
import pytest

from orbital.data import load_elements
from orbital.search import search, normalize, suggest


@pytest.fixture(scope="module")
def elements():
    return load_elements()


def test_empty_query(elements):
    assert search("", elements) == []
    assert search("   ", elements) == []


def test_find_by_name(elements):
    r = search("oxygen", elements)
    assert r and r[0].number == 8
    r = search("  OXYGEN  ", elements)
    assert r[0].number == 8


def test_find_by_symbol(elements):
    r = search("O", elements)
    assert r[0].number == 8
    r = search("fe", elements)
    assert r[0].number == 26
    r = search("FE", elements)
    assert r[0].number == 26


def test_exact_symbol_ranks_above_name_prefix(elements):
    # "o" — Oxygen (exact symbol) must beat Osmium/Oganesson (name prefix)
    r = search("o", elements)
    assert r[0].symbol == "O"


def test_find_by_number(elements):
    r = search("8", elements)
    assert r[0].number == 8
    r = search("118", elements)
    assert r[0].number == 118
    # multi-digit prefix matches, ranked
    r = search("11", elements)
    assert r[0].number == 11
    assert {e.number for e in r} >= {11, 111, 112, 113, 114, 115, 116, 117, 118}


def test_category_queries(elements):
    r = search("alkali metals", elements)
    assert [e.symbol for e in r] == ["Li", "Na", "K", "Rb", "Cs", "Fr"]
    r = search("noble gases", elements)
    assert "He" in [e.symbol for e in r]
    r = search("radioactive", elements)
    assert all(e.radioactive for e in r)
    r = search("synthetic", elements)
    assert all(e.synthetic for e in r)
    assert len(r) == 28


def test_ranking_determinism(elements):
    a = search("ch", elements)
    b = search("ch", elements)
    assert [e.number for e in a] == [e.number for e in b]


def test_normalize():
    assert normalize("  Hydrogen  ") == "hydrogen"
    assert normalize("what about H2O?") == "what about h2o"


def test_suggest_limit(elements):
    assert len(suggest(elements, "h", limit=5)) == 5
