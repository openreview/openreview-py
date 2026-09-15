from types import SimpleNamespace

import openreview
import pytest

from openreview.journal.tracks import TrackManager, is_eligible, validate_tracks
from openreview.journal.invitation import InvitationBuilder


TRACKS = [
    {'id': 'Regular', 'name': 'Regular', 'open': True, 'default': True, 'eligibility_mode': 'exclude'},
    {'id': 'Software', 'name': 'Software', 'open': True, 'default': False, 'eligibility_mode': 'include'}
]


@pytest.mark.parametrize('tracks, message', [
    ({}, 'list'),
    ([{'id': 'Regular'}], 'exactly'),
    ([dict(TRACKS[0], extra=True)], 'exactly'),
    ([dict(TRACKS[0], id='bad id')], 'invalid track id'),
    ([TRACKS[0], dict(TRACKS[1], id='Regular')], 'duplicate'),
    ([dict(TRACKS[0], open=1)], 'booleans'),
    ([dict(TRACKS[0], eligibility_mode='sometimes')], 'eligibility_mode'),
    ([dict(TRACKS[0], default=False), TRACKS[1]], 'exactly one'),
    ([dict(TRACKS[0], open=False)], 'default track must be open')
])
def test_validate_tracks_rejects_malformed_registry(tracks, message):
    with pytest.raises(ValueError, match=message):
        validate_tracks(tracks)


def test_track_eligibility_modes():
    assert is_eligible(TRACKS[0], False)
    assert not is_eligible(TRACKS[0], True)
    assert is_eligible(TRACKS[1], True)
    assert not is_eligible(TRACKS[1], False)


class FakeClient:
    def __init__(self):
        self.groups = {
            'Test/Tracks': SimpleNamespace(content={'tracks': {'value': TRACKS}}),
            'Test/Action_Editors': SimpleNamespace(members=['~One1', '~Two1', '~Three1'])
        }
        self.notes = {
            'p1': SimpleNamespace(
                id='p1', invitations=['Test/-/Submission'], domain='Test', ddate=None,
                content={'track_id': {'value': 'Regular'}}),
            'p2': SimpleNamespace(
                id='p2', invitations=['Test/-/Submission'], domain='Test', ddate=None,
                content={'track_id': {'value': 'Software'}})
        }
        self.edges = [
            openreview.api.Edge(
                id='eligibility-1', invitation='Test/Action_Editors/-/Track_Eligibility',
                head='Test/Action_Editors', tail='~One1', label='Regular', weight=1),
            openreview.api.Edge(
                id='eligibility-2', invitation='Test/Action_Editors/-/Track_Eligibility',
                head='Test/Action_Editors', tail='~Two1', label='Software', weight=1)
        ]
        self.writes = []
        self.invitation = None

    def get_group(self, group_id=None, id=None):
        return self.groups[group_id or id]

    def get_note(self, note_id):
        return self.notes[note_id]

    def get_invitation(self, invitation_id=None, id=None):
        return self.invitation

    def get_all_notes(self, invitation):
        return list(self.notes.values())

    def get_all_edges(self, invitation, **params):
        return [edge for edge in self.edges if edge.invitation == invitation and all(
            getattr(edge, key) == value for key, value in params.items()
        )]

    def post_edges(self, edges):
        self.writes.extend(edges)
        for edge in edges:
            if edge.id:
                prior = next(item for item in self.edges if item.id == edge.id)
                self.edges.remove(prior)
            else:
                edge.id = f'score-{len(self.edges)}'
            self.edges.append(edge)
        return edges


def make_manager(client=None, tracks=TRACKS):
    client = client or FakeClient()
    journal = SimpleNamespace(
        client=client,
        settings={'tracks': tracks},
        venue_id='Test',
        get_tracks_id=lambda: 'Test/Tracks',
        get_action_editors_id=lambda: 'Test/Action_Editors',
        get_editors_in_chief_id=lambda: 'Test/Editors_In_Chief',
        get_track_eligibility_id=lambda: 'Test/Action_Editors/-/Track_Eligibility',
        get_track_score_id=lambda: 'Test/Action_Editors/-/Track_Score',
        get_author_submission_id=lambda: 'Test/-/Submission'
    )
    return TrackManager(journal)


def test_closed_track_is_valid_only_for_authorized_inheritance():
    client = FakeClient()
    client.groups['Test/Tracks'].content['tracks']['value'] = [
        TRACKS[0], dict(TRACKS[1], open=False)
    ]
    manager = make_manager(client)
    with pytest.raises(openreview.OpenReviewException, match='closed'):
        manager.validate_submission_track('Software')
    assert manager.validate_submission_track('Software', allow_closed=True) == 'Software'


def test_referenced_track_cannot_be_deleted():
    manager = make_manager()
    with pytest.raises(openreview.OpenReviewException, match='close them instead'):
        manager.validate_registry_update([TRACKS[0]])


def test_deleted_paper_still_prevents_track_deletion():
    client = FakeClient()
    client.notes['p2'].ddate = 1
    with pytest.raises(openreview.OpenReviewException, match='close them instead'):
        make_manager(client).validate_registry_update([TRACKS[0]])


def test_prepare_scores_writes_complete_matrix_and_is_idempotent():
    client = FakeClient()
    manager = make_manager(client)
    assert manager.prepare_scores(['p1', 'p2']) == {
        'papers': 2, 'action_editors': 3, 'scores': 6
    }
    scores = {
        (edge.head, edge.tail): edge.weight for edge in client.edges
        if edge.invitation == 'Test/Action_Editors/-/Track_Score' and not edge.ddate
    }
    assert scores == {
        ('p1', '~One1'): 0, ('p1', '~Two1'): 1, ('p1', '~Three1'): 1,
        ('p2', '~One1'): 0, ('p2', '~Two1'): 1, ('p2', '~Three1'): 0
    }
    client.writes.clear()
    manager.prepare_scores(['p1', 'p2'])
    assert client.writes == []


def test_prepare_scores_rejects_all_input_before_writes():
    client = FakeClient()
    client.notes['bad'] = SimpleNamespace(
        id='bad', invitations=['Other/-/Submission'], domain='Other', ddate=None,
        content={'track_id': {'value': 'Unknown'}})
    with pytest.raises(ValueError, match='invalid managed-track paper'):
        make_manager(client).prepare_scores(['p1', 'bad'])
    assert client.writes == []


def test_missing_or_empty_setting_is_disabled():
    assert not make_manager(tracks=[]).enabled


def test_journal_validates_settings_without_database_access():
    with pytest.raises(ValueError, match='duplicate'):
        openreview.journal.Journal(
            SimpleNamespace(), 'Test', 'secret', 'test@example.com', 'Test', 'Test',
            settings={'tracks': [TRACKS[0], dict(TRACKS[1], id='Regular')]}
        )
    with pytest.raises(ValueError, match='reserved'):
        openreview.journal.Journal(
            SimpleNamespace(), 'Test', 'secret', 'test@example.com', 'Test', 'Test',
            settings={'tracks': TRACKS, 'submission_additional_fields': {'track_id': {}}}
        )


def test_prepare_scores_retires_duplicates_and_removed_editors():
    client = FakeClient()
    manager = make_manager(client)
    manager.prepare_scores(['p1'])
    score = next(edge for edge in client.edges if edge.invitation.endswith('/Track_Score'))
    client.edges.append(openreview.api.Edge(
        id='duplicate', invitation=score.invitation, head=score.head,
        tail=score.tail, label=score.label, weight=score.weight
    ))
    client.groups['Test/Action_Editors'].members.remove('~Three1')
    manager.prepare_scores(['p1'])
    active = [
        edge for edge in client.edges
        if edge.invitation.endswith('/Track_Score') and not edge.ddate
    ]
    assert len(active) == 2
    assert {edge.tail for edge in active} == {'~One1', '~Two1'}


def test_submission_preprocess_composition_is_stable_across_setup():
    builder = InvitationBuilder.__new__(InvitationBuilder)
    builder.get_process_content = lambda path: '# journal-managed-track-validation\ndef process(client, edit, invitation):\n    pass\n'
    custom = 'def process(client, edit, invitation):\n    edit.checked = True\n'
    combined = builder.get_combined_preprocess_content(custom, 'unused.py')
    assert builder.get_combined_preprocess_content(combined, 'unused.py') == combined
    assert builder.get_preprocess_without_managed_tracks(combined) == custom


def test_disabling_tracks_removes_only_native_validation():
    client = FakeClient()
    enabled = openreview.journal.Journal(
        client, 'Test', 'secret', 'test@example.com', 'Test', 'Test',
        settings={'tracks': TRACKS}
    )
    saved = []
    enabled.invitation_builder.save_invitation = saved.append
    enabled.invitation_builder.set_submission_invitation()
    client.invitation = saved[0]

    disabled = openreview.journal.Journal(
        client, 'Test', 'secret', 'test@example.com', 'Test', 'Test', settings={}
    )
    saved = []
    disabled.invitation_builder.save_invitation = saved.append
    disabled.invitation_builder.set_submission_invitation()
    assert 'track_id' not in saved[0].edit['note']['content']
    assert saved[0].preprocess is None


@pytest.mark.parametrize('tracks, expected', [(TRACKS, True), ([], False)])
def test_submission_form_is_feature_gated(tracks, expected):
    client = FakeClient()
    journal = openreview.journal.Journal(
        client, 'Test', 'secret', 'test@example.com', 'Test', 'Test',
        settings={'tracks': tracks}
    )
    saved = []
    journal.invitation_builder.save_invitation = saved.append
    journal.invitation_builder.set_submission_invitation()
    content = saved[0].edit['note']['content']
    assert ('track_id' in content) is expected
    assert bool(saved[0].preprocess) is expected
    if expected:
        assert content['track_id']['value']['param']['default'] == 'Regular'
        assert [item['value'] for item in content['track_id']['value']['param']['enum']] == [
            'Regular', 'Software'
        ]


def test_track_management_invitations_are_feature_gated():
    client = FakeClient()
    journal = openreview.journal.Journal(
        client, 'Test', 'secret', 'test@example.com', 'Test', 'Test',
        settings={'tracks': TRACKS}
    )
    saved = []
    journal.invitation_builder.save_invitation = saved.append
    journal.invitation_builder.set_track_invitations()
    assert [invitation.id for invitation in saved] == [
        'Test/-/Manage_Tracks',
        'Test/Action_Editors/-/Track_Eligibility',
        'Test/Action_Editors/-/Track_Score'
    ]
    assert saved[0].invitees == ['Test/Editors_In_Chief']
    assert 'Listed AEs are included' in saved[0].web
    assert 'set_submission_invitation()' in saved[0].process
    assert 'settings={"tracks":' in saved[0].process
    assert saved[1].readers == ['Test', 'Test/Editors_In_Chief']
    assert saved[1].edit['id']['param']['withInvitation'] == saved[1].id
    assert saved[2].edit['id']['param']['withInvitation'] == saved[2].id
    assert saved[2].edit['weight']['param']['enum'] == [0, 1]


def test_standard_revisions_do_not_expose_track_id():
    journal = openreview.journal.Journal(
        FakeClient(), 'Test', 'secret', 'test@example.com', 'Test', 'Test',
        settings={'tracks': TRACKS}
    )
    saved = []
    journal.invitation_builder.save_super_invitation = lambda *args: saved.append(args[-1])
    journal.invitation_builder.set_revision_invitation()
    journal.invitation_builder.set_eic_revision_invitation()
    for invitation in saved:
        content = invitation['edit']['note']['content']
        assert 'track_id' not in content


def test_failed_score_cleanup_fails_readback():
    class BrokenCleanupClient(FakeClient):
        def post_edges(self, edges):
            accepted = []
            for edge in edges:
                if edge.ddate:
                    edge.ddate = None
                else:
                    accepted.append(edge)
            return super().post_edges(accepted)

    client = BrokenCleanupClient()
    manager = make_manager(client)
    manager.prepare_scores(['p1'])
    score = next(edge for edge in client.edges if edge.invitation.endswith('/Track_Score'))
    client.edges.append(openreview.api.Edge(
        id='duplicate', invitation=score.invitation, head=score.head,
        tail=score.tail, label=score.label, weight=score.weight
    ))
    with pytest.raises(openreview.OpenReviewException, match='readback'):
        manager.prepare_scores(['p1'])
