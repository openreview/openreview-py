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

class TestOptionalDoubleBlind():

    def test_anonymize_based_user_option(self, client, test_client, selenium, request_page):

        builder = openreview.conference.ConferenceBuilder(client)

        builder.set_conference_id('icaps-conference.org/ICAPS/2019/Workshop/VRDIP')
        builder.set_conference_name('Planning the Future: Economics and Value-Rational')
        builder.set_conference_short_name('ICAPS Workshop 2019 VRDIP')
        builder.set_homepage_header({
        'title': 'Planning the Future: Economics and Value-Rational',
        'subtitle': 'ICAPS 2019 Workshop',
        'deadline': 'Submission Deadline: April 15, 2019',
        'date': 'July 11, 2019',
        'website': 'https://icaps19.icaps-conference.org/workshops/Planning-the-Future/index.html',
        'location': 'Berkeley, CA, USA'
        })
        builder.set_double_blind(True)
        builder.set_submission_public(True)   
        conference = builder.get_result()
        assert conference    

        now = datetime.datetime.now() + datetime.timedelta(hours = (time.timezone / 3600.0))
        invitation = conference.open_submissions(due_date = now + datetime.timedelta(minutes = 10), additional_fields = {
            "author_identity_visibility": {
                "order": 4,
                "value-checkbox": 'Reveal author identities',
                "required": False
            }
        })
        assert invitation

        note = openreview.Note(invitation = invitation.id,
            readers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            writers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
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

        note_2 = openreview.Note(invitation = invitation.id,
            readers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            writers = ['~Test_User1', 'peter@mail.com', 'andrew@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'This is an abstract 2',
                'authorids': ['test@mail.com', 'peter@mail.com', 'andrew@mail.com'],
                'authors': ['Test User', 'Peter User', 'Andrew Mc'],
                'author_identity_visibility': 'Reveal author identities'
            }
        )
        url = test_client.put_pdf(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'))
        note_2.content['pdf'] = url
        test_client.post_note(note_2)        

        # Author user
        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/VRDIP", test_client.token)
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 1
        assert 'ICAPS 2019 Workshop VRDIP Submission' == invitation_panel.find_element_by_class_name('btn').text
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

        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/VRDIP/Authors", test_client.token)
        tabs = selenium.find_element_by_class_name('tabs-container')
        assert tabs
        assert tabs.find_element_by_id('author-schedule')
        assert tabs.find_element_by_id('author-tasks')
        assert tabs.find_element_by_id('your-submissions')
        papers = tabs.find_element_by_id('your-submissions').find_element_by_class_name('submissions-list')
        assert len(papers.find_elements_by_class_name('note')) == 2

        conference.close_submissions()

        blind_submissions = conference.create_blind_submissions()
        assert blind_submissions
        assert len(blind_submissions) == 2

        guest_client = openreview.Client()

        request_page(selenium, "http://localhost:3000/group?id=icaps-conference.org/ICAPS/2019/Workshop/VRDIP", guest_client.token)
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        assert len(invitation_panel.find_elements_by_tag_name('div')) == 0
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        submissions = tabs.find_element_by_id('all-submissions')
        assert submissions
        assert len(submissions.find_elements_by_class_name('submissions-list')) == 1
        assert len(submissions.find_elements_by_class_name('note-authors')) == 2
        assert 'Test User, Peter User, Andrew Mc' == submissions.find_elements_by_class_name('note-authors')[0].text
        assert 'Anonymous' == submissions.find_elements_by_class_name('note-authors')[1].text
        






        