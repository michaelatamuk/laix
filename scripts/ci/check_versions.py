"""Check the package version and the public version references agree.

Run from the repository root:

    python scripts/ci/check_versions.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    python_version = re.search(
        r'^version = "([^"]+)"$', read("packages/python/laix/pyproject.toml"), re.M
    )
    typescript_version = json.loads(
        read("packages/typescript/laix/package.json")
    )["version"]
    if python_version is None:
        print("python package version not found")
        return 1
    version = python_version.group(1)
    errors: list[str] = []
    if typescript_version != version:
        errors.append(f"TypeScript version {typescript_version} != Python version {version}")

    a2a_version = json.loads(read("packages/contracts/a2a-agent-card.v1.json"))["version"]
    if a2a_version != version:
        errors.append(f"A2A card version {a2a_version} != package version {version}")

    checks = {
        "README.md": [
            f"Current release: `{version}`",
            f"@v{version}#subdirectory=packages/python/laix",
        ],
        "docs/01-start/02-first-steps/01-quickstart.md": [
            f"@v{version}#subdirectory=packages/python/laix",
            f"laix-{version}.tgz",
        ],
        "docs/05-project/03-release/01-versioning.md": [
            f"| Python package | `{version}` |",
            f"| TypeScript package | `{version}` |",
        ],
        "docs/02-core/01-contract/03-records.md": [
            f"| Package | `{version}` |",
        ],
        "docs/02-core/07-support/02-support.md": [
            f"(`{version}`)",
        ],
        "CHANGELOG.md": [
            f"## {version} -",
        ],
    }
    for path, fragments in checks.items():
        text = read(path)
        for fragment in fragments:
            if fragment not in text:
                errors.append(f"{path}: missing {fragment!r}")

    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"version references agree: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
