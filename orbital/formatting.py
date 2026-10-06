"""Field formatting shared by the detail panel, compare view and tooltips.

One formatter per field id, so numbers, units and "unknown" markers are
rendered identically everywhere.
"""
from __future__ import annotations

from orbital.profiles import FIELDS


def _num(value, decimals=None):
    if value is None:
        return None
    if decimals is not None:
        return "%.*f" % (decimals, value)
    return "%g" % value


def kelvin_pair(k):
    """'1811 K (1538 C)' or None."""
    if k is None:
        return None
    return "%.4g K (%.4g \u00b0C)" % (k, k - 273.15)


def density_string(element):
    d = element.density_g_cm3
    if d is None:
        return None
    if element.state == "gas":
        return "%.4g g/L" % (d * 1000)
    if d < 0.01:
        return "%.4g g/cm\u00b3" % d
    return "%.4g g/cm\u00b3" % d


def oxidation_string(element, common_only=False):
    states = element.oxidation_states_common if common_only else element.oxidation_states_all
    if not states:
        return None
    out = []
    for v in states:
        out.append(("\u2212%d" % -v) if v < 0 else ("+%d" % v if v > 0 else "0"))
    return ", ".join(out)


def group_string(element):
    if element.group is None:
        return None  # f-block: no group
    return str(element.group)


def discovery_string(element):
    y = element.discovery.year
    if y == "ancient":
        return "Known since antiquity"
    return "%d \u2014 %s" % (y, element.discovery.by)


def mass_string(element, precision: int = 3):
    if element.atomic_mass_type == "isotope":
        return "[%g]" % round(element.atomic_mass)
    text = "%.*f" % (max(precision, 1), element.atomic_mass)
    text = text.rstrip("0").rstrip(".")
    return text or "0"


def mass_note(element):
    if element.atomic_mass_type == "isotope":
        return "Bracketed value: the mass of the longest-lived isotope \u2014 the element has no standard atomic weight."
    if element.atomic_mass_type == "interval":
        return "Standard atomic weight is an interval: [%s, %s]" % tuple(
            "%g" % v for v in element.atomic_mass_range
        )
    return None


def field_value(element, field_id: str, *, config_style: str = "short",
                ox_common_only: bool = False, mass_precision: int = 3):
    """Return the display value for a field: a string, a tuple of strings,
    or None when unknown (the UI shows an em dash)."""
    if field_id == "number":
        return str(element.number)
    if field_id == "symbol":
        return element.symbol
    if field_id == "name":
        return element.name
    if field_id == "atomic_mass":
        return mass_string(element, mass_precision)
    if field_id == "group":
        return group_string(element)
    if field_id == "period":
        return str(element.period)
    if field_id == "block":
        return element.block + "-block"
    if field_id == "category":
        return element.category.title().replace("Post-Transition", "Post-transition")
    if field_id == "state":
        return element.state_string()
    if field_id == "configuration":
        return (element.electron_configuration_full
                if config_style == "full" else element.electron_configuration)
    if field_id == "shells":
        return element.shells_string()
    if field_id == "oxidation_states":
        return oxidation_string(element, common_only=ox_common_only)
    if field_id == "electronegativity":
        return _num(element.electronegativity)
    if field_id == "ionization":
        if element.ionization_energy_kj is None:
            return None
        return "%g kJ/mol" % element.ionization_energy_kj
    if field_id == "radius":
        if element.atomic_radius_pm is None:
            return None
        return "%g pm" % element.atomic_radius_pm
    if field_id == "melt":
        return kelvin_pair(element.melt_k)
    if field_id == "boil":
        return kelvin_pair(element.boil_k)
    if field_id == "density":
        return density_string(element)
    if field_id == "uses":
        return tuple(element.uses)
    if field_id == "compounds":
        return tuple(element.compounds)
    if field_id == "discovered":
        return discovery_string(element)
    if field_id == "origin":
        return element.discovery.origin
    if field_id == "abundance":
        if element.abundance_ppm is None:
            return None
        return "%s ppm (crust)" % format(element.abundance_ppm, ",.4g").replace(",", " ")
    if field_id == "mass_note":
        return mass_note(element)
    raise ValueError("unknown field: %r" % field_id)


def field_label(field_id: str) -> str:
    return FIELDS[field_id][1]


def formula_html(text: str) -> str:
    """Format 'H2O — water' for a Qt rich-text label: digits that follow an
    element symbol or closing bracket become subscripts."""
    import html
    import re as _re

    escaped = html.escape(text, quote=False)
    return _re.sub(
        r"(?<=[A-Za-z\)\]])\d+",
        lambda m: "<sub>%s</sub>" % m.group(0),
        escaped,
    )
