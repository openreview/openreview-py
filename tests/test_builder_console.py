from __future__ import absolute_import, division, print_function, unicode_literals
import os
import datetime
import openreview
import pytest
from selenium.common.exceptions import NoSuchElementException

class TestBuilderConsoles():

    def test_PC_console_web_edit(self, client, test_client, selenium, request_page, helpers):
        def word_after(text, keyword):
            before_keyword, keyword, after_keyword = text.partition(keyword)
            before_keyword, keyword, after_keyword = after_keyword.partition(";")
            return before_keyword

        builder = openreview.conference.ConferenceBuilder(client, support_user='openreview.net/Support')
        assert builder, 'builder is None'

        builder.set_conference_id('PcConsoleTest.org/2020/Conference')
        builder.set_conference_name('PC Console Test Conference 2020')
        builder.set_conference_short_name('PC Console TEST Conf 2020')
        builder.set_homepage_header({
            'title': 'PC Console Test Conference 2020',
            'subtitle': 'PC Console TEST Conf 2020',
            'deadline': 'Submission Deadline: March 17, 2020 midnight AoE',
            'date': 'Sept 11-15, 2020',
            'website': 'https://testconf20.com',
            'location': 'Berkeley, CA, USA'
        })
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(double_blind=True, public=False, due_date=now + datetime.timedelta(minutes=10))
        builder.has_area_chairs(False)
        conference = builder.get_result()

        pc_group = client.get_group(conference.get_program_chairs_id())
        orig_web = pc_group.web
        assert orig_web, "Error initializing PC console"
        # check setting PC group doesn't change the PC console
        conference.set_program_chairs(emails=['pc_testconsole1@mail.com'])
        pc_group = client.get_group(conference.get_program_chairs_id())
        assert orig_web == pc_group.web, "Error setting PC members changed console"

        # update web manually
        pc_group.web = pc_group.web.replace("PC Console TEST Conf 2020",
                                            "PC Console TEST Conf YEAR")
        # we make manual change so we don't want it overwritten
        pc_group.web = pc_group.web.replace("// webfield_template",
                                            "")
        pc_group = client.post_group(pc_group)
        customized_web = pc_group.web

        # check customized web different from original
        assert orig_web != customized_web, "Error customizing PC web"

        conference = builder.get_result()
        pc_group = client.get_group(conference.get_program_chairs_id())
        assert pc_group.web == customized_web, "Error customized PC Console overwritten"

        # need a paper to be able to check if reassign reviewers is activated
        helpers.create_user('author_test2@mail.com', 'SomeFirstName', 'AuthorTwo')
        author_client = openreview.Client(username='author_test2@mail.com', password=helpers.strong_password)

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~SomeFirstName_AuthorTwo1', 'drew@mail.com', conference.get_id()],
            writers = [conference.id, '~SomeFirstName_AuthorTwo1', 'drew@mail.com'],
            signatures = ['~SomeFirstName_AuthorTwo1'],
            content = {
                'title': 'Paper title PC Console Conference',
                'abstract': 'This is an abstract',
                'authorids': ['author_test2@mail.com', 'drew@mail.com'],
                'authors': ['SomeFirstName AuthorTwo', 'Drew Barrymore']
            }
        )
        url = author_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note.content['pdf'] = url
        author_client.post_note(note)

        pc_group = client.get_group(conference.get_program_chairs_id())
        assert word_after(pc_group.web, 'ENABLE_REVIEWER_REASSIGNMENT = ') == 'false'

        conference.set_reviewer_reassignment(enabled = True)
        pc_group = client.get_group(conference.get_program_chairs_id())
        assert word_after(pc_group.web, 'ENABLE_REVIEWER_REASSIGNMENT = ') == 'true'

        conference.set_reviewer_reassignment(enabled=False)
        pc_group = client.get_group(conference.get_program_chairs_id())
        assert word_after(pc_group.web, 'ENABLE_REVIEWER_REASSIGNMENT = ') == 'false'

        assert "Blind" not in word_after(pc_group.web, 'BLIND_SUBMISSION_ID = ')
        conference.setup_post_submission_stage(force=True)
        pc_group = client.get_group(conference.get_program_chairs_id())
        assert "Blind"  in word_after(pc_group.web, 'BLIND_SUBMISSION_ID = ')
