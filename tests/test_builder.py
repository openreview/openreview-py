from __future__ import absolute_import, division, print_function, unicode_literals
import os
import datetime
import json
import openreview
import pytest

class TestBuilder():

    def test_override_homepage(self, client):

        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('test.org/2019/Conference')
        conference = builder.get_result()
        assert conference, 'conference is None'

        groups = conference.get_conference_groups()
        assert groups
        assert len(groups) == 3
        home_group = groups[-1]
        assert home_group.id == 'test.org/2019/Conference'
        assert 'Venue homepage template' in home_group.web

        home_group.web = 'This is a webfield'
        client.post_group(home_group)

        conference = builder.get_result()
        groups = conference.get_conference_groups()
        assert 'This is a webfield' in groups[-1].web

        builder.set_override_homepage(True)
        conference = builder.get_result()
        groups = conference.get_conference_groups()
        assert 'Venue homepage template' in groups[-1].web

    def test_web_set_landing_page(self, client):
        builder = openreview.conference.ConferenceBuilder(client)
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
        print(group.web)
        client.post_group(group)

        builder.set_conference_id("ds.cs.umass.edu/Test_I/2019/Workshop/WS_1")
        conference = builder.get_result()
        # check webfield contains 'Conference', 'Party' and 'Workshop'
        group = client.get_group(id='ds.cs.umass.edu/Test_I/2019')
        assert 'ds.cs.umass.edu/Test_I/2019/Conference' in group.web, 'Venue parent group missing child conference group'
        assert 'ds.cs.umass.edu/Test_I/2019/Workshop' in group.web, 'Venue parent group missing child workshop group'
        assert 'Party' in group.web, 'Venue parent group missing child inserted group'

    def test_modify_review_form(self, client, test_client, selenium, request_page, helpers):

        builder = openreview.conference.ConferenceBuilder(client)
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
        conference = builder.get_result()

        conference.set_program_chairs()
        conference.set_reviewers(emails = ['reviewer_test1@mail.com'])

        author_client = helpers.create_user('author_test1@mail.com', 'Test', 'Author')
        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~Test_Author1', 'drew@mail.com', 'test.org/2019/Conference/Program_Chairs'],
            writers = [conference.id, '~Test_Author1', 'drew@mail.com'],
            signatures = ['~Test_Author1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['author_test1@mail.com', 'drew@mail.com'],
                'authors': ['Test Author', 'Drew Barrymore']
            }
        )
        url = client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note.content['pdf'] = url
        client.post_note(note)

        original_notes = client.get_notes(invitation = conference.get_submission_id())
        assert original_notes
        assert len(original_notes) == 1

        with pytest.raises(openreview.OpenReviewException, match=r'.*Submission invitation is still due. Aborted blind note creation.*'):
            conference.create_blind_submissions()

        builder.set_submission_stage(double_blind = True, public = False, due_date = now)
        conference = builder.get_result()

        blind_submissions = conference.create_blind_submissions()
        assert blind_submissions
        assert len(blind_submissions) == 1

        conference.set_authors()
        conference.set_review_stage(conference.review_stage)

        reviewer_client = helpers.create_user('reviewer_test1@mail.com', 'Test', 'ReviewerOne')

        conference.set_assignment('reviewer_test1@mail.com', blind_submissions[0].number)

        request_page(selenium, "http://localhost:3000/forum?id=" + blind_submissions[0].id, reviewer_client.token)
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