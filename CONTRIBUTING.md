# Contributing

1. Create a branch for the change.
2. Never add real account credentials or machine-specific calibration files.
3. Keep automation logic in `src/wotk/features/` and OS/UI primitives in `src/wotk/automation/`.
4. Add or update tests for deterministic logic.
5. Run `python -m compileall src`, `pytest`, and (when installed) `ruff check .` before opening a PR.
6. Document behavior changes in `CHANGELOG.md`.

Real-game integration should be tested on a disposable/non-critical setup first because coordinate
or window changes can make desktop automation click the wrong place.
