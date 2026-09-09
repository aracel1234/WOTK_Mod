from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SECRET_KEYS = {"password", "confirm_password", "passwd", "pwd"}


def sanitize(value: Any, include_secrets: bool) -> Any:
    if isinstance(value, dict):
        output = {}
        for key, item in value.items():
            if not include_secrets and key.lower() in SECRET_KEYS:
                output[key] = ""
            else:
                output[key] = sanitize(item, include_secrets)
        return output
    if isinstance(value, list):
        return [sanitize(item, include_secrets) for item in value]
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sanitize/copy a legacy WOTK JSON file into a migration workspace."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--include-secrets",
        action="store_true",
        help="Keep password-like values. Not recommended for Git repositories.",
    )
    args = parser.parse_args()

    data = json.loads(args.source.read_text(encoding="utf-8"))
    cleaned = sanitize(data, args.include_secrets)
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(
        json.dumps(cleaned, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote: {args.destination}")
    if not args.include_secrets:
        print("Password-like fields were stripped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
