import openreview
import pytest
import time
from selenium.common.exceptions import NoSuchElementException


class TestAgora():

    def test_setup(self, client, request_page, selenium):

        ##Create support group

        support_group = openreview.Group(
            id='openreview.net/Support',
            readers=['everyone'],
            writers=['openreview.net'],
            signatures=['openreview.net'],
            signatories=['openreview.net/Support'],
            members=[],

        )
        client.post_group(support_group)

        agora = openreview.agora.Agora(client, support_group.id, 'openreview.net')

        request_page(selenium, "http://localhost:3000/group?id=-Agora/Covid-19")
        header = selenium.find_element_by_id('header')
        assert header
        invitation_panel = selenium.find_element_by_id('invitation')
        assert invitation_panel
        notes_panel = selenium.find_element_by_id('notes')
        assert notes_panel
        tabs = notes_panel.find_element_by_class_name('tabs-container')
        assert tabs
        with pytest.raises(NoSuchElementException):
            notes_panel.find_element_by_class_name('spinner-container')

    def test_post_submission(self, client, helpers):

        author_client = helpers.create_user(email = 'author@agora.net', first = 'Author', last = 'One')

        note = openreview.Note(invitation = '-Agora/Covid-19/-/Submission',
            readers = ['openreview.net/Support', '-Agora/Covid-19/Editors', '~Author_One1'],
            writers = ['openreview.net/Support', '-Agora/Covid-19/Editors', '~Author_One1'],
            signatures = ['~Author_One1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['~Author_One1'],
                'authors': ['Author One'],
                'pdf': 'https://openreview.net',
                'requested_editors': ['editor-submission@agora.net']
            }
        )

        posted_note = author_client.post_note(note)

        time.sleep(2)

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = 'Agora Covid-19 has received your submission titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients