import openreview
import pytest
from openreview.api import OpenReviewClient
from openreview.api import Note


class TestJournalRequestWorkflow():

    def test_user_submitted_request(self, openreview_client, journal_request, helpers):

        support_group_id = 'openreview.net/Support'

        request_invitation = openreview_client.get_invitation('openreview.net/Support/-/Journal_Request')
        assert 'venue_id' not in request_invitation.edit['note']['content']
        assert 'secret_key' not in request_invitation.edit['note']['content']
        assert 'id' not in request_invitation.edit['note']
        settings_param = request_invitation.edit['note']['content']['settings']['value']['param']
        assert settings_param['default']['assignment_delay'] == 5
        assert settings_param['default']['submission_name'] == 'Submission'
        assert settings_param['default']['number_of_reviewers'] == 3
        assert 'docs.openreview.net' in request_invitation.edit['note']['content']['settings']['description']

        assert openreview_client.get_invitation('openreview.net/Support/-/Journal_Request_Deployment')

        helpers.create_user('eic@ijcv.org', 'EICFirst', 'IJCV')
        eic_client = OpenReviewClient(username='eic@ijcv.org', password=helpers.strong_password)

        request = eic_client.post_note_edit(invitation='openreview.net/Support/-/Journal_Request',
            signatures=['~EICFirst_IJCV1'],
            note=Note(
                content={
                    'official_venue_name': { 'value': 'International Journal of Computer Vision' },
                    'abbreviated_venue_name': { 'value': 'IJCV' },
                    'contact_info': { 'value': 'eic@ijcv.org' },
                    'support_role': { 'value': 'eic@ijcv.org' },
                    'editors': { 'value': ['eic@ijcv.org'] },
                    'website': { 'value': 'https://ijcv.org' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        # the EICs receive a confirmation email
        messages = openreview_client.get_messages(to='eic@ijcv.org', subject='Your journal request has been received.')
        assert len(messages) == 1

        # the journal must not be deployed yet: no venue id was assigned
        assert openreview.tools.get_group(openreview_client, 'IJCV') is None

        # the editors listed in the form can read the pending request
        request_note = eic_client.get_note(request['note']['id'])
        assert 'venue_id' not in request_note.content
        assert 'secret_key' not in request_note.content
        assert request_note.readers == [support_group_id, 'eic@ijcv.org']
        assert request_note.writers == [support_group_id, 'eic@ijcv.org']

        # the Revision invitation is available from submission for the listed editors
        revision_invitation = openreview_client.get_invitation(f'openreview.net/Support/Journal_Request{request_note.number}/-/Revision')
        assert revision_invitation.invitees == [support_group_id, 'eic@ijcv.org']
        assert 'secret_key' not in revision_invitation.edit['note']['content']

        # the submitter edits the pending request through the Revision invitation
        edit = eic_client.post_note_edit(invitation=f'openreview.net/Support/Journal_Request{request_note.number}/-/Revision',
            signatures=['~EICFirst_IJCV1'],
            note=Note(
                id=request_note.id,
                content={
                    'official_venue_name': { 'value': 'International Journal of Computer Vision' },
                    'abbreviated_venue_name': { 'value': 'IJCV' },
                    'contact_info': { 'value': 'eic@ijcv.org' },
                    'support_role': { 'value': 'eic@ijcv.org' },
                    'editors': { 'value': ['eic@ijcv.org'] },
                    'website': { 'value': 'https://ijcv.org' },
                    'settings': {
                        'value': {
                            'assignment_delay': 0
                        }
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        # still not deployed, and no duplicate confirmation email for the edit
        assert openreview.tools.get_group(openreview_client, 'IJCV') is None
        messages = openreview_client.get_messages(to='eic@ijcv.org', subject='Your journal request has been received.')
        assert len(messages) == 1

    def test_deployment(self, openreview_client, journal_request, helpers):

        support_group_id = 'openreview.net/Support'

        request = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'abbreviated_venue_name': 'IJCV' })[0]

        # deploy the journal: the venue id is assigned by the deployment edit
        edit = openreview_client.post_note_edit(invitation='openreview.net/Support/-/Journal_Request_Deployment',
            signatures=[support_group_id],
            note=Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'IJCV' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        journal_group = openreview_client.get_group('IJCV')
        assert journal_group.content['journal_request_id']['value'] == request.id

        eic_group = openreview_client.get_group('IJCV/Editors_In_Chief')
        assert 'eic@ijcv.org' in eic_group.members

        assert openreview_client.get_group('IJCV/Action_Editors')
        assert openreview_client.get_group('IJCV/Reviewers')
        assert openreview_client.get_invitation('IJCV/-/Submission')

        # the request note got the venue id and was released to the journal groups
        request = openreview_client.get_note(request.id)
        assert request.content['venue_id']['value'] == 'IJCV'
        assert set(request.readers) == { support_group_id, 'IJCV', 'IJCV/Action_Editors' }
        assert set(request.writers) == { support_group_id, 'IJCV' }

        # the secret key was generated at deployment, stored in the venue group
        # content and is only visible to the venue
        assert 'secret_key' not in request.content
        assert journal_group.content['secret_key']['value']
        assert len(journal_group.content['secret_key']['value']) == 16
        assert journal_group.content['secret_key']['readers'] == ['IJCV']

        # the journal request tooling was set up on the request forum
        assert openreview_client.get_group(f'openreview.net/Support/Journal_Request{request.number}')
        assert openreview_client.get_invitation(f'openreview.net/Support/Journal_Request{request.number}/-/Comment')
        assert openreview_client.get_invitation(f'openreview.net/Support/Journal_Request{request.number}/-/Action_Editor_Recruitment')
        assert openreview_client.get_invitation(f'openreview.net/Support/Journal_Request{request.number}/-/Reviewer_Recruitment')
        assert openreview_client.get_invitation(f'openreview.net/Support/Journal_Request{request.number}/-/Reviewer_Recruitment_by_AE')

        # the Revision invitation now belongs to the venue groups
        revision_invitation = openreview_client.get_invitation(f'openreview.net/Support/Journal_Request{request.number}/-/Revision')
        assert revision_invitation.invitees == ['IJCV', support_group_id]
        assert 'secret_key' not in revision_invitation.edit['note']['content']

        # the request form cannot edit notes: it only creates new requests
        eic_client = OpenReviewClient(username='eic@ijcv.org', password=helpers.strong_password)
        with pytest.raises(openreview.OpenReviewException):
            eic_client.post_note_edit(invitation='openreview.net/Support/-/Journal_Request',
                signatures=['~EICFirst_IJCV1'],
                note=Note(
                    id=request.id,
                    content={
                        'official_venue_name': { 'value': 'International Journal of Computer Vision' },
                        'abbreviated_venue_name': { 'value': 'IJCV' },
                        'contact_info': { 'value': 'eic@ijcv.org' },
                        'support_role': { 'value': 'eic@ijcv.org' },
                        'editors': { 'value': ['eic@ijcv.org'] },
                        'website': { 'value': 'https://ijcv.org' }
                    }
                ))

        # the EICs edit the settings after deployment through the Revision invitation
        edit = eic_client.post_note_edit(invitation=f'openreview.net/Support/Journal_Request{request.number}/-/Revision',
            signatures=['~EICFirst_IJCV1'],
            note=Note(
                id=request.id,
                content={
                    'official_venue_name': { 'value': 'International Journal of Computer Vision' },
                    'abbreviated_venue_name': { 'value': 'IJCV' },
                    'contact_info': { 'value': 'eic@ijcv.org' },
                    'support_role': { 'value': 'eic@ijcv.org' },
                    'editors': { 'value': ['eic@ijcv.org'] },
                    'website': { 'value': 'https://ijcv.org' },
                    'settings': {
                        'value': {
                            'assignment_delay': 5
                        }
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert openreview_client.get_invitation('IJCV/-/Submission')

        # the secret key is preserved and the journal groups keep access to the forum
        updated_group = openreview_client.get_group('IJCV')
        assert updated_group.content['secret_key']['value'] == journal_group.content['secret_key']['value']
        updated_request = openreview_client.get_note(request.id)
        assert set(updated_request.readers) == { support_group_id, 'IJCV', 'IJCV/Action_Editors' }
        assert set(updated_request.writers) == { support_group_id, 'IJCV' }

    def test_deployment_with_used_venue_id(self, openreview_client, journal_request, helpers):

        support_group_id = 'openreview.net/Support'

        eic_client = OpenReviewClient(username='eic@ijcv.org', password=helpers.strong_password)

        second_request = eic_client.post_note_edit(invitation='openreview.net/Support/-/Journal_Request',
            signatures=['~EICFirst_IJCV1'],
            note=Note(
                content={
                    'official_venue_name': { 'value': 'International Journal of Computer Vision Two' },
                    'abbreviated_venue_name': { 'value': 'IJCV2' },
                    'contact_info': { 'value': 'eic@ijcv.org' },
                    'support_role': { 'value': 'eic@ijcv.org' },
                    'editors': { 'value': ['eic@ijcv.org'] },
                    'website': { 'value': 'https://ijcv.org' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=second_request['id'])

        # deploying a different request reusing the same venue id must be rejected
        with pytest.raises(openreview.OpenReviewException, match=r'The venue id IJCV has already been used'):
            openreview_client.post_note_edit(invitation='openreview.net/Support/-/Journal_Request_Deployment',
                signatures=[support_group_id],
                note=Note(
                    id=second_request['note']['id'],
                    content={
                        'venue_id': { 'value': 'IJCV' }
                    }
                ))
