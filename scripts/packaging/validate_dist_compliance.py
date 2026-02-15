"""
Validate packaged distribution for licensing/legal compliance safeguards.

Checks:
- Required notice files/folders are present.
- Qt Virtual Keyboard module artifacts are absent.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_RELATIVE_PATH_CANDIDATES = (
    (Path("THIRD_PARTY_LICENSES.txt"), Path("_internal") / "THIRD_PARTY_LICENSES.txt"),
    (Path("licenses") / "qt", Path("_internal") / "licenses" / "qt"),
)

BLOCKED_TOKENS = (
    "Qt6VirtualKeyboard.dll",
    "qtvirtualkeyboardplugin.dll",
    "qml/QtQuick/VirtualKeyboard",
    "qml\\QtQuick\\VirtualKeyboard",
)


def _collect_all_relpaths(dist_root: Path) -> list[str]:
    relpaths: list[str] = []
    for path in dist_root.rglob("*"):
        try:
            relpaths.append(path.relative_to(dist_root).as_posix())
        except Exception:
            continue
    return relpaths


def validate_distribution(dist_root: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    relpaths = _collect_all_relpaths(dist_root)
    joined = "\n".join(relpaths)

    for candidates in REQUIRED_RELATIVE_PATH_CANDIDATES:
        if not any((dist_root / candidate).exists() for candidate in candidates):
            candidate_text = " or ".join(candidate.as_posix() for candidate in candidates)
            errors.append(f"Missing required distribution artifact: {candidate_text}")

    for token in BLOCKED_TOKENS:
        if token.replace("\\", "/") in joined:
            errors.append(f"Blocked Qt module artifact found in dist: {token}")

    return (len(errors) == 0, errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dist-root",
        type=Path,
        default=Path("dist") / "WaterBalanceDashboard",
        help="Path to unpacked dist root folder.",
    )
    args = parser.parse_args()
    dist_root = args.dist_root.resolve()

    if not dist_root.exists():
        print(f"[ERROR] Dist folder not found: {dist_root}")
        return 2

    ok, errors = validate_distribution(dist_root)
    if not ok:
        print("[ERROR] Distribution compliance validation failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print(f"[OK] Distribution compliance checks passed for: {dist_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
