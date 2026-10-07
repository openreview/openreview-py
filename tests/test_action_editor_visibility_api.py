"""Journal visibility tests executed by the real API in the upstream CI harness."""
import datetime
import time
from types import SimpleNamespace
from uuid import uuid4

import openreview
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from openreview.journal import JournalRequest


def assert_denied(operation, *, edge_not_found=False):
    with pytest.raises(openreview.OpenReviewException) as caught:
        operation()
    details = caught.value.args[0]
    # get_edge reports a filtered-out edge with this exact client-side error.
    if edge_not_found and details == 'Edge not found':
        return
    assert isinstance(details, dict), details
    assert (details.get('status') in (403, 404) or
            details.get('name') in ('ForbiddenError', 'NotFoundError')), details


def assert_group_identity_hidden(client, group_id, *, anonymous_member_prefix=None):
    """Allow safe group metadata, but never expose member identities to ordinary authors."""
    try:
        group = client.get_group(group_id)
    except openreview.OpenReviewException as error:
        def denied():
            raise error
        assert_denied(denied)
        return
    if anonymous_member_prefix is None:
        assert not group.members, group.members
    else:
        assert all(member.startswith(anonymous_member_prefix)
                   for member in (group.members or [])), group.members


def await_edge_update(client, edge_id, min_start, timeout=60):
    """Wait for this update, excluding successful logs from earlier edge versions."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        logs = client.get_process_logs(id=edge_id, min_sdate=min_start)
        logs = [log for log in logs if log.get('processIndex', 0) == 0]
        assert not any(log['status'] == 'error' for log in logs), logs
        if logs and all(log['status'] == 'ok' for log in logs):
            return
        time.sleep(0.25)
    raise TimeoutError(f'No completed new process for edge {edge_id} after {min_start}')


class TestJournalActionEditorVisibilityAPI:
    @pytest.fixture(scope='class')
    def actors(self, helpers, openreview_client):
        suffix = uuid4().hex[:10]
        name_suffix = suffix.translate(str.maketrans('0123456789abcdef', 'abcdefghijklmnop'))
        actors = {}
        for role in ('eic', 'eic_author', 'author', 'ae', 'other_ae', 'reviewer'):
            # Distinct institutions avoid introducing conflicts between test actors.
            email = f'visibility-{suffix}@{role.replace("_", "")}-{suffix}.org'
            client = helpers.create_user(email, 'Visibility', f'{role.title().replace("_", "")}{name_suffix}')
            profile = openreview.tools.get_profile(openreview_client, email)
            names = profile.content['names']
            preferred_name = next((name for name in names if name.get('preferred')), names[0])
            actors[role] = SimpleNamespace(client=client, id=profile.id, email=email,
                                          name=preferred_name['fullname'])
        return actors

    @pytest.fixture
    def create_journal(self, actors, helpers, openreview_client, journal_request):
        def create(visibility='assigned_only', public=False, anonymous=True, direct=False):
            venue = 'VisibilityAPI' + uuid4().hex[:12]
            settings = {
                'submission_public': public,
                'release_submission_after_acceptance': False,
                'author_anonymity': True,
                'AE_anonymity': anonymous,
                'assignment_delay': 0,
                'skip_official_recommendation': True,
                'skip_ac_recommendation': True,
            }
            if visibility is not None:
                settings['action_editor_paper_visibility'] = visibility
            request = openreview_client.post_note_edit(
                invitation='openreview.net/Support/-/Journal_Request',
                signatures=['openreview.net/Support'],
                note=openreview.api.Note(content={
                    'official_venue_name': {'value': 'Visibility API Test Journal'},
                    'abbreviated_venue_name': {'value': venue},
                    'contact_info': {'value': actors['eic'].email},
                    'support_role': {'value': actors['eic'].id},
                    'editors': {'value': [actors['eic'].id, actors['eic_author'].id]},
                    'website': {'value': 'example.org'},
                    'settings': {'value': settings},
                }))
            helpers.await_queue_edit(openreview_client, request['id'])
            deployment = openreview_client.post_note_edit(
                invitation='openreview.net/Support/-/Journal_Request_Deployment',
                signatures=['openreview.net/Support'],
                note=openreview.api.Note(id=request['note']['id'],
                                         content={'venue_id': {'value': venue}}))
            helpers.await_queue_edit(openreview_client, deployment['id'])
            backend = helpers.get_user(actors['eic'].email)
            backend.impersonate(venue)
            journal = JournalRequest.get_journal(backend, request['note']['id'])
            if direct:
                # Direct invitation setup includes Super_User-signed invitations.
                # Use the administrator only for setup; actors keep their own clients.
                journal = JournalRequest.get_journal(openreview_client, request['note']['id'])
                # No request_form_id exercises settings serialization in callbacks.
                journal.request_form_id = None
                journal.invitation_builder.set_invitations(assignment_delay=0)
            openreview_client.add_members_to_group(
                journal.get_action_editors_id(), [actors['ae'].id, actors['other_ae'].id])
            openreview_client.add_members_to_group(journal.get_reviewers_id(), actors['reviewer'].id)
            return journal
        return create

    def submit(self, journal, actors, helpers, super_client, author_role='author'):
        author = actors[author_role]
        edit = author.client.post_note_edit(
            invitation=journal.get_author_submission_id(), signatures=[author.id],
            note=openreview.api.Note(content={
                'title': {'value': 'Visibility test submission'},
                'abstract': {'value': 'A controlled API integration test.'},
                'authors': {'value': ['Visibility Test Author']},
                'authorids': {'value': [author.id]},
                'pdf': {'value': '/pdf/' + 'p' * 40 + '.pdf'},
                'competing_interests': {'value': 'None'},
                'human_subjects_reporting': {'value': 'Not applicable'},
            }))
        helpers.await_queue_edit(super_client, edit['id'])
        note = super_client.get_note(edit['note']['id'])
        assert super_client.get_group(journal.get_action_editors_id(note.number)).members == []
        return note

    def assign(self, journal, note, actors, helpers, super_client, role='ae'):
        edge = actors['eic'].client.post_edge(openreview.api.Edge(
            invitation=journal.get_ae_assignment_id(),
            signatures=[journal.get_editors_in_chief_id()],
            head=note.id, tail=actors[role].id, weight=1))
        helpers.await_queue_edit(super_client, edge.id)
        assert actors[role].id in super_client.get_group(
            journal.get_action_editors_id(note.number)).members
        return edge

    def approve(self, journal, note, actors, helpers, super_client):
        ae = actors['ae']
        groups = ae.client.get_groups(
            prefix=journal.get_action_editors_id(note.number, anon=True), signatory=ae.id)
        assert len(groups) == 1
        edit = ae.client.post_note_edit(
            invitation=journal.get_review_approval_id(note.number),
            signatures=[groups[0].id],
            note=openreview.api.Note(content={
                'under_review': {'value': 'Appropriate for Review'}}))
        helpers.await_queue_edit(super_client, edit['id'])
        transitions = super_client.get_note_edits(
            note_id=note.id, invitation=journal.get_under_review_id())
        assert len(transitions) == 1
        helpers.await_queue_edit(super_client, transitions[0].id)
        assert super_client.get_note(note.id).content['venueid']['value'] == journal.under_review_venue_id
        return groups[0].id

    @pytest.mark.parametrize('visibility,public,anonymous,direct', [
        pytest.param('assigned_only', False, True, False, id='private-anonymous'),
        pytest.param('assigned_only', False, False, False, id='private-named'),
        pytest.param('assigned_only', True, True, False, id='public-private-author-fields'),
        pytest.param('assigned_only', False, True, True, id='direct-journal-anonymous'),
        pytest.param(None, False, False, False, id='default'),
        pytest.param('all', False, False, False, id='explicit-all'),
    ])
    def test_assignment_review_and_replacement(
            self, create_journal, actors, helpers, openreview_client,
            visibility, public, anonymous, direct):
        journal = create_journal(visibility, public, anonymous, direct)
        note = self.submit(journal, actors, helpers, openreview_client)
        other = actors['other_ae'].client
        assert_denied(lambda: other.get_note(note.id))
        edge = self.assign(journal, note, actors, helpers, openreview_client)
        ae = actors['ae'].client
        assert ae.get_note(note.id).content['authorids']['value'] == [actors['author'].id]
        assert actors['eic'].client.get_note(note.id).id == note.id
        if visibility != 'all':
            assert 'assigned_action_editor' not in openreview_client.get_note(note.id).content
        else:
            assert openreview_client.get_note(note.id).content['assigned_action_editor']['value'] == actors['ae'].id
        # Unrelated AEs cannot submit Review Approval even when the manuscript is public.
        assert_denied(lambda: other.post_note_edit(
            invitation=journal.get_review_approval_id(note.number),
            signatures=[actors['other_ae'].id],
            note=openreview.api.Note(content={'under_review': {'value': 'Appropriate for Review'}})))
        signature = self.approve(journal, note, actors, helpers, openreview_client)
        reviewer_edge = actors['ae'].client.post_edge(openreview.api.Edge(
            invitation=journal.get_reviewer_assignment_id(), signatures=[signature],
            head=note.id, tail=actors['reviewer'].id, weight=1))
        helpers.await_queue_edit(openreview_client, reviewer_edge.id)
        assert actors['reviewer'].id in openreview_client.get_group(
            journal.get_reviewers_id(note.number)).members
        assert actors['reviewer'].client.get_note(note.id).id == note.id
        author_note = actors['author'].client.get_note(note.id)
        paper_group = journal.get_action_editors_id(note.number)
        if visibility != 'all':
            if public:
                # Public manuscript access must not expose anonymous author fields.
                assert 'authorids' not in other.get_note(note.id).content
            else:
                assert_denied(lambda: other.get_note(note.id))
            if not public:
                assert other.get_note_edits(note_id=note.id) == []
            assert 'assigned_action_editor' not in author_note.content
            if anonymous:
                assert_denied(lambda: actors['author'].client.get_group(paper_group))
                for group in openreview_client.get_groups(
                        prefix=journal.get_action_editors_id(note.number, anon=True)):
                    assert_group_identity_hidden(actors['author'].client, group.id)
            else:
                assert actors['ae'].id in actors['author'].client.get_group(paper_group).members
        else:
            assert other.get_note(note.id).id == note.id
            assert journal.get_action_editors_id() in openreview_client.get_note(note.id).readers
        min_start = openreview.tools.datetime_millis(datetime.datetime.now())
        edge.ddate = min_start
        deleted = actors['eic'].client.post_edge(edge)
        await_edge_update(openreview_client, deleted.id, min_start)
        assert actors['ae'].id not in openreview_client.get_group(paper_group).members
        if visibility != 'all' and not public:
            assert_denied(lambda: ae.get_note(note.id))
            assert ae.get_note_edits(note_id=note.id) == []
        self.assign(journal, note, actors, helpers, openreview_client, role='other_ae')
        assert other.get_note(note.id).content['authorids']['value'] == [actors['author'].id]
        if visibility != 'all' and not public:
            assert_denied(lambda: ae.get_note(note.id))

    @pytest.mark.parametrize('visibility', ['assigned_only', None, 'all'], ids=['assigned-only', 'default', 'all'])
    def test_eic_author_console_visibility(
            self, create_journal, actors, helpers, openreview_client,
            selenium, request_page, visibility):
        journal = create_journal(visibility=visibility)
        note = self.submit(journal, actors, helpers, openreview_client, author_role='eic_author')
        edge = self.assign(journal, note, actors, helpers, openreview_client)
        control = self.submit(journal, actors, helpers, openreview_client)
        self.assign(journal, control, actors, helpers, openreview_client)
        author = actors['eic_author'].client
        assert author.get_note(note.id).id == note.id
        paper_group = journal.get_action_editors_id(note.number)
        anon_prefix = journal.get_action_editors_id(note.number, anon=True)
        anonymous_groups = openreview_client.get_groups(prefix=anon_prefix)
        assert len(anonymous_groups) == 1
        for group in anonymous_groups:
            # Venue administrator access is intentional; console masking does
            # not promise protection against deliberate API lookups.
            assert actors['ae'].id in author.get_group(group.id).members
        console = f'http://localhost:3030/group?id={journal.get_editors_in_chief_id()}'
        own_link = f'#all-submissions a[href*="forum?id={note.id}"]'
        control_link = f'#all-submissions a[href*="forum?id={control.id}"]'
        for approved in (False, True):
            if approved:
                self.approve(journal, note, actors, helpers, openreview_client)
            for role in ('eic_author', 'eic'):
                request_page(selenium, console, actors[role].client,
                             wait_for_element='group-container')
                WebDriverWait(selenium, 60).until(
                    lambda browser: browser.find_elements(By.CSS_SELECTOR, control_link))
                rows = selenium.find_elements(By.CSS_SELECTOR, own_link)
                hidden = visibility != 'all' and role == 'eic_author'
                assert bool(rows) is not hidden, (role, visibility, approved)
                if rows:
                    row = rows[0].find_element(By.XPATH, 'ancestor::tr')
                    # The native AE progress cell shows a name and Copy Email
                    # identity; the legacy submission field adds a profile link.
                    progress = row.find_element(By.CSS_SELECTOR, '.areachair-progress')
                    assert actors['ae'].name in progress.get_attribute('textContent'), (
                        role, visibility, approved)
                    assert progress.find_elements(By.CSS_SELECTOR,
                        f'a.copy-email[data-user-id="{actors["ae"].id}"]'), (
                            role, visibility, approved)
                if visibility != 'all':
                    scoped_links = selenium.find_elements(By.CSS_SELECTOR,
                        'a.journal-scoped-assignments')
                    assert len(scoped_links) == 3
                    assert all('maxColumns=2' in link.get_attribute('href')
                               for link in scoped_links)
                assignment_link = selenium.find_element(By.XPATH,
                    '//a[text()="Modify Action Editor Assignments"]')
                assignment_link.click()
                assignment_control = f'a[href*="forum?id={control.id}"]'
                WebDriverWait(selenium, 60).until(
                    lambda browser: browser.find_elements(By.CSS_SELECTOR, assignment_control))
                assignment_own = selenium.find_elements(By.CSS_SELECTOR,
                    f'a[href*="forum?id={note.id}"]')
                assert bool(assignment_own) is not hidden, (role, visibility, approved)
                if visibility != 'all':
                    paper = selenium.find_element(By.CSS_SELECTOR, assignment_control)
                    paper_entry = paper.find_element(By.XPATH, 'ancestor::li[contains(@class,"entry-note")]')
                    selenium.execute_script('arguments[0].click()', paper_entry)
                    ae_link = WebDriverWait(selenium, 60).until(
                        lambda browser: browser.find_element(By.CSS_SELECTOR,
                            f'a[href*="profile?id={actors["ae"].id}"]'))
                    ae_entry = ae_link.find_element(By.XPATH,
                        'ancestor::li[contains(@class,"entry-reviewer")]')
                    assert not ae_entry.find_elements(By.CSS_SELECTOR, 'a.show-assignments')
                    selenium.execute_script('arguments[0].click()', ae_entry)
                    assert len(selenium.find_elements(By.CSS_SELECTOR,
                        '.explore-interface > .column:not(.column-spacer)')) == 2
                    assert bool(selenium.find_elements(By.CSS_SELECTOR,
                        f'a[href*="forum?id={note.id}"]')) is not hidden
            assert author.get_note(note.id).id == note.id
        if visibility != 'all':
            assert 'assigned_action_editor' not in author.get_note(note.id).content
            assert_denied(lambda: author.get_edge(edge.id), edge_not_found=True)
        assert actors['eic'].client.get_group(paper_group).members == [actors['ae'].id]
        assert actors['eic'].client.get_edge(edge.id).tail == actors['ae'].id
