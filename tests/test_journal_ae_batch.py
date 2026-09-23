"""Standalone contracts for AE batch preparation on managed tracks."""

import json
from pathlib import Path
import re
import shutil
import subprocess
from types import SimpleNamespace

import openreview
import pytest

from openreview.journal import Journal
from openreview.journal.ae_batch import (
    batch_is_enabled, batch_recommendation_eligible,
    batch_track_pairs,
    batch_track_reconcile,
    prepare_ae_batch,
    validate_batch_configuration,
)
from openreview.journal.invitation import InvitationBuilder


REGULAR = {"id": "Regular", "name": "Regular", "open": True}
OSS = {"id": "OSS", "name": "Open Source", "open": True}
EIC_WEBFIELD = Path(__file__).parents[1] / "openreview/journal/webfield/editorsInChiefWebfield.js"
NODE = shutil.which("node")


def render_eic_navigation(batch_setting):
    if not NODE:
        pytest.skip("Node.js is required for the Journal webfield unit test")
    source = EIC_WEBFIELD.read_text(encoding="utf-8")
    source = source.replace("var VENUE_ID = '';", "var VENUE_ID = 'Test';")
    source = source.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = 'Action_Editors';")
    if batch_setting is True:
        source = source.replace(
            "var PREPARE_AE_BATCH_ID = '';",
            "var PREPARE_AE_BATCH_ID = 'Test/-/Prepare_Action_Editor_Batch';",
        )
    source = re.sub(r"\nmain\(\);\s*$", "", source)
    program = """
const vm = require('vm');
const context = {encodeURIComponent, args: {perf: '0'}};
vm.createContext(context);
vm.runInContext(JSON.parse(process.argv[1]), context);
process.stdout.write(JSON.stringify(context.HEADER.instructions));
"""
    completed = subprocess.run(
        [NODE, "-e", program, json.dumps(source)], check=True,
        capture_output=True, text=True,
    )
    return json.loads(completed.stdout)


def navigation_rows(html):
    return re.findall(r'<ul class="list-inline mb-0">(.*?)</ul>', html)


@pytest.mark.parametrize("batch_setting", [None, False, "true", 1])
def test_default_eic_navigation_preserves_original_assignments_row(batch_setting):
    rows = navigation_rows(render_eic_navigation(batch_setting))
    assignments = next(row for row in rows if "Assignments Browser:" in row)
    assert "Action Editor Proposed Assignments" in assignments
    assert "Run / Inspect / Deploy Batch" not in assignments
    assert all("Batch AE Assignment:" not in row for row in rows)


def test_enabled_eic_navigation_groups_batch_controls_in_one_row():
    rows = navigation_rows(render_eic_navigation(True))
    assignments = next(row for row in rows if "Assignments Browser:" in row)
    batch = [row for row in rows if "Batch AE Assignment:" in row]
    assert len(batch) == 1
    assert "Action Editor Proposed Assignments" not in assignments
    assert "Run / Inspect / Deploy Batch" not in assignments
    assert batch[0].index("Prepare Batch") < batch[0].index("Run / Inspect / Deploy Batch")
    assert batch[0].count("Test%2F-%2FPrepare_Action_Editor_Batch") == 1
    assert batch[0].count("/assignments?group=Test/Action_Editors") == 1


def test_eic_submitted_table_keeps_unassigned_assigning_papers_visible():
    source = EIC_WEBFIELD.read_text(encoding="utf-8")
    submitted_filter = source[source.index("var submittedStatusRows"):
                              source.index("var underReviewStatusRows")]
    assert "row.submission.content.venueid === SUBMITTED_STATUS" in submitted_filter
    assert "row.submission.content.venueid === ASSIGNING_AE_STATUS" in submitted_filter


def execute_callback(source):
    namespace = {"openreview": openreview}
    exec(compile(source, "emitted-batch-callback.py", "exec"), namespace)
    return namespace["process"]


def test_ae_batch_callback_is_an_ordinary_native_process():
    journal = Journal(SimpleNamespace(), "Test", "secret", "editors@example.org",
        "Test Journal", "TJ", settings={"tracks": [],
        "ae_batch_preparation_enabled": True})
    saved = []
    journal.invitation_builder.save_invitation = saved.append
    journal.invitation_builder.set_ae_batch_invitation()
    source = saved[0].process
    assert source.startswith('def process(client, edit, invitation):\n')
    compile(source, 'emitted-batch-callback.py', 'exec')
    assert 'inspect.getsource' not in source


def test_pr4_direct_callback_forwards_only_matching_and_continuity_settings():
    journal = Journal(
        SimpleNamespace(), "Test", "secret", "editors@example.org", "Test Journal", "TJ",
        settings={"tracks": [], "ae_batch_preparation_enabled": True,
                  "skip_ac_recommendation": True,
                  "action_editors_max_papers": 7,
                  "ae_max_active_submissions": 4,
                  "resubmission_continuity_enabled": True,
                  "resubmission_continuity": "score",
                  "resubmission_previous_submission_field": "prior_round",
                  "resubmission_permission_field": "permission",
                  "resubmission_permission_value": "allowed",
                  "submission_public": False,
                  "release_submission_after_acceptance": False})
    builder = journal.invitation_builder
    captured = []
    builder.save_invitation = captured.append
    builder.set_ae_batch_invitation()
    source = captured[0].process
    assert "'tracks': []" in source
    assert "'ae_batch_preparation_enabled': True" in source
    assert "'skip_ac_recommendation': True" in source
    assert "'action_editors_max_papers': 7" in source
    assert "'ae_max_active_submissions': 4" in source
    assert "'resubmission_continuity_enabled': True" in source
    assert "'resubmission_continuity': 'score'" in source
    assert "resubmission_previous_submission_field" not in source
    assert "resubmission_permission_field" not in source
    assert "resubmission_permission_value" not in source
    assert "submission_public" not in source
    assert "release_submission_after_acceptance" not in source


@pytest.mark.parametrize("request_form_id", [None, "Test/Request"])
def test_batch_callback_uses_matching_nondefault_quotas(monkeypatch, request_form_id):
    settings = {"tracks": [], "ae_batch_preparation_enabled": True,
                "action_editors_max_papers": 7,
                "ae_max_active_submissions": 4}
    owner = Journal(SimpleNamespace(), "Test", "secret", "editors@example.org",
        "Test Journal", "TJ", settings=settings)
    owner.request_form_id = request_form_id
    saved = []
    owner.invitation_builder.save_invitation = saved.append
    owner.invitation_builder.set_ae_batch_invitation()
    process = execute_callback(saved[0].process)

    observed = []
    original = openreview.journal.Journal
    def construct(*args, **kwargs):
        journal = original(*args, **kwargs)
        observed.append(journal)
        return journal
    monkeypatch.setattr(openreview.journal, "Journal", construct)
    monkeypatch.setattr(openreview.tools, "get_group", lambda *_args: SimpleNamespace(
        content={"secret_key": {"value": "secret"}}))
    request_note = SimpleNamespace(content={
        "venue_id": {"value": "Test"}, "contact_info": {"value": "editors@example.org"},
        "official_venue_name": {"value": "Test Journal"},
        "abbreviated_venue_name": {"value": "TJ"},
        "website": {"value": "https://example.org"}, "support_role": {"value": "Support"},
        "editors": {"value": ["~EIC1"]}, "settings": {"value": settings}})
    batch_note = SimpleNamespace(id="request", content={"status": {"value": "Prepared"}})
    client = SimpleNamespace(get_note=lambda note_id: (
        request_note if note_id == request_form_id else batch_note))
    process(client, SimpleNamespace(note=SimpleNamespace(id="request")), None)
    active = observed[0]
    assert active.get_ae_max_papers() == 7
    assert active.get_ae_max_active_submissions() == 4


def test_batch_invitation_renders_one_eic_form_with_exact_note_edit():
    journal = Journal(
        SimpleNamespace(), "Test", "secret", "editors@example.org", "Test Journal", "TJ",
        settings={"tracks": [REGULAR, OSS], "ae_batch_preparation_enabled": True})
    saved = []
    journal.invitation_builder.save_invitation = saved.append
    journal.invitation_builder.set_ae_batch_invitation()
    invitation = saved[0]
    assert "var PREPARE_AE_BATCH_ID = 'Test/-/Prepare_Action_Editor_Batch';" in invitation.web
    assert "var EIC_ID = 'Test/Editors_In_Chief';" in invitation.web
    assert "var VENUE_ID = 'Test';" in invitation.web
    assert "Webfield2.api.post('/notes/edits'" in invitation.web
    assert "invitation: PREPARE_AE_BATCH_ID" in invitation.web
    assert "status: {value: 'Pending'}" in invitation.web
    assert "Prepare batch" in invitation.web


def test_native_configuration_schema_exposes_terminal_recovery_statuses():
    journal = Journal(
        SimpleNamespace(), "Test", "secret", "editors@example.org", "Test Journal", "TJ")
    saved = []
    journal.invitation_builder.save_invitation = saved.append
    journal.invitation_builder.set_assignment_configuration_invitation()
    status = saved[0].edit["note"]["content"]["status"]["value"]["param"]
    assert status["input"] == "select"
    assert "Cancelled" in status["enum"]
    assert "Deployed" in status["enum"]
    assert saved[0].invitees == ["Test"]


def test_batch_track_matrix_is_complete_and_uses_classical_eligibility_rules():
    papers = [
        SimpleNamespace(id="regular", content={"track_id": {"value": "Regular"}}),
        SimpleNamespace(id="oss", content={"track_id": {"value": "OSS"}}),
    ]
    regular_ineligible = [SimpleNamespace(tail="~AE2", ddate=None)]
    managed = [SimpleNamespace(tail="~AE2", label="OSS", ddate=None)]
    assert batch_track_pairs(
        papers, ["~AE1", "~AE2"], [REGULAR, OSS], regular_ineligible, managed
    ) == {
        ("regular", "~AE1"): 1,
        ("regular", "~AE2"): 0,
        ("oss", "~AE1"): 0,
        ("oss", "~AE2"): 1,
    }


@pytest.mark.parametrize("count,skip,expected", [
    (0, None, False), (2, None, False), (3, None, True),
    (0, False, False), (2, False, False), (3, False, True),
    (0, True, True), (2, True, True), (3, True, True),
])
def test_batch_recommendation_policy_matches_native(count, skip, expected):
    edges = [SimpleNamespace(ddate=None) for _ in range(count)]
    client = SimpleNamespace(get_all_edges=lambda **_kwargs: edges)
    journal = SimpleNamespace(
        venue_id="Test",
        should_skip_ac_recommendation=lambda: skip,
        get_ae_recommendation_id=lambda: "Test/-/Recommendation")
    assert batch_recommendation_eligible(
        client, journal, SimpleNamespace(id="paper")) is expected


@pytest.mark.parametrize("batch_setting", [None, False])
def test_legacy_matching_does_not_apply_batch_skip_exception(batch_setting):
    settings = {"skip_ac_recommendation": True}
    if batch_setting is not None:
        settings["ae_batch_preparation_enabled"] = batch_setting
    paper = SimpleNamespace(id="paper", number=1, invitations=[], content={})

    class Client:
        def get_notes(self, **kwargs):
            return [paper] if kwargs["content"]["venueid"] == "Test/Submitted" else []
        def get_group(self, group_id):
            return SimpleNamespace(members=[] if "Paper1" in group_id else ["~AE1"])
        def get_edges(self, **_kwargs): return []
        def get_all_notes(self, **_kwargs): raise RuntimeError("past selection")
        def post_note_edit(self, **_kwargs):
            raise AssertionError("legacy paper was selected by batch-only skip")

    journal = SimpleNamespace(
        client=Client(), settings=settings, venue_id="Test", short_name="TJ",
        submitted_venue_id="Test/Submitted", assigning_AE_venue_id="Test/Assigning_AE",
        get_author_submission_id=lambda: "Test/-/Submission",
        get_action_editors_id=lambda number=None: (
            "Test/Action_Editors" if number is None else f"Test/Paper{number}/Action_Editors"),
        get_ae_recommendation_id=lambda: "Test/Action_Editors/-/Recommendation",
        should_show_conflict_details=lambda: False,
        should_skip_ac_recommendation=lambda: True)
    assignment = openreview.journal.assignment.Assignment(journal)
    with pytest.raises(RuntimeError, match="past selection"):
        assignment.setup_ae_matching("legacy", None)


def test_track_score_reconcile_rejects_duplicate_post_write_readback():
    class Journal:
        venue_id = "Test"
        def get_editors_in_chief_id(self): return "Test/Editors_In_Chief"
        def get_track_score_id(self): return "Test/Action_Editors/-/Track_Score"

    class Client:
        def __init__(self): self.posted = None
        def get_all_edges(self, **_kwargs):
            if self.posted is None: return []
            duplicate = SimpleNamespace(**self.posted.__dict__)
            return [self.posted, duplicate]
        def post_edge(self, edge): self.posted = edge

    with pytest.raises(ValueError, match="Duplicate Track Score readback"):
        batch_track_reconcile(Client(), Journal(), {("paper", "~AE1"): 1})


def test_batch_configuration_rejects_wrong_fixed_destination():
    class Journal:
        def get_action_editors_id(self): return "Test/Action_Editors"
        def get_ae_aggregate_score_id(self): return "Test/-/Aggregate_Score"
        def get_ae_conflict_id(self): return "Test/-/Conflict"
        def get_ae_assignment_id(self, proposed=False):
            return "Test/-/" + ("Proposed_Assignment" if proposed else "Assignment")

    values = {
        "title": "matching-next", "paper_invitation": "papers",
        "scores_specification": {}, "match_group": "Other/Reviewers",
        "aggregate_score_invitation": "Test/-/Aggregate_Score",
        "conflicts_invitation": "Test/-/Conflict",
        "assignment_invitation": "Test/-/Proposed_Assignment",
        "deployed_assignment_invitation": "Test/-/Assignment",
    }
    config = SimpleNamespace(content={key: {"value": value}
                                      for key, value in values.items()})
    with pytest.raises(ValueError, match="configuration differs"):
        validate_batch_configuration(Journal(), config, "matching-next", "papers", {})


@pytest.mark.parametrize("status", [None, "Error", "Running", "Complete"])
def test_batch_configuration_requires_initialized_status(status):
    class Journal:
        def get_action_editors_id(self): return "Test/Action_Editors"
        def get_ae_aggregate_score_id(self): return "Test/-/Aggregate_Score"
        def get_ae_conflict_id(self): return "Test/-/Conflict"
        def get_ae_assignment_id(self, proposed=False):
            return "Test/-/" + ("Proposed_Assignment" if proposed else "Assignment")
    values = {
        "title": "matching-next", "paper_invitation": "papers",
        "scores_specification": {}, "match_group": "Test/Action_Editors",
        "aggregate_score_invitation": "Test/-/Aggregate_Score",
        "conflicts_invitation": "Test/-/Conflict",
        "assignment_invitation": "Test/-/Proposed_Assignment",
        "deployed_assignment_invitation": "Test/-/Assignment",
    }
    if status is not None:
        values["status"] = status
    config = SimpleNamespace(content={key: {"value": value}
                                      for key, value in values.items()})
    with pytest.raises(ValueError, match="configuration differs"):
        validate_batch_configuration(Journal(), config, "matching-next", "papers", {})


def test_combined_setup_creates_track_registry_before_invitations():
    source = openreview.journal.Journal.setup.__code__
    names = source.co_names
    assert names.index("post_group") < names.index("set_invitations")


def test_batch_activation_uses_current_venue_state_for_queued_callbacks():
    journal = SimpleNamespace(
        venue_id="Test", settings={"ae_batch_preparation_enabled": True,
                                   "tracks": [REGULAR, OSS]})
    enabled_client = SimpleNamespace(get_group=lambda _id: SimpleNamespace(
        content={"ae_batch_preparation_enabled": {"value": True}}))
    disabled_client = SimpleNamespace(get_group=lambda _id: SimpleNamespace(
        content={"ae_batch_preparation_enabled": {"value": False}}))
    assert batch_is_enabled(enabled_client, journal) is True
    assert batch_is_enabled(disabled_client, journal) is False


def test_batch_uses_native_track_invitation_ids():
    journal = Journal(SimpleNamespace(), 'Test', 'secret', 'editors@example.org',
                      'Test Journal', 'TJ')
    assert journal.get_tracks_id() == 'Test/Tracks'
    assert journal.get_regular_ineligible_id() == \
        'Test/Action_Editors/-/Regular_Ineligible'
    assert journal.get_track_eligibility_id() == \
        'Test/Action_Editors/-/Track_Eligible'
    assert journal.get_track_score_id() == 'Test/Action_Editors/-/Track_Score'


@pytest.mark.parametrize("request_form_id", [None, "Test/Request"])
def test_captured_batch_callback_observes_later_disable(monkeypatch, request_form_id):
    class Owner:
        venue_id, secret_key, contact_info = "Test", "secret", "editors@example.org"
        full_name, short_name, website, submission_name = \
            "Test Journal", "TJ", "https://example.org", "Submission"
        settings = {"ae_batch_preparation_enabled": True, "tracks": [REGULAR, OSS]}
        def __init__(self): self.request_form_id = request_form_id
        def get_editors_in_chief_id(self): return "Test/Editors_In_Chief"
        def get_prepare_ae_batch_id(self): return "Test/-/Prepare_Action_Editor_Batch"

    runtime = SimpleNamespace(
        venue_id="Test", settings=dict(Owner.settings),
        has_managed_tracks=lambda: True,
        get_meta_invitation_id=lambda: "Test/-/Edit")
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.journal = Owner()
    saved = []
    builder.save_invitation = saved.append
    builder.set_ae_batch_invitation()
    process = execute_callback(saved[0].process)
    monkeypatch.setattr(openreview.journal, "Journal", lambda *_args, **_kwargs: runtime)
    monkeypatch.setattr(openreview.journal.JournalRequest, "get_journal",
        staticmethod(lambda *_args, **_kwargs: runtime))

    class Client:
        def __init__(self, enabled): self.enabled, self.writes = enabled, []
        def get_group(self, group_id):
            assert group_id == "Test"
            return SimpleNamespace(content={"ae_batch_preparation_enabled": {
                "value": self.enabled}})
        def get_note(self, _note_id):
            status = "Prepared" if self.enabled else "Pending"
            return SimpleNamespace(id="request", content={"status": {"value": status}})
        def post_note_edit(self, **kwargs): self.writes.append(kwargs)

    disabled = Client(False)
    with pytest.raises(ValueError, match="disabled"):
        process(disabled, SimpleNamespace(note=SimpleNamespace(id="request")), None)
    assert disabled.writes[-1]["note"].content["status"] == {"value": "Failed"}
    class StatusFailure(Client):
        def post_note_edit(self, **_kwargs):
            raise RuntimeError("status persistence failed")
    with pytest.raises(ValueError, match="disabled") as caught:
        process(StatusFailure(False),
                SimpleNamespace(note=SimpleNamespace(id="request")), None)
    assert isinstance(caught.value.__cause__, RuntimeError)
    enabled = Client(True)
    process(enabled, SimpleNamespace(note=SimpleNamespace(id="request")), None)
    assert enabled.writes == []


@pytest.mark.parametrize("tracks, expected", [
    ([], True), ([REGULAR], True), (None, False), (False, False),
    ("Regular", False), ({"id": "Regular"}, False),
])
def test_batch_activation_matches_managed_tracks_type_contract(tracks, expected):
    client = SimpleNamespace(get_group=lambda _id: SimpleNamespace(
        content={"ae_batch_preparation_enabled": {"value": True}}))
    journal = SimpleNamespace(venue_id="Test", settings={
        "tracks": tracks, "ae_batch_preparation_enabled": True})
    assert batch_is_enabled(client, journal) is expected


@pytest.mark.parametrize("include_eligible", [True, False])
def test_recommendation_mismatch_fails_before_preparation_writes(include_eligible):
    request = SimpleNamespace(id="request", content={
        "status": {"value": "Pending"}, "batch_label": {"value": "next"}})
    papers = [SimpleNamespace(id="blocked", number=1, ddate=None, content={
                  "venueid": {"value": "Test/Assigning_AE"}})]
    if include_eligible:
        papers.append(SimpleNamespace(id="eligible", number=2, ddate=None, content={
            "venueid": {"value": "Test/Submitted"}}))
    writes = []
    client = SimpleNamespace(
        get_note=lambda _id: request,
        get_group=lambda group_id: SimpleNamespace(
            content={"ae_batch_preparation_enabled": {"value": True}}
            if group_id == "Test" else {}, members=[]),
        get_all_notes=lambda invitation=None, **_kwargs: (
            [] if invitation == "Test/-/Assignment_Configuration" else papers),
        get_all_edges=lambda invitation=None, head=None, **_kwargs: (
            [SimpleNamespace(ddate=None)] * 3
            if invitation == "Test/Action_Editors/-/Recommendation" and head == "eligible" else []),
        post_note_edit=lambda **kwargs: writes.append(kwargs),
    )
    journal = SimpleNamespace(
        venue_id="Test", short_name="TJ", submitted_venue_id="Test/Submitted",
        assigning_AE_venue_id="Test/Assigning_AE",
        settings={"tracks": [], "ae_batch_preparation_enabled": True},
        should_skip_ac_recommendation=lambda: False,
        get_meta_invitation_id=lambda: "Test/-/Edit",
        get_ae_assignment_configuration_id=lambda: "Test/-/Assignment_Configuration",
        get_author_submission_id=lambda: "Test/-/Submission",
        get_ae_assignment_id=lambda: "Test/Action_Editors/-/Assignment",
        get_action_editors_id=lambda number=None: "Test" + (
            f"/Paper{number}" if number else "") + "/Action_Editors",
        get_ae_recommendation_id=lambda: "Test/Action_Editors/-/Recommendation",
    )
    with pytest.raises(ValueError, match="ineligible papers: blocked"):
        prepare_ae_batch(client, journal, request)
    assert writes[-1]["note"].content["status"] == {"value": "Failed"}
    assert len(writes) == 1


@pytest.mark.parametrize("request_form_id", [None, "Test/Request"])
def test_regular_only_batch_callback_reaches_request_state(monkeypatch, request_form_id):
    client = SimpleNamespace(
        get_group=lambda _id: SimpleNamespace(
            content={"ae_batch_preparation_enabled": {"value": True}}),
        get_note=lambda _id: SimpleNamespace(content={"status": {"value": "Prepared"}}))
    journal = Journal(client, "Test", "secret", "editors@example.org", "Test", "TJ",
        settings={"tracks": [], "ae_batch_preparation_enabled": True})
    assert journal.has_managed_tracks()
    journal.request_form_id = request_form_id
    saved = []
    journal.invitation_builder.save_invitation = saved.append
    journal.invitation_builder.set_ae_batch_invitation()
    if request_form_id:
        monkeypatch.setattr(openreview.journal.JournalRequest, "get_journal",
            staticmethod(lambda *_args: journal))
    process = execute_callback(saved[0].process)
    assert process(client, SimpleNamespace(note=SimpleNamespace(id="request")), None) is None


def test_preparation_materializes_binary_track_score_with_coefficient_two():
    class BatchJournal:
        venue_id, short_name = "Test", "TJ"
        submitted_venue_id, assigning_AE_venue_id = "Test/Submitted", "Test/Assigning_AE"
        settings = {"tracks": [], "ae_batch_preparation_enabled": True,
                    "skip_ac_recommendation": True}
        def should_skip_ac_recommendation(self): return True
        def get_meta_invitation_id(self): return "Test/-/Edit"
        def get_editors_in_chief_id(self): return "Test/Editors_In_Chief"
        def get_action_editors_id(self, number=None):
            return "Test" + (f"/Paper{number}" if number else "") + "/Action_Editors"
        def get_ae_recommendation_id(self): return "Test/Action_Editors/-/Recommendation"
        def get_tracks_id(self): return "Test/Tracks"
        def get_regular_ineligible_id(self): return "Test/Action_Editors/-/Regular_Ineligible"
        def get_track_eligibility_id(self): return "Test/Action_Editors/-/Track_Eligible"
        def get_track_score_id(self): return "Test/Action_Editors/-/Track_Score"
        def get_ae_assignment_id(self, proposed=False):
            return "Test/Action_Editors/-/" + ("Proposed_Assignment" if proposed else "Assignment")
        def get_ae_assignment_configuration_id(self): return "Test/-/Assignment_Configuration"
        def get_author_submission_id(self): return "Test/-/Submission"
        def get_ae_affinity_score_id(self): return "Test/Action_Editors/-/Affinity_Score"
        def get_ae_resubmission_score_id(self): return "Test/Action_Editors/-/Resubmission_Score"
        def get_ae_aggregate_score_id(self): return "Test/Action_Editors/-/Aggregate_Score"
        def get_ae_conflict_id(self): return "Test/Action_Editors/-/Conflict"
        def setup_ae_matching(self, label):
            client.config = SimpleNamespace(id="config", ddate=None, content={
                "title": {"value": "matching-" + label},
                "status": {"value": "Initialized"},
                "paper_invitation": {"value": "Test/-/Submission&content.venueid=Test/Assigning_AE"},
                "scores_specification": {"value": {
                    self.get_ae_affinity_score_id(): {"weight": 1, "default": 0},
                    self.get_ae_recommendation_id(): {"weight": 0.1, "default": 0},
                    self.get_ae_resubmission_score_id(): {"weight": 10, "default": 0},
                }},
                "match_group": {"value": self.get_action_editors_id()},
                "aggregate_score_invitation": {"value": self.get_ae_aggregate_score_id()},
                "conflicts_invitation": {"value": self.get_ae_conflict_id()},
                "assignment_invitation": {"value": self.get_ae_assignment_id(proposed=True)},
                "deployed_assignment_invitation": {"value": self.get_ae_assignment_id()},
            })

    class BatchClient:
        def __init__(self):
            self.request = SimpleNamespace(id="request", content={
                "status": {"value": "Pending"}, "batch_label": {"value": "next"}})
            self.paper = SimpleNamespace(id="paper", number=1, ddate=None, content={
                "venueid": {"value": "Test/Submitted"},
                "track_id": {"value": "Regular"}})
            self.config = None
            self.track_edges = []
        def get_group(self, group_id):
            if group_id == "Test":
                return SimpleNamespace(content={"ae_batch_preparation_enabled": {"value": True}})
            if group_id == "Test/Tracks":
                return SimpleNamespace(content={"tracks": {"value": [REGULAR]}})
            if group_id == "Test/Action_Editors":
                return SimpleNamespace(members=["~AE1"])
            return SimpleNamespace(members=[])
        def get_note(self, note_id):
            if note_id in ("config", "old-config"):
                return self.config
            return {"request": self.request, "paper": self.paper}[note_id]
        def get_all_notes(self, invitation=None, content=None, **_kwargs):
            if invitation == "Test/-/Assignment_Configuration":
                return [self.config] if self.config else []
            if content:
                return [self.paper] if self.paper.content["venueid"]["value"] == content["venueid"] else []
            return [self.paper]
        def get_all_edges(self, invitation=None, head=None, **_kwargs):
            if invitation == "Test/Action_Editors/-/Track_Score":
                return [edge for edge in self.track_edges if edge.head == head]
            return []
        def post_edge(self, edge):
            edge.id = edge.id or "track"
            self.track_edges = [edge]
            return edge
        def post_note_edit(self, note=None, **_kwargs):
            target = self.get_note(note.id)
            for key, value in (note.content or {}).items():
                target.content[key] = value

    client = BatchClient()
    journal = BatchJournal()
    prepare_ae_batch(client, journal, client.request)
    scores = client.config.content["scores_specification"]["value"]
    assert scores["Test/Action_Editors/-/Track_Score"] == {"weight": 2, "default": 0}
    assert client.track_edges[0].weight == 1
    assert client.request.content["status"] == {"value": "Prepared"}

    removed = BatchClient()
    removed.paper.content["venueid"] = {"value": "Test/Assigning_AE"}
    client = removed
    prepare_ae_batch(removed, journal, removed.request)
    assert removed.request.content["status"] == {"value": "Prepared"}

    class AssignedClient(BatchClient):
        def get_group(self, group_id):
            if group_id == "Test/Paper1/Action_Editors":
                return SimpleNamespace(members=["~AE1"])
            return super().get_group(group_id)
        def get_all_edges(self, invitation=None, head=None, **kwargs):
            if invitation == "Test/Action_Editors/-/Assignment":
                return [SimpleNamespace(
                    head="paper", tail="~AE1", ddate=None)]
            return super().get_all_edges(invitation=invitation, head=head, **kwargs)

    replaced = AssignedClient()
    replaced.paper.content["venueid"] = {"value": "Test/Assigning_AE"}
    client = replaced
    with pytest.raises(ValueError, match="ineligible papers: paper"):
        prepare_ae_batch(replaced, journal, replaced.request)
    assert replaced.request.content["status"] == {"value": "Failed"}

    class MixedAssignedClient(BatchClient):
        def __init__(self):
            super().__init__()
            self.assigned = SimpleNamespace(id="assigned", number=2, ddate=None, content={
                "venueid": {"value": "Test/Assigning_AE"},
                "track_id": {"value": "Regular"}})
        def get_group(self, group_id):
            if group_id == "Test/Paper2/Action_Editors":
                return SimpleNamespace(members=["~AE1"])
            return super().get_group(group_id)
        def get_all_notes(self, invitation=None, content=None, **kwargs):
            if invitation == "Test/-/Submission":
                papers = [self.paper, self.assigned]
                return [paper for paper in papers if not content or
                        paper.content["venueid"]["value"] == content["venueid"]]
            return super().get_all_notes(invitation=invitation, content=content, **kwargs)
        def get_all_edges(self, invitation=None, head=None, **kwargs):
            if invitation == "Test/Action_Editors/-/Assignment":
                return [SimpleNamespace(head="assigned", tail="~AE1", ddate=None)]
            return super().get_all_edges(invitation=invitation, head=head, **kwargs)

    mixed = MixedAssignedClient()
    client = mixed
    with pytest.raises(ValueError, match="ineligible papers: assigned"):
        prepare_ae_batch(mixed, journal, mixed.request)
    assert mixed.request.content["status"] == {"value": "Failed"}
    assert mixed.paper.content["venueid"] == {"value": "Test/Submitted"}
    assert mixed.assigned.content["venueid"] == {"value": "Test/Assigning_AE"}
    assert mixed.track_edges == []
    assert mixed.config is None

    inconsistent = BatchClient()
    inconsistent.paper.content["venueid"] = {"value": "Test/Assigning_AE"}
    original_edges = inconsistent.get_all_edges
    inconsistent.get_all_edges = lambda invitation=None, **kwargs: (
        [SimpleNamespace(head="paper", tail="~AE1", ddate=None)]
        if invitation == "Test/Action_Editors/-/Assignment"
        else original_edges(invitation=invitation, **kwargs))
    client = inconsistent
    with pytest.raises(ValueError, match="assignment state is inconsistent"):
        prepare_ae_batch(inconsistent, journal, inconsistent.request)
    assert inconsistent.request.content["status"] == {"value": "Failed"}

    duplicate = AssignedClient()
    duplicate.paper.content["venueid"] = {"value": "Test/Assigning_AE"}
    assigned_edges = duplicate.get_all_edges
    duplicate.get_all_edges = lambda invitation=None, **kwargs: (
        assigned_edges(invitation=invitation, **kwargs) * 2
        if invitation == "Test/Action_Editors/-/Assignment"
        else assigned_edges(invitation=invitation, **kwargs))
    client = duplicate
    with pytest.raises(ValueError, match="assignment state is inconsistent"):
        prepare_ae_batch(duplicate, journal, duplicate.request)

    unresolved = BatchClient()
    unresolved.config = SimpleNamespace(id="old-config", ddate=None, content={
        "title": {"value": "matching-old"}, "status": {"value": "Running"}})
    unresolved.paper.content["venueid"] = {"value": "Test/Assigning_AE"}
    client = unresolved
    with pytest.raises(ValueError, match="Resolve the existing native AE configuration"):
        prepare_ae_batch(unresolved, journal, unresolved.request)
    assert unresolved.request.content["status"] == {"value": "Failed"}
    assert "mark it Cancelled before retrying" in \
        unresolved.request.content["result"]["value"]

    cancelled = BatchClient()
    cancelled.config = SimpleNamespace(id="old-config", ddate=None, content={
        "title": {"value": "matching-old"}, "status": {"value": "No Solution"}})
    cancelled.post_note_edit(
        invitation="Test/-/Assignment_Configuration", signatures=["Test"],
        note=openreview.api.Note(id="old-config", content={
            "status": {"value": "Cancelled"}}))
    assert cancelled.config.content["status"] == {"value": "Cancelled"}
    client = cancelled
    prepare_ae_batch(cancelled, journal, cancelled.request)
    assert cancelled.request.content["status"] == {"value": "Prepared"}

    deployed = BatchClient()
    deployed.config = SimpleNamespace(id="old-config", ddate=None, content={
        "title": {"value": "matching-old"}, "status": {"value": "Deployed"}})
    client = deployed
    prepare_ae_batch(deployed, journal, deployed.request)
    assert deployed.request.content["status"] == {"value": "Prepared"}

    bad_client = BatchClient()
    client = bad_client
    bad_journal = BatchJournal()
    initialized_setup = bad_journal.setup_ae_matching
    def setup_with_invalid_status(label):
        initialized_setup(label)
        bad_client.config.content["status"] = {"value": "Error"}
    bad_journal.setup_ae_matching = setup_with_invalid_status
    with pytest.raises(ValueError, match="configuration differs"):
        prepare_ae_batch(bad_client, bad_journal, bad_client.request)
    assert "Test/Action_Editors/-/Track_Score" not in \
        bad_client.config.content["scores_specification"]["value"]
    assert bad_client.request.content["status"] == {"value": "Blocked"}

    class TimeoutAfterScoreClient(BatchClient):
        def post_edge(self, edge):
            super().post_edge(edge)
            raise TimeoutError("track score write outcome is uncertain")

    partial = TimeoutAfterScoreClient()
    with pytest.raises(TimeoutError, match="outcome is uncertain"):
        prepare_ae_batch(partial, journal, partial.request)
    assert len(partial.track_edges) == 1
    assert partial.request.content["status"] == {"value": "Blocked"}
    prepare_ae_batch(partial, journal, partial.request)
    assert len(partial.track_edges) == 1

    class FailedStatusClient(TimeoutAfterScoreClient):
        def post_note_edit(self, note=None, **kwargs):
            if (note.content or {}).get("status") == {"value": "Blocked"}:
                raise RuntimeError("status persistence failed")
            return super().post_note_edit(note=note, **kwargs)

    failed_status = FailedStatusClient()
    with pytest.raises(TimeoutError, match="outcome is uncertain") as caught:
        prepare_ae_batch(failed_status, journal, failed_status.request)
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert failed_status.request.content["status"] == {"value": "Running"}
    assert len(failed_status.track_edges) == 1
