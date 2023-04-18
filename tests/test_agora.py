import openreview
import pytest
import time
from selenium.common.exceptions import NoSuchElementException


class TestAgora():

    def test_setup(self, client, helpers, request_page, selenium):

        ##Create support group

        support_group = openreview.Group(
            id='openreview.net/Support',
            readers=['everyone'],
            writers=['openreview.net/Support'],
            signatures=['openreview.net'],
            signatories=['openreview.net/Support'],
            members=[],
        )
        client.post_group(support_group)

        agora = openreview.agora.Agora(client, support_group.id, 'openreview.net', 'editor@agora.net')

        request_page(selenium, "http://localhost:3030/group?id=-Agora/COVID-19", by='class name', wait_for_element='tabs-container')
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

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = 'Agora COVID-19 has received your submission titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients
        text = messages[0]['content']['text']
        assert 'Your submission to Agora COVID-19 has been posted.' in text
        assert 'Title: Paper title\nYour submission will be examined by the Editor-in-Chief of the venue and you will receive an email with their response shortly.\nTo your submission can be viewed on OpenReview here:' in text

        messages = client.get_messages(subject = 'Agora COVID-19 has received a submission titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'editor@agora.net' in recipients

    def test_moderate_submission(self, client, helpers):

        editor_client = helpers.create_user(email = 'editor@agora.net', first = 'Editor', last = 'One')

        submissions = editor_client.get_notes(invitation='-Agora/COVID-19/-/Submission')
        assert submissions

        note = openreview.Note(invitation = '-Agora/COVID-19/Submission1/-/Moderation',
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

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        assert not editor_client.get_notes(invitation='-Agora/COVID-19/-/Submission')
        assert len(editor_client.get_notes(invitation='-Agora/COVID-19/-/Article')) == 1
        assert len(editor_client.get_notes(invitation='-Agora/COVID-19/-/Desk_Rejected')) == 0

        messages = client.get_messages(subject = '[Agora/COVID-19] Your submission has been accepted')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients
        assert messages[0]['content']['text'] == f'Congratulations, your submission titled "Paper title" has been accepted by ~Editor_One1, the Editor-in-Chief of this venue.\nYour article is now visible to the public and an editor will be assigned soon based on your suggestions.\n\nThe article can be viewed on OpenReview here: https://openreview.net/forum?id={submissions[0].id}'


    def test_assign_editor(self, client, helpers):

        editor_client = openreview.Client(username='editor@agora.net', password=helpers.strong_password)

        articles = editor_client.get_notes(invitation='-Agora/COVID-19/-/Article')
        assert articles

        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Editors_Assignment',
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

        helpers.await_queue()

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

        messages = client.get_messages(subject = '[Agora/COVID-19] You have been assigned to be an editor of the article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'article_editor@agora.net' in recipients


    def test_assign_reviewer(self, client, helpers):

        article_editor_client = helpers.create_user(email = 'article_editor@agora.net', first = 'ArticleEditor', last = 'One')

        articles = article_editor_client.get_notes(invitation='-Agora/COVID-19/-/Article')
        assert articles

        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Reviewers_Assignment',
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

        helpers.await_queue()

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

        messages = client.get_messages(subject = '[Agora/COVID-19] You have been assigned as a reviewer of the article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer@agora.net' in recipients

        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Reviewers_Assignment',
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

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        group = client.get_group('-Agora/COVID-19/Article1/Reviewers')
        assert group
        assert group.members == ['reviewer@agora.net', 'reviewer2@agora.net']

        messages = client.get_messages(subject = '[Agora/COVID-19] You have been assigned as a reviewer of the article titled "Paper title"')
        assert len(messages) == 2
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer@agora.net' in recipients
        assert 'reviewer2@agora.net' in recipients

    def test_post_review(self, client, helpers):

        reviewer_client = helpers.create_user(email = 'reviewer@agora.net', first = 'ArticleReviewer', last = 'One')

        articles = reviewer_client.get_notes(invitation='-Agora/COVID-19/-/Article')
        assert articles

        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Review',
            readers = ['everyone'],
            writers = ['openreview.net/Support', '~ArticleReviewer_One1'],
            signatures = ['~ArticleReviewer_One1'],
            forum = articles[0].id,
            replyto = articles[0].id,
            content = {
                'title': 'review title',
                'review': 'excelent paper'
            }
        )

        posted_note = reviewer_client.post_note(note)

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[Agora/COVID-19] Review posted to your article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients

        messages = client.get_messages(subject = '[Agora/COVID-19] Your review has been posted on your assigned article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer@agora.net' in recipients

        messages = client.get_messages(subject = '[Agora/COVID-19] A review has been posted on the article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'article_editor@agora.net' in recipients


    def test_post_comment(self, client, helpers):

        reviewer_client = openreview.Client(username = 'reviewer@agora.net', password = helpers.strong_password)

        reviews = reviewer_client.get_notes(invitation='-Agora/COVID-19/Article1/-/Review')
        assert reviews

        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Comment',
            readers = ['everyone'],
            writers = ['openreview.net/Support', '~ArticleReviewer_One1'],
            signatures = ['~ArticleReviewer_One1'],
            forum = reviews[0].forum,
            replyto = reviews[0].id,
            content = {
                'title': 'review title',
                'comment': 'comment on a review'
            }
        )

        posted_note = reviewer_client.post_note(note)

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[Agora/COVID-19] Comment posted to your article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients

        messages = client.get_messages(subject = '[Agora/COVID-19] Your comment has been posted on the article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer@agora.net' in recipients

        messages = client.get_messages(subject = '[Agora/COVID-19] A comment has been posted on the article titled "Paper title"')
        assert len(messages) == 2
        recipients = [m['content']['to'] for m in messages]
        assert 'article_editor@agora.net' in recipients
        assert 'reviewer2@agora.net' in recipients

        author_client = openreview.Client(username = 'author@agora.net', password = helpers.strong_password)
        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Comment',
            readers = ['everyone'],
            writers = ['openreview.net/Support', '-Agora/COVID-19/Article1/Authors'],
            signatures = ['-Agora/COVID-19/Article1/Authors'],
            forum = reviews[0].forum,
            replyto = reviews[0].id,
            content = {
                'title': 'review title',
                'comment': 'comment on a review'
            }
        )

        posted_note = author_client.post_note(note)

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[Agora/COVID-19] Your comment has been posted on the article titled "Paper title"')
        assert len(messages) == 2
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer@agora.net' in recipients
        assert 'author@agora.net' in recipients

        messages = client.get_messages(subject = '[Agora/COVID-19] A comment has been posted on the article titled "Paper title"')
        assert len(messages) == 5
        recipients = [m['content']['to'] for m in messages]
        assert 'article_editor@agora.net' in recipients
        assert 'reviewer2@agora.net' in recipients
        assert 'reviewer@agora.net' in recipients

    def test_suggest_reviewer(self, client, helpers):

        melisa_client = helpers.create_user(email = 'melisa_agora@mail.com', first = 'Melissa', last = 'Agora')

        articles = melisa_client.get_notes(invitation='-Agora/COVID-19/-/Article')
        assert articles

        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Reviewers_Suggestion',
            readers = ['everyone'],
            writers = ['openreview.net/Support', '~Melissa_Agora1'],
            signatures = ['~Melissa_Agora1'],
            forum = articles[0].forum,
            replyto = articles[0].id,
            content = {
                'suggested_reviewers': ['~Melissa_Agora1'],
                'comment': 'I think I can review this paper'
            }
        )

        posted_note = melisa_client.post_note(note)

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[Agora/COVID-19] Your suggestion has been posted on the article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'melisa_agora@mail.com' in recipients

        messages = client.get_messages(subject = '[Agora/COVID-19] A reviewer has been suggested on the article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'article_editor@agora.net' in recipients


    def test_add_revision(self, client, helpers):

        author_client = openreview.Client(username = 'author@agora.net', password = helpers.strong_password)

        articles = author_client.get_notes(invitation='-Agora/COVID-19/-/Article')
        assert articles

        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Revision',
            readers = ['everyone'],
            writers = ['openreview.net/Support', '-Agora/COVID-19/Article1/Authors'],
            signatures = ['-Agora/COVID-19/Article1/Authors'],
            forum = articles[0].forum,
            referent = articles[0].id,
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['~Author_One1'],
                'authors': ['Author One'],
                'pdf': 'https://openreview.net',
                'requested_editors': ['editor-submission@agora.net', 'editor-submission-2@agora.net']
            }
        )

        posted_note = author_client.post_note(note)

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[Agora/COVID-19] Your revision has been posted on your article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients

        messages = client.get_messages(subject = '[Agora/COVID-19] A revision has been posted on the article titled "Paper title"')
        assert len(messages) == 3
        recipients = [m['content']['to'] for m in messages]
        assert 'article_editor@agora.net' in recipients
        assert 'reviewer@agora.net' in recipients
        assert 'reviewer2@agora.net' in recipients

    def test_post_metareview(self, client, helpers):

        article_editor_client = openreview.Client(username='article_editor@agora.net', password=helpers.strong_password)

        articles = article_editor_client.get_notes(invitation='-Agora/COVID-19/-/Article')
        assert articles

        note = openreview.Note(invitation = '-Agora/COVID-19/Article1/-/Meta_Review',
            readers = ['everyone'],
            writers = ['openreview.net/Support', '~ArticleEditor_One1'],
            signatures = ['~ArticleEditor_One1'],
            forum = articles[0].id,
            replyto = articles[0].id,
            content = {
                'title': 'review title',
                'metareview': 'excelent paper',
                'recommendation': 'Accept'
            }
        )

        posted_note = article_editor_client.post_note(note)

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = client.get_messages(subject = '[Agora/COVID-19] Meta Review posted to your article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients

        messages = client.get_messages(subject = '[Agora/COVID-19] Your meta review has been posted on your assigned article titled "Paper title"')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'article_editor@agora.net' in recipients

        messages = client.get_messages(subject = '[Agora/COVID-19] A meta review has been posted on the article titled "Paper title"')
        assert len(messages) == 2
        recipients = [m['content']['to'] for m in messages]
        assert 'reviewer@agora.net' in recipients
        assert 'reviewer2@agora.net' in recipients

    def test_desk_reject(self, client, helpers):

        author_client = openreview.Client(username = 'author@agora.net', password = helpers.strong_password)

        note = openreview.Note(invitation = '-Agora/COVID-19/-/Submission',
            readers = ['openreview.net/Support', '-Agora/COVID-19/Editors', '~Author_One1'],
            writers = ['openreview.net/Support', '-Agora/COVID-19/Editors', '~Author_One1'],
            signatures = ['~Author_One1'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'This is an abstract 2',
                'authorids': ['~Author_One1'],
                'authors': ['Author One'],
                'pdf': 'https://openreview.net',
                'requested_editors': ['editor-submission@agora.net']
            }
        )

        posted_note = author_client.post_note(note)

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        editor_client = openreview.Client(username='editor@agora.net', password=helpers.strong_password)

        submissions = editor_client.get_notes(invitation='-Agora/COVID-19/-/Submission')
        assert submissions

        note = openreview.Note(invitation = '-Agora/COVID-19/Submission2/-/Moderation',
            readers = ['openreview.net/Support', '-Agora/COVID-19/Editors', '-Agora/COVID-19/Submission2/Authors'],
            writers = ['openreview.net/Support'],
            signatures = ['~Editor_One1'],
            forum = submissions[0].id,
            replyto = submissions[0].id,
            content = {
                'resolution': 'Desk-Reject',
                'comment': 'This is not good'
            }
        )

        posted_note = editor_client.post_note(note)

        helpers.await_queue()

        process_logs = client.get_process_logs(id = posted_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        assert not editor_client.get_notes(invitation='-Agora/COVID-19/-/Submission')
        assert len(editor_client.get_notes(invitation='-Agora/COVID-19/-/Article')) == 1
        assert len(editor_client.get_notes(invitation='-Agora/COVID-19/-/Desk_Rejected')) == 1

        messages = client.get_messages(subject = '[Agora/COVID-19] Your submission has been rejected')
        assert len(messages) == 1
        recipients = [m['content']['to'] for m in messages]
        assert 'author@agora.net' in recipients
        text = messages[0]['content']['text']
        assert 'Unfortunately your submission has been desk-rejected by the Editor-in-Chief of this venue.' in text
        assert 'For more information, see their comment on the OpenReview submission forum here:' in text
