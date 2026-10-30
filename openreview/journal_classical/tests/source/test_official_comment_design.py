"""JMLR documents but does not fork Journal's Official Comment action."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SITE_CONFIG = ROOT / "site_config"


def test_official_comment_is_documented_without_a_jmlr_behavior_fork():
    owner = DOCS / "workflow/actions/official-comment.md"
    text = owner.read_text(encoding="utf-8")

    assert "Official Comment" in text
    assert "paper Authors and\n  paper Action Editors" in text
    assert "should not select Reviewers" in text
    assert not (DOCS / "workflow/actions/contact-action-editor.md").exists()
    assert not (SITE_CONFIG / "invitations/venue/official_comment").exists()
