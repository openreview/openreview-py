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

        now = datetime.datetime.utcnow()
        start_date = now + datetime.timedelta(minutes=30)
        due_date = now + datetime.timedelta(days=1)

        # post a conference request form
        conference_request = openreview_client.post_note_edit(invitation='openreview.net/-/Conference_Venue_Request',
            signatures=['~Super_User1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The Thirteenth International Conference on Learning Representations' },
                    'abbreviated_venue_name': { 'value': 'ICLR 2025' },
                    'venue_website_url': { 'value': 'https://iclr.cc/Conferences/2025' },
                    'location': { 'value': 'Vienna, Austria' },
                    'venue_start_date': { 'value': now.strftime('%Y/%m/%d') },
                    'program_chair_emails': { 'value': ['sherry@iclr.cc'] },
                    'contact_email': { 'value': 'iclr2024.programchairs@gmail.com' },
                    'publication_chairs': { 'value': 'No, our venue does not have Publication Chairs' },
                    'area_chairs_and_senior_area_chairs': { 'value': 'Yes, our venue has Area Chairs and Senior Area Chairs' },
                    'ethics_chairs_and_reviewers': { 'value': 'No, our venue does not have Ethics Chairs and Reviewers' },
                    'secondary_area_chairs': { 'value': 'No, our venue does not have Secondary Area Chairs' },
                    'submission_start_date': { 'value': start_date.strftime('%Y/%m/%d %H:%M') },
                    'submission_deadline': { 'value': due_date.strftime('%Y/%m/%d %H:%M') },
                    'author_and_reviewer_anonymity': { 'value': 'Double-blind' },
                    'force_profiles_only': { 'value': 'No, allow submissions with email addresses' },
                    'submission_readers': { 'value': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)' },
                    'submission_license': { 'value': ['CC BY-NC 4.0'] },
                    'email_pcs_for_new_submissions': { 'value': 'No, do not email PCs.' }
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
        assert submission_inv and submission_inv.cdate == openreview.tools.datetime_millis(start_date.replace(second=0, microsecond=0))
        assert submission_inv.duedate == openreview.tools.datetime_millis(due_date.replace(second=0, microsecond=0))
        assert submission_inv.expdate == submission_inv.duedate + (30*60*1000)
        submission_deadline_inv =  openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission/Deadline')
        assert submission_deadline_inv and submission_inv.id in submission_deadline_inv.edit['invitation']['id']
        post_submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Post_Submission')
        assert post_submission_inv and post_submission_inv.cdate == submission_inv.expdate

        now = datetime.datetime.now()
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        # extend Submission duedate with Submission/Deadline invitation
        pc_client_v2.post_invitation_edit(
            invitations=submission_deadline_inv.id,
            invitation=openreview.api.Invitation(
                id=submission_inv.id,
                duedate=new_duedate
            )
        )
        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2025/Conference/-/Submission/Deadline')

        # assert submission deadline and expdate get updated
        submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission')
        assert submission_inv and submission_inv.duedate == new_duedate
        assert submission_inv.expdate == new_duedate + (30*60*1000)
        post_submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Post_Submission')
        assert post_submission_inv and post_submission_inv.cdate == submission_inv.expdate

        content_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission/Content')
        assert content_inv
        assert 'subject_area' not in submission_inv.edit['note']['content']
        assert 'keywords' in submission_inv.edit['note']['content']

        ## edit Submission content with Submission/Content invitation
        pc_client_v2.post_invitation_edit(
            invitations=content_inv.id,
            content = {
                'note_content': {
                    'value': {
                        'subject_area': {
                            'order': 10,
                            "description": "Select one subject area.",
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
                                        "3D from multi-view and sensors",
                                        "3D from single images",
                                        "Adversarial attack and defense",
                                        "Autonomous driving",
                                        "Biometrics",
                                        "Computational imaging",
                                        "Computer vision for social good",
                                        "Computer vision theory",
                                        "Datasets and evaluation"
                                    ],
                                    "input": "select"
                                }
                            }
                        },
                        'keywords': {
                            'delete': True
                        }
                    }
                }
            }
        )

        submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission')
        assert submission_inv and 'subject_area' in submission_inv.edit['note']['content']
        assert 'keywords' not in submission_inv.edit['note']['content']
        content_keys = submission_inv.edit['note']['content'].keys()
        assert all(field in content_keys for field in ['title', 'authors', 'authorids', 'TLDR', 'abstract', 'pdf'])