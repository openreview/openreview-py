"""Standalone contracts for opt-in managed Journal tracks."""

import ast
import json
import shutil
import subprocess
from copy import deepcopy
from importlib import resources
from pathlib import Path
from types import SimpleNamespace

import openreview
import pytest

from openreview.journal import Journal
from openreview.journal.invitation import InvitationBuilder
from openreview.journal.tracks import (
    load_tracks,
    action_editor_eligibility_webfield,
    changed_action_editors,
    cleanup_action_editor_eligibility,
    refresh_submission_track_field,
    refresh_tracks,
    submission_track_field,
    validate_eligibility,
    validate_action_editor_update,
    validate_track_submission,
    validate_track_update,
    validate_tracks,
)


REGULAR = {"id": "Regular", "name": "Regular", "open": True}
OSS = {"id": "OSS", "name": "Open Source", "open": True}
AWARD = {"id": "Award", "name": "Award", "open": True}


def test_managed_track_schema_is_declared_as_package_data():
    manifest = Path(__file__).parents[1] / "MANIFEST.in"
    assert "include openreview/journal/schemas/*.json" in manifest.read_text()
    assert resources.files("openreview.journal").joinpath(
        "schemas/managed_tracks.json"
    ).is_file()


def test_manage_tracks_reports_saved_only_after_authoritative_reload():
    web = Path(__file__).parents[1].joinpath(
        "openreview/journal/webfield/manageTracksWebfield.js"
    ).read_text()
    assert "if (done) done(true);" in web
    assert "if (done) done(false);" in web
    assert "if (loaded) $('#journal-track-status').text('Saved.');" in web


def test_manage_tracks_executes_serial_saves_and_reports_reload_failure():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required to execute the Manage Tracks webfield")
    driver = Path(__file__).with_name("run_manage_tracks_webfield.js")
    webfield = Path(__file__).parents[1].joinpath(
        "openreview/journal/webfield/manageTracksWebfield.js"
    )
    result = subprocess.run(
        [node, str(driver), str(webfield)], text=True, capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "postCount": 4,
        "reloadStatus": "Authoritative reload failed.",
        "status": "Saved.",
    }


class TrackClient:
    def __init__(self, *, notes=(), edges=()):
        self.notes = list(notes)
        self.edges = list(edges)
        self.note_queries = []
        self.edge_queries = []

    def get_group(self, _group_id):
        return SimpleNamespace(content={"tracks": {"value": [REGULAR, OSS, AWARD]}},
                               members=["~AE1"], tmdate=123)

    def get_all_notes(self, **kwargs):
        assert kwargs["trash"] is True
        self.note_queries.append(kwargs)
        track_id = kwargs["content"]["track_id"]
        return [note for note in self.notes
                if note.content.get("track_id", {}).get("value") == track_id]

    def get_all_edges(self, **kwargs):
        self.edge_queries.append(kwargs)
        return [edge for edge in self.edges if edge.label == kwargs["label"]]


CONTEXT = {
    "venue_id": "Test",
    "tracks_id": "Test/Tracks",
    "submission_id": "Test/-/Submission",
    "track_eligibility_id": "Test/Action_Editors/-/Track_Eligible",
    "meta_id": "Test/-/Edit",
    "action_editors_id": "Test/Action_Editors",
    "eic_id": "Test/Editors_In_Chief",
}


def edit_tracks(records):
    return SimpleNamespace(group=SimpleNamespace(
        content={"tracks": {"value": records}}))


def test_serial_track_save_accepts_supplied_validated_order():
    proposed = [REGULAR, AWARD,
        {"id": "New", "name": "New", "open": True},
        {"id": "Later", "name": "Later", "open": False}]
    edit = edit_tracks(proposed)
    validate_track_update(TrackClient(), CONTEXT, edit)
    assert edit.group.content["tracks"]["value"] == proposed
    assert [item["id"] for item in proposed] == [
        "Regular", "Award", "New", "Later"
    ]


def test_add_or_close_track_does_not_scan_submission_history():
    client = TrackClient()
    closed = dict(OSS, open=False)
    validate_track_update(client, CONTEXT, edit_tracks([REGULAR, closed, AWARD]))
    validate_track_update(client, CONTEXT, edit_tracks([
        REGULAR, OSS, AWARD, {"id": "New", "name": "New", "open": True},
    ]))
    assert client.note_queries == []
    assert client.edge_queries == []


@pytest.mark.parametrize(
    "client",
    [
        TrackClient(notes=[SimpleNamespace(content={"track_id": {"value": "OSS"}})]),
        TrackClient(edges=[SimpleNamespace(label="OSS", ddate=None)]),
    ],
)
def test_referenced_track_removal_is_rejected(client):
    with pytest.raises(openreview.OpenReviewException, match="close them instead: OSS"):
        validate_track_update(client, CONTEXT, edit_tracks([REGULAR, AWARD]))


def test_submission_reference_short_circuits_eligibility_lookup():
    client = TrackClient(notes=[SimpleNamespace(
        content={"track_id": {"value": "OSS"}})])
    with pytest.raises(openreview.OpenReviewException, match="OSS"):
        validate_track_update(client, CONTEXT, edit_tracks([REGULAR, AWARD]))
    assert client.edge_queries == []


def test_tombstoned_eligibility_does_not_block_unused_track_removal():
    client = TrackClient(edges=[SimpleNamespace(label="OSS", ddate=1)])
    validate_track_update(client, CONTEXT, edit_tracks([REGULAR, AWARD]))


def test_every_referenced_removed_track_is_reported():
    client = TrackClient(notes=[
        SimpleNamespace(content={"track_id": {"value": "OSS"}}),
        SimpleNamespace(content={"track_id": {"value": "Award"}}),
    ])
    with pytest.raises(openreview.OpenReviewException, match="OSS, Award"):
        validate_track_update(client, CONTEXT, edit_tracks([REGULAR]))


def test_serial_track_save_allows_reordering_and_insertion():
    new = {"id": "New", "name": "New", "open": True}
    validate_track_update(
        TrackClient(), CONTEXT, edit_tracks([REGULAR, AWARD, new, OSS]))


def test_orphaned_eligibility_edge_can_be_deleted_after_unused_track_removal():
    edge = SimpleNamespace(
        tail="~AE1", label="Removed", ddate=1,
        readers=["Test/Editors_In_Chief", "~AE1"],
    )
    validate_eligibility(TrackClient(), CONTEXT, edge, managed=True)


def test_active_eligibility_edges_remain_private_to_venue_and_eic():
    edge = SimpleNamespace(
        tail="~AE1", label="OSS", ddate=None,
        readers=["Test", "Test/Editors_In_Chief"],
    )
    validate_eligibility(TrackClient(), CONTEXT, edge, managed=True)
    edge.readers = ["everyone"]
    with pytest.raises(openreview.OpenReviewException, match="readers are invalid"):
        validate_eligibility(TrackClient(), CONTEXT, edge, managed=True)


def test_direct_api_duplicate_eligibility_is_validated_but_consumed_as_a_set():
    existing = SimpleNamespace(
        id="edge-1", head="Test/Action_Editors", tail="~AE1", label="OSS",
        ddate=None, readers=["Test", "Test/Editors_In_Chief"])
    client = TrackClient(edges=[existing])
    duplicate = SimpleNamespace(
        id=None, invitation="Test/Action_Editors/-/Track_Eligible",
        head=existing.head, tail=existing.tail, label=existing.label, ddate=None,
        readers=list(existing.readers))
    validate_eligibility(client, CONTEXT, duplicate, managed=True)
    duplicate.id = existing.id
    validate_eligibility(client, CONTEXT, duplicate, managed=True)


def execute_callback(source):
    namespace = {"openreview": openreview}
    exec(compile(source, "emitted-track-callback.py", "exec"), namespace)
    return namespace["process"]


def test_emitted_track_callbacks_run_in_fresh_server_namespace():
    builder, artifacts = track_artifacts()
    client = TrackClient()
    submission = builder.track_submission_preprocess(None)
    process = execute_callback(submission)
    process(client, SimpleNamespace(note=SimpleNamespace(
        content={"track_id": {"value": "OSS"}}
    )), None)
    with pytest.raises(openreview.OpenReviewException, match="open track"):
        process(client, SimpleNamespace(note=SimpleNamespace(
            content={"track_id": {"value": "Missing"}}
        )), None)

    manage = artifacts["Test/-/Manage_Tracks"].preprocess
    execute_callback(manage)(client, edit_tracks([REGULAR, OSS, AWARD]), None)
    with pytest.raises(openreview.OpenReviewException, match="Regular must"):
        execute_callback(manage)(client, edit_tracks([OSS, AWARD]), None)

    posted = []
    refresh_client = TrackClient()
    refresh_client.get_invitation = lambda _invitation_id: SimpleNamespace(
        edit={"note": {"content": {}}}, signatures=[]
    )
    refresh_client.post_invitation_edit = lambda **kwargs: posted.append(kwargs)
    postprocess = artifacts["Test/-/Manage_Tracks"].process
    execute_callback(postprocess)(refresh_client, None, None)
    assert posted[0]["invitation"].edit["note"]["content"]["track_id"]


@pytest.mark.parametrize("managed,label", [(False, "Regular Ineligible"), (True, "OSS")])
def test_emitted_eligibility_callbacks_run_for_create_and_delete(managed, label):
    _, artifacts = track_artifacts()
    invitation_id = ("Test/Action_Editors/-/Track_Eligible" if managed else
                     "Test/Action_Editors/-/Regular_Ineligible")
    process = execute_callback(artifacts[invitation_id].preprocess)
    process(TrackClient(), SimpleNamespace(
        tail="~AE1", label=label, ddate=None,
        readers=["Test", "Test/Editors_In_Chief"],
    ), None)
    process(TrackClient(), SimpleNamespace(
        tail="~AE1", label=label, ddate=1,
        readers=["Test/Editors_In_Chief", "~AE1"],
    ), None)


def test_eligibility_schema_and_callback_allow_safe_membership_cleanup_and_readd():
    enabled = TrackInvitationJournal(True)
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = enabled
    saved = []
    builder.save_invitation = saved.append
    builder.set_track_invitations()
    eligibility = [invitation for invitation in saved if invitation.id in {
        enabled.get_regular_ineligible_id(), enabled.get_track_eligibility_id()}]
    assert len(eligibility) == 2
    for invitation in eligibility:
        assert invitation.edit["id"]["param"] == {
            "withInvitation": invitation.id, "optional": True}
        assert invitation.edit["head"]["param"] == {
            "type": "group", "const": enabled.get_action_editors_id()}
        tail = invitation.edit["tail"]["param"]
        assert tail == {"type": "profile"}
        assert invitation.edit["ddate"]["param"]["deletable"] is True
        assert "assignment_id" not in invitation.preprocess
        assert "regular_ineligible_id" not in invitation.preprocess
        assert "active_venue_ids" not in invitation.preprocess

    score = next(
        invitation for invitation in saved
        if invitation.id == enabled.get_track_score_id())
    assert score.edit["id"]["param"] == {
        "withInvitation": score.id, "optional": True}
    assert score.edit["nonreaders"] == []
    assert score.edit["ddate"]["param"]["deletable"] is True

    members = ["~AE1"]
    client = TrackClient()
    client.get_group = lambda _group_id: SimpleNamespace(
        content={"tracks": {"value": [REGULAR, OSS, AWARD]}}, members=list(members))
    process = execute_callback(next(
        invitation.preprocess for invitation in eligibility
        if invitation.id == enabled.get_track_eligibility_id()))
    active = SimpleNamespace(tail="~AE1", label="OSS", ddate=None,
                             readers=["Test", "Test/Editors_In_Chief"])
    process(client, active, None)
    members.clear()
    with pytest.raises(openreview.OpenReviewException, match="current Action Editor"):
        process(client, active, None)
    process(client, SimpleNamespace(
        tail="~AE1", label="OSS", ddate=1,
        readers=["Test/Editors_In_Chief", "~AE1"]), None)
    members.append("~AE1")
    process(client, active, None)


def test_native_action_editor_eligibility_page_and_callbacks_are_venue_bound():
    web = action_editor_eligibility_webfield("Neutral/Venue")
    assert "Neutral/Venue/-/Manage_Action_Editors" in web
    assert "Neutral/Venue/Action_Editors/-/Regular_Ineligible" in web
    assert "VENUE_PLACEHOLDER" not in web and "JMLR/" not in web

    _, artifacts = track_artifacts()
    edit = SimpleNamespace(
        group=SimpleNamespace(members={"remove": ["~AE1"]}), tmdate=1234)
    active_client = SimpleNamespace(
        get_edges=lambda **_kwargs: [SimpleNamespace(head="paper")],
        get_note=lambda _id: SimpleNamespace(
            number=7, content={"venueid": {"value": "Test/Under_Review"}}
        ),
    )
    manage = artifacts["Test/-/Manage_Action_Editors"]
    with pytest.raises(openreview.OpenReviewException, match="Paper7"):
        execute_callback(manage.preprocess)(active_client, edit, None)

    expired = []
    existing = SimpleNamespace(id="edge", ddate=None, label="OSS")
    cleanup_client = SimpleNamespace(
        get_edges=lambda **_kwargs: [existing],
        post_edge=lambda edge: expired.append(edge),
    )
    execute_callback(manage.process)(cleanup_client, edit, None)
    assert len(expired) == 2
    assert all(edge.readers == ["Test/Editors_In_Chief", "~AE1"]
               and edge.ddate for edge in expired)


def test_action_editor_page_retires_every_duplicate_eligibility_edge():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required to execute the Action Editor eligibility webfield")
    driver = Path(__file__).resolve().with_name("run_action_editor_eligibility_webfield.js")
    webfield = Path(__file__).resolve().parents[1].joinpath(
        "openreview/journal/webfield/actionEditorEligibilityWebfield.js"
    )
    result = subprocess.run([
        node, str(driver), str(webfield),
    ], check=True, capture_output=True, text=True)
    assert json.loads(result.stdout) == {
        "retired": ["first", "second"], "remaining": 0}


class TrackInvitationJournal:
    venue_id = "Test"
    secret_key = "secret"
    contact_info = "editors@example.org"
    full_name = "Test Journal"
    short_name = "Test"
    website = "https://example.org"
    submission_name = "Submission"
    request_form_id = None
    settings = {"tracks": [REGULAR, OSS]}
    submitted_venue_id = "Test/Submitted"
    under_review_venue_id = "Test/Under_Review"
    assigning_AE_venue_id = "Test/Assigning_AE"
    assigned_AE_venue_id = "Test/Assigned_AE"
    def __init__(self, enabled): self.enabled = enabled
    def has_managed_tracks(self): return self.enabled
    def get_tracks_id(self): return "Test/Tracks"
    def get_author_submission_id(self): return "Test/-/Submission"
    def get_track_eligibility_id(self): return "Test/Action_Editors/-/Track_Eligible"
    def get_meta_invitation_id(self): return "Test/-/Edit"
    def get_manage_tracks_id(self): return "Test/-/Manage_Tracks"
    def get_editors_in_chief_id(self): return "Test/Editors_In_Chief"
    def get_action_editors_id(self): return "Test/Action_Editors"
    def get_ae_assignment_id(self): return "Test/Action_Editors/-/Assignment"
    def get_regular_ineligible_id(self): return "Test/Action_Editors/-/Regular_Ineligible"
    def get_track_score_id(self): return "Test/Action_Editors/-/Track_Score"
    def get_add_action_editor_id(self): return "Test/-/Add_Action_Editor"
    def get_manage_action_editors_id(self): return "Test/-/Manage_Action_Editors"


def track_artifacts(enabled=True):
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = TrackInvitationJournal(enabled)
    saved = []
    builder.save_invitation = saved.append
    builder.set_track_invitations()
    return builder, {invitation.id: invitation for invitation in saved}


@pytest.mark.parametrize("tracks", [[], [REGULAR, OSS], False])
@pytest.mark.parametrize("request_id", [None, "request123"])
def test_generated_track_callback_preserves_journal_settings(monkeypatch, tracks, request_id):
    client = SimpleNamespace()
    journal = Journal(client, "Test", "secret", "editors@example.org",
        'Test "Journal"', "TJ", settings={"tracks": tracks})
    journal.request_form_id = request_id
    source = journal.invitation_builder.get_process_content(
        "process/track_submission_pre_process.py")
    reconstructed = []
    def construct(*args, **kwargs):
        result = Journal(*args, **kwargs)
        reconstructed.append(result)
        return result
    monkeypatch.setattr(openreview.journal, "Journal", construct)
    monkeypatch.setattr(openreview.journal.JournalRequest, "get_journal",
        lambda actual_client, actual_id: (
            reconstructed.append(journal) or journal)
            if actual_client is client and actual_id == request_id else None)
    monkeypatch.setattr(openreview.journal.tracks, "validate_track_submission",
        lambda *_args: None)
    namespace = {}
    exec(source, namespace)
    namespace["process"](client, SimpleNamespace(), None)
    assert len(reconstructed) == 1
    assert reconstructed[0].settings.get("tracks", False) == tracks
    assert reconstructed[0].full_name == journal.full_name


def test_missing_tracks_setting_leaves_track_invitations_untouched():
    journal = Journal(SimpleNamespace(), "Test", "secret", "editors@example.org",
        "Test Journal", "TJ", settings={})
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = journal
    saved, expired = [], []
    builder.save_invitation = saved.append
    builder.expire_invitation = expired.append
    builder.set_track_invitations()
    assert saved == []
    assert expired == []


def test_empty_tracks_setting_opts_in_with_regular_seed(monkeypatch):
    journal = Journal(SimpleNamespace(), "Test", "secret", "editors@example.org",
        "Test Journal", "TJ", settings={"tracks": []})
    monkeypatch.setattr(openreview.tools, "get_group", lambda *_args: None)
    assert journal.has_managed_tracks()
    assert journal.get_tracks() == [REGULAR]


def test_venue_owned_submission_preprocess_is_not_double_wrapped():
    journal = Journal(SimpleNamespace(), "Test", "secret", "editors@example.org",
        "Test Journal", "TJ", settings={"tracks": []})
    builder = journal.invitation_builder
    owned = ("def process(client, edit, invitation):\n"
             "    pass\n"
             "# journal-track-preprocess-owner-v1\n")
    assert builder.track_submission_preprocess(owned) == owned

    ordinary = "def process(client, edit, invitation):\n    pass\n"
    with pytest.raises(ValueError, match="require ownership"):
        builder.track_submission_preprocess(ordinary)


def test_disabling_tracks_removes_owned_preprocess():
    journal = Journal(SimpleNamespace(), "Test", "secret", "editors@example.org",
        "Test Journal", "TJ", settings={"tracks": []})
    builder = journal.invitation_builder
    wrapped = builder.track_submission_preprocess(None)
    builder.journal = Journal(SimpleNamespace(), "Test", "secret",
        "editors@example.org", "Test Journal", "TJ", settings={"tracks": False})
    assert builder.track_submission_preprocess(wrapped) == {"delete": True}


@pytest.mark.parametrize("tracks,expect_track", [
    (None, False), (False, False), ([], True), ([REGULAR, OSS], True),
])
def test_assign_ae_invitation_gates_track_score_browser_column(tracks, expect_track):
    settings = {} if tracks is None else {"tracks": tracks}
    journal = Journal(SimpleNamespace(), "Test", "secret", "editors@example.org",
        "Test Journal", "TJ", settings=settings)
    saved = []
    journal.invitation_builder.save_invitation = saved.append
    journal.invitation_builder.set_ae_assignment(0)
    assignment = next(invitation for invitation in saved
                      if invitation.id == journal.get_ae_assignment_id())
    marker = "Test/Action_Editors/-/Track_Score"
    web = getattr(assignment, "web", None)
    assert bool(web) is expect_track
    assert (marker in (web or "")) is expect_track
    assert "Aggregate_Score" not in (web or "")


def test_all_native_manual_ae_urls_share_one_tracks_only_score_list():
    root = Path(__file__).resolve().parents[1]
    web = (root / "openreview/journal/webfield/editorsInChiefWebfield.js").read_text()
    group = (root / "openreview/journal/group.py").read_text()
    assert web.count("aeBrowseInvitations.join(';')") == 2
    assert "if (ACTION_EDITORS_TRACK_SCORE_ID)" in web
    guards = [node for node in ast.walk(ast.parse(group))
              if isinstance(node, ast.If) and
              "has_managed_tracks" in ast.unparse(node.test)]
    assert len(guards) == 1
    assert "get_track_score_id" in ast.unparse(guards[0])
    assert "Aggregate_Score" not in web


def test_track_routes_disable_completely_and_reenable_from_schema():
    disabled = TrackInvitationJournal(False)
    disabled.settings = {"tracks": False}
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = disabled
    expired = []
    builder.expire_invitation = expired.append
    builder.set_track_invitations()
    assert set(expired) == {
        disabled.get_manage_tracks_id(), disabled.get_add_action_editor_id(),
        disabled.get_manage_action_editors_id(), disabled.get_regular_ineligible_id(),
        disabled.get_track_eligibility_id(), disabled.get_track_score_id()}

    enabled = TrackInvitationJournal(True)
    builder.journal = enabled
    saved = []
    builder.save_invitation = saved.append
    builder.set_track_invitations()
    assert {invitation.id for invitation in saved} == {
        enabled.get_manage_tracks_id(), enabled.get_add_action_editor_id(),
        enabled.get_manage_action_editors_id(), enabled.get_regular_ineligible_id(),
        enabled.get_track_eligibility_id(), enabled.get_track_score_id()}
    manage = next(item for item in saved
                  if item.id == enabled.get_manage_tracks_id())
    assert manage.edit["group"]["content"]["tracks"]["value"]["param"] == {
        "type": "object[]"
    }
    assert manage.edit["group"]["readers"] == ["everyone"]
    assert manage.edit["group"]["writers"] == ["Test"]
    assert manage.edit["group"]["signatures"] == ["Test"]
    assert manage.edit["group"]["signatories"] == ["Test"]
    assert "value: tracks" in manage.web
    assert "typeof value === 'string' ? JSON.parse(value) : value" in manage.web
    assert not manage.preprocess.startswith("import ")
    assert not manage.process.startswith("import ")


def test_track_backend_and_page_use_all_results_for_eligibility():
    edge = SimpleNamespace(id="late", head="paper", tail="~AE1", label="OSS",
                           ddate=None)
    client = SimpleNamespace(
        get_all_edges=lambda **_kwargs: [edge],
        get_edges=lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("bounded get_edges must not be used")),
        get_note=lambda _id: SimpleNamespace(
            number=9, content={"venueid": {"value": "Test/Under_Review"}}))
    edit = SimpleNamespace(
        group=SimpleNamespace(members={"remove": ["~AE1"]}), cdate=5678)
    with pytest.raises(openreview.OpenReviewException, match="Paper9"):
        validate_action_editor_update(client, dict(CONTEXT,
            assignment_id="Test/Action_Editors/-/Assignment",
            active_venue_ids=["Test/Under_Review"]), edit)

    posted = []
    client.post_edge = posted.append
    cleanup_action_editor_eligibility(client, dict(CONTEXT,
        regular_ineligible_id="Test/Action_Editors/-/Regular_Ineligible",
        eic_id="Test/Editors_In_Chief"), edit)
    assert len(posted) == 2 and all(item.ddate for item in posted)
    web = action_editor_eligibility_webfield("Test")
    assert web.count("Webfield2.api.getAll('/edges'") == 2


def test_track_refresh_changes_only_choices_and_is_idempotent():
    field = {
        "description": "Venue-specific instructions",
        "order": 42,
        "readers": ["Test/Editors_In_Chief"],
        "value": {"param": {
            "type": "string", "enum": ["stale", "Previous track"],
            "input": "select", "optional": True,
        }},
    }
    submission = SimpleNamespace(
        edit={"note": {"content": {"track_id": field}}}, signatures=[])
    writes = []
    client = TrackClient()
    client.get_invitation = lambda _invitation_id: submission
    client.post_invitation_edit = lambda **kwargs: writes.append(kwargs)
    refresh_tracks(client, CONTEXT, None)
    refresh_tracks(client, CONTEXT, None)
    assert submission.edit["note"]["content"]["track_id"] == {
        "description": "Venue-specific instructions",
        "order": 42,
        "readers": ["Test/Editors_In_Chief"],
        "value": {"param": {
            "type": "string",
            "enum": [
                {"value": "Regular", "description": "Regular"},
                {"value": "OSS", "description": "Open Source"},
                {"value": "Award", "description": "Award"},
            ],
            "input": "select", "optional": True,
        }},
    }
    assert len(writes) == 2


def test_track_refresh_drops_non_native_extra_choice():
    field = {"value": {"param": {
        "type": "string", "enum": [
            "Regular", "Closed ordinary track", "Previous track"]}}}
    submission = SimpleNamespace(
        edit={"note": {"content": {"track_id": field}}}, signatures=[],
        preprocess="# journal-track-preprocess-owner-v1\ndef process(*args): pass\n")
    client = TrackClient()
    client.get_invitation = lambda _invitation_id: submission
    client.post_invitation_edit = lambda **_kwargs: None
    refresh_tracks(client, CONTEXT, None)
    refresh_tracks(client, CONTEXT, None)
    choices = submission.edit["note"]["content"]["track_id"]["value"]["param"]["enum"]
    assert [choice["value"] for choice in choices] == ["Regular", "OSS", "Award"]


def test_track_refresh_creates_generic_field_only_when_absent():
    submission = SimpleNamespace(edit={"note": {"content": {}}}, signatures=[])
    client = TrackClient()
    client.get_invitation = lambda _invitation_id: submission
    client.post_invitation_edit = lambda **_kwargs: None
    refresh_tracks(client, CONTEXT, None)
    assert submission.edit["note"]["content"]["track_id"] == \
        submission_track_field([REGULAR, OSS, AWARD])


def test_repeated_setup_preserves_existing_or_configured_track_surface():
    existing = {"track_id": {
        "description": "Existing instructions", "order": 2,
        "readers": ["Test/Editors_In_Chief"],
        "value": {"param": {"type": "string", "enum": ["stale"],
            "input": "select", "optional": False}},
    }}
    rebuilt = {"track_id": existing["track_id"]}
    refresh_submission_track_field(rebuilt, [REGULAR])
    assert rebuilt["track_id"]["description"] == "Existing instructions"
    assert rebuilt["track_id"]["order"] == 2
    assert rebuilt["track_id"]["readers"] == ["Test/Editors_In_Chief"]
    assert rebuilt["track_id"]["value"]["param"] == {
        "type": "string", "enum": [{"value": "Regular", "description": "Regular"}],
        "input": "select", "optional": False,
    }
    configured = {"track_id": {
        "description": "New configured instructions", "order": 3,
        "value": {"param": {"type": "string", "enum": [], "input": "radio"}},
    }}
    refresh_submission_track_field(configured, [REGULAR, OSS])
    assert configured["track_id"]["description"] == "New configured instructions"
    assert configured["track_id"]["order"] == 3
    assert configured["track_id"]["value"]["param"]["input"] == "radio"


@pytest.mark.parametrize("mode", ["configured", "existing", "override"])
def test_actual_submission_setup_preserves_track_field(monkeypatch, mode):
    records = [REGULAR, OSS, {"id": "Award", "name": "Award", "open": False}]
    original = {
        "description": "Custom instructions", "order": 2,
        "readers": ["V/Editors_In_Chief"],
        "value": {"param": {"type": "string", "enum": ["stale"],
            "input": "select", "optional": False}},
    }
    configured = deepcopy(original) if mode != "existing" else None
    if mode == "override":
        configured.update(description="New configured instructions", order=3)
    stored = None if mode == "configured" else openreview.api.Invitation(
        id="V/-/Submission",
        edit={"note": {"content": {"track_id": deepcopy(original)}}})
    journal = Journal(SimpleNamespace(), "V", "secret", "editors@example.org",
        "Venue", "V", settings={"tracks": [],
            "submission_additional_fields": ({"track_id": configured}
                if configured else {})})
    monkeypatch.setattr(journal, "get_tracks", lambda: records)
    monkeypatch.setattr(openreview.tools, "get_invitation", lambda *_args: stored)
    saved = []
    monkeypatch.setattr(journal.invitation_builder, "save_invitation", saved.append)
    expected = deepcopy(configured or original)
    expected["value"]["param"]["enum"] = [
        {"value": "Regular", "description": "Regular"},
        {"value": "OSS", "description": "Open Source"},
    ]
    for _ in range(2):
        journal.invitation_builder.set_submission_invitation()
        stored = saved[-1]
        assert stored.edit["note"]["content"]["track_id"] == expected
