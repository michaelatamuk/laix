"""Check that relative Markdown links and anchors resolve."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"\]\(([^)]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
SKIP = ("http://", "https://", "mailto:", "tel:")
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


def slugify(text: str) -> str:
    text = re.sub(r"`", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s", "-", text)


def anchors(path: Path) -> set[str]:
    if path.suffix.lower() != ".md":
        return set()
    found: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(line)
        if not match:
            continue
        base = slugify(match.group(2))
        if not base:
            continue
        count = seen.get(base, 0)
        anchor = base if count == 0 else f"{base}-{count}"
        seen[base] = count + 1
        found.add(anchor)
    return found


def link_parts(raw: str) -> tuple[str, str] | None:
    target = raw.strip()
    if target.startswith("<"):
        end = target.find(">")
        target = target[1:end] if end > 0 else target[1:]
    else:
        target = target.split()[0]
    if not target or target.startswith(SKIP):
        return None
    path, _, anchor = target.partition("#")
    path = path.split("?", 1)[0]
    return unquote(path), unquote(anchor)


def main() -> int:
    broken: list[str] = []
    cache: dict[Path, set[str]] = {}
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for raw in LINK.findall(text):
            parts = link_parts(raw)
            if parts is None:
                continue
            target, anchor = parts
            if not target:
                if anchor and anchor not in anchors(path):
                    broken.append(f"{path.relative_to(ROOT).as_posix()}: {raw}")
                continue
            target_path = (path.parent / target).resolve()
            if not target_path.exists():
                broken.append(f"{path.relative_to(ROOT).as_posix()}: {raw}")
                continue
            if not anchor:
                continue
            if target_path.is_dir():
                target_path = target_path / "README.md"
            if target_path.suffix.lower() != ".md" or not target_path.exists():
                continue
            if target_path not in cache:
                cache[target_path] = anchors(target_path)
            if anchor not in cache[target_path]:
                broken.append(f"{path.relative_to(ROOT).as_posix()}: {raw}")
    if broken:
        print(f"{len(broken)} broken link(s):")
        for item in broken:
            print(f"  {item}")
        return 1
    print("All relative links and anchors resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
