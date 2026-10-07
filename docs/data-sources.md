# Element data sources and accuracy notes

Orbital ships with a complete, self-contained dataset for all 118 elements
(`orbital/data/elements/*.json`, one file per element). This page documents
where each field comes from and how much to trust it. Where a value is
unknown or only estimated, the data says so rather than pretending.

## Primary sources

| Field | Source |
|---|---|
| Relative atomic masses | IUPAC/CIAAW *Abridged atomic weights (2021)*, rounded to 5 significant figures |
| Electron configurations | NIST Atomic Spectra Database, ground-state assignments (including the known anomalies: Cr, Cu, Nb, Mo, Ru, Rh, Pd, Ag, Pt, Au, La, Ce, Gd, Ac, Th, Pa, U, Np, Cm, Lr) |
| First ionisation energies | NIST (kJ/mol) |
| Electronegativity | Pauling scale |
| Melting/boiling points | CRC *Handbook of Chemistry and Physics*-style values at 1 atm |
| Densities | CRC-style; gases stored in g/cm³ and displayed as g/L |
| Atomic radii | Empirical (Slater) values, pm |
| Crustal abundance | CRC-style ppm; omitted where not meaningful |
| Discovery year/attribution | Standard historical attributions; "ancient" for the nine elements known since prehistory |
| Categories, blocks, groups | IUPAC conventions (La/Ac placed in the group-3 column in the extended layout) |

## Derived values

- **Shell arrangements** (e.g. Fe = 2, 8, 14, 2) are derived at load time
  from the full electron configuration by grouping electrons by principal
  quantum number. This is the presentation used in school chemistry.
- **Full configurations** are expanded from the noble-gas shorthand at
  load time, so both notations are always consistent.

## Known limitations (by design, stated)

- **Standard atomic weight intervals.** For the elements whose isotopic
  composition varies in nature (H, Li, B, C, N, O, Si, S, Cl, Tl), the
  database stores the conventional single value **and** the IUPAC interval.
  The detail panel shows the interval in the *More detail* section.
- **Synthetic elements (Z ≥ 93, plus Tc and Pm).** The bracketed atomic
  mass is the mass number of the most stable known isotope — there is no
  standard atomic weight.
- **Superheavy elements (Z ≥ 104).** Melting points, boiling points,
  densities and oxidation states are *predictions* (relativistic
  calculations, single-atom experiments), not measurements. Copernicium,
  for example, is predicted to be a volatile liquid near room temperature;
  treat every superheavy value as provisional.
- **Oxidation states** follow standard reference lists; for the
  superheavies the listed states are theoretically predicted. A star
  (`*`) marks the commonly cited states — what the IGCSE level shows.
- **Bismuth** is treated as non-radioactive (its half-life exceeds a
  billion times the age of the universe), which matches everyday practice.
- **Astatine's** melting/boiling points are commonly cited estimates.

## Uses and compounds

Curated short summaries written for the education profiles — practical
rather than exhaustive, and deliberately conservative for toxic or
synthetic elements. If you spot an inaccuracy, a data fix is a one-file
PR (see [CONTRIBUTING](../CONTRIBUTING.md)).

## Jokes

`orbital/data/jokes.json` is a hand-curated set of 200. Where a joke
contains a factual claim (the Radium Girls, Haber's legacy, the four
Ytterby elements, Curie's glowing notebooks), the claim is real — the rest
is puns.

Dataset version: 1.0.0 (October 2026). Corrections welcome; the data
files are the source of truth and never generated at runtime.
