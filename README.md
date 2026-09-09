# WOTK Mod 2.0

WOTK Mod is a Windows desktop automation project for **Clash of Three Kingdoms** workflows. This
version replaces the old collection of loosely coupled scripts with one maintainable Python package
and one Control Center GUI.

> **Important:** this software drives a real mouse/keyboard and depends on calibrated coordinates.
> Test with non-critical accounts first. UI changes, resolution scaling, pop-ups, or focus changes
> can cause misclicks. Use the project only where automation is permitted by the game/service rules.

## Included modules

| Module | Main capability |
|---|---|
| Auto Login | UC Browser login/register flow for multiple accounts; credentials are not saved by normal profile persistence. |
| Individual | Challenge → Crusade → Individual → stage/fight/quick/OK/reward/claim loops for 1–10 stages. |
| Mysteriland | 1–5 stage execution plus 1x/5x swipe action and separate stage-coordinate profiles. |
| Supremacy | 12 challenge choices, phase-1 direct fights, phase-2 bounded hero rotation, progress summary. |
| Auto War | Multi-account target attack, OCR Watch detection, March, chained Assault routing, `No hero can march` fallback, 31-minute cycle support. |
| Multi-Instance | Sandboxie-Plus launch support, per-instance client-relative coordinates, window focus/recovery, thread pool execution with serialized physical input. |

## Why the architecture changed

The supporting design calls for independent instance threads, but PyAutoGUI controls one physical
OS mouse and keyboard. Letting multiple threads click concurrently is unsafe. WOTK Mod therefore
allows multiple worker threads while **serializing the actual focus/click operation through a shared
lock**. Each instance stores coordinates relative to the game client area and transforms them to
absolute screen positions immediately before interaction.

## Quick start on Windows

1. Install Python 3.11 or 3.12.
2. Install Tesseract OCR separately if Auto War OCR will be used. The default path detected is
   `C:\Program Files\Tesseract-OCR\tesseract.exe`.
3. Open PowerShell in this repository.
4. Create and activate a virtual environment:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -e .
   ```

5. Run setup verification:

   ```powershell
   python scripts\verify_setup.py
   ```

6. Start the Control Center:

   ```powershell
   python -m wotk
   ```

   or, after editable install:

   ```powershell
   wotk-mod
   ```

## First calibration

All shipped example coordinates are intentionally `0,0`; they are safe templates, **not runnable
calibration**. In the GUI, select a module and use **Configure Coordinates**. For Auto War also use
**OCR Regions**. Profile files are stored outside the repository using the operating system's user
configuration directory so device-specific calibration does not accidentally enter Git.

For Auto War, configure at minimum:

- `bendera_biru`, `search`, `field_search`, `konfirmasi_search`, `nama_kota`, `fight`, `dispatch`,
  `minimize`, `watch`, `march`, `back`, and `exit`;
- `watch_area` and `select_city_area`;
- optionally `defender_area`, `no_hero_area`, `assault_area`, and separate Assault coordinates.

## Auto War route model

The default target-color mapping retained from the specification is:

- `hijau` → `Mianzhu`
- `merah` → `Dongxing`
- `biru` → `WeiXian`

The initial target is derived from `target_color`. `city_route` then controls chained March/Assault
routing. Every account must also have an `account_colors` entry, and an account's alliance color may
not be the same as the selected target color.

`max_cycles: null` means continuous Auto War execution until Stop/FAILSAFE. Use `max_cycles: 1`
while calibrating.

## Multi-instance setup

Multi-instance mode assumes **existing Sandboxie-Plus sandboxes**. It does not silently create or
change Sandboxie security/isolation policy. Configure `master_config.json` plus one instance JSON per
game account. See `config/examples/master_config.example.json` and
`config/examples/instances/instance_1.example.json`.

Coordinates in instance files are relative to the game **client area**, not the desktop. The runtime
focuses the selected window, reads its current client rectangle, applies optional offset correction,
checks bounds, then clicks the transformed coordinate.

## Safety controls

- GUI **STOP** uses cooperative cancellation and interruptible waits.
- PyAutoGUI FAILSAFE remains enabled: move the pointer to a screen corner to raise a failsafe stop.
- Multi-instance mode also attempts to register the configured emergency global hotkey (default
  `Ctrl+Shift+Q`). If the OS blocks the global listener, the GUI Stop and PyAutoGUI FAILSAFE remain.
- A safety maximum (`max_march_hops`) prevents an OCR/route mistake from creating an unbounded March
  chain.

## Credentials and GitHub publishing

Never commit account files. Auto Login profile saving excludes the account editor by design. Keep
real credentials only in memory while running the session. Read `SECURITY.md` before making the
repository public.

The project also intentionally **does not bundle Tesseract executables/DLLs**. Install Tesseract as
an external dependency. This keeps the repository smaller, avoids mixing large third-party binaries
with your code, and makes dependency ownership clearer.

## Repository layout

```text
WOTK_Mod_Complete/
├── src/wotk/
│   ├── automation/        # PyAutoGUI, OCR, window, Sandboxie, stop/hotkey primitives
│   ├── features/          # Login, Individual, Mysteriland, Supremacy, Auto War, Multi-instance
│   └── gui/               # unified thread-safe Tkinter Control Center
├── config/examples/       # sanitized examples only
├── docs/                  # architecture, legacy audit, traceability, configuration, validation
├── scripts/               # run, setup verification, migration, Windows build
├── tests/                 # deterministic unit tests using RecordingBackend
└── .github/workflows/     # CI
```

## Validation status

The repository includes headless/unit checks for parsing, route logic, Supremacy hero rotation,
coordinate transformation, and deterministic button sequences. The execution environment used to
prepare this repository is not the user's Windows game environment, so real UC Browser, Sandboxie,
Tesseract-on-Windows, and in-game coordinates still require local integration testing after
calibration. See `docs/VALIDATION.md`.

## Build a Windows executable

After validating the source version:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

The script installs the project and PyInstaller in a local virtual environment and builds the GUI
entry point. Tesseract remains an external dependency.

## Documentation

- `docs/ANALYSIS_LEGACY.md` — audit of the original Mod-main source and the problems addressed.
- `docs/ARCHITECTURE.md` — design and concurrency model.
- `docs/CONFIGURATION.md` — configuration reference.
- `docs/TRACEABILITY.md` — supporting-document requirement → implementation mapping.
- `docs/MIGRATION.md` — moving calibration from the legacy folders.
- `docs/VALIDATION.md` — what was and was not tested.
- `docs/GITHUB_UPLOAD_CHECKLIST.md` — final checks before publishing.
