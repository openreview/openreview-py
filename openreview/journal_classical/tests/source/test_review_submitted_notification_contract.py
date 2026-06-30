from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESS_PATH = REPO_ROOT / "site_config/invitations/venue/review/content_process_functions/process.py"


def assert_order(text: str, first: str, second: str) -> None:
    first_index = text.find(first)
    second_index = text.find(second)
    assert first_index != -1, f"missing fragment: {first}"
    assert second_index != -1, f"missing fragment: {second}"
    assert first_index < second_index, f"expected {first!r} before {second!r}"


def test_review_submission_notifies_ae_before_follow_up_maintenance() -> None:
    text = PROCESS_PATH.read_text(encoding="utf-8")
    required_fragments = [
        "def send_review_submitted_email_to_ae(submission, reviews, reviewer_label):",
        "review_submitted_email_template_script",
        "client.post_message(",
        "recipients=[journal.get_action_editors_id(number=submission.number)]",
        "subject=f'''[{journal.short_name}] Review submitted for {journal.short_name} paper {submission.number}: {submission.content['title']['value']}'''",
        "if review_note.ddate or (review_signatures and all(signature in processed_signatures for signature in review_signatures)):",
        "send_review_submitted_email_to_ae(submission, reviews, reviewer_label)",
        "Could not create reviewer rating action for Paper{submission.number}",
    ]
    for fragment in required_fragments:
        assert fragment in text

    notification_call = "    send_review_submitted_email_to_ae(submission, reviews, reviewer_label)"
    assert_order(
        text,
        "if review_note.ddate or (review_signatures and all(signature in processed_signatures for signature in review_signatures)):",
        notification_call,
    )
    assert_order(text, notification_call, "print('Close submitted review to reviewer edits')")
    assert_order(text, notification_call, "print('Expire review action for submitting reviewer')")
    assert_order(text, notification_call, "print('Create reviewer rating action for submitted review')")
