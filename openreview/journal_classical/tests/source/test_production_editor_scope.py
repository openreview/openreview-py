from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PE_CONSOLE = REPO_ROOT / "site_config" / "global_settings" / "production_editor_console_webfield_parts" / "core.js"
PE_GROUP = REPO_ROOT / "site_config" / "global_settings" / "groups" / "production_editors.json"
SITE_CONFIG = REPO_ROOT / "site_config"
DOCS = REPO_ROOT / "docs"


def source_text(paths: list[Path]) -> str:
    chunks = []
    for root in paths:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".js", ".json", ".py", ".txt", ".md"}:
                chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_production_editor_replaces_legacy_role_terminology() -> None:
    combined = source_text([SITE_CONFIG, DOCS])
    legacy_fragments = ["Managing Editor", "Managing Editors", "Managing_Editors", "managing_editor"]
    for fragment in legacy_fragments:
        assert fragment not in combined


def test_production_editor_console_is_restricted_to_publication_scope() -> None:
    console_text = PE_CONSOLE.read_text(encoding="utf-8")
    required_console_fragments = [
        "Pending Publication",
        "Published",
        "Camera_Ready_Approved",
        "Camera_Ready_Published",
        "resolveConsolePaperRoleContext(note, 'pe'",
        "applyConsoleModel({ rows: operationalNotes }, 'pe')",
    ]
    for fragment in required_console_fragments:
        assert fragment in console_text

    forbidden_console_fragments = [
        "All Papers",
        "Bulk Invite",
        "Assign Roles",
        "roleContext: 'eic'",
        "Review_Due_Date_Extension",
        "Reviewer_Rating",
        "Decision",
        "js-mark-published",
        "/pdf?id=",
    ]
    for fragment in forbidden_console_fragments:
        assert fragment not in console_text


def test_production_editor_group_source_has_no_hardcoded_members() -> None:
    group = json.loads(PE_GROUP.read_text(encoding="utf-8"))
    assert group.get("id") == "JMLR/Production_Editors"
    assert group.get("signatories") == ["JMLR/Production_Editors"]
    assert not group.get("members")
