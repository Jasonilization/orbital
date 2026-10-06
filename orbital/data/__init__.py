"""Element data layer.

The 118 element JSON files in ``elements/`` are the source of truth for all
chemistry data. Nothing in the UI may hardcode element facts; everything is
read through :class:`Element` / :func:`load_elements`.

Derived values (full electron configuration, shell arrangement, oxidation
state lists) are computed here so the data files stay small and the rules
live in exactly one place.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent / "elements"

CATEGORIES = (
    "alkali metal",
    "alkaline earth metal",
    "transition metal",
    "post-transition metal",
    "metalloid",
    "nonmetal",
    "halogen",
    "noble gas",
    "lanthanide",
    "actinide",
)

BLOCKS = ("s", "p", "d", "f")
STATES = ("solid", "liquid", "gas")

_TOKEN_RE = re.compile(r"^(\d)([spdf])(\d+)$")
_NOBLE_CORE_RE = re.compile(r"^\[([A-Za-z]+)\]$")


@dataclass(frozen=True)
class Discovery:
    year: object  # int, or the string "ancient"
    by: str
    origin: str


@dataclass(frozen=True)
class Element:
    number: int
    symbol: str
    name: str
    atomic_mass: float
    group: Optional[int]
    period: int
    block: str
    category: str
    state: str
    electron_configuration: str  # noble-gas shorthand, e.g. "[Ar] 3d5 4s1"
    oxidation_states: tuple  # raw tokens like "-2*", "+3"
    electronegativity: Optional[float]
    ionization_energy_kj: Optional[float]
    atomic_radius_pm: Optional[float]
    melt_k: Optional[float]
    boil_k: Optional[float]
    density_g_cm3: Optional[float]
    abundance_ppm: Optional[float]
    radioactive: bool
    synthetic: bool
    discovery: Discovery
    uses: tuple
    compounds: tuple
    atomic_mass_type: str = "standard"  # standard | interval | isotope
    atomic_mass_range: Optional[tuple] = None
    electron_configuration_full: str = ""
    shells: tuple = ()

    # -- derived / convenience ------------------------------------------------

    @property
    def oxidation_states_common(self) -> tuple:
        return tuple(
            int(tok.rstrip("*")) for tok in self.oxidation_states if tok.endswith("*")
        )

    @property
    def oxidation_states_all(self) -> tuple:
        return tuple(int(tok.rstrip("*")) for tok in self.oxidation_states)

    def state_string(self) -> str:
        return {"solid": "Solid", "liquid": "Liquid", "gas": "Gas"}.get(
            self.state, "Unknown"
        )

    def mass_string(self, precision: int = 0) -> str:
        if self.atomic_mass_type == "isotope":
            return "[%g]" % round(self.atomic_mass)
        text = "%.*f" % (precision if precision else 3, self.atomic_mass)
        if precision:
            return text
        return text.rstrip("0").rstrip(".") if "." in text else text

    def mass_range_string(self) -> str:
        if self.atomic_mass_range:
            return "[%s, %s]" % tuple(self.atomic_mass_range)
        return ""

    def config_string(self, style: str = "full") -> str:
        return self.electron_configuration_full if style == "full" else self.electron_configuration

    def shells_string(self) -> str:
        return ", ".join(str(n) for n in self.shells)


def _parse_oxidation_states(raw) -> tuple:
    if raw is None:
        return ()
    out = []
    for tok in raw:
        t = str(tok).strip()
        if not re.match(r"^(?:[+-]\d+|0)\*?$", t):
            raise ValueError("bad oxidation state token: %r" % t)
        out.append(t)
    return tuple(out)


def _config_tokens(config: str):
    """Yield (n, subshell, count) tuples for a shorthand config string."""
    for part in config.split():
        m = _NOBLE_CORE_RE.match(part)
        if m:
            symbol = m.group(1)
            core = _CORE_CONFIGS[symbol]
            yield from _config_tokens(core)
            continue
        m = _TOKEN_RE.match(part)
        if not m:
            raise ValueError("bad configuration token: %r" % part)
        n, sub, count = int(m.group(1)), m.group(2), int(m.group(3))
        yield (n, sub, count)


def _expand_config(config: str) -> str:
    """Expand noble-gas shorthand to the full configuration string."""
    parts = []
    for part in config.split():
        m = _NOBLE_CORE_RE.match(part)
        if m:
            parts.append(_expand_config(_CORE_CONFIGS[m.group(1)]))
        else:
            parts.append(part)
    return " ".join(parts)


def _shells_from_config(config: str) -> tuple:
    shells = {}
    for n, _sub, count in _config_tokens(config):
        shells[n] = shells.get(n, 0) + count
    if not shells:
        return ()
    return tuple(shells[i] for i in range(1, max(shells) + 1))


# Noble-gas cores, spelled out in terms of the next core up (kept literal so
# the expansion cannot silently depend on load order).
_CORE_CONFIGS = {
    "He": "1s2",
    "Ne": "[He] 2s2 2p6",
    "Ar": "[Ne] 3s2 3p6",
    "Kr": "[Ar] 3d10 4s2 4p6",
    "Xe": "[Kr] 4d10 5s2 5p6",
    "Rn": "[Xe] 4f14 5d10 6s2 6p6",
}


def _element_from_json(data: dict) -> Element:
    d = Discovery(
        year=data["discovered"]["year"],
        by=data["discovered"]["by"],
        origin=data["discovered"].get("origin", ""),
    )
    return Element(
        number=data["number"],
        symbol=data["symbol"],
        name=data["name"],
        atomic_mass=float(data["atomic_mass"]),
        group=data.get("group"),
        period=data["period"],
        block=data["block"],
        category=data["category"],
        state=data.get("state", "unknown"),
        electron_configuration=data["electron_configuration"],
        oxidation_states=_parse_oxidation_states(data.get("oxidation_states")),
        electronegativity=data.get("electronegativity"),
        ionization_energy_kj=data.get("ionization_energy_kj"),
        atomic_radius_pm=data.get("atomic_radius_pm"),
        melt_k=data.get("melt_k"),
        boil_k=data.get("boil_k"),
        density_g_cm3=data.get("density_g_cm3"),
        abundance_ppm=data.get("abundance_ppm"),
        radioactive=bool(data.get("radioactive", False)),
        synthetic=bool(data.get("synthetic", False)),
        discovery=d,
        uses=tuple(data.get("uses", ())),
        compounds=tuple(data.get("compounds", ())),
        atomic_mass_type=data.get("atomic_mass_type", "standard"),
        atomic_mass_range=tuple(data["atomic_mass_range"]) if data.get("atomic_mass_range") else None,
        electron_configuration_full=_expand_config(data["electron_configuration"]),
        shells=_shells_from_config(data["electron_configuration"]),
    )


@lru_cache(maxsize=1)
def load_elements() -> tuple:
    """Load, validate and return all 118 elements ordered by atomic number."""
    elements = []
    for path in sorted(DATA_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            elements.append(_element_from_json(json.load(f)))

    elements.sort(key=lambda e: e.number)
    _validate(elements)
    return tuple(elements)


def _validate(elements) -> None:
    numbers = [e.number for e in elements]
    if numbers != list(range(1, 119)):
        raise ValueError(
            "expected exactly the atomic numbers 1-118, got %d elements" % len(elements)
        )
    symbols = [e.symbol for e in elements]
    if len(set(symbols)) != 118:
        raise ValueError("duplicate element symbols")
    names = [e.name for e in elements]
    if len(set(names)) != 118:
        raise ValueError("duplicate element names")
    for e in elements:
        if e.category not in CATEGORIES:
            raise ValueError("%s: bad category %r" % (e.name, e.category))
        if e.block not in BLOCKS:
            raise ValueError("%s: bad block %r" % (e.name, e.block))
        if e.state not in STATES:
            raise ValueError("%s: bad state %r" % (e.name, e.state))
        if sum(e.shells) != e.number:
            raise ValueError(
                "%s: shells %s sum to %d, not %d"
                % (e.name, e.shells, sum(e.shells), e.number),
            )
        # Full config must contain exactly Z electrons.
        total = sum(c for _n, _s, c in _config_tokens(e.electron_configuration))
        if total != e.number:
            raise ValueError(
                "%s: configuration %s has %d electrons, not %d"
                % (e.name, e.electron_configuration, total, e.number),
            )
        if e.group is not None and not 1 <= e.group <= 18:
            raise ValueError("%s: bad group %d" % (e.name, e.group))
        if not 1 <= e.period <= 7:
            raise ValueError("%s: bad period %d" % (e.name, e.period))


def by_number(elements, number: int) -> Element:
    return elements[number - 1]


def by_symbol(elements, symbol: str):
    symbol = symbol.strip().capitalize()
    for e in elements:
        if e.symbol == symbol:
            return e
    return None


def by_name(elements, name: str):
    name = name.strip().lower()
    for e in elements:
        if e.name.lower() == name:
            return e
    return None
