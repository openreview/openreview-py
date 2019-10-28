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

class TestWorkshop():

    def test_create_conference(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        conference = builder.get_result()
        assert conference, 'conference is None'

        resp = requests.get('http://localhost:3000/groups?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        assert resp.status_code == 200

    def test_enable_submissions(self, client, selenium, request_page):


        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = True, due_date = now + datetime.timedelta(minutes = 10))
        conference = builder.get_result()
        conference.set_program_chairs(emails = ['program_chairs@hsdip.org'])

        invitation = client.get_invitation(id = conference.get_submission_id())
        assert invitation
        assert invitation.duedate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 10))
        assert invitation.expdate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 40))

        posted_invitation = client.get_invitation(id = 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Submission')
        assert posted_invitation
        assert posted_invitation.duedate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 10))
        assert posted_invitation.expdate == openreview.tools.datetime_millis(now + datetime.timedelta(minutes = 40))

        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP")

        assert "ICAPS 2019 Workshop HSDIP | OpenReview" in selenium.title
        header = selenium.find_element_by_id('header')
        assert header
        assert "Heuristics and Search for Domain-independent Planning" == header.find_element_by_tag_name("h1").text
        assert "ICAPS 2019 Workshop" == header.find_element_by_tag_name("h3").text
        assert "Berkeley, CA, USA" == header.find_element_by_xpath(".//span[@class='venue-location']").text
        assert "July 11-15, 2019" == header.find_element_by_xpath(".//span[@class='venue-date']").text
        assert "https://icaps19.icaps-conference.org/workshops/HSDIP/index" in header.find_element_by_xpath(".//span[@class='venue-website']/a").text
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'ICAPS 2019 Workshop HSDIP Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 0
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_tag_name('ul')) == 0

    def test_post_submissions(self, client, test_client, peter_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = True, due_date = now + datetime.timedelta(minutes = 10))
        conference = builder.get_result()

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com', 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Peter User', 'Andrew Mc']
            }
        )
        url = test_client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note.content['pdf'] = url
        test_client.post_note(note)

        # Author user
        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP", test_client.token)
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'ICAPS 2019 Workshop HSDIP Submission' == invitation_panel.find_element_by_class_name('btn').text
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

        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Authors", test_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-schedule')
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('submissions-list')
        assert len(papers.find_elements_by_class_name('note')) == 1

        # Guest user
        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP")
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'ICAPS 2019 Workshop HSDIP Submission' == invitation_panel.find_element_by_class_name('btn').text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('your-consoles')
        assert len(tabs.find_element_by_id('your-consoles').find_elements_by_tag_name('ul')) == 0
        assert tabs.find_element_by_id('recent-activity')
        assert len(tabs.find_element_by_id('recent-activity').find_elements_by_class_name('activity-list')) == 0

        # Co-author user
        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP", peter_client.token)
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'ICAPS 2019 Workshop HSDIP Submission' == invitation_panel.find_element_by_class_name('btn').text
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

        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Authors", peter_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-schedule')
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('submissions-list')
        assert len(papers.find_elements_by_class_name('note')) == 1

    def test_create_blind_submissions(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = False, due_date = now + datetime.timedelta(minutes = 10))

        builder.has_area_chairs(False)
        conference = builder.get_result()

        group = client.get_group(id = conference.get_authors_id())
        assert group
        assert len(group.members) == 0

        groups = client.get_groups(id = conference.get_authors_id(number = '.*'))
        assert len(groups) == 0

        builder.set_submission_stage(double_blind = True, public = False, due_date = now)
        conference = builder.get_result()

        blind_submissions = conference.create_blind_submissions()
        assert blind_submissions
        assert len(blind_submissions) == 1

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com', 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Peter User', 'Andrew Mc']
            }
        )
        url = client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note.content['pdf'] = url
        client.post_note(note)

        blind_submissions_2 = conference.create_blind_submissions()
        assert blind_submissions_2
        assert len(blind_submissions_2) == 2
        assert blind_submissions[0].id == blind_submissions_2[0].id
        assert blind_submissions_2[1].readers == [
            'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper2/Authors',
            'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Reviewers',
            'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'
        ]

        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = True, due_date = now + datetime.timedelta(minutes = 10))
        conference = builder.get_result()

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com', 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Peter User', 'Andrew Mc']
            }
        )
        url = client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note.content['pdf'] = url
        client.post_note(note)

        builder.set_submission_stage(double_blind = True, public = True, due_date = now)
        conference = builder.get_result()

        blind_submissions_3 = conference.create_blind_submissions()
        assert blind_submissions_3
        assert len(blind_submissions_3) == 3
        assert blind_submissions[0].id == blind_submissions_3[0].id
        assert blind_submissions_3[2].readers == ['everyone']

    def test_setup_matching(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = False, due_date = now + datetime.timedelta(minutes = 10))

        builder.has_area_chairs(False)
        conference = builder.get_result()

        conference.setup_matching()

        invitation = client.get_invitation('icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Reviewers/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert not invitation.reply['content']['scores_specification']['default']

    def test_set_authors(self, client, test_client, selenium, request_page, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = False, due_date = now + datetime.timedelta(minutes = 10))
        builder.set_review_stage(due_date = now + datetime.timedelta(minutes = 10), release_to_authors= True, release_to_reviewers=True)
        builder.has_area_chairs(False)
        conference = builder.get_result()

        group = client.get_group(id = conference.get_authors_id())
        assert group
        assert len(group.members) == 3

        groups = client.get_groups(id = conference.get_authors_id(number = '.*'))
        assert len(groups) == 3

        for group in groups:
            assert group.members

        conference.set_authors()

        group = client.get_group(id = conference.get_authors_id())
        assert group
        assert len(group.members) == 3

        conference = builder.get_result()

        group = client.get_group(id = conference.get_authors_id())
        assert group
        assert len(group.members) == 3

    def test_open_reviews(self, client, test_client, selenium, request_page, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = False, due_date = now + datetime.timedelta(minutes = 10))
        builder.set_review_stage(due_date = now + datetime.timedelta(minutes = 10), release_to_authors= True, release_to_reviewers=True)
        builder.has_area_chairs(False)
        conference = builder.get_result()
        conference.set_authors()
        conference.set_reviewers(emails = ['reviewer4@mail.com'])

        notes = test_client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Blind_Submission')
        submission = notes[2]

        # Reviewer
        reviewer_client = helpers.create_user('reviewer4@mail.com', 'Reviewer', 'Four')

        conference.set_assignment('reviewer4@mail.com', submission.number)

        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, reviewer_client.token)
        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 1
        assert 'Official Review' == reply_row.find_elements_by_class_name('btn')[0].text

        # Author
        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 0

        note = openreview.Note(invitation = 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/-/Official_Review',
            forum = submission.id,
            replyto = submission.id,
            readers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs',
            'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/Reviewers',
            'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/Authors'],
            writers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/AnonReviewer1'],
            signatures = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/AnonReviewer1'],
            content = {
                'title': 'Review title',
                'review': 'Paper is very good!',
                'rating': '9: Top 15% of accepted papers, strong accept',
                'confidence': '4: The reviewer is confident but not absolutely certain that the evaluation is correct'
            }
        )
        review_note = reviewer_client.post_note(note)
        assert review_note

        process_logs = client.get_process_logs(id = review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[ICAPS HSDIP 2019] Review posted to your submission: "New paper title"')
        assert len(messages) == 0

        messages = client.get_messages(subject = '[ICAPS HSDIP 2019] Review posted to your assigned paper: "New paper title"')
        assert len(messages) == 0

        ## Check review visibility
        notes = reviewer_client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/-/Official_Review')
        assert len(notes) == 1

        notes = test_client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/-/Official_Review')
        assert len(notes) == 1

    def test_open_comments(self, client, test_client, selenium, request_page, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = False, due_date = now + datetime.timedelta(minutes = 10))

        builder.has_area_chairs(False)
        builder.set_comment_stage(unsubmitted_reviewers = True, email_pcs = True, reader_selection=True, allow_public_comments = True)
        conference = builder.get_result()
        assert conference

        notes = test_client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Blind_Submission')
        submission = notes[2]

        reviews = client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/-/Official_Review')
        assert reviews
        review = reviews[0]

        note = openreview.Note(invitation = 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/-/Official_Comment',
            forum = submission.id,
            replyto = review.id,
            readers = [
                'everyone',
                'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/Authors',
                'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/Reviewers',
                'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            writers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/AnonReviewer1'],
            signatures = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/AnonReviewer1'],
            content = {
                'title': 'Comment title',
                'comment': 'Paper is very good!'
            }
        )
        reviewer_client = openreview.Client(username='reviewer4@mail.com', password='1234')
        review_note = reviewer_client.post_note(note)
        assert review_note

        process_logs = client.get_process_logs(id = review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '.*ICAPS HSDIP 2019.*Your submission has received a comment. Paper Number: 1, Paper Title')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        assert 'andrew@mail.com' in recipients

        messages = client.get_messages(subject = '.*ICAPS HSDIP 2019.*Comment posted to a paper you are reviewing. Paper Number: 1, Paper Number')
        assert len(messages) == 0

        messages = client.get_messages(subject = '.*ICAPS HSDIP 2019.*Comment posted to a paper in your area. Paper Number: 1, Paper Number')
        assert len(messages) == 0

        messages = client.get_messages(subject = '.*ICAPS HSDIP 2019.*A comment was posted. Paper Number')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'program_chairs@hsdip.org' in recipients

        note = openreview.Note(invitation = 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/-/Public_Comment',
            forum = submission.id,
            replyto = review.id,
            readers = ['everyone'],
            writers = ['~Reviewer_Four1'],
            signatures = ['~Reviewer_Four1'],
            content = {
                'title': 'Comment title',
                'comment': 'Paper is very good!'
            }
        )
        reviewer_client = openreview.Client(username='reviewer4@mail.com', password='1234')
        review_note = reviewer_client.post_note(note)
        assert review_note

        process_logs = client.get_process_logs(id = review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

    def test_open_revise_reviews(self, client, test_client, selenium, request_page, helpers):

        now = datetime.datetime.utcnow()
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = False, due_date = now + datetime.timedelta(minutes = 10))

        builder.has_area_chairs(False)
        conference = builder.get_result()
        assert conference

        notes = test_client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Blind_Submission')
        submission = notes[2]

        reviews = client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/-/Official_Review')
        assert reviews
        review = reviews[0]

        conference.open_revise_reviews(due_date = now + datetime.timedelta(minutes = 10))

        note = openreview.Note(invitation = 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/-/Official_Review/AnonReviewer1/Revision',
            forum = submission.id,
            referent = review.id,
            readers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs',
            'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/Reviewers',
            'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/Authors'],
            writers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/AnonReviewer1'],
            signatures = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/AnonReviewer1'],
            content = {
                'title': 'UPDATED Review title',
                'review': 'Paper is very good!',
                'rating': '9: Top 15% of accepted papers, strong accept',
                'confidence': '4: The reviewer is confident but not absolutely certain that the evaluation is correct'
            }
        )
        reviewer_client = openreview.Client(username='reviewer4@mail.com', password='1234')
        review_note = reviewer_client.post_note(note)
        assert review_note

        process_logs = client.get_process_logs(id = review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '.*ICAPS HSDIP 2019.*Revised review posted to your submission')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        assert 'andrew@mail.com' in recipients

        messages = client.get_messages(subject = '.*ICAPS HSDIP 2019.*Revised review posted to your assigned paper')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer4@mail.com' in recipients

    def test_open_meta_reviews(self, client, test_client, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = False, due_date = now + datetime.timedelta(minutes = 10))

        builder.has_area_chairs(False)
        conference = builder.get_result()
        conference.open_meta_reviews()

        notes = test_client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Blind_Submission')
        submission = notes[2]

        note = openreview.Note(invitation = 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/-/Meta_Review',
            forum = submission.id,
            replyto = submission.id,
            readers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            writers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            signatures = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            content = {
                'title': 'Meta review title',
                'metareview': 'Paper is very good!',
                'recommendation': 'Accept (Oral)',
                'confidence': '4: The area chair is confident but not absolutely certain'
            }
        )
        pc_client = helpers.create_user('program_chairs@hsdip.org', 'Program', 'HSDIPChair')
        meta_review_note = pc_client.post_note(note)
        assert meta_review_note

    def test_open_decisions(self, client, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = False, due_date = now + datetime.timedelta(minutes = 10))

        builder.has_area_chairs(False)
        conference = builder.get_result()

        conference.open_decisions()

        pc_client = openreview.Client(username = 'program_chairs@hsdip.org', password = '1234')

        notes = pc_client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Blind_Submission')
        submission = notes[2]

        note = openreview.Note(invitation = 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/-/Decision',
            forum = submission.id,
            replyto = submission.id,
            readers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            nonreaders = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper1/Authors'],
            writers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            signatures = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            content = {
                'title': 'Paper Decision',
                'decision': 'Accept (Oral)',
                'comment': 'this is a comment'
            }
        )
        decision_note = pc_client.post_note(note)
        assert decision_note

        notes = conference.get_submissions(accepted=True)
        assert notes

    def test_release_decisions(self, client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = False, due_date = now + datetime.timedelta(minutes = 10))

        builder.has_area_chairs(False)
        conference = builder.get_result()

        conference.set_homepage_decisions(decision_heading_map = {
            'Accept (Oral)': 'Oral Presentations',
            'Accept (Poster)': 'Post Presentations',
            'Reject': 'All Presentations'
        })

        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP#accept-oral", client.token)
        assert "ICAPS 2019 Workshop HSDIP | OpenReview" in selenium.title
        header = selenium.find_element_by_id('header')
        assert header
        assert "Heuristics and Search for Domain-independent Planning" == header.find_element_by_tag_name("h1").text
        assert "ICAPS 2019 Workshop" == header.find_element_by_tag_name("h3").text
        assert "Berkeley, CA, USA" == header.find_element_by_xpath(".//span[@class='venue-location']").text
        assert "July 11-15, 2019" == header.find_element_by_xpath(".//span[@class='venue-date']").text
        assert "https://icaps19.icaps-conference.org/workshops/HSDIP/index" in header.find_element_by_xpath(".//span[@class='venue-website']/a").text
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        accepted_panel = selenium.find_element_by_id('accept-oral')
        assert accepted_panel
        accepted_notes = accepted_panel.find_elements_by_class_name('note')
        assert accepted_notes
        assert len(accepted_notes) == 1

        pc_client = openreview.Client(username='program_chairs@hsdip.org', password='1234')
        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP", pc_client.token)
        consoles_tab = selenium.find_element_by_id('your-consoles')
        assert consoles_tab

    def test_pc_console(self, client, selenium, request_page):

        pc_client = openreview.Client(username = 'program_chairs@hsdip.org', password = '1234')

        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs#paper-status", pc_client.token)
        assert "ICAPS 2019 Workshop HSDIP Program Chairs | OpenReview" in selenium.title
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('paper-status')
        assert tabs.find_element_by_id('reviewer-status')
        with pytest.raises(NoSuchElementException):
            assert tabs.find_element_by_id('areachair-status')

        assert '#' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-1').text
        assert 'Paper Summary' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-2').text
        assert 'Review Progress' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-3').text
        assert 'Decision' == tabs.find_element_by_id('paper-status').find_element_by_class_name('row-4').text

        with pytest.raises(NoSuchElementException):
            assert tabs.find_element_by_id('paper-status').find_element_by_class_name('row-5')

    def test_accepted_papers(self, client, test_client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/HSDIP')
        builder.set_conference_name('Heuristics and Search for Domain-independent Planning')
        builder.set_conference_short_name('ICAPS HSDIP 2019')
        builder.set_homepage_header({
        'title': 'Heuristics and Search for Domain-independent Planning',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/HSDIP/index.html',
        'location': 'Berkeley, CA, USA'
        })
        builder.has_area_chairs(False)
        builder.set_submission_stage(double_blind=True)
        conference = builder.get_result()

        accepted_notes = conference.get_submissions(accepted=True)
        assert accepted_notes
        assert len(accepted_notes) == 1

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com', 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            writers = [conference.id, '~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Peter User', 'Andrew Mc']
            }
        )
        url = test_client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note.content['pdf'] = url
        posted_note = test_client.post_note(note)
        assert posted_note

        conference.create_blind_submissions()
        conference.set_authors()
        conference.open_decisions()

        pc_client = openreview.Client(username = 'program_chairs@hsdip.org', password = '1234')

        notes = pc_client.get_notes(invitation='icaps-conference.org/ICAPS/2019/Workshop/HSDIP/-/Blind_Submission')
        submission = notes[2]

        note = openreview.Note(invitation = 'icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper2/-/Decision',
            forum = submission.id,
            replyto = submission.id,
            readers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            nonreaders = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Paper2/Authors'],
            writers = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            signatures = ['icaps-conference.org/ICAPS/2019/Workshop/HSDIP/Program_Chairs'],
            content = {
                'title': 'Paper Decision',
                'decision': 'Reject',
                'comment': 'this is a comment'
            }
        )
        decision_note = pc_client.post_note(note)
        assert decision_note

        notes = conference.get_submissions(accepted=True)
        assert notes
        assert len(notes) == 1

        notes = conference.get_submissions(accepted=False)
        assert notes
        assert len(notes) == 4
