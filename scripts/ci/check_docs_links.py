"""Check that relative Markdown links resolve to a file or directory."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"\]\(([^)]+)\)")
SKIP = ("http://", "https://", "mailto:", "tel:", "#")
EXCLUDED = {".git", ".pytest_cache", ".ruff_cache", "__pycache__", "node_modules", "dist", "build"}


def markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED for part in relative.parts):
            continue
        if relative.parts[0] == "docs" or path.name == "README.md" or path.parent == ROOT:
            files.append(path)
    return sorted(set(files))


def link_target(raw: str) -> str | None:
    target = raw.strip()
    if target.startswith("<"):
        end = target.find(">")
        target = target[1:end] if end > 0 else target[1:]
    else:
        target = target.split()[0]
    if not target or target.startswith(SKIP):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    return unquote(target) or None


def main() -> int:
    broken: list[str] = []
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for raw in LINK.findall(text):
            target = link_target(raw)
            if target is None:
                continue
            if not (path.parent / target).resolve().exists():
                broken.append(f"{path.relative_to(ROOT).as_posix()}: {raw}")
    if broken:
        print(f"{len(broken)} broken link(s):")
        for item in broken:
            print(f"  {item}")
        return 1
    print("All relative links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
