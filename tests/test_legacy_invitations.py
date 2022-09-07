from __future__ import absolute_import, division, print_function, unicode_literals
from selenium.webdriver.common.by import By
import openreview
from openreview.conference.builder import MetaReviewStage
import pytest
import requests
import datetime
import time
import os

class TestLegacyInvitations():

    def test_single_blind_conference(self, client, test_client, selenium, request_page, helpers) :

        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2019/Workshop/MLITS')
        builder.set_conference_name('2019 NIPS MLITS Workshop')
        builder.set_homepage_header({
        'title': '2019 NIPS MLITS Workshop',
        'subtitle': 'Machine Learning for Intelligent Transportation Systems',
        'deadline': 'October 12, 2018, 11:59 pm UTC',
        'date': 'December 3-8, 2018',
        'website': 'https://sites.google.com/site/nips2018mlits/home',
        'location': 'Montreal, Canada',
        'instructions': ''
        })
        builder.has_area_chairs(True)
        builder.use_legacy_invitation_id(True)
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(
            public = True,
            due_date = now + datetime.timedelta(minutes = 40),
            withdrawn_submission_public=True,
            withdrawn_submission_reveal_authors=True,
            desk_rejected_submission_public=True,
            desk_rejected_submission_reveal_authors=True)
        builder.set_review_stage(openreview.ReviewStage(due_date = now + datetime.timedelta(minutes = 40)))
        builder.set_meta_review_stage(openreview.MetaReviewStage(due_date = now + datetime.timedelta(minutes = 40)))
        conference = builder.get_result()
        conference.create_review_stage()
        conference.create_meta_review_stage()

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@mail.com'],
            writers = ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@mail.com'],
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
        test_client.post_note(note)

        conference.setup_final_deadline_stage()

        submissions = conference.get_submissions()
        assert len(submissions) == 1
        assert submissions[0].readers == ['everyone']

        conference.set_reviewers(['reviewer_legacy@mail.com'])
        conference.set_area_chairs(['ac_legacy@mail.com'])
        conference.set_program_chairs(['pc_legacy@mail.com'])
        conference.set_assignment('reviewer_legacy@mail.com', 1)
        conference.set_assignment('ac_legacy@mail.com', 1, True)

        comment_invitees = [openreview.CommentStage.Readers.REVIEWERS_ASSIGNED, openreview.CommentStage.Readers.AREA_CHAIRS_ASSIGNED,
                            openreview.CommentStage.Readers.AUTHORS]
        conference.set_comment_stage(openreview.CommentStage(invitees=comment_invitees, readers=comment_invitees))
        conference.open_reviews()
        conference.open_meta_reviews()
        conference.open_decisions()

        assert client.get_invitations(regex = 'NIPS.cc/2019/Workshop/MLITS/-/Paper.*/Official_Comment')
        assert client.get_invitations(regex = 'NIPS.cc/2019/Workshop/MLITS/-/Paper.*/Official_Review')
        assert client.get_invitations(regex = 'NIPS.cc/2019/Workshop/MLITS/-/Paper.*/Meta_Review')
        assert client.get_invitations(regex = 'NIPS.cc/2019/Workshop/MLITS/-/Paper.*/Decision')

        reviewer_client = helpers.create_user('reviewer_legacy@mail.com', 'Reviewer', 'Legacy')
        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2019/Workshop/MLITS/Reviewers", reviewer_client.token, by=By.CLASS_NAME, wait_for_element='tabs-container')
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('assigned-papers')
        assert len(tabs.find_element_by_id('assigned-papers').find_elements_by_class_name('note')) == 1
        assert tabs.find_element_by_id('reviewer-tasks')
        assert len(tabs.find_element_by_id('reviewer-tasks').find_elements_by_class_name('note')) == 1

        ac_client = helpers.create_user('ac_legacy@mail.com', 'AC', 'Legacy')
        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2019/Workshop/MLITS/Area_Chairs", ac_client.token, by=By.CLASS_NAME, wait_for_element='tabs-container')
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('assigned-papers')
        assert len(tabs.find_element_by_id('assigned-papers').find_elements_by_class_name('note')) == 1
        assert tabs.find_element_by_id('areachair-tasks')
        assert len(tabs.find_element_by_id('areachair-tasks').find_elements_by_class_name('note')) == 1
        reviews = tabs.find_elements_by_class_name('reviewer-progress')
        assert reviews
        assert len(reviews) == 1
        headers = reviews[0].find_elements_by_tag_name('h4')
        assert headers
        assert headers[0].text == '0 of 1 Reviews Submitted'

        pc_client = helpers.create_user('pc_legacy@mail.com', 'PC', 'Legacy')
        request_page(selenium, "http://localhost:3030/group?id=NIPS.cc/2019/Workshop/MLITS/Program_Chairs", pc_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('venue-configuration')
        assert tabs.find_element_by_id('paper-status')
        assert tabs.find_element_by_id('areachair-status')
        assert tabs.find_element_by_id('reviewer-status')
