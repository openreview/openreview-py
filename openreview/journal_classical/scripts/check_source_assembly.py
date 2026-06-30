#!/usr/bin/env python3
"""Check `site_config/` template references and build entrypoints."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_CONFIG = ROOT / "site_config"

PLACEHOLDER_RE = re.compile(r"\{\{([A-Z_]+):([^}:]+)(?::([^}]+))?\}\}")


def text_files() -> list[Path]:
    return sorted(path for path in SITE_CONFIG.rglob("*") if path.is_file())


def check_reference(kind: str, value: str, path: Path) -> str | None:
    if kind == "MESSAGE_TEMPLATE_JSON":
        targets = [SITE_CONFIG / "message_templates" / value]
    elif kind == "EMAIL_TEMPLATE_JSON":
        targets = [SITE_CONFIG / "email_templates" / value]
    elif kind == "PYTHON_SCRIPT_JSON":
        targets = [SITE_CONFIG / "python_scripts" / value, SITE_CONFIG / value]
    elif kind == "PYTHON_SCRIPT_FILE":
        targets = [SITE_CONFIG / "python_scripts" / value, SITE_CONFIG / value]
    elif kind == "PYTHON_SCRIPT_CHUNK_FILE":
        targets = [SITE_CONFIG / "python_scripts" / value, SITE_CONFIG / value]
    elif kind in {"GLOBAL_SETTING_JS_JSON", "GLOBAL_SETTING_JS_FILE"}:
        targets = [SITE_CONFIG / "global_settings" / value]
    else:
        return None
    if not any(target.exists() for target in targets):
        return f"{path.relative_to(ROOT)} references missing {kind} target: {value}"
    return None


def check_template_references() -> list[str]:
    failures: list[str] = []
    for path in text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in PLACEHOLDER_RE.finditer(text):
            failure = check_reference(match.group(1), match.group(2), path)
            if failure:
                failures.append(failure)
    return failures


def check_required_source_roots() -> list[str]:
    failures: list[str] = []
    for relative in [
        "openreview.json",
        "global_settings",
        "invitations",
        "python_scripts",
        "message_templates",
        "email_templates",
        "ui_helpers",
    ]:
        if not (SITE_CONFIG / relative).exists():
            failures.append(f"missing required source area: site_config/{relative}")
    return failures


def check_build_entrypoints() -> list[str]:
    failures: list[str] = []
    for relative in [
        "scripts/build/site_config.py",
        "scripts/build/site_config_public.py",
    ]:
        if not (ROOT / relative).exists():
            failures.append(f"missing source build entrypoint: {relative}")
    return failures


def main() -> int:
    failures = []
    failures.extend(check_required_source_roots())
    failures.extend(check_build_entrypoints())
    failures.extend(check_template_references())
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print("Source assembly checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
