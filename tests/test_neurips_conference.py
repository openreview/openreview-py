from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
import time
import os
import re
import csv
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

class TestNeurIPSConference():

    # @pytest.fixture(scope="class")
    # def conference(self, client):
    #     now = datetime.datetime.utcnow()
    #     builder = openreview.conference.ConferenceBuilder(client)
    #     assert builder, 'builder is None'

    #     builder.set_conference_id('NeurIPS.cc/2021/Conference')
    #     builder.set_conference_short_name('NeurIPS 2021')
    #     builder.has_area_chairs(True)
    #     builder.set_homepage_header({
    #         'title': 'Conference on Neural Information Processing Systems',
    #         'subtitle': 'NeurIPS 2021',
    #         'deadline': '',
    #         'date': 'Dec 04 2021',
    #         'website': 'https://neurips.cc',
    #         'location': 'Online',
    #         'instructions': '',
    #         'contact': 'pc@neurips.cc'
    #     })

    #     builder.set_expertise_selection_stage(due_date = now + datetime.timedelta(minutes = 10))
    #     builder.set_submission_stage(double_blind = True,
    #         public = True,
    #         due_date = now + datetime.timedelta(minutes = 10),
    #         second_due_date = now + datetime.timedelta(minutes = 20),
    #         withdrawn_submission_public=True,
    #         withdrawn_submission_reveal_authors=True,
    #         email_pcs_on_withdraw=False,
    #         desk_rejected_submission_public=True,
    #         desk_rejected_submission_reveal_authors=True,
    #         additional_fields={
    #             "one-sentence_summary": {
    #                 "description": "A short sentence describing your paper.",
    #                 "order": 5,
    #                 "value-regex": "[^\n]{0,250}",
    #                 "required": False
    #             },
    #             "pdf": {
    #                 "description": "Upload a PDF file that ends with .pdf. The maximum file size is 50MB. Note: optional before the abstract submission deadline.",
    #                 "order": 9,
    #                 "value-file": {
    #                     "fileTypes": [
    #                         "pdf"
    #                     ],
    #                     "size": 50
    #                 },
    #                 "required": False
    #             },
    #             "supplementary_material": {
    #                 "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
    #                 "order": 10,
    #                 "value-file": {
    #                     "fileTypes": [
    #                         "zip"
    #                     ],
    #                     "size": 100
    #                 },
    #                 "required": False
    #             },
    #             "code_of_ethics": {
    #                 "description": "See the ICLR Code of Ethics: https://iclr.cc/public/CodeOfEthics",
    #                 "order": 16,
    #                 "value-checkbox": "I acknowledge that I and all co-authors of this work have read and commit to adhering to the ICLR Code of Ethics",
    #                 "required": True
    #             }
    #         })

    #     conference = builder.get_result()
    #     conference.set_program_chairs(['pc@iclr.cc'])
    #     return conference

    def test_create_conference(self, client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        # Post the request form note
        pc_client=helpers.create_user('pc@neurips.cc', 'Program', 'NeurIPSChair')
        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_NeurIPSChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_NeurIPSChair1'
            ],
            writers=[],
            content={
                'title': 'Conference on Neural Information Processing Systems',
                'Official Venue Name': 'Conference on Neural Information Processing Systems',
                'Abbreviated Venue Name': 'NeurIPS 2021',
                'Official Website URL': 'https://neurips.cc',
                'program_chair_emails': ['pc@neurips.cc'],
                'contact_email': 'pc@neurips.cc',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'Venue Start Date': '2021/12/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'Paper Matching': [
                    'Reviewer Bid Scores',
                    'Reviewer Recommendation Scores'],
                'Author and Reviewer Anonymity': 'Double-blind',
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'NeurIPS.cc/2021/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert client.get_group('NeurIPS.cc/2021/Conference')

#     def test_recruit_reviewer(self, conference, client, helpers, selenium, request_page):

#         result = conference.recruit_reviewers(['iclr2021_one@mail.com',
#         'iclr2021_two@mail.com',
#         'iclr2021_three@mail.com',
#         'iclr2021_four@mail.com',
#         'iclr2021_five@mail.com',
#         'iclr2021_six@mail.com',
#         'iclr2021_seven@mail.com',
#         'iclr2021_one_alternate@mail.com'])

#         assert result
#         assert result.id == 'ICLR.cc/2021/Conference/Reviewers/Invited'
#         assert len(result.members) == 7
#         assert 'iclr2021_one@mail.com' in result.members
#         assert 'iclr2021_two@mail.com' in result.members
#         assert 'iclr2021_three@mail.com' in result.members
#         assert 'iclr2021_four@mail.com' in result.members
#         assert 'iclr2021_five@mail.com' in result.members
#         assert 'iclr2021_six@mail.com' in result.members
#         assert 'iclr2021_seven@mail.com' in result.members
#         assert 'iclr2021_one_alternate@mail.com' not in result.members

#         messages = client.get_messages(to = 'iclr2021_one@mail.com', subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         text = messages[0]['content']['text']
#         assert 'Dear invitee,' in text
#         assert 'You have been nominated by the program chair committee of ICLR 2021 to serve as reviewer' in text

#         reject_url = re.search('https://.*response=No', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')

#         request_page(selenium, reject_url, alert=True)
#         time.sleep(2)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 1
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 0

#         request_page(selenium, accept_url, alert=True)
#         time.sleep(2)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 0
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 1

#         messages = client.get_messages(to = 'iclr2021_two@mail.com', subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         text = messages[0]['content']['text']
#         assert 'Dear invitee,' in text
#         assert 'You have been nominated by the program chair committee of ICLR 2021 to serve as reviewer' in text

#         reject_url = re.search('https://.*response=No', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')

#         request_page(selenium, reject_url, alert=True)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 1
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 1

#         messages = client.get_messages(to = 'iclr2021_four@mail.com', subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         text = messages[0]['content']['text']
#         assert 'Dear invitee,' in text
#         assert 'You have been nominated by the program chair committee of ICLR 2021 to serve as reviewer' in text

#         reject_url = re.search('https://.*response=No', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')

#         request_page(selenium, accept_url, alert=True)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 1
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 2

#         messages = client.get_messages(to = 'iclr2021_five@mail.com', subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         text = messages[0]['content']['text']
#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
#         request_page(selenium, accept_url, alert=True)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 1
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 3

#         messages = client.get_messages(to = 'iclr2021_six_alternate@mail.com', subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         text = messages[0]['content']['text']
#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')
#         request_page(selenium, accept_url, alert=True)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 1
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 4

#     def test_registration(self, conference, helpers, selenium, request_page):

#         reviewer_client = openreview.Client(username='iclr2021_one@mail.com', password='1234')
#         reviewer_tasks_url = 'http://localhost:3030/group?id=ICLR.cc/2021/Conference/Reviewers#reviewer-tasks'
#         request_page(selenium, reviewer_tasks_url, reviewer_client.token)

#         assert selenium.find_element_by_link_text('Reviewer Registration')
#         assert selenium.find_element_by_link_text('Expertise Selection')

#         registration_notes = reviewer_client.get_notes(invitation = 'ICLR.cc/2021/Conference/Reviewers/-/Form')
#         assert registration_notes
#         assert len(registration_notes) == 1

#         registration_forum = registration_notes[0].forum

#         registration_note = reviewer_client.post_note(
#             openreview.Note(
#                 invitation = 'ICLR.cc/2021/Conference/Reviewers/-/Registration',
#                 forum = registration_forum,
#                 replyto = registration_forum,
#                 content = {
#                     'profile_confirmed': 'Yes',
#                     'expertise_confirmed': 'Yes',
#                     'TPMS_registration_confirmed': 'Yes',
#                     'reviewer_instructions_confirm': 'Yes',
#                     'emergency_review_count': '0'
#                 },
#                 signatures = [
#                     '~ReviewerOne_ICLR1'
#                 ],
#                 readers = [
#                     conference.get_id(),
#                     '~ReviewerOne_ICLR1'
#                 ],
#                 writers = [
#                     conference.get_id(),
#                     '~ReviewerOne_ICLR1'
#                 ]
#             ))
#         assert registration_note


#         request_page(selenium, 'http://localhost:3030/group?id=ICLR.cc/2021/Conference/Reviewers', reviewer_client.token)
#         header = selenium.find_element_by_id('header')
#         assert header
#         notes = header.find_elements_by_class_name("description")
#         assert notes
#         assert len(notes) == 1
#         assert notes[0].text == 'This page provides information and status updates for the ICLR 2021. It will be regularly updated as the conference progresses, so please check back frequently.'

#         request_page(selenium, reviewer_tasks_url, reviewer_client.token)

#         assert selenium.find_element_by_link_text('Reviewer Registration')
#         assert selenium.find_element_by_link_text('Expertise Selection')
#         tasks = selenium.find_element_by_id('reviewer-tasks')
#         assert tasks
#         assert len(tasks.find_elements_by_class_name('note')) == 2
#         assert len(tasks.find_elements_by_class_name('completed')) == 2

#     def test_remind_registration(self, conference, helpers, client):

#         five_reviewer_client = openreview.Client(username='iclr2021_five@mail.com', password='1234')
#         six_reviewer_client = openreview.Client(username='iclr2021_six_alternate@mail.com', password='1234')

#         subject = '[ICLR 2021] Please complete your profile'
#         message = '''
# Dear Reviewer,


# Thank you for accepting our invitation to serve on the program committee for ICLR 2021. The first task we ask of you is to complete your profile, which is essential in order for us to:

# - Assign you relevant submissions.

# - Identify gaps in reviewer expertise.


# To complete your profile, please log into OpenReview and navigate to the reviewer console(https://openreview.net/group?id=ICLR.cc/2021/Conference/Reviewers).
# There you will see a task to "Reviewer Registration". This task should not take more than 10-15 minutes.
# Please complete it by September 4th. Note that you will have to create an OpenReview account if you don’t already have one.


# Thanks again for your ongoing service to our community.


# ICLR2021 Programme Chairs,

# Naila, Katja, Alice, and Ivan
#         '''

#         reminders = conference.remind_registration_stage(subject, message, 'ICLR.cc/2021/Conference/Reviewers')
#         assert reminders
#         assert reminders == ['iclr2021_four@mail.com', 'iclr2021_five@mail.com', 'iclr2021_six@mail.com']

#         registration_notes = six_reviewer_client.get_notes(invitation = 'ICLR.cc/2021/Conference/Reviewers/-/Form')
#         assert registration_notes
#         assert len(registration_notes) == 1

#         registration_forum = registration_notes[0].forum

#         registration_note = six_reviewer_client.post_note(
#             openreview.Note(
#                 invitation = 'ICLR.cc/2021/Conference/Reviewers/-/Registration',
#                 forum = registration_forum,
#                 replyto = registration_forum,
#                 content = {
#                     'profile_confirmed': 'Yes',
#                     'expertise_confirmed': 'Yes',
#                     'TPMS_registration_confirmed': 'Yes',
#                     'reviewer_instructions_confirm': 'Yes',
#                     'emergency_review_count': '0'
#                 },
#                 signatures = [
#                     '~ReviewerSix_ICLR1'
#                 ],
#                 readers = [
#                     conference.get_id(),
#                     '~ReviewerSix_ICLR1'
#                 ],
#                 writers = [
#                     conference.get_id(),
#                     '~ReviewerSix_ICLR1'
#                 ]
#             ))

#         reminders = conference.remind_registration_stage(subject, message, 'ICLR.cc/2021/Conference/Reviewers')
#         assert reminders
#         assert reminders == ['iclr2021_four@mail.com', 'iclr2021_five@mail.com']


#     def test_retry_declined_reviewers(self, conference, helpers, client, selenium, request_page):

#         title = '[ICLR 2021] Please reconsider serving as a reviewer'
#         message = '''
# Dear Reviewer,


# Thank you for responding to our invitation to serve as a reviewer for ICLR 2021. We would still very much benefit from your expertise and wonder whether you would reconsider our invitation in light of the fact that we will guarantee you a maximum load of 3 papers.


# If you would now like to ACCEPT the invitation, please click on the following link:


# {accept_url}


# We would appreciate an answer by Friday September 4th (in 7 days).


# If you have any questions, please don’t hesitate to reach out to us at iclr2021programchairs@googlegroups.com.


# We do hope you will reconsider and we thank you as always for your ongoing service to our community.


# ICLR2021 Programme Chairs,

# Naila, Katja, Alice, and Ivan
#         '''

#         result = conference.recruit_reviewers(title=title, message=message, retry_declined=True)

#         messages = client.get_messages(subject = '[ICLR 2021] Please reconsider serving as a reviewer')
#         assert len(messages) == 1
#         assert messages[0]['content']['to'] == 'iclr2021_two@mail.com'
#         text = messages[0]['content']['text']

#         accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030')

#         request_page(selenium, accept_url, alert=True)
#         declined_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers/Declined')
#         assert len(declined_group.members) == 0
#         accepted_group = client.get_group(id='ICLR.cc/2021/Conference/Reviewers')
#         assert len(accepted_group.members) == 5

#     def test_invite_suggested_reviewers(self, conference, helpers, client, selenium, request_page):

#         result = conference.recruit_reviewers(['iclr2021_one@mail.com',
#         'iclr2021_two@mail.com',
#         'iclr2021_three@mail.com',
#         'iclr2021_four@mail.com',
#         'iclr2021_five@mail.com',
#         'iclr2021_six@mail.com',
#         'iclr2021_seven@mail.com',
#         'iclr2021_eight@mail.com',
#         'iclr2021_nine@mail.com',
#         'iclr2021_six_alternate@mail.com'], invitee_names=['', '', '', '', '', '', '', '', 'Melisa Bok', ''])

#         messages = client.get_messages(subject = '[ICLR 2021]: Invitation to serve as Reviewer')
#         assert len(messages) == 9

#         assert 'Melisa Bok' in messages[8]['content']['text']


#     def test_submit_papers(self, conference, helpers, test_client, client):

#         domains = ['umass.edu', 'umass.edu', 'fb.com', 'umass.edu', 'google.com', 'mit.edu']
#         for i in range(1,6):
#             note = openreview.Note(invitation = 'ICLR.cc/2021/Conference/-/Submission',
#                 readers = ['ICLR.cc/2021/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~Test_User1'],
#                 writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@' + domains[i]],
#                 signatures = ['~Test_User1'],
#                 content = {
#                     'title': 'Paper title ' + str(i) ,
#                     'abstract': 'This is an abstract ' + str(i),
#                     'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
#                     'authors': ['Test User', 'Peter Test', 'Andrew Mc'],
#                     'code_of_ethics': 'I acknowledge that I and all co-authors of this work have read and commit to adhering to the ICLR Code of Ethics'
#                 }
#             )
#             note = test_client.post_note(note)

#         conference.setup_first_deadline_stage(force=True)

#         blinded_notes = test_client.get_notes(invitation='ICLR.cc/2021/Conference/-/Blind_Submission')
#         assert len(blinded_notes) == 5

#         invitations = test_client.get_invitations(replyForum=blinded_notes[0].id)
#         assert len(invitations) == 1
#         assert invitations[0].id == 'ICLR.cc/2021/Conference/Paper5/-/Withdraw'

#         invitations = test_client.get_invitations(replyForum=blinded_notes[0].original)
#         assert len(invitations) == 1
#         assert invitations[0].id == 'ICLR.cc/2021/Conference/Paper5/-/Revision'

#         invitations = client.get_invitations(replyForum=blinded_notes[0].id)
#         assert len(invitations) == 2
#         assert invitations[0].id == 'ICLR.cc/2021/Conference/Paper5/-/Desk_Reject'
#         assert invitations[1].id == 'ICLR.cc/2021/Conference/Paper5/-/Withdraw'

#         # Add a revision
#         pdf_url = test_client.put_attachment(
#             os.path.join(os.path.dirname(__file__), 'data/paper.pdf'),
#             'ICLR.cc/2021/Conference/Paper5/-/Revision',
#             'pdf'
#         )

#         supplementary_material_url = test_client.put_attachment(
#             os.path.join(os.path.dirname(__file__), 'data/paper.pdf.zip'),
#             'ICLR.cc/2021/Conference/Paper5/-/Revision',
#             'supplementary_material'
#         )

#         note = openreview.Note(referent=blinded_notes[0].original,
#             forum=blinded_notes[0].original,
#             invitation = 'ICLR.cc/2021/Conference/Paper5/-/Revision',
#             readers = ['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
#             writers = ['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
#             signatures = ['ICLR.cc/2021/Conference/Paper5/Authors'],
#             content = {
#                 'title': 'EDITED Paper title 5',
#                 'abstract': 'This is an abstract 5',
#                 'authorids': ['test@mail.com', 'peter@mail.com', 'melisa@mail.com'],
#                 'authors': ['Test User', 'Peter Test', 'Melisa Bok'],
#                 'code_of_ethics': 'I acknowledge that I and all co-authors of this work have read and commit to adhering to the ICLR Code of Ethics',
#                 'pdf': pdf_url,
#                 'supplementary_material': supplementary_material_url
#             }
#         )

#         test_client.post_note(note)

#         helpers.await_queue()

#         author_group = client.get_group('ICLR.cc/2021/Conference/Paper5/Authors')
#         assert len(author_group.members) == 3
#         assert 'melisa@mail.com' in author_group.members
#         assert 'test@mail.com' in author_group.members
#         assert 'peter@mail.com' in author_group.members

#         messages = client.get_messages(subject='ICLR 2021 has received a new revision of your submission titled EDITED Paper title 5')
#         assert len(messages) == 3
#         recipients = [m['content']['to'] for m in messages]
#         assert 'melisa@mail.com' in recipients
#         assert 'test@mail.com' in recipients
#         assert 'peter@mail.com' in recipients
#         assert messages[0]['content']['text'] == '''Your new revision of the submission to ICLR 2021 has been posted.\n\nTitle: EDITED Paper title 5\n\nAbstract: This is an abstract 5\n\nTo view your submission, click here: https://openreview.net/forum?id=''' + note.forum

#         ## Edit revision
#         references = client.get_references(invitation='ICLR.cc/2021/Conference/Paper5/-/Revision')
#         assert len(references) == 1
#         revision_note = references[0]
#         revision_note.content['title'] = 'EDITED Rev 2 Paper title 5'
#         test_client.post_note(revision_note)

#         helpers.await_queue()

#         messages = client.get_messages(subject='ICLR 2021 has received a new revision of your submission titled EDITED Rev 2 Paper title 5')
#         assert len(messages) == 3
#         recipients = [m['content']['to'] for m in messages]
#         assert 'melisa@mail.com' in recipients
#         assert 'test@mail.com' in recipients
#         assert 'peter@mail.com' in recipients

#         assert messages[0]['content']['text'] == '''Your new revision of the submission to ICLR 2021 has been updated.\n\nTitle: EDITED Rev 2 Paper title 5\n\nAbstract: This is an abstract 5\n\nTo view your submission, click here: https://openreview.net/forum?id=''' + note.forum

#         ## Withdraw paper
#         test_client.post_note(openreview.Note(invitation='ICLR.cc/2021/Conference/Paper1/-/Withdraw',
#             forum = blinded_notes[4].forum,
#             replyto = blinded_notes[4].forum,
#             readers = [
#                 'ICLR.cc/2021/Conference',
#                 'ICLR.cc/2021/Conference/Paper1/Authors',
#                 'ICLR.cc/2021/Conference/Paper1/Reviewers',
#                 'ICLR.cc/2021/Conference/Paper1/Area_Chairs',
#                 'ICLR.cc/2021/Conference/Program_Chairs'],
#             writers = [conference.get_id(), 'ICLR.cc/2021/Conference/Paper1/Authors'],
#             signatures = ['ICLR.cc/2021/Conference/Paper1/Authors'],
#             content = {
#                 'title': 'Submission Withdrawn by the Authors',
#                 'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
#             }
#         ))

#         helpers.await_queue()

#         withdrawn_notes = client.get_notes(invitation='ICLR.cc/2021/Conference/-/Withdrawn_Submission')
#         assert len(withdrawn_notes) == 1
#         withdrawn_notes[0].readers == [
#             'ICLR.cc/2021/Conference/Paper1/Authors',
#             'ICLR.cc/2021/Conference/Paper1/Reviewers',
#             'ICLR.cc/2021/Conference/Paper1/Area_Chairs',
#             'ICLR.cc/2021/Conference/Program_Chairs'
#         ]
#         assert len(conference.get_submissions()) == 4

#     def test_post_submission_stage(self, conference, helpers, test_client, client):

#         conference.setup_final_deadline_stage(force=True)

#         submissions = conference.get_submissions()
#         assert len(submissions) == 4
#         assert submissions[0].readers == ['everyone']
#         assert submissions[1].readers == ['everyone']
#         assert submissions[2].readers == ['everyone']
#         assert submissions[3].readers == ['everyone']

#         ## Withdraw paper
#         test_client.post_note(openreview.Note(invitation='ICLR.cc/2021/Conference/Paper2/-/Withdraw',
#             forum = submissions[3].forum,
#             replyto = submissions[3].forum,
#             readers = [
#                 'everyone'],
#             writers = [conference.get_id(), 'ICLR.cc/2021/Conference/Paper2/Authors'],
#             signatures = ['ICLR.cc/2021/Conference/Paper2/Authors'],
#             content = {
#                 'title': 'Submission Withdrawn by the Authors',
#                 'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
#             }
#         ))

#         helpers.await_queue()

#         withdrawn_notes = client.get_notes(invitation='ICLR.cc/2021/Conference/-/Withdrawn_Submission')
#         assert len(withdrawn_notes) == 2
#         withdrawn_notes[0].readers == [
#             'everyone'
#         ]
#         withdrawn_notes[1].readers == [
#             'ICLR.cc/2021/Conference/Paper1/Authors',
#             'ICLR.cc/2021/Conference/Paper1/Reviewers',
#             'ICLR.cc/2021/Conference/Paper1/Area_Chairs',
#             'ICLR.cc/2021/Conference/Program_Chairs'
#         ]


#     def test_revision_stage(self, conference, helpers, test_client, client):

#         now = datetime.datetime.utcnow()
#         conference.set_submission_revision_stage(openreview.SubmissionRevisionStage(due_date=now + datetime.timedelta(minutes = 40), allow_author_reorder=True))

#         submissions = conference.get_submissions()

#         print(submissions[0])

#         test_client.post_note(openreview.Note(
#             invitation='ICLR.cc/2021/Conference/Paper5/-/Revision',
#             referent=submissions[0].original,
#             forum=submissions[0].original,
#             readers=['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
#             writers=['ICLR.cc/2021/Conference', 'ICLR.cc/2021/Conference/Paper5/Authors'],
#             signatures=['ICLR.cc/2021/Conference/Paper5/Authors'],
#             content={
#                 'title': 'EDITED V3 Paper title 5',
#                 'abstract': 'This is an abstract 5',
#                 'authorids': ['peter@mail.com', 'test@mail.com', 'melisa@mail.com'],
#                 'authors': ['Peter Test', 'Test User', 'Melisa Bok'],
#                 'code_of_ethics': 'I acknowledge that I and all co-authors of this work have read and commit to adhering to the ICLR Code of Ethics',
#                 'pdf': submissions[0].content['pdf'],
#                 'supplementary_material': submissions[0].content['supplementary_material']
#             }

#         ))
