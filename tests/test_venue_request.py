import openreview
import pytest
import time
import datetime
from selenium.common.exceptions import NoSuchElementException
from openreview import VenueRequest

class TestVenueRequest():

    @pytest.fixture(scope='class')
    def venue(self, client, support_client, test_client):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        VenueRequest(client, support_group_id, super_id)

        time.sleep(2)

        # Add support group user to the support group object
        support_group = client.get_group(support_group_id)
        client.add_members_to_group(group=support_group, members=['~Support_User1'])

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        request_form_note = test_client.post_note(openreview.Note(
            invitation=support_group_id +'/-/Request_Form',
            signatures=['~Test_User1'],
            readers=[
                support_group_id,
                '~Test_User1',
                'test@mail.com',
                'tom@mail.com'
            ],
            writers=[],
            content={
                'title': 'Test 2030 Venue',
                'Official Venue Name': 'Test 2030 Venue',
                'Abbreviated Venue Name': 'TestVenue@OR2030',
                'Official Website URL': 'https://testvenue2030.gitlab.io/venue/',
                'program_chair_emails': [
                    'test@mail.com',
                    'tom@mail.com'],
                'contact_email': 'test@mail.com',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'Venue Start Date': now.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'Paper Matching': [
                    'Reviewer Bid Scores',
                    'Reviewer Recommendation Scores'],
                'Author and Reviewer Anonymity': 'Double-blind',
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'Public Commentary': 'No, do not allow public commentary.',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
            }))
        time.sleep(5)

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'TEST.cc/2030/Conference'},
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number),
            readers=[support_group_id],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=[support_group_id],
            writers=[support_group_id]
        ))

        # Return venue details as a dict
        venue_details = {
            'request_form_note': request_form_note,
            'support_group_id': support_group_id,
            'venue_id': 'TEST.cc/2030/Conference'
        }
        return venue_details

    def test_venue_setup(self, client):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        venue = VenueRequest(client, support_group_id=support_group_id, super_user='openreview.net')

        assert venue.support_group.id == support_group_id
        assert venue.bid_stage_super_invitation
        assert venue.decision_stage_super_invitation
        assert venue.meta_review_stage_super_invitation
        assert venue.review_stage_super_invitation
        assert venue.submission_revision_stage_super_invitation
        assert venue.official_comment_stage_super_invitation

        assert venue.deploy_super_invitation
        assert venue.comment_super_invitation
        assert venue.recruitment_super_invitation
        assert venue.venue_revision_invitation

    def test_venue_deployment(self, client, selenium, request_page, helpers, support_client):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        VenueRequest(client, support_group_id, super_id)

        time.sleep(2)
        request_page(selenium, 'http://localhost:3030/group?id={}&mode=default'.format(support_group_id), client.token)

        helpers.create_user('new_test_user@mail.com', 'Newtest', 'User')

        support_group = client.get_group(support_group_id)
        client.add_members_to_group(group=support_group, members=['~Support_User1'])

        support_members = client.get_group(support_group_id).members
        assert support_members and len(support_members) == 1

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(minutes=30)

        request_form_note = client.post_note(openreview.Note(
            invitation=support_group_id +'/-/Request_Form',
            signatures=['~Newtest_User1'],
            readers=[
                support_group_id,
                '~Newtest_User1',
                'new_test_user@mail.com',
                'tom@mail.com'
            ],
            writers=[],
            content={
                'title': 'Test 2021 Venue',
                'Official Venue Name': 'Test 2021 Venue',
                'Abbreviated Venue Name': 'TestVenue@OR2021',
                'Official Website URL': 'https://testvenue2021.gitlab.io/venue/',
                'program_chair_emails': [
                    'new_test_user@mail.com',
                    'tom@mail.com'],
                'contact_email': 'new_test_user@mail.com',
                'Area Chairs (Metareviewers)': 'No, our venue does not have Area Chairs',
                'Venue Start Date': start_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'Paper Matching': [
                    'Reviewer Bid Scores',
                    'Reviewer Recommendation Scores'],
                'Author and Reviewer Anonymity': 'Single-blind (Reviewers are anonymous)',
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'Public Commentary': 'Yes, allow members of the public to comment non-anonymously.',
                'withdrawn_submissions_visibility': 'No, withdrawn submissions should not be made public.',
                'withdrawn_submissions_author_anonymity': 'No, author identities of withdrawn submissions should not be revealed.',
                'email_pcs_for_withdrawn_submissions': 'Yes, email PCs.',
                'desk_rejected_submissions_visibility': 'No, desk rejected submissions should not be made public.',
                'desk_rejected_submissions_author_anonymity': 'No, author identities of desk rejected submissions should not be revealed.',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
            }))

        assert request_form_note
        request_page(selenium, 'http://localhost:3030/forum?id=' + request_form_note.forum, client.token)

        messages = client.get_messages(
            to='new_test_user@mail.com',
            subject='Your request for OpenReview service has been received.')
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'] == 'Thank you for choosing OpenReview to host your upcoming venue. We are reviewing your request and will post a comment on the request forum when the venue is deployed. You can access the request forum here: https://openreview.net/forum?id=' + request_form_note.forum

        messages = client.get_messages(
            to='support_user@mail.com',
            subject='A request for service has been submitted'
        )
        assert messages and len(messages) == 1
        assert messages[0]['content']['text'].startswith('A request for service has been submitted. Check it here')

        # Test Deploy
        deploy_note = client.post_note(openreview.Note(
            content={'venue_id': 'TEST.cc/2021/Conference'},
            forum=request_form_note.forum,
            invitation='{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number),
            readers=[support_group_id],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=[support_group_id],
            writers=[support_group_id]
        ))
        assert deploy_note

        time.sleep(5)
        process_logs = client.get_process_logs(id=deploy_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Deploy'.format(support_group_id, request_form_note.number)

    def test_venue_revision(self, client, test_client, selenium, request_page, venue):

        # Test Revision
        request_page(selenium, 'http://localhost:3030/group?id={}'.format(venue['venue_id']), test_client.token)
        header_div = selenium.find_element_by_id('header')
        assert header_div
        title_tag = header_div.find_element_by_tag_name('h1')
        assert title_tag
        assert title_tag.text == venue['request_form_note'].content['title']

        messages = client.get_messages(subject='Comment posted to your request for service: {}'.format(venue['request_form_note'].content['title']))
        assert messages and len(messages) == 2
        recipients = [msg['content']['to'] for msg in messages]
        assert 'test@mail.com' in recipients
        assert 'tom@mail.com' in recipients
        assert 'Venue home page: https://openreview.net/group?id=TEST.cc/2030/Conference' in messages[0]['content']['text']
        assert 'Venue Program Chairs console: https://openreview.net/group?id=TEST.cc/2030/Conference/Program_Chairs' in messages[0]['content']['text']

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        venue_revision_note = test_client.post_note(openreview.Note(
            content={
                'title': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Official Venue Name': '{} Updated'.format(venue['request_form_note'].content['title']),
                'Abbreviated Venue Name': venue['request_form_note'].content['Abbreviated Venue Name'],
                'Official Website URL': venue['request_form_note'].content['Official Website URL'],
                'program_chair_emails': venue['request_form_note'].content['program_chair_emails'],
                'Expected Submissions': '100',
                'How did you hear about us?': 'ML conferences',
                'Location': 'Virtual',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Venue Start Date': start_date.strftime('%Y/%m/%d'),
                'contact_email': venue['request_form_note'].content['contact_email'],
                'remove_submission_options': ['pdf']
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~Test_User1'],
            writers=['~Test_User1']
        ))
        assert venue_revision_note

        time.sleep(5)
        process_logs = client.get_process_logs(id=venue_revision_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Revision'.format(venue['support_group_id'], venue['request_form_note'].number)

        request_page(selenium, 'http://localhost:3030/group?id={}'.format(venue['venue_id']), test_client.token)
        header_div = selenium.find_element_by_id('header')
        assert header_div
        title_tag = header_div.find_element_by_tag_name('h1')
        assert title_tag
        assert title_tag.text == '{} Updated'.format(venue['request_form_note'].content['title'])

    def test_venue_recruitment(self, client, test_client, selenium, request_page, venue):

        # Test Reviewer Recruitment
        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(venue['request_form_note'].id), test_client.token)
        recruitment_div = selenium.find_element_by_id('note_{}'.format(venue['request_form_note'].id))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Recruitment']

        reviewer_details = '''reviewer_candidate1@email.com, Reviewer One\nreviewer_candidate2@email.com, Reviewer Two'''
        recruitment_note = test_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'reviewer',
                'invitee_details': reviewer_details,
                'invitation_email_subject': '[' + venue['request_form_note'].content['Abbreviated Venue Name'] + '] Invitation to serve as {invitee_role}',
                'invitation_email_content': 'Dear {name},\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as {invitee_role}.\n\nACCEPT LINK:\n\n{accept_url}\n\nDECLINE LINK:\n\n{decline_url}\n\nCheers!\n\nProgram Chairs'
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~Test_User1'],
            writers=[]
        ))
        assert recruitment_note

        time.sleep(5)
        process_logs = client.get_process_logs(id=recruitment_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Recruitment'.format(venue['support_group_id'], venue['request_form_note'].number)

        messages = client.get_messages(to='reviewer_candidate1@email.com')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == '[TestVenue@OR2030] Invitation to serve as reviewer'
        assert messages[0]['content']['text'].startswith('Dear Reviewer One,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as reviewer.')

        messages = client.get_messages(to='reviewer_candidate2@email.com')
        assert messages and len(messages) == 1
        assert messages[0]['content']['subject'] == '[TestVenue@OR2030] Invitation to serve as reviewer'
        assert messages[0]['content']['text'].startswith('Dear Reviewer Two,\n\nYou have been nominated by the program chair committee of Theoretical Foundations of RL Workshop @ ICML 2020 to serve as reviewer.')

    def test_venue_bid_stage(self, client, test_client, selenium, request_page, helpers, venue):

        reviewer_client = helpers.create_user('venue_reviewer1@mail.com', 'Venue', 'Reviewer')

        reviewer_group_id = '{}/Reviewers'.format(venue['venue_id'])
        reviewer_group = client.get_group(reviewer_group_id)
        client.add_members_to_group(reviewer_group, '~Venue_Reviewer1')

        reviewer_url = 'http://localhost:3030/group?id={}#reviewer-tasks'.format(reviewer_group_id)
        request_page(selenium, reviewer_url, reviewer_client.token)
        with pytest.raises(NoSuchElementException):
            assert selenium.find_element_by_link_text('Reviewer Bid')

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)

        bid_stage_note = test_client.post_note(openreview.Note(
            content={
                'bid_start_date': start_date.strftime('%Y/%m/%d'),
                'bid_due_date': due_date.strftime('%Y/%m/%d')
            },
            forum=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            referent=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Bid_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            signatures=['~Test_User1'],
            writers=['~Test_User1']
        ))
        assert bid_stage_note

        time.sleep(5)
        process_logs = client.get_process_logs(id=bid_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['invitation'] == '{}/-/Request{}/Bid_Stage'.format(venue['support_group_id'], venue['request_form_note'].number)
        assert process_logs[0]['status'] == 'ok'

        request_page(selenium, reviewer_url, reviewer_client.token)
        assert selenium.find_element_by_link_text('Reviewer Bid')

    def test_venue_review_stage(self, client, test_client, selenium, request_page, helpers, venue):

        author_client = helpers.create_user('venue_author1@mail.com', 'Venue', 'Author')
        reviewer_client = helpers.create_user('venue_reviewer2@mail.com', 'Venue', 'Reviewer')

        submission = author_client.post_note(openreview.Note(
            invitation='{}/-/Submission'.format(venue['venue_id']),
            readers=[
                venue['venue_id'],
                '~Venue_Author1'],
            writers=[
                '~Venue_Author1',
                venue['venue_id']
            ],
            signatures=['~Venue_Author1'],
            content={
                'title': 'test submission',
                'authorids': ['~Venue_Author1'],
                'authors': ['Venue Author'],
                'abstract': 'test abstract'
            }
        ))

        assert submission

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        conference.create_blind_submissions(force=True)

        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']))
        assert blind_submissions and len(blind_submissions) == 1

        # Post a review stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        review_stage_note = test_client.post_note(openreview.Note(
            content={
                'review_start_date': start_date.strftime('%Y/%m/%d'),
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                'email_program_chairs_about_reviews': 'Yes, email program chairs for each review received'
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Review_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~Test_User1'],
            writers=['~Test_User1']
        ))
        assert review_stage_note
        time.sleep(5)

        process_logs = client.get_process_logs(id = review_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        reviewer_group = client.get_group('{}/Reviewers'.format(venue['venue_id']))
        client.add_members_to_group(reviewer_group, '~Venue_Reviewer2')

        openreview.tools.add_assignment(client, paper_number=1, conference=venue['venue_id'], reviewer='~Venue_Reviewer2')

        reviewer_group = client.get_group('{}/Reviewers'.format(venue['venue_id']))
        assert reviewer_group and len(reviewer_group.members) == 2

        reviewer_page_url = 'http://localhost:3030/group?id={}/Reviewers#assigned-papers'.format(venue['venue_id'])
        request_page(selenium, reviewer_page_url, token=reviewer_client.token)

        note_div = selenium.find_element_by_id('note-summary-1')
        assert note_div
        assert 'test submission' == note_div.find_element_by_link_text('test submission').text

        review_invitations = client.get_invitations(regex='{}/Paper[0-9]*/-/Official_Review$'.format(venue['venue_id']))
        assert review_invitations and len(review_invitations) == 1

    def test_venue_official_comment_stage(self, client, test_client, selenium, request_page, helpers, venue):

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']))
        assert blind_submissions and len(blind_submissions) == 1

        # Post an official comment stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        official_comment_stage_note = test_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'allow_unsubmitted_reviewers_to_comment': 'Yes, unsubmitted reviewers should be able to post official comments',
                'allow_reader_selection': 'No, comment authors should not be able to select comment readers',
                'email_program_chairs_about_official_reviews': 'Yes, email PCs for each official comment made in the venue',
                'allow_authors_to_comment': 'Yes, allow submission authors to post official comments on their own papers'
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Official_Comment_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~Test_User1'],
            writers=['~Test_User1']
        ))
        assert official_comment_stage_note
        time.sleep(5)

        process_logs = client.get_process_logs(id=official_comment_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        forum_note = blind_submissions[0]
        official_comment_note = client.post_note(openreview.Note(
            invitation=conference.get_invitation_id('Official_Comment', number=forum_note.number),
            readers=[
                conference.get_program_chairs_id(),
                conference.get_area_chairs_id(number=forum_note.number),
                conference.get_reviewers_id(number=forum_note.number) + '/Submitted'
            ],
            writers=[
                conference.get_id() + '/Paper{}/AnonReviewer1'.format(forum_note.number),
                conference.get_id()],
            signatures=[conference.get_id() + '/Paper{}/AnonReviewer1'.format(forum_note.number)],
            forum=forum_note.forum,
            replyto=forum_note.forum,
            content={
                'comment': 'test comment',
                'title': 'test official comment title'
            }
        ))
        assert official_comment_note

    def test_venue_meta_review_stage(self, client, test_client, selenium, request_page, helpers, venue):

        author_client = helpers.create_user('venue_author2@mail.com', 'Venue', 'Author')
        meta_reviewer_client = helpers.create_user('venue_ac1@mail.com', 'Venue', 'Ac')

        submission = author_client.post_note(openreview.Note(
            invitation='{}/-/Submission'.format(venue['venue_id']),
            readers=[
                venue['venue_id'],
                '~Venue_Author2'],
            writers=[
                '~Venue_Author2',
                venue['venue_id']
            ],
            signatures=['~Venue_Author2'],
            content={
                'title': 'test submission 2',
                'authorids': ['~Venue_Author2'],
                'authors': ['Venue Author'],
                'abstract': 'test abstract 2'
            }
        ))
        assert submission

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        conference.create_blind_submissions(force=True)

        blind_submissions = client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']))
        assert blind_submissions and len(blind_submissions) == 2

        # Assert that ACs do not see the Submit button for meta reviews at this point
        meta_reviewer_group = client.get_group('{}/Area_Chairs'.format(venue['venue_id']))
        client.add_members_to_group(meta_reviewer_group, '~Venue_Ac1')

        openreview.tools.add_assignment(client, paper_number=1, conference=venue['venue_id'], reviewer='~Venue_Ac1', parent_label='Area_Chairs', individual_label='Area_Chair')
        openreview.tools.add_assignment(client, paper_number=2, conference=venue['venue_id'], reviewer='~Venue_Ac1', parent_label='Area_Chairs', individual_label='Area_Chair')

        ac_group = client.get_group('{}/Area_Chairs'.format(venue['venue_id']))
        assert ac_group and len(ac_group.members) == 1

        ac_page_url = 'http://localhost:3030/group?id={}/Area_Chairs'.format(venue['venue_id'])
        request_page(selenium, ac_page_url, token=meta_reviewer_client.token)

        submit_div_1 = selenium.find_element_by_id('1-metareview-status')
        with pytest.raises(NoSuchElementException):
            assert submit_div_1.find_element_by_link_text('Submit')

        submit_div_2 = selenium.find_element_by_id('2-metareview-status')
        with pytest.raises(NoSuchElementException):
            assert submit_div_2.find_element_by_link_text('Submit')

        # Post a meta review stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        meta_review_stage_note = test_client.post_note(openreview.Note(
            content={
                'make_meta_reviews_public': 'No, meta reviews should NOT be revealed publicly when they are posted',
                'meta_review_start_date': start_date.strftime('%Y/%m/%d'),
                'meta_review_deadline': due_date.strftime('%Y/%m/%d')
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Meta_Review_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~Test_User1'],
            writers=['~Test_User1']
        ))
        assert meta_review_stage_note
        time.sleep(5)

        process_logs = client.get_process_logs(id = meta_review_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        # Assert that AC now see the Submit button for assigned papers
        request_page(selenium, ac_page_url, token=meta_reviewer_client.token)

        note_div_1 = selenium.find_element_by_id('note-summary-1')
        assert note_div_1
        note_div_2 = selenium.find_element_by_id('note-summary-2')
        assert note_div_2
        assert 'test submission' == note_div_1.find_element_by_link_text('test submission').text
        assert 'test submission 2' == note_div_2.find_element_by_link_text('test submission 2').text

        submit_div_1 = selenium.find_element_by_id('1-metareview-status')
        assert submit_div_1.find_element_by_link_text('Submit')

        submit_div_2 = selenium.find_element_by_id('2-metareview-status')
        assert submit_div_2.find_element_by_link_text('Submit')

    def test_venue_decision_stage(self, client, test_client, selenium, request_page, venue):

        # Assert that PCs do not see a Decision button on the submissions
        submissions = test_client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']))
        assert submissions and len(submissions) == 2

        paper_url = 'http://localhost:3030/forum?id={}'.format(submissions[0].forum)
        request_page(selenium, paper_url, token=test_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert reply_row
        with pytest.raises(NoSuchElementException):
            assert 'Decision' == reply_row.find_element_by_class_name('btn-xs').text

        # Post a decision stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        decision_stage_note = test_client.post_note(openreview.Note(
            content={
                'decision_start_date': start_date.strftime('%Y/%m/%d'),
                'decision_deadline': due_date.strftime('%Y/%m/%d'),
                'make_decisions_public': 'No, decisions should NOT be revealed publicly when they are posted',
                'release_decisions_to_authors': 'No, decisions should NOT be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'No, decisions should not be immediately revealed to the paper\'s reviewers',
                'notify_authors': 'No, I will send the emails to the authors'
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Decision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~Test_User1'],
            writers=['~Test_User1']
        ))
        assert decision_stage_note
        time.sleep(5)

        process_logs = client.get_process_logs(id = decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        # Assert that PC now sees the Decision button
        request_page(selenium, paper_url, token=test_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert reply_row
        assert 'Decision' == reply_row.find_element_by_class_name('btn-xs').text

        submissions = test_client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']))
        assert submissions and len(submissions) == 2

        # Post a decision note using pc test_client
        submission = submissions[0]
        program_chairs = '{}/Program_Chairs'.format(venue['venue_id'])
        area_chairs = '{}/Paper{}/Area_Chairs'.format(venue['venue_id'], submission.number)
        decision_note = test_client.post_note(openreview.Note(
            invitation='{}/Paper{}/-/Decision'.format(venue['venue_id'], submission.number),
            writers=[program_chairs],
            readers=[program_chairs, area_chairs],
            nonreaders=['{}/Paper{}/Authors'.format(venue['venue_id'], submission.number)],
            signatures=[program_chairs],
            content={
                'title': 'Paper Decision',
                'decision': 'Accept (Oral)',
                'comment':  'Good paper. I like!'
            },
            forum=submission.forum,
            replyto=submission.forum
        ))

        assert decision_note
        time.sleep(5)

        process_logs = client.get_process_logs(id = decision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

    def test_venue_submission_revision_stage(self, client, test_client, selenium, request_page, helpers, venue):

        author_client = helpers.create_user('venue_author3@mail.com', 'Venue', 'Author')
        submission = author_client.post_note(openreview.Note(
            invitation='{}/-/Submission'.format(venue['venue_id']),
            readers=[
                venue['venue_id'],
                '~Venue_Author3'
            ],
            writers=[
                '~Venue_Author3',
                venue['venue_id']
            ],
            signatures=['~Venue_Author3'],
            content={
                'title': 'test submission 3',
                'authorids': ['~Venue_Author3'],
                'authors': ['Venue Author'],
                'abstract': 'test abstract 3'
            }
        ))

        assert submission

        conference = openreview.get_conference(client, request_form_id=venue['request_form_note'].forum)
        conference.create_blind_submissions(force=True)

        blind_submissions = author_client.get_notes(
            invitation='{}/-/Blind_Submission'.format(venue['venue_id']))
        assert blind_submissions and len(blind_submissions) == 1

        # Post a revision stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        revision_stage_note = test_client.post_note(openreview.Note(
            content={
                'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for all submissions',
                'submission_revision_remove_options': ['keywords', 'pdf']
            },
            forum=venue['request_form_note'].forum,
            invitation='{}/-/Request{}/Submission_Revision_Stage'.format(venue['support_group_id'], venue['request_form_note'].number),
            readers=['{}/Program_Chairs'.format(venue['venue_id']), venue['support_group_id']],
            referent=venue['request_form_note'].forum,
            replyto=venue['request_form_note'].forum,
            signatures=['~Test_User1'],
            writers=['~Test_User1']
        ))
        assert revision_stage_note

        time.sleep(5)
        process_logs = client.get_process_logs(id=revision_stage_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        blind_submissions = author_client.get_notes(invitation='{}/-/Blind_Submission'.format(venue['venue_id']))

        author_page_url = 'http://localhost:3030/forum?id={}'.format(blind_submissions[0].forum)
        print('checkig url: {}'.format(author_page_url))
        request_page(selenium, author_page_url, token=author_client.token)

        meta_actions = selenium.find_element_by_class_name('meta_actions')
        assert meta_actions
        assert 'Revision' == meta_actions.find_element_by_class_name('edit_button').text

        # Post revision note for a submission
        revision_note = author_client.post_note(openreview.Note(
            invitation='{}/Paper{}/-/Revision'.format(venue['venue_id'], blind_submissions[0].number),
            forum=blind_submissions[0].original,
            referent=blind_submissions[0].original,
            replyto=blind_submissions[0].original,
            readers=[venue['venue_id'], '~Venue_Author3'],
            writers=['~Venue_Author3', venue['venue_id']],
            signatures=['~Venue_Author3'],
            content={
                'title': 'revised test submission 3',
                'abstract': 'revised abstract 3',
                'authors': ['Venue Author'],
                'authorids': ['~Venue_Author3']
            }
        ))
        assert revision_note

        time.sleep(5)
        process_logs = client.get_process_logs(id=revision_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        updated_note = author_client.get_note(id=blind_submissions[0].forum)
        assert updated_note
        assert updated_note.content['title'] == 'revised test submission 3'
        assert updated_note.content['abstract'] == 'revised abstract 3'
        assert updated_note.content['authors'] == blind_submissions[0].content['authors']
        assert updated_note.content['authorids'] == blind_submissions[0].content['authorids']

        messages = client.get_messages(subject='{} has received a new revision of your submission titled revised test submission 3'.format(venue['request_form_note'].content['Abbreviated Venue Name']))
        assert messages and len(messages) == 1
        assert messages[0]['content']['to'] == 'venue_author3@mail.com'
