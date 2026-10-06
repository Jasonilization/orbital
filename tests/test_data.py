"""Chemistry data integrity tests. If these fail, the data is wrong, not the test."""
import pytest

from orbital.data import load_elements, by_number, by_symbol, by_name


@pytest.fixture(scope="module")
def elements():
    return load_elements()


def test_all_118_load(elements):
    assert len(elements) == 118
    assert [e.number for e in elements] == list(range(1, 119))


def test_symbols_unique_and_correct(elements):
    assert len({e.symbol for e in elements}) == 118
    expected = {
        1: "H", 2: "He", 3: "Li", 6: "C", 7: "N", 8: "O", 9: "F", 10: "Ne",
        11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P", 16: "S", 17: "Cl", 18: "Ar",
        19: "K", 20: "Ca", 26: "Fe", 29: "Cu", 30: "Zn", 47: "Ag", 53: "I", 74: "W",
        79: "Au", 80: "Hg", 82: "Pb", 86: "Rn", 92: "U", 94: "Pu", 118: "Og",
    }
    for z, sym in expected.items():
        assert by_number(elements, z).symbol == sym


def test_names_correct(elements):
    expected = {
        1: "Hydrogen", 2: "Helium", 26: "Iron", 47: "Silver", 82: "Lead",
        92: "Uranium", 103: "Lawrencium", 118: "Oganesson",
    }
    for z, name in expected.items():
        assert by_number(elements, z).name == name
    assert len({e.name for e in elements}) == 118


def test_table_positions(elements):
    e = by_number(elements, 1)
    assert (e.group, e.period, e.block) == (1, 1, "s")
    e = by_number(elements, 2)
    assert (e.group, e.period, e.block) == (18, 1, "s")
    e = by_number(elements, 26)
    assert (e.group, e.period, e.block) == (8, 4, "d")
    e = by_number(elements, 5)
    assert (e.group, e.period, e.block) == (13, 2, "p")
    # f-block has no group
    for z in range(57, 72):
        assert by_number(elements, z).group is None
        assert by_number(elements, z).category == "lanthanide"
    for z in range(89, 104):
        assert by_number(elements, z).group is None
        assert by_number(elements, z).category == "actinide"
    assert by_number(elements, 118).group == 18


def test_electron_counts(elements):
    for e in elements:
        assert sum(e.shells) == e.number, e.name
        tokens = e.electron_configuration_full.split()
        total = 0
        for tok in tokens:
            total += int(tok[2:]) if tok[1] in "spdf" and tok[0].isdigit() else 0
        assert total == e.number, e.name


def test_known_configurations(elements):
    cases = {
        24: ("[Ar] 3d5 4s1", "1s2 2s2 2p6 3s2 3p6 3d5 4s1"),
        29: ("[Ar] 3d10 4s1", None),
        46: ("[Kr] 4d10", None),
        26: ("[Ar] 3d6 4s2", None),
    }
    for z, (short, full) in cases.items():
        e = by_number(elements, z)
        assert e.electron_configuration == short
        if full:
            assert e.electron_configuration_full == full


def test_school_shell_arrangements(elements):
    assert by_number(elements, 11).shells == (2, 8, 1)
    assert by_number(elements, 20).shells == (2, 8, 8, 2)
    assert by_number(elements, 26).shells == (2, 8, 14, 2)
    assert by_number(elements, 19).shells == (2, 8, 8, 1)


def test_atomic_masses(elements):
    assert by_number(elements, 1).atomic_mass == 1.008
    assert by_number(elements, 6).atomic_mass == 12.011
    assert by_number(elements, 26).atomic_mass == 55.845
    # bracketed = most stable isotope
    assert by_number(elements, 43).atomic_mass_type == "isotope"
    assert by_number(elements, 98).mass_string() == "[251]"
    # interval elements carry a range
    assert by_number(elements, 1).atomic_mass_range == (1.00784, 1.00811)
    assert by_number(elements, 17).atomic_mass_range is not None
    for e in elements:
        assert e.atomic_mass > 0


def test_states(elements):
    liquids = [e.name for e in elements if e.state == "liquid"]
    assert set(liquids) == {"Mercury", "Bromine"}
    gases = {e.symbol for e in elements if e.state == "gas"}
    assert "He" in gases and "Rn" in gases
    for e in elements:
        assert e.state in ("solid", "liquid", "gas")


def test_radioactive_and_synthetic(elements):
    radioactive = {e.number for e in elements if e.radioactive}
    assert 43 in radioactive and 61 in radioactive
    assert 84 in radioactive
    assert all(z in radioactive for z in range(84, 119))
    assert 83 not in radioactive  # bismuth treated as stable for practical purposes
    synthetic = {e.number for e in elements if e.synthetic}
    assert synthetic == {43, 61} | set(range(93, 119))
    # naturally occurring trace elements stay natural
    for z in (85, 87, 88, 89, 90, 91, 92):
        assert z not in synthetic


def test_discovery_data(elements):
    ancient = {e.name for e in elements if e.discovery.year == "ancient"}
    assert {"Iron", "Gold", "Lead"} <= ancient
    for e in elements:
        y = e.discovery.year
        assert y == "ancient" or (isinstance(y, int) and 1200 <= y <= 2026)
        assert e.discovery.by
    assert by_number(elements, 43).discovery.year == 1937  # technetium
    assert by_number(elements, 118).discovery.year == 2002


def test_oxidation_states(elements):
    assert by_number(elements, 8).oxidation_states_all == (-2, -1, 0, 1, 2)
    assert -2 in by_number(elements, 8).oxidation_states_common
    assert by_number(elements, 9).oxidation_states_common == (-1,)
    assert by_number(elements, 26).oxidation_states_common == (2, 3)
    for e in elements:
        assert all(isinstance(v, int) for v in e.oxidation_states_all)


def test_key_physical_values(elements):
    assert by_number(elements, 8).electronegativity == 3.44
    assert by_number(elements, 9).electronegativity == 3.98
    assert by_number(elements, 74).melt_k == 3695  # tungsten
    assert by_number(elements, 80).melt_k == 234.32  # mercury
    assert by_number(elements, 13).density_g_cm3 == 2.70
    assert by_number(elements, 11).ionization_energy_kj == 496


def test_uses_and_compounds_present(elements):
    for e in elements:
        assert isinstance(e.uses, tuple) and len(e.uses) >= 1
        assert isinstance(e.compounds, tuple)
    # Noble gases may form none; beyond mendelevium (Z 101) chemistry is
    # tracer-scale or absent, so compounds are optional there too.
    must_have = [
        e for e in elements
        if e.category != "noble gas" and e.number <= 101
    ]
    assert all(len(e.compounds) >= 1 for e in must_have)
    assert len(by_number(elements, 2).compounds) == 0  # helium forms none


def test_lookup_helpers(elements):
    assert by_symbol(elements, "fe").name == "Iron"
    assert by_symbol(elements, "FE").name == "Iron"
    assert by_name(elements, "  oxygen ").number == 8
    assert by_symbol(elements, "Xx") is None
    assert by_name(elements, "unobtainium") is None


def test_name_origins(elements):
    assert "Ytterby" in by_number(elements, 39).discovery.origin
    for e in elements:
        assert e.discovery.origin
