"""Managed Journal tracks exercised through real server invitations."""
import datetime
import time
from types import SimpleNamespace
from uuid import uuid4

import openreview
import pytest

from openreview.journal import JournalRequest
from openreview.journal.tracks import REGULAR


OSS = {'id': 'OSS', 'name': 'Open Source', 'open': True}
AWARD = {'id': 'Award', 'name': 'Award Papers', 'open': True}


def denied(operation, role, *, edge_not_found=False):
    with pytest.raises(openreview.OpenReviewException) as caught:
        operation()
    detail = caught.value.args[0]
    if edge_not_found and detail == 'Edge not found':
        return
    assert isinstance(detail, dict), (role, detail)
    assert detail.get('status') in (403, 404) or detail.get('name') in (
        'ForbiddenError', 'NotFoundError'), (role, detail)


def invalid(operation, *expected):
    with pytest.raises(openreview.OpenReviewException) as caught:
        operation()
    detail = caught.value.args[0]
    assert isinstance(detail, dict), detail
    assert detail.get('status') == 400, detail
    assert any(word.lower() in str(detail).lower() for word in expected), detail


def wait_new_process(client, edit_id, since):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        logs = [log for log in client.get_process_logs(id=edit_id, min_sdate=since)
                if log.get('processIndex', 0) == 0]
        assert not any(log['status'] == 'error' for log in logs), logs
        if logs and all(log['status'] == 'ok' for log in logs):
            return
        time.sleep(0.25)
    raise TimeoutError(f'No new successful process for {edit_id} after {since}')


class TestJournalTracksAPI:
    @pytest.fixture(scope='class')
    def actors(self, helpers, openreview_client):
        suffix = uuid4().hex[:10]
        letters = suffix.translate(str.maketrans('0123456789abcdef', 'abcdefghijklmnop'))
        result = {}
        for role in ('eic', 'author', 'ae', 'otherae', 'outsider'):
            email = f'tracks-{suffix}@{role}-{suffix}.org'
            client = helpers.create_user(email, 'Tracks', role.title() + letters)
            result[role] = SimpleNamespace(client=client, email=email,
                id=openreview.tools.get_profile(openreview_client, email).id)
        return result

    @pytest.fixture
    def create_journal(self, actors, helpers, openreview_client, journal_request):
        def create(tracks=(OSS, AWARD), direct=False):
            venue = 'TracksAPI' + uuid4().hex[:12]
            settings = {'submission_public': False, 'author_anonymity': True,
                        'AE_anonymity': True, 'assignment_delay': 0,
                        'skip_official_recommendation': True,
                        'skip_ac_recommendation': True}
            if tracks is not None:
                settings['tracks'] = list(tracks) if isinstance(tracks, (list, tuple)) else tracks
            request = openreview_client.post_note_edit(
                invitation='openreview.net/Support/-/Journal_Request',
                signatures=['openreview.net/Support'], note=openreview.api.Note(content={
                    'official_venue_name': {'value': 'Tracks API Test Journal'},
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
                [actors['ae'].id, actors['otherae'].id])
            return journal
        return create

    def submit(self, journal, actors, helpers, admin, track='OSS'):
        content = {'title': {'value': 'Track paper'}, 'abstract': {'value': 'API test'},
            'authors': {'value': ['Tracks Author']}, 'authorids': {'value': [actors['author'].id]},
            'pdf': {'value': '/pdf/' + 'p' * 40 + '.pdf'},
            'competing_interests': {'value': 'None'},
            'human_subjects_reporting': {'value': 'Not applicable'}}
        if track is not None:
            content['track_id'] = {'value': track}
        edit = actors['author'].client.post_note_edit(invitation=journal.get_author_submission_id(),
            signatures=[actors['author'].id], note=openreview.api.Note(content=content))
        helpers.await_queue_edit(admin, edit['id'])
        return admin.get_note(edit['note']['id'])

    def manage(self, journal, records, actors, admin):
        since = openreview.tools.datetime_millis(datetime.datetime.now())
        edit = actors['eic'].client.post_group_edit(invitation=journal.get_manage_tracks_id(),
            signatures=[journal.get_editors_in_chief_id()], group=openreview.api.Group(
                id=journal.get_tracks_id(), content={'tracks': {'value': records}}))
        wait_new_process(admin, edit['id'], since)
        assert admin.get_group(journal.get_tracks_id()).content['tracks']['value'] == records
        return edit

    def eligibility(self, journal, actors, managed=True, role='ae', label='OSS', **changes):
        values = dict(invitation=journal.get_track_eligibility_id() if managed else
            journal.get_regular_ineligible_id(), signatures=[journal.get_editors_in_chief_id()],
            readers=[journal.venue_id, journal.get_editors_in_chief_id()],
            writers=[journal.get_editors_in_chief_id()], head=journal.get_action_editors_id(),
            tail=actors[role].id, label=label if managed else 'Regular Ineligible', weight=1)
        values.update(changes)
        return actors['eic'].client.post_edge(openreview.api.Edge(**values))

    @pytest.mark.parametrize('tracks', [None, False, []], ids=['missing', 'false', 'regular-only'])
    def test_default_and_regular_only(self, tracks, create_journal, actors, helpers, openreview_client):
        journal = create_journal(tracks)
        invitation = openreview_client.get_invitation(journal.get_author_submission_id())
        assert ('track_id' in invitation.edit['note']['content']) == (tracks == [])
        if tracks == []:
            assert journal.get_tracks() == [REGULAR]
            note = self.submit(journal, actors, helpers, openreview_client, 'Regular')
            assert note.content['track_id']['value'] == 'Regular'
            default = self.submit(journal, actors, helpers, openreview_client, None)
            assert default.content['track_id']['value'] == 'Regular'
        else:
            note = self.submit(journal, actors, helpers, openreview_client, None)
            assert 'track_id' not in note.content
            for invitation_id in (journal.get_manage_tracks_id(), journal.get_track_eligibility_id()):
                assert openreview.tools.get_invitation(openreview_client, invitation_id) is None

    @pytest.mark.parametrize('direct', [False, True], ids=['journal-request', 'direct-settings'])
    def test_track_lifecycle_and_immutable_selection(self, direct, create_journal, actors, helpers, openreview_client):
        journal = create_journal(direct=direct)
        note = self.submit(journal, actors, helpers, openreview_client)
        renamed = dict(OSS, name='Software', open=False)
        records = [REGULAR, AWARD, renamed, {'id': 'New', 'name': 'New Track', 'open': True}]
        self.manage(journal, records, actors, openreview_client)
        fresh = openreview_client.get_note(note.id)
        assert fresh.content['track_id']['value'] == 'OSS'
        choices = openreview_client.get_invitation(journal.get_author_submission_id()).edit['note']['content']['track_id']['value']['param']['enum']
        assert choices == [{'value': r['id'], 'description': r['name']} for r in records if r['open']]
        for track in ('OSS', 'Unknown'):
            invalid(lambda: self.submit(journal, actors, helpers, openreview_client, track), 'track', 'enum')
        invalid(lambda: self.manage(journal, [REGULAR, AWARD], actors, openreview_client), 'Referenced tracks')
        revision = journal.get_revision_id(note.number)
        invalid(lambda: actors['author'].client.post_note_edit(invitation=revision,
            signatures=[journal.get_authors_id(note.number)], note=openreview.api.Note(
                id=note.id, content={'title': {'value': 'Revised'}, 'track_id': {'value': 'Award'}})), 'track_id')
        edit = actors['author'].client.post_note_edit(invitation=revision,
            signatures=[journal.get_authors_id(note.number)], note=openreview.api.Note(
                id=note.id, content={'title': {'value': 'Revised'}}))
        helpers.await_queue_edit(openreview_client, edit['id'])
        assert openreview_client.get_note(note.id).content['track_id']['value'] == 'OSS'
        assert openreview_client.get_note(note.id).content['title']['value'] == 'Revised'

    def test_registry_invalid_and_unauthorized_writes(self, create_journal, actors, openreview_client):
        journal = create_journal()
        original = journal.get_tracks()
        for records in ([OSS], [REGULAR, OSS, OSS], [REGULAR, dict(OSS, open='yes')]):
            invalid(lambda: self.manage(journal, records, actors, openreview_client), 'Regular', 'unique', 'boolean')
            assert journal.get_tracks() == original
        for role in ('author', 'ae', 'outsider'):
            denied(lambda: actors[role].client.post_group_edit(
                invitation=journal.get_manage_tracks_id(), signatures=[actors[role].id],
                group=openreview.api.Group(id=journal.get_tracks_id(),
                    content={'tracks': {'value': [REGULAR]}})), role)
        self.manage(journal, [REGULAR, OSS], actors, openreview_client)

    def test_eligibility_membership_cleanup_and_assignment(self, create_journal, actors, helpers, openreview_client):
        journal = create_journal()
        note = self.submit(journal, actors, helpers, openreview_client)
        managed = self.eligibility(journal, actors)
        regular = self.eligibility(journal, actors, managed=False)
        for edge in (managed, regular):
            assert actors['eic'].client.get_edge(edge.id).weight == 1
            denied(lambda: actors['ae'].client.get_edge(edge.id), 'ae', edge_not_found=True)
        denied(lambda: actors['ae'].client.get_note(note.id), 'unassigned eligible ae')
        # Eligibility is advisory: assigning an ineligible AE remains supported.
        assignment = actors['eic'].client.post_edge(openreview.api.Edge(
            invitation=journal.get_ae_assignment_id(), signatures=[journal.get_editors_in_chief_id()],
            head=note.id, tail=actors['otherae'].id, weight=1))
        helpers.await_queue_edit(openreview_client, assignment.id)
        assert actors['otherae'].client.get_note(note.id).id == note.id
        invalid(lambda: actors['eic'].client.post_group_edit(
            invitation=journal.get_manage_action_editors_id(), signatures=[journal.get_editors_in_chief_id()],
            group=openreview.api.Group(id=journal.get_action_editors_id(),
                members={'remove': [actors['otherae'].id]})), 'Reassign active papers')
        edit = actors['eic'].client.post_group_edit(invitation=journal.get_manage_action_editors_id(),
            signatures=[journal.get_editors_in_chief_id()], group=openreview.api.Group(
                id=journal.get_action_editors_id(), members={'remove': [actors['ae'].id]}))
        helpers.await_queue_edit(openreview_client, edit['id'])
        assert actors['ae'].id not in openreview_client.get_group(journal.get_action_editors_id()).members
        for edge in (managed, regular):
            deleted = openreview_client.get_edge(edge.id, trash=True)
            assert deleted.ddate
            assert set(deleted.readers) == {journal.get_editors_in_chief_id(), actors['ae'].id}
        actors['eic'].client.post_group_edit(invitation=journal.get_add_action_editor_id(),
            signatures=[journal.get_editors_in_chief_id()], group=openreview.api.Group(
                id=journal.get_action_editors_id(), members={'add': [actors['ae'].id]}))
        assert actors['ae'].id in openreview_client.get_group(journal.get_action_editors_id()).members
        restored = self.eligibility(journal, actors, id=managed.id, ddate={'delete': True})
        assert not openreview_client.get_edge(restored.id).ddate

    @pytest.mark.parametrize('managed', [False, True], ids=['regular', 'managed'])
    def test_invalid_and_unauthorized_eligibility(self, managed, create_journal, actors, openreview_client):
        journal = create_journal()
        invalid(lambda: self.eligibility(journal, actors, managed, role='outsider'), 'membership')
        invalid(lambda: self.eligibility(journal, actors, managed, readers=[actors['ae'].id]), 'readers')
        if managed:
            invalid(lambda: self.eligibility(journal, actors, label='Unknown'), 'Unknown managed track')
        edge = self.eligibility(journal, actors, managed)
        for role in ('author', 'ae', 'outsider'):
            denied(lambda: actors[role].client.post_edge(openreview.api.Edge(
                invitation=edge.invitation, signatures=[actors[role].id],
                head=edge.head, tail=edge.tail, readers=edge.readers, writers=edge.writers,
                label=edge.label, weight=1)), role)
        assert openreview_client.get_edge(edge.id).weight == 1

    def test_eligibility_reference_and_membership_permissions(self, create_journal, actors, openreview_client):
        journal = create_journal()
        self.eligibility(journal, actors, label='Award')
        invalid(lambda: self.manage(journal, [REGULAR, OSS], actors, openreview_client), 'Referenced tracks')
        closed = dict(AWARD, open=False)
        self.manage(journal, [REGULAR, OSS, closed], actors, openreview_client)
        assert journal.get_tracks()[-1] == closed
        for role in ('author', 'ae', 'outsider'):
            for invitation, change in ((journal.get_add_action_editor_id(), 'add'),
                                       (journal.get_manage_action_editors_id(), 'remove')):
                denied(lambda: actors[role].client.post_group_edit(invitation=invitation,
                    signatures=[actors[role].id], group=openreview.api.Group(
                        id=journal.get_action_editors_id(), members={change: [actors['ae'].id]})), role)
        assert set(openreview_client.get_group(journal.get_action_editors_id()).members) == {
            actors['ae'].id, actors['otherae'].id}
