import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site_config"


def text(path):
    return (SITE / path).read_text(encoding="utf-8")


def test_worklist_has_one_pending_tab_one_url_and_one_completion_action():
    web = text("global_settings/production_editor_console_webfield.js")
    assert "tabs: ['Pending']" in web
    assert "JMLR publication URL" in web
    assert "https://www.jmlr.org/papers/v27/" in web
    assert web.count('data-next="Published"') == 1
    for obsolete in (
        "Needs correction",
        "JMLR PDF URL",
        "js-pdf-url",
        "Correction note",
        "js-correction",
        "JMLR URLs",
    ):
        assert obsolete not in web


def test_successful_mark_published_removes_the_pending_row():
    web = text("global_settings/production_editor_console_webfield.js")
    assert "tr.remove()" in web
    assert "#pe-pending-count" in web
    assert web.index(".then(function ()") < web.index("tr.remove()")
    assert "window.location.reload()" not in web


def test_mark_published_validates_the_visible_url_before_posting():
    web = text("global_settings/production_editor_console_webfield.js")
    required = "The JMLR publication URL is required before marking publication complete."
    invalid = "The JMLR publication URL must use https://www.jmlr.org/papers/v<volume>/<paper>.html."
    post = "Webfield2.api.post('/notes/edits?awaitProcess=true'"
    assert required in web
    assert invalid in web
    assert "^https:\\/\\/(www\\.)?jmlr\\.org\\/papers\\/v[0-9]+\\/[^/?#]+\\.html$" in web
    assert web.index(required) < web.index(post)
    assert web.index(invalid) < web.index(post)


def test_mark_published_preserves_json_failure_messages_and_reenables_retry():
    web = text("global_settings/production_editor_console_webfield.js")
    assert "typeof error === 'string' && error" in web
    assert "error.responseJSON.message" in web
    assert "JSON.parse(error.responseText)" in web
    assert "failureMessage(error, 'Could not save publication status.')" in web
    assert "button.prop('disabled', false)" in web


def test_only_explicit_publication_handoffs_enter_the_worklist():
    web = text("global_settings/production_editor_console_webfield.js")
    assert "byForum[paper.id] && statusFor(byForum[paper.id]) !== 'Published'" in web


def test_publication_status_contract_is_ready_to_published_with_one_v_url():
    reply = json.loads(text("invitations/venue/publication_status/edit/reply.json"))
    content = reply["note"]["content"]
    assert set(content) == {
        "status", "jmlr_publication_url", "pdf", "supplementary_material",
    }
    assert content["pdf"]["readers"] == ["JMLR/Editors_In_Chief", "JMLR/Production_Editors"]
    assert content["supplementary_material"]["readers"] == ["JMLR/Editors_In_Chief", "JMLR/Production_Editors"]
    assert content["status"]["value"]["param"]["enum"] == ["Ready", "Published"]
    assert "/papers/v" in content["jmlr_publication_url"]["value"]["param"]["regex"]

    preprocess = text("python_scripts/invitations/venue/publication_status/preprocess.py")
    assert "{'Ready', 'Published'}" in preprocess
    assert "parsed.path.startswith('/papers/v')" in preprocess
    assert "jmlr_pdf_url" not in preprocess
    assert "Needs correction" not in preprocess


def test_initial_ready_ledger_stores_one_publication_page_url_and_private_file_refs():
    postprocess = text("python_scripts/invitations/venue/accepted/postprocess.py")
    status_block = postprocess[postprocess.index("if not publication_statuses:"):]
    status_block = status_block[:status_block.index("if bundle_exists:")]
    assert "'jmlr_publication_url'" in status_block
    assert "'pdf'" in status_block
    assert "'supplementary_material'" in status_block
    assert "'jmlr_pdf_url'" not in status_block
    assert "'correction_note'" not in status_block


def test_public_design_owns_one_url_one_action_and_pending_row_removal():
    role = (ROOT / "docs/roles/production-editors.md").read_text(encoding="utf-8")
    console = (ROOT / "docs/workflow/consoles/production-editor.md").read_text(encoding="utf-8")
    publication = (ROOT / "docs/workflow/actions/publication.md").read_text(encoding="utf-8")
    combined = "\n".join((role, console, publication))
    assert "one JMLR publication URL" in combined
    assert "removes the paper from the pending worklist" in combined
    assert "`/papers/v<volume>/`" in combined
    for obsolete in ("Needs correction", "publication-page and PDF URLs", "JMLR URLs"):
        assert obsolete not in combined
