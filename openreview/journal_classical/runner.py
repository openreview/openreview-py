"""Build helpers for the migrated JMLR classical journal configuration."""

from __future__ import annotations

import importlib.util
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
BUILD_MODULE_PATH = PACKAGE_ROOT / "scripts" / "build" / "site_config_public.py"


def _load_build_module():
    spec = importlib.util.spec_from_file_location(
        "openreview.journal_classical._site_config_public",
        BUILD_MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load build module: {BUILD_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_all() -> None:
    """Render dev and prod site configuration from the migrated source tree."""
    _load_build_module().build_all()


def main() -> int:
    _load_build_module().main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

