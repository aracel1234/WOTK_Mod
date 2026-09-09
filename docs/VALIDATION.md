# Validation status

## Automated validation included

The project is checked with:

- Python bytecode compilation;
- deterministic unit tests using `RecordingBackend`;
- model/config validation tests;
- route-index and hero-rotation tests;
- deterministic Individual/Mysteriland button sequence tests;
- multi-instance config parsing tests;
- GitHub Actions on supported Python versions.

## Not validated in the build environment

The build environment used to prepare the repository is not the final Windows game machine. The
following cannot be truthfully certified without the user's local setup:

- UC Browser executable/title and real website state;
- actual game buttons/coordinates;
- DPI scaling and per-window client rectangles;
- Sandboxie-Plus installation and box policy;
- real Tesseract OCR quality on the chosen regions;
- network/game latency;
- game-specific state transitions after Fight, Dispatch, Watch, March, and Assault.

## Acceptance test before normal use

1. Set Windows display scaling/resolution to the value used during calibration.
2. Run `python scripts/verify_setup.py`.
3. Run one module with the smallest workload.
4. Keep the mouse near a screen corner so PyAutoGUI FAILSAFE is available.
5. Confirm every click and OCR state in the Activity Log.
6. For Auto War, use `max_cycles: 1` and a short temporary `cycle_minutes` during calibration.
7. For multi-instance, start with one instance and then add instances one by one.
8. Only after successful local testing restore production delays/cycle settings.
