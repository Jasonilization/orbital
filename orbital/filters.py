"""Element filtering. Pure logic, no Qt.

Empty/None means "no constraint". ``FilterSpec.is_active()`` tells the UI
whether any filter is applied.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Optional


@dataclass(frozen=True)
class FilterSpec:
    categories: frozenset = frozenset()
    states: frozenset = frozenset()
    blocks: frozenset = frozenset()
    groups: frozenset = frozenset()
    periods: frozenset = frozenset()
    synthetic: Optional[bool] = None
    radioactive: Optional[bool] = None
    discovered_before: Optional[int] = None
    discovered_after: Optional[int] = None

    def is_active(self) -> bool:
        return bool(
            self.categories or self.states or self.blocks or self.groups
            or self.periods
            or self.synthetic is not None or self.radioactive is not None
            or self.discovered_before is not None
            or self.discovered_after is not None
        )

    def summary(self) -> str:
        parts = []
        if self.categories:
            parts.append("category")
        if self.states:
            parts.append("state")
        if self.blocks:
            parts.append("block")
        if self.groups:
            parts.append("groups")
        if self.periods:
            parts.append("periods")
        if self.synthetic is not None:
            parts.append("synthetic" if self.synthetic else "natural")
        if self.radioactive is not None:
            parts.append("radioactive" if self.radioactive else "stable")
        if self.discovered_before is not None or self.discovered_after is not None:
            parts.append("discovery year")
        return ", ".join(parts)


def _discovery_year(element) -> Optional[int]:
    y = element.discovery.year
    if y == "ancient":
        return -1  # older than any explicit year
    return y


def matches(element, spec: FilterSpec) -> bool:
    if spec.categories and element.category not in spec.categories:
        return False
    if spec.states and element.state not in spec.states:
        return False
    if spec.blocks and element.block not in spec.blocks:
        return False
    if spec.groups:
        if element.group is None or element.group not in spec.groups:
            return False
    if spec.periods and element.period not in spec.periods:
        return False
    if spec.synthetic is not None and element.synthetic != spec.synthetic:
        return False
    if spec.radioactive is not None and element.radioactive != spec.radioactive:
        return False
    if spec.discovered_before is not None:
        y = _discovery_year(element)
        if y is None or y > spec.discovered_before:
            return False
    if spec.discovered_after is not None:
        y = _discovery_year(element)
        if y is None or y < spec.discovered_after:
            return False
    return True


def apply_filter(elements, spec: FilterSpec):
    if not spec.is_active():
        return list(elements)
    return [e for e in elements if matches(e, spec)]


def matching_numbers(elements, spec: FilterSpec):
    """Atomic numbers passing the filter — used by the table to dim tiles."""
    if not spec.is_active():
        return None
    return {e.number for e in elements if matches(e, spec)}
