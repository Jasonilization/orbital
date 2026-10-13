# Orbital — full feature list

Everything the app does, as of v1.0.0. Written for the person using it,
not for a store page.

## The table

- **118 elements**, one JSON file each in `orbital/data/elements/` — the
  complete dataset is always present; levels and filters only change what
  you *see*
- **4 layouts** (Ctrl+1…4): Standard 18-column, Compact, Extended
  32-column (f-block inline), School (groups 1–7 and 0)
- **15 colour modes**: category, block, state, group, period, atomic mass,
  melting point, boiling point, electronegativity, density, ionisation
  energy, discovery era, natural/synthetic, radioactive, monochrome —
  the legend under the table always explains the colours
- **Zoom**: − / % / + buttons in the toolbar, Ctrl+= / Ctrl+− / Ctrl+0,
  or **Ctrl + scroll wheel** over the table (80%–160%). Zooming resizes
  tiles in place — it doesn't rebuild anything
- **Navigation**: arrow keys walk the grid, Enter opens, drag the
  background to pan, scroll to move. The `57–71` / `89–103` marker cells
  jump to the f-block
- **Export**: File → Export table as image (PNG)

## Education levels

One setting changes how much detail each element shows — the data itself
never changes:

- **General** — one facts line (group · period · state · mass), shells,
  melting/boiling, density, uses, compounds
- **IGCSE** — built for the Cambridge 0620 assessment: the 46 data-sheet
  elements highlighted (*Syllabus only* toggle), simple atomic masses
  exactly as the data sheet prints them (O 16, Cl 35.5, Cu 63.5), shells
  as 2, 8, 1, common oxidation states
- **A Level** — full electron configurations, all oxidation states,
  electronegativity, atomic radius
- **Advanced** — everything: ionisation energies, crustal abundance,
  atomic-weight intervals, discovery details

Every hidden thing stays one click away: the "+ More detail" button
reveals toggle chips (Config, Oxidation, Electroneg., Ionisation,
Radius, History) that apply instantly and persist.

## Search & filtering

- `/` or Ctrl+F focuses search; **name, symbol, or atomic number**, ranked
  (typing `o` finds Oxygen first). Category phrases work: `noble gases`,
  `alkali metals`, `radioactive`, `synthetic`…
- Matches stay bright; everything else dims
- Filter dialog: category, state, block, natural/synthetic, radioactive,
  discovery-year range — live count in the status bar, one click clears

## Detail panel

- Compact facts line instead of a wall of labels
- Collapsible sections with icons: Chemistry (flask), Uses (box),
  History (clock), More detail (layers)
- Long lists cap at 3 items with a "+N more" link
- Right-click any tile: Open, Add to comparison, Copy details

## Compare

- Up to 4 elements side by side, one click each (Ctrl+Shift+C from a tile)
- 16 property rows, IGCSE-aware masses

## First-run wizard

- 3 steps: level → theme & accent → done summary. **Skip setup** on any
  step keeps defaults and never nags again (Help → First-time setup…
  re-opens it)

## Appearance

- Light / Dark / System themes; **sun/moon button in the toolbar**
- 6 restrained accent colours
- Tile text is measured, so it can never overlap at any zoom

## Data you can trust

- Atomic masses: CIAAW *Abridged Standard Atomic Weights* (2024 table),
  pinned by test
- Electron configurations: all 118 pinned against the NIST-based
  reference table, including every known ground-state anomaly
- Ionisation energies, melting/boiling points audited against reference
  tables; corrections applied (Tc 686.9, Fr 393, At 503, Pa 231.04, C
  sublimes…)
- Superheavy values are labelled predictions in `docs/data-sources.md` —
  the app never presents a guess as a measurement
- **147 automated tests** run headless on macOS, Windows and Linux in CI

## Offline & privacy

- No network code exists. No account, no telemetry, no cloud
- Settings stored natively per OS (macOS defaults, Windows registry,
  Linux INI) and nothing else

## Keyboard

| Key | Action |
|---|---|
| `/` or Ctrl+F | search |
| arrows | move |
| Enter | open |
| Esc | clear search → filters → close panel |
| Ctrl+1…4 | layout |
| Ctrl+= / − / 0 or Ctrl+scroll | zoom |
| Ctrl+Shift+C | compare |
| Ctrl+Shift+E | export PNG |
| Ctrl+, | settings |

## Packaging

- macOS `.app` + `.dmg` (ad-hoc signed), Windows portable zip, Linux
  tarball/AppImage — built by the same CI that runs the tests
