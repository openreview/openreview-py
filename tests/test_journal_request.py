import openreview
import pytest
from openreview.api import OpenReviewClient
from openreview.api import Invitation
from openreview.api import Note
from openreview.journal import JournalRequest

class TestJournalRequest():

    @pytest.fixture(scope='class')
    def journal(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        journal_request = JournalRequest(openreview_client, support_group_id)
        journal_request.setup_journal_request()

        helpers.await_queue()

        #post journal request form
        request_form = openreview_client.post_note_edit(invitation= support_group_id + '/-/Journal_Request',
            signatures = [support_group_id],
            note = Note(
                signatures = [support_group_id],
                content = {
                    'official_venue_name': {'value': 'Test Journal 2022'},
                    'abbreviated_venue_name' : {'value': 'TJ22'},
                    'venue_id': {'value': '.TJ22'},
                    'contact_info': {'value': 'test@venue.org'},
                    'secret_key': {'value': '4567'},
                    'support_role': {'value': 'support_role@mail.com' },
                    'editors': {'value': ['editor1@mail.com', 'editor2@mail.com'] }
                }
            ))

        helpers.await_queue()

        #return journal details
        journal_details = {
            'journal_request_note': request_form['note'],
            'suppot_group_id': support_group_id
        }
        return journal_details

    def test_journal_setup(self, openreview_client, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        journal_request = JournalRequest(openreview_client, support_group_id)
        journal_request.setup_journal_request()

        assert journal_request.support_group.id == support_group_id
        journal_request_invitation = openreview_client.get_invitation(id = support_group_id + '/-/Journal_Request')
        assert journal_request_invitation

    def test_journal_deployment(self, openreview_client, test_client, selenium, request_page, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        journal_request = JournalRequest(openreview_client, support_group_id)
        journal_request.setup_journal_request()

        helpers.await_queue()
        request_page(selenium, 'http://localhost:3030/group?id={}&mode=default'.format(support_group_id), openreview_client.token)

        request_form = openreview_client.post_note_edit(invitation = support_group_id + '/-/Journal_Request',
            signatures = [support_group_id],
            note = Note(
                signatures = [support_group_id],
                content = {
                    'official_venue_name': {'value': 'Test Journal 2040'},
                    'abbreviated_venue_name' : {'value': 'TJ40'},
                    'venue_id': {'value': '.TJ40'},
                    'contact_info': {'value': 'test@journal.org'},
                    'secret_key': {'value': '4567'},
                    'support_role': {'value': 'support_role@mail.com' },
                    'editors': {'value': ['editor1@mail.com', 'editor2@mail.com'] }
                }
            ))

        assert request_form
        request_page(selenium, 'http://localhost:3030/forum?id=' + request_form['note']['id'], openreview_client.token)

        process_logs = openreview_client.get_process_logs(invitation = support_group_id + '/-/Journal_Request')
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

    def test_journal_recruitment(self, openreview_client, selenium, request_page, helpers, journal):

        helpers.create_user('support_role@mail.com', 'Support', 'Role')
        test_client = OpenReviewClient(username='support_role@mail.com', password='1234')

        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(journal['journal_request_note']['id']), test_client.token)
        recruitment_div = selenium.find_element_by_id('note_{}'.format(journal['journal_request_note']['id']))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Recruitment']

        helpers.create_user('reviewer_journal2@mail.com', 'Second', 'Reviewer')

        reviewer_details = { 'value': '''reviewer_journal1@mail.com, First Reviewer\n~Second_Reviewer1'''}
        recruitment_note = test_client.post_note_edit(
            invitation = '{}/-/Journal_Request{}/Recruitment'.format(journal['suppot_group_id'],journal['journal_request_note']['number']),
            signatures = ['~Support_Role1'],
            note = Note(
                content = {
                    'title': { 'value': 'Recruitment' },
                    'invitee_role': { 'value': 'reviewer' },
                    'invitee_details': reviewer_details,
                    'email_subject': { 'value': '[' + journal['journal_request_note']['content']['abbreviated_venue_name']['value'] + '] Invitation to serve as {invitee_role}' },
                    'email_content': {'value': 'Dear {name},\n\nYou have been nominated by the program chair committee of TJ22 to serve as {invitee_role}.\n\nACCEPT LINK:\n{accept_url}\n\nDECLINE LINK:\n{decline_url}\n\nCheers!'}
                },
                forum = journal['journal_request_note']['forum'],
                replyto = journal['journal_request_note']['forum'],
                signatures = ['~Support_Role1']
            ))
        assert recruitment_note

        helpers.await_queue(openreview_client)
        process_logs = openreview_client.get_process_logs(id = recruitment_note['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/-/Journal_Request{}/Recruitment'.format(journal['suppot_group_id'],journal['journal_request_note']['number'])

        invited_group = openreview_client.get_group('{}/Reviewers/Invited'.format(journal['journal_request_note']['content']['venue_id']['value']))
        assert invited_group
        assert len(invited_group.members) == 2
        assert 'reviewer_journal1@mail.com' in invited_group.members
        assert '~Second_Reviewer1' in invited_group.members

        messages = openreview_client.get_messages(to = 'reviewer_journal1@mail.com', subject = '[TJ22] Invitation to serve as reviewer')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('<p>Dear First Reviewer,</p>\n<p>You have been nominated by the program chair committee of TJ22 to serve as reviewer.</p>')

        messages = openreview_client.get_messages(to = 'reviewer_journal2@mail.com', subject = '[TJ22] Invitation to serve as reviewer')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('<p>Dear Second Reviewer,</p>\n<p>You have been nominated by the program chair committee of TJ22 to serve as reviewer.</p>')