import os
import pytest
import datetime
import openreview
from openreview.api import Note
from openreview.api import OpenReviewClient
from openreview.workflows import Simple_Dual_Anonymous_Workflow

class TestSimpleDualAnonymous():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@abcd.cc', 'ProgramChair', 'ABCD')
        pc_client_v2=openreview.api.OpenReviewClient(username='programchair@abcd.cc', password=helpers.strong_password)

        workflow_setup = Simple_Dual_Anonymous_Workflow(openreview_client, support_group_id, super_id)
        workflow_setup.setup()

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_invitation('openreview.net/Support/Simple_Dual_Anonymous/-/Venue_Configuration_Request')
        assert openreview_client.get_invitation('openreview.net/Support/-/Deployment')

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=1)

        request = openreview_client.post_note_edit(invitation='openreview.net/Support/Simple_Dual_Anonymous/-/Venue_Configuration_Request',
            signatures=['~ProgramChair_ABCD1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The ABCD Conference' },
                    'abbreviated_venue_name': { 'value': 'ABCD 2025' },
                    'venue_website_url': { 'value': 'https://abcd.cc/Conferences/2025' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@abcd.cc'] },
                    'contact_email': { 'value': 'abcd2025.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'submission_license': { 'value': ['CC BY-NC 4.0'] }
                }
            ))
        
        assert request
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Support/Simple_Dual_Anonymous/-/Venue_Configuration_Request')

        request = openreview_client.get_note(request['note']['id'])
        # assert openreview_client.get_invitation(f'openreview.net/Venue_Configuration_Request{request.number}/-/Comment')
        assert openreview_client.get_invitation(f'openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request{request.number}/-/Deployment')

        openreview_client.post_note_edit(invitation=f'openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request{request.number}/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'ABCD.cc/2025/Conference' }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Support/Simple_Dual_Anonymous/Venue_Configuration_Request1/-/Deployment')

        assert openreview.tools.get_group(openreview_client, 'ABCD.cc/2025/Conference')
        assert openreview.tools.get_group(openreview_client, 'ABCD.cc/2025')
        assert openreview.tools.get_group(openreview_client, 'ABCD.cc')

        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Submission')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Official_Review')
        assert openreview_client.get_invitation('ABCD.cc/2025/Conference/-/Decision')

    def test_post_submissions(self, openreview_client, test_client, helpers):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,11):
            note = openreview.api.Note(
                license = 'CC BY 4.0',
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Andrew Mc'] },
                    'keywords': { 'value': ['nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                }
            )

            test_client.post_note_edit(invitation='ABCD.cc/2025/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        # helpers.await_queue_edit(openreview_client, invitation='ABCD.cc/2025/Conference/-/Submission', count=10)

        submissions = openreview_client.get_notes(invitation='ABCD.cc/2025/Conference/-/Submission')
        assert len(submissions) == 10
        assert submissions[0].readers == ['ABCD.cc/2025/Conference', '~SomeFirstName_User1', 'andrew@umass.edu']