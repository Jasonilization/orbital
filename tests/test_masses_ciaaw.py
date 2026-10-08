"""Atomic mass audit against the CIAAW 'Abridged Standard Atomic Weights
2024' table (five significant figures; based on the Atomic Weights 2021
report, including the 2024 gadolinium/lutetium/zirconium revisions).

The reference values below are transcribed from ciaaw.org. Interval
elements carry their full-table intervals; elements without a standard
atomic weight (no stable/natural isotope situation) must use bracketed
most-stable-isotope masses.
"""
import pytest

from orbital.data import load_elements


# symbol -> (abridged display value, interval or None)
CIAAW_2024_ABRIDGED = {
    "H": (1.008, (1.00784, 1.00811)),
    "He": (4.0026, None),
    "Li": (6.94, (6.938, 6.997)),
    "Be": (9.0122, None),
    "B": (10.81, (10.806, 10.821)),
    "C": (12.011, (12.0096, 12.0116)),
    "N": (14.007, (14.00643, 14.00728)),
    "O": (15.999, (15.99903, 15.99977)),
    "F": (18.998, None),
    "Ne": (20.180, None),
    "Na": (22.990, None),
    "Mg": (24.305, (24.304, 24.307)),
    "Al": (26.982, None),
    "Si": (28.085, (28.084, 28.086)),
    "P": (30.974, None),
    "S": (32.06, (32.059, 32.076)),
    "Cl": (35.45, (35.446, 35.457)),
    "Ar": (39.95, (39.792, 39.963)),
    "K": (39.098, None),
    "Ca": (40.078, None),
    "Sc": (44.956, None),
    "Ti": (47.867, None),
    "V": (50.942, None),
    "Cr": (51.996, None),
    "Mn": (54.938, None),
    "Fe": (55.845, None),
    "Co": (58.933, None),
    "Ni": (58.693, None),
    "Cu": (63.546, None),
    "Zn": (65.38, None),
    "Ga": (69.723, None),
    "Ge": (72.630, None),
    "As": (74.922, None),
    "Se": (78.971, None),
    "Br": (79.904, (79.901, 79.907)),
    "Kr": (83.798, None),
    "Rb": (85.468, None),
    "Sr": (87.62, None),
    "Y": (88.906, None),
    "Zr": (91.222, None),   # revised by CIAAW in 2024
    "Nb": (92.906, None),
    "Mo": (95.95, None),
    "Ru": (101.07, None),
    "Rh": (102.91, None),
    "Pd": (106.42, None),
    "Ag": (107.87, None),
    "Cd": (112.41, None),
    "In": (114.82, None),
    "Sn": (118.71, None),
    "Sb": (121.76, None),
    "Te": (127.60, None),
    "I": (126.90, None),
    "Xe": (131.29, None),
    "Cs": (132.91, None),
    "Ba": (137.33, None),
    "La": (138.91, None),
    "Ce": (140.12, None),
    "Pr": (140.91, None),
    "Nd": (144.24, None),
    "Sm": (150.36, None),
    "Eu": (151.96, None),
    "Gd": (157.25, None),   # revised by CIAAW in 2024
    "Tb": (158.93, None),
    "Dy": (162.50, None),
    "Ho": (164.93, None),
    "Er": (167.26, None),
    "Tm": (168.93, None),
    "Yb": (173.05, None),
    "Lu": (174.97, None),   # revised by CIAAW in 2024
    "Hf": (178.49, None),
    "Ta": (180.95, None),
    "W": (183.84, None),
    "Re": (186.21, None),
    "Os": (190.23, None),
    "Ir": (192.22, None),
    "Pt": (195.08, None),
    "Au": (196.97, None),
    "Hg": (200.59, None),
    "Tl": (204.38, (204.382, 204.385)),
    "Pb": (207.2, (206.14, 207.94)),
    "Bi": (208.98, None),
    "Th": (232.04, None),
    "Pa": (231.04, None),
    "U": (238.03, None),
}

# Elements with no standard atomic weight: bracketed most-stable-isotope mass.
NO_STANDARD_WEIGHT = set(
    "Tc Pm Po At Rn Fr Ra Ac Np Pu Am Cm Bk Cf Es Fm Md No Lr "
    "Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split()
)


@pytest.fixture(scope="module")
def elements():
    return load_elements()


def test_abridged_display_matches_ciaaw(elements):
    for e in elements:
        if e.symbol in NO_STANDARD_WEIGHT:
            assert e.atomic_mass_type == "isotope", e.symbol
            continue
        expected, interval = CIAAW_2024_ABRIDGED[e.symbol]
        assert abs(e.atomic_mass - expected) < 0.0005, (
            "%s: stored %s, CIAAW abridged %s" % (e.symbol, e.atomic_mass, expected))
        if interval:
            assert e.atomic_mass_type == "interval", e.symbol
            assert e.atomic_mass_range == tuple(interval), (
                e.symbol, e.atomic_mass_range, interval)
            # the abridged display value may round slightly outside the
            # interval (CIAAW's own convention, e.g. oxygen: 15.999 vs
            # [15.99903, 15.99977]) — matching the abridged table is the
            # authoritative check
        else:
            assert e.atomic_mass_type == "standard", e.symbol


def test_interval_elements_complete(elements):
    intervals = {e.symbol for e in elements if e.atomic_mass_type == "interval"}
    expected_intervals = {
        s for s, (_v, iv) in CIAAW_2024_ABRIDGED.items() if iv is not None
    }
    assert intervals == expected_intervals


def test_isotope_masses_are_bracketed(elements):
    for e in elements:
        if e.symbol in NO_STANDARD_WEIGHT:
            assert e.mass_string().startswith("["), e.symbol


def test_zirconium_2024_revision(elements):
    zr = [e for e in elements if e.symbol == "Zr"][0]
    assert abs(zr.atomic_mass - 91.222) < 0.0005
