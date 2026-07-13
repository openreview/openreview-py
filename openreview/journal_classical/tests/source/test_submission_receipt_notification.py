from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SUBMISSION_PROCESS = (
    REPO_ROOT / "site_config/invitations/venue/submission/content_process_functions/process.py"
)


def test_submission_receipt_email_targets_author_ids_with_author_group_fallback():
    process_source = SUBMISSION_PROCESS.read_text(encoding="utf-8")

    assert "recipients=note.content['authorids']['value']" in process_source
    assert "note.content['authorids']['value']" in process_source
    assert "recipients=receipt_recipients" not in process_source
    assert "recipients=[journal.get_authors_id(number=note.number)]" not in process_source
