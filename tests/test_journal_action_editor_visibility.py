from types import SimpleNamespace
from pathlib import Path
import datetime

import openreview
import pytest

from openreview.journal import Journal
from openreview.journal.invitation import InvitationBuilder
from openreview.journal.reader_policy import (
    action_editor_reader,
    synchronize_action_editor_readers,
)
from openreview.journal.process import ae_assignment_process


def make_journal(settings=None):
    return Journal(None, "Test", "secret", "editors@example.org", "Test Journal", "TJ",
                   settings=settings or {})


def direct_journal(source):
    constructor = next(line.strip().split("=", 1)[1].strip()
                       for line in source.splitlines()
                       if line.strip().startswith("journal = "))
    return eval(constructor, {"openreview": openreview, "client": SimpleNamespace()})


def rendered_callback(settings):
    owner = SimpleNamespace(
        request_form_id=None, settings=settings, venue_id="Test", secret_key="secret",
        contact_info="editors@example.org", full_name="Test Journal", short_name="TJ",
        website="https://example.org", submission_name="Submission")
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    return builder.get_process_content("process/under_review_submission_process.py")


def test_missing_and_all_preserve_upstream_private_readers():
    expected = ["Test", "Test/Action_Editors", "Test/Paper7/Reviewers",
                "Test/Paper7/Authors"]
    assert make_journal({"submission_public": False}).get_under_review_submission_readers(7) == expected
    assert make_journal({"submission_public": False,
                         "action_editor_paper_visibility": "all"}).get_under_review_submission_readers(7) == expected


def test_assigned_only_scopes_private_but_not_public_readers():
    private = make_journal({"submission_public": False,
                            "release_submission_after_acceptance": False,
                            "action_editor_paper_visibility": "assigned_only"})
    assert private.get_under_review_submission_readers(7)[1] == "Test/Paper7/Action_Editors"
    assert private.get_release_review_readers(7)[1] == "Test/Paper7/Action_Editors"
    assert private.get_release_authors_readers(7)[1] == "Test/Paper7/Action_Editors"
    assert private.get_official_comment_readers(7).count("Test/Paper7/Action_Editors") == 1
    public = make_journal({"submission_public": True,
                           "action_editor_paper_visibility": "assigned_only"})
    assert public.get_under_review_submission_readers(7) == ["everyone"]


def test_invalid_value_is_rejected():
    with pytest.raises(ValueError, match="must be all or assigned_only"):
        make_journal({"action_editor_paper_visibility": "chairs"})


def test_direct_callback_off_path_and_enabled_settings():
    legacy = {"submission_public": False, "release_submission_after_acceptance": False}
    off_source = rendered_callback(legacy)
    assert "settings={}" in off_source
    assert direct_journal(off_source).settings == {}

    enabled = {**legacy, "action_editor_paper_visibility": "assigned_only"}
    source = rendered_callback(enabled)
    reconstructed = direct_journal(source)
    assert reconstructed.settings == enabled
    assert reconstructed.get_under_review_submission_readers(7)[1] == "Test/Paper7/Action_Editors"


class RepairClient:
    def __init__(self):
        self.note_edits = []
        self.invitation_edits = []
        self.history_edits = []
        self.group_edits = []
        self.edge_edits = []
        self.operations = []
        self.groups = [
            SimpleNamespace(id="Test/Paper7/Action_Editors", nonreaders=[]),
            SimpleNamespace(id="Test/Paper7/Action_Editor_abc", nonreaders=None),
        ]

    def get_all_notes(self, **kwargs):
        assert kwargs == {"forum": "paper"}
        return [
            SimpleNamespace(id="paper", readers=["Test", "Test/Action_Editors"],
                content={"pdf": {"value": "/pdf/root",
                                  "readers": ["Test/Action_Editors"]},
                         "assigned_action_editor": {"value": "~Assigned1",
                             "readers": ["Test", "Test/Paper7/Action_Editors",
                                         "Test/Paper7/Reviewers"]}}),
            SimpleNamespace(id="reply", readers=["Test", "Test/Action_Editors",
                                                   "Test/Paper7/Action_Editors"],
                content={"attachment": {"value": "/attachment/reply",
                    "readers": ["Test/Action_Editors", "Test/Paper7/Authors"]}}),
        ]

    def get_note_edits(self, **kwargs):
        assert kwargs["sort"] == "tmdate:asc"
        note_id = kwargs["note_id"]
        return [SimpleNamespace(
            id="edit-" + note_id,
            invitation=("Test/-/Submission" if note_id == "paper" else
                        "Test/Paper7/-/Original_" + note_id),
            signatures=["~Original1"],
            readers=["Test", "Test/Action_Editors"],
            note=SimpleNamespace(id=note_id,
                readers=["Test", "Test/Action_Editors"],
                content={"title": {"value": "Original title"},
                    "file": {"value": "/original/file",
                        "readers": ["Test/Action_Editors"]},
                    "assigned_action_editor": {"value": "~Assigned1",
                        "readers": ["Test", "Test/Paper7/Action_Editors",
                                    "Test/Paper7/Reviewers"]}}),
            cdate=123, tmdate=456)]

    def get_invitations(self, **kwargs):
        assert kwargs == {"replyForum": "paper", "type": "all"}
        return [SimpleNamespace(id="Test/Paper7/Reviewers/Review1/-/Rating")]

    def get_invitation(self, **kwargs):
        if kwargs.get("id") in (
                "Test/Paper7/-/Review",
                "Test/Paper7/-/Review_Release",
                "Test/Paper7/-/Decision_Release",
                "Test/Paper7/Reviewers/Review1/-/Rating"):
            return SimpleNamespace(id=kwargs["id"], edit={"note": {"content": {
                "confidential_file": {"value": {"param": {"type": "file"}},
                    "readers": ["Test/Action_Editors", "Test/Paper7/Authors"]}
            }}})
        raise openreview.OpenReviewException({"name": "NotFoundError", "status": 404})

    def post_note_edit(self, **kwargs):
        self.note_edits.append(kwargs)

    def post_invitation_edit(self, **kwargs):
        self.invitation_edits.append(kwargs)
        self.operations.append("invitation")

    def post_edit(self, edit):
        self.history_edits.append(edit)
        self.operations.append("history")

    def get_all_groups(self, **kwargs):
        assert kwargs == {"prefix": "Test/Paper7/Action_Editors"}
        return self.groups

    def post_group_edit(self, **kwargs):
        self.group_edits.append(kwargs)
        changed = kwargs["group"]
        next(group for group in self.groups if group.id == changed.id).nonreaders = \
            list(changed.nonreaders)

    def get_all_edges(self, **kwargs):
        assert kwargs["head"] == "paper"
        assert kwargs["invitation"] in {
            "Test/Action_Editors/-/Assignment",
            "Test/Action_Editors/-/Archived_Assignment",
        }
        return [SimpleNamespace(id=kwargs["invitation"], nonreaders=[])]

    def post_edge(self, edge):
        self.edge_edits.append(edge)


def test_explicit_synchronization_repairs_only_requested_paper():
    client = RepairClient()
    journal = make_journal({"action_editor_paper_visibility": "assigned_only"})
    synchronize_action_editor_readers(client, journal, SimpleNamespace(
        id="paper", number=7,
        content={"venueid": {"value": journal.assigned_AE_venue_id}}))
    assert client.note_edits[0]["note"].readers == ["Test", "Test/Paper7/Action_Editors"]
    assert client.note_edits[0]["note"].content["pdf"]["readers"] == [
        "Test/Paper7/Action_Editors"]
    assert client.note_edits[0]["note"].content["assigned_action_editor"]["readers"] == [
        "Test/Paper7/Action_Editors", "Test/Paper7/Reviewers"]
    assert client.note_edits[1]["note"].readers == [
        "Test", "Test/Paper7/Action_Editors"]
    assert len(client.history_edits) == 2
    assert {edit.note.id for edit in client.history_edits} == {"paper", "reply"}
    for edit in client.history_edits:
        if edit.note.id == "paper":
            assert edit.invitation == "Test/-/Edit"
            assert edit.signatures == ["Test"]
        else:
            assert edit.invitation == "Test/Paper7/-/Original_reply"
            assert edit.signatures == ["~Original1"]
        assert edit.readers == ["Test", "Test/Paper7/Action_Editors"]
        assert edit.note.content["file"]["readers"] == [
            "Test/Paper7/Action_Editors"]
        assert edit.note.content["file"]["value"] == "/original/file"
        assert edit.note.content["title"]["value"] == "Original title"
        assert edit.note.content["assigned_action_editor"]["readers"] == [
            "Test/Paper7/Action_Editors", "Test/Paper7/Reviewers"]
        assert edit.note.mdate is None and edit.note.cdate is None
        assert edit.note.forum is None
    assert len(client.invitation_edits) == 4
    assert client.operations == ["invitation"] * 4 + ["history"] * 2
    assert client.invitation_edits[0]["invitation"].edit == {"note": {"content": {
        "confidential_file": {"readers": [
            "Test/Paper7/Action_Editors", "Test/Paper7/Authors"]}
    }}}
    assert [edit["group"].id for edit in client.group_edits] == [
        "Test/Paper7/Action_Editors", "Test/Paper7/Action_Editor_abc"]
    assert all(edit["group"].nonreaders == ["Test/Paper7/Authors"]
               for edit in client.group_edits)
    assert {edge.id for edge in client.edge_edits} == {
        "Test/Action_Editors/-/Assignment",
        "Test/Action_Editors/-/Archived_Assignment",
    }
    assert all(edge.nonreaders == ["Test/Paper7/Authors"]
               for edge in client.edge_edits)


@pytest.mark.parametrize("anonymous,status,revealed", [
    (False, "under_review", True),
    (True, "under_review", False),
    (False, "assigned", False),
])
def test_assigned_only_sync_preserves_native_ae_reveal(
        anonymous, status, revealed):
    journal = make_journal({
        "action_editor_paper_visibility": "assigned_only",
        "AE_anonymity": anonymous,
    })
    client = RepairClient()
    authors = "Test/Paper7/Authors"
    for group in client.groups:
        group.nonreaders = [authors, "Test/Unrelated"]
    venue = (journal.under_review_venue_id if status == "under_review"
             else journal.assigned_AE_venue_id)
    submission = SimpleNamespace(
        id="paper", number=7, content={"venueid": {"value": venue}})
    synchronize_action_editor_readers(client, journal, submission)
    assert all((authors not in group.nonreaders) == revealed
               for group in client.groups)
    assert all("Test/Unrelated" in group.nonreaders for group in client.groups)
    group_edit_count = len(client.group_edits)
    synchronize_action_editor_readers(client, journal, submission)
    assert len(client.group_edits) == group_edit_count


def test_default_sync_does_not_change_ae_identity_exclusions():
    journal = make_journal({"AE_anonymity": False})
    client = RepairClient()
    client.groups[0].nonreaders = ["Test/Paper7/Authors", "Test/Unrelated"]
    synchronize_action_editor_readers(client, journal, SimpleNamespace(
        id="paper", number=7,
        content={"venueid": {"value": journal.under_review_venue_id}}))
    assert client.group_edits == []
    assert client.groups[0].nonreaders == ["Test/Paper7/Authors", "Test/Unrelated"]


@pytest.mark.parametrize("assigned_only,anonymous,expected", [
    (True, False, ["Test/Unrelated"]),
    (True, True, None),
    (False, False, ["Test/Paper7/Authors", "Test/Unrelated"]),
])
def test_review_approval_reveals_only_feature_owned_ae_exclusion(
        monkeypatch, assigned_only, anonymous, expected):
    settings = {"AE_anonymity": anonymous}
    if assigned_only:
        settings["action_editor_paper_visibility"] = "assigned_only"
    journal = make_journal(settings)
    journal.notify_readers = lambda *_args, **_kwargs: None
    journal.get_bibtex = lambda *_args, **_kwargs: "bibtex"
    submission = SimpleNamespace(
        id="paper", number=7,
        content={"venueid": {"value": journal.assigned_AE_venue_id}})
    group = SimpleNamespace(
        id="Test/Paper7/Action_Editors",
        nonreaders=["Test/Paper7/Authors", "Test/Unrelated"])

    class Client:
        def __init__(self): self.group_edits = []
        def get_note(self, _note_id): return submission
        def get_group(self, _group_id=None, **_kwargs): return group
        def post_note_edit(self, **_kwargs): return None
        def post_group_edit(self, **kwargs): self.group_edits.append(kwargs["group"])

    client = Client()
    monkeypatch.setattr(openreview.journal, "Journal", lambda: journal)
    source = (Path(__file__).parents[1] /
              "openreview/journal/process/review_approval_process.py").read_text()
    namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(source, "review-approval.py", "exec"), namespace)
    namespace["process"](client, SimpleNamespace(note=SimpleNamespace(
        id="approval", forum="paper", content={
            "under_review": {"value": "Appropriate for Review"}})), None)
    if expected is None:
        assert client.group_edits == []
    else:
        assert client.group_edits[0].nonreaders == expected


def test_action_editor_reader_default_is_venue_wide():
    assert action_editor_reader(make_journal(), 7) == "Test/Action_Editors"


def test_assigned_only_hides_assignment_identity_from_paper_authors():
    journal = make_journal({"action_editor_paper_visibility": "assigned_only"})
    builder = InvitationBuilder(journal)
    saved = []
    builder.save_invitation = lambda invitation: saved.append(invitation)
    builder.set_ae_assignment(0)
    assignment = next(item for item in saved
                      if item.id == "Test/Action_Editors/-/Assignment")
    archived = next(item for item in saved
                    if item.id == "Test/Action_Editors/-/Archived_Assignment")
    assert assignment.edit["nonreaders"] == ["Test/Paper${{2/head}/number}/Authors"]
    assert archived.edit["nonreaders"] == ["Test/Paper${{2/head}/number}/Authors"]

    journal.client = SimpleNamespace(get_group=lambda group_id: SimpleNamespace(
        members=["~Assigned1"] if group_id == "Test/Paper7/Action_Editors" else []))
    submission = SimpleNamespace(number=7, content={})
    assert journal.get_assigned_action_editor(submission) == "~Assigned1"
    successor = "Test/Paper8/Action_Editors"
    journal.client = SimpleNamespace(get_group=lambda _group_id: SimpleNamespace(
        members=[successor, "~Assigned1"]))
    assert journal.get_assigned_action_editor(submission) == "~Assigned1"
    assert journal.client.get_group("Test/Paper7/Action_Editors").members[0] == successor
    for members, count in (([], 0), ([successor], 0),
                           (["~Assigned1", "~Assigned2"], 2),
                           ([successor, "~Assigned1", "~Assigned2"], 2),
                           (["Test/Unknown_Group"], 1)):
        journal.client = SimpleNamespace(get_group=lambda _group_id, members=members:
                                         SimpleNamespace(members=members))
        with pytest.raises(openreview.OpenReviewException,
                           match=f"found {count}"):
            journal.get_assigned_action_editor(submission)
    process = (Path(__file__).parents[1] /
               "openreview/journal/process/ae_assignment_process.py").read_text()
    assert "if assigned_only and 'assigned_action_editor' in note.content:" in process
    assert "content['assigned_action_editor'] = { 'delete': True }" in process
    assert "if not assigned_only and (journal.is_action_editor_anonymous()" in process


def test_assignment_identity_defaults_remain_unchanged():
    journal = make_journal()
    builder = InvitationBuilder(journal)
    saved = []
    builder.save_invitation = lambda invitation: saved.append(invitation)
    builder.set_ae_assignment(0)
    assignment = next(item for item in saved
                      if item.id == "Test/Action_Editors/-/Assignment")
    archived = next(item for item in saved
                    if item.id == "Test/Action_Editors/-/Archived_Assignment")
    assert assignment.edit["nonreaders"] == []
    assert archived.edit["nonreaders"] == []
    submission = SimpleNamespace(number=7, content={
        "assigned_action_editor": {"value": "~Assigned1,assigned@example.org"}})
    assert journal.get_assigned_action_editor(submission) == "~Assigned1"
    with pytest.raises(KeyError):
        journal.get_assigned_action_editor(SimpleNamespace(number=7, content={}))


@pytest.mark.parametrize(
    "assigned_only,initial_members,stored_assignment,expect_state_change",
    [
        (False, ["~Assigned1"], "~Assigned1", True),
        (False, ["~Assigned1"], None, False),
        (False, ["~Assigned1"], "~Other", False),
        (True, ["~Assigned1"], None, True),
        (True, ["~Assigned1", "~Assigned2"], None, False),
    ],
)
def test_unassignment_preserves_default_guard_and_rolls_back_after_last_hidden_ae(
        monkeypatch, assigned_only, initial_members, stored_assignment,
        expect_state_change):
    class AssignmentJournal:
        short_name = "TJ"
        contact_info = "editors@example.org"
        venue_id = "Test"
        settings = {}
        assigned_AE_venue_id = "Test/Assigned_AE"
        assigning_AE_venue_id = "Test/Assigning_AE"

        def get_action_editors_id(self, number=None):
            return "Test/Action_Editors" if number is None else f"Test/Paper{number}/Action_Editors"

        def get_meta_invitation_id(self):
            return "Test/-/Edit"

        def get_message_sender(self):
            return None

    AssignmentJournal.settings = ({"action_editor_paper_visibility": "assigned_only"}
                                  if assigned_only else {})

    note_content = {
        "title": {"value": "Title"},
        "venueid": {"value": "Test/Assigned_AE"},
    }
    if stored_assignment:
        note_content["assigned_action_editor"] = {"value": stored_assignment}
    paper_group = SimpleNamespace(
        id="Test/Paper7/Action_Editors", members=list(initial_members), content={})

    def get_group(group_id):
        if group_id == paper_group.id:
            return paper_group
        return SimpleNamespace(id=group_id, members=[], content={
            "unassignment_email_template_script": {"value": "unassigned"}})

    def remove_member(_group_id, member):
        paper_group.members.remove(member)

    client = SimpleNamespace(
        get_edge=lambda *_args: SimpleNamespace(ddate=1),
        get_note=lambda _id: SimpleNamespace(id="paper", number=7, content=note_content),
        get_group=get_group,
        post_message=lambda *_args, **_kwargs: None,
        remove_members_from_group=remove_member,
        post_note_edit=lambda **kwargs: posted.append(kwargs),
    )
    posted = []
    monkeypatch.setattr(ae_assignment_process, "openreview", openreview, raising=False)
    monkeypatch.setattr(openreview.journal, "Journal", AssignmentJournal)

    ae_assignment_process.process_update(
        client,
        SimpleNamespace(id="edge", head="paper", tail="~Assigned1", ddate=1),
        None,
        None,
    )

    assert len(posted) == int(expect_state_change or stored_assignment == "~Assigned1")
    if posted:
        content = posted[0]["note"].content
        assert ("venueid" in content) is expect_state_change
        assert ("assigned_action_editor" in content) is (stored_assignment == "~Assigned1")


def test_assigned_only_remove_then_reassign_keeps_group_as_identity_source(monkeypatch):
    class AssignmentJournal:
        short_name = "TJ"
        contact_info = "editors@example.org"
        venue_id = "Test"
        settings = {"action_editor_paper_visibility": "assigned_only"}
        assigned_AE_venue_id = "Test/Assigned_AE"
        assigning_AE_venue_id = "Test/Assigning_AE"
        invitation_builder = SimpleNamespace(
            set_note_review_approval_invitation=lambda *_args: None,
            expire_invitation=lambda *_args: None,
        )
        def get_action_editors_id(self, number=None):
            return "Test/Action_Editors" if number is None else f"Test/Paper{number}/Action_Editors"
        def get_editors_in_chief_id(self): return "Test/Editors_In_Chief"
        def get_meta_invitation_id(self): return "Test/-/Edit"
        def get_message_sender(self): return None
        def get_due_date(self, **_kwargs): return datetime.datetime(2026, 1, 1)
        def get_under_review_approval_period_length(self): return 1
        def get_review_approval_id(self, number=None): return f"Test/Paper{number}/-/Review_Approval"
        def get_ae_recommendation_id(self, number=None): return f"Test/Paper{number}/-/Recommendation"
        def get_number_of_reviewers(self): return 3
        def is_action_editor_anonymous(self): return False

    note = SimpleNamespace(id="paper", number=7, content={
        "title": {"value": "Title"}, "venueid": {"value": "Test/Assigned_AE"}})
    paper_group = SimpleNamespace(id="Test/Paper7/Action_Editors",
                                  members=["~Assigned1"], content={})
    global_group = SimpleNamespace(id="Test/Action_Editors", members=["~Assigned1"], content={
        "unassignment_email_template_script": {"value": "unassigned"},
        "assignment_email_template_script": {"value": "assigned"},
        "eic_as_author_email_template_script": {"value": "eic"},
    })
    current_edge = None
    posted = []
    def get_group(group_id):
        if group_id == paper_group.id: return paper_group
        if group_id == global_group.id: return global_group
        return SimpleNamespace(id=group_id, members=[])
    def post_edit(**kwargs):
        posted.append(kwargs["note"].content)
        note.content.update(kwargs["note"].content)
    client = SimpleNamespace(
        get_edge=lambda *_args: current_edge,
        get_note=lambda _id: note, get_group=get_group,
        post_message=lambda *_args, **_kwargs: None,
        remove_members_from_group=lambda _id, member: paper_group.members.remove(member),
        add_members_to_group=lambda _id, member: paper_group.members.append(member),
        post_note_edit=post_edit, get_groups=lambda **_kwargs: [],
    )
    monkeypatch.setattr(ae_assignment_process, "openreview", openreview, raising=False)
    monkeypatch.setattr(openreview.journal, "Journal", AssignmentJournal)

    current_edge = SimpleNamespace(id="remove", head="paper", tail="~Assigned1", ddate=1)
    ae_assignment_process.process_update(client, current_edge, None, None)
    assert paper_group.members == [] and note.content["venueid"]["value"] == "Test/Assigning_AE"
    current_edge = SimpleNamespace(id="add", head="paper", tail="~Assigned1", ddate=None)
    ae_assignment_process.process_update(client, current_edge, None, None)
    assert paper_group.members == ["~Assigned1"]
    assert note.content["venueid"]["value"] == "Test/Assigned_AE"
    assert all("assigned_action_editor" not in content for content in posted)


@pytest.mark.parametrize("assigned_only", [False, True])
def test_release_reviews_resolves_ae_in_both_visibility_modes(monkeypatch,
                                                              assigned_only):
    settings = {"action_editor_paper_visibility": "assigned_only"} if assigned_only else {}
    journal = make_journal(settings)
    submission = SimpleNamespace(id="paper", number=7, content={
        "title": {"value": "Title"},
    })
    if not assigned_only:
        submission.content["assigned_action_editor"] = {"value": "~Assigned1"}
    profile = SimpleNamespace(
        get_preferred_name=lambda pretty=False: "Assigned Editor",
        get_preferred_email=lambda: "assigned@example.org",
    )
    resolved = []
    monkeypatch.setattr(openreview.tools, "get_profiles", lambda _client,
        ids_or_emails, **_kwargs: resolved.extend(ids_or_emails) or [profile])
    templates = {
        "discussion_starts_email_template_script": {"value": "{assigned_action_editor}"},
        "discussion_too_many_reviewers_email_template_script": {"value": "too many"},
    }
    ae_templates = {
        "discussion_starts_email_template_script": {"value": "discussion"},
        "discussion_too_many_reviewers_email_template_script": {"value": "too many"},
    }
    journal.client = SimpleNamespace(
        get_group=lambda group_id=None, id=None, **_kwargs: (
            SimpleNamespace(id=group_id or id, members=["~Assigned1"], content=templates)
            if (group_id or id) == "Test/Paper7/Action_Editors"
            else SimpleNamespace(id=group_id or id, members=[], content=(
                ae_templates if (group_id or id) == "Test/Action_Editors" else templates))),
        post_message=lambda **_kwargs: None,
    )
    journal.invitation_builder = SimpleNamespace(
        set_note_release_review_invitation=lambda *_args: None,
        set_note_release_comment_invitation=lambda *_args: None,
        set_note_official_recommendation_invitation=lambda *_args: None,
        expire_invitation=lambda *_args: None,
    )
    journal.get_number_of_reviewers = lambda: 3
    journal.should_enable_ai_review = lambda: False
    journal.should_skip_official_recommendation = lambda: False
    journal.get_due_date = lambda **_kwargs: datetime.datetime(2026, 1, 1)
    journal.get_discussion_period_length = lambda: 1
    journal.get_recommendation_period_length = lambda: 1
    journal.is_submission_public = lambda: False
    journal.is_action_editor_anonymous = lambda: False
    journal.release_reviews_process(submission)
    assert resolved == ["~Assigned1"]


def test_decision_readers_do_not_dispatch_through_review_reader_override():
    class CustomJournal(Journal):
        def get_release_review_readers(self, number):
            return [f"custom-review-readers-{number}"]

    journal = CustomJournal(None, "Test", "secret", "editors@example.org",
                            "Test Journal", "TJ",
                            settings={"submission_public": False})
    assert journal.get_release_decision_readers(7) == [
        "Test/Editors_In_Chief", "Test/Action_Editors",
        "Test/Paper7/Reviewers", "Test/Paper7/Authors",
    ]
