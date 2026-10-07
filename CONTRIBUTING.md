# Contributing

Thanks for wanting to help. Orbital is deliberately small — the best
contributions keep it that way.

## Data corrections

Chemistry accuracy is the whole point of the app. If a value is wrong:

1. Edit the element's file in `orbital/data/elements/<name>.json` — one
   file per element, so a fix is a one-file diff.
2. Check it against the sources listed in
   [docs/data-sources.md](docs/data-sources.md) and name the source in
   the PR.
3. Run the tests — the data layer validates all 118 elements on load
   (electron counts, shell sums, symbol uniqueness, category sanity).

Element files are the single source of truth. Nothing in the UI may
hardcode element facts — if you find a violation, that's a bug.

## Code

- Python 3.10+, PySide6 (Qt 6) for the UI, no other runtime dependencies.
- The data layer (`orbital/data`) and layout engine (`orbital/layouts.py`)
  are pure Python with no Qt imports — keep them that way; they're the
  testable core.
- New table layouts belong in `orbital/layouts.py` as a build function
  registered in `LAYOUTS`. They must pass `validate_layout`.
- New colour modes go in `orbital/ui/colors.py` and get a legend entry —
  unexplained colours are a bug, not a feature.

## Testing

```sh
python -m pip install -e .[dev]
python -m pytest
```

The UI tests run offscreen, so everything works headless on any platform.

## Packaging

- macOS: `scripts/build_mac.sh` (needs Xcode CLT + hdiutil)
- Windows: `scripts/build_windows.ps1`
- Linux: `scripts/build_linux.sh`

## Design rules

These are deliberate — please preserve them:

- Offline-first. No network requests, no accounts, no telemetry.
- The periodic table dominates the window; chrome stays quiet.
- No gratuitous animation, gradients or glass effects.
- Every colour means something, and the legend says what.
- Keyboard access is a feature, not an afterthought.

## Commit style

Conventional-ish and imperative, e.g. `fix: wrong boiling point for
bismuth`, `feat: add atomic radius colour mode`.
