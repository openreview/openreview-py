from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build" / "site_config.py"
PUBLIC_BUILD_IMPL = REPO_ROOT / "scripts" / "build" / "site_config_public.py"
TEMPLATE_ROOT = REPO_ROOT / "site_config" / "message_templates"


def test_message_template_build_support_and_removed_review_due_date_template() -> None:
    assert BUILD_SCRIPT.exists()
    build_text = PUBLIC_BUILD_IMPL.read_text(encoding="utf-8")

    assert "MESSAGE_TEMPLATE_JSON" in build_text
    assert "safe_message_template_path" in build_text
    assert '".."' in build_text
    assert "message_templates" in build_text
    assert not (TEMPLATE_ROOT / "editorial_comments" / "review_due_date_extended.txt").exists()
    assert not (
        REPO_ROOT
        / "site_config"
        / "python_scripts"
        / "invitations"
        / "venue"
        / "review_due_date_extension"
        / "process.py"
    ).exists()


def test_message_templates_do_not_reintroduce_obsolete_phrases() -> None:
    obsolete_phrases = [
        "separate reviewer recommendation due date",
        "Assignment Acknowledgement",
        "JMLR Submission Details",
    ]

    for path in sorted(TEMPLATE_ROOT.rglob("*.txt")):
        text = path.read_text(encoding="utf-8").lower()
        for phrase in obsolete_phrases:
            assert phrase.lower() not in text, f"{phrase!r} appears in {path.relative_to(REPO_ROOT)}"

    assert not any(path.name == "review_due_date_extended.txt" for path in TEMPLATE_ROOT.rglob("*.txt"))
