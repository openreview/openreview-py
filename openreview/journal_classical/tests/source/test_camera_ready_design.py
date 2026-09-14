"""The durable JMLR camera-ready design reflects the approved workflow."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/workflow/actions/camera-ready-revision.md"


def test_camera_ready_design_owns_the_reduced_author_material_contract():
    design = DOC.read_text(encoding="utf-8")
    lowered = design.lower()
    compact = " ".join(design.split())

    assert "Final PDF | Required" in design
    assert "Supplementary material | Optional" in design
    assert "contains only the two material fields above" in design
    assert "no separate code upload, required source archive, video field, or OSS-specific material field" in compact
    assert "submission metadata, not a third camera-ready material field" in compact
    assert "final publication author list" not in lowered
    assert "reorder" not in lowered


def test_camera_ready_design_uses_official_comments_for_minor_revision():
    design = DOC.read_text(encoding="utf-8")

    assert "Accept with minor revision" in design
    assert "revision-summary Official Comment" in design
    assert "The author does not select Reviewers\nor public readers" in design
    assert "the Action Editor does not approve it" in design
    assert "Reviewers do not re-review the paper" in design


def test_messages_link_to_forms_that_own_exact_paper_metadata():
    design = DOC.read_text(encoding="utf-8")
    compact = " ".join(design.split())

    assert "jmlr_or.sty" in design
    assert "\\jmlropenreviewdates{...}" in design
    assert "\\jmlrheading{...}" in design
    assert "\\editor{...}" in design
    assert "same JMLR format\ninstructions and configured Author Guidelines given to the author" in design
    assert "website_urls.camera_ready_author_guidelines" in design
    assert "https://www.jmlr.org/format/authors-guide.html" in design
    assert "Decision and camera-ready messages provide\ngeneral JMLR formatting guidance" in design
    assert "direct the author\nor Action Editor to the paper form for the exact dates" in design
    assert "Camera Ready Revision and Verification\nforms display the paper-specific values" in design
    assert "accepted-decision email, author upload form, Action Editor email" not in compact
    assert (
        "Where the general page differs from those paper-specific OpenReview "
        "instructions, the OpenReview instructions govern this workflow"
        in compact
    )
    assert "does not render an Editor line" in design
    assert "displays these values" in design
    assert "paper-specific JMLR\n  URL" in design
    assert (
        "does not ask the Action Editor to compare or approve a separate author list"
        in " ".join(design.split())
    )
