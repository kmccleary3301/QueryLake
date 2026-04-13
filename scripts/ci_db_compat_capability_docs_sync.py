from __future__ import annotations

import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "database" / "DB_COMPAT_PROFILES.md"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES


def extract_capability_ids(markdown: str) -> set[str]:
    candidates = re.findall(r"`([a-z0-9_.]+)`", markdown)
    return {candidate for candidate in candidates if "." in candidate}


def expected_capability_ids() -> set[str]:
    capability_ids: set[str] = set()
    for profile in DEPLOYMENT_PROFILES.values():
        for capability in profile.capabilities:
            capability_ids.add(capability.id)
    return capability_ids


def main() -> int:
    if not DOC_PATH.exists():
        raise SystemExit(f"missing documentation file: {DOC_PATH}")

    markdown = DOC_PATH.read_text(encoding="utf-8")
    documented = extract_capability_ids(markdown)
    expected = expected_capability_ids()

    missing = sorted(expected - documented)
    extra = sorted(
        capability
        for capability in documented - expected
        if capability.startswith(("authority.", "projection.", "retrieval.", "acl.", "explain."))
    )

    if missing or extra:
        print("DB compatibility capability docs are out of sync.")
        if missing:
            print(f"Missing from docs: {', '.join(missing)}")
        if extra:
            print(f"Present only in docs: {', '.join(extra)}")
        return 1

    print(f"DB compatibility capability docs match code ({len(expected)} capabilities).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
