# Migration from the legacy Mod-main repository

## Do not copy the whole old folder

The old tree may contain plaintext account credentials, machine-specific paths, large Tesseract
binaries, and stale calibration. Copy only calibration you understand.

## Recommended migration

1. Install and run WOTK Mod 2.0.
2. Open the corresponding module tab.
3. Copy coordinate values from the old JSON into the new editor, or recapture them.
4. Save the new profile through the GUI.
5. For Auto War, recapture OCR regions; the new region format is `{x, y, width, height}`.
6. Re-enter account credentials manually in the Auto Login account editor for the current session.
7. Validate with one stage / one Auto War cycle before enabling long runs.

## Legacy format conversion

`scripts/migrate_legacy.py` can extract coordinate/profile data from common legacy JSON files. It
strips account passwords by default. Use it as a starting point only; some old formats differed per
module and still require manual review.
