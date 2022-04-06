import openreview
import pytest
import datetime
from selenium.common.exceptions import NoSuchElementException
from openreview import VenueRequest

class TestSubmissionReaders():

    @pytest.fixture(scope='class')
    def venue(self, client, test_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        VenueRequest(client, support_group_id, super_id)

        helpers.await_queue()

        # Add support group user to the support group object
        support_group = client.get_group(support_group_id)
        client.add_members_to_group(group=support_group, members=['~Support_User1'])

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        request_form_note = openreview.Note(
            invitation=support_group_id +'/-/Request_Form',
            signatures=['~SomeFirstName_User1'],
            readers=[
                support_group_id,
                '~SomeFirstName_User1',
                'test@mail.com',
                'tom@mail.com'
            ],
            writers=[],
            content={
                'title': 'Test 2040 Venue',
                'Official Venue Name': 'Test 2040 Venue',
                'Abbreviated Venue Name': 'TestVenue@OR2040',
                'Official Website URL': 'https://testvenue2040.gitlab.io/venue/',
                'program_chair_emails': [
                    'test@mail.com',
                    'tom@mail.com'],
                'contact_email': 'test@mail.com',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'No, our venue does not have Senior Area Chairs',
                'Venue Start Date': now.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'Author and Reviewer Anonymity': 'Double-blind',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                'email_pcs_for_new_submissions': 'Yes, email PCs for every new submission.',
                'reviewer_identity': ['Program Chairs', 'Assigned Area Chair', 'Assigned Senior Area Chair'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair']
            })

        request_form_note=test_client.post_note(request_form_note)

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'TEST.cc/2040/Conference'},
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number),
            readers=[support_group_id],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=[support_group_id],
            writers=[support_group_id]
        ))

        helpers.await_queue()

        # Return venue details as a dict
        venue_details = {
            'request_form_note': request_form_note,
            'support_group_id': support_group_id,
            'venue_id': 'TEST.cc/2040/Conference'
        }
        return venue_details

    def test_submission_stage(self, client, venue, helpers):

        author_client = helpers.create_user('workshop_author1@mail.com', 'Workshop', 'Author')

        submission_one = author_client.post_note(openreview.Note(
            invitation='{}/-/Submission'.format(venue['venue_id']),
            readers=[
                venue['venue_id'],
                '~Workshop_Author1'],
            writers=[
                '~Workshop_Author1',
                venue['venue_id']
            ],
            signatures=['~Workshop_Author1'],
            content={
                'title': 'test submission',
                'authorids': ['~Workshop_Author1'],
                'authors': ['Workshop Author'],
                'abstract': 'test abstract',
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        ))

        assert submission_one
        helpers.await_queue()

        submission_two = author_client.post_note(openreview.Note(
            invitation='{}/-/Submission'.format(venue['venue_id']),
            readers=[
                venue['venue_id'],
                '~Workshop_Author1',
                'workshop_author2@mail.com'],
            writers=[
                '~Workshop_Author1',
                venue['venue_id']
            ],
            signatures=['~Workshop_Author1'],
            content={
                'title': 'test submission',
                'authorids': ['~Workshop_Author1', 'workshop_author2@mail.com'],
                'authors': ['Workshop Author', 'Workshop Author'],
                'abstract': 'test abstract',
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        ))

        assert submission_two
        helpers.await_queue()

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        conference.setup_post_submission_stage(force=True)

        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']), sort='number:asc')
        assert blind_submissions and len(blind_submissions) == 2

        venue_id = venue['venue_id']

        assert f'{venue_id}/Paper1/Reviewers' in blind_submissions[0].readers
        assert f'{venue_id}/Reviewers' not in blind_submissions[0].readers

        assert f'{venue_id}/Paper1/Area_Chairs' in blind_submissions[0].readers
        assert f'{venue_id}/Area_Chairs' not in blind_submissions[0].readers