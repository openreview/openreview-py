from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "docs/workflow/actions/review.md"
SUMMARIES = (
    ROOT / "docs/roles/reviewers.md",
    ROOT / "docs/roles/action-editors.md",
    ROOT / "docs/workflow/action-inventory.md",
)


def test_review_form_owner_records_the_current_rendered_shape():
    owner = OWNER.read_text(encoding="utf-8")
    fields = (
        "Summary Of Contributions",
        "Strengths And Weaknesses",
        "Requested Changes",
        "Broader Impact Concerns",
        "Claims And Evidence",
        "Audience",
    )
    assert all(field in owner for field in fields)
    assert "no recommendation field" in owner
    assert "no review-file upload" in owner


def test_review_form_summaries_do_not_restore_retired_fields():
    text = "\n".join(path.read_text(encoding="utf-8") for path in (OWNER, *SUMMARIES))
    retired = (
        "review and recommendation together",
        "recommendation and optional review file",
        "Review text, recommendation",
    )
    assert all(item not in text for item in retired)
