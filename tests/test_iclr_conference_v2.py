import time
import openreview
import pytest
import datetime
import re
import random
import os
import csv
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class TestICLRConference():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        abstract_date = now + datetime.timedelta(days=1)
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        helpers.create_user('pc@iclr.cc', 'Program', 'ICLRChair')
        pc_client = openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)


        helpers.create_user('sac10@gmail.com', 'SAC', 'ICLROne')
        helpers.create_user('sac2@iclr.cc', 'SAC', 'ICLRTwo')
        helpers.create_user('ac1@iclr.cc', 'AC', 'ICLROne')
        helpers.create_user('ac2@iclr.cc', 'AC', 'ICLRTwo')
        helpers.create_user('reviewer1@iclr.cc', 'Reviewer', 'ICLROne')
        helpers.create_user('reviewer2@iclr.cc', 'Reviewer', 'ICLRTwo')
        helpers.create_user('reviewer3@iclr.cc', 'Reviewer', 'ICLRThree')
        helpers.create_user('reviewer4@gmail.com', 'Reviewer', 'ICLRFour')
        helpers.create_user('reviewer5@gmail.com', 'Reviewer', 'ICLRFive')
        helpers.create_user('reviewer6@gmail.com', 'Reviewer', 'ICLRSix')
        helpers.create_user('reviewerethics@gmail.com', 'Reviewer', 'ICLRSeven')
        helpers.create_user('peter@mail.com', 'Peter', 'SomeLastName') # Author

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_ICLRChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_ICLRChair1'
            ],
            writers=[],
            content={
                'title': 'International Conference on Learning Representations',
                'Official Venue Name': 'International Conference on Learning Representations',
                'Abbreviated Venue Name': 'ICLR 2024',
                'Official Website URL': 'https://iclr.cc',
                'program_chair_emails': ['pc@iclr.cc'],
                'contact_email': 'pc@iclr.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'Venue Start Date': '2024/07/01',
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be public.',
                'submission_readers': 'Everyone (submissions are public)',
                'withdrawn_submissions_visibility': 'Yes, withdrawn submissions should be made public.',
                'withdrawn_submissions_author_anonymity': 'Yes, author identities of withdrawn submissions should be revealed.',
                'desk_rejected_submissions_visibility':'Yes, desk rejected submissions should be made public.',
                'desk_rejected_submissions_author_anonymity':'Yes, author identities of desk rejected submissions should be revealed.',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'submission_license': ['CC BY 4.0', 'CC BY-SA 4.0', 'CC0 1.0'] # Allow authors to select license
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'ICLR.cc/2024/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        venue_group = openreview_client.get_group('ICLR.cc/2024/Conference')
        assert venue_group
        assert venue_group.content['date']['value'] == f'Abstract Registration: {abstract_date.strftime("%b %d %Y")} 12:00AM UTC-0, Submission Deadline: {due_date.strftime("%b %d %Y")} 12:00AM UTC-0'
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Senior_Area_Chairs')
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Area_Chairs')
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers')
        assert openreview_client.get_group('ICLR.cc/2024/Conference/Authors')

        submission_invitation = openreview_client.get_invitation('ICLR.cc/2024/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('ICLR.cc/2024/Conference/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2024/Conference/Area_Chairs/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2024/Conference/Senior_Area_Chairs/-/Expertise_Selection')
        assert not openreview.tools.get_invitation(openreview_client, 'ICML.cc/2023/Conference/-/Preferred_Emails')

    def test_reviewer_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        pc_client=openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        reviewer_details = '''reviewer1@iclr.cc, Reviewer ICLROne\nreviewer2@iclr.cc, Reviewer ICLRTwo'''
        pc_client.post_note(openreview.Note(
            content={
                'title': 'Recruitment',
                'invitee_role': 'Reviewers',
                'invitee_details': reviewer_details,
                'allow_accept_with_reduced_load': 'Yes',
                'invitee_reduced_load': ["1", "2", "3"],
                'invitation_email_subject': '[ICLR 2024] Invitation to serve as {{invitee_role}}',
                'invitation_email_content': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of International Conference on Learning Representations @ ICLR 2024 to serve as {{invitee_role}}.\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
            },
            forum=request_form.forum,
            replyto=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Recruitment'.format(request_form.number),
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers').members) == 0
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Invited').members) == 2
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Declined').members) == 0

        messages = openreview_client.get_messages(subject = '[ICLR 2024] Invitation to serve as Reviewer')
        assert len(messages) == 2

        # Accept invitation with reduced load
        for message in messages:
            text = message['content']['text']
            invitation_url = re.search('https://.*\n', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
            helpers.respond_invitation(selenium, request_page, invitation_url, accept=True, quota=3)

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2024/Conference/Reviewers/-/Recruitment', count=2)

        messages = openreview_client.get_messages(subject='[ICLR 2024] Reviewer Invitation accepted with reduced load')
        assert len(messages) == 2

        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers').members) == 2
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Invited').members) == 2
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Declined').members) == 0

        # Decline invitation
        messages = openreview_client.get_messages(to='reviewer1@iclr.cc', subject='[ICLR 2024] Invitation to serve as Reviewer')
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=False)

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2024/Conference/Reviewers/-/Recruitment', count=3)

        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers').members) == 1
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Invited').members) == 2
        assert len(openreview_client.get_group('ICLR.cc/2024/Conference/Reviewers/Declined').members) == 1

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer2@iclr.cc', password=helpers.strong_password)

        request_page(selenium, "http://localhost:3030/group?id=ICLR.cc/2024/Conference/Reviewers", reviewer_client.token, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'You have agreed to review up to 1 submission' in header.text

    def test_submissions(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,12):
            note = openreview.api.Note(
                license = 'CC BY-SA 4.0',
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                }
            )
            if i == 1 or i == 11:
                note.content['authors']['value'].append('SAC ICLROne')
                note.content['authorids']['value'].append('~SAC_ICLROne1')

            test_client.post_note_edit(invitation='ICLR.cc/2024/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2024/Conference/-/Submission', count=11)

        submissions = openreview_client.get_notes(invitation='ICLR.cc/2024/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 11
        assert ['ICLR.cc/2024/Conference', '~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ICLROne1'] == submissions[0].readers
        assert ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com', '~SAC_ICLROne1'] == submissions[0].content['authorids']['value']

        # Check that note.license is from license list
        licenses = request_form.content['submission_license']
        assert submissions[0].license in licenses

        authors_group = openreview_client.get_group(id='ICLR.cc/2024/Conference/Authors')

        for i in range(1,12):
            assert f'ICLR.cc/2024/Conference/Submission{i}/Authors' in authors_group.members

    def test_post_submission(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        venue = openreview.get_conference(client, request_form.id, support_user='openreview.net/Support')

        ## close abstract submission
        now = datetime.datetime.utcnow()
        abstract_date = now - datetime.timedelta(minutes=28)
        due_date = now + datetime.timedelta(days=3)        
        pc_client.post_note(openreview.Note(
            content={
                'title': 'International Conference on Learning Representations',
                'Official Venue Name': 'International Conference on Learning Representations',
                'Abbreviated Venue Name': 'ICLR 2024',
                'Official Website URL': 'https://iclr.cc',
                'program_chair_emails': ['pc@iclr.cc', 'pc3@iclr.cc'],
                'contact_email': 'pc@iclr.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2024/07/01',
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Post_Submission-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Desk_Rejection-0-1', count=1)

        pc_client_v2=openreview.api.OpenReviewClient(username='pc@iclr.cc', password=helpers.strong_password)
        submission_invitation = pc_client_v2.get_invitation('ICLR.cc/2024/Conference/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(now)

        submissions = pc_client_v2.get_notes(invitation='ICLR.cc/2024/Conference/-/Submission', sort='number:asc')
        submission = submissions[0]
        assert len(submissions) == 11
        assert submission.license == 'CC BY-SA 4.0'
        assert submission.readers == ['everyone']
        assert '_bibtex' in submission.content
        assert 'author={Anonymous}' in submission.content['_bibtex']['value']

        # Author revises submission license
        author_client = openreview.api.OpenReviewClient(username='peter@mail.com', password=helpers.strong_password)
        revision_note = author_client.post_note_edit(
            invitation = f'ICLR.cc/2024/Conference/Submission{submission.number}/-/Full_Submission',
            signatures = [f'ICLR.cc/2024/Conference/Submission{submission.number}/Authors'],
            note = openreview.api.Note(
                license = 'CC0 1.0',
                content = {
                    'title': { 'value': submission.content['title']['value'] + ' license revision' },
                    'abstract': submission.content['abstract'],
                    'authorids': { 'value': submission.content['authorids']['value'] },
                    'authors': { 'value': submission.content['authors']['value'] },
                    'keywords': submission.content['keywords'],
                    'pdf': submission.content['pdf'],
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=revision_note['id'])

        submission = pc_client_v2.get_notes(invitation='ICLR.cc/2024/Conference/-/Submission', sort='number:asc')[0]
        assert submission.license == 'CC0 1.0'
        
        # Assert that activation date of matching invitation == abstract deadline
        matching_invitation = client.get_invitation(f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup')
        abstract_date_midnight = datetime.datetime.combine(abstract_date, datetime.datetime.min.time())
        abstract_date_ms = abstract_date_midnight.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000
        assert matching_invitation.cdate == abstract_date_ms

        ## close full paper submission
        now = datetime.datetime.utcnow()
        abstract_date = now - datetime.timedelta(days=2)
        due_date = now - datetime.timedelta(minutes=28)        
        pc_client.post_note(openreview.Note(
            content={
                'title': 'International Conference on Learning Representations',
                'Official Venue Name': 'International Conference on Learning Representations',
                'Abbreviated Venue Name': 'ICLR 2024',
                'Official Website URL': 'https://iclr.cc',
                'program_chair_emails': ['pc@iclr.cc', 'pc3@iclr.cc'],
                'contact_email': 'pc@iclr.cc',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2024/07/01',
                'abstract_registration_deadline': abstract_date.strftime('%Y/%m/%d'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Post_Submission-0-1', count=3)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Withdrawal-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2024/Conference/-/Desk_Rejection-0-1', count=2)

        # Author can't revise license after paper deadline
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation ICLR.cc/2024/Conference/Submission1/-/Full_Submission has expired'):
            revision_note = author_client.post_note_edit(
                invitation = f'ICLR.cc/2024/Conference/Submission{submission.number}/-/Full_Submission',
                signatures = [f'ICLR.cc/2024/Conference/Submission{submission.number}/Authors'],
                note = openreview.api.Note(
                    license = 'CC BY 4.0',
                    content = {
                        'title': submission.content['title'],
                        'abstract': submission.content['abstract'],
                        'authorids': { 'value': submission.content['authorids']['value'] },
                        'authors': { 'value': submission.content['authors']['value'] },
                        'keywords': submission.content['keywords'],
                        'pdf': submission.content['pdf'],
                    }
                ))

        # PC revises submission license
        pc_revision = pc_client_v2.post_note_edit(
            invitation='ICLR.cc/2024/Conference/-/PC_Revision',
            signatures=['ICLR.cc/2024/Conference/Program_Chairs'],
            note=openreview.api.Note(
                id = submission.id,
                license = 'CC BY 4.0',
                content = {
                    'title': submission.content['title'],
                    'abstract': submission.content['abstract'],
                    'authorids': { 'value': submission.content['authorids']['value'] },
                    'authors': { 'value': submission.content['authors']['value'] },
                    'keywords': submission.content['keywords'],
                    'pdf': submission.content['pdf'],
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=pc_revision['id'])

        submission = pc_client_v2.get_notes(invitation='ICLR.cc/2024/Conference/-/Submission', sort='number:asc')[0]
        assert submission.license == 'CC BY 4.0'

    def test_review_stage(self, client, openreview_client, helpers, test_client):

        openreview_client.add_members_to_group('ICLR.cc/2024/Conference/Submission1/Reviewers', ['~Reviewer_ICLROne1', '~Reviewer_ICLRTwo1', '~Reviewer_ICLRThree1'])

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        pc_client=openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]
        review_stage_note=pc_client.post_note(openreview.Note(
            content={
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))
        helpers.await_queue()

        invitation = openreview_client.get_invitation('ICLR.cc/2024/Conference/Submission1/-/Official_Review')

        reviewer_client=openreview.api.OpenReviewClient(username='reviewer1@iclr.cc', password=helpers.strong_password)

        anon_groups = reviewer_client.get_groups(prefix='ICLR.cc/2024/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICLROne1')
        anon_group_id = anon_groups[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='ICLR.cc/2024/Conference/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Good paper, accept'},
                    'review': { 'value': 'Excellent paper, accept'},
                    'rating': { 'value': 10},
                    'confidence': { 'value': 5},
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])        

    def test_submission_withdrawal(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        withdraw_note = test_client.post_note_edit(invitation='ICLR.cc/2024/Conference/Submission11/-/Withdrawal',
                                    signatures=['ICLR.cc/2024/Conference/Submission11/Authors'],
                                    note=openreview.api.Note(
                                        content={
                                            'withdrawal_confirmation': { 'value': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=withdraw_note['id'])

        note = test_client.get_note(withdraw_note['note']['forum'])
        assert note
        assert note.invitations == ['ICLR.cc/2024/Conference/-/Submission', 'ICLR.cc/2024/Conference/-/Post_Submission', 'ICLR.cc/2024/Conference/-/Withdrawn_Submission']
        assert note.readers == ['everyone']
        assert note.writers == ['ICLR.cc/2024/Conference', 'ICLR.cc/2024/Conference/Submission11/Authors']
        assert note.signatures == ['ICLR.cc/2024/Conference/Submission11/Authors']
        assert note.content['venue']['value'] == 'ICLR 2024 Conference Withdrawn Submission'
        assert note.content['venueid']['value'] == 'ICLR.cc/2024/Conference/Withdrawn_Submission'
        assert 'readers' not in note.content['authors']
        assert 'readers' not in note.content['authorids']

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2024/Conference/-/Withdrawn_Submission')

        pc_openreview_client = openreview.api.OpenReviewClient(username='pc@iclr.cc', password=helpers.strong_password)

        # reverse withdrawal
        withdrawal_reversion_note = pc_openreview_client.post_note_edit(invitation='ICLR.cc/2024/Conference/Submission11/-/Withdrawal_Reversion',
                                    signatures=['ICLR.cc/2024/Conference/Program_Chairs'],
                                    note=openreview.api.Note(
                                        content={
                                            'revert_withdrawal_confirmation': { 'value': 'We approve the reversion of withdrawn submission.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=withdrawal_reversion_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2024/Conference/Submission11/-/Withdrawal_Reversion')

        #desk-reject paper
        desk_reject_note = pc_openreview_client.post_note_edit(invitation=f'ICLR.cc/2024/Conference/Submission11/-/Desk_Rejection',
                                    signatures=['ICLR.cc/2024/Conference/Program_Chairs'],
                                    note=openreview.api.Note(
                                        content={
                                            'desk_reject_comments': { 'value': 'Wrong format.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_reject_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2024/Conference/-/Desk_Rejected_Submission')

        note = test_client.get_note(desk_reject_note['note']['forum'])
        assert note
        assert note.invitations == ['ICLR.cc/2024/Conference/-/Submission', 
                                    'ICLR.cc/2024/Conference/-/Post_Submission', 
                                    'ICLR.cc/2024/Conference/-/Withdrawn_Submission', 
                                    'ICLR.cc/2024/Conference/-/Desk_Rejected_Submission']

        assert note.readers == ["everyone"]
        assert note.writers == ['ICLR.cc/2024/Conference', 'ICLR.cc/2024/Conference/Submission11/Authors']
        assert note.signatures == ['ICLR.cc/2024/Conference/Submission11/Authors']
        assert note.content['venue']['value'] == 'ICLR 2024 Conference Desk Rejected Submission'
        assert note.content['venueid']['value'] == 'ICLR.cc/2024/Conference/Desk_Rejected_Submission'
        assert 'readers' not in note.content['authors']
        assert 'readers' not in note.content['authorids']

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2024/Conference/-/Desk_Rejected_Submission')

    def test_comment_stage(self, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@iclr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        # Post an official comment stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        end_date = now + datetime.timedelta(days=3)
        comment_stage_note = pc_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'additional_readers': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Assigned Submitted Reviewers'],
                'email_program_chairs_about_official_comments': 'Yes, email PCs for each official comment made in the venue'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Comment_Stage',
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        invitation = openreview_client.get_invitation('ICLR.cc/2024/Conference/Submission1/-/Official_Comment')
        assert invitation.edit['signatures']['param']['items'] == [
            {
                "value": "ICLR.cc/2024/Conference/Program_Chairs",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Senior_Area_Chairs",
                "optional": True
            },
            {
                "prefix": "ICLR.cc/2024/Conference/Submission1/Area_Chair_.*",
                "optional": True
            },
            {
                "prefix": "ICLR.cc/2024/Conference/Submission1/Reviewer_.*",
                "optional": True
            }
        ]

        assert invitation.edit['note']['readers']['param']['items'] == [
            {
                "value": "ICLR.cc/2024/Conference/Program_Chairs",
                "optional": False
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Senior_Area_Chairs",
                "optional": False
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Area_Chairs",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Reviewers",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Reviewers/Submitted",
                "optional": True
            },
            {
                "prefix": "ICLR.cc/2024/Conference/Submission1/Reviewer_.*",
                "optional": True
            }
        ]

        # PC posts comment to Reviewers/Submitted, no email is sent to group
        submissions = openreview_client.get_notes(invitation='ICLR.cc/2024/Conference/-/Submission', sort='number:asc')
        official_comment_note = pc_client_v2.post_note_edit(
            invitation='ICLR.cc/2024/Conference/Submission2/-/Official_Comment',
            signatures=['ICLR.cc/2024/Conference/Program_Chairs'],
            note=openreview.api.Note(
                replyto=submissions[1].id,
                content={
                    'title': {'value': 'test comment title'},
                    'comment': {'value': 'test comment'}
                },
                readers=[
                    'ICLR.cc/2024/Conference/Program_Chairs',
                    'ICLR.cc/2024/Conference/Submission2/Senior_Area_Chairs',
                    'ICLR.cc/2024/Conference/Submission2/Reviewers/Submitted'
                ]
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=official_comment_note['id'])

        official_comment_notes = openreview_client.get_notes(invitation='ICLR.cc/2024/Conference/Submission2/-/Official_Comment')
        assert len(official_comment_notes) == 1
        assert 'ICLR.cc/2024/Conference/Submission2/Reviewers/Submitted' in official_comment_notes[0].readers

        messages = openreview_client.get_messages(subject='[ICLR 2024] Program Chairs commented on a paper.*')
        assert messages and len(messages) == 1
        assert messages[0]['content']['to'] == 'pc3@iclr.cc'

        ## allow public comments
        comment_stage_note = pc_client.post_note(openreview.Note(
            content={
                'commentary_start_date': start_date.strftime('%Y/%m/%d'),
                'commentary_end_date': end_date.strftime('%Y/%m/%d'),
                'participants': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers'],
                'additional_readers': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Assigned Submitted Reviewers', 'Authors', 'Public'],
                'email_program_chairs_about_official_comments': 'Yes, email PCs for each official comment made in the venue'
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Comment_Stage',
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        invitation = openreview_client.get_invitation('ICLR.cc/2024/Conference/Submission1/-/Official_Comment')

        assert invitation.edit['note']['readers']['param']['items'] == [
            {
                'value': 'everyone',
                'optional': True
            },
            {
                "value": "ICLR.cc/2024/Conference/Program_Chairs",
                "optional": False
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Senior_Area_Chairs",
                "optional": False
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Area_Chairs",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Reviewers",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Reviewers/Submitted",
                "optional": True
            },
            {
                "prefix": "ICLR.cc/2024/Conference/Submission1/Reviewer_.*",
                "optional": True
            },
            {
                "value": "ICLR.cc/2024/Conference/Submission1/Authors",
                "optional": True
            }
        ]

    def test_camera_ready_revision_stage(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@iclr.cc', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        decisions = ['Accept (Oral)', 'Accept (Poster)', 'Reject']
        comment = {
            'Accept (Oral)': 'Congratulations on your acceptance.',
            'Accept (Poster)': 'Congratulations on your acceptance.',
            'Reject': 'We regret to inform you...'
        }

        submissions = openreview_client.get_notes(invitation='ICLR.cc/2024/Conference/-/Submission', sort='number:asc')

        with open(os.path.join(os.path.dirname(__file__), 'data/ICML_decisions.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([submissions[0].number, 'Accept (Oral)', comment["Accept (Oral)"]])
            writer.writerow([submissions[1].number, 'Accept (Poster)', comment["Accept (Poster)"]])
            writer.writerow([submissions[2].number, 'Reject', comment["Reject"]])
            for submission in submissions[3:]:
                decision = random.choice(decisions)
                writer.writerow([submission.number, decision, comment[decision]])

        decision_stage_invitation = f'openreview.net/Support/-/Request{request_form.number}/Decision_Stage'
        url = pc_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/ICML_decisions.csv'),
                                         decision_stage_invitation, 'decisions_file')

        ## enable decision stage
        now = datetime.datetime.utcnow()
        end_date = now + datetime.timedelta(days=3)
        decision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'decision_deadline': end_date.strftime('%Y/%m/%d'),
                'make_decisions_public': "No, decisions should NOT be revealed publicly when they are posted",
                'release_decisions_to_authors': 'Yes, decisions should be revealed when they are posted to the paper\'s authors',
                'release_decisions_to_reviewers': 'Yes, decisions should be immediately revealed to the paper\'s reviewers',
                'release_decisions_to_area_chairs': 'Yes, decisions should be immediately revealed to the paper\'s area chairs',
                'decisions_file': url
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Decision_Stage',
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))

        helpers.await_queue()

        invitation = client.get_invitation(f'openreview.net/Support/-/Request{request_form.number}/Post_Decision_Stage')
        invitation.cdate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        client.post_invitation(invitation)

        # Post revision stage note before releasing authors to the public
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=5)
        revision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'submission_revision_name': 'Camera_Ready_Revision',
                'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for accepted submissions only',
                'submission_author_edition': 'Allow reorder of existing authors only',
                'submission_revision_additional_options': {
                    "submission_type": {
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Regular Long Paper",
                                    "Regular Short Paper"
                                ],
                                "input": "select"
                            }
                        },
                        "description": "Please enter the category under which the submission should be reviewed. This cannot be changed after the abstract submission deadline.",
                        "order": 20
                    }
                },
                'submission_revision_remove_options': ['keywords']
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Submission_Revision_Stage',
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))
        assert revision_stage_note
        helpers.await_queue()

        invitation = openreview_client.get_invitation('ICLR.cc/2024/Conference/Submission1/-/Camera_Ready_Revision')
        assert invitation
        assert 'authorids' in invitation.edit['note']['content']
        assert 'readers' in invitation.edit['note']['content']['authorids']

        # post a post decision stage note
        short_name = 'ICLR 2024'
        post_decision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'reveal_authors': 'Reveal author identities of only accepted submissions to the public',
                'submission_readers': 'Everyone (submissions are public)',
                'home_page_tab_names': {
                    'Accept (Oral)': 'Accept (Oral)',
                    'Accept (Poster)': 'Accept (Poster)',
                    'Reject': 'Submitted'
                },
                'send_decision_notifications': 'No, I will send the emails to the authors',
                'accept_(oral)_email_content': f'''Dear {{{{fullname}}}},

Thank you for submitting your paper, {{{{submission_title}}}}, to {short_name}. We are delighted to inform you that your submission has been accepted. Congratulations!
You can find the final reviews for your paper on the submission page in OpenReview at: {{{{forum_url}}}}

Best,
{short_name} Program Chairs
''',
                'accept_(poster)_email_content': f'''Dear {{{{fullname}}}},

Thank you for submitting your paper, {{{{submission_title}}}}, to {short_name}. We are delighted to inform you that your submission has been accepted. Congratulations!
You can find the final reviews for your paper on the submission page in OpenReview at: {{{{forum_url}}}}

Best,
{short_name} Program Chairs
''',
                'reject_email_content': f'''Dear {{{{fullname}}}},

Thank you for submitting your paper, {{{{submission_title}}}}, to {short_name}. We regret to inform you that your submission was not accepted.
You can find the final reviews for your paper on the submission page in OpenReview at: {{{{forum_url}}}}

Best,
{short_name} Program Chairs
'''
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Post_Decision_Stage',
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))
        assert post_decision_stage_note
        helpers.await_queue()

        # Post revision stage note
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=5)
        revision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'submission_revision_name': 'Camera_Ready_Revision',
                'submission_revision_start_date': start_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for accepted submissions only',
                'submission_author_edition': 'Allow reorder of existing authors only',
                'submission_revision_additional_options': {
                    "submission_type": {
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Regular Long Paper",
                                    "Regular Short Paper"
                                ],
                                "input": "select"
                            }
                        },
                        "description": "Please enter the category under which the submission should be reviewed. This cannot be changed after the abstract submission deadline.",
                        "order": 20
                    }
                },
                'submission_revision_remove_options': ['keywords']
            },
            forum=request_form.forum,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Submission_Revision_Stage',
            readers=['ICLR.cc/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_ICLRChair1'],
            writers=[]
        ))
        assert revision_stage_note
        helpers.await_queue()

        invitation = openreview_client.get_invitation('ICLR.cc/2024/Conference/Submission1/-/Camera_Ready_Revision')
        assert invitation
        assert 'authorids' in invitation.edit['note']['content']
        assert 'readers' not in invitation.edit['note']['content']['authorids']