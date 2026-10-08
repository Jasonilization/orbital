# Element data sources and accuracy notes

Orbital ships with a complete, self-contained dataset for all 118 elements
(`orbital/data/elements/*.json`, one file per element). This page documents
where each field comes from and how much to trust it. Where a value is
unknown or only estimated, the data says so rather than pretending.

## Primary sources

| Field | Source |
|---|---|
| Relative atomic masses | CIAAW *Abridged Standard Atomic Weights* (the 2024 table, based on the Atomic Weights 2021 report, incl. the 2024 Gd/Lu/Zr revisions), 5 significant figures |
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

- **Standard atomic weight intervals.** For the 14 elements whose
  isotopic composition varies in nature (H, Li, B, C, N, O, Mg, Si, S,
  Cl, Ar, Br, Tl, Pb), the database stores the abridged display value
  **and** the full CIAAW interval. The detail panel shows the interval in
  the *More detail* section. (Argon's abridged value 39.95 rounds just
  outside its own interval — that's CIAAW's convention, kept verbatim.)
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
- **First ionisation energies** follow the reference molar table
  (kJ/mol); from rutherfordium (Z 104) onward they are predictions.
  Technetium (686.9), francium (393), astatine (899) and fermium (629)
  reflect the measured/published values rather than older estimates.
  Protactinium has a standard atomic weight (231.04) — it occurs
  naturally, unlike the bracketed elements around it.
- **Bismuth** is treated as non-radioactive (its half-life exceeds a
  billion times the age of the universe), which matches everyday practice.
- **Astatine's** melting point is a commonly cited estimate; its boiling
  point (503 K) follows Otozai's 1982 radio-gas-chromatography estimate.
- **Carbon** does not melt at 1 atm — graphite *sublimes* around 3915 K.
  The dataset stores no melting point and shows the sublimation
  temperature for the boiling-point field, which is what every reference
  table does.
- **Francium's** melting point (~300 K) is an estimate; older references
  (and the CRC) give 27 °C, Lavrukhina gives 8 °C — we follow the more
  commonly cited 27 °C-derived value.

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
