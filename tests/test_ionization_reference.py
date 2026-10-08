"""First ionisation energies audited against the reference table of molar
ionisation energies (kJ/mol). Values from rutherfordium (Z 104) onward are
predictions the reference labels as such; they are included here because
the dataset deliberately carries predicted superheavy values (documented in
docs/data-sources.md). Tolerance is +/- 1 kJ/mol to allow rounding.
"""
import pytest

from orbital.data import load_elements


# first molar ionisation energies (kJ/mol), transcribed from the reference
REFERENCE = {
    1: 1312.0, 2: 2372.4, 3: 520.2, 4: 899.5, 5: 800.6, 6: 1086.5, 7: 1402.3,
    8: 1313.9, 9: 1681.0, 10: 2080.7, 11: 495.8, 12: 737.7, 13: 577.5,
    14: 786.5, 15: 1011.8, 16: 999.6, 17: 1251.2, 18: 1520.6, 19: 418.8,
    20: 589.8, 21: 633.1, 22: 658.8, 23: 650.9, 24: 652.9, 25: 717.3,
    26: 762.5, 27: 760.4, 28: 737.1, 29: 745.5, 30: 906.4, 31: 578.8,
    32: 762.0, 33: 947.0, 34: 941.0, 35: 1139.9, 36: 1350.8, 37: 403.0,
    38: 549.5, 39: 600.0, 40: 640.1, 41: 652.1, 42: 684.3, 43: 686.9,
    44: 710.2, 45: 719.7, 46: 804.4, 47: 731.0, 48: 867.8, 49: 558.3,
    50: 708.6, 51: 834.0, 52: 869.3, 53: 1008.4, 54: 1170.4, 55: 375.7,
    56: 502.9, 57: 538.1, 58: 534.4, 59: 527.0, 60: 533.1, 61: 540.0,
    62: 544.5, 63: 547.1, 64: 593.4, 65: 565.8, 66: 573.0, 67: 581.0,
    68: 589.3, 69: 596.7, 70: 603.4, 71: 523.5, 72: 658.5, 73: 761.0,
    74: 770.0, 75: 760.0, 76: 840.0, 77: 880.0, 78: 870.0, 79: 890.1,
    80: 1007.1, 81: 589.4, 82: 715.6, 83: 703.0, 84: 812.1, 85: 899.0,
    86: 1037.0, 87: 393.0, 88: 509.3, 89: 499.0, 90: 587.0, 91: 568.0,
    92: 597.6, 93: 604.5, 94: 584.7, 95: 578.0, 96: 581.0, 97: 601.0,
    98: 608.0, 99: 619.0, 100: 629.0, 101: 636.0, 102: 639.0, 103: 479.0,
    # predictions from here (rutherfordium onward)
    104: 580.0, 105: 665.0, 106: 757.0, 107: 740.0, 108: 730.0, 109: 800.0,
    110: 960.0, 111: 1020.0, 112: 1155.0, 113: 707.2, 114: 832.2, 115: 538.3,
    116: 663.9, 117: 736.9, 118: 860.1,
}


@pytest.fixture(scope="module")
def elements():
    return load_elements()


def test_first_ionization_energies_match_reference(elements):
    for e in elements:
        expected = REFERENCE[e.number]
        assert e.ionization_energy_kj is not None, e.symbol
        assert abs(e.ionization_energy_kj - expected) <= 1.0, (
            "%s: stored %s, reference %s"
            % (e.symbol, e.ionization_energy_kj, expected))


def test_measured_updates_present(elements):
    # values updated after real measurements, kept honest
    assert abs(elements[42].ionization_energy_kj - 686.9) < 0.5   # Tc, 2010
    assert abs(elements[86].ionization_energy_kj - 393.0) < 0.5  # Fr, 2018
    assert abs(elements[84].ionization_energy_kj - 899.0) < 0.5  # At
