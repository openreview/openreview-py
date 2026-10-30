import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site_config"
EMAIL_REFERENCE = re.compile(r'"\{\{EMAIL_TEMPLATE_JSON:([^}]+)\}\}"')

OWNERS = {
    "python_scripts/invitations/venue/camera_ready/dateprocess_reminder.py": {
        "author/camera_ready_revision_reminder_subject.txt",
        "author/camera_ready_revision_reminder.txt",
        "ae/camera_ready_verification_reminder_subject.txt",
        "ae/camera_ready_verification_reminder.txt",
    },
    "python_scripts/invitations/venue/accepted/postprocess.py": {
        "production_editor/final_record_ready_subject.txt",
        "production_editor/final_record_ready.txt",
    },
    "invitations/venue/rejected/process_functions/process.py": {
        "author/decision_subject.txt",
        "author/decision_reject_with_resubmission.txt",
        "author/decision_reject_without_resubmission.txt",
    },
    "python_scripts/invitations/venue/production_change_notification/postprocess.py": {
        "production_editor/production_change_subject.txt",
        "production_editor/production_change.txt",
    },
}


def render_embedded_callback(relative: str) -> str:
    source = (SITE / relative).read_text(encoding="utf-8")

    def replace(match):
        return json.dumps(
            (SITE / "email_templates" / match.group(1)).read_text(encoding="utf-8")
        )

    return EMAIL_REFERENCE.sub(replace, source)


def test_every_jmlr_post_message_owner_embeds_external_subject_and_body_content():
    discovered = {
        str(path.relative_to(SITE))
        for path in SITE.rglob("*.py")
        if "client.post_message" in path.read_text(encoding="utf-8")
    }
    assert discovered == set(OWNERS)
    for owner, templates in OWNERS.items():
        source = (SITE / owner).read_text(encoding="utf-8")
        for template in templates:
            assert f"{{{{EMAIL_TEMPLATE_JSON:{template}}}}}" in source
        rendered = render_embedded_callback(owner)
        assert "{{EMAIL_TEMPLATE_JSON:" not in rendered
        compile(rendered, owner, "exec")


def test_notification_callbacks_keep_user_facing_prose_out_of_executable_source():
    forbidden = {
        "camera_ready/dateprocess_reminder.py": (
            "Camera-ready revision reminder for submission",
            "Please upload the final PDF",
            "Camera-ready verification reminder for submission",
            "Please verify the latest upload",
        ),
        "accepted/postprocess.py": ("Final record ready for production",),
        "rejected/process_functions/process.py": ("Decision for submission",),
        "production_change_notification/postprocess.py": (
            "Production follow-up:",
            "This is a notification only",
        ),
    }
    for suffix, fragments in forbidden.items():
        owner = next(path for path in OWNERS if path.endswith(suffix))
        source = (SITE / owner).read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment not in source


def test_extracted_notification_content_preserves_exact_rendered_wording():
    values = {
        "short_name": "JMLR",
        "submission_number": 42,
        "submission_title": "Example Paper",
        "duedate": "Aug 16",
        "paper_url": "https://openreview.test/forum?id=paper",
        "invitation_url": "https://openreview.test/forum?id=paper&invitationId=verify",
        "event": "retraction of an accepted paper",
    }
    expected_subjects = {
        "author/camera_ready_revision_reminder_subject.txt": "[JMLR] Camera-ready revision reminder for submission 42: Example Paper",
        "ae/camera_ready_verification_reminder_subject.txt": "[JMLR] Camera-ready verification reminder for submission 42: Example Paper",
        "production_editor/final_record_ready_subject.txt": "[JMLR] Final record ready for production: 42",
        "author/decision_subject.txt": "[JMLR] Decision for submission 42: Example Paper",
        "production_editor/production_change_subject.txt": "[JMLR] Production follow-up: retraction of an accepted paper for paper 42",
    }
    for relative, expected in expected_subjects.items():
        template = (SITE / "email_templates" / relative).read_text(encoding="utf-8")
        assert template.format(**values).strip() == expected

    revision = (
        SITE / "email_templates/author/camera_ready_revision_reminder.txt"
    ).read_text(encoding="utf-8").format(**values)
    assert revision == (
        "Hi {{fullname}},\n\n"
        "The Camera Ready Revision for your JMLR submission 42: Example Paper was due on Aug 16.\n\n"
        "Please upload the final PDF and any optional supplementary material as soon as possible:\n"
        "https://openreview.test/forum?id=paper\n\n"
        "The JMLR Editors-in-Chief\n"
    )
    verification = (
        SITE / "email_templates/ae/camera_ready_verification_reminder.txt"
    ).read_text(encoding="utf-8").format(**values)
    assert verification == (
        "Hi {{fullname}},\n\n"
        "Verification of the latest camera-ready PDF for JMLR submission 42: Example Paper was due on Aug 16.\n\n"
        "Please verify the latest upload. If correction is needed, post a restricted Official Comment to the paper Authors and wait for a corrected upload before approving:\n"
        "https://openreview.test/forum?id=paper&invitationId=verify\n\n"
        "The JMLR Editors-in-Chief\n"
    )
    production = (
        SITE / "email_templates/production_editor/production_change.txt"
    ).read_text(encoding="utf-8").format(**values).rstrip("\n")
    assert production == (
        "A retraction of an accepted paper was completed for JMLR paper 42.\n\n"
        "Review the public record and reconcile the manual jmlr.org publication if needed:\n"
        "https://openreview.test/forum?id=paper\n\n"
        "This is a notification only; OpenReview creates no production task or completion state."
    )


def test_shared_camera_ready_reminder_preserves_both_recipient_contracts():
    namespace = {}
    exec(
        compile(
            render_embedded_callback(
                "python_scripts/invitations/venue/camera_ready/dateprocess_reminder.py"
            ),
            "camera_ready/dateprocess_reminder.py",
            "exec",
        ),
        namespace,
    )

    class Journal:
        short_name = "JMLR"
        contact_info = "contact@example.test"
        venue_id = "JMLR"

        def __init__(self, late):
            self.late = late

        def get_late_invitees(self, invitation_id):
            self.late_invitation = invitation_id
            return self.late

        def get_meta_invitation_id(self):
            return "JMLR/-/Edit"

        def get_action_editors_id(self, number):
            return f"JMLR/Paper{number}/Action_Editors"

        def get_message_sender(self):
            return "OpenReview.net"

    class Client:
        def __init__(self, journal):
            self.journal = journal
            self.messages = []

        def get_note(self, _forum):
            return type("Submission", (), {
                "id": "paper-id", "number": 42,
                "content": {"title": {"value": "Example Paper"}},
            })()

        def post_message(self, **kwargs):
            self.messages.append(kwargs)

    namespace["openreview"] = type("OpenReview", (), {
        "journal": type("JournalModule", (), {
            "JournalRequest": type("JournalRequest", (), {
                "get_journal": staticmethod(lambda client, _journal_id: client.journal)
            })
        })
    })
    namespace["datetime"] = type("DateTimeModule", (), {
        "datetime": type("DateTime", (), {
            "fromtimestamp": staticmethod(
                lambda _timestamp: type("Date", (), {"strftime": lambda self, _fmt: "Aug 16"})()
            )
        })
    })
    process = namespace["process"]

    for suffix, late, expected_recipients in (
        ("Camera_Ready_Revision", ["authors"], ["authors"]),
        ("Camera_Ready_Verification", ["late-ae"], ["JMLR/Paper42/Action_Editors"]),
    ):
        journal = Journal(late)
        client = Client(journal)
        invitation = type("Invitation", (), {
            "id": f"JMLR/Paper42/-/{suffix}",
            "duedate": 1_700_000_000_000,
            "edit": {"note": {"forum": "paper-id"}},
        })()
        process(client, invitation)

        assert journal.late_invitation == invitation.id
        assert len(client.messages) == 1
        message = client.messages[0]
        assert message["recipients"] == expected_recipients
        assert message["replyTo"] == journal.contact_info
        assert message["signature"] == journal.venue_id
        assert message["sender"] == "OpenReview.net"
        assert "Aug 16" in message["message"]
        assert "Example Paper" in message["subject"]
        if suffix == "Camera_Ready_Revision":
            assert "forum?id=paper-id" in message["message"]
            assert "invitationId=" not in message["message"]
        else:
            assert f"invitationId={invitation.id}" in message["message"]

    for suffix in ("Camera_Ready_Revision", "Camera_Ready_Verification"):
        journal = Journal([])
        client = Client(journal)
        invitation = type("Invitation", (), {
            "id": f"JMLR/Paper42/-/{suffix}", "duedate": 0,
            "edit": {"note": {"forum": "paper-id"}},
        })()
        process(client, invitation)
        assert client.messages == []

    source = (
        SITE / "python_scripts/invitations/venue/camera_ready/dateprocess_reminder.py"
    ).read_text(encoding="utf-8")
    assert "invitation.id.endswith(revision_suffix)" in source
    assert "invitation.id.endswith(verification_suffix)" in source
    assert "invitation.duedate / 1000" in source
    assert ".strftime('%b %d')" in source

    class UnsupportedReminder(Exception):
        pass

    namespace["openreview"].OpenReviewException = UnsupportedReminder
    accesses = []

    class UntouchedClient:
        @property
        def journal(self):
            accesses.append("journal")
            raise AssertionError("journal lookup must not run")

        def get_note(self, *_args, **_kwargs):
            accesses.append("note")
            raise AssertionError("note lookup must not run")

        def post_message(self, **_kwargs):
            accesses.append("message")
            raise AssertionError("message delivery must not run")

    unsupported = type("Invitation", (), {
        "id": "JMLR/Paper42/-/Unrelated_Reminder",
    })()
    with pytest.raises(UnsupportedReminder, match="Unsupported camera-ready"):
        process(UntouchedClient(), unsupported)
    assert accesses == []


def test_standalone_assignment_overview_failure_copy_is_an_external_asset():
    source = (SITE / "global_settings/jmlr_eic_compatibility_landing.js").read_text(
        encoding="utf-8"
    )
    relative = "eic/assignment_overview_load_failure.html"
    assert f"{{{{MESSAGE_TEMPLATE_JSON:{relative}}}}}" in source
    content = (SITE / "message_templates" / relative).read_text(encoding="utf-8")
    assert content == (
        '<div class="container"><p class="alert alert-warning">The assignment overview '
        "could not be loaded. Reload this page or use the direct assignment links.</p></div>\n"
    )
    rendered = source.replace(
        f'"{{{{MESSAGE_TEMPLATE_JSON:{relative}}}}}"', json.dumps(content)
    )
    assert "{{MESSAGE_TEMPLATE_JSON:" not in rendered
    assert json.dumps(content) in rendered
