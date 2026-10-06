"""Filter and comparison tests."""
import pytest

from orbital.data import load_elements
from orbital.filters import FilterSpec, apply_filter, matching_numbers, matches
from orbital.compare import compare_rows, comparable, MAX_COMPARE


@pytest.fixture(scope="module")
def elements():
    return load_elements()


def test_no_filter_returns_all(elements):
    spec = FilterSpec()
    assert not spec.is_active()
    assert apply_filter(elements, spec) == list(elements)
    assert matching_numbers(elements, spec) is None


def test_category_filter(elements):
    spec = FilterSpec(categories=frozenset({"halogen"}))
    out = apply_filter(elements, spec)
    assert {e.symbol for e in out} == {"F", "Cl", "Br", "I", "At", "Ts"}


def test_state_and_radioactive(elements):
    spec = FilterSpec(states=frozenset({"liquid"}))
    assert {e.name for e in apply_filter(elements, spec)} == {"Mercury", "Bromine"}
    spec = FilterSpec(radioactive=True, synthetic=False)
    out = apply_filter(elements, spec)
    assert all(e.radioactive and not e.synthetic for e in out)
    assert 84 in {e.number for e in out}  # polonium occurs naturally


def test_group_period_filters(elements):
    spec = FilterSpec(groups=frozenset({1}), periods=frozenset({4}))
    assert [e.symbol for e in apply_filter(elements, spec)] == ["K"]
    spec = FilterSpec(groups=frozenset({3}))
    out = apply_filter(elements, spec)
    # f-block has no group, so only Sc and Y
    assert [e.symbol for e in out] == ["Sc", "Y"]


def test_discovery_year_filters(elements):
    spec = FilterSpec(discovered_after=2000)
    out = apply_filter(elements, spec)
    for e in out:
        assert e.discovery.year != "ancient" and e.discovery.year >= 2000
    spec = FilterSpec(discovered_before=1700)
    out = apply_filter(elements, spec)
    ancient = {e.name for e in out if e.discovery.year == "ancient"}
    assert "Gold" in ancient
    # explicit old discoveries, e.g. Brand's phosphorus (1669)
    assert any(e.discovery.year == 1669 for e in out)


def test_synthetic_filter(elements):
    spec = FilterSpec(synthetic=True)
    assert len(apply_filter(elements, spec)) == 28
    spec = FilterSpec(synthetic=False)
    assert len(apply_filter(elements, spec)) == 90


def test_matches_helper(elements):
    spec = FilterSpec(blocks=frozenset({"f"}))
    assert matches(elements[56], spec)   # La
    assert not matches(elements[0], spec)  # H


def test_compare_rows(elements):
    rows = compare_rows([elements[7], elements[15]])  # O vs S
    labels = [r[0] for r in rows]
    assert labels[:5] == ["number", "symbol", "atomic_mass", "group", "period"]
    by_id = {r[0]: r for r in rows}
    assert by_id["group"][2] == ["16", "16"]
    assert by_id["melt"][2] == ["54.36 K (-218.8 \u00b0C)", "388.4 K (115.2 \u00b0C)"]
    assert by_id["oxidation_states"][2][0].startswith("\u22122")
    assert "uses" not in by_id  # practical fields stay in the detail panel only


def test_compare_validation(elements):
    with pytest.raises(ValueError):
        compare_rows([elements[0]])
    with pytest.raises(ValueError):
        compare_rows(elements[:5])


def test_comparable(elements):
    sel = [elements[0], elements[1]]
    assert comparable(sel, 3)
    assert not comparable(sel, 1)  # already selected
    sel = [elements[0], elements[1], elements[2], elements[3]]
    assert not comparable(sel, 10)  # max 4
