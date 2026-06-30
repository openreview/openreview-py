from __future__ import annotations

from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]
WEBFIELD_FILES = [
    "assign_action_editor_webfield.js",
    "action_editor_console_webfield.js",
    "author_console_webfield.js",
    "eic_console_webfield.js",
    "production_editor_console_webfield.js",
    "reviewer_console_webfield.js",
]


def test_build_bundles_ui_helpers_into_console_webfields() -> None:
    subprocess.run(["python3", "scripts/build/site_config.py"], cwd=REPO_ROOT, check=True)

    for env in ("dev", "prod"):
        global_settings_dir = REPO_ROOT / "build" / "local" / env / "global_settings"
        ui_helper_dir = REPO_ROOT / "build" / "local" / env / "ui_helpers"
        assert (ui_helper_dir / "permission_helpers.js").exists()
        assert (ui_helper_dir / "permission_catalog.json").exists()
        for filename in WEBFIELD_FILES:
            text = (global_settings_dir / filename).read_text(encoding="utf-8")
            assert "Bundled from site_config/ui_helpers/permission_helpers.js" in text
            assert "JMLRPermissionHelpers" in text
            assert "resolveRoleContext" in text
            assert "validateSubmissionContext" in text
            assert "renderVenueHomepageStrip" in text
            assert "position: relative" in text
            assert "position: fixed" not in text
            assert "getBootstrapContentInset" in text
            assert "documentElement.clientWidth" in text
            assert "stripContainer.css('margin-top', gap > 0 ? (-gap) + 'px' : '0px')" in text
            assert "eventTarget && eventTarget.addEventListener" in text
            assert "window.addEventListener('resize', syncStripPosition)" not in text
