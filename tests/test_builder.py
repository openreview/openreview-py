from __future__ import absolute_import, division, print_function, unicode_literals
import os
import datetime
import json
import time
import openreview
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

class TestBuilder():

    def test_override_homepage(self, client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
        assert builder, 'builder is None'

        builder.set_conference_id('test.org/2019/Conference')
        conference = builder.get_result()
        assert conference, 'conference is None'

        groups = conference.get_conference_groups()
        assert groups
        assert len(groups) == 3
        home_group = groups[-1]
        assert home_group.id == 'test.org/2019/Conference'

        request_page(selenium, 'http://localhost:3030/group?id=test.org/2019/Conference')
        assert selenium.find_element_by_tag_name('h3').text == 'test.org/2019/Conference'

        builder.set_homepage_header({ 'subtitle': 'TEST 2019' })
        conference = builder.get_result()

        request_page(selenium, 'http://localhost:3030/group?id=test.org/2019/Conference')
        assert selenium.find_element_by_tag_name('h3').text == 'TEST 2019'


    def test_web_set_landing_page(self, client):
        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
        builder.set_conference_id("ds.cs.umass.edu/Test_I/2019/Conference")
        conference = builder.get_result()
        group = client.get_group(id='ds.cs.umass.edu/Test_I/2019')
        assert group.web,'Venue parent group missing webfield'

        # check webfield contains 'Conference'
        assert 'ds.cs.umass.edu/Test_I/2019/Conference' in group.web, 'Venue parent group missing child group'

        # add 'Party'
        child_str = ''', {'url': '/group?id=Party', 'name': 'Party'}'''
        start_pos = group.web.find('VENUE_LINKS')
        insert_pos = group.web.find('];', start_pos)
        group.web = group.web[:insert_pos] + child_str + group.web[insert_pos:]
        client.post_group(group)

        builder.set_conference_id("ds.cs.umass.edu/Test_I/2019/Workshop/WS_1")
        conference = builder.get_result()
        # check webfield contains 'Conference', 'Party' and 'Workshop'
        group = client.get_group(id='ds.cs.umass.edu/Test_I/2019')
        assert 'ds.cs.umass.edu/Test_I/2019/Conference' in group.web, 'Venue parent group missing child conference group'
        assert 'ds.cs.umass.edu/Test_I/2019/Workshop' in group.web, 'Venue parent group missing child workshop group'
        assert 'Party' in group.web, 'Venue parent group missing child inserted group'

    def test_modify_review_form(self, client, test_client, selenium, request_page, helpers):

        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
        assert builder, 'builder is None'

        builder.set_conference_id('test.org/2019/Conference')
        builder.set_conference_name('Test Conference 2019')
        builder.set_conference_short_name('TEST Conf 2019')
        builder.set_homepage_header({
        'title': 'Test Conference 2019',
        'subtitle': 'TEST Conf 2019',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'Sept 11-15, 2019',
        'website': 'https://testconf19.com',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = False, due_date = now + datetime.timedelta(minutes = 10))
        builder.has_area_chairs(False)
        builder.use_legacy_anonids(True)
        conference = builder.get_result()

        conference.set_program_chairs()
        conference.set_reviewers(emails = ['reviewer_test1@mail.com'])

        author_client = helpers.create_user('author_test1@mail.com', 'SomeFirstName', 'Author')
        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~SomeFirstName_Author1', 'drew@mail.com', 'test.org/2019/Conference'],
            writers = [conference.id, '~SomeFirstName_Author1', 'drew@mail.com'],
            signatures = ['~SomeFirstName_Author1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['author_test1@mail.com', 'drew@mail.com'],
                'authors': ['SomeFirstName Author', 'Drew Barrymore']
            }
        )
        url = author_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note.content['pdf'] = url
        author_client.post_note(note)

        original_notes = client.get_notes(invitation = conference.get_submission_id())
        assert original_notes
        assert len(original_notes) == 1

        conference.setup_post_submission_stage(force=True)
        blind_submissions = conference.get_submissions()
        assert blind_submissions
        assert len(blind_submissions) == 1

        conference.set_review_stage(conference.review_stage)

        reviewer_client = helpers.create_user('reviewer_test1@mail.com', 'SomeFirstName', 'ReviewerOne')

        conference.set_assignment('reviewer_test1@mail.com', blind_submissions[0].number)

        request_page(selenium=selenium, url="http://localhost:3030/forum?id=" + blind_submissions[0].id, token=reviewer_client.token, wait_for_element='note_{}'.format(blind_submissions[0].id))
        reply_row = selenium.find_element_by_class_name('reply_row')
        assert len(reply_row.find_elements_by_class_name('btn')) == 1
        assert 'Official Review' == reply_row.find_elements_by_class_name('btn')[0].text

        official_review_invitations = reviewer_client.get_invitations(regex = conference.get_invitation_id('Official_Review', blind_submissions[0].number))
        assert len(official_review_invitations) == 1
        assert official_review_invitations[0].id == conference.get_id() + '/Paper' + str(blind_submissions[0].number) + '/-/Official_Review'
        assert 'confidence' in official_review_invitations[0].reply['content'].keys()

        conference.review_stage.additional_fields = {
            'additional description': {
                'description': 'Provide additional description of your review here',
                'required': True,
                'value-regex': '.*'
            }
        }
        conference.review_stage.release_to_reviewers = openreview.ReviewStage.Readers.REVIEWERS_SUBMITTED
        conference.set_review_stage(conference.review_stage)
        official_review_invitations = reviewer_client.get_invitations(regex = conference.get_invitation_id('Official_Review', blind_submissions[0].number))
        assert len(official_review_invitations) == 1
        assert official_review_invitations[0].id == conference.get_id() + '/Paper' + str(blind_submissions[0].number) + '/-/Official_Review'
        assert 'additional description' in official_review_invitations[0].reply['content'].keys()

        conference.review_stage.remove_fields = ['confidence', 'additional description']
        conference.set_review_stage(conference.review_stage)
        official_review_invitations = reviewer_client.get_invitations(regex = conference.get_invitation_id('Official_Review', blind_submissions[0].number))
        assert len(official_review_invitations) == 1
        assert official_review_invitations[0].id == conference.get_id() + '/Paper' + str(blind_submissions[0].number) + '/-/Official_Review'
        assert 'confidence' not in official_review_invitations[0].reply['content'].keys()
        assert 'additional description' not in official_review_invitations[0].reply['content'].keys()

        note = openreview.Note(invitation = conference.get_invitation_id('Official_Review', blind_submissions[0].number),
            forum = blind_submissions[0].id,
            replyto = blind_submissions[0].id,
            readers = [
                conference.get_program_chairs_id(),
                conference.get_reviewers_id(blind_submissions[0].number) + '/Submitted'],
            nonreaders = [conference.get_authors_id(blind_submissions[0].number)],
            writers = [conference.get_id() + '/Paper1/AnonReviewer1'],
            signatures = [conference.get_id() + '/Paper1/AnonReviewer1'],
            content = {
                'title': 'Review title',
                'review': 'Paper is very good!',
                'rating': '9: Top 15% of accepted papers, strong accept'
            }
        )
        review_note = reviewer_client.post_note(note)
        assert review_note

    def test_PC_console_sort_by_options(self, client, test_client, selenium, request_page, helpers):

        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
        assert builder, 'builder is None'

        builder.set_conference_id('sortTest.org/2019/Conference')
        builder.set_conference_name('Sort Test Conference 2019')
        builder.set_conference_short_name('Sort TEST Conf 2019')
        builder.set_homepage_header({
        'title': 'Sort Test Conference 2019',
        'subtitle': 'Sort TEST Conf 2019',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'Sept 11-15, 2019',
        'website': 'https://testconf19.com',
        'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind = True, public = False, due_date = now + datetime.timedelta(minutes = 10))
        builder.has_area_chairs(False)
        conference = builder.get_result()
        conference.set_program_chairs(emails=['pc_testconsole1@mail.com'])

        author_client = openreview.Client(username='author_test1@mail.com', password='1234')

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~SomeFirstName_Author1', 'drew@mail.com', 'sortTest.org/2019/Conference'],
            writers = [conference.id, '~SomeFirstName_Author1', 'drew@mail.com'],
            signatures = ['~SomeFirstName_Author1'],
            content = {
                'title': 'Paper title Sort Conference',
                'abstract': 'This is an abstract',
                'authorids': ['author_test1@mail.com', 'drew@mail.com'],
                'authors': ['SomeFirstName Author', 'Drew Barrymore']
            }
        )
        url = author_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note.content['pdf'] = url
        author_client.post_note(note)

        builder.set_submission_stage(double_blind = True, public = False, due_date = now)
        conference = builder.get_result()

        conference.create_blind_submissions()

        pc_client = helpers.create_user('pc_testconsole1@mail.com', 'SomeFirstName', 'PCConsole')
        request_page(selenium, 'http://localhost:3030/group?id=' + conference.get_program_chairs_id() + '#paper-status', pc_client.token, wait_for_element='venue-configuration')

        assert selenium.find_element_by_xpath('//a[@href="#paper-status"]')
        assert selenium.find_element_by_xpath('//div[@id="venue-configuration"]//h3')

        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'message-papers-btn'))
        )

        expected_options = ['Paper Number', 'Paper Title', 'Average Rating', 'Max Rating', 'Min Rating', 'Average Confidence', 'Max Confidence', 'Min Confidence', 'Reviewers Assigned', 'Reviews Submitted', 'Reviews Missing', 'Decision']
        unexpected_options = ['Meta Review Missing']
        for option in expected_options:
            assert selenium.find_element_by_class_name('-'.join(option.split(' ')) + '-paper-status')

        with pytest.raises(NoSuchElementException):
            for option in unexpected_options:
                assert selenium.find_element_by_class_name('-'.join(option.split(' ')) + '-paper-status')

        builder.has_area_chairs(True)
        conference = builder.get_result()

        request_page(selenium, 'http://localhost:3030/group?id=' + conference.get_program_chairs_id() + '#paper-status', pc_client.token, wait_for_element='paper-status')

        expected_options.append('Meta Review Missing')
        for option in expected_options:
            assert selenium.find_element_by_class_name('-'.join(option.split(' ')) + '-paper-status')
