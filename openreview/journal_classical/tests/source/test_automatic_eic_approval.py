from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "site_config/python_scripts/invitations/venue/automatic_eic_approval.py"
APPROVAL = "I approve the AE's decision."


class FakeOpenReviewException(Exception):
    pass


class FakeClient:
    def __init__(self, *, existing=(), persist=True, failure=None):
        self.approvals = list(existing)
        self.persist = persist
        self.failure = failure
        self.posts = []

    def get_notes(self, **_kwargs):
        return list(self.approvals)

    def post_note_edit(self, **kwargs):
        self.posts.append(kwargs)
        if self.failure:
            raise self.failure
        if self.persist:
            self.approvals.append(SimpleNamespace(
                forum=kwargs["note"].forum,
                replyto=kwargs["note"].replyto,
                signatures=kwargs["signatures"],
                invitations=[kwargs["invitation"]],
                content=kwargs["note"].content,
            ))


def load_helper():
    openreview = SimpleNamespace(
        api=SimpleNamespace(Note=lambda **kwargs: SimpleNamespace(**kwargs)),
        OpenReviewException=FakeOpenReviewException,
    )
    namespace = {"openreview": openreview}
    exec(compile(HELPER.read_text(encoding="utf-8"), str(HELPER), "exec"), namespace)
    return namespace["post_standard_eic_approval"]


def invoke(client, **overrides):
    values = {
        "client": client,
        "approval_invitation_id": "JMLR/Paper7/-/Approval",
        "forum_id": "forum-7",
        "replyto_id": "source-note-7",
        "eic_signature": "JMLR/Editors_In_Chief",
        "expected_approval_value": APPROVAL,
        "comment_field": "comment",
        "comment_text": "Automatic approval.",
        "authoritative_existing_values": ("manual decline",),
        "readback_error": "approval readback failed",
    }
    values.update(overrides)
    return load_helper()(**values)


def test_helper_posts_exact_standard_value_signature_comment_and_readback():
    client = FakeClient()

    assert invoke(client) == {"created": True, "approval_value": APPROVAL}

    post = client.posts[0]
    assert post["invitation"] == "JMLR/Paper7/-/Approval"
    assert post["signatures"] == ["JMLR/Editors_In_Chief"]
    assert post["await_process"] is True
    assert post["note"].forum == "forum-7"
    assert post["note"].replyto == "source-note-7"
    assert post["note"].content == {
        "approval": {"value": APPROVAL},
        "comment": {"value": "Automatic approval."},
    }


def test_helper_is_idempotent_for_the_same_reply():
    client = FakeClient(existing=[SimpleNamespace(
        forum="forum-7", replyto="source-note-7",
        signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Approval"],
        content={"approval": {"value": APPROVAL},
                 "comment": {"value": "Automatic approval."}},
    )])

    assert invoke(client) == {"created": False, "approval_value": APPROVAL}
    assert client.posts == []


@pytest.mark.parametrize("existing", [
    SimpleNamespace(
        forum="forum-7", replyto="source-note-7", signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Approval"],
        content={"approval": {"value": "wrong"}, "comment": {"value": "Automatic approval."}},
    ),
    SimpleNamespace(
        forum="forum-7", replyto="source-note-7", signatures=["JMLR/Paper7/Action_Editors"],
        invitations=["JMLR/Paper7/-/Approval"],
        content={"approval": {"value": APPROVAL}, "comment": {"value": "Automatic approval."}},
    ),
])
def test_helper_rejects_nonstandard_existing_reply(existing):
    client = FakeClient(existing=[existing])

    with pytest.raises(FakeOpenReviewException, match="approval readback failed"):
        invoke(client)
    assert client.posts == []


def test_helper_rejects_duplicate_existing_replies():
    exact = SimpleNamespace(
        forum="forum-7", replyto="source-note-7", signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Approval"],
        content={"approval": {"value": APPROVAL}, "comment": {"value": "Automatic approval."}},
    )
    client = FakeClient(existing=[exact, exact])

    with pytest.raises(FakeOpenReviewException, match="approval readback failed"):
        invoke(client)
    assert client.posts == []


def test_helper_preserves_exact_authoritative_manual_decline():
    decline = SimpleNamespace(
        forum="forum-7", replyto="source-note-7",
        signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Approval"],
        content={"approval": {"value": "manual decline"},
                 "comment": {"value": "Human-authored decline explanation."}},
    )
    client = FakeClient(existing=[decline])

    assert invoke(client) == {"created": False, "approval_value": "manual decline"}
    assert client.posts == []


def test_helper_preserves_manual_approve_with_human_comment():
    approve = SimpleNamespace(
        forum="forum-7", replyto="source-note-7",
        signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Approval"],
        content={"approval": {"value": APPROVAL},
                 "comment": {"value": "Human-authored approval explanation."}},
    )
    client = FakeClient(existing=[approve])

    assert invoke(client) == {"created": False, "approval_value": APPROVAL}
    assert client.posts == []


def test_helper_rejects_reply_from_wrong_invitation():
    wrong = SimpleNamespace(
        forum="forum-7", replyto="source-note-7",
        signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Other"],
        content={"approval": {"value": APPROVAL},
                 "comment": {"value": "Automatic approval."}},
    )
    client = FakeClient(existing=[wrong])

    with pytest.raises(FakeOpenReviewException, match="approval readback failed"):
        invoke(client)
    assert client.posts == []


def test_helper_omits_optional_comment_when_not_supplied():
    client = FakeClient()

    invoke(client, comment_field=None, comment_text=None)

    assert client.posts[0]["note"].content == {"approval": {"value": APPROVAL}}


def test_helper_propagates_post_failure_without_synthesizing_readback():
    client = FakeClient(failure=RuntimeError("post failed"))

    with pytest.raises(RuntimeError, match="post failed"):
        invoke(client)
    assert client.approvals == []


def test_helper_fails_when_post_does_not_persist_the_expected_reply():
    client = FakeClient(persist=False)

    with pytest.raises(FakeOpenReviewException, match="approval readback failed"):
        invoke(client)
    assert len(client.posts) == 1
