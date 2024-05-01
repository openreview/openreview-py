import pytest
import datetime
import openreview
from openreview.api import Note
from openreview import ProfileManagement
from openreview.api import OpenReviewClient
from openreview.venue.configuration import VenueConfiguration

class TestVenueConfiguration():

    @pytest.fixture(scope="class")
    def profile_management(self, openreview_client):
        profile_management = ProfileManagement(openreview_client, 'openreview.net')
        profile_management.setup()
        return profile_management

    def test_venue_configuration_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        venue_configuration = VenueConfiguration(openreview_client, support_group_id, super_id)
        venue_configuration.setup()

        helpers.create_user('sherry@iclr.cc', 'ProgramChair', 'ICLR')
        pc_client_v2=openreview.api.OpenReviewClient(username='sherry@iclr.cc', password=helpers.strong_password)

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_invitation('openreview.net/-/Conference_Venue_Request')
        assert openreview_client.get_invitation('openreview.net/-/Comment')
        assert openreview_client.get_invitation('openreview.net/-/Deploy')

        # post a conference request form
        conference_request = openreview_client.post_note_edit(invitation='openreview.net/-/Conference_Venue_Request',
            signatures=['~Super_User1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The Thirteenth International Conference on Learning Representations' },
                    'abbreviated_venue_name': { 'value': 'ICLR 2025' },
                    'venue_website_url': { 'value': 'https://iclr.cc/Conferences/2025' },
                    'program_chair_emails': { 'value': ['sherry@iclr.cc'] },
                    'contact_email': { 'value': 'iclr2024.programchairs@gmail.com' },
                    'location': { 'value': 'Vienna, Austria' },
                    'publication_chairs': { 'value': 'No, our venue does not have Publication Chairs' },
                    'area_chairs_and_senior_area_chairs': { 'value': 'Yes, our venue has Area Chairs and Senior Area Chairs' },
                    'ethics_chairs_and_reviewers': { 'value': 'No, our venue does not have Ethics Chairs and Reviewers' },
                    'secondary_area_chairs': { 'value': 'No, our venue does not have Secondary Area Chairs' },
                    'author_and_reviewer_anonymity': { 'value': 'Double-blind' }
                }
            ))
        
        assert conference_request
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/-/Conference_Venue_Request')

        request = openreview_client.get_note(conference_request['note']['id'])
        assert openreview_client.get_invitation(f'openreview.net/Conference_Venue_Request{request.number}/-/Comment')
        assert openreview_client.get_invitation(f'openreview.net/Conference_Venue_Request{request.number}/-/Deploy')

        openreview_client.post_note_edit(invitation=f'openreview.net/Conference_Venue_Request{request.number}/-/Deploy',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'ICLR.cc/2025/Conference' }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Conference_Venue_Request1/-/Deploy')
        
        assert openreview.tools.get_group(openreview_client, 'ICLR.cc/2025/Conference')
        assert openreview.tools.get_group(openreview_client, 'ICLR.cc/2025')
        submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission')
        assert submission_inv and not submission_inv.duedate
        assert not submission_inv.expdate
        submission_deadline_inv =  openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission/Deadline')
        assert submission_deadline_inv and submission_inv.id in submission_deadline_inv.edit['invitation']['id']
        submission_expiration_inv =  openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission/Expiration')
        assert submission_expiration_inv and submission_inv.id in submission_expiration_inv.edit['invitation']['id']

        now = datetime.datetime.now()
        duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=1))

        # edit Submission duedate with Submission/Deadline invitation
        pc_client_v2.post_invitation_edit(
            invitations=submission_deadline_inv.id,
            invitation=openreview.api.Invitation(
                id=submission_inv.id,
                duedate=duedate
            )
        )
        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2025/Conference/-/Submission/Deadline')

        # assert submission deadline and expdate get updated
        submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission')
        assert submission_inv and submission_inv.duedate == duedate
        assert submission_inv.expdate == duedate + (30*60*1000)

        # # edit Submission content with Submission/Content invitation
        # pc_client_v2.post_invitation_edit(
        #     invitations=submission_deadline_inv.id,
        #     invitation=openreview.api.Invitation(
        #         id=submission_inv.id,
        #         edit={
        #             'note': {
        #                 'content': {
        #                     'subject_area': {
        #                         'order': 10,
        #                         "description": "Select one subject area.",
        #                         'value': {
        #                             'param': {
        #                                 'type': 'string',
        #                                 'enum': [
        #                                     "3D from multi-view and sensors",
        #                                     "3D from single images",	
        #                                     "Adversarial attack and defense",	
        #                                     "Autonomous driving",
        #                                     "Biometrics",	
        #                                     "Computational imaging",	
        #                                     "Computer vision for social good",	
        #                                     "Computer vision theory",	
        #                                     "Datasets and evaluation"
        #                                 ],
        #                                 "input": "select"
        #                             }
        #                         }
        #                     }
        #                 }
        #             }
        #         }
        #     )
        # )
        # helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2025/Conference/-/Submission/Deadline')

        # submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission')
        # assert submission_inv and 'subject_area' in submission_inv.edit['note']['content']