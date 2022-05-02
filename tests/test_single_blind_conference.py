from __future__ import absolute_import, division, print_function, unicode_literals
from selenium.webdriver.common.by import By
import openreview
import pytest
import requests
import datetime
import time
import os

class TestSingleBlindConference():

    def test_create_single_blind_conference(self, client, selenium, request_page) :

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        builder.set_conference_name('2018 NIPS MLITS Workshop')
        builder.set_homepage_header({
        'title': '2018 NIPS MLITS Workshop',
        'subtitle': 'Machine Learning for Intelligent Transportation Systems',
        'deadline': 'October 12, 2018, 11:59 pm UTC',
        'date': 'December 3-8, 2018',
        'website': 'https://sites.google.com/site/nips2018mlits/home',
        'location': 'Montreal, Canada',
        'instructions': ''
        })
        builder.set_conference_program_chairs_ids(['pc2@mail.com'])
        builder.has_area_chairs(True)

        conference = builder.get_result()
        assert conference, 'conference is None'

        groups = conference.get_conference_groups()
        assert groups
        assert groups[0].id == 'NIPS.cc'
        assert groups[0].readers == ['everyone']
        assert groups[0].nonreaders == []
        assert groups[0].writers == ['NIPS.cc']
        assert groups[0].signatures == ['~Super_User1']
        assert groups[0].signatories == ['NIPS.cc']
        assert groups[0].members == []
        assert groups[1].id == 'NIPS.cc/2018'
        assert groups[1].readers == ['everyone']
        assert groups[1].nonreaders == []
        assert groups[1].writers == ['NIPS.cc/2018']
        assert groups[1].signatures == ['~Super_User1']
        assert groups[1].signatories == ['NIPS.cc/2018']
        assert groups[1].members == []
        assert groups[2].id == 'NIPS.cc/2018/Workshop'
        assert groups[2].readers == ['everyone']
        assert groups[2].nonreaders == []
        assert groups[2].writers == ['NIPS.cc/2018/Workshop']
        assert groups[2].signatures == ['~Super_User1']
        assert groups[2].signatories == ['NIPS.cc/2018/Workshop']
        assert groups[2].members == []
        assert groups[3].id == 'NIPS.cc/2018/Workshop/MLITS'
        assert groups[3].readers == ['everyone']
        assert groups[3].nonreaders == []
        assert groups[3].writers == ['NIPS.cc/2018/Workshop/MLITS']
        assert groups[3].signatures == ['NIPS.cc/2018/Workshop/MLITS']
        assert groups[3].signatories == ['NIPS.cc/2018/Workshop/MLITS']
        assert groups[3].members == ['NIPS.cc/2018/Workshop/MLITS/Program_Chairs']
        assert '"title": "2018 NIPS MLITS Workshop"' in groups[3].web
        assert '"subtitle": "Machine Learning for Intelligent Transportation Systems"' in groups[3].web
        assert '"location": "Montreal, Canada"' in groups[3].web
        assert '"date": "December 3-8, 2018"' in groups[3].web
        assert '"website": "https://sites.google.com/site/nips2018mlits/home"' in groups[3].web
        assert '"deadline": "October 12, 2018, 11:59 pm UTC"' in groups[3].web

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS", wait_for_element='header')

        assert "NIPS 2018 Workshop MLITS | OpenReview" in selenium.title
        header = selenium.find_element_by_id('header')
        assert header
        assert "2018 NIPS MLITS Workshop" == header.find_element_by_tag_name("h1").text
        assert "Machine Learning for Intelligent Transportation Systems" == header.find_element_by_tag_name("h3").text
        assert "Montreal, Canada" == header.find_element_by_xpath(".//span[@class='venue-location']").text
        assert "December 3-8, 2018" == header.find_element_by_xpath(".//span[@class='venue-date']").text
        assert "https://sites.google.com/site/nips2018mlits/home" == header.find_element_by_xpath(".//span[@class='venue-website']/a").text
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 0
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel

    def test_enable_submissions(self, client, selenium, request_page):


        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        now = datetime.datetime.utcnow()
        builder.has_area_chairs(True)
        builder.set_submission_stage(start_date = now + datetime.timedelta(minutes = 10), due_date = now + datetime.timedelta(minutes = 40), public=True)

        conference = builder.get_result()
        assert conference, 'conference is None'

        invitation = client.get_invitation(conference.get_submission_id())
        assert invitation
        assert invitation.cdate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 10))
        assert invitation.duedate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 40))
        assert invitation.expdate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 70))

        posted_invitation = client.get_invitation(id = 'NIPS.cc/2018/Workshop/MLITS/-/Submission')
        assert posted_invitation
        assert posted_invitation.cdate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 10))
        assert posted_invitation.duedate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 40))
        assert posted_invitation.expdate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 70))

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS", wait_for_element='invitation')

        assert "NIPS 2018 Workshop MLITS | OpenReview" in selenium.title
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 0

        builder.set_submission_stage(start_date = now - datetime.timedelta(minutes = 10), due_date = now + datetime.timedelta(minutes = 40), public=True)
        conference = builder.get_result()
        invitation = client.get_invitation(conference.get_submission_id())
        assert invitation
        assert invitation.cdate == openreview.tools.datetime_millis(now - datetime.timedelta(minutes = 10))
        assert invitation.duedate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 40))
        assert invitation.expdate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 70))

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS", wait_for_element='invitation')

        assert "NIPS 2018 Workshop MLITS | OpenReview" in selenium.title
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'NIPS 2018 Workshop MLITS Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 0
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_tag_name('ul')) == 0

    def test_post_submissions(self, client, test_client, peter_client, selenium, request_page, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        builder.set_conference_short_name('MLITS 2018')
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(
            due_date = now + datetime.timedelta(minutes = 40),
            public=True,
            email_pcs=True,
            create_groups=False,
            withdrawn_submission_public=True,
            withdrawn_submission_reveal_authors=True,
            desk_rejected_submission_public=True,
            desk_rejected_submission_reveal_authors=True)

        builder.has_area_chairs(True)
        conference = builder.get_result()

        invitation = client.get_invitation(conference.get_submission_id())
        assert invitation
        assert invitation.id == 'NIPS.cc/2018/Workshop/MLITS/-/Submission'
        assert invitation.reply['content']
        content = invitation.reply['content']
        assert content.get('title')
        assert content.get('abstract')
        assert content.get('authorids')
        assert content.get('authors')
        assert not content.get('subject_areas')
        assert not content.get('archival_status')

        note = openreview.Note(invitation = invitation.id,
            readers = [conference.id, '~SomeFirstName_User1', 'peter@mail.com', 'andrew@mail.com'],
            writers = [conference.id, '~SomeFirstName_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~SomeFirstName_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc']
            }
        )
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note.content['pdf'] = url
        note = test_client.post_note(note)

        helpers.await_queue()
        note = client.get_note(note.id)

        process_logs = client.get_process_logs(id = note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = 'MLITS 2018 has received your submission titled Paper title')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        assert 'andrew@mail.com' in recipients

        messages = client.get_messages(subject = 'MLITS 2018 has received a new submission titled Paper title')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'pc2@mail.com' in recipients

        conference.setup_final_deadline_stage()

        submissions = conference.get_submissions(sort='tmdate')
        assert len(submissions) == 1
        assert submissions[0].readers == ['everyone']

        # Author user
        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS", test_client.token, wait_for_element='notes')
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'NIPS 2018 Workshop MLITS Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 1
        console = tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')[0]
        assert 'Author Console' == console.find_element_by_tag_name('a').text
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_class_name('activity-list')) == 1
        allsubmissions_tab = tabs.find_element_by_id('all-submissions')
        assert allsubmissions_tab
        assert len(allsubmissions_tab.find_element_by_class_name('submissions-list').find_elements_by_tag_name('li')) == 2

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS/Authors", test_client.token, wait_for_element='your-submissions')
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('console-table')
        assert len(papers.find_elements_by_tag_name('tr')) == 2

        # Guest user
        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS", wait_for_element='all-submissions')
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'NIPS 2018 Workshop MLITS Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 0
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_class_name('activity-list')) == 0
        allsubmissions_tab = tabs.find_element_by_id('all-submissions')
        assert allsubmissions_tab
        assert len(allsubmissions_tab.find_element_by_class_name('submissions-list').find_elements_by_tag_name('li')) == 2

        # Co-author user
        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS", peter_client.token, wait_for_element='all-submissions')
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'NIPS 2018 Workshop MLITS Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 1
        console = tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')[0]
        assert 'Author Console' == console.find_element_by_tag_name('a').text
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_class_name('activity-list')) == 1
        allsubmissions_tab = tabs.find_element_by_id('all-submissions')
        assert allsubmissions_tab
        assert len(allsubmissions_tab.find_element_by_class_name('submissions-list').find_elements_by_tag_name('li')) == 2

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS/Authors", peter_client.token, wait_for_element='your-submissions')
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('console-table')
        assert len(papers.find_elements_by_tag_name('tr')) == 2

    def test_close_submission(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        builder.has_area_chairs(True)
        conference = builder.get_result()

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/-/Submission')
        submission = notes[0]
        submission.content['title'] = 'New paper title'
        test_client.post_note(submission)

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/-/Submission')
        assert 'New paper title' == notes[0].content['title']
        assert '~SomeFirstName_User1' in notes[0].writers
        assert 'peter@mail.com' in notes[0].writers
        assert 'andrew@mail.com' in notes[0].writers

        request_page(selenium, "http://localhost:3030/forum?id=" + submission.id, test_client.token, by=By.CLASS_NAME, wait_for_element='edit_button')

        assert len(selenium.find_elements_by_class_name('edit_button')) == 1
        assert len(selenium.find_elements_by_class_name('trash_button')) == 1

    def test_open_comments(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        builder.has_area_chairs(True)
        conference = builder.get_result()

        conference.set_comment_stage(openreview.CommentStage(authors=True))

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/-/Submission')
        submission = notes[0]
        request_page(selenium, "http://localhost:3030/forum?id=" + submission.id, test_client.token, by=By.CLASS_NAME, wait_for_element='reply_row')

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 2
        assert 'Official Comment' == reply_row.find_elements_by_class_name('btn')[0].text
        assert 'Withdraw' == reply_row.find_elements_by_class_name('btn')[1].text

    def test_close_comments(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        builder.has_area_chairs(True)
        conference = builder.get_result()

        conference.close_comments('Official_Comment')

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/-/Submission')
        submission = notes[0]
        request_page(selenium, "http://localhost:3030/forum?id=" + submission.id, test_client.token, by=By.CLASS_NAME, wait_for_element='reply_row')

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 1
        assert 'Withdraw' == reply_row.find_elements_by_class_name('btn')[0].text

    def test_open_reviews(self, client, test_client, selenium, request_page, helpers):

        now = datetime.datetime.utcnow()
        reviewer_client = openreview.Client(baseurl = 'http://localhost:3000')
        assert reviewer_client is not None, "Client is none"
        res = reviewer_client.register_user(email = 'reviewer@mail.com', first = 'Reviewer', last = 'SomeLastName', password = '1234')
        assert res, "Res i none"
        res = reviewer_client.activate_user('reviewer@mail.com', {
            'names': [
                    {
                        'first': 'Reviewer',
                        'last': 'SomeLastName',
                        'username': '~Reviewer_SomeLastName1'
                    }
                ],
            'emails': ['reviewer@mail.com'],
            'preferredEmail': 'reviewer@mail.com'
            })
        assert res, "Res i none"
        group = reviewer_client.get_group(id = 'reviewer@mail.com')
        assert group
        assert group.members == ['~Reviewer_SomeLastName1']

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/-/Submission')
        submission = notes[0]

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        builder.set_conference_short_name('MLITS 2018')
        builder.has_area_chairs(True)
        builder.use_legacy_anonids(True)
        builder.set_review_stage(openreview.ReviewStage(due_date = now + datetime.timedelta(minutes = 100), additional_fields = {
            'rating': {
                'order': 3,
                'value-dropdown': [
                    '5',
                    '4',
                    '3',
                    '2',
                    '1'
                ],
                'required': True
            }
        }, release_to_reviewers=openreview.ReviewStage.Readers.REVIEWERS_SUBMITTED))
        conference = builder.get_result()
        conference.set_program_chairs(emails = ['pc2@mail.com'])
        conference.set_area_chairs(emails = ['ac2@mail.com'])
        conference.set_reviewers(emails = ['reviewer@mail.com', 'reviewer3@mail.com'])

        conference.set_assignment('ac2@mail.com', submission.number, is_area_chair = True)
        conference.set_assignment('reviewer@mail.com', submission.number)
        conference.set_assignment('reviewer3@mail.com', submission.number)

        # Reviewer
        request_page(selenium, "http://localhost:3030/forum?id=" + submission.id, reviewer_client.token, by=By.CLASS_NAME, wait_for_element='reply_row')

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 1
        assert 'Official Review' == reply_row.find_elements_by_class_name('btn')[0].text

        # Author
        request_page(selenium, "http://localhost:3030/forum?id=" + submission.id, test_client.token, by=By.CLASS_NAME, wait_for_element='reply_row')

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 1
        assert 'Withdraw' == reply_row.find_elements_by_class_name('btn')[0].text

        note = openreview.Note(invitation = 'NIPS.cc/2018/Workshop/MLITS/Paper1/-/Official_Review',
            forum = submission.id,
            replyto = submission.id,
            readers = ['NIPS.cc/2018/Workshop/MLITS/Program_Chairs', 'NIPS.cc/2018/Workshop/MLITS/Paper1/Area_Chairs', 'NIPS.cc/2018/Workshop/MLITS/Paper1/Reviewers/Submitted'],
            nonreaders = ['NIPS.cc/2018/Workshop/MLITS/Paper1/Authors'],
            writers = ['NIPS.cc/2018/Workshop/MLITS/Paper1/AnonReviewer1'],
            signatures = ['NIPS.cc/2018/Workshop/MLITS/Paper1/AnonReviewer1'],
            content = {
                'title': 'Review title',
                'review': 'Paper is very good!',
                'rating': '5',
                'confidence': '4: The reviewer is confident but not absolutely certain that the evaluation is correct'
            }
        )
        review_note = reviewer_client.post_note(note)
        assert review_note

        helpers.await_queue()

        process_logs = client.get_process_logs(id = review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[MLITS 2018] Review posted to your submission - Paper number: 1, Paper title: "New paper title"')
        assert len(messages) == 0

        messages = client.get_messages(subject = '[MLITS 2018] Review posted to your assigned Paper number: 1, Paper title: "New paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'ac2@mail.com' in recipients

        messages = client.get_messages(subject = '[MLITS 2018] Your review has been received on your assigned Paper number: 1, Paper title: "New paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer@mail.com' in recipients

        ## Check review visibility
        notes = reviewer_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/Paper1/-/Official_Review')
        assert len(notes) == 1

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/Paper1/-/Official_Review')
        assert len(notes) == 0

        reviewer2_client = helpers.create_user('reviewer3@mail.com', 'Reviewer', 'Three')
        notes = reviewer2_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/Paper1/-/Official_Review')
        assert len(notes) == 0

        note = openreview.Note(invitation = 'NIPS.cc/2018/Workshop/MLITS/Paper1/-/Official_Review',
            forum = submission.id,
            replyto = submission.id,
            readers = ['NIPS.cc/2018/Workshop/MLITS/Program_Chairs', 'NIPS.cc/2018/Workshop/MLITS/Paper1/Area_Chairs', 'NIPS.cc/2018/Workshop/MLITS/Paper1/Reviewers/Submitted'],
            nonreaders = ['NIPS.cc/2018/Workshop/MLITS/Paper1/Authors'],
            writers = ['NIPS.cc/2018/Workshop/MLITS/Paper1/AnonReviewer2'],
            signatures = ['NIPS.cc/2018/Workshop/MLITS/Paper1/AnonReviewer2'],
            content = {
                'title': 'Review title',
                'review': 'Paper is very good!',
                'rating': '2',
                'confidence': '4: The reviewer is confident but not absolutely certain that the evaluation is correct'
            }
        )
        review_note = reviewer2_client.post_note(note)
        assert review_note

        helpers.await_queue()

        notes = reviewer2_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/Paper1/-/Official_Review')
        assert len(notes) == 2

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/Paper1/-/Official_Review')
        assert len(notes) == 0

        messages = client.get_messages(subject = '[MLITS 2018] Review posted to your assigned Paper number: 1, Paper title: "New paper title"')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'ac2@mail.com' in recipients
        assert 'reviewer@mail.com' in recipients

    def test_consoles(self, client, test_client, selenium, request_page, helpers):

        now = datetime.datetime.utcnow()
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        builder.set_conference_short_name('MLITS 2018')
        builder.has_area_chairs(True)
        builder.use_legacy_anonids(True)
        builder.set_review_stage(openreview.ReviewStage(due_date = now + datetime.timedelta(minutes = 100), additional_fields = {
            'rating': {
                'order': 3,
                'value-dropdown': [
                    '5',
                    '4',
                    '3',
                    '2',
                    '1'
                ],
                'required': True
            }
        }, release_to_reviewers = openreview.ReviewStage.Readers.REVIEWERS_SUBMITTED))
        conference = builder.get_result()

        # Author user
        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS", test_client.token, wait_for_element='your-consoles')
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 1
        console = tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')[0]
        assert 'Author Console' == console.find_element_by_tag_name('a').text

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS/Authors", test_client.token, wait_for_element='your-submissions')
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-tasks')
        tasks = tabs.find_element_by_id('author-tasks').find_element_by_class_name('task-list')
        assert len(tasks.find_elements_by_class_name('empty-message')) == 1
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('console-table')
        assert len(papers.find_elements_by_tag_name('tr')) == 2

        conference.set_authorpage_header({
            'title': 'Author Console',
            'instructions': 'Set of instructions',
            'schedule': 'This is a schedule'
        })

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS/Authors", test_client.token, wait_for_element='your-submissions')

        header = selenium.find_element_by_id('header')
        assert header
        assert len(header.find_elements_by_tag_name('h1')) == 1
        assert 'Author Console' == header.find_elements_by_tag_name('h1')[0].text
        assert len(header.find_elements_by_class_name('description')) == 1
        assert 'Set of instructions' == header.find_elements_by_class_name('description')[0].text
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-tasks')
        tasks = tabs.find_element_by_id('author-tasks').find_element_by_class_name('task-list')
        assert len(tasks.find_elements_by_class_name('empty-message')) == 1
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('console-table')
        assert len(papers.find_elements_by_tag_name('tr')) == 2

        # Reviewer user
        reviewer_client = openreview.Client(baseurl = 'http://localhost:3000', username='reviewer@mail.com', password='1234')
        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS", reviewer_client.token, wait_for_element='your-submissions')
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 1
        console = tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')[0]
        assert 'Reviewer Console' == console.find_element_by_tag_name('a').text

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS/Reviewers", reviewer_client.token, wait_for_element='reviewer-tasks')
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('assigned-papers')
        assert len(tabs.find_element_by_id('assigned-papers').find_elements_by_class_name('note')) == 1
        assert tabs.find_element_by_id('reviewer-tasks')
        assert len(tabs.find_element_by_id('reviewer-tasks').find_elements_by_class_name('note')) == 1

        conference.set_reviewerpage_header({
            'title': 'Reviewer Console',
            'instructions': 'Set of instructions',
            'schedule': 'This is a schedule'
        })

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS/Reviewers", reviewer_client.token, wait_for_element='reviewer-tasks')

        header = selenium.find_element_by_id('header')
        assert header
        assert len(header.find_elements_by_tag_name('h1')) == 1
        assert 'Reviewer Console' == header.find_elements_by_tag_name('h1')[0].text
        assert len(header.find_elements_by_class_name('description')) == 1
        assert 'Set of instructions' == header.find_elements_by_class_name('description')[0].text
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('assigned-papers')
        assert len(tabs.find_element_by_id('assigned-papers').find_elements_by_class_name('note')) == 1
        assert tabs.find_element_by_id('reviewer-tasks')
        assert len(tabs.find_element_by_id('reviewer-tasks').find_elements_by_class_name('note')) == 1

        # Area chair user
        ac_client = helpers.create_user('ac2@mail.com', 'AC', 'MLITS')
        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS", ac_client.token, wait_for_element='your-consoles')
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 1
        console = tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')[0]
        assert 'Area Chair Console' == console.find_element_by_tag_name('a').text

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS/Area_Chairs", ac_client.token, wait_for_element='areachair-tasks')
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('assigned-papers')
        assert len(tabs.find_element_by_id('assigned-papers').find_elements_by_class_name('note')) == 1
        assert tabs.find_element_by_id('areachair-tasks')
        assert len(tabs.find_element_by_id('areachair-tasks').find_elements_by_class_name('note')) == 0
        reviews = tabs.find_elements_by_class_name('reviewer-progress')
        assert reviews
        assert len(reviews) == 1
        headers = reviews[0].find_elements_by_tag_name('h4')
        assert headers
        assert headers[0].text == '2 of 2 Reviews Submitted'

        #Program chair user
        pc_client = helpers.create_user('pc2@mail.com', 'ProgramChair', 'SomeLastName')

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS", pc_client.token, wait_for_element='your-consoles')
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 1
        console = tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')[0]
        assert 'Program Chair Console' == console.find_element_by_tag_name('a').text

        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2018/Workshop/MLITS/Program_Chairs", pc_client.token, by=By.CLASS_NAME, wait_for_element='reviewer-status')
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('paper-status')
        assert tabs.find_element_by_id('areachair-status')
        assert tabs.find_element_by_id('reviewer-status')

    def test_post_decisions(self, client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        builder.has_area_chairs(True)
        builder.set_conference_year(2018)
        builder.set_conference_name('NIPS Workshop MLITS')
        conference = builder.get_result()
        decision_additional_fields = {
            "comment test": {
                'order': 4,
                'value-regex': '.*'
            }
        }
        conference.set_decision_stage(openreview.DecisionStage(public=True, additional_fields=decision_additional_fields))

        submissions = conference.get_submissions(sort='tmdate')
        assert len(submissions) == 1
        note = openreview.Note(invitation = 'NIPS.cc/2018/Workshop/MLITS/Paper1/-/Decision',
            forum = submissions[0].id,
            replyto = submissions[0].id,
            readers = ['everyone'],
            writers = ['NIPS.cc/2018/Workshop/MLITS/Program_Chairs'],
            signatures = ['NIPS.cc/2018/Workshop/MLITS/Program_Chairs'],
            content = {
                'title': 'Paper Decision',
                'decision': 'Accept (Oral)',
                'comment test': 'Accepted',
            }
        )
        note = client.post_note(note)

        conference.post_decision_stage(submission_readers=[openreview.SubmissionStage.Readers.EVERYONE_BUT_REJECTED])

        submissions = conference.get_submissions(sort='tmdate')
        assert len(submissions) == 1

        valid_bibtex = '''@inproceedings{
user2018new,
title={New paper title},
author={SomeFirstName User and Peter SomeLastName and Andrew Mc},
booktitle={NIPS Workshop MLITS},
year={2018},
url={https://openreview.net/forum?id='''

        valid_bibtex = valid_bibtex + submissions[0].forum + '''}
}'''

        assert submissions[0].content['_bibtex'] == valid_bibtex

    def test_enable_camera_ready_revisions(self, client, test_client, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        builder.has_area_chairs(True)
        builder.set_conference_year(2018)
        builder.set_conference_name('NIPS Workshop MLITS')
        conference = builder.get_result()

        conference.set_submission_revision_stage(openreview.SubmissionRevisionStage(name='Camera_Ready_Revision', only_accepted=True))

        notes = conference.get_submissions(sort='tmdate')
        assert notes
        assert len(notes) == 1
        note = notes[0]

        note = openreview.Note(invitation = 'NIPS.cc/2018/Workshop/MLITS/Paper1/-/Camera_Ready_Revision',
            forum = notes[0].id,
            referent = notes[0].id,
            readers = ['NIPS.cc/2018/Workshop/MLITS', 'NIPS.cc/2018/Workshop/MLITS/Paper1/Authors'],
            writers = [conference.id, 'NIPS.cc/2018/Workshop/MLITS/Paper1/Authors'],
            signatures = ['NIPS.cc/2018/Workshop/MLITS/Paper1/Authors'],
            content = {
                'title': 'New paper title Version 2',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com', 'melisa@mail.com'],
                'authors': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc', 'Melisa Bok'],
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        )

        posted_note = test_client.post_note(note)
        assert posted_note

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        notes = conference.get_submissions(sort='tmdate')
        assert notes
        assert len(notes) == 1
        note = notes[0]

        valid_bibtex = '''@inproceedings{
user2018new,
title={New paper title Version 2},
author={SomeFirstName User and Peter SomeLastName and Andrew Mc and Melisa Bok},
booktitle={NIPS Workshop MLITS},
year={2018},
url={https://openreview.net/forum?id='''

        valid_bibtex = valid_bibtex + notes[0].forum + '''}
}'''

        assert notes[0].content['_bibtex'] == valid_bibtex
        assert ['everyone'] == notes[0].readers
