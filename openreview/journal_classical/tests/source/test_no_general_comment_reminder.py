from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
EDITORIAL_COMMENT_PATH = REPO_ROOT / "site_config" / "invitations" / "venue" / "editorial_comment" / "edit" / "reply.json"
AUTHOR_CONSOLE_PATH = REPO_ROOT / "site_config" / "global_settings" / "author_console_webfield.js"


def find_keys(value: Any, key_name: str, path: str = "$") -> list[str]:
    matches: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key == key_name:
                matches.append(child_path)
            matches.extend(find_keys(child, key_name, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            matches.extend(find_keys(child, key_name, f"{path}[{index}]"))
    return matches


def test_editorial_comment_has_no_reminder_wiring() -> None:
    editorial_comment = json.loads(EDITORIAL_COMMENT_PATH.read_text(encoding="utf-8"))
    editorial_comment_text = EDITORIAL_COMMENT_PATH.read_text(encoding="utf-8")

    assert find_keys(editorial_comment, "dateprocesses") == []
    assert "post_message" not in editorial_comment_text
    assert re.search(r"remind\w*|Reminder", editorial_comment_text, re.IGNORECASE) is None


def test_author_console_pending_tasks_exclude_editorial_comments() -> None:
    author_console_text = AUTHOR_CONSOLE_PATH.read_text(encoding="utf-8")
    filter_start = author_console_text.find("invitations.filter(function(invitation)")
    filter_end = author_console_text.find("});", filter_start)
    assert filter_start >= 0
    assert filter_end >= 0
    pending_filter = author_console_text[filter_start:filter_end]

    assert "CAMERA_READY_REVISION_NAME" in pending_filter
    assert "authoredPaperNumbers.has(match[1])" in pending_filter
    assert "Editorial_Comment" not in pending_filter
    assert "Editorial_Comment" not in author_console_text
