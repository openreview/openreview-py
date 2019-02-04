from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
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
        assert groups[3].signatures == ['~Super_User1']
        assert groups[3].signatories == ['NIPS.cc/2018/Workshop/MLITS']
        assert groups[3].members == []
        assert '"title": "2018 NIPS MLITS Workshop"' in groups[3].web
        assert '"subtitle": "Machine Learning for Intelligent Transportation Systems"' in groups[3].web
        assert '"location": "Montreal, Canada"' in groups[3].web
        assert '"date": "December 3-8, 2018"' in groups[3].web
        assert '"website": "https://sites.google.com/site/nips2018mlits/home"' in groups[3].web
        assert '"deadline": "October 12, 2018, 11:59 pm UTC"' in groups[3].web

        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS")

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
        conference = builder.get_result()
        assert conference, 'conference is None'

        invitation = conference.open_submissions(due_date = datetime.datetime(2019, 10, 5, 18, 00), public = True)
        assert invitation
        assert invitation.duedate == 1570298400000

        posted_invitation = client.get_invitation(id = 'NIPS.cc/2018/Workshop/MLITS/-/Submission')
        assert posted_invitation
        assert posted_invitation.duedate == 1570298400000

        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS")

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

    def test_post_submissions(self, client, test_client, peter_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        conference = builder.get_result()
        invitation = conference.open_submissions(due_date = datetime.datetime(2019, 10, 5, 18, 00), public = True)

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
            readers = ['everyone'],
            writers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Peter Test', 'Andrew Mc']
            }
        )
        url = test_client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note.content['pdf'] = url
        test_client.post_note(note)

        # Author user
        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS", test_client.token)
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

        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS/Authors", test_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-schedule')
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('submissions-list')
        assert len(papers.find_elements_by_class_name('note')) == 1

        # Guest user
        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS")
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
        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS", peter_client.token)
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

        request_page(selenium, "http://localhost:3000/group?id=NIPS.cc/2018/Workshop/MLITS/Authors", peter_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-schedule')
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('submissions-list')
        assert len(papers.find_elements_by_class_name('note')) == 1

    def test_close_submission(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        conference = builder.get_result()

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/-/Submission')
        submission = notes[0]
        submission.content['title'] = 'New paper title'
        test_client.post_note(submission)

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/-/Submission')
        assert 'New paper title' == notes[0].content['title']
        assert '~Test_User1' in notes[0].writers
        assert 'peter@mail.com' in notes[0].writers
        assert 'andrew@mail.com' in notes[0].writers

        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        assert len(selenium.find_elements_by_class_name('edit_button')) == 1
        assert len(selenium.find_elements_by_class_name('trash_button')) == 1

        conference.close_submissions()
        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/-/Submission')
        submission = notes[0]
        assert ['NIPS.cc/2018/Workshop/MLITS'] == submission.writers

        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        assert len(selenium.find_elements_by_class_name('edit_button')) == 0
        assert len(selenium.find_elements_by_class_name('trash_button')) == 0

    def test_open_comments(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        conference = builder.get_result()

        conference.open_comments('Public_Comment', public = True, anonymous = True)

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/-/Submission')
        submission = notes[0]
        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 1
        assert 'Public Comment' == reply_row.find_elements_by_class_name('btn')[0].text

    def test_close_comments(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        conference = builder.get_result()

        conference.close_comments('Public_Comment')

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/-/Submission')
        submission = notes[0]
        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 0

    def test_open_reviews(self, client, test_client, selenium, request_page):

        reviewer_client = openreview.Client(baseurl = 'http://localhost:3000')
        assert reviewer_client is not None, "Client is none"
        res = reviewer_client.register_user(email = 'reviewer@mail.com', first = 'Reviewer', last = 'Test', password = '1234')
        assert res, "Res i none"
        res = reviewer_client.activate_user('reviewer@mail.com', {
            'names': [
                    {
                        'first': 'Reviewer',
                        'last': 'Test',
                        'username': '~Reviewer_Test1'
                    }
                ],
            'emails': ['reviewer@mail.com'],
            'preferredEmail': 'reviewer@mail.com'
            })
        assert res, "Res i none"
        group = reviewer_client.get_group(id = 'reviewer@mail.com')
        assert group
        assert group.members == ['~Reviewer_Test1']

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        notes = test_client.get_notes(invitation='NIPS.cc/2018/Workshop/MLITS/-/Submission')
        submission = notes[0]

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        builder.set_conference_short_name('MLITS 2018')
        conference = builder.get_result()
        conference.set_authors()
        conference.set_program_chairs(emails = ['pc@mail.com'])
        conference.set_area_chairs(emails = ['ac@mail.com'])
        conference.set_reviewers(emails = ['reviewer@mail.com'])

        conference.set_assignment('ac@mail.com', submission.number, is_area_chair = True)
        conference.set_assignment('reviewer@mail.com', submission.number)
        conference.open_reviews('Official_Review', public = True)

        # Reviewer
        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, reviewer_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 1
        assert 'Official Review' == reply_row.find_elements_by_class_name('btn')[0].text

        # Author
        request_page(selenium, "http://localhost:3000/forum?id=" + submission.id, test_client.token)

        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 0

        note = openreview.Note(invitation = 'NIPS.cc/2018/Workshop/MLITS/-/Paper1/Official_Review',
            forum = submission.id,
            replyto = submission.id,
            readers = ['everyone'],
            writers = ['NIPS.cc/2018/Workshop/MLITS/Paper1/AnonReviewer1'],
            signatures = ['NIPS.cc/2018/Workshop/MLITS/Paper1/AnonReviewer1'],
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

        messages = client.get_messages(subject = '[MLITS 2018] Review posted to your submission: "New paper title"')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'test@mail.com' in recipients
        assert 'peter@mail.com' in recipients
        assert 'andrew@mail.com' in recipients

        messages = client.get_messages(subject = '[MLITS 2018] Review posted to your assigned paper: "New paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'ac@mail.com' in recipients

