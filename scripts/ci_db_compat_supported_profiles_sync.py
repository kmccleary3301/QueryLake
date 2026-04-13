from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "database" / "SUPPORTED_PROFILES.md"
START_MARKER = "<!-- BEGIN_SUPPORTED_PROFILES_MANIFEST -->"
END_MARKER = "<!-- END_SUPPORTED_PROFILES_MANIFEST -->"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import build_supported_profiles_manifest_payload


def extract_manifest(markdown: str) -> dict:
    start = markdown.find(START_MARKER)
    end = markdown.find(END_MARKER)
    if start == -1 or end == -1 or end <= start:
        raise SystemExit("supported profiles manifest markers are missing from docs/database/SUPPORTED_PROFILES.md")
    payload = markdown[start + len(START_MARKER) : end].strip()
    if payload.startswith("```json"):
        payload = payload[len("```json") :].strip()
    if payload.endswith("```"):
        payload = payload[: -3].strip()
    return json.loads(payload)


def main() -> int:
    if not DOC_PATH.exists():
        raise SystemExit(f"missing documentation file: {DOC_PATH}")

    markdown = DOC_PATH.read_text(encoding="utf-8")
    documented = extract_manifest(markdown)
    expected = build_supported_profiles_manifest_payload()

    if documented != expected:
        print("Supported profiles manifest is out of sync with code.")
        print("Expected:")
        print(json.dumps(expected, indent=2, sort_keys=True))
        print("Documented:")
        print(json.dumps(documented, indent=2, sort_keys=True))
        return 1

    print(f"Supported profiles manifest matches code ({len(expected['profiles'])} profiles).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
