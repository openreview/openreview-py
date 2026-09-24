"""Safety and callback contracts for native resubmission continuity."""

import datetime
import json
import re
from types import SimpleNamespace

import openreview
import pytest

from openreview.journal.invitation import InvitationBuilder
from openreview.journal.assignment import (
    iter_resubmission_score_assignments, resubmission_score_assignments,
)
from openreview.journal.resubmission import (
    ensure_resubmission_ae_access, prepare_resubmission_continuity,
    parse_forum_id, resolve_resubmission_predecessor,
    validate_resubmission_submission_edit,
)


URL = "https://openreview.net/forum?id=prior"


class JournalView:
    venue_id = "Neutral/Venue"
    rejected_venue_id = "Neutral/Venue/Rejected"
    short_name = "NV"
    settings = {
        "resubmission_continuity_enabled": True,
        "resubmission_continuity": "immediate_previous_ae",
    }
    assignment = SimpleNamespace(compute_conflicts=lambda *_args: [])

    def get_author_submission_id(self): return self.venue_id + "/-/Article"
    def get_ae_decision_id(self, number=None): return f"{self.venue_id}/Paper{number}/-/Decision"
    def get_ae_assignment_id(self, archived=False):
        return self.venue_id + "/Action_Editors/-/" + ("Archived_Assignment" if archived else "Assignment")
    def get_reviewer_assignment_id(self, archived=False):
        return self.venue_id + "/Reviewers/-/" + ("Archived_Assignment" if archived else "Assignment")
    def get_action_editors_id(self, number=None):
        return self.venue_id + (f"/Paper{number}" if number else "") + "/Action_Editors"
    def get_authors_id(self, number=None): return self.venue_id + f"/Paper{number}/Authors"
    def get_editors_in_chief_id(self): return self.venue_id + "/Editors_In_Chief"
    def get_revision_id(self, number=None): return self.venue_id + f"/Paper{number}/-/Revision"
    def get_eic_revision_id(self, number=None): return self.venue_id + f"/Paper{number}/-/EIC_Revision"
    def get_camera_ready_revision_id(self, number=None):
        return self.venue_id + f"/Paper{number}/-/Camera_Ready_Revision"
    def is_active_submission(self, _submission): return True


def note(note_id, number, authors, previous=None):
    content = {"authorids": {"value": authors}}
    if previous: content["previous_NV_submission_url"] = {"value": previous}
    return SimpleNamespace(
        id=note_id, forum=note_id, domain="Neutral/Venue", number=number,
        invitations=["Neutral/Venue/-/Article"], ddate=None, content=content)


class Client:
    def __init__(self, current, previous, *, permitted=True):
        self.current, self.previous = current, previous
        self.groups = {
            "Neutral/Venue/Action_Editors": SimpleNamespace(members=["~AE1", "~AE2"]),
            "Neutral/Venue/Paper1/Action_Editors": SimpleNamespace(members=[]),
        }
        self.added, self.posted = [], []
        self.decision = SimpleNamespace(
            id="decision", tcdate=5, ddate=None,
            content={"recommendation": {"value": "Reject"},
                "resubmission_of_major_revision": {"value":
                "The authors may consider submitting a major revision at a later time."
                if permitted else "Reject"}})
        self.prior = [SimpleNamespace(
            id="old", tail="~AE1", ddate=None, tcdate=10)]

    def get_profile(self, value):
        profile_id = {
            "~Author1": "~Author1", "~Author_One1": "~Author1",
            "author@example.org": "~Author1", "~Author2": "~Author2",
            "~Other": "~Other", "other@example.org": "~Other",
            "~Editor1": "~Editor1", "editor@example.org": "~Editor1",
        }.get(value)
        if not profile_id:
            raise openreview.OpenReviewException(["Profile Not Found"])
        return SimpleNamespace(id=profile_id)

    def get_note(self, note_id):
        found = {self.current.id: self.current, self.previous.id: self.previous}
        if note_id not in found:
            raise openreview.OpenReviewException({"name": "NotFoundError", "status": 404})
        return found[note_id]

    def get_notes(self, invitation=None): return [self.decision]

    def get_all_edges(self, invitation=None, head=None, **_kwargs):
        if head == self.previous.id and invitation.endswith("Assignment"):
            return self.prior
        return []

    def get_edges(self, invitation=None, head=None, tail=None, **_kwargs):
        if head == self.current.id: return list(self.posted)
        return self.get_all_edges(invitation=invitation, head=head)

    def get_group(self, group_id):
        return self.groups.setdefault(group_id, SimpleNamespace(members=[]))

    def add_members_to_group(self, group_id, members):
        self.added.append((group_id, list(members)))
        self.get_group(group_id).members.extend(
            member for member in members if member not in self.get_group(group_id).members)

    def get_groups(self, id=None, member=None, **_kwargs):
        if id == "Neutral/Venue/Editors_In_Chief" and member == "~Editor1":
            return [SimpleNamespace(id=id)]
        return []

    def post_edge(self, edge):
        edge.id = "new-assignment"
        self.posted.append(edge)
        return edge


def fixture(*, current_authors=("~Author1",), previous_authors=("~Author1",), permitted=True):
    current = note("current", 2, list(current_authors), URL)
    previous = note("prior", 1, list(previous_authors))
    previous.content["venueid"] = {"value": "Neutral/Venue/Rejected"}
    return JournalView(), Client(current, previous, permitted=permitted), current, previous


def test_validated_predecessor_and_access_use_author_and_decision_policy():
    journal, client, current, previous = fixture()
    assert resolve_resubmission_predecessor(client, journal, current) is previous
    assert ensure_resubmission_ae_access(client, journal, current) is previous
    assert client.added == [("Neutral/Venue/Paper1/Action_Editors",
                             ["Neutral/Venue/Paper2/Action_Editors"])]


def test_supported_author_email_alias_is_resolved_for_admission(monkeypatch):
    journal, client, current, _previous = fixture()
    proposed = note(None, current.number, ["~Author1"], URL)
    monkeypatch.setattr(openreview.tools, "get_profile", lambda _client, value:
                        SimpleNamespace(id="~Author1" if value in
                        ("~Author1", "author@example.org") else "~Other"))
    assert validate_resubmission_submission_edit(
        client, journal,
        SimpleNamespace(note=proposed, tauthor="author@example.org"),
    ).id == "prior"
    with pytest.raises(openreview.OpenReviewException,
                       match="invalid or inaccessible"):
        validate_resubmission_submission_edit(
            client, journal,
            SimpleNamespace(note=proposed, tauthor="other@example.org"))
    monkeypatch.setattr(openreview.tools, "get_profile",
                        lambda _client, _value: None)
    with pytest.raises(openreview.OpenReviewException,
                       match="invalid or inaccessible"):
        validate_resubmission_submission_edit(
            client, journal,
            SimpleNamespace(note=proposed, tauthor="missing@example.org"))


@pytest.mark.parametrize("current_authors,previous_authors,actor", [
    (("~Author1",), ("~Author1",), "~Author1"),
    (("author@example.org",), ("~Author1",), "author@example.org"),
    (("~Author_One1",), ("~Author1",), "~Author_One1"),
])
def test_equivalent_author_identities_are_admitted(
        current_authors, previous_authors, actor):
    journal, client, current, _previous = fixture(
        current_authors=current_authors, previous_authors=previous_authors)
    proposed = note(None, current.number, list(current_authors), URL)
    assert validate_resubmission_submission_edit(
        client, journal, SimpleNamespace(note=proposed, tauthor=actor)).id == "prior"


@pytest.mark.parametrize("actor,invitation_getter", [
    ("author@example.org", "get_revision_id"),
    ("~Author_One1", "get_revision_id"),
    ("author@example.org", "get_camera_ready_revision_id"),
    ("~Author_One1", "get_camera_ready_revision_id"),
])
def test_equivalent_author_identities_can_revise_existing_link(
        actor, invitation_getter):
    journal, client, current, previous = fixture()
    proposed = SimpleNamespace(id=current.id, content={"title": {"value": "New"}})
    invitation_id = getattr(journal, invitation_getter)(number=current.number)
    assert validate_resubmission_submission_edit(
        client, journal, SimpleNamespace(note=proposed, tauthor=actor),
        SimpleNamespace(id=invitation_id)) is previous


@pytest.mark.parametrize("actor,invitation_getter", [
    ("missing@example.org", "get_revision_id"),
    ("other@example.org", "get_camera_ready_revision_id"),
    ("editor@example.org", "get_camera_ready_revision_id"),
])
def test_unrelated_or_unresolved_identity_cannot_revise_existing_link(
        actor, invitation_getter):
    journal, client, current, _previous = fixture()
    proposed = SimpleNamespace(id=current.id, content={"title": {"value": "New"}})
    with pytest.raises(openreview.OpenReviewException,
                       match="authorized Editor-in-Chief"):
        validate_resubmission_submission_edit(
            client, journal, SimpleNamespace(note=proposed, tauthor=actor),
            SimpleNamespace(id=getattr(journal, invitation_getter)(number=2)))


def test_eic_email_alias_retains_revision_only_exemption():
    journal, client, current, previous = fixture()
    proposed = SimpleNamespace(id=current.id, content={"title": {"value": "New"}})
    assert validate_resubmission_submission_edit(
        client, journal, SimpleNamespace(note=proposed, tauthor="editor@example.org"),
        SimpleNamespace(id=journal.get_revision_id(number=2))) is previous
    with pytest.raises(openreview.OpenReviewException,
                       match="authorized Editor-in-Chief"):
        validate_resubmission_submission_edit(
            client, journal,
            SimpleNamespace(note=proposed, tauthor="editor@example.org"),
            SimpleNamespace(id=journal.get_camera_ready_revision_id(number=2)))


@pytest.mark.parametrize("value,expected", [
    ("https://openreview.net/forum?id=prior&referrer=%5BHomepage%5D", "prior"),
    ("https://dev.openreview.net/forum?referrer=mail&id=prior", "prior"),
    ("https://foreign.example/forum?id=prior", None),
    ("https://openreview.net/group?id=prior", None),
    ("https://openreview.net/forum;extra?id=prior", None),
    ("https://openreview.net/forum?id=", None),
    ("https://openreview.net/forum?id=prior&id=other", None),
    ("https://openreview.net/forum?id=prior&id=", None),
    ("https://openreview.net:bad/forum?id=prior", None),
])
def test_forum_url_parser_accepts_one_id_and_rejects_ambiguous_targets(
        value, expected):
    assert parse_forum_id(value) == expected


def test_admission_accepts_and_preserves_copied_url_text():
    copied_url = URL + "&referrer=%5BHomepage%5D"
    journal, client, current, previous = fixture()
    proposed = note(None, current.number, ["~Author1"], copied_url)
    assert validate_resubmission_submission_edit(
        client, journal, SimpleNamespace(note=proposed, tauthor="~Author1")) \
        is previous
    assert proposed.content["previous_NV_submission_url"]["value"] == copied_url


@pytest.mark.parametrize("builder_name", [
    None,
    "set_revision_invitation",
    "set_camera_ready_revision_invitation",
    "set_eic_revision_invitation",
])
def test_generated_url_schemas_admit_copied_links_for_native_preprocess(
        monkeypatch, builder_name):
    journal = openreview.journal.Journal(
        SimpleNamespace(), "Neutral/Venue", "secret", "contact@example.org",
        "Neutral Venue", "NV", settings=JournalView.settings)
    field = journal.get_resubmission_previous_submission_field()
    if builder_name is None:
        schema = journal.get_submission_additional_fields()[field]
    else:
        monkeypatch.setattr(openreview.tools, "get_invitation", lambda *_args: None)
        captured = {}
        journal.invitation_builder.save_super_invitation = \
            lambda _id, _content, _edit, invitation: captured.update(invitation)
        getattr(journal.invitation_builder, builder_name)()
        schema = captured["edit"]["note"]["content"][field]
    pattern = schema["value"]["param"]["regex"]
    canonical = "https://openreview.net/forum?id=prior"
    copied = canonical + "&referrer=%5BHomepage%5D"
    assert re.fullmatch(pattern, canonical)
    assert re.fullmatch(pattern, copied)
    assert re.fullmatch(pattern, "https://dev.openreview.net/forum?id=prior")
    assert not re.fullmatch(pattern, "https://foreign.example/forum?id=prior")
    assert not re.fullmatch(pattern, "https://openreview.net/group?id=prior")

    runtime_journal, client, current, previous = fixture()
    proposed = note(None, current.number, ["~Author1"], copied)
    assert validate_resubmission_submission_edit(
        client, runtime_journal,
        SimpleNamespace(note=proposed, tauthor="~Author1")) is previous
    for invalid in (
            "https://openreview.net/forum?id=prior&id=other",
            "https://openreview.net/forum;extra?id=prior"):
        proposed.content["previous_NV_submission_url"]["value"] = invalid
        with pytest.raises(openreview.OpenReviewException, match="invalid"):
            validate_resubmission_submission_edit(
                client, runtime_journal,
                SimpleNamespace(note=proposed, tauthor="~Author1"))


@pytest.mark.parametrize("enabled", [False, True])
def test_null_submission_additional_fields_is_treated_as_empty(enabled):
    journal = openreview.journal.Journal(
        SimpleNamespace(), "Neutral/Venue", "secret", "contact@example.org",
        "Neutral Venue", "NV", settings={
            "submission_additional_fields": None,
            "resubmission_continuity_enabled": enabled})
    fields = journal.get_submission_additional_fields()
    assert (journal.get_resubmission_previous_submission_field() in fields) is enabled
    assert journal.settings["submission_additional_fields"] is None


@pytest.mark.parametrize("settings", [{}, {"resubmission_continuity_enabled": False}])
@pytest.mark.parametrize("builder_name", ["set_submission_invitation", "set_revision_invitation",
    "set_camera_ready_revision_invitation", "set_eic_revision_invitation"])
def test_disabled_url_schema_matches_upstream_on_all_surfaces(
        monkeypatch, settings, builder_name):
    journal = openreview.journal.Journal(
        SimpleNamespace(), "Neutral/Venue", "secret", "contact@example.org",
        "Neutral Venue", "NV", settings=settings)
    field = journal.get_resubmission_previous_submission_field()
    if builder_name == "set_submission_invitation":
        assert field not in journal.get_submission_additional_fields()
        monkeypatch.setattr(openreview.tools, "get_invitation", lambda *_args: None)
        captured = []
        journal.invitation_builder.save_invitation = captured.append
        journal.invitation_builder.set_submission_invitation()
        schema = captured[0].edit["note"]["content"][field]
    else:
        monkeypatch.setattr(openreview.tools, "get_invitation", lambda *_args: None)
        captured = {}
        journal.invitation_builder.save_super_invitation = \
            lambda _id, _content, _edit, invitation: captured.update(invitation)
        getattr(journal.invitation_builder, builder_name)()
        schema = captured["edit"]["note"]["content"][field]
    upstream = r'https:\/\/openreview\.net\/forum\?id=.*'
    assert schema["value"]["param"]["regex"] == upstream
    for url in ("https://openreview.net/forum?id=prior",
                "https://openreview.net/forum?id=prior&referrer=x",
                "https://openreview.net/forum?id=prior#fragment",
                "https://openreview.net/forum?id=prior with space",
                "https://dev.openreview.net/forum?id=prior"):
        assert bool(re.fullmatch(schema["value"]["param"]["regex"], url)) == \
            bool(re.fullmatch(upstream, url))


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("builder_name", ["set_submission_invitation",
    "set_revision_invitation", "set_camera_ready_revision_invitation",
    "set_eic_revision_invitation"])
def test_explicit_predecessor_field_override_is_preserved(
        monkeypatch, enabled, builder_name):
    field = "previous_NV_submission_url"
    custom = {"value": {"param": {"type": "string", "regex": "custom"}}}
    journal = openreview.journal.Journal(
        SimpleNamespace(), "Neutral/Venue", "secret", "contact@example.org",
        "Neutral Venue", "NV", settings={
            "resubmission_continuity_enabled": enabled,
            "submission_additional_fields": {field: custom}})
    monkeypatch.setattr(openreview.tools, "get_invitation", lambda *_args: None)
    if builder_name == "set_submission_invitation":
        captured = []
        journal.invitation_builder.save_invitation = captured.append
        journal.invitation_builder.set_submission_invitation()
        schema = captured[0].edit["note"]["content"][field]
    else:
        captured = {}
        journal.invitation_builder.save_super_invitation = \
            lambda _id, _content, _edit, invitation: captured.update(invitation)
        getattr(journal.invitation_builder, builder_name)()
        schema = captured["edit"]["note"]["content"][field]
    assert schema == custom


@pytest.mark.parametrize("invitation_getter,actor", [
    ("get_revision_id", "~Author1"),
    ("get_camera_ready_revision_id", "~Author1"),
    ("get_eic_revision_id", "~Editor1"),
])
def test_existing_revision_preserves_copied_url_text(
        invitation_getter, actor):
    copied_url = URL + "&referrer=%5BHomepage%5D"
    journal, client, current, previous = fixture()
    current.content["previous_NV_submission_url"]["value"] = copied_url
    proposed = SimpleNamespace(id=current.id, content={
        "title": {"value": "New"},
        "previous_NV_submission_url": {"value": copied_url},
    })
    invitation_id = getattr(journal, invitation_getter)(number=current.number)
    assert validate_resubmission_submission_edit(
        client, journal, SimpleNamespace(note=proposed, tauthor=actor),
        SimpleNamespace(id=invitation_id)) is previous
    assert proposed.content["previous_NV_submission_url"]["value"] == copied_url

    proposed.content["previous_NV_submission_url"]["value"] = URL
    with pytest.raises(openreview.OpenReviewException, match="immutable"):
        validate_resubmission_submission_edit(
            client, journal, SimpleNamespace(note=proposed, tauthor=actor),
            SimpleNamespace(id=invitation_id))


@pytest.mark.parametrize("authors,permitted,message", [
    (("~Other",), True, "current author"),
    (("~Author1",), False, "does not permit"),
])
def test_untrusted_relationship_is_rejected_at_admission(authors, permitted, message):
    journal, client, current, _previous = fixture(
        previous_authors=authors, permitted=permitted)
    proposed = note(None, current.number, ["~Author1"], URL)
    with pytest.raises(openreview.OpenReviewException,
                       match="previous submission reference is invalid or inaccessible"):
        validate_resubmission_submission_edit(
            client, journal, SimpleNamespace(note=proposed, tauthor="~Author1"))
    assert client.added == [] and client.posted == []


def test_foreign_or_changed_link_never_grants_access():
    journal, client, current, previous = fixture()
    previous.domain = "Other"
    assert resolve_resubmission_predecessor(client, journal, current) is None
    assert ensure_resubmission_ae_access(client, journal, current) is None
    current.content["previous_NV_submission_url"]["value"] = \
        "https://openreview.net/forum?id=missing"
    assert ensure_resubmission_ae_access(client, journal, current) is None
    assert client.added == []


def test_submission_preflight_rejects_changed_or_untrusted_link_before_write():
    journal, client, current, _previous = fixture()
    changed = note(current.id, current.number, ["~Author1"],
                   "https://openreview.net/forum?id=missing")
    with pytest.raises(openreview.OpenReviewException, match="immutable"):
        validate_resubmission_submission_edit(
            client, journal, SimpleNamespace(note=changed, tauthor="~Author1"))
    create = note(None, 2, ["~Other"], URL)
    with pytest.raises(openreview.OpenReviewException,
                       match="invalid or inaccessible"):
        validate_resubmission_submission_edit(
            client, journal, SimpleNamespace(note=create, tauthor="~Other"))
    assert client.added == [] and client.posted == []


def test_admitted_relationship_survives_mutable_predecessor_drift():
    journal, client, current, previous = fixture()
    previous.content["authorids"]["value"] = ["~FormerAuthor"]
    client.decision.content["resubmission_of_major_revision"]["value"] = "Reject"

    assert resolve_resubmission_predecessor(client, journal, current) is previous
    assert ensure_resubmission_ae_access(client, journal, current) is previous
    assigned = prepare_resubmission_continuity(client, journal, current)
    assert assigned.tail == "~AE1"

    revision = SimpleNamespace(
        id=current.id, content={"title": {"value": "Revised title"}})
    assert validate_resubmission_submission_edit(
        client, journal,
        SimpleNamespace(note=revision, tauthor="~Author1", signatures=["~Author1"]),
        SimpleNamespace(id=journal.get_revision_id(number=current.number)),
    ) is previous


def test_admission_collapses_invalid_and_inaccessible_predecessor_errors():
    journal, client, _current, _previous = fixture()
    invalid = [
        "not-a-forum-url",
        "https://openreview.net/forum?id=missing",
    ]
    for previous_url in invalid:
        proposed = note(None, 2, ["~Author1"], previous_url)
        with pytest.raises(openreview.OpenReviewException,
                           match="previous submission reference is invalid or inaccessible"):
            validate_resubmission_submission_edit(
                client, journal, SimpleNamespace(note=proposed, tauthor="~Author1"))

    proposed = note(None, 2, ["~Other"], URL)
    with pytest.raises(openreview.OpenReviewException,
                       match="previous submission reference is invalid or inaccessible"):
        validate_resubmission_submission_edit(
            client, journal, SimpleNamespace(note=proposed, tauthor="~Other"))


def test_admission_rejects_self_link_but_later_missing_predecessor_is_absent():
    journal, client, current, _previous = fixture()
    current.content["previous_NV_submission_url"]["value"] = \
        "https://openreview.net/forum?id=current"
    proposed = note("current", 2, ["~Author1"],
                    "https://openreview.net/forum?id=current")
    with pytest.raises(openreview.OpenReviewException,
                       match="previous submission reference is invalid or inaccessible"):
        validate_resubmission_submission_edit(
            client, journal, SimpleNamespace(note=proposed, tauthor="~Author1"))

    current.content["previous_NV_submission_url"]["value"] = \
        "https://openreview.net/forum?id=missing"
    assert resolve_resubmission_predecessor(client, journal, current) is None
    assert prepare_resubmission_continuity(client, journal, current) is None


def test_existing_two_cycle_is_rejected_for_author_and_eic_revisions():
    journal, client, current, previous = fixture()
    previous.content["previous_NV_submission_url"] = {
        "value": "https://openreview.net/forum?id=current"}
    proposed = SimpleNamespace(id=current.id, content={"title": {"value": "New"}})
    for invitation_id, actor in (
            (journal.get_revision_id(number=2), "~Author1"),
            (journal.get_eic_revision_id(number=2), "~Editor1")):
        with pytest.raises(openreview.OpenReviewException, match="invalid"):
            validate_resubmission_submission_edit(
                client, journal,
                SimpleNamespace(note=proposed, tauthor=actor, signatures=[actor]),
                SimpleNamespace(id=invitation_id))


def test_immediate_mode_uses_newest_prior_ae_without_availability_gate():
    journal, client, current, _previous = fixture()
    client.prior.append(SimpleNamespace(id="new", tail="~AE2", ddate=None, tcdate=20))
    assigned = prepare_resubmission_continuity(client, journal, current)
    assert assigned.tail == "~AE2"
    assert assigned.label == "Resubmission continuity"


def test_immediate_mode_does_not_post_without_an_eligible_prior_ae():
    journal, client, current, _previous = fixture()
    client.prior = []
    assert prepare_resubmission_continuity(client, journal, current) is None
    assert client.posted == []

    client.prior = [SimpleNamespace(id="old", tail="~AE1", ddate=None, tcdate=10)]
    journal.assignment = SimpleNamespace(
        compute_conflicts=lambda _submission, profile_id: ["conflict"]
        if profile_id == "~AE1" else [])
    assert prepare_resubmission_continuity(client, journal, current) is None
    assert client.posted == []


@pytest.mark.parametrize("settings,status,label,expected", [
    ({"resubmission_continuity_enabled": True,
      "resubmission_continuity": "immediate_previous_ae"},
     "Submitted", "Resubmission continuity", "Assigned_AE"),
    ({"resubmission_continuity_enabled": True,
      "resubmission_continuity": "immediate_previous_ae"},
     "Submitted", "Manual assignment", "Submitted"),
    ({"resubmission_continuity_enabled": True,
      "resubmission_continuity": "score"},
     "Submitted", "Resubmission continuity", "Submitted"),
    ({"resubmission_continuity_enabled": False},
     "Submitted", "Manual assignment", "Submitted"),
    ({"resubmission_continuity_enabled": False},
     "Assigning_AE", "Manual assignment", "Assigned_AE"),
])
def test_assignment_callback_only_advances_successful_immediate_continuity(
        monkeypatch, settings, status, label, expected):
    journal, client, current, _previous = fixture()
    journal.settings = settings
    journal.submitted_venue_id = journal.venue_id + "/Submitted"
    journal.assigning_AE_venue_id = journal.venue_id + "/Assigning_AE"
    journal.assigned_AE_venue_id = journal.venue_id + "/Assigned_AE"
    journal.contact_info = "contact@example.org"
    journal.is_action_editor_anonymous = lambda: False
    journal.get_due_date = lambda **_kwargs: 1
    journal.get_under_review_approval_period_length = lambda: 1
    journal.get_review_approval_id = lambda number=None: \
        f"{journal.venue_id}/Paper{number}/-/Review_Approval"
    journal.get_ae_recommendation_id = lambda number=None: \
        f"{journal.venue_id}/Paper{number}/-/AE_Recommendation"
    journal.get_meta_invitation_id = lambda: journal.venue_id + "/-/Edit"
    journal.get_message_sender = lambda: None
    journal.get_number_of_reviewers = lambda: 3
    journal.get_reviewers_id = lambda number=None: \
        journal.venue_id + (f"/Paper{number}" if number else "") + "/Reviewers"
    journal.invitation_builder = SimpleNamespace(
        set_note_review_approval_invitation=lambda *_args: None,
        expire_invitation=lambda *_args: None)
    current.content.update(
        title={"value": "Current"},
        venueid={"value": journal.venue_id + "/" + status})

    for group_id, group in client.groups.items():
        group.id = group_id
    client.groups[journal.get_action_editors_id()].content = {
        "assignment_email_template_script": {"value": "assigned"},
        "unassignment_email_template_script": {"value": "unassigned"},
        "eic_as_author_email_template_script": {"value": "eic"},
    }
    original_get_group = client.get_group
    def get_group(group_id):
        group = original_get_group(group_id)
        group.id = group_id
        return group
    client.get_group = get_group
    original_add = client.add_members_to_group
    client.add_members_to_group = lambda group_id, members: original_add(
        group_id, members if isinstance(members, list) else [members])
    edge = SimpleNamespace(
        id="edge", head=current.id, tail="~AE1", ddate=None, label=label)
    client.get_edge = lambda *_args: edge
    client.post_message = lambda *_args, **_kwargs: None
    def post_note_edit(note=None, **_kwargs):
        for key, value in note.content.items():
            if value == {"delete": True}:
                current.content.pop(key, None)
            else:
                current.content[key] = value
    client.post_note_edit = post_note_edit

    owner = SimpleNamespace(request_form_id="Neutral/Request", settings=settings)
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    monkeypatch.setattr(openreview.journal.JournalRequest, "get_journal",
                        staticmethod(lambda *_args: journal))
    source = builder.get_process_content("process/ae_assignment_process.py")
    namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(source, "ae-assignment-process.py", "exec"), namespace)
    namespace["process_update"](client, edge, None, None)
    assert current.content["venueid"]["value"] == journal.venue_id + "/" + expected


def test_resubmission_preprocess_is_an_ordinary_native_process():
    owner = SimpleNamespace(request_form_id="Neutral/Request",
        settings=JournalView.settings)
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    source = builder.resubmission_submission_preprocess()
    namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(source, "resubmission-runtime.py", "exec"), namespace)
    assert callable(namespace["process"])
    assert "from openreview.journal.resubmission import" in source


def test_assembled_submission_process_uses_validated_stored_authors(monkeypatch):
    journal, client, current, _previous = fixture()
    current.content["title"] = {"value": "Linked paper"}
    current.tcdate, current.tmdate = 1, 2
    journal.setup_author_submission = lambda _note: None
    journal.should_eic_submission_notification = lambda: False
    journal.should_enable_ai_review = lambda: False
    journal.contact_info = "contact@example.org"
    journal.get_message_sender = lambda: None
    client.groups[journal.get_authors_id()] = SimpleNamespace(
        members=["~Author1"], content={})
    owner = SimpleNamespace(
        request_form_id="Neutral/Request", settings=journal.settings)
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    monkeypatch.setattr(
        openreview.journal.JournalRequest, "get_journal",
        staticmethod(lambda *_args: journal))
    source = builder.get_process_content("process/author_submission_process.py")
    namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(source, "assembled-author-submission.py", "exec"), namespace)
    namespace["process"](
        client,
        SimpleNamespace(note=SimpleNamespace(id=current.id),
                        tauthor="author@example.org"),
        None,
    )
    assert [edge.tail for edge in client.posted] == ["~AE1"]


def test_author_submission_invitation_runs_preflight_before_write(monkeypatch):
    journal, client, _current, _previous = fixture()
    owner = SimpleNamespace(
        request_form_id="Neutral/Request", settings=journal.settings)
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    source = builder.track_submission_preprocess(None)
    monkeypatch.setattr(
        openreview.journal.JournalRequest, "get_journal",
        staticmethod(lambda _client, _request: journal))
    namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(source, "author-submission-preflight.py", "exec"), namespace)
    proposed = note(None, 2, ["~Author1"], URL)
    namespace["process"](
        client, SimpleNamespace(note=proposed, tauthor="~Author1"), None)
    proposed.content["previous_NV_submission_url"]["value"] = \
        "https://openreview.net/forum?id=missing"
    with pytest.raises(openreview.OpenReviewException, match="invalid"):
        namespace["process"](
            client, SimpleNamespace(note=proposed, tauthor="~Author1"), None)

    revision = builder.resubmission_submission_preprocess()
    namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(revision, "revision-preflight.py", "exec"), namespace)
    changed = note("current", 2, ["~Author1"],
                   "https://openreview.net/forum?id=missing")
    edit = SimpleNamespace(note=changed, tauthor="~Author1")
    with pytest.raises(openreview.OpenReviewException, match="immutable"):
        namespace["process"](client, edit, None)


@pytest.mark.parametrize("callback_name,actor,invitation_id", [
    ("ordinary-author", "~Author1", "Neutral/Venue/Paper2/-/Revision"),
    ("ordinary-new-coauthor", "~Author2", "Neutral/Venue/Paper2/-/Revision"),
    ("ordinary-eic", "~Editor1", "Neutral/Venue/Paper2/-/Revision"),
    ("camera-ready-author", "~Author1",
     "Neutral/Venue/Paper2/-/Camera_Ready_Revision"),
    ("camera-ready-new-coauthor", "~Author2",
     "Neutral/Venue/Paper2/-/Camera_Ready_Revision"),
])
def test_authorized_roles_can_run_generated_revision_preprocess(
        monkeypatch, callback_name, actor, invitation_id):
    journal, client, current, _previous = fixture(
        current_authors=("~Author1", "~Author2"))
    owner = SimpleNamespace(
        request_form_id="Neutral/Request", settings=journal.settings)
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    monkeypatch.setattr(openreview.journal.JournalRequest, "get_journal",
        staticmethod(lambda *_args: journal))
    source = builder.resubmission_submission_preprocess()
    namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(source, callback_name + ".py", "exec"), namespace)
    proposed = SimpleNamespace(id=current.id, content={
        "title": {"value": "Revised title"}, "pdf": {"value": "/pdf/new"}})
    edit = SimpleNamespace(note=proposed, tauthor=actor,
                           signatures=["Neutral/Venue/Editors_In_Chief"])
    namespace["process"](client, edit, SimpleNamespace(id=invitation_id))


@pytest.mark.parametrize("actor,invitation_id", [
    ("~Other", "Neutral/Venue/Paper2/-/Revision"),
    ("~Editor1", "Neutral/Venue/Paper2/-/Camera_Ready_Revision"),
])
def test_generated_revision_rejects_unauthorized_role_even_with_eic_signature(
        monkeypatch, actor, invitation_id):
    journal, client, current, _previous = fixture(
        current_authors=("~Author1", "~Author2"))
    owner = SimpleNamespace(request_form_id="Neutral/Request", settings=journal.settings)
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    monkeypatch.setattr(openreview.journal.JournalRequest, "get_journal",
        staticmethod(lambda *_args: journal))
    source = builder.resubmission_submission_preprocess()
    namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(source, "unauthorized-revision.py", "exec"), namespace)
    edit = SimpleNamespace(note=SimpleNamespace(id=current.id, content={
        "title": {"value": "Revised title"}}), tauthor=actor,
        signatures=["Neutral/Venue/Editors_In_Chief"])
    with pytest.raises(openreview.OpenReviewException, match="authorized Editor-in-Chief"):
        namespace["process"](client, edit, SimpleNamespace(id=invitation_id))


def test_score_mode_uses_the_fixed_predecessor_field():
    journal, client, current, _previous = fixture()
    journal.settings = dict(journal.settings,
        resubmission_continuity="score")
    assert [edge.tail for edge in resubmission_score_assignments(
        client, journal, current)] == ["~AE1"]

    journal.settings["resubmission_previous_submission_field"] = "prior_round"
    current.content = {"authorids": {"value": ["~Author1"]},
                       "prior_round": {"value": URL}}
    assert resubmission_score_assignments(client, journal, current) == []


def test_fixed_permission_accepts_native_and_jmlr_decision_values():
    captured = {}
    journal = SimpleNamespace(
        venue_id="Neutral/Venue", short_name="NV",
        get_editors_in_chief_id=lambda: "Neutral/Venue/Editors_In_Chief",
        get_ae_decision_id=lambda number=None: "Neutral/Venue/-/Decision",
        get_action_editors_id=lambda number=None, anon=False: "Neutral/Venue/Action_Editors",
        get_authors_id=lambda number=None: "Neutral/Venue/Authors",
        get_website_url=lambda *_args: "https://example.org",
        get_certifications=lambda: [], get_decision_additional_fields=lambda: {},
    )
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = journal
    builder.get_process_content = lambda _path: ""
    builder.preprocess_script = builder.process_script = builder.ae_reminder_process = ""
    builder.save_super_invitation = lambda _id, _content, _edit, invitation: captured.update(invitation)
    builder.set_decision_invitation()
    native_value = captured["edit"]["note"]["content"]["resubmission_of_major_revision"]["value"]["param"]["enum"][0]

    runtime_journal, client, current, previous = fixture()
    assert client.decision.content["resubmission_of_major_revision"]["value"] == native_value
    assert resolve_resubmission_predecessor(client, runtime_journal, current) is previous

    client.decision.content = {"resubmission_of_major_revision": {
        "value": ["Reject with encouragement to resubmit"]}}
    assert resolve_resubmission_predecessor(client, runtime_journal, current) is previous
    client.decision.content["resubmission_of_major_revision"]["value"] = []
    proposed = note(None, current.number, ["~Author1"], URL)
    with pytest.raises(openreview.OpenReviewException,
                       match="invalid or inaccessible"):
        validate_resubmission_submission_edit(
            client, runtime_journal,
            SimpleNamespace(note=proposed, tauthor="~Author1"))


@pytest.mark.parametrize("venue,recommendation", [
    ("Neutral/Venue/Accepted", "Reject"),
    ("Neutral/Venue/Rejected", "Accept as is"),
])
def test_admission_requires_rejected_state_and_recommendation(venue, recommendation):
    journal, client, current, previous = fixture()
    previous.content["venueid"]["value"] = venue
    client.decision.content["recommendation"]["value"] = recommendation
    proposed = note(None, current.number, ["~Author1"], URL)
    with pytest.raises(openreview.OpenReviewException,
                       match="invalid or inaccessible"):
        validate_resubmission_submission_edit(
            client, journal, SimpleNamespace(note=proposed, tauthor="~Author1"))


@pytest.mark.parametrize("status", [403, 503])
def test_predecessor_operational_failures_are_visible(status):
    journal, client, current, _previous = fixture()
    journal.settings = dict(journal.settings, resubmission_continuity="score")
    client.get_note = lambda _note_id: (_ for _ in ()).throw(
        openreview.OpenReviewException({"name": "ServiceError", "status": status}))
    with pytest.raises(openreview.OpenReviewException) as error:
        resolve_resubmission_predecessor(client, journal, current)
    assert error.value.args[0]["status"] == status
    with pytest.raises(openreview.OpenReviewException):
        resubmission_score_assignments(client, journal, current)


def test_missing_predecessor_is_absent_but_service_recovery_retries_once():
    journal, client, current, previous = fixture()
    missing = note("current", 2, ["~Author1"],
                   "https://openreview.net/forum?id=missing")
    assert resolve_resubmission_predecessor(client, journal, missing) is None

    original = client.get_note
    attempts = {"count": 0}
    def recovering(note_id):
        if note_id == previous.id and attempts["count"] == 0:
            attempts["count"] += 1
            raise openreview.OpenReviewException({"name": "ServiceUnavailable", "status": 503})
        return original(note_id)
    client.get_note = recovering
    with pytest.raises(openreview.OpenReviewException):
        prepare_resubmission_continuity(client, journal, current)
    assert client.posted == [] and client.added == []
    assigned = prepare_resubmission_continuity(client, journal, current)
    assert assigned.tail == "~AE1"
    assert len(client.posted) == 1
    assert prepare_resubmission_continuity(client, journal, current) is None
    assert len(client.posted) == 1


def test_custom_preprocesses_are_explicitly_unsupported_and_owned_setup_is_stable():
    journal, _client, _current, _previous = fixture()
    owner = SimpleNamespace(
        request_form_id="Neutral/Request", settings=dict(journal.settings))
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    existing = "def process(client, edit, invitation):\n    pass\n"
    for compose in (builder.track_submission_preprocess,):
        with pytest.raises(ValueError, match="ownership"):
            compose(existing)
        owned = compose(None)
        assert compose(owned) == owned
        owner.settings = {"resubmission_continuity_enabled": False}
        assert compose(owned) == {"delete": True}
        owner.settings = dict(journal.settings)

def test_disabled_continuity_preserves_unrelated_submission_preprocess():
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = SimpleNamespace(
        request_form_id=None, settings={})
    existing = "def process(client, edit, invitation):\n    edit.legacy = True\n"
    assert builder.track_submission_preprocess(existing) == existing
    assert builder.track_submission_preprocess(None) is None


@pytest.mark.parametrize("builder_name,invitation_getter", [
    ("set_revision_invitation", "get_revision_id"),
    ("set_camera_ready_revision_invitation", "get_camera_ready_revision_id"),
    ("set_eic_revision_invitation", "get_eic_revision_id"),
])
def test_disabled_revision_builders_preserve_preprocess_contract(
        monkeypatch, builder_name, invitation_getter):
    journal = openreview.journal.Journal(
        SimpleNamespace(), "Neutral/Venue", "secret", "contact@example.org",
        "Neutral Venue", "NV", settings={"resubmission_continuity_enabled": False})
    builder = journal.invitation_builder
    custom_script = "def process(client, edit, invitation):\n    edit.field_ran = True\n"
    custom_dispatcher = (
        "def process(client, edit, invitation):\n"
        "    edit.dispatcher_ran = True\n"
        "    raise RuntimeError('custom dispatcher')\n")
    field = {"value": custom_script, "readers": ["Neutral/Venue"],
             "description": "retain me", "order": 7}
    existing = SimpleNamespace(
        content={"preprocess_script": field},
        edit={"invitation": {"preprocess": custom_dispatcher}})
    target_id = getattr(journal, invitation_getter)()
    monkeypatch.setattr(openreview.tools, "get_invitation",
                        lambda _client, invitation_id: existing
                        if invitation_id == target_id else None)
    captured = {}
    builder.save_super_invitation = lambda _id, content, _edit, invitation: \
        captured.update(content=content, invitation=invitation)
    getattr(builder, builder_name)()
    assert captured["content"]["preprocess_script"] == field
    assert captured["invitation"]["preprocess"] == custom_dispatcher
    edit = SimpleNamespace(dispatcher_ran=False)
    namespace = {}
    exec(compile(captured["invitation"]["preprocess"], "custom-dispatcher.py", "exec"),
         namespace)
    with pytest.raises(RuntimeError, match="custom dispatcher"):
        namespace["process"](None, edit, None)
    assert edit.dispatcher_ran is True


def test_emitted_eic_revision_rejects_changed_predecessor(monkeypatch):
    runtime_journal, client, current, _previous = fixture()
    journal = openreview.journal.Journal(
        SimpleNamespace(), "Neutral/Venue", "secret", "contact@example.org",
        "Neutral Venue", "NV", settings=runtime_journal.settings)
    builder = journal.invitation_builder
    monkeypatch.setattr(openreview.tools, "get_invitation", lambda *_args: None)
    monkeypatch.setattr(openreview.journal.JournalRequest, "get_journal",
        staticmethod(lambda *_args: runtime_journal))
    captured = {}
    builder.save_super_invitation = lambda _id, content, _edit, invitation: \
        captured.update(content=content, invitation=invitation)
    builder.set_eic_revision_invitation()
    assert "journal-resubmission-preprocess-owner-v2" in \
        captured["content"]["preprocess_script"]["value"]
    namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(captured["content"]["preprocess_script"]["value"],
                 "eic-revision.py", "exec"), namespace)
    changed = note(current.id, current.number, ["~Author1"],
                   "https://openreview.net/forum?id=missing")
    with pytest.raises(openreview.OpenReviewException, match="immutable"):
        namespace["process"](client,
            SimpleNamespace(note=changed, tauthor="~Editor1"),
            SimpleNamespace(id=runtime_journal.get_eic_revision_id(number=2)))


def test_revision_preprocess_rejects_custom_field_and_dispatcher():
    owner = SimpleNamespace(
        request_form_id="Neutral/Request",
        settings={"resubmission_continuity_enabled": True})
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    builder.preprocess_script = "native-dispatcher"
    continuity = "# journal-resubmission-preprocess-owner-v2\n"
    builder.resubmission_submission_preprocess = lambda: (
        continuity if owner.settings.get("resubmission_continuity_enabled") is True
        else None)
    original_field = {"value": "def process(client, edit, invitation):\n    pass\n",
                      "readers": ["Neutral/Venue"], "description": "custom"}
    original_dispatcher = \
        "def process(client, edit, invitation):\n    edit.events.append('custom')\n"
    existing = SimpleNamespace(content={"preprocess_script": original_field},
        edit={"invitation": {"preprocess": original_dispatcher}})
    with pytest.raises(ValueError, match="ownership of the revision preprocess field"):
        builder.revision_preprocess_fields(existing)

    existing.content["preprocess_script"] = {"value": continuity}
    with pytest.raises(ValueError, match="does not compose custom revision dispatchers"):
        builder.revision_preprocess_fields(existing)


def test_revision_preprocess_disable_explicitly_removes_owned_field_and_dispatcher():
    owner = SimpleNamespace(
        request_form_id="Neutral/Request",
        settings={"resubmission_continuity_enabled": True})
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    builder.preprocess_script = "native-dispatcher"
    builder.resubmission_submission_preprocess = lambda: (
        "# journal-resubmission-preprocess-owner-v2\n"
        "def process(client, edit, invitation):\n    pass\n"
        if owner.settings.get("resubmission_continuity_enabled") is True else None)
    enabled_field, enabled_dispatcher = builder.revision_preprocess_fields(
        SimpleNamespace(content={}, edit={"invitation": {}}))

    owner.settings = {"resubmission_continuity_enabled": False}
    disabled_field, disabled_dispatcher = builder.revision_preprocess_fields(
        SimpleNamespace(content={"preprocess_script": enabled_field},
                        edit={"invitation": {"preprocess": enabled_dispatcher}}))
    assert disabled_field == {"delete": True}
    assert disabled_dispatcher == {"delete": True}


def test_custom_dispatcher_without_content_field_is_rejected_when_enabled():
    owner = SimpleNamespace(request_form_id="Neutral/Request",
        settings={"resubmission_continuity_enabled": True})
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    builder.preprocess_script = "native-dispatcher"
    builder.resubmission_submission_preprocess = lambda: (
        "def process(client, edit, invitation):\n    edit.events.append('continuity')\n"
        if owner.settings.get("resubmission_continuity_enabled") is True else None)
    dispatcher = (
        "def process(client, edit, invitation):\n    edit.events.append('custom')\n")
    with pytest.raises(ValueError, match="does not compose custom revision dispatchers"):
        builder.revision_preprocess_fields(SimpleNamespace(
            content={}, edit={"invitation": {"preprocess": dispatcher}}))


@pytest.mark.parametrize("host", ["openreview.net", "dev.openreview.net"])
def test_rendered_reviewer_assignment_accepts_prior_reviewer_on_supported_hosts(
        monkeypatch, host):
    class AssignmentJournal:
        venue_id = "Neutral/Venue"
        short_name = "NV"
        under_review_venue_id = "Neutral/Venue/Under_Review"
        settings = {"resubmission_continuity_enabled": True}
        assignment = SimpleNamespace(compute_conflicts=lambda *_args: [])
        def get_authors_id(self, number=None): return f"Neutral/Venue/Paper{number}/Authors"
        def get_review_id(self, number=None): return f"Neutral/Venue/Paper{number}/-/Review"
        def get_reviewer_assignment_id(self, number=None, archived=False):
            return (f"Neutral/Venue/Paper{number}/-/Assignment" if number else
                    "Neutral/Venue/Reviewers/-/Assignment")
        def get_solicit_reviewers_id(self, number=None): return "Neutral/Venue/Solicit"
        def get_reviewers_id(self, number=None, anon=False): return "Neutral/Venue/Reviewers"
        def get_reviewer_availability_id(self): return "Neutral/Venue/Reviewers/-/Availability"
        def get_reviewer_pending_review_id(self): return "Neutral/Venue/Reviewers/-/Pending"
        def get_resubmission_previous_submission_field(self): return "previous_NV_submission_url"

    journal = AssignmentJournal()
    submission = SimpleNamespace(id="current", number=2, content={
        "venueid": {"value": journal.under_review_venue_id},
        "previous_NV_submission_url": {"value": f"https://{host}/forum?id=prior"}})
    queries = []
    class AssignmentClient:
        fail_prior = False
        def get_note(self, _note_id): return submission
        def get_groups(self, id=None, member=None, **_kwargs):
            return [SimpleNamespace(id=id)] if id == journal.get_reviewers_id() else []
        def get_edges(self, invitation=None, head=None, tail=None, **_kwargs):
            queries.append((invitation, head, tail))
            if head == "prior":
                if self.fail_prior:
                    raise RuntimeError("prior lookup failed")
                return [SimpleNamespace(id="prior-assignment")]
            if invitation == journal.get_reviewer_pending_review_id():
                return [SimpleNamespace(weight=1)]
            return []
    client = AssignmentClient()
    monkeypatch.setattr(openreview.journal.JournalRequest, "get_journal",
                        staticmethod(lambda *_args: journal))
    owner = SimpleNamespace(request_form_id="Neutral/Request", settings=journal.settings)
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    source = builder.get_process_content("process/reviewer_assignment_pre_process.py")
    namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(source, "reviewer-assignment.py", "exec"), namespace)
    monkeypatch.setattr(openreview.tools, "get_invitation",
                        lambda *_args, **_kwargs: SimpleNamespace(id="active"))
    namespace["process"](client, SimpleNamespace(
        head="current", tail="~Reviewer1", tauthor="~Editor1", ddate=None), None)
    assert any(head == "prior" for _invitation, head, _tail in queries)

    submission.content["previous_NV_submission_url"]["value"] = "not-a-forum-url"
    queries.clear()
    with pytest.raises(openreview.OpenReviewException, match="pending reviews"):
        namespace["process"](client, SimpleNamespace(
            head="current", tail="~Reviewer1", tauthor="~Editor1", ddate=None), None)
    assert not any(head == "not-a-forum-url" for _invitation, head, _tail in queries)

    submission.content["previous_NV_submission_url"]["value"] = \
        "https://dev.openreview.net/forum?id=prior"
    client.fail_prior = True
    with pytest.raises(RuntimeError, match="prior lookup failed"):
        namespace["process"](client, SimpleNamespace(
            head="current", tail="~Reviewer1", tauthor="~Editor1", ddate=None), None)

    journal.settings["resubmission_continuity_enabled"] = False
    client.fail_prior = False
    disabled_source = builder.get_process_content(
        "process/reviewer_assignment_pre_process.py")
    disabled_namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(disabled_source, "disabled-reviewer-assignment.py", "exec"),
         disabled_namespace)
    edge = SimpleNamespace(
        head="current", tail="~Reviewer1", tauthor="~Editor1", ddate=None)
    for value, expected_head, bypasses_pending in (
            ("https://openreview.net/forum?id=prior", "prior", True),
            ("https://dev.openreview.net/forum?id=prior",
             "https://dev.openreview.net/forum?id=prior", False),
            ("not-a-forum-url", "not-a-forum-url", False)):
        submission.content["previous_NV_submission_url"]["value"] = value
        queries.clear()
        if bypasses_pending:
            disabled_namespace["process"](client, edge, None)
        else:
            with pytest.raises(openreview.OpenReviewException, match="pending reviews"):
                disabled_namespace["process"](client, edge, None)
        assert any(head == expected_head for _invitation, head, _tail in queries)

    journal.settings = {}
    submission.content["previous_NV_submission_url"]["value"] = \
        "https://openreview.net/forum?id=prior"
    queries.clear()
    absent_source = builder.get_process_content(
        "process/reviewer_assignment_pre_process.py")
    absent_namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(absent_source, "absent-reviewer-assignment.py", "exec"),
         absent_namespace)
    absent_namespace["process"](client, edge, None)
    assert any(head == "prior" for _invitation, head, _tail in queries)


def test_reviewer_assignment_callback_uses_shared_parser_and_normal_imports():
    settings = {"resubmission_continuity_enabled": False}
    owner = SimpleNamespace(request_form_id=None, settings=settings,
        venue_id="Neutral/Venue", secret_key="secret", contact_info="c@example.org",
        full_name="Neutral", short_name="NV", website="example.org",
        submission_name="Submission")
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    disabled = builder.get_process_content("process/reviewer_assignment_pre_process.py")
    assert "journal.settings.get('resubmission_continuity_enabled') is True" in disabled
    assert "def parse_forum_id" not in disabled
    compile(disabled, "disabled-reviewer-assignment.py", "exec")

    owner.settings = {"resubmission_continuity_enabled": True}
    enabled = builder.get_process_content("process/reviewer_assignment_pre_process.py")
    assert "from openreview.journal.resubmission import parse_forum_id" in enabled
    compile(enabled, "enabled-reviewer-assignment.py", "exec")


@pytest.mark.parametrize("request_form_id", [None, "Neutral/Request"])
def test_disabled_callbacks_remain_ordinary_importable_sources(request_form_id):
    owner = SimpleNamespace(request_form_id=request_form_id,
        settings={"resubmission_continuity_enabled": False},
        venue_id="Neutral/Venue", secret_key="secret", contact_info="c@example.org",
        full_name="Neutral", short_name="NV", website="example.org",
        submission_name="Submission")
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = owner
    for path in (
            "process/author_submission_process.py",
            "process/ae_assignment_pre_process.py",
            "process/ae_assignment_process.py",
            "process/reviewer_assignment_pre_process.py"):
        source = builder.get_process_content(path)
        compile(source, path, "exec")
        assert ("journal = openreview.journal.Journal(" in source or
                "journal = openreview.journal.JournalRequest.get_journal(" in source)
        assert "exec(" not in source


def test_disabled_legacy_score_field_and_immediate_mode_remain_separate():
    journal, client, current, _previous = fixture()
    journal.settings = {"resubmission_continuity_enabled": False}
    current.content["previous_NV_submission_url"] = {"value": URL}
    assert resubmission_score_assignments(client, journal, current)
    journal.settings = {"resubmission_continuity_enabled": True,
                        "resubmission_continuity": "immediate_previous_ae"}
    assert resubmission_score_assignments(client, journal, current) == []


def test_disabled_score_iteration_preserves_active_then_archived_error_order():
    journal, _client, current, _previous = fixture()
    journal.settings = {"resubmission_continuity_enabled": False}
    current.content["previous_NV_submission_url"] = {"value": URL}
    events = []

    class OrderedClient:
        def get_edges(self, invitation=None, head=None):
            events.append((invitation, head))
            if invitation == journal.get_ae_assignment_id():
                return [SimpleNamespace(tail="~AE1")]
            raise RuntimeError("archived lookup failed")

    assignments = iter_resubmission_score_assignments(
        OrderedClient(), journal, current)
    assert next(assignments).tail == "~AE1"
    assert events == [(journal.get_ae_assignment_id(), "prior")]
    with pytest.raises(RuntimeError, match="archived lookup failed"):
        next(assignments)
    assert events[-1] == (journal.get_ae_assignment_id(archived=True), "prior")
