"""Backward-compatible source entry point for the old Mod-main layout."""

from wotk.app import main


if __name__ == "__main__":
    raise SystemExit(main())
