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

class TestECCVConference():

    @pytest.fixture(scope="class")
    def conference(self, client):
        now = datetime.datetime.utcnow()
        #pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('thecvf.com/ECCV/2020/Conference')
        builder.set_override_homepage(True)
        builder.has_area_chairs(True)
        builder.set_recruitment_reduced_load(['4','5','6','7'], 7)
        # Reviewers
        reviewer_registration_tasks = {
            'profile_confirmed': {
                'required': True,
                'description': 'I confirm that I updated my OpenReview profile.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'expertise_confirmed': {
                'required': True,
                'description': 'I confirm that I verified my expertise.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'TPMS_registration_confirmed' : {
                'required': True,
                'description': 'I confirm that I updated my TPMS account.',
                'value-checkbox': 'Yes',
                'order': 3
            },
            'reviewer_instructions_confirm' : {
                'required': True,
                'description': 'I confirm that I will adhere to the reviewer instructions and will do my best to provide the agreed upon number of reviews in time.',
                'value-checkbox': 'Yes',
                'order': 4
            },
            'emergency_review_count' : {
                'required': True,
                'description': 'Decide whether you can and want to serve as emergency reviewer. Select how many reviews you can volunteer as emergency reviewer.',
                'value-radio': ['0', '1', '2'],
                'order': 5,
                'default': '0'
            }
        }

        ac_registration_tasks = {
            'profile_confirmed': {
                'required': True,
                'description': 'I confirm that I updated my OpenReview profile.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'expertise_confirmed': {
                'required': True,
                'description': 'I confirm that I verified my expertise.',
                'value-checkbox': 'Yes',
                'order': 1
            },
            'TPMS_registration_confirmed' : {
                'required': True,
                'description': 'I confirm that I updated my TPMP account',
                'value-checkbox': 'Yes',
                'order': 3}
        }

        reviewer_instructions = '''
1. In order to avoid conflicts of interest in reviewing, we ask that all reviewers take a moment to update their OpenReview profiles with their latest information regarding email addresses, work history and professional relationships: https://openreview.net/profile?mode=edit

2. We automatically populated your profile with your published papers. These represent your expertise and will be used to match submissions to you. Please take a moment to verify if the selection of papers is representative of your expertise and modify it if necessary: https://openreview.net/invitation?id=thecvf.com/ECCV/2020/Conference/-/Expertise_Selection

3. Full paper matching will be done via the Toronto paper matching system (TPMS). Please update your TPMS profile so that it represents your expertise well: http://torontopapermatching.org/webapp/profileBrowser/login/
If you don't have a TPMS account yet, you can create one here: http://torontopapermatching.org/webapp/profileBrowser/register/
Ensure that the email you use for your TPMS profile is listed as one of the emails in your OpenReview profile.

4. Please check the reviewer instructions: https://eccv2020.eu/reviewer-instructions/

5. Emergency reviewers are important to ensure that all papers receive 3 reviews even if some reviewers cannot submit their reviews in time (e.g. due to sickness). If you know for sure that you will be able to review 1 or 2 papers within 72-96 hours in the time from May 15 to May 19, you can volunteer as emergency reviewer. We will reduce your normal load by the number of papers you agree to handle as emergency reviewer. Every emergency review will increase your reviewer score in addition to the score assigned by the area chair.
        '''

        ac_instructions = '''
1. In order to avoid conflicts of interest in reviewing, we ask that all reviewers take a moment to update their OpenReview profiles with their latest information regarding email addresses, work history and professional relationships: https://openreview.net/profile?mode=edit

2. We automatically populated your profile with your published papers. These represent your expertise and will be used to match submissions to you. Please take a moment to verify if the selection of papers is representative of your expertise and modify it if necessary: https://openreview.net/invitation?id=thecvf.com/ECCV/2020/Conference/-/Expertise_Selection

3. Full paper matching will be done via the Toronto paper matching system (TPMS). Please update your TPMS profile so that it represents your expertise well: http://torontopapermatching.org/webapp/profileBrowser/login/
If you don't have a TPMS account yet, you can create one here: http://torontopapermatching.org/webapp/profileBrowser/register/
Ensure that the email you use for your TPMS profile is listed as one of the emails in your OpenReview profile.
        '''
        builder.set_registration_stage(name='Profile_Confirmation',
        additional_fields = reviewer_registration_tasks,
        due_date = now + datetime.timedelta(minutes = 40),
        ac_additional_fields=ac_registration_tasks,
        instructions=reviewer_instructions,
        ac_instructions=ac_instructions)
        builder.set_expertise_selection_stage(due_date = now + datetime.timedelta(minutes = 10))
        builder.set_submission_stage(double_blind = True,
            public = False,
            due_date = now + datetime.timedelta(minutes = 10),
            additional_fields= {
                'video': {
                    'description': 'Short video with presentation of the paper, it supports: mov, mp4, zip',
                    'required': True,
                    'value-file': {
                        'fileTypes': ['mov', 'mp4', 'zip'],
                        'size': 50000000000
                    }
                },
                'supplemental_material': {
                    'description': 'Paper appendix',
                    'required': False,
                    'value-file': {
                        'fileTypes': ['pdf'],
                        'size': 500000000000
                    }
                }
            })


        instructions = '''<p class="dark"><strong>Instructions:</strong></p>
        <ul>
            <li>
                Please indicate your <strong>level of interest</strong> in
                reviewing the submitted papers below,
                on a scale from "Very Low" interest to "Very High" interest. Papers were automatically pre-ranked using the expertise information in your profile.
            </li>
            <li>
                Bid on as many papers as possible to correct errors of this automatic procedure.
            </li>
            <li>
                Bidding on the top ranked papers removes false positives.
            </li>
            <li>
                You can use the search field to find papers by keywords from the title or abstract to reduce false negatives.
            </li>
            <li>
                Ensure that you have at least <strong>{request_count} bids</strong>, which are "Very High" or "High".
            </li>
            <li>
                Papers for which you have a conflict of interest are not shown.
            </li>
        </ul>
        <br>'''
        builder.set_bid_stage(due_date =  now + datetime.timedelta(minutes = 1440), request_count = 40, use_affinity_score=True, instructions = instructions, ac_request_count=60)
        conference = builder.get_result()
        conference.set_program_chairs(['pc@eccv.org'])
        return conference


    def test_create_conference(self, client, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('thecvf.com/ECCV/2020/Conference')
        builder.has_area_chairs(True)
        conference = builder.get_result()
        assert conference, 'conference is None'
        conference.set_program_chairs(['pc@eccv.org'])

        pc_client = helpers.create_user('pc@eccv.org', 'Program', 'ECCVChair')

        group = pc_client.get_group('thecvf.com/ECCV/2020/Conference')
        assert group
        assert group.web

        pc_group = pc_client.get_group('thecvf.com/ECCV/2020/Conference/Program_Chairs')
        assert pc_group
        assert pc_group.web

    def test_recruit_reviewer(self, conference, client, helpers, selenium, request_page):

        result = conference.recruit_reviewers(['test_reviewer_eccv@mail.com', 'mohit+1@mail.com'])
        assert result
        assert result.id == 'thecvf.com/ECCV/2020/Conference/Reviewers/Invited'
        assert 'test_reviewer_eccv@mail.com' in result.members
        assert 'mohit+1@mail.com' in result.members

        messages = client.get_messages(to = 'mohit+1@mail.com', subject = 'thecvf.com/ECCV/2020/Conference: Invitation to Review')
        text = messages[0]['content']['text']
        assert 'Dear invitee,' in text
        assert 'You have been nominated by the program chair committee of  to serve as a reviewer' in text

        reject_url = re.search('http://.*response=No', text).group(0)
        request_page(selenium, reject_url, alert=True)
        notes = selenium.find_element_by_id("notes")
        assert notes
        messages = notes.find_elements_by_tag_name("h3")
        assert messages
        assert 'You have declined the invitation from thecvf.com/ECCV/2020/Conference.' == messages[0].text
        assert 'In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here: Request reduced load' == messages[1].text

        group = client.get_group('thecvf.com/ECCV/2020/Conference/Reviewers')
        assert group
        assert len(group.members) == 0

        group = client.get_group('thecvf.com/ECCV/2020/Conference/Reviewers/Declined')
        assert group
        assert len(group.members) == 1
        assert 'mohit+1@mail.com' in group.members

        messages = client.get_messages(to='mohit+1@mail.com', subject='[] Reviewer Invitation declined')
        assert messages
        assert len(messages)
        assert messages[0]['content']['text'].startswith('You have declined the invitation to become a Reviewer for .\n\nIf you would like to change your decision, please click the Accept link in the previous invitation email.\n\nIn case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here:')

        ## Reduce the load of Mohit
        notes = client.get_notes(invitation='thecvf.com/ECCV/2020/Conference/-/Recruit_Reviewers', content={'user': 'mohit+1@mail.com'})
        assert notes
        assert len(notes) == 1

        client.post_note(openreview.Note(
            invitation='thecvf.com/ECCV/2020/Conference/-/Reduced_Load',
            readers=['thecvf.com/ECCV/2020/Conference', 'mohit+1@mail.com'],
            writers=['thecvf.com/ECCV/2020/Conference'],
            signatures=['(anonymous)'],
            content={
                'user': 'mohit+1@mail.com',
                'key': notes[0].content['key'],
                'response': 'Yes',
                'reviewer_load': '4'
            }
        ))

        messages = client.get_messages(to = 'test_reviewer_eccv@mail.com', subject = 'thecvf.com/ECCV/2020/Conference: Invitation to Review')
        text = messages[0]['content']['text']

        accept_url = re.search('http://.*response=Yes', text).group(0)
        request_page(selenium, accept_url, alert=True)

        group = client.get_group(conference.get_reviewers_id())
        assert group
        assert len(group.members) == 2
        assert group.members[0] == 'mohit+1@mail.com'
        assert group.members[1] == 'test_reviewer_eccv@mail.com'

    def test_expertise_selection(self, conference, helpers, selenium, request_page):

        reviewer_client = helpers.create_user('test_reviewer_eccv@mail.com', 'Testreviewer', 'Eccv')
        reviewer_tasks_url = 'http://localhost:3000/group?id=' + conference.get_reviewers_id() + '#reviewer-tasks'
        request_page(selenium, reviewer_tasks_url, reviewer_client.token)

        assert selenium.find_element_by_link_text('Expertise Selection')

        request_page(selenium, 'http://localhost:3000/invitation?id=thecvf.com/ECCV/2020/Conference/-/Expertise_Selection', reviewer_client.token)
        header = selenium.find_element_by_id('header')
        assert header
        notes = header.find_elements_by_class_name("description")
        assert notes
        assert len(notes) == 1
        assert notes[0].text == '''Listed below are all the papers you have authored that exist in the OpenReview database.

By default, we consider all of these papers to formulate your expertise. Please click on "Exclude" for papers that you do NOT want to be used to represent your expertise.

Your previously authored papers from selected conferences were imported automatically from DBLP.org. The keywords in these papers will be used to rank submissions for you during the bidding process, and to assign submissions to you during the review process.

Papers not automatically included as part of this import process can be uploaded by using the Upload button. Make sure that your email is part of the "authorids" field of the upload form. Otherwise the paper will not appear in the list, though it will be included in the recommendations process. Only upload papers co-authored by you.

Please contact info@openreview.net with any questions or concerns about this interface, or about the expertise scoring process.'''

    def test_open_registration(self, conference, helpers, selenium, request_page):

        reviewer_client = openreview.Client(username='test_reviewer_eccv@mail.com', password='1234')
        reviewer_tasks_url = 'http://localhost:3000/group?id=' + conference.get_reviewers_id() + '#reviewer-tasks'
        request_page(selenium, reviewer_tasks_url, reviewer_client.token)

        assert selenium.find_element_by_link_text('Reviewer Profile Confirmation')

        registration_notes = reviewer_client.get_notes(invitation = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Form')
        assert registration_notes
        assert len(registration_notes) == 1

        registration_forum = registration_notes[0].forum

        registration_note = reviewer_client.post_note(
            openreview.Note(
                invitation = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Profile_Confirmation',
                forum = registration_forum,
                replyto = registration_forum,
                content = {
                    'profile_confirmed': 'Yes',
                    'expertise_confirmed': 'Yes',
                    'TPMS_registration_confirmed': 'Yes',
                    'reviewer_instructions_confirm': 'Yes',
                    'emergency_review_count': '0'
                },
                signatures = [
                    '~Testreviewer_Eccv1'
                ],
                readers = [
                    conference.get_id(),
                    '~Testreviewer_Eccv1'
                ],
                writers = [
                    conference.get_id(),
                    '~Testreviewer_Eccv1'
                ]
            ))
        assert registration_note


        request_page(selenium, 'http://localhost:3000/group?id=thecvf.com/ECCV/2020/Conference/Reviewers', reviewer_client.token)
        header = selenium.find_element_by_id('header')
        assert header
        notes = header.find_elements_by_class_name("description")
        assert notes
        assert len(notes) == 2
        assert notes[0].text == 'This page provides information and status updates for the . It will be regularly updated as the conference progresses, so please check back frequently for news and other updates.'
        assert notes[1].text == 'You agreed to review up to 7 papers.'

        reviewer2_client = helpers.create_user('mohit+1@mail.com', 'Mohit', 'EccvReviewer')
        request_page(selenium, 'http://localhost:3000/group?id=thecvf.com/ECCV/2020/Conference/Reviewers', reviewer2_client.token)
        header = selenium.find_element_by_id('header')
        assert header
        notes = header.find_elements_by_class_name("description")
        assert notes
        assert len(notes) == 2
        assert notes[0].text == 'This page provides information and status updates for the . It will be regularly updated as the conference progresses, so please check back frequently for news and other updates.'
        assert notes[1].text == 'You agreed to review up to 4 papers.'

        #Area Chairs
        conference.set_area_chairs(['test_ac_eccv@mail.com'])
        ac_client = helpers.create_user('test_ac_eccv@mail.com', 'Testareachair', 'Eccv')
        reviewer_tasks_url = 'http://localhost:3000/group?id=thecvf.com/ECCV/2020/Conference/Area_Chairs#areachair-tasks'
        request_page(selenium, reviewer_tasks_url, ac_client.token)

        assert selenium.find_element_by_link_text('Area Chair Profile Confirmation')


    def test_submission_additional_files(self, conference, test_client):

        domains = ['umass.edu', 'umass.edu', 'fb.com', 'umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.Note(invitation = conference.get_submission_id(),
                readers = ['thecvf.com/ECCV/2020/Conference', 'test@mail.com', 'peter@mail.com', 'andrew@' + domains[i], '~Test_User1'],
                writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@' + domains[i]],
                signatures = ['~Test_User1'],
                content = {
                    'title': 'Paper title ' + str(i) ,
                    'abstract': 'This is an abstract ' + str(i),
                    'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@' + domains[i]],
                    'authors': ['Test User', 'Peter Test', 'Andrew Mc']
                }
            )
            url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
            note.content['pdf'] = url
            url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf.zip'), conference.get_submission_id(), 'video')
            note.content['video'] = url
            test_client.post_note(note)

    def test_submission_edit(self, conference, client, test_client):

        existing_notes = client.get_notes(invitation = conference.get_submission_id())
        assert len(existing_notes) == 5

        time.sleep(2)
        note = existing_notes[0]
        process_logs = client.get_process_logs(id = note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = ' has received your submission titled ' + note.content['title'])
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients

        note.content['title'] = 'I have been updated'
        client.post_note(note)

        time.sleep(2)
        note = client.get_note(note.id)

        process_logs = client.get_process_logs(id = note.id)
        assert len(process_logs) == 2
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[1]['status'] == 'ok'

        messages = client.get_messages(subject = ' has received your submission titled I have been updated')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        assert 'andrew@mit.edu' in recipients

        tauthor_message = [msg for msg in messages if msg['content']['to'] == note.tauthor][0]
        assert tauthor_message
        assert tauthor_message['content']['text'] == 'Your submission to  has been updated.\n\nSubmission Number: ' + str(note.number) + ' \n\nTitle: ' + note.content['title'] + ' \n\nAbstract: ' + note.content['abstract'] + ' \n\nTo view your submission, click here: http://localhost:3000/forum?id=' + note.id

        other_author_messages = [msg for msg in messages if msg['content']['to'] != note.tauthor]
        assert len(other_author_messages) == 2
        assert other_author_messages[0]['content']['text'] == 'Your submission to  has been updated.\n\nSubmission Number: ' + str(note.number) + ' \n\nTitle: ' + note.content['title'] + ' \n\nAbstract: ' + note.content['abstract'] + ' \n\nTo view your submission, click here: http://localhost:3000/forum?id=' + note.id + '\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at ' + note.tauthor

    def test_revise_additional_files(self, conference, test_client):

        pc_client = openreview.Client(username='pc@eccv.org', password='1234')

        conference.create_blind_submissions(force=True, hide_fields=['pdf', 'video', 'supplemental_material'])
        conference.set_authors()

        notes = conference.get_submissions()
        assert notes
        assert len(notes) == 5
        note = notes[0]

        invitation = openreview.Invitation(
            id = 'thecvf.com/ECCV/2020/Conference/-/Revision',
            readers = ['everyone'],
            writers = [conference.get_id()],
            signatures = [conference.get_id()],
            invitees = note.content['authorids'] + note.signatures,
            reply = {
                'forum': note.original,
                'referent': note.original,
                'readers': {
                    'values-copied': [
                        conference.get_id(),
                        '{signatures}'
                    ]
                },
                'writers': {
                    'values-copied': [
                        conference.get_id(),
                        '{signatures}'
                    ]
                },
                'signatures': {
                    'values-regex': '~.*'
                },
                'content': {
                    'pdf': {
                        'description': 'Paper pdf',
                        'required': False,
                        'value-file': {
                            'fileTypes': ['pdf'],
                            'size': 50
                        }
                    },
                    'video': {
                        'description': 'Short video with presentation of the paper, it supports: mov, mp4, zip',
                        'required': False,
                        'value-file': {
                            'fileTypes': ['mov', 'mp4', 'zip'],
                            'size': 50
                        }
                    },
                    'supplemental_material': {
                        'description': 'Paper appendix',
                        'required': False,
                        'value-file': {
                            'fileTypes': ['pdf'],
                            'size': 50
                        }
                    }
                }
            }
        )

        pc_client.post_invitation(invitation)

        note = openreview.Note(invitation = 'thecvf.com/ECCV/2020/Conference/-/Revision',
            readers = ['thecvf.com/ECCV/2020/Conference', '~Test_User1'],
            writers = [conference.id, '~Test_User1'],
            signatures = ['~Test_User1'],
            referent = note.original,
            forum = note.original,
            content = {
            }
        )
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), 'thecvf.com/ECCV/2020/Conference/-/Revision', 'pdf')
        note.content['pdf'] = url
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), 'thecvf.com/ECCV/2020/Conference/-/Revision', 'supplemental_material')
        note.content['supplemental_material'] = url
        test_client.post_note(note)


    def test_bid_stage(self, conference, helpers, selenium, request_page):

        reviewer_client = openreview.Client(username='test_reviewer_eccv@mail.com', password='1234')
        reviewer_tasks_url = 'http://localhost:3000/group?id=' + conference.get_reviewers_id() + '#reviewer-tasks'
        request_page(selenium, reviewer_tasks_url, reviewer_client.token)

        assert selenium.find_element_by_link_text('Reviewer Bid')

        request_page(selenium, 'http://localhost:3000/invitation?id=thecvf.com/ECCV/2020/Conference/Reviewers/-/Bid', reviewer_client.token)
        header = selenium.find_element_by_id('header')
        assert header
        notes = header.find_elements_by_tag_name("li")
        assert notes
        assert len(notes) == 6
        assert notes[4].text == 'Ensure that you have at least 40 bids, which are "Very High" or "High".'

        ac_client = openreview.Client(username='test_ac_eccv@mail.com', password='1234')
        request_page(selenium, 'http://localhost:3000/group?id=' + conference.get_area_chairs_id() + '#areachair-tasks', ac_client.token)

        assert selenium.find_element_by_link_text('Area Chair Bid')

        request_page(selenium, 'http://localhost:3000/invitation?id=thecvf.com/ECCV/2020/Conference/Area_Chairs/-/Bid', ac_client.token)
        header = selenium.find_element_by_id('header')
        assert header
        notes = header.find_elements_by_tag_name("li")
        assert notes
        assert len(notes) == 6
        assert notes[4].text == 'Ensure that you have at least 60 bids, which are "Very High" or "High".'

    def test_recommend_reviewers(self, conference, test_client, helpers, selenium, request_page):

        r1_client = helpers.create_user('reviewer1@fb.com', 'Reviewer', 'ECCV_One')
        r2_client = helpers.create_user('reviewer2@google.com', 'Reviewer', 'ECCV_Two')
        r3_client = helpers.create_user('reviewer3@umass.edu', 'Reviewer', 'ECCV_Three')
        r4_client = helpers.create_user('reviewer4@mit.edu', 'Reviewer', 'ECCV_Four')
        ac1_client = helpers.create_user('ac1@eccv.org', 'AreaChair', 'ECCV_One')
        ac2_client = helpers.create_user('ac2eccv.org', 'AreaChair', 'ECCV_Two')

        conference.set_reviewers(['~Reviewer_ECCV_One1', '~Reviewer_ECCV_Two1', '~Reviewer_ECCV_Three1'])
        conference.set_area_chairs(['~AreaChair_ECCV_One1', '~AreaChair_ECCV_Two1'])

        blinded_notes = conference.get_submissions()

        with open(os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in blinded_notes:
                writer.writerow([submission.id, '~Reviewer_ECCV_One1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_ECCV_Two1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_ECCV_Three1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_ECCV_Four1', round(random.random(), 2)])

        with open(os.path.join(os.path.dirname(__file__), 'data/temp.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in blinded_notes:
                writer.writerow([submission.number, 'reviewer1@fb.com', round(random.random(), 2)])
                writer.writerow([submission.number, 'reviewer2@google.com', round(random.random(), 2)])
                writer.writerow([submission.number, 'reviewer3@umass.edu', round(random.random(), 2)])
                writer.writerow([submission.number, 'reviewer4@mit.edu', round(random.random(), 2)])


        conference.setup_matching(
            affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_affinity_scores.csv'),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/temp.csv')
        )


        with open(os.path.join(os.path.dirname(__file__), 'data/ac_affinity_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in blinded_notes:
                writer.writerow([submission.id, '~AreaChair_ECCV_One1', round(random.random(), 2)])
                writer.writerow([submission.id, '~AreaChair_ECCV_Two1', round(random.random(), 2)])

        with open(os.path.join(os.path.dirname(__file__), 'data/temp.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in blinded_notes:
                writer.writerow([submission.number, 'ac1@eccv.org', round(random.random(), 2)])
                writer.writerow([submission.number, 'ac2eccv.org', round(random.random(), 2)])

        conference.setup_matching(is_area_chair=True, affinity_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_affinity_scores.csv'),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/temp.csv'))

        ### Bids
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_One1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[0].number)],
            writers = [conference.id, '~Reviewer_ECCV_One1'],
            signatures = ['~Reviewer_ECCV_One1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_ECCV_One1',
            label = 'Neutral'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_One1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[1].number)],
            writers = [conference.id, '~Reviewer_ECCV_One1'],
            signatures = ['~Reviewer_ECCV_One1'],
            head = blinded_notes[1].id,
            tail = '~Reviewer_ECCV_One1',
            label = 'Very High'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_One1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[4].number)],
            writers = [conference.id, '~Reviewer_ECCV_One1'],
            signatures = ['~Reviewer_ECCV_One1'],
            head = blinded_notes[4].id,
            tail = '~Reviewer_ECCV_One1',
            label = 'High'
        ))

        r2_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Two1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[2].number)],
            writers = [conference.id, '~Reviewer_ECCV_Two1'],
            signatures = ['~Reviewer_ECCV_Two1'],
            head = blinded_notes[2].id,
            tail = '~Reviewer_ECCV_Two1',
            label = 'Neutral'
        ))
        r2_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Two1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[3].number)],
            writers = [conference.id, '~Reviewer_ECCV_Two1'],
            signatures = ['~Reviewer_ECCV_Two1'],
            head = blinded_notes[3].id,
            tail = '~Reviewer_ECCV_Two1',
            label = 'Very High'
        ))
        r2_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Two1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[4].number)],
            writers = [conference.id, '~Reviewer_ECCV_Two1'],
            signatures = ['~Reviewer_ECCV_Two1'],
            head = blinded_notes[4].id,
            tail = '~Reviewer_ECCV_Two1',
            label = 'High'
        ))

        r3_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Three1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[4].number)],
            writers = [conference.id, '~Reviewer_ECCV_Three1'],
            signatures = ['~Reviewer_ECCV_Three1'],
            head = blinded_notes[4].id,
            tail = '~Reviewer_ECCV_Three1',
            label = 'Neutral'
        ))
        r3_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Three1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[2].number)],
            writers = [conference.id, '~Reviewer_ECCV_Three1'],
            signatures = ['~Reviewer_ECCV_Three1'],
            head = blinded_notes[2].id,
            tail = '~Reviewer_ECCV_Three1',
            label = 'Very High'
        ))
        r3_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Three1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[0].number)],
            writers = [conference.id, '~Reviewer_ECCV_Three1'],
            signatures = ['~Reviewer_ECCV_Three1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_ECCV_Three1',
            label = 'High'
        ))
        r4_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = [conference.id, conference.get_area_chairs_id(), '~Reviewer_ECCV_Four1'],
            nonreaders = [conference.get_authors_id(number=blinded_notes[0].number)],
            writers = [conference.id, '~Reviewer_ECCV_Four1'],
            signatures = ['~Reviewer_ECCV_Four1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_ECCV_Four1',
            label = 'High'
        ))

        ## Area chairs assignments
        pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, '~AreaChair_ECCV_One1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = '~AreaChair_ECCV_One1',
            label = 'ac-matching',
            weight = 0.98
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, '~AreaChair_ECCV_One1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = '~AreaChair_ECCV_One1',
            label = 'ac-matching',
            weight = 0.88
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, '~AreaChair_ECCV_One1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = '~AreaChair_ECCV_One1',
            label = 'ac-matching',
            weight = 0.79
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, '~AreaChair_ECCV_Two1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[3].id,
            tail = '~AreaChair_ECCV_Two1',
            label = 'ac-matching',
            weight = 0.99
        ))
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_area_chairs_id()),
            readers = [conference.id, '~AreaChair_ECCV_Two1'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[4].id,
            tail = '~AreaChair_ECCV_Two1',
            label = 'ac-matching',
            weight = 0.86
        ))

        now = datetime.datetime.utcnow()
        conference.open_recommendations(assignment_title='ac-matching', due_date=now + datetime.timedelta(minutes = 1440))

        ac1_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = [conference.id, '~AreaChair_ECCV_One1'],
            writers = ['~AreaChair_ECCV_One1'],
            signatures = ['~AreaChair_ECCV_One1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_ECCV_Three1',
            weight = 1))

        ac2_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = [conference.id, '~AreaChair_ECCV_Two1'],
            writers = ['~AreaChair_ECCV_Two1'],
            signatures = ['~AreaChair_ECCV_Two1'],
            head = blinded_notes[3].id,
            tail = '~Reviewer_ECCV_Three1',
            weight = 10))

        ac2_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = [conference.id, '~AreaChair_ECCV_Two1'],
            writers = ['~AreaChair_ECCV_Two1'],
            signatures = ['~AreaChair_ECCV_Two1'],
            head = blinded_notes[4].id,
            tail = '~Reviewer_ECCV_Three1',
            weight = 5))

        ## Go to edge browser to recommend reviewers
        start = 'thecvf.com/ECCV/2020/Conference/Area_Chairs/-/Paper_Assignment,label:ac-matching,tail:~AreaChair_ECCV_One1'
        edit = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Recommendation'
        browse = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/TPMS_Score;\
thecvf.com/ECCV/2020/Conference/Reviewers/-/Affinity_Score;\
thecvf.com/ECCV/2020/Conference/Reviewers/-/Bid'
        hide = 'thecvf.com/ECCV/2020/Conference/Reviewers/-/Conflict'
        referrer = '[Return%20Instructions](/invitation?id=thecvf.com/ECCV/2020/Conference/Reviewers/-/Recommendation)'

        url = 'http://localhost:3000/edge/browse?start={start}&traverse={edit}&edit={edit}&browse={browse}&hide={hide}&referrer={referrer}&maxColumns=2'.format(start=start, edit=edit, browse=browse, hide=hide, referrer=referrer)

        request_page(selenium, 'http://localhost:3000/invitation?id=thecvf.com/ECCV/2020/Conference/Reviewers/-/Recommendation', ac1_client.token)
        panel = selenium.find_element_by_id('notes')
        assert panel
        links = panel.find_elements_by_tag_name('a')
        assert links
        assert len(links) == 1
        assert url == links[0].get_attribute("href")


    def test_desk_reject_submission(self, conference, client, test_client):

        conference.close_submissions()
        conference.create_desk_reject_invitations(reveal_submission=False)

        blinded_notes = conference.get_submissions()
        assert len(blinded_notes) == 5

        desk_reject_note = openreview.Note(
            invitation = 'thecvf.com/ECCV/2020/Conference/Paper5/-/Desk_Reject',
            forum = blinded_notes[0].forum,
            replyto = blinded_notes[0].forum,
            readers = ['thecvf.com/ECCV/2020/Conference/Paper5/Authors',
            'thecvf.com/ECCV/2020/Conference/Paper5/Reviewers',
            'thecvf.com/ECCV/2020/Conference/Paper5/Area_Chairs',
            'thecvf.com/ECCV/2020/Conference/Program_Chairs'],
            writers = [conference.get_id(), conference.get_program_chairs_id()],
            signatures = [conference.get_program_chairs_id()],
            content = {
                'desk_reject_comments': 'PC has decided to reject this submission.',
                'title': 'Submission Desk Rejected by Program Chairs'
            }
        )

        pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        posted_note = pc_client.post_note(desk_reject_note)
        assert posted_note

        time.sleep(2)

        logs = client.get_process_logs(id = posted_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        blinded_notes = conference.get_submissions()
        assert len(blinded_notes) == 4

        desk_rejected_notes = client.get_notes(invitation = conference.submission_stage.get_desk_rejected_submission_id(conference))

        assert len(desk_rejected_notes) == 1
        assert desk_rejected_notes[0].content['authors'] == ['Anonymous']
        assert desk_rejected_notes[0].content['authorids'] == ['thecvf.com/ECCV/2020/Conference/Paper5/Authors']
        assert desk_rejected_notes[0].readers == ['thecvf.com/ECCV/2020/Conference/Paper5/Authors',
            'thecvf.com/ECCV/2020/Conference/Paper5/Reviewers',
            'thecvf.com/ECCV/2020/Conference/Paper5/Area_Chairs',
            'thecvf.com/ECCV/2020/Conference/Program_Chairs']

        desk_reject_note = test_client.get_note(posted_note.id)
        assert desk_reject_note
        assert desk_reject_note.content['desk_reject_comments'] == 'PC has decided to reject this submission.'

        author_group = client.get_group('thecvf.com/ECCV/2020/Conference/Authors')
        assert author_group
        print(author_group)
        assert len(author_group.members) == 4
        assert 'thecvf.com/ECCV/2020/Conference/Paper5/Authors' not in author_group.members


    def test_withdraw_submission(self, conference, client, test_client):

        conference.create_withdraw_invitations(reveal_submission=False)

        blinded_notes = conference.get_submissions()
        assert len(blinded_notes) == 4

        withdrawal_note = openreview.Note(
            invitation = 'thecvf.com/ECCV/2020/Conference/Paper4/-/Withdraw',
            forum = blinded_notes[0].forum,
            replyto = blinded_notes[0].forum,
            readers = ['thecvf.com/ECCV/2020/Conference/Paper4/Authors',
            'thecvf.com/ECCV/2020/Conference/Paper4/Reviewers',
            'thecvf.com/ECCV/2020/Conference/Paper4/Area_Chairs',
            'thecvf.com/ECCV/2020/Conference/Program_Chairs'],
            writers = [conference.get_id(), 'thecvf.com/ECCV/2020/Conference/Paper4/Authors'],
            signatures = ['thecvf.com/ECCV/2020/Conference/Paper4/Authors'],
            content = {
                'title': 'Submission Withdrawn by the Authors',
                'withdrawal confirmation': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
            }
        )

        posted_note = test_client.post_note(withdrawal_note)
        assert posted_note

        time.sleep(2)

        logs = client.get_process_logs(id = posted_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        blinded_notes = conference.get_submissions()
        assert len(blinded_notes) == 3

        withdrawn_notes = client.get_notes(invitation = conference.submission_stage.get_withdrawn_submission_id(conference))

        assert len(withdrawn_notes) == 1
        assert withdrawn_notes[0].content['authors'] == ['Anonymous']
        assert withdrawn_notes[0].content['authorids'] == ['thecvf.com/ECCV/2020/Conference/Paper4/Authors']
        assert withdrawn_notes[0].readers == ['thecvf.com/ECCV/2020/Conference/Paper4/Authors',
            'thecvf.com/ECCV/2020/Conference/Paper4/Reviewers',
            'thecvf.com/ECCV/2020/Conference/Paper4/Area_Chairs',
            'thecvf.com/ECCV/2020/Conference/Program_Chairs']

        author_group = client.get_group('thecvf.com/ECCV/2020/Conference/Authors')
        assert author_group
        print(author_group)
        assert len(author_group.members) == 3
        assert 'thecvf.com/ECCV/2020/Conference/Paper4/Authors' not in author_group.members

