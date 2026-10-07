from types import SimpleNamespace
from pathlib import Path
import datetime
import json
import subprocess

import openreview
import pytest

from openreview.journal import Journal
from openreview.journal.invitation import InvitationBuilder
from openreview.journal.reader_policy import action_editor_reader
from openreview.journal.process import ae_assignment_process


def test_eic_console_scopes_authored_papers():
    webfield = Path(__file__).parents[1] / 'openreview/journal/webfield/editorsInChiefWebfield.js'
    script = r'''
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(process.argv[1], 'utf8').replace(/main\(\);\s*$/, '');
const context = {args: {perf: '0'}};
vm.createContext(context);
vm.runInContext(source, context);
const papers = ['~Eic1', 'eic@example.org', '~EicAlias1', '~Other1'].map((id, i) => ({
  id: 'paper' + i, content: {authorids: {value: [id]}}
}));
const user = {id: '~Eic1', profile: {id: '~Eic1', emails: ['eic@example.org'], names: [{username: '~EicAlias1'}]}};
const ordinary = context.editableSubmissions(papers, user).map(p => p.id);
context.HIDE_AUTHORED_PAPERS = true;
const scoped = context.editableSubmissions(papers, user).map(p => p.id);
const peer = context.editableSubmissions(papers, {id: '~Peer1'}).map(p => p.id);
console.log(JSON.stringify({ordinary, scoped, peer}));
'''
    result = subprocess.run(['node', '-e', script, str(webfield)],
                            check=True, capture_output=True, text=True, timeout=10)
    assert json.loads(result.stdout) == {
        'ordinary': ['paper0', 'paper1', 'paper2', 'paper3'],
        'scoped': ['paper3'],
        'peer': ['paper0', 'paper1', 'paper2', 'paper3'],
    }


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


def test_missing_defaults_to_paper_scope_and_all_is_explicit():
    expected = ["Test", "Test/Action_Editors", "Test/Paper7/Reviewers",
                "Test/Paper7/Authors"]
    assert make_journal({"submission_public": False}).get_under_review_submission_readers(7) == ["Test", "Test/Paper7/Action_Editors", "Test/Paper7/Reviewers", "Test/Paper7/Authors"]
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


def test_direct_callback_preserves_all_settings_and_default():
    legacy = {"submission_public": False, "release_submission_after_acceptance": False}
    off_source = rendered_callback(legacy)
    assert direct_journal(off_source).settings == legacy

    enabled = {**legacy, "action_editor_paper_visibility": "assigned_only"}
    source = rendered_callback(enabled)
    reconstructed = direct_journal(source)
    assert reconstructed.settings == enabled
    assert reconstructed.get_under_review_submission_readers(7)[1] == "Test/Paper7/Action_Editors"


@pytest.mark.parametrize('skip_recommendation', [False, True])
@pytest.mark.parametrize('visibility', [None, 'assigned_only', 'all'])
def test_direct_callback_preserves_explicit_workflow_settings(skip_recommendation, visibility):
    settings = {
        'action_editor_paper_visibility': 'assigned_only',
        'submission_public': False,
        'author_anonymity': False,
        'skip_official_recommendation': skip_recommendation,
        'skip_ac_recommendation': True,
        'review_period': 3,
        'website_urls': {'instructions': 'https://example.org/instructions'},
    }
    if visibility is None:
        settings.pop('action_editor_paper_visibility')
    else:
        settings['action_editor_paper_visibility'] = visibility
    reconstructed = direct_journal(rendered_callback(settings))
    assert reconstructed.settings == settings
    assert reconstructed.should_skip_official_recommendation() is skip_recommendation
    assert reconstructed.should_skip_ac_recommendation()
    assert not reconstructed.are_authors_anonymous()


def test_direct_opt_in_callback_keeps_defaults_for_omitted_workflow_settings():
    reconstructed = direct_journal(rendered_callback({
        'action_editor_paper_visibility': 'assigned_only',
    }))
    assert not reconstructed.should_skip_official_recommendation()
    assert not reconstructed.should_skip_ac_recommendation()
    assert reconstructed.are_authors_anonymous()










@pytest.mark.parametrize("assigned_only,anonymous,expected", [
    (True, False, ["Test/Unrelated"]),
    (True, True, None),
    (False, False, ["Test/Paper7/Authors", "Test/Unrelated"]),
])
def test_review_approval_reveals_only_feature_owned_ae_exclusion(
        monkeypatch, assigned_only, anonymous, expected):
    settings = {"AE_anonymity": anonymous, "action_editor_paper_visibility": "all"}
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


def test_action_editor_reader_default_is_paper_scoped():
    assert action_editor_reader(make_journal(), 7) == "Test/Paper7/Action_Editors"


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


def test_explicit_all_assignment_identity_remains_unchanged():
    journal = make_journal({"action_editor_paper_visibility": "all"})
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
                                  if assigned_only else {"action_editor_paper_visibility": "all"})

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

    events = []

    def remove_member(_group_id, member):
        paper_group.members.remove(member)
        events.append(('remove', member))

    client = SimpleNamespace(
        get_edge=lambda *_args: SimpleNamespace(ddate=1),
        get_note=lambda _id: SimpleNamespace(id="paper", number=7, content=note_content),
        get_group=get_group,
        post_message=lambda *_args, **_kwargs: None,
        remove_members_from_group=remove_member,
        flush_members_cache=lambda member: events.append(('flush', member)),
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

    assert events == [('remove', '~Assigned1'), ('flush', '~Assigned1')]
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
        flush_members_cache=lambda _member: None,
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
    settings = {"action_editor_paper_visibility": "assigned_only"} if assigned_only else {"action_editor_paper_visibility": "all"}
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
        "Test/Editors_In_Chief", "Test/Paper7/Action_Editors",
        "Test/Paper7/Reviewers", "Test/Paper7/Authors",
    ]


def test_direct_callback_preserves_anonymous_ae_setting():
    source = rendered_callback({
        'action_editor_paper_visibility': 'assigned_only',
        'AE_anonymity': True,
    })
    assert direct_journal(source).is_action_editor_anonymous()




def test_submission_invitation_already_scopes_private_author_fields(monkeypatch):
    journal = make_journal({'action_editor_paper_visibility': 'assigned_only',
                            'author_anonymity': True})
    builder = InvitationBuilder(journal)
    saved = []
    builder.save_invitation = lambda invitation: saved.append(invitation)
    monkeypatch.setattr(openreview.tools, 'get_invitation', lambda *_args: None)
    builder.set_submission_invitation()
    invitation = next(item for item in saved if item.id == 'Test/-/Submission')
    for name in ('authors', 'authorids'):
        readers = invitation.edit['note']['content'][name]['readers']
        assert 'Test/Action_Editors' not in readers
        assert 'Test/Paper${4/number}/Action_Editors' in readers




def test_edge_update_wait_ignores_old_success_and_waits_for_new_process(monkeypatch):
    import test_action_editor_visibility_api as api_tests
    calls = []

    class Client:
        def get_process_logs(self, id, min_sdate=None):
            calls.append((id, min_sdate))
            logs = [
                {'sdate': 100, 'status': 'ok', 'processIndex': 0},
                {'sdate': 200, 'status': 'running' if len(calls) == 1 else 'ok',
                 'processIndex': 0},
            ]
            return [log for log in logs if min_sdate is None or log['sdate'] >= min_sdate]

    monkeypatch.setattr(api_tests.time, 'sleep', lambda _seconds: None)
    api_tests.await_edge_update(Client(), 'same-edge-id', 150)
    assert calls == [('same-edge-id', 150), ('same-edge-id', 150)]


def test_edge_update_wait_reports_new_process_failure():
    from test_action_editor_visibility_api import await_edge_update
    client = SimpleNamespace(get_process_logs=lambda **_kwargs: [
        {'status': 'error', 'log': 'removal failed', 'processIndex': 0}])
    with pytest.raises(AssertionError, match='removal failed'):
        await_edge_update(client, 'same-edge-id', 150)


@pytest.mark.parametrize('details,edge_not_found', [
    ('Edge not found', True),
    ({'name': 'NotFoundError', 'status': 404}, False),
    ({'name': 'ForbiddenError', 'status': 403}, False),
])
def test_denial_helper_accepts_supported_access_errors(details, edge_not_found):
    from test_action_editor_visibility_api import assert_denied

    def denied():
        raise openreview.OpenReviewException(details)

    assert_denied(denied, edge_not_found=edge_not_found)


@pytest.mark.parametrize('details,edge_not_found', [
    ('Edge not found', False),
    ('Connection failed', True),
    ({'name': 'ValidationError', 'status': 400}, True),
])
def test_denial_helper_rejects_unrelated_errors(details, edge_not_found):
    from test_action_editor_visibility_api import assert_denied

    def unrelated_error():
        raise openreview.OpenReviewException(details)

    with pytest.raises(AssertionError):
        assert_denied(unrelated_error, edge_not_found=edge_not_found)


def test_denial_helper_rejects_successful_reads():
    from test_action_editor_visibility_api import assert_denied
    with pytest.raises(pytest.fail.Exception, match='DID NOT RAISE'):
        assert_denied(lambda: object(), edge_not_found=True)


@pytest.mark.parametrize('members', [[], ['Test/Paper7/Action_Editor_abc']])
def test_identity_check_accepts_only_anonymous_parent_members(members):
    from test_action_editor_visibility_api import assert_group_identity_hidden
    client = SimpleNamespace(get_group=lambda _id: SimpleNamespace(members=members))
    assert_group_identity_hidden(client, 'Test/Paper7/Action_Editors',
                                 anonymous_member_prefix='Test/Paper7/Action_Editor_')


@pytest.mark.parametrize('group_id,prefix', [
    ('Test/Paper7/Action_Editors', 'Test/Paper7/Action_Editor_'),
    ('Test/Paper7/Action_Editor_abc', None),
])
def test_identity_check_rejects_real_member_identities(group_id, prefix):
    from test_action_editor_visibility_api import assert_group_identity_hidden
    client = SimpleNamespace(get_group=lambda _id: SimpleNamespace(members=['~Assigned1']))
    with pytest.raises(AssertionError):
        assert_group_identity_hidden(client, group_id, anonymous_member_prefix=prefix)


def test_identity_check_does_not_swallow_validation_errors():
    from test_action_editor_visibility_api import assert_group_identity_hidden
    def invalid(_id):
        raise openreview.OpenReviewException({'name': 'ValidationError', 'status': 400})
    with pytest.raises(AssertionError):
        assert_group_identity_hidden(SimpleNamespace(get_group=invalid), 'group')




@pytest.mark.parametrize('failure_stage', ['metadata', 'cache'])
@pytest.mark.parametrize('visibility', [None, 'assigned_only', 'all'])
def test_removal_retry_finishes_cleanup_without_duplicate_mail(monkeypatch, failure_stage, visibility):
    journal = make_journal({} if visibility is None else {
        'action_editor_paper_visibility': visibility})
    paper = SimpleNamespace(id='paper', number=7, content={
        'title': {'value': 'Title'},
        'venueid': {'value': journal.assigned_AE_venue_id},
        'assigned_action_editor': {'value': '~Assigned1'}})
    group = SimpleNamespace(id=journal.get_action_editors_id(7), members=['~Assigned1'])
    events = []
    failures = [failure_stage]

    class Client:
        def get_edge(self, *_args): return SimpleNamespace(ddate=1)
        def get_note(self, _id): return paper
        def get_group(self, group_id):
            return group if group_id == group.id else SimpleNamespace(content={
                'unassignment_email_template_script': {'value': 'unassigned'}})
        def post_message(self, *_args, **_kwargs): events.append('mail')
        def remove_members_from_group(self, _id, member):
            group.members.remove(member)
            events.append('remove')
        def post_note_edit(self, **kwargs):
            if failures == ['metadata']:
                failures.clear()
                raise RuntimeError('metadata failed after persisted removal')
            for key, value in kwargs['note'].content.items():
                if value.get('delete'): paper.content.pop(key, None)
                else: paper.content[key] = value
            events.append('metadata')
        def flush_members_cache(self, _id):
            if failures == ['cache']:
                failures.clear()
                raise RuntimeError('profile cache failed after persisted removal')
            events.append('cache')

    monkeypatch.setattr(ae_assignment_process, 'openreview', openreview, raising=False)
    monkeypatch.setattr(openreview.journal, 'Journal', lambda: journal)
    client = Client()
    edge = SimpleNamespace(id='edge', head=paper.id, tail='~Assigned1', ddate=1)
    with pytest.raises(RuntimeError, match='failed after persisted removal'):
        ae_assignment_process.process_update(client, edge, None, None)
    assert group.members == []
    ae_assignment_process.process_update(client, edge, None, None)
    assert paper.content['venueid']['value'] == journal.assigning_AE_venue_id
    assert 'assigned_action_editor' not in paper.content
    assert events.count('mail') == events.count('remove') == events.count('metadata') == 1
    assert events[-1] == 'cache'


@pytest.mark.parametrize('visibility', [None, 'assigned_only', 'all'])
def test_removal_retry_preserves_replacement_editor(monkeypatch, visibility):
    journal = make_journal({} if visibility is None else {
        'action_editor_paper_visibility': visibility})
    paper = SimpleNamespace(id='paper', number=7, content={
        'title': {'value': 'Title'},
        'venueid': {'value': journal.assigned_AE_venue_id},
        'assigned_action_editor': {'value': '~Replacement1'}})
    group = SimpleNamespace(id=journal.get_action_editors_id(7), members=['~Replacement1'])
    events = []
    client = SimpleNamespace(
        get_edge=lambda *_args: SimpleNamespace(ddate=1),
        get_note=lambda _id: paper,
        get_group=lambda _id: group,
        post_message=lambda *_args, **_kwargs: events.append('mail'),
        remove_members_from_group=lambda *_args: events.append('remove'),
        post_note_edit=lambda **_kwargs: events.append('metadata'),
        flush_members_cache=lambda member: events.append(('cache', member)),
    )
    monkeypatch.setattr(ae_assignment_process, 'openreview', openreview, raising=False)
    monkeypatch.setattr(openreview.journal, 'Journal', lambda: journal)
    edge = SimpleNamespace(id='edge', head=paper.id, tail='~Assigned1', ddate=1)
    ae_assignment_process.process_update(client, edge, None, None)
    assert events == [('cache', '~Assigned1')]
    assert group.members == ['~Replacement1']
    assert paper.content['assigned_action_editor']['value'] == '~Replacement1'
    assert paper.content['venueid']['value'] == journal.assigned_AE_venue_id


@pytest.mark.parametrize('visibility', [None, 'assigned_only', 'all'])
def test_optional_ae_resolution_retains_strict_assignment_contract(visibility):
    journal = make_journal({} if visibility is None else {
        'action_editor_paper_visibility': visibility})
    members = []
    journal.client = SimpleNamespace(get_group=lambda _id: SimpleNamespace(members=members))
    paper = SimpleNamespace(number=7, content={})
    assert journal.get_assigned_action_editor(paper, allow_unassigned=True) is None
    with pytest.raises(KeyError if visibility == 'all' else openreview.OpenReviewException):
        journal.get_assigned_action_editor(paper)
    members.append('~Current1')
    if visibility == 'all':
        paper.content['assigned_action_editor'] = {'value': '~Current1,current@example.org'}
    assert journal.get_assigned_action_editor(paper, allow_unassigned=True) == '~Current1'
    assert journal.get_assigned_action_editor(paper) == '~Current1'
    if visibility != 'all':
        members.append('~Second1')
        with pytest.raises(openreview.OpenReviewException, match='exactly one'):
            journal.get_assigned_action_editor(paper, allow_unassigned=True)
        members[:] = ['not-a-profile']
        with pytest.raises(openreview.OpenReviewException, match='exactly one'):
            journal.get_assigned_action_editor(paper, allow_unassigned=True)
        def failed(_id): raise openreview.OpenReviewException('lookup failed')
        journal.client.get_group = failed
        with pytest.raises(openreview.OpenReviewException, match='lookup failed'):
            journal.get_assigned_action_editor(paper, allow_unassigned=True)


@pytest.mark.parametrize('visibility', [None, 'assigned_only', 'all'])
@pytest.mark.parametrize('anonymous', [False, True])
@pytest.mark.parametrize('assigned', [False, True])
@pytest.mark.parametrize('reminder,is_reviewer,ack', [
    ('author_reminder_process.py', False, False),
    ('author_edge_reminder_process.py', False, False),
    ('reviewer_reminder_process.py', True, False),
    ('reviewer_reminder_process.py', True, True),
])
def test_reminders_resolve_current_group_ae_and_preserve_reply_privacy(
        monkeypatch, visibility, anonymous, assigned, reminder, is_reviewer, ack):
    settings = {'AE_anonymity': anonymous}
    if visibility is not None:
        settings['action_editor_paper_visibility'] = visibility
    journal = make_journal(settings)
    paper = SimpleNamespace(id='paper', number=7, content={'title': {'value': 'Title'}})
    # The current group supplies identity, including after reassignment; no stale
    # stored identity is consulted in scoped mode.
    if visibility == 'all' and assigned:
        paper.content['assigned_action_editor'] = {'value': '~Replacement1'}
    journal.client = SimpleNamespace(get_group=lambda _id: SimpleNamespace(
        members=['~Replacement1'] if assigned else []))
    journal.get_late_invitees = lambda _id: ['recipient']
    messages = []
    client = SimpleNamespace(get_note=lambda _id: paper, get_edges_count=lambda **_kwargs: 0,
                             post_message=lambda **kwargs: messages.append(kwargs))
    monkeypatch.setattr(openreview.journal, 'Journal', lambda: journal)
    invitation = SimpleNamespace(
        id='Test/Paper7/-/' + ('Assignment/Acknowledgement' if ack else 'Review'),
        edit={'note': {'forum': 'paper'}, 'head': {'param': {'const': 'paper'}}},
        duedate=0, pretty_id=lambda: 'Task')
    source = (Path(__file__).parents[1] / 'openreview/journal/process' / reminder).read_text()
    namespace = {'openreview': openreview, 'datetime': datetime, 'date_index': 0, 'days_late_map': {}}
    exec(compile(source, reminder, 'exec'), namespace)
    namespace['process'](client, invitation)
    assert len(messages) == 1
    expected = '~Replacement1' if assigned and (is_reviewer or not anonymous) else journal.contact_info
    assert messages[0]['replyTo'] == expected
    assert messages[0]['signature'] == 'Test'
    assert 'Title' in messages[0]['message']


@pytest.mark.parametrize('statuses', [('ok', 'ok'), ('ok', 'error')])
def test_queue_wait_checks_every_requested_process_log(monkeypatch, helpers, statuses):
    logs = [{'status': status, 'log': 'second process failed'} for status in statuses]
    client = SimpleNamespace(get_process_logs=lambda **_kwargs: logs)
    monkeypatch.setattr(helpers, 'get_user', lambda _user: client)
    if 'error' in statuses:
        with pytest.raises(AssertionError, match='second process failed'):
            helpers.await_queue_edit(client, edit_id='edge', count=2)
    else:
        helpers.await_queue_edit(client, edit_id='edge', count=2)
