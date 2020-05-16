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

        agora = openreview.agora.Agora(client, support_group.id, 'openreview.net', 'editor@agora.net')

        request_page(selenium, "http://localhost:3000/group?id=-Agora/COVID-19")
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

        note = openreview.Note(invitation = '-Agora/COVID-19/-/Submission',
            readers = ['openreview.net/Support', '-Agora/COVID-19/Editors', '~Author_One1'],
            writers = ['openreview.net/Support', '-Agora/COVID-19/Editors', '~Author_One1'],
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

        messages = client.get_messages(subject = 'Agora COVID-19 has received your submission titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients
        assert messages[0]['content']['text'] == 'Your submission to Agora COVID-19 has been posted.\n\nTitle: Paper title\nYour submission will be examined by the Editor-in-Chief of the venue and then you will receive an email with a response.\nTo view your submission, click here: https://openreview.net/forum?id=' + posted_note.id

        messages = client.get_messages(subject = 'Agora COVID-19 has received a submission titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'editor@agora.net' in recipients

    def test_moderate_submission(self, client, helpers):

        editor_client = helpers.create_user(email = 'editor@agora.net', first = 'Editor', last = 'One')

        submissions = editor_client.get_notes(invitation='-Agora/COVID-19/-/Submission')
        assert submissions

        note = openreview.Note(invitation = '-Agora/COVID-19/Submission1/-/Moderate',
            readers = ['openreview.net/Support', '-Agora/COVID-19/Editors', '-Agora/COVID-19/Submission1/Authors'],
            writers = ['openreview.net/Support'],
            signatures = ['~Editor_One1'],
            forum = submissions[0].id,
            replyto = submissions[0].id,
            content = {
                'resolution': 'Accept',
                'comment': 'Thanks for submitting!'
            }
        )

        posted_note = editor_client.post_note(note)

        time.sleep(2)

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        assert not editor_client.get_notes(invitation='-Agora/COVID-19/-/Submission')
        assert editor_client.get_notes(invitation='-Agora/COVID-19/-/Article')

        messages = client.get_messages(subject = '[Agora/COVID-19] Your submission has been accepted')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients
        assert messages[0]['content']['text'] == 'Congratulations, your submission has been accepted by ~Editor_One1, the Editor-in-Chief of this venue.\nYour article is now visible to the public and an editor will be assigned soon based on your suggestions.\n\nTo view your article, click here: https://openreview.net/forum?id=' + submissions[0].id


    def test_assign_editor(self, client, helpers):

        editor_client = openreview.Client(username='editor@agora.net', password='1234')

        articles = editor_client.get_notes(invitation='-Agora/COVID-19/-/Article')
        assert articles

        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Assign_Editor',
            readers = ['everyone'],
            writers = ['openreview.net/Support', '-Agora/COVID-19/Editors'],
            signatures = ['~Editor_One1'],
            forum = articles[0].id,
            referent = articles[0].id,
            content = {
                'assigned_editors': ['article_editor@agora.net'],
            }
        )

        posted_note = editor_client.post_note(note)

        time.sleep(2)

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        group = client.get_group('-Agora/COVID-19/Article1/Editors')
        assert group
        assert group.members == ['article_editor@agora.net']

        messages = client.get_messages(subject = '[Agora/COVID-19] An editor has been assigned to your article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients

        messages = client.get_messages(subject = '[Agora/COVID-19] You have been assigned as editor of the article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'article_editor@agora.net' in recipients


    def test_assign_reviewer(self, client, helpers):

        article_editor_client = helpers.create_user(email = 'article_editor@agora.net', first = 'ArticleEditor', last = 'One')

        articles = article_editor_client.get_notes(invitation='-Agora/COVID-19/-/Article')
        assert articles

        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Assign_Reviewer',
            readers = ['everyone'],
            writers = ['openreview.net/Support', '-Agora/COVID-19/Article1/Editors'],
            signatures = ['~ArticleEditor_One1'],
            forum = articles[0].id,
            referent = articles[0].id,
            content = {
                'assigned_reviewers': ['reviewer@agora.net'],
            }
        )

        posted_note = article_editor_client.post_note(note)

        time.sleep(2)

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        group = client.get_group('-Agora/COVID-19/Article1/Reviewers')
        assert group
        assert group.members == ['reviewer@agora.net']

        messages = client.get_messages(subject = '[Agora/COVID-19] A reviewer has been assigned to your article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients

        messages = client.get_messages(subject = '[Agora/COVID-19] You have been assigned as reviewer of the article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer@agora.net' in recipients

        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Assign_Reviewer',
            readers = ['everyone'],
            writers = ['openreview.net/Support', '-Agora/COVID-19/Article1/Editors'],
            signatures = ['~ArticleEditor_One1'],
            forum = articles[0].id,
            referent = articles[0].id,
            content = {
                'assigned_reviewers': ['reviewer@agora.net', 'reviewer2@agora.net'],
            }
        )

        posted_note = article_editor_client.post_note(note)

        time.sleep(2)

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        group = client.get_group('-Agora/COVID-19/Article1/Reviewers')
        assert group
        assert group.members == ['reviewer@agora.net', 'reviewer2@agora.net']

        messages = client.get_messages(subject = '[Agora/COVID-19] You have been assigned as reviewer of the article titled "Paper title"')
        assert len(messages) == 2
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer@agora.net' in recipients
        assert 'reviewer2@agora.net' in recipients