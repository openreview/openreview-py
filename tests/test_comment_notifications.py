from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
import time
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

class TestCommentNotification():

    def test_notify_all(self, client, test_client):

        builder = openreview.conference.ConferenceBuilder(client)

        builder.set_conference_id('MIDL.io/2019/Conference')
        builder.set_conference_name('Medical Imaging with Deep Learning')
        builder.set_conference_short_name('MIDL 2019')
        builder.set_homepage_header({
        'title': 'Medical Imaging with Deep Learning',
        'subtitle': 'MIDL 2019 Conference',
        'deadline': 'Submission Deadline: 13th of December, 2018',
        'date': '8-10 July 2019',
        'website': 'http://2019.midl.io',
        'location': 'London',
        'instructions': 'Full papers contain well-validated applications or methodological developments of deep learning algorithms in medical imaging. There is no strict limit on paper length. However, we strongly recommend keeping full papers at 8 pages (excluding references and acknowledgements). An appendix section can be added if needed with additional details but must be compiled into a single pdf. The appropriateness of using pages over the recommended page length will be judged by reviewers. All accepted papers will be presented as posters with a selection of these papers will also be invited for oral presentation.<br/><br/> <p><strong>Questions or Concerns</strong></p><p>Please contact the OpenReview support team at <a href=\"mailto:info@openreview.net\">info@openreview.net</a> with any questions or concerns about the OpenReview platform.<br/>    Please contact the MIDL 2019 Program Chairs at <a href=\"mailto:program-chairs@midl.io\">program-chairs@midl.io</a> with any questions or concerns about conference administration or policy.</p><p>We are aware that some email providers inadequately filter emails coming from openreview.net as spam so please check your spam folder regularly.</p>'
        })
        builder.set_conference_submission_name('Full_Submission')
        builder.set_submission_public(True)
        builder.has_area_chairs(True)
        conference = builder.get_result()

        now = datetime.datetime.utcnow()
        invitation = conference.open_submissions(due_date = now + datetime.timedelta(minutes = 10))

        note = openreview.Note(invitation = invitation.id,
            readers = ['everyone'],
            writers = ['~Test_User1', 'author@mail.com', 'author2@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'author@mail.com', 'author2@mail.com'],
                'authors': ['Test User', 'Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/sdfskdls.pdf'
            }
        )

        note = test_client.post_note(note)
        assert note

        conference.close_submissions()

        conference.set_authors()
        conference.set_program_chairs(emails= ['programchair@midl.io'])
        conference.open_comments(name = 'Official_Comment', public = False, anonymous = True, unsubmitted_reviewers= True, reader_selection=True)

        comment_invitation_id = '{conference_id}/-/Paper{number}/Official_Comment'.format(conference_id = conference.id, number = note.number)
        authors_group_id = '{conference_id}/Paper{number}/Authors'.format(conference_id = conference.id, number = note.number)
        reviewers_group_id = '{conference_id}/Paper{number}/Reviewers'.format(conference_id = conference.id, number = note.number)
        anon_reviewers_group_id = '{conference_id}/Paper{number}/AnonReviewer1'.format(conference_id = conference.id, number = note.number)
        acs_group_id = '{conference_id}/Paper{number}/Area_Chairs'.format(conference_id = conference.id, number = note.number)

        openreview.tools.add_assignment(client, note.number, conference.id, 'reviewer@midl.io')
        openreview.tools.add_assignment(client, note.number, conference.id, 'areachair@midl.io', individual_label='Area_Chair', parent_label='Area_Chairs')

        comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'reviewer@midl.io'],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Comment title',
                'comment': 'This is an comment'
            }
        )
        comment_note = client.post_note(comment_note)

        assert comment_note
        assert comment_note.forum == note.id

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'

        reply_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [authors_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'test@mail.com'],
            signatures = [authors_group_id],
            content = {
                'title': 'Reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply_comment_note = test_client.post_note(reply_comment_note)

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'

        reply2_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [reviewers_group_id, acs_group_id],
            writers = [conference.id, 'reviewer@midl.io'],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Another reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply2_comment_note = client.post_note(reply2_comment_note)

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'

        pc_client = openreview.Client(baseurl = 'http://localhost:3000')
        assert pc_client is not None, "Client is none"
        res = pc_client.register_user(email = 'programchair@midl.io', first = 'Program', last = 'Chair', password = '1234')
        assert res, "Res i none"
        res = pc_client.activate_user('programchair@midl.io', {
            'names': [
                    {
                        'first': 'Program',
                        'last': 'Chair',
                        'username': '~Program_Chair1'
                    }
                ],
            'emails': ['programchair@midl.io'],
            'preferredEmail': 'programchair@midl.io'
            })
        assert res

        reply3_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'programchair@midl.io'],
            signatures = [conference.get_program_chairs_id()],
            content = {
                'title': 'Another reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply3_comment_note = pc_client.post_note(reply3_comment_note)

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == 'OpenReview signup confirmation'


    def test_notify_submitted_reviewers(self, client, test_client, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        builder.set_conference_id('auai.org/UAI/2020/Conference')
        builder.set_conference_name('Conference on Uncertainty in Artificial Intelligence')
        builder.set_conference_short_name('UAI 2020')
        builder.set_homepage_header({
        'title': 'UAI 2020',
        'subtitle': 'Conference on Uncertainty in Artificial Intelligence',
        'deadline': 'Abstract Submission Deadline: 11:59 pm Samoa Standard Time, March 4, 2019, Full Submission Deadline: 11:59 pm Samoa Standard Time, March 8, 2019',
        'date': 'July 22 - July 25, 2019',
        'website': 'http://auai.org/uai2019/',
        'location': 'Tel Aviv, Israel',
        'instructions': '''<p><strong>Important Information about Anonymity:</strong><br>
            When you post a submission to UAI 2019, please provide the real names and email addresses of authors in the submission form below (but NOT in the manuscript).
            The <em>original</em> record of your submission will be private, and will contain your real name(s).
            The PDF in your submission should not contain the names of the authors. </p>
            <p><strong>Conflict of Interest:</strong><br>
            Please make sure that your current and previous affiliations listed on your OpenReview <a href=\"/profile\">profile page</a> is up-to-date to avoid conflict of interest.</p>
            <p><strong>Questions or Concerns:</strong><br> Please contact the UAI 2019 Program chairs at <a href=\"mailto:uai2019chairs@gmail.com\">uai2019chairs@gmail.com</a>.
            <br>Please contact the OpenReview support team at <a href=\"mailto:info@openreview.net\">info@openreview.net</a> with any OpenReview related questions or concerns.
            </p>'''
        })
        builder.set_conference_area_chairs_name('Senior_Program_Committee')
        builder.set_conference_reviewers_name('Program_Committee')
        builder.set_double_blind(True)
        builder.set_override_homepage(True)
        builder.set_subject_areas([
            "Algorithms: Approximate Inference",
            "Algorithms: Belief Propagation",
            "Algorithms: Distributed and Parallel",
            "Algorithms: Exact Inference",
        ])
        conference = builder.get_result()

        now = datetime.datetime.utcnow()
        invitation = conference.open_submissions(due_date = now + datetime.timedelta(minutes = 10))

        note = openreview.Note(invitation = invitation.id,
            readers = ['everyone'],
            writers = ['~Test_User1', 'author@mail.com', 'author2@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'author@mail.com', 'author2@mail.com'],
                'authors': ['Test User', 'Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/sdfskdls.pdf',
                'subject_areas': [
                    'Algorithms: Approximate Inference',
                    'Algorithms: Belief Propagation'
                ]
            }
        )

        note = test_client.post_note(note)
        assert note

        conference.close_submissions()
        blinded_notes = conference.create_blind_submissions()
        paper_note = blinded_notes[0]
        conference.set_authors()
        conference.set_program_chairs(emails= ['programchair@auai.org'])
        conference.set_area_chairs(emails = ['areachair@auai.org'])
        conference.set_reviewers(emails = ['reviewer@auai.org', 'reviewer2@auai.org'])
        openreview.tools.add_assignment(client, paper_note.number, conference.id, 'reviewer@auai.org', individual_label='AnonReviewer', parent_label='Reviewers')
        openreview.tools.add_assignment(client, paper_note.number, conference.id, 'reviewer2@auai.org', individual_label='AnonReviewer', parent_label='Reviewers')
        openreview.tools.add_assignment(client, paper_note.number, conference.id, 'areachair@auai.org', individual_label='Area_Chair', parent_label='Area_Chairs')

        conference.open_reviews(release_to_authors=True)

        note = openreview.Note(invitation = 'auai.org/UAI/2020/Conference/-/Paper1/Official_Review',
            forum = paper_note.id,
            replyto = paper_note.id,
            readers = ['auai.org/UAI/2020/Conference/Program_Chairs',
            'auai.org/UAI/2020/Conference/Paper1/Area_Chairs',
            'auai.org/UAI/2020/Conference/Paper1/Reviewers/Submitted',
            'auai.org/UAI/2020/Conference/Paper1/Authors'],
            writers = ['auai.org/UAI/2020/Conference/Paper1/AnonReviewer1'],
            signatures = ['auai.org/UAI/2020/Conference/Paper1/AnonReviewer1'],
            content = {
                'title': 'Review title',
                'review': 'Paper is very good!',
                'rating': '9: Top 15% of accepted papers, strong accept',
                'confidence': '4: The reviewer is confident but not absolutely certain that the evaluation is correct'
            }
        )
        reviewer_client = helpers.create_user('reviewer@auai.org', 'Reviewer', 'UAI')
        review_note = reviewer_client.post_note(note)
        assert review_note

        conference.open_comments(name = 'Official_Comment', public = False, anonymous = True)

        comment_invitation_id = '{conference_id}/-/Paper{number}/Official_Comment'.format(conference_id = conference.id, number = paper_note.number)
        authors_group_id = '{conference_id}/Paper{number}/Authors'.format(conference_id = conference.id, number = paper_note.number)
        reviewers_group_id = '{conference_id}/Paper{number}/Reviewers/Submitted'.format(conference_id = conference.id, number = paper_note.number)
        anon_reviewers_group_id = '{conference_id}/Paper{number}/AnonReviewer1'.format(conference_id = conference.id, number = paper_note.number)
        acs_group_id = '{conference_id}/Paper{number}/Area_Chairs'.format(conference_id = conference.id, number = paper_note.number)

        comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = review_note.forum,
            replyto = review_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'reviewer@auai.org'],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Comment title',
                'comment': 'This is an comment'
            }
        )
        comment_note = reviewer_client.post_note(comment_note)

        messages = client.get_messages(subject='.*UAI.*A comment was posted. Paper Number: 1.*')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'programchair@auai.org'

        messages = client.get_messages(subject='.*UAI.*Comment posted to a paper in your area. Paper Number: 1.*')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'areachair@auai.org'

        messages = client.get_messages(subject='.*UAI.*Comment posted to a paper you are reviewing. Paper Number: 1.*')
        assert not messages

        messages = client.get_messages(subject='.*UAI.*Your submission has received a comment. Paper Title: .*')
        assert messages
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'author2@mail.com' in recipients
        assert 'author@mail.com' in recipients
        assert 'test@mail.com' in recipients

        note = openreview.Note(invitation = 'auai.org/UAI/2020/Conference/-/Paper1/Official_Review',
            forum = paper_note.id,
            replyto = paper_note.id,
            readers = ['auai.org/UAI/2020/Conference/Program_Chairs',
            'auai.org/UAI/2020/Conference/Paper1/Area_Chairs',
            'auai.org/UAI/2020/Conference/Paper1/Reviewers/Submitted',
            'auai.org/UAI/2020/Conference/Paper1/Authors'],
            writers = ['auai.org/UAI/2020/Conference/Paper1/AnonReviewer2'],
            signatures = ['auai.org/UAI/2020/Conference/Paper1/AnonReviewer2'],
            content = {
                'title': 'Review title',
                'review': 'Paper is very good!',
                'rating': '9: Top 15% of accepted papers, strong accept',
                'confidence': '4: The reviewer is confident but not absolutely certain that the evaluation is correct'
            }
        )
        reviewer2_client = helpers.create_user('reviewer2@auai.org', 'Reviewer', 'UAITwo')
        review_note = reviewer2_client.post_note(note)
        assert review_note

        comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = review_note.forum,
            replyto = review_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'reviewer@auai.org'],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Second Comment title',
                'comment': 'This is an a second comment to a review'
            }
        )
        comment_note = reviewer_client.post_note(comment_note)

        messages = client.get_messages(subject='.*UAI.*A comment was posted. Paper Number: 1.*')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['to'] == 'programchair@auai.org'
        assert messages[1]['content']['to'] == 'programchair@auai.org'

        messages = client.get_messages(subject='.*UAI.*Comment posted to a paper in your area. Paper Number: 1.*')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['to'] == 'areachair@auai.org'
        assert messages[1]['content']['to'] == 'areachair@auai.org'

        messages = client.get_messages(subject='.*UAI.*Comment posted to a paper you are reviewing. Paper Number: 1.*')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'reviewer2@auai.org'


        messages = client.get_messages(subject='.*UAI.*Your submission has received a comment. Paper Title: .*')
        assert messages
        assert len(messages) == 6
        recipients = [m['content']['to'] for m in messages]
        assert 'author2@mail.com' in recipients
        assert 'author@mail.com' in recipients
        assert 'test@mail.com' in recipients


    def test_notify_all_mandatory_readers(self, client, test_client):

        builder = openreview.conference.ConferenceBuilder(client)

        builder.set_conference_id('learningtheory.org/COLT/2018/Conference')
        builder.set_conference_name('Conference on Learning Theory')
        builder.set_conference_short_name('COLT 2018')
        builder.set_homepage_header({
        'title': 'COLT 2018',
        'subtitle': 'Conference on Learning Theory',
        'deadline': 'Submission Deadline: 11:00pm Eastern Standard Time, February 1, 2019',
        'date': 'June 25 - June 28, 2019',
        'website': 'http://learningtheory.org/colt2019/',
        'location': 'Phoenix, Arizona, United States'
        })
        builder.set_conference_submission_name('Full_Submission')
        builder.set_submission_public(True)
        builder.has_area_chairs(True)
        conference = builder.get_result()

        now = datetime.datetime.utcnow()
        invitation = conference.open_submissions(due_date = now + datetime.timedelta(minutes = 10))

        note = openreview.Note(invitation = invitation.id,
            readers = ['everyone'],
            writers = ['~Test_User1', 'author@colt.io', 'author2@colt.io'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'author@colt.io', 'author2@colt.io'],
                'authors': ['Test User', 'Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/sdfskdls.pdf'
            }
        )

        note = test_client.post_note(note)
        assert note

        conference.close_submissions()

        conference.set_authors()
        conference.set_program_chairs(emails= ['programchair@colt.io'])
        conference.open_comments(name = 'Official_Comment', public = False, anonymous = True, unsubmitted_reviewers= True)

        comment_invitation_id = '{conference_id}/-/Paper{number}/Official_Comment'.format(conference_id = conference.id, number = note.number)
        authors_group_id = '{conference_id}/Paper{number}/Authors'.format(conference_id = conference.id, number = note.number)
        reviewers_group_id = '{conference_id}/Paper{number}/Reviewers'.format(conference_id = conference.id, number = note.number)
        anon_reviewers_group_id = '{conference_id}/Paper{number}/AnonReviewer1'.format(conference_id = conference.id, number = note.number)
        acs_group_id = '{conference_id}/Paper{number}/Area_Chairs'.format(conference_id = conference.id, number = note.number)

        openreview.tools.add_assignment(client, note.number, conference.id, 'reviewer@colt.io')
        openreview.tools.add_assignment(client, note.number, conference.id, 'areachair@colt.io', individual_label='Area_Chair', parent_label='Area_Chairs')

        comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'reviewer@colt.io'],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Comment title',
                'comment': 'This is an comment'
            }
        )
        comment_note = client.post_note(comment_note)

        assert comment_note
        assert comment_note.forum == note.id

        messages = client.get_messages(to = 'author@colt.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        assert len(messages) == 10
        assert messages[8]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[9]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@colt.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@colt.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[COLT 2018] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@colt.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[COLT 2018] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@colt.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[COLT 2018] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        reply_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'test@mail.com'],
            signatures = [authors_group_id],
            content = {
                'title': 'Reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )
        reply_comment_note = test_client.post_note(reply_comment_note)

        messages = client.get_messages(to = 'author@colt.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@colt.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@colt.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[COLT 2018] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[0]['content']['subject'] == '[COLT 2018] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@colt.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[COLT 2018] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@colt.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[COLT 2018] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'

        reply2_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'reviewer@colt.io'],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Another reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply2_comment_note = client.post_note(reply2_comment_note)

        messages = client.get_messages(to = 'author@colt.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        assert len(messages) == 11
        assert messages[8]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[9]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[10]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@colt.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@colt.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[COLT 2018] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@colt.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[COLT 2018] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@colt.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[COLT 2018] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'

        pc_client = openreview.Client(baseurl = 'http://localhost:3000')
        assert pc_client is not None, "Client is none"
        res = pc_client.register_user(email = 'programchair@colt.io', first = 'Program', last = 'Chair', password = '1234')
        assert res, "Res i none"
        res = pc_client.activate_user('programchair@colt.io', {
            'names': [
                    {
                        'first': 'Program',
                        'last': 'Chair',
                        'username': '~Program_Chair2'
                    }
                ],
            'emails': ['programchair@colt.io'],
            'preferredEmail': 'programchair@colt.io'
            })
        assert res

        reply3_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, 'programchair@colt.io'],
            signatures = [conference.get_program_chairs_id()],
            content = {
                'title': 'Another reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply3_comment_note = pc_client.post_note(reply3_comment_note)

        messages = client.get_messages(to = 'author@colt.io')
        assert messages
        assert len(messages) == 5
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[4]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        assert len(messages) == 12
        assert messages[8]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[9]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[10]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[11]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@colt.io')
        assert messages
        assert len(messages) == 5
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'
        assert messages[4]['content']['subject'] == '[COLT 2018] Your submission has received a comment. Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@colt.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == '[COLT 2018] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] Comment posted to a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@colt.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == '[COLT 2018] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] Comment posted to a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@colt.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == '[COLT 2018] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] A comment was posted. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == 'OpenReview signup confirmation'