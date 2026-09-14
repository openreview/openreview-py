from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RATING_DOC = ROOT / "docs/workflow/actions/reviewer-rating.md"
INVENTORY_DOC = ROOT / "docs/workflow/action-inventory.md"
AE_DOC = ROOT / "docs/roles/action-editors.md"


def test_reviewer_rating_docs_match_the_single_field_contract():
    rating = RATING_DOC.read_text(encoding="utf-8")
    related = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (RATING_DOC, INVENTORY_DOC, AE_DOC)
    )

    assert "one required field" in rating
    assert "The standard Rating action defines its schema" in rating
    assert "JMLR adds no fork or additional rating fields" in rating
    for value in (
        "Exceeds expectations", "Meets expectations", "Falls below expectations",
    ):
        assert value in rating
    for unsupported in (
        "No rating", "Report problem", "Timeliness", "timeliness",
        "Resubmission reviewer selection", "resubmission selection",
        "rating comments", "| Comment |",
    ):
        assert unsupported not in related
