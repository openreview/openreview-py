"""Resubmission admission and continuity through real Journal API callbacks."""
import datetime
import time
from types import SimpleNamespace
from uuid import uuid4

import openreview
import pytest
from openreview.journal import JournalRequest


PERMISSION = 'The authors may consider submitting a major revision at a later time.'


def denied(operation, role, *, write=False):
    with pytest.raises(openreview.OpenReviewException) as caught:
        operation()
    detail = caught.value.args[0]
    names = {'ForbiddenError', 'NotFoundError'}
    if write:
        names.update(('NotInviteeError', 'NotSignatoryError'))
    def permission(error):
        return isinstance(error, dict) and (error.get('status') in (403, 404) or
            error.get('name') in names or
            any(permission(child) for child in error.get('errors', [])))
    assert permission(detail), (role, detail)



@pytest.mark.parametrize('detail,write,accepted', [
    ({'status': 403}, False, True),
    ({'status': 404}, False, True),
    ({'status': 400, 'name': 'NotInviteeError'}, True, True),
    ({'status': 400, 'name': 'NotSignatoryError'}, True, True),
    ({'status': 400, 'errors': [{'status': 400, 'name': 'NotSignatoryError'}]}, True, True),
    ({'status': 400, 'name': 'NotSignatoryError'}, False, False),
    ({'status': 400, 'name': 'ValidationError'}, True, False),
    ({'status': 500, 'name': 'InternalError'}, True, False),
])
def test_permission_denial_requires_explicit_permission_error(detail, write, accepted):
    def operation():
        raise openreview.OpenReviewException(detail)
    if accepted:
        denied(operation, 'test role', write=write)
    else:
        with pytest.raises(AssertionError):
            denied(operation, 'test role', write=write)


def invalid(operation, *words):
    with pytest.raises(openreview.OpenReviewException) as caught:
        operation()
    detail = caught.value.args[0]
    assert isinstance(detail, dict) and detail.get('status') == 400, detail
    assert any(word.lower() in str(detail).lower() for word in words), detail


def wait_new_process(admin, edit_id, since):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        logs = [log for log in admin.get_process_logs(id=edit_id, min_sdate=since)
                if log.get('processIndex', 0) == 0]
        assert not any(log['status'] == 'error' for log in logs), logs
        if logs and all(log['status'] == 'ok' for log in logs):
            return
        time.sleep(0.25)
    raise TimeoutError(f'No new successful process for {edit_id} after {since}')


class TestJournalResubmissionAPI:
    @pytest.fixture(scope='class')
    def actors(self, helpers, openreview_client):
        suffix = uuid4().hex[:10]
        letters = suffix.translate(str.maketrans('0123456789abcdef', 'abcdefghijklmnop'))
        actors = {}
        for role in ('eic', 'author', 'ae', 'otherae', 'thirdae', 'reviewer', 'outsider'):
            email = f'continuity-{suffix}@{role}-{suffix}.org'
            client = helpers.create_user(email, 'Continuity', role.title() + letters)
            profile = openreview.tools.get_profile(openreview_client, email)
            actors[role] = SimpleNamespace(client=client, email=email, id=profile.id)
        # Native Journal submissions require tilde IDs, including profile aliases.
        author = actors['author']
        profile = author.client.get_profile(author.id)
        profile.content['names'].append({
            'first': 'Continuity', 'middle': 'Alternate', 'last': 'Author' + letters})
        author.client.post_profile(profile)
        profile = openreview_client.get_profile(author.id)
        author.alias = profile.content['names'][-1]['username']
        assert author.alias != author.id
        assert openreview_client.get_profile(author.alias).id == author.id
        assert author.email in openreview_client.get_group(author.alias).members
        return actors

    @pytest.fixture
    def create_journal(self, actors, helpers, openreview_client, journal_request):
        def create(enabled=True, mode='score', direct=False):
            venue = 'ContinuityAPI' + uuid4().hex[:12]
            settings = {'submission_public': False, 'release_submission_after_acceptance': False,
                'author_anonymity': True, 'AE_anonymity': True, 'assignment_delay': 0,
                'skip_official_recommendation': True, 'skip_ac_recommendation': True,
                'archived_action_editors': True, 'archived_reviewers': True,
                'submission_additional_fields': None}
            if enabled is not None:
                settings['resubmission_continuity_enabled'] = enabled
            if enabled:
                settings['resubmission_continuity'] = mode
            request = openreview_client.post_note_edit(
                invitation='openreview.net/Support/-/Journal_Request',
                signatures=['openreview.net/Support'], note=openreview.api.Note(content={
                    'official_venue_name': {'value': 'Continuity API Test Journal'},
                    'abbreviated_venue_name': {'value': venue},
                    'contact_info': {'value': actors['eic'].email},
                    'support_role': {'value': actors['eic'].id},
                    'editors': {'value': [actors['eic'].id]},
                    'website': {'value': 'example.org'}, 'settings': {'value': settings}}))
            helpers.await_queue_edit(openreview_client, request['id'])
            deployment = openreview_client.post_note_edit(
                invitation='openreview.net/Support/-/Journal_Request_Deployment',
                signatures=['openreview.net/Support'], note=openreview.api.Note(
                    id=request['note']['id'], content={'venue_id': {'value': venue}}))
            helpers.await_queue_edit(openreview_client, deployment['id'])
            backend = helpers.get_user(actors['eic'].email)
            backend.impersonate(venue)
            journal = JournalRequest.get_journal(backend, request['note']['id'])
            if direct:
                journal = JournalRequest.get_journal(openreview_client, request['note']['id'])
                journal.request_form_id = None
                journal.invitation_builder.set_invitations(assignment_delay=0)
            openreview_client.add_members_to_group(journal.get_action_editors_id(),
                [actors[role].id for role in ('ae', 'otherae', 'thirdae')])
            openreview_client.add_members_to_group(journal.get_reviewers_id(), actors['reviewer'].id)
            return journal
        return create

    def submit(self, journal, actors, helpers, admin, previous=None, role='author', authors=None):
        author = actors[role]
        content = {'title': {'value': 'Continuity test paper'}, 'abstract': {'value': 'API test'},
            'authors': {'value': ['Continuity Author'] * len(authors or [author.id])},
            'authorids': {'value': authors or [author.id]},
            'pdf': {'value': '/pdf/' + 'p' * 40 + '.pdf'},
            'competing_interests': {'value': 'None'},
            'human_subjects_reporting': {'value': 'Not applicable'}}
        if previous is not None:
            content[journal.get_resubmission_previous_submission_field()] = {'value': previous}
        edit = author.client.post_note_edit(invitation=journal.get_author_submission_id(),
            signatures=[author.id], note=openreview.api.Note(content=content))
        helpers.await_queue_edit(admin, edit['id'])
        return admin.get_note(edit['note']['id'])

    def assign(self, journal, note, actors, helpers, admin, role='ae'):
        edge = actors['eic'].client.post_edge(openreview.api.Edge(
            invitation=journal.get_ae_assignment_id(), signatures=[journal.get_editors_in_chief_id()],
            head=note.id, tail=actors[role].id, weight=1))
        helpers.await_queue_edit(admin, edge.id)
        assert actors[role].id in admin.get_group(journal.get_action_editors_id(note.number)).members
        return edge

    def approve_review(self, journal, note, actors, helpers, admin):
        groups = actors['ae'].client.get_groups(
            prefix=journal.get_action_editors_id(note.number, anon=True), signatory=actors['ae'].id)
        assert len(groups) == 1
        edit = actors['ae'].client.post_note_edit(invitation=journal.get_review_approval_id(note.number),
            signatures=[groups[0].id], note=openreview.api.Note(
                content={'under_review': {'value': 'Appropriate for Review'}}))
        helpers.await_queue_edit(admin, edit['id'])
        transitions = admin.get_note_edits(note_id=note.id, invitation=journal.get_under_review_id())
        assert len(transitions) == 1
        helpers.await_queue_edit(admin, transitions[0].id)
        assert admin.get_note(note.id).content['venueid']['value'] == journal.under_review_venue_id
        return groups[0].id, edit['note']['id']

    def predecessor(self, journal, actors, helpers, admin, *, permitted=True, released=True, reviewer=False):
        note = self.submit(journal, actors, helpers, admin)
        assignment = self.assign(journal, note, actors, helpers, admin)
        signature, review_approval_id = self.approve_review(journal, note, actors, helpers, admin)
        if reviewer:
            edge = actors['ae'].client.post_edge(openreview.api.Edge(
                invitation=journal.get_reviewer_assignment_id(), signatures=[signature],
                head=note.id, tail=actors['reviewer'].id, weight=1))
            helpers.await_queue_edit(admin, edge.id)
            assert actors['reviewer'].id in admin.get_group(journal.get_reviewers_id(note.number)).members
        # Minimal decision-ready fixture: enable the native Decision invitation.
        # No fake decision or rejection status is written; actual AE/EIC callbacks follow.
        journal.invitation_builder.set_note_decision_invitation(note,
            datetime.datetime.now() - datetime.timedelta(minutes=1), journal.get_due_date(days=7))
        content = {'claims_and_evidence': {'value': 'No'}, 'audience': {'value': 'Yes'},
            'recommendation': {'value': 'Reject'}, 'comment': {'value': 'Major revision required'}}
        if permitted:
            content['resubmission_of_major_revision'] = {'value': PERMISSION}
        decision = actors['ae'].client.post_note_edit(invitation=journal.get_ae_decision_id(note.number),
            signatures=[signature], note=openreview.api.Note(content=content))
        helpers.await_queue_edit(admin, decision['id'])
        assert admin.get_note(note.id).content['venueid']['value'] == journal.decision_pending_venue_id
        if released:
            approval = actors['eic'].client.post_note_edit(
                invitation=journal.get_decision_approval_id(note.number),
                signatures=[journal.get_editors_in_chief_id()], note=openreview.api.Note(
                    content={'approval': {'value': "I approve the AE's decision."}}))
            helpers.await_queue_edit(admin, approval['id'])
            rejected = admin.get_note_edits(note_id=note.id, invitation=journal.get_rejected_id())
            assert len(rejected) == 1
            helpers.await_queue_edit(admin, rejected[0].id)
            helpers.await_venue_processes(admin, journal.venue_id)
            assert admin.get_note(note.id).content['venueid']['value'] == journal.rejected_venue_id
            assert actors['author'].client.get_note(decision['note']['id']).content['recommendation']['value'] == 'Reject'
        return SimpleNamespace(note=admin.get_note(note.id), assignment=assignment,
            decision=admin.get_note(decision['note']['id']), review_approval_id=review_approval_id)

    def restrict_predecessor(self, journal, previous, admin):
        # Supported private fixture predates linking. This tests access via group
        # nesting, without importing PR1 or changing the journal's global policy.
        admin.post_note_edit(invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id], note=openreview.api.Note(id=previous.note.id,
                readers=[journal.venue_id, journal.get_action_editors_id(previous.note.number),
                    journal.get_reviewers_id(previous.note.number), journal.get_authors_id(previous.note.number)]))

    def revise(self, journal, note, actors, helpers, admin, *, role='author', previous=None):
        content = {key: {'value': note.content[key]['value']} for key in
            ('title', 'abstract', 'pdf', 'competing_interests', 'human_subjects_reporting')}
        content['title'] = {'value': 'Revised linked paper'}
        if previous is not None:
            content[journal.get_resubmission_previous_submission_field()] = {'value': previous}
        signature = journal.get_editors_in_chief_id() if role == 'eic' else journal.get_authors_id(note.number)
        edit = actors[role].client.post_note_edit(invitation=journal.get_revision_id(note.number),
            signatures=[signature], note=openreview.api.Note(id=note.id, content=content))
        helpers.await_queue_edit(admin, edit['id'])
        return admin.get_note(note.id)

    @pytest.mark.parametrize('enabled', [None, False], ids=['missing', 'false'])
    def test_default_preserves_unvalidated_link_and_ordinary_assignment(self, enabled,
            create_journal, actors, helpers, openreview_client):
        journal = create_journal(enabled=enabled)
        invitation = openreview_client.get_invitation(journal.get_author_submission_id())
        assert 'journal-resubmission-preprocess-owner-v2' not in (invitation.preprocess or '')
        url = 'https://openreview.net/forum?id=missing' + uuid4().hex
        note = self.submit(journal, actors, helpers, openreview_client, url)
        assert note.content[journal.get_resubmission_previous_submission_field()]['value'] == url
        assert openreview_client.get_group(journal.get_action_editors_id(note.number)).members == []
        self.assign(journal, note, actors, helpers, openreview_client)
        self.approve_review(journal, note, actors, helpers, openreview_client)
        # Ordinary native private Journal readership includes the AE roster.
        assert actors['otherae'].client.get_note(note.id).id == note.id
        assert 'authorids' not in actors['otherae'].client.get_note(note.id).content

    @pytest.mark.parametrize('direct', [False, True], ids=['request', 'direct'])
    @pytest.mark.parametrize('mode', ['score', 'immediate_previous_ae'])
    def test_admitted_link_revisions_and_private_predecessor_access(self, direct, mode,
            create_journal, actors, helpers, openreview_client):
        journal = create_journal(mode=mode, direct=direct)
        previous = self.predecessor(journal, actors, helpers, openreview_client, reviewer=True)
        self.restrict_predecessor(journal, previous, openreview_client)
        denied(lambda: actors['otherae'].client.get_note(previous.note.id), 'unassigned successor AE')
        url = 'https://dev.openreview.net/forum?id=' + previous.note.id + '&referrer=%5BHomepage%5D'
        # Alternate tilde author ID and copied DEV URL exercise actual API admission.
        note = self.submit(journal, actors, helpers, openreview_client, url, authors=[actors['author'].alias])
        field = journal.get_resubmission_previous_submission_field()
        assert note.content[field]['value'] == url
        current_group = journal.get_action_editors_id(note.number)
        if mode == 'immediate_previous_ae':
            edges = openreview_client.get_edges(invitation=journal.get_ae_assignment_id(), head=note.id)
            assert len(edges) == 1 and edges[0].tail == actors['ae'].id
            helpers.await_queue_edit(openreview_client, edges[0].id)
            assert openreview_client.get_note(note.id).content['venueid']['value'] == journal.assigned_AE_venue_id
        else:
            assert openreview_client.get_group(current_group).members == []
            assert openreview_client.get_edges(invitation=journal.get_ae_assignment_id(), head=note.id) == []
            self.assign(journal, note, actors, helpers, openreview_client, 'otherae')
        denied(lambda: actors['author'].client.post_edge(openreview.api.Edge(
            invitation=journal.get_ae_assignment_id(), signatures=[journal.get_editors_in_chief_id()],
            head=note.id, tail=actors['thirdae'].id, weight=1)), 'author assignment', write=True)
        assert openreview_client.get_edges(invitation=journal.get_ae_assignment_id(),
            head=note.id, tail=actors['thirdae'].id) == []
        assigned_role = 'ae' if mode == 'immediate_previous_ae' else 'otherae'
        assert current_group in openreview_client.get_group(
            journal.get_action_editors_id(previous.note.number)).members
        predecessor = actors[assigned_role].client.get_note(previous.note.id)
        assert predecessor.content['authorids']['value'] == [actors['author'].id]
        assert actors[assigned_role].client.get_note(previous.review_approval_id).id == previous.review_approval_id
        denied(lambda: actors['thirdae'].client.get_note(previous.note.id), 'unrelated AE')
        denied(lambda: actors['thirdae'].client.get_note(previous.review_approval_id), 'unrelated AE')
        assert actors['eic'].client.get_note(previous.note.id).id == previous.note.id
        assert openreview_client.get_edges(invitation=journal.get_reviewer_assignment_id(), head=note.id) == []
        assert openreview_client.get_group(journal.get_reviewers_id(note.number)).members == []
        denied(lambda: actors['reviewer'].client.get_note(note.id), 'prior reviewer')
        revised = self.revise(journal, note, actors, helpers, openreview_client)
        assert revised.content[field]['value'] == url
        invalid(lambda: self.revise(journal, revised, actors, helpers, openreview_client,
            previous='https://openreview.net/forum?id=' + previous.note.id), 'immutable')
        before = len(openreview_client.get_note_edits(note_id=note.id,
            invitation=journal.get_revision_id(note.number)))
        denied(lambda: self.revise(journal, revised, actors, helpers, openreview_client,
            role='outsider'), 'outsider', write=True)
        assert len(openreview_client.get_note_edits(note_id=note.id,
            invitation=journal.get_revision_id(note.number))) == before
        # Admission is once-only; a later predecessor decision change must not
        # retroactively prevent unrelated successor author or EIC revisions.
        openreview_client.post_note_edit(invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id], note=openreview.api.Note(id=previous.decision.id,
                content={'resubmission_of_major_revision': {'delete': True}}))
        assert self.revise(journal, revised, actors, helpers, openreview_client).content[field]['value'] == url
        assert self.revise(journal, revised, actors, helpers, openreview_client, role='eic').content[field]['value'] == url
        # Removal/replacement revokes inherited access via successor membership.
        edge = openreview_client.get_edges(invitation=journal.get_ae_assignment_id(), head=note.id)[0]
        since = openreview.tools.datetime_millis(datetime.datetime.now())
        edge.ddate = since
        removed = actors['eic'].client.post_edge(edge)
        wait_new_process(openreview_client, removed.id, since)
        assert actors[assigned_role].id not in openreview_client.get_group(current_group).members
        if assigned_role != 'ae':
            denied(lambda: actors[assigned_role].client.get_note(previous.note.id), 'removed successor AE')
        self.assign(journal, note, actors, helpers, openreview_client, 'thirdae')
        assert actors['thirdae'].client.get_note(previous.note.id).content['authorids']['value'] == [actors['author'].id]

    @pytest.mark.parametrize('case', ['foreign', 'unshared', 'nonshared-submitter', 'unreleased',
        'disallowed', 'missing', 'ambiguous', 'fragment', 'deleted', 'reply'])
    def test_invalid_predecessors_rejected_before_persistence(self, case,
            create_journal, actors, helpers, openreview_client):
        journal = create_journal()
        source = create_journal() if case == 'foreign' else journal
        previous = self.predecessor(source, actors, helpers, openreview_client,
            permitted=case != 'disallowed', released=case != 'unreleased')
        url = 'https://openreview.net/forum?id=' + previous.note.id
        role = 'outsider' if case in ('unshared', 'nonshared-submitter') else 'author'
        authors = [actors['outsider'].id, actors['author'].id] if case == 'nonshared-submitter' else None
        if case == 'missing':
            url = 'https://openreview.net/forum?id=missing' + uuid4().hex
        elif case == 'ambiguous':
            url += '&id=other'
        elif case == 'fragment':
            url += '#reply'
        elif case == 'deleted':
            openreview_client.post_note_edit(invitation=source.get_meta_invitation_id(),
                signatures=[source.venue_id], note=openreview.api.Note(id=previous.note.id,
                    ddate=openreview.tools.datetime_millis(datetime.datetime.now())))
        elif case == 'reply':
            url = 'https://openreview.net/forum?id=' + previous.decision.id
        before = {note.id for note in openreview_client.get_all_notes(invitation=journal.get_author_submission_id())}
        invalid(lambda: self.submit(journal, actors, helpers, openreview_client, url,
            role=role, authors=authors), 'invalid', 'previous', 'regex')
        assert {note.id for note in openreview_client.get_all_notes(
            invitation=journal.get_author_submission_id())} == before

    @pytest.mark.parametrize('mode', ['score', 'immediate_previous_ae'])
    def test_prior_ae_unavailability_exception_and_ordinary_guard(self, mode,
            create_journal, actors, helpers, openreview_client):
        journal = create_journal(mode=mode)
        previous = self.predecessor(journal, actors, helpers, openreview_client)
        for role in ('ae', 'otherae'):
            actors['eic'].client.post_edge(openreview.api.Edge(invitation=journal.get_ae_availability_id(),
                signatures=[journal.get_editors_in_chief_id()], head=journal.get_action_editors_id(),
                tail=actors[role].id, label='Unavailable'))
        note = self.submit(journal, actors, helpers, openreview_client,
            'https://openreview.net/forum?id=' + previous.note.id)
        if mode == 'score':
            invalid(lambda: self.assign(journal, note, actors, helpers, openreview_client, 'otherae'), 'unavailable')
            self.assign(journal, note, actors, helpers, openreview_client)
        else:
            edge = openreview_client.get_edges(invitation=journal.get_ae_assignment_id(), head=note.id)[0]
            helpers.await_queue_edit(openreview_client, edge.id)
            assert edge.tail == actors['ae'].id
        assert actors['ae'].id in openreview_client.get_group(journal.get_action_editors_id(note.number)).members
        assert openreview_client.get_edge(previous.assignment.id).tail == actors['ae'].id
        unlinked = self.submit(journal, actors, helpers, openreview_client)
        invalid(lambda: self.assign(journal, unlinked, actors, helpers, openreview_client, 'otherae'), 'unavailable')


    @pytest.mark.parametrize('mode', ['score', 'immediate_previous_ae'])
    @pytest.mark.parametrize('case', ['not-current', 'conflict', 'no-prior'])
    def test_fallback_and_current_assignment_guards(self, case, mode,
            create_journal, actors, helpers, openreview_client):
        journal = create_journal(mode=mode)
        previous = self.predecessor(journal, actors, helpers, openreview_client)
        authors = None
        if case == 'not-current':
            openreview_client.remove_members_from_group(journal.get_action_editors_id(), actors['ae'].id)
            assert actors['ae'].id not in openreview_client.get_group(journal.get_action_editors_id()).members
        elif case == 'conflict':
            authors = [actors['author'].id, actors['ae'].id]
        else:
            # Native archival/cleanup can leave no qualifying prior assignment.
            journal.client.delete_edges(invitation=journal.get_ae_assignment_id(), head=previous.note.id, soft_delete=True)
        note = self.submit(journal, actors, helpers, openreview_client,
            'https://openreview.net/forum?id=' + previous.note.id, authors=authors)
        assert openreview_client.get_edges(invitation=journal.get_ae_assignment_id(), head=note.id) == []
        assert openreview_client.get_group(journal.get_action_editors_id(note.number)).members == []
        assert note.content['venueid']['value'] == journal.submitted_venue_id
        if case != 'no-prior':
            invalid(lambda: self.assign(journal, note, actors, helpers, openreview_client), 'conflict', 'inGroup', 'member')
        self.assign(journal, note, actors, helpers, openreview_client, 'otherae')
        assert actors['otherae'].id in openreview_client.get_group(journal.get_action_editors_id(note.number)).members

    def test_archived_prior_score_and_native_matching_setup(self,
            create_journal, actors, helpers, openreview_client):
        journal = create_journal(mode='score')
        previous = self.predecessor(journal, actors, helpers, openreview_client)
        archived = actors['eic'].client.post_edge(openreview.api.Edge(
            invitation=journal.get_ae_assignment_id(archived=True),
            signatures=[journal.get_editors_in_chief_id()], head=previous.note.id,
            tail=actors['ae'].id, weight=1))
        journal.client.delete_edges(invitation=journal.get_ae_assignment_id(), head=previous.note.id, soft_delete=True)
        assert openreview_client.get_edge(archived.id).tail == actors['ae'].id
        note = self.submit(journal, actors, helpers, openreview_client,
            'https://openreview.net/forum?id=' + previous.note.id)
        assert openreview_client.get_edges(invitation=journal.get_ae_assignment_id(), head=note.id) == []
        journal.invitation_builder.set_ae_recommendation_invitation(note, journal.get_due_date(days=7))
        for role in ('ae', 'otherae', 'thirdae'):
            actors['author'].client.post_edge(openreview.api.Edge(
                invitation=journal.get_ae_recommendation_id(), signatures=[journal.get_authors_id(note.number)],
                head=note.id, tail=actors[role].id, weight=1))
        label = 'continuity' + uuid4().hex[:10]
        journal.setup_ae_matching(label)
        fresh = openreview_client.get_note(note.id)
        assert fresh.content['venueid']['value'] == journal.assigning_AE_venue_id
        scores = openreview_client.get_edges(invitation=journal.get_ae_resubmission_score_id(), head=note.id)
        assert len(scores) == 1 and scores[0].tail == actors['ae'].id and scores[0].weight == 1
        configs = openreview_client.get_notes(invitation=journal.get_ae_assignment_configuration_id(),
            content={'title': 'matching-' + label})
        assert len(configs) == 1 and configs[0].content['status']['value'] == 'Initialized'
        spec = configs[0].content['scores_specification']['value']
        assert spec[journal.get_ae_resubmission_score_id()] == {'weight': 10, 'default': 0}
        assert openreview_client.get_edges(invitation=journal.get_ae_assignment_id(), head=note.id) == []
        self.assign(journal, fresh, actors, helpers, openreview_client)
        assert actors['ae'].client.get_note(previous.note.id).id == previous.note.id

    def test_immediate_mode_uses_archived_assignment(self,
            create_journal, actors, helpers, openreview_client):
        journal = create_journal(mode='immediate_previous_ae')
        previous = self.predecessor(journal, actors, helpers, openreview_client)
        archived = actors['eic'].client.post_edge(openreview.api.Edge(
            invitation=journal.get_ae_assignment_id(archived=True),
            signatures=[journal.get_editors_in_chief_id()], head=previous.note.id,
            tail=actors['ae'].id, weight=1))
        journal.client.delete_edges(invitation=journal.get_ae_assignment_id(),
            head=previous.note.id, soft_delete=True)
        assert openreview_client.get_edge(archived.id).tail == actors['ae'].id
        note = self.submit(journal, actors, helpers, openreview_client,
            'https://openreview.net/forum?id=' + previous.note.id)
        edges = openreview_client.get_edges(invitation=journal.get_ae_assignment_id(), head=note.id)
        assert len(edges) == 1 and edges[0].tail == actors['ae'].id
        helpers.await_queue_edit(openreview_client, edges[0].id)
        assert openreview_client.get_note(note.id).content['venueid']['value'] == journal.assigned_AE_venue_id
