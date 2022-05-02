from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
from openreview.conference.builder import ReviewStage
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

    def test_notify_all(self, client, test_client, helpers):

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
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(name = 'Full_Submission', public = True, due_date = now + datetime.timedelta(minutes = 10), withdrawn_submission_reveal_authors=True, desk_rejected_submission_reveal_authors=True)
        builder.has_area_chairs(True)
        builder.use_legacy_anonids(True)
        conference = builder.get_result()

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = [conference.get_id(), '~SomeFirstName_User1', 'author@mail.com', 'author2@mail.com'],
            writers = [conference.get_id(), '~SomeFirstName_User1', 'author@mail.com', 'author2@mail.com'],
            signatures = ['~SomeFirstName_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'author@mail.com', 'author2@mail.com'],
                'authors': ['SomeFirstName User', 'Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        )

        note = test_client.post_note(note)
        assert note

        helpers.await_queue()

        logs = client.get_process_logs(id = note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        conference.setup_post_submission_stage(force=True)
        conference.set_program_chairs(emails= ['programchair@midl.io'])
        conference.set_comment_stage(openreview.CommentStage(unsubmitted_reviewers=True, reader_selection=True, email_pcs=True, authors=True))

        comment_invitation_id = '{conference_id}/Paper{number}/-/Official_Comment'.format(conference_id = conference.id, number = note.number)
        authors_group_id = '{conference_id}/Paper{number}/Authors'.format(conference_id = conference.id, number = note.number)
        reviewers_group_id = '{conference_id}/Paper{number}/Reviewers'.format(conference_id = conference.id, number = note.number)
        anon_reviewers_group_id = '{conference_id}/Paper{number}/AnonReviewer1'.format(conference_id = conference.id, number = note.number)
        acs_group_id = '{conference_id}/Paper{number}/Area_Chairs'.format(conference_id = conference.id, number = note.number)

        reviewer_client = helpers.create_user('reviewer@midl.io', 'Reviewer', 'MIDL')
        openreview.tools.add_assignment(client, note.number, conference.id, 'reviewer@midl.io')
        openreview.tools.add_assignment(client, note.number, conference.id, 'areachair@midl.io', individual_label='Area_Chair', parent_label='Area_Chairs')

        comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, anon_reviewers_group_id],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Comment title',
                'comment': 'This is an comment'
            }
        )
        comment_note = reviewer_client.post_note(comment_note)
        helpers.await_queue()

        logs = client.get_process_logs(id = comment_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        assert comment_note
        assert comment_note.forum == note.id

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['text'] == f'<p>AnonReviewer1 commented on your submission.</p>\n<p>Paper Number: 1</p>\n<p>Paper Title: &quot;Paper title&quot;</p>\n<p>Comment title: Comment title</p>\n<p>Comment: This is an comment</p>\n<p>To view the comment, click here: <a href=\"http://localhost:3030/forum?id={comment_note.forum}&amp;noteId={comment_note.id}\">http://localhost:3030/forum?id={comment_note.forum}&amp;noteId={comment_note.id}</a></p>\n'

        assert client.get_messages(to = 'test@mail.com', subject='MIDL 2019 has received your submission titled Paper title')
        assert client.get_messages(to = 'test@mail.com', subject='[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"')

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on a paper. Paper Number: 1, Paper Title: "Paper title"'

        reply_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [authors_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, authors_group_id],
            signatures = [authors_group_id],
            content = {
                'title': 'Reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply_comment_note = test_client.post_note(reply_comment_note)

        helpers.await_queue()

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        assert client.get_messages(to = 'test@mail.com', subject='MIDL 2019 has received your submission titled Paper title')
        assert client.get_messages(to = 'test@mail.com', subject='[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"')
        assert client.get_messages(to = 'test@mail.com', subject='[MIDL 2019] Your comment was received on Paper Number: 1, Paper Title: "Paper title"')

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on a paper. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] An author commented on a paper. Paper Number: 1, Paper Title: "Paper title"'

        reply2_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [reviewers_group_id, acs_group_id],
            writers = [conference.id, anon_reviewers_group_id],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Another reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply2_comment_note = reviewer_client.post_note(reply2_comment_note)

        helpers.await_queue()

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        assert client.get_messages(to = 'test@mail.com', subject='MIDL 2019 has received your submission titled Paper title')
        assert client.get_messages(to = 'test@mail.com', subject='[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"')
        assert client.get_messages(to = 'test@mail.com', subject='[MIDL 2019] Your comment was received on Paper Number: 1, Paper Title: "Paper title"')

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on a paper. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] An author commented on a paper. Paper Number: 1, Paper Title: "Paper title"'

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
            writers = [conference.id, conference.get_program_chairs_id()],
            signatures = [conference.get_program_chairs_id()],
            content = {
                'title': 'Another reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply3_comment_note = pc_client.post_note(reply3_comment_note)

        helpers.await_queue()

        messages = client.get_messages(to = 'author@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        assert client.get_messages(to = 'test@mail.com', subject='MIDL 2019 has received your submission titled Paper title')
        assert client.get_messages(to = 'test@mail.com', subject='[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"')
        assert client.get_messages(to = 'test@mail.com', subject='[MIDL 2019] Your comment was received on Paper Number: 1, Paper Title: "Paper title"')

        messages = client.get_messages(to = 'author2@mail.com')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'MIDL 2019 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@midl.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == '[MIDL 2019] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[MIDL 2019] Program Chairs commented on a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@midl.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[MIDL 2019] Program Chairs commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@midl.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == '[MIDL 2019] AnonReviewer1 commented on a paper. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[MIDL 2019] An author commented on a paper. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[3]['content']['subject'] == '[MIDL 2019] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'

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
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, due_date = now + datetime.timedelta(minutes = 10), subject_areas= [
            "Algorithms: Approximate Inference",
            "Algorithms: Belief Propagation",
            "Algorithms: Distributed and Parallel",
            "Algorithms: Exact Inference",
        ])
        builder.set_comment_stage(email_pcs = True, unsubmitted_reviewers = False, authors=True)
        builder.set_review_stage(openreview.ReviewStage(release_to_authors=True, release_to_reviewers=openreview.ReviewStage.Readers.REVIEWERS_SUBMITTED))
        builder.has_area_chairs(True)
        builder.use_legacy_anonids(True)
        conference = builder.get_result()

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = [conference.id, '~SomeFirstName_User1', 'author@mail.com', 'author2@mail.com'],
            writers = [conference.id, '~SomeFirstName_User1', 'author@mail.com', 'author2@mail.com'],
            signatures = ['~SomeFirstName_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'author@mail.com', 'author2@mail.com'],
                'authors': ['SomeFirstName User', 'Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf',
                'subject_areas': [
                    'Algorithms: Approximate Inference',
                    'Algorithms: Belief Propagation'
                ]
            }
        )

        note = test_client.post_note(note)
        assert note

        helpers.await_queue()

        logs = client.get_process_logs(id = note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        builder.set_submission_stage(double_blind = True, due_date = now, subject_areas= [
            "Algorithms: Approximate Inference",
            "Algorithms: Belief Propagation",
            "Algorithms: Distributed and Parallel",
            "Algorithms: Exact Inference",
        ])
        conference = builder.get_result()

        conference.setup_post_submission_stage(force=True)
        blinded_notes = conference.get_submissions()
        paper_note = blinded_notes[0]
        conference.set_program_chairs(emails= ['programchair@auai.org'])
        conference.set_area_chairs(emails = ['areachair@auai.org'])
        conference.set_reviewers(emails = ['reviewer@auai.org', 'reviewer2@auai.org'])
        conference.set_assignment('reviewer@auai.org', 1)
        conference.set_assignment('reviewer2@auai.org', 1)
        conference.set_assignment('areachair@auai.org', 1, True)

        conference.open_reviews()

        note = openreview.Note(invitation = 'auai.org/UAI/2020/Conference/Paper1/-/Official_Review',
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

        helpers.await_queue()

        logs = client.get_process_logs(id = review_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        messages = client.get_messages(subject='.*UAI.*A review has been received on Paper number: 1.*')
        assert len(messages) == 0

        messages = client.get_messages(subject='.*UAI.*Review posted to your assigned Paper number: 1.*')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'areachair@auai.org'

        messages = client.get_messages(subject='.*UAI.*Your review has been received on your assigned Paper number: 1, Paper title: .*')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'reviewer@auai.org'

        messages = client.get_messages(subject='.*UAI.*Review posted to your submission - Paper number: 1, Paper title: .*')
        assert messages
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'author2@mail.com' in recipients
        assert 'author@mail.com' in recipients
        assert 'test@mail.com' in recipients

        conference.set_comment_stage(openreview.CommentStage(email_pcs = True, unsubmitted_reviewers = False, authors=True))
        comment_invitation_id = '{conference_id}/Paper{number}/-/Official_Comment'.format(conference_id = conference.id, number = paper_note.number)
        authors_group_id = '{conference_id}/Paper{number}/Authors'.format(conference_id = conference.id, number = paper_note.number)
        reviewers_group_id = '{conference_id}/Paper{number}/Reviewers/Submitted'.format(conference_id = conference.id, number = paper_note.number)
        anon_reviewers_group_id = '{conference_id}/Paper{number}/AnonReviewer1'.format(conference_id = conference.id, number = paper_note.number)
        acs_group_id = '{conference_id}/Paper{number}/Area_Chairs'.format(conference_id = conference.id, number = paper_note.number)

        comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = review_note.forum,
            replyto = review_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, anon_reviewers_group_id],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Comment title',
                'comment': 'This is an comment'
            }
        )
        comment_note = reviewer_client.post_note(comment_note)

        helpers.await_queue()

        logs = client.get_process_logs(id = comment_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        messages = client.get_messages(subject='.*UAI.*AnonReviewer1 commented on a paper. Paper Number: 1.*')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'programchair@auai.org'

        messages = client.get_messages(subject='.*UAI.*AnonReviewer1 commented on a paper in your area. Paper Number: 1.*')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'areachair@auai.org'

        messages = client.get_messages(subject='.*UAI.*AnonReviewer1 commented on a paper you are reviewing. Paper Number: 1.*')
        assert not messages

        messages = client.get_messages(subject='.*UAI.*AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: .*')
        assert messages
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'author2@mail.com' in recipients
        assert 'author@mail.com' in recipients
        assert 'test@mail.com' in recipients

        note = openreview.Note(invitation = 'auai.org/UAI/2020/Conference/Paper1/-/Official_Review',
            forum = paper_note.id,
            replyto = paper_note.id,
            readers = ['auai.org/UAI/2020/Conference/Program_Chairs',
            'auai.org/UAI/2020/Conference/Paper1/Area_Chairs',
            'auai.org/UAI/2020/Conference/Paper1/Reviewers/Submitted',
            'auai.org/UAI/2020/Conference/Paper1/Authors'],
            writers = ['auai.org/UAI/2020/Conference/Paper1/AnonReviewer2'],
            signatures = ['auai.org/UAI/2020/Conference/Paper1/AnonReviewer2'],
            content = {
                'title': 'Review title 2',
                'review': 'Paper is very good!',
                'rating': '9: Top 15% of accepted papers, strong accept',
                'confidence': '4: The reviewer is confident but not absolutely certain that the evaluation is correct'
            }
        )
        reviewer2_client = helpers.create_user('reviewer2@auai.org', 'Reviewer', 'UAITwo')
        review_note = reviewer2_client.post_note(note)
        assert review_note

        helpers.await_queue()

        logs = client.get_process_logs(id = review_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        messages = client.get_messages(subject='.*UAI.*A review has been received on Paper number: 1.*', to='programchair@auai.org')
        assert len(messages) == 0

        messages = client.get_messages(subject='.*UAI.*Review posted to your assigned Paper number: 1.*', to='reviewer@auai.org')
        assert messages
        assert len(messages) == 1

        messages = client.get_messages(subject='.*UAI.*Review posted to your assigned Paper number: 1.*', to='areachair@auai.org')
        assert messages
        assert len(messages) == 2

        messages = client.get_messages(subject='.*UAI.*Your review has been received on your assigned Paper number: 1, Paper title: .*', to='reviewer2@auai.org')
        assert messages
        assert len(messages) == 1

        messages = client.get_messages(subject='.*UAI.*Review posted to your submission - Paper number: 1, Paper title: .*')
        assert messages
        assert len(messages) == 6
        recipients = [m['content']['to'] for m in messages]
        assert 'author2@mail.com' in recipients
        assert 'author@mail.com' in recipients
        assert 'test@mail.com' in recipients

        comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = review_note.forum,
            replyto = review_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, anon_reviewers_group_id],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Second Comment title',
                'comment': 'This is an a second comment to a review'
            }
        )
        comment_note = reviewer_client.post_note(comment_note)

        helpers.await_queue()

        logs = client.get_process_logs(id = comment_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        messages = client.get_messages(subject='.*UAI.*AnonReviewer1 commented on a paper. Paper Number: 1.*', to='programchair@auai.org')
        assert messages
        assert len(messages) == 2

        messages = client.get_messages(subject='.*UAI.*AnonReviewer1 commented on a paper in your area. Paper Number: 1.*', to='areachair@auai.org')
        assert messages
        assert len(messages) == 2

        messages = client.get_messages(subject='.*UAI.*AnonReviewer1 commented on a paper you are reviewing. Paper Number: 1.*', to='reviewer2@auai.org')
        assert messages
        assert len(messages) == 1

        messages = client.get_messages(subject='.*UAI.*AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: .*')
        assert messages
        assert len(messages) == 6
        recipients = [m['content']['to'] for m in messages]
        assert 'author2@mail.com' in recipients
        assert 'author@mail.com' in recipients
        assert 'test@mail.com' in recipients

    def test_remind_reviewers(self, client, helpers):

        ac_client = helpers.create_user('areachair@auai.org', 'Area', 'ChairUAI')
        subject = 'Remind to reviewers'
        recipients = ['reviewer@auai.org']
        message = 'This is a reminder'
        response = ac_client.post_message(subject, recipients, message)
        assert response

        messages = client.get_messages(subject='Remind to reviewers')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'reviewer@auai.org'

        recipients = ['auai.org/UAI/2020/Conference/Paper1/AnonReviewer1']
        response = ac_client.post_message(subject, recipients, 'This is a second reminder')
        assert response

        messages_2 = client.get_messages(subject='.*Remind to reviewers.*')
        assert messages_2
        assert len(messages_2) == 2
        assert messages_2[0]['content']['to'] == 'reviewer@auai.org'
        assert messages_2[1]['content']['to'] == 'reviewer@auai.org'

        with pytest.raises(openreview.OpenReviewException, match=r'Group Not Found: auai.org/UAI/2020/Conference/Paper2/AnonReviewer1'):
            ac_client.post_message(subject, ['auai.org/UAI/2020/Conference/Paper2/AnonReviewer1'], 'This is an invalid reminder')

        ac_client.post_message(subject, ['auai.org/UAI/2020/Conference/Reviewers'], 'This is an invalid reminder')

    def test_notify_all_mandatory_readers(self, client, test_client, helpers):

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
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(name = 'Full_Submission', public = True, due_date = now + datetime.timedelta(minutes = 10), withdrawn_submission_reveal_authors=True, desk_rejected_submission_reveal_authors=True)
        builder.has_area_chairs(True)
        builder.set_comment_stage(unsubmitted_reviewers = True, reader_selection = True, email_pcs = True, authors=True)
        builder.use_legacy_anonids(True)
        conference = builder.get_result()

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = [conference.get_id(), '~SomeFirstName_User1', 'author@colt.io', 'author2@colt.io'],
            writers = [conference.get_id(), '~SomeFirstName_User1', 'author@colt.io', 'author2@colt.io'],
            signatures = ['~SomeFirstName_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'author@colt.io', 'author2@colt.io'],
                'authors': ['SomeFirstName User', 'Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        )

        note = test_client.post_note(note)
        assert note

        helpers.await_queue()

        logs = client.get_process_logs(id = note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        conference.setup_post_submission_stage(force=True)
        conference.set_program_chairs(emails = ['programchair@colt.io'])
        conference.set_comment_stage(openreview.CommentStage(unsubmitted_reviewers = True, reader_selection = True, email_pcs = True, authors=True))


        comment_invitation_id = '{conference_id}/Paper{number}/-/Official_Comment'.format(conference_id = conference.id, number = note.number)
        authors_group_id = '{conference_id}/Paper{number}/Authors'.format(conference_id = conference.id, number = note.number)
        reviewers_group_id = '{conference_id}/Paper{number}/Reviewers'.format(conference_id = conference.id, number = note.number)
        anon_reviewers_group_id = '{conference_id}/Paper{number}/AnonReviewer1'.format(conference_id = conference.id, number = note.number)
        acs_group_id = '{conference_id}/Paper{number}/Area_Chairs'.format(conference_id = conference.id, number = note.number)

        reviewer_client = helpers.create_user('reviewer@colt.io', 'Reviewer', 'COLT')
        openreview.tools.add_assignment(client, note.number, conference.id, 'reviewer@colt.io')
        openreview.tools.add_assignment(client, note.number, conference.id, 'areachair@colt.io', individual_label='Area_Chair', parent_label='Area_Chairs')

        comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, anon_reviewers_group_id],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Comment title',
                'comment': 'This is an comment'
            }
        )
        comment_note = reviewer_client.post_note(comment_note)

        helpers.await_queue()

        logs = client.get_process_logs(id = comment_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        assert comment_note
        assert comment_note.forum == note.id

        messages = client.get_messages(to = 'author@colt.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        assert client.get_messages(to = 'test@mail.com', subject='COLT 2018 has received your submission titled Paper title')
        assert client.get_messages(to = 'test@mail.com', subject='[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"')

        messages = client.get_messages(to = 'author2@colt.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@colt.io')
        assert messages
        assert len(messages) == 2
        assert messages[1]['content']['subject'] == '[COLT 2018] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@colt.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@colt.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper. Paper Number: 1, Paper Title: "Paper title"'
        reply_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, authors_group_id],
            signatures = [authors_group_id],
            content = {
                'title': 'Reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )
        reply_comment_note = test_client.post_note(reply_comment_note)

        helpers.await_queue()

        logs = client.get_process_logs(id = reply_comment_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        messages = client.get_messages(to = 'author@colt.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@colt.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@colt.io')
        assert messages
        assert len(messages) == 3
        assert messages[1]['content']['subject'] == '[COLT 2018] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] An author commented on a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        assert client.get_messages(to = 'test@mail.com', subject='[COLT 2018] Your comment was received on Paper Number: 1, Paper Title: "Paper title"')

        messages = client.get_messages(to = 'areachair@colt.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@colt.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] An author commented on a paper. Paper Number: 1, Paper Title: "Paper title"'

        reply2_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, anon_reviewers_group_id],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Another reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply2_comment_note = reviewer_client.post_note(reply2_comment_note)

        helpers.await_queue()

        logs = client.get_process_logs(id = reply2_comment_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        messages = client.get_messages(to = 'author@colt.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        assert client.get_messages(to = 'test@mail.com', subject='[COLT 2018] Your comment was received on Paper Number: 1, Paper Title: "Paper title"')
        assert len(client.get_messages(to = 'test@mail.com', subject='[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"')) == 2

        messages = client.get_messages(to = 'author2@colt.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@colt.io')
        assert messages
        assert len(messages) == 4
        assert messages[1]['content']['subject'] == '[COLT 2018] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] An author commented on a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@colt.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] An author commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@colt.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] An author commented on a paper. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper. Paper Number: 1, Paper Title: "Paper title"'

        pc_client = helpers.create_user('programchair@colt.io', 'ProgramChair', 'COLT')

        reply3_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, conference.get_program_chairs_id()],
            signatures = [conference.get_program_chairs_id()],
            content = {
                'title': 'Another reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply3_comment_note = pc_client.post_note(reply3_comment_note)

        helpers.await_queue()

        logs = client.get_process_logs(id = reply3_comment_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        messages = client.get_messages(to = 'author@colt.io')
        assert messages
        assert len(messages) == 5
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[4]['content']['subject'] == '[COLT 2018] Program Chairs commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        assert client.get_messages(to = 'test@mail.com', subject='[COLT 2018] Program Chairs commented on your submission. Paper Number: 1, Paper Title: "Paper title"')

        messages = client.get_messages(to = 'author2@colt.io')
        assert messages
        assert len(messages) == 5
        assert messages[0]['content']['subject'] == 'COLT 2018 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[4]['content']['subject'] == '[COLT 2018] Program Chairs commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@colt.io')
        assert messages
        assert len(messages) == 5
        assert messages[1]['content']['subject'] == '[COLT 2018] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] An author commented on a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'
        assert messages[4]['content']['subject'] == '[COLT 2018] Program Chairs commented on a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@colt.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] An author commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2018] Program Chairs commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@colt.io')
        assert messages
        assert len(messages) == 5
        assert messages[0]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2018] An author commented on a paper. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2018] AnonReviewer1 commented on a paper. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[4]['content']['subject'] == '[COLT 2018] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'

    def test_notify_except_program_chairs(self, client, test_client, helpers):

        builder = openreview.conference.ConferenceBuilder(client)

        builder.set_conference_id('learningtheory.org/COLT/2017/Conference')
        builder.set_conference_name('Conference on Learning Theory')
        builder.set_conference_short_name('COLT 2017')
        builder.set_homepage_header({
        'title': 'COLT 2017',
        'subtitle': 'Conference on Learning Theory',
        'deadline': 'Submission Deadline: 11:00pm Eastern Standard Time, February 1, 2019',
        'date': 'June 25 - June 28, 2019',
        'website': 'http://learningtheory.org/colt2017/',
        'location': 'Phoenix, Arizona, United States'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(name = 'Full_Submission', public= True, due_date = now + datetime.timedelta(minutes = 10), withdrawn_submission_reveal_authors=True, desk_rejected_submission_reveal_authors=True)
        builder.has_area_chairs(True)
        builder.set_comment_stage(unsubmitted_reviewers = True, reader_selection=True, authors=True)
        builder.use_legacy_anonids(True)
        conference = builder.get_result()

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = [conference.id, '~SomeFirstName_User1', 'author@colt17.io', 'author2@colt17.io'],
            writers = [conference.id, '~SomeFirstName_User1', 'author@colt17.io', 'author2@colt17.io'],
            signatures = ['~SomeFirstName_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'author@colt17.io', 'author2@colt17.io'],
                'authors': ['SomeFirstName User', 'Melisa Bok', 'Andrew Mc'],
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        )

        note = test_client.post_note(note)
        assert note

        helpers.await_queue()

        logs = client.get_process_logs(id = note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        conference.setup_post_submission_stage(force=True)
        conference.set_program_chairs(emails = ['programchair@colt17.io'])
        conference.set_comment_stage(openreview.CommentStage(unsubmitted_reviewers = True, reader_selection=True, authors=True))

        comment_invitation_id = '{conference_id}/Paper{number}/-/Official_Comment'.format(conference_id = conference.id, number = note.number)
        authors_group_id = '{conference_id}/Paper{number}/Authors'.format(conference_id = conference.id, number = note.number)
        reviewers_group_id = '{conference_id}/Paper{number}/Reviewers'.format(conference_id = conference.id, number = note.number)
        anon_reviewers_group_id = '{conference_id}/Paper{number}/AnonReviewer1'.format(conference_id = conference.id, number = note.number)
        acs_group_id = '{conference_id}/Paper{number}/Area_Chairs'.format(conference_id = conference.id, number = note.number)

        reviewer_client = helpers.create_user('reviewer@colt17.io', 'Reviewer', 'COLTIO')
        openreview.tools.add_assignment(client, note.number, conference.id, 'reviewer@colt17.io')
        openreview.tools.add_assignment(client, note.number, conference.id, 'areachair@colt17.io', individual_label='Area_Chair', parent_label='Area_Chairs')

        comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, anon_reviewers_group_id],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': 'Comment title',
                'comment': 'This is an comment'
            }
        )
        comment_note = reviewer_client.post_note(comment_note)

        helpers.await_queue()

        logs = client.get_process_logs(id = comment_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        assert comment_note
        assert comment_note.forum == note.id

        messages = client.get_messages(to = 'author@colt17.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'COLT 2017 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2017] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        assert client.get_messages(to = 'test@mail.com', subject='COLT 2017 has received your submission titled Paper title')
        assert client.get_messages(to = 'test@mail.com', subject='[COLT 2017] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"')

        messages = client.get_messages(to = 'author2@colt17.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'COLT 2017 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2017] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@colt17.io')
        assert messages
        assert len(messages) == 2
        assert messages[1]['content']['subject'] == '[COLT 2017] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@colt17.io')
        assert messages
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == '[COLT 2017] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@colt17.io')
        assert len(messages) == 0

        reply_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, authors_group_id],
            signatures = [authors_group_id],
            content = {
                'title': 'Reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )
        reply_comment_note = test_client.post_note(reply_comment_note)

        helpers.await_queue()

        logs = client.get_process_logs(id = reply_comment_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        messages = client.get_messages(to = 'author@colt17.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'COLT 2017 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2017] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2017] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'author2@colt17.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == 'COLT 2017 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2017] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2017] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        assert client.get_messages(to = 'test@mail.com', subject='[COLT 2017] Your comment was received on Paper Number: 1, Paper Title: "Paper title"')

        messages = client.get_messages(to = 'reviewer@colt17.io')
        assert messages
        assert len(messages) == 3
        assert messages[1]['content']['subject'] == '[COLT 2017] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2017] An author commented on a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@colt17.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == '[COLT 2017] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@colt17.io')
        assert len(messages) == 0

        pc_client = helpers.create_user('programchair@colt17.io', 'Program', 'COLTIO')

        reply3_comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = comment_note.id,
            readers = [authors_group_id, reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            writers = [conference.id, conference.get_program_chairs_id()],
            signatures = [conference.get_program_chairs_id()],
            content = {
                'title': 'Another reply to comment title',
                'comment': 'This is a reply to the comment'
            }
        )

        reply3_comment_note = pc_client.post_note(reply3_comment_note)

        helpers.await_queue()

        logs = client.get_process_logs(id = reply3_comment_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        messages = client.get_messages(to = 'author@colt17.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == 'COLT 2017 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2017] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2017] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2017] Program Chairs commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        assert client.get_messages(to = 'test@mail.com', subject='[COLT 2017] Program Chairs commented on your submission. Paper Number: 1, Paper Title: "Paper title"')

        messages = client.get_messages(to = 'author2@colt17.io')
        assert messages
        assert len(messages) == 4
        assert messages[0]['content']['subject'] == 'COLT 2017 has received your submission titled Paper title'
        assert messages[1]['content']['subject'] == '[COLT 2017] AnonReviewer1 commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2017] An author commented on your submission. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2017] Program Chairs commented on your submission. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'reviewer@colt17.io')
        assert messages
        assert len(messages) == 4
        assert messages[1]['content']['subject'] == '[COLT 2017] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2017] An author commented on a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[3]['content']['subject'] == '[COLT 2017] Program Chairs commented on a paper you are reviewing. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'areachair@colt17.io')
        assert messages
        assert len(messages) == 3
        assert messages[0]['content']['subject'] == '[COLT 2017] AnonReviewer1 commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[1]['content']['subject'] == '[COLT 2017] An author commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'
        assert messages[2]['content']['subject'] == '[COLT 2017] Program Chairs commented on a paper in your area. Paper Number: 1, Paper Title: "Paper title"'

        messages = client.get_messages(to = 'programchair@colt17.io')
        assert messages
        assert len(messages) == 2
        assert messages[0]['content']['subject'] == 'OpenReview signup confirmation'
        assert messages[1]['content']['subject'] == '[COLT 2017] Your comment was received on Paper Number: 1, Paper Title: "Paper title"'

    def test_notify_except_authors_are_program_chairs(self, client, helpers, test_client):

        builder = openreview.conference.ConferenceBuilder(client)

        builder.set_conference_id('learningtheory.org/COLT/2017/Conference')
        builder.set_conference_name('Conference on Learning Theory')
        builder.set_conference_short_name('COLT 2017')
        builder.set_homepage_header({
        'title': 'COLT 2017',
        'subtitle': 'Conference on Learning Theory',
        'deadline': 'Submission Deadline: 11:00pm Eastern Standard Time, February 1, 2019',
        'date': 'June 25 - June 28, 2019',
        'website': 'http://learningtheory.org/colt2017/',
        'location': 'Phoenix, Arizona, United States'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(name = 'Full_Submission', public= True, due_date = now + datetime.timedelta(minutes = 10) )
        builder.has_area_chairs(True)
        builder.set_comment_stage(unsubmitted_reviewers = True, reader_selection = True, authors=True)
        builder.use_legacy_anonids(True)
        conference = builder.get_result()

        conference.set_program_chairs(emails = ['author2@colt17.io'])

        notes = list(conference.get_submissions())
        assert notes
        note = notes[0]

        comment_invitation_id = '{conference_id}/Paper{number}/-/Official_Comment'.format(conference_id = conference.id, number = note.number)
        authors_group_id = '{conference_id}/Paper{number}/Authors'.format(conference_id = conference.id, number = note.number)
        reviewers_group_id = '{conference_id}/Paper{number}/Reviewers'.format(conference_id = conference.id, number = note.number)
        anon_reviewers_group_id = '{conference_id}/Paper{number}/AnonReviewer1'.format(conference_id = conference.id, number = note.number)
        acs_group_id = '{conference_id}/Paper{number}/Area_Chairs'.format(conference_id = conference.id, number = note.number)

        reviewer_client = openreview.Client(username='reviewer@colt17.io', password='1234')
        openreview.tools.add_assignment(client, note.number, conference.id, 'reviewer@colt17.io')
        openreview.tools.add_assignment(client, note.number, conference.id, 'areachair@colt17.io', individual_label='Area_Chair', parent_label='Area_Chairs')

        comment_note = openreview.Note(invitation = comment_invitation_id,
            forum = note.id,
            replyto = note.id,
            readers = [reviewers_group_id, acs_group_id, conference.get_program_chairs_id()],
            nonreaders = [authors_group_id],
            writers = [conference.id, anon_reviewers_group_id],
            signatures = [anon_reviewers_group_id],
            content = {
                'title': '[NO_AUTHORS] comment',
                'comment': 'This is an comment'
            }
        )
        comment_note = reviewer_client.post_note(comment_note)

        helpers.await_queue()

        logs = client.get_process_logs(id = comment_note.id)
        assert logs
        assert logs[0]['status'] == 'ok'

        assert comment_note
        assert comment_note.forum == note.id

        messages = client.get_messages(to = 'author@colt17.io')
        assert messages
        expected_messages = [m for m in messages if '[NO_AUTHORS]' in m['content']['text']]
        assert len(expected_messages) == 0

        messages = client.get_messages(to = 'test@mail.com')
        assert messages
        expected_messages = [m for m in messages if '[NO_AUTHORS]' in m['content']['text']]
        assert len(expected_messages) == 0

        messages = client.get_messages(to = 'author2@colt17.io')
        assert messages
        expected_messages = [m for m in messages if '[NO_AUTHORS]' in m['content']['text']]
        assert len(expected_messages) == 0

        messages = client.get_messages(to = 'reviewer@colt17.io')
        assert messages
        expected_messages = [m for m in messages if '[NO_AUTHORS]' in m['content']['text']]
        assert len(expected_messages) == 1

        messages = client.get_messages(to = 'areachair@colt17.io')
        assert messages
        expected_messages = [m for m in messages if '[NO_AUTHORS]' in m['content']['text']]
        assert len(expected_messages) == 1
