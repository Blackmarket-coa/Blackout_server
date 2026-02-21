#!/usr/bin/env python3
"""Static regression check for runtime NotImplementedError raises in synapse/.

This check is intentionally import-free: it parses Python source via `ast` to avoid
runtime environment coupling while still guarding against introducing raw
`raise NotImplementedError` paths in production modules.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNAPSE_DIR = ROOT / "synapse"


def iter_notimplemented_raises(path: Path) -> list[tuple[int, str]]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    hits: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue

        exc = node.exc
        target = exc.func if isinstance(exc, ast.Call) else exc

        name: str | None = None
        if isinstance(target, ast.Name):
            name = target.id
        elif isinstance(target, ast.Attribute):
            name = target.attr

        if name == "NotImplementedError":
            snippet = ast.get_source_segment(source, node) or "raise NotImplementedError"
            hits.append((node.lineno, snippet.strip()))

    return hits


def main() -> int:
    violations: list[str] = []
    for py_file in sorted(SYNAPSE_DIR.rglob("*.py")):
        hits = iter_notimplemented_raises(py_file)
        for lineno, snippet in hits:
            violations.append(f"{py_file.relative_to(ROOT)}:{lineno}: {snippet}")

    if violations:
        print("Found runtime NotImplementedError raise sites:")
        print("\n".join(violations))
        return 1

    print("OK: no runtime `raise NotImplementedError` sites found under synapse/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
