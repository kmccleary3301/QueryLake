from __future__ import annotations

import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "database" / "DB_COMPAT_PROFILES.md"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES


def extract_profile_ids(markdown: str) -> set[str]:
    return set(re.findall(r"`([a-z0-9_]+_v1)`", markdown))


def main() -> int:
    if not DOC_PATH.exists():
        raise SystemExit(f"missing documentation file: {DOC_PATH}")

    markdown = DOC_PATH.read_text(encoding="utf-8")
    documented = extract_profile_ids(markdown)
    expected = set(DEPLOYMENT_PROFILES.keys())

    missing = sorted(expected - documented)
    extra = sorted(documented - expected)

    if missing or extra:
        print("DB compatibility profile docs are out of sync.")
        if missing:
            print(f"Missing from docs: {', '.join(missing)}")
        if extra:
            print(f"Present only in docs: {', '.join(extra)}")
        return 1

    print(f"DB compatibility profile docs match code ({len(expected)} profiles).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
