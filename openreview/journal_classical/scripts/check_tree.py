#!/usr/bin/env python3
"""Run repository checks for documentation and source shape."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def markdown_files() -> list[Path]:
    return sorted(ROOT.rglob("*.md"))


def check_markdown_links() -> list[str]:
    failures: list[str] = []
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip().split()[0].strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (path.parent / target_path).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                failures.append(f"{path.relative_to(ROOT)} links outside repo: {target}")
                continue
            if not resolved.exists():
                failures.append(f"{path.relative_to(ROOT)} missing link target: {target}")
    return failures


def templated(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return "{{" in text or "}}" in text


def partial_source(path: Path) -> bool:
    return any(part.endswith("_parts") or part == "process_functions" for part in path.parts)


def check_json_files() -> list[str]:
    failures: list[str] = []
    for path in sorted((ROOT / "site_config").rglob("*.json")):
        if templated(path):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - report parse failure concisely
            failures.append(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")
    return failures


def check_python_files() -> list[str]:
    failures: list[str] = []
    candidates = [
        path
        for path in sorted((ROOT / "site_config").rglob("*.py"))
        if not templated(path) and not partial_source(path)
    ]
    for path in candidates:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{path.relative_to(ROOT)} failed Python syntax check: {exc}")
    return failures


def check_javascript_files() -> list[str]:
    failures: list[str] = []
    if shutil.which("node") is None:
        return failures
    candidates = [
        path
        for path in sorted((ROOT / "site_config").rglob("*.js"))
        if not templated(path) and not partial_source(path)
    ]
    for path in candidates:
        result = subprocess.run(["node", "--check", str(path)], cwd=ROOT, text=True, capture_output=True)
        if result.returncode:
            failures.append(f"{path.relative_to(ROOT)} failed JavaScript syntax check: {result.stderr.strip()}")
    return failures


def check_workflow_design_docs_do_not_own_source_mapping() -> list[str]:
    failures: list[str] = []
    allowed = {
        ROOT / "docs" / "workflow" / "checks.md",
        ROOT / "docs" / "workflow" / "contributing.md",
        ROOT / "docs" / "site_config" / "overview.md",
    }
    banned_patterns = [
        "Source orientation",
        "| Source Area",
        "`site_config/",
    ]
    for path in sorted((ROOT / "docs" / "workflow").rglob("*.md")):
        if path in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in banned_patterns:
            if pattern in text:
                failures.append(
                    f"{path.relative_to(ROOT)} contains source mapping pattern {pattern!r}; "
                    "move implementation mapping to private implementation contracts"
                )
    return failures


def main() -> int:
    failures = []
    failures.extend(check_markdown_links())
    failures.extend(check_workflow_design_docs_do_not_own_source_mapping())
    failures.extend(check_json_files())
    failures.extend(check_python_files())
    failures.extend(check_javascript_files())
    source_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_source_assembly.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if source_check.returncode:
        failures.extend(line for line in source_check.stderr.splitlines() if line.strip())
    build_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build" / "site_config.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if build_check.returncode:
        failures.extend(line for line in (build_check.stderr or build_check.stdout).splitlines() if line.strip())
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print("Tree checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
