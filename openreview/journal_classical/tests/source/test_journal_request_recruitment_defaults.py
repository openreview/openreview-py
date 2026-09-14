from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "site_config" / "email_templates" / "journal_request"


def template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def test_action_editor_recruitment_default_is_jmlr_specific_without_load_promises():
    body = template("action_editor_recruitment.txt")

    for required in (
        "Dear {{fullname}}",
        "invited by the JMLR Editors-in-Chief",
        "Journal of Machine Learning Research",
        "https://www.jmlr.org/",
        "handle assigned submissions",
        "select reviewers",
        "guide review progress",
        "submit editorial decisions",
        "OpenReview",
        "{{accept_url}}",
        "{{decline_url}}",
        "{{SITE_URL}}/login",
        "{{SITE_URL}}/signup",
        "The JMLR Editors-in-Chief",
    ):
        assert required in body

    lowered = body.lower()
    for forbidden in (
        "program chair",
        "conference",
        "annual quota",
        "cooldown",
        "active papers",
        "max papers",
        "maximum papers",
    ):
        assert forbidden not in lowered


def test_reviewer_recruitment_default_has_no_program_chair_language():
    body = template("reviewer_recruitment.txt")

    assert "Dear {{fullname}}" in body
    assert "the JMLR Editors-in-Chief" in body
    assert "Journal of Machine Learning Research" in body
    assert "{{accept_url}}" in body
    assert "{{decline_url}}" in body
    assert "The JMLR Editors-in-Chief" in body
    lowered = body.lower()
    assert "program chair" not in lowered
    assert "conference" not in lowered
