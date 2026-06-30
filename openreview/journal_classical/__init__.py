"""Conservative JMLR classical journal configuration migration.

This package intentionally keeps the migrated public configuration source close
to its original repository layout. Use :mod:`openreview.journal_classical.runner`
or the copied ``scripts/build/site_config.py`` entry point to render artifacts.
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
SITE_CONFIG_DIR = PACKAGE_ROOT / "site_config"
BUILD_SCRIPT = PACKAGE_ROOT / "scripts" / "build" / "site_config.py"

