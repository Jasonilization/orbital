"""Search over the element data. Pure logic, no Qt.

Queries match element name, symbol, or atomic number, ranked sensibly:
exact symbol > exact name > name prefix > symbol prefix > substring > number.
Category phrases ("alkali metals", "noble gases", "radioactive", ...) resolve
to filter results, so the same box can be used for both.
"""
from __future__ import annotations

import re

_WORD_RE = re.compile(r"[a-z0-9]+")

# Phrase -> predicate over Element.
_PHRASES = {
    "alkali metal": lambda e: e.category == "alkali metal",
    "alkali metals": lambda e: e.category == "alkali metal",
    "alkaline earth metal": lambda e: e.category == "alkaline earth metal",
    "alkaline earth metals": lambda e: e.category == "alkaline earth metal",
    "alkaline earth": lambda e: e.category == "alkaline earth metal",
    "transition metal": lambda e: e.category == "transition metal",
    "transition metals": lambda e: e.category == "transition metal",
    "post transition metal": lambda e: e.category == "post-transition metal",
    "post transition metals": lambda e: e.category == "post-transition metal",
    "post-transition": lambda e: e.category == "post-transition metal",
    "metalloid": lambda e: e.category == "metalloid",
    "metalloids": lambda e: e.category == "metalloid",
    "nonmetal": lambda e: e.category == "nonmetal",
    "nonmetals": lambda e: e.category == "nonmetal",
    "non metal": lambda e: e.category == "nonmetal",
    "non metals": lambda e: e.category == "nonmetal",
    "halogen": lambda e: e.category == "halogen",
    "halogens": lambda e: e.category == "halogen",
    "noble gas": lambda e: e.category == "noble gas",
    "noble gases": lambda e: e.category == "noble gas",
    "lanthanide": lambda e: e.category == "lanthanide",
    "lanthanides": lambda e: e.category == "lanthanide",
    "actinide": lambda e: e.category == "actinide",
    "actinides": lambda e: e.category == "actinide",
    "metal": lambda e: e.category in (
        "alkali metal", "alkaline earth metal", "transition metal",
        "post-transition metal", "lanthanide", "actinide"),
    "metals": lambda e: e.category in (
        "alkali metal", "alkaline earth metal", "transition metal",
        "post-transition metal", "lanthanide", "actinide"),
    "radioactive": lambda e: e.radioactive,
    "synthetic": lambda e: e.synthetic,
    "man made": lambda e: e.synthetic,
    "natural": lambda e: not e.synthetic,
    "gas": lambda e: e.state == "gas",
    "gases": lambda e: e.state == "gas",
    "liquid": lambda e: e.state == "liquid",
    "liquids": lambda e: e.state == "liquid",
    "solid": lambda e: e.state == "solid",
    "solids": lambda e: e.state == "solid",
}


def normalize(query: str) -> str:
    return " ".join(_WORD_RE.findall(query.lower()))


def search(query: str, elements):
    """Return elements matching the query, best first. Empty query -> []."""
    q = normalize(query)
    if not q:
        return []
    q = q.replace(" ", "")

    # Multi-word queries like "alkali metals" first: try with the space kept.
    spaced = normalize(query)
    if spaced in _PHRASES:
        pred = _PHRASES[spaced]
        return [e for e in elements if pred(e)]

    results = []
    for e in elements:
        name = e.name.lower()
        symbol = e.symbol.lower()
        score = 0
        if q == symbol:
            score = 100
        elif q == name:
            score = 90
        elif name.startswith(q):
            score = 80
        elif symbol.startswith(q) and len(q) <= len(symbol):
            score = 70
        elif q in name:
            score = 50
        if score == 0 and q.isdigit():
            if str(e.number) == q:
                score = 40
            elif str(e.number).startswith(q) and len(q) > 1:
                score = 30
        if score:
            results.append((score, e.number, e))
    results.sort(key=lambda t: (-t[0], t[1]))
    return [e for _s, _n, e in results]


def suggest(elements, prefix: str, limit: int = 8):
    """Typeahead-style suggestions for the search box."""
    return search(prefix, elements)[:limit]
