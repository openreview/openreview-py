import openreview
import pytest
from selenium.webdriver.common.by import By
import re
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

        helpers.await_queue(openreview_client)

        #post journal request form
        request_form = openreview_client.post_note_edit(invitation= support_group_id + '/-/Journal_Request',
            signatures = [support_group_id],
            note = Note(
                signatures = [support_group_id],
                content = {
                    'official_venue_name': {'value': 'Test Journal 2022'},
                    'abbreviated_venue_name' : {'value': 'TJ22'},
                    'venue_id': {'value': 'TJ22'},
                    'contact_info': {'value': 'test@venue.org'},
                    'secret_key': {'value': '4567'},
                    'support_role': {'value': 'support_role@mail.com' },
                    'editors': {'value': ['editor1@mail.com', 'editor2@mail.com'] },
                    'website': {'value': 'testjournal.org' }
                }
            ))

        helpers.await_queue(openreview_client)

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

        helpers.await_queue(openreview_client)
        request_page(selenium, 'http://localhost:3030/group?id={}&mode=default'.format(support_group_id), openreview_client.token)

        request_form = openreview_client.post_note_edit(invitation = support_group_id + '/-/Journal_Request',
            signatures = [support_group_id],
            note = Note(
                signatures = [support_group_id],
                content = {
                    'official_venue_name': {'value': 'Test Journal 2040'},
                    'abbreviated_venue_name' : {'value': 'TJ40'},
                    'venue_id': {'value': 'TJ40'},
                    'contact_info': {'value': 'test@journal.org'},
                    'secret_key': {'value': '4567'},
                    'support_role': {'value': 'support_role@mail.com' },
                    'editors': {'value': ['editor1@mail.com', 'editor2@mail.com'] },
                    'website': {'value': 'testjournal.org' }
                }
            ))

        helpers.await_queue(openreview_client)
        request_page(selenium, 'http://localhost:3030/forum?id=' + request_form['note']['id'], openreview_client.token)

        process_logs = openreview_client.get_process_logs(invitation = support_group_id + '/-/Journal_Request')
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        helpers.create_user('support_role@mail.com', 'Support', 'Role')
        test_client = OpenReviewClient(username='support_role@mail.com', password='1234')

        request_page(selenium, 'http://localhost:3030/forum?id=' + request_form['note']['id'], openreview_client.token, by=By.CLASS_NAME, wait_for_element='reply_row')
        recruitment_div = selenium.find_element_by_id('note_{}'.format(request_form['note']['id']))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Comment']

        #check request form id is added to AE console
        AE_group = openreview_client.get_group('{}/Action_Editors'.format(request_form['note']['content']['venue_id']['value']))
        assert "var JOURNAL_REQUEST_ID = '{}';".format(request_form['note']['id']) in AE_group.web

    def test_journal_reviewer_recruitment(self, openreview_client, selenium, request_page, helpers, journal):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        journal_request = JournalRequest(openreview_client, support_group_id)
        rev_template = '''Hi {name},

Greetings! You have been nominated by the program chair committee of TJ22 to serve as reviewer.

ACCEPT LINK:
{accept_url}

DECLINE LINK:
{decline_url}

Cheers!
TJ22 Editors-in-Chief
'''
        journal_request.setup_recruitment_invitations(journal['journal_request_note']['id'], reviewer_template=rev_template)

        test_client = OpenReviewClient(username='support_role@mail.com', password='1234')

        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(journal['journal_request_note']['id']), test_client.token, by=By.CLASS_NAME, wait_for_element='reply_row')
        recruitment_div = selenium.find_element_by_id('note_{}'.format(journal['journal_request_note']['id']))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Reviewer Recruitment']

        invitation = test_client.get_invitation(id='{}/Journal_Request{}/-/Reviewer_Recruitment'.format(journal['suppot_group_id'],journal['journal_request_note']['number']))
        assert 'Hi {name},\n\nGreetings! You have been nominated by the program chair committee of TJ22' in invitation.edit['note']['content']['email_content']['presentation']['default']

        helpers.create_user('reviewer_journal2@mail.com', 'Second', 'Reviewer')

        #add reviewer to invited group
        openreview_client.add_members_to_group(journal['journal_request_note']['content']['venue_id']['value']+ '/Reviewers/Invited', 'reviewer_journal3@mail.com')

        reviewer_details = { 'value': '''reviewer_journal1@mail.com, First Reviewer\n~Second_Reviewer1\nreviewer_journal3@mail.com'''}
        recruitment_note = test_client.post_note_edit(
            invitation = '{}/Journal_Request{}/-/Reviewer_Recruitment'.format(journal['suppot_group_id'],journal['journal_request_note']['number']),
            signatures = ['~Support_Role1'],
            note = Note(
                content = {
                    'title': { 'value': 'Recruitment' },
                    'invitee_details': reviewer_details,
                    'email_subject': { 'value': '[' + journal['journal_request_note']['content']['abbreviated_venue_name']['value'] + '] Invitation to serve as Reviewer for ' +  journal['journal_request_note']['content']['abbreviated_venue_name']['value']},
                    'email_content': {'value': 'Dear {name},\n\nYou have been nominated by the program chair committee of TJ22 to serve as reviewer.\n\nACCEPT LINK:\n{accept_url}\n\nDECLINE LINK:\n{decline_url}\n\nCheers!'}
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
        assert process_logs[0]['invitation'] == '{}/Journal_Request{}/-/Reviewer_Recruitment'.format(journal['suppot_group_id'],journal['journal_request_note']['number'])

        invited_group = openreview_client.get_group('{}/Reviewers/Invited'.format(journal['journal_request_note']['content']['venue_id']['value']))
        assert invited_group
        assert len(invited_group.members) == 3
        assert 'reviewer_journal1@mail.com' in invited_group.members
        assert '~Second_Reviewer1' in invited_group.members
        assert 'reviewer_journal3@mail.com' in invited_group.members

        messages = openreview_client.get_messages(to = 'reviewer_journal1@mail.com', subject = '[TJ22] Invitation to serve as Reviewer for TJ22')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('<p>Dear First Reviewer,</p>\n<p>You have been nominated by the program chair committee of TJ22 to serve as reviewer.</p>')

        messages = openreview_client.get_messages(to = 'reviewer_journal2@mail.com', subject = '[TJ22] Invitation to serve as Reviewer for TJ22')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('<p>Dear Second Reviewer,</p>\n<p>You have been nominated by the program chair committee of TJ22 to serve as reviewer.</p>')

        messages = openreview_client.get_messages(to = 'reviewer_journal3@mail.com')
        assert not messages

        inv = '{}/Journal_Request{}/-/Comment'.format(journal['suppot_group_id'],journal['journal_request_note']['number'])
        recruitment_status = openreview_client.get_notes(invitation=inv, replyto=recruitment_note['note']['id'])

        assert recruitment_status
        assert recruitment_status[0].content['title']['value'] == 'Recruitment Status'
        assert 'Invited: 2 Reviewer(s).' in recruitment_status[0].content['comment']['value']

    def test_journal_action_editor_recruitment(self, openreview_client, selenium, request_page, helpers, journal):

        test_client = OpenReviewClient(username='support_role@mail.com', password='1234')

        invitation = test_client.get_invitation(id='{}/Journal_Request{}/-/Action_Editor_Recruitment'.format(journal['suppot_group_id'],journal['journal_request_note']['number']))
        assert 'Dear {name},\n\nYou have been nominated by the program chair committee of TJ22' in invitation.edit['note']['content']['email_content']['presentation']['default']

        #add ae to invited group
        openreview_client.add_members_to_group(journal['journal_request_note']['content']['venue_id']['value']+ '/Action_Editors/Invited', 'ae_journal1@mail.com')

        #add ae to action editors group
        openreview_client.add_members_to_group(journal['journal_request_note']['content']['venue_id']['value']+ '/Action_Editors', 'already_actioneditor@mail.com')

        ae_details = { 'value': '''ae_journal1@mail.com, First AE\nae_journal2@mail.com, Second AE\nae_journal3@mail.com, Third AE\nalready_actioneditor@mail.com, Action Editor'''}
        recruitment_note = test_client.post_note_edit(
            invitation = '{}/Journal_Request{}/-/Action_Editor_Recruitment'.format(journal['suppot_group_id'],journal['journal_request_note']['number']),
            signatures = ['~Support_Role1'],
            note = Note(
                content = {
                    'title': { 'value': 'Recruitment' },
                    'invitee_details': ae_details,
                    'email_subject': { 'value': '[' + journal['journal_request_note']['content']['abbreviated_venue_name']['value'] + '] Invitation to serve as {role} for ' + journal['journal_request_note']['content']['abbreviated_venue_name']['value'] },
                    'email_content': {'value': 'Dear {name},\n\nYou have been nominated by the program chair committee of TJ22 to serve as action editor.\n\nACCEPT LINK:\n{accept_url}\n\nDECLINE LINK:\n{decline_url}\n\nCheers!'}
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
        assert process_logs[0]['invitation'] == '{}/Journal_Request{}/-/Action_Editor_Recruitment'.format(journal['suppot_group_id'],journal['journal_request_note']['number'])

        messages = openreview_client.get_messages(to = 'ae_journal1@mail.com')
        assert len(messages) == 0

        messages = openreview_client.get_messages(to = 'already_actioneditor@mail.com')
        assert len(messages) == 0

        messages = openreview_client.get_messages(to = 'ae_journal2@mail.com', subject = '[TJ22] Invitation to serve as Action Editor for TJ22')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('<p>Dear Second AE,</p>\n<p>You have been nominated by the program chair committee of TJ22 to serve as action editor.</p>')

        messages = openreview_client.get_messages(to = 'ae_journal3@mail.com', subject = '[TJ22] Invitation to serve as Action Editor for TJ22')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('<p>Dear Third AE,</p>\n<p>You have been nominated by the program chair committee of TJ22 to serve as action editor.</p>')

        inv = '{}/Journal_Request{}/-/Comment'.format(journal['suppot_group_id'],journal['journal_request_note']['number'])
        recruitment_status = openreview_client.get_notes(invitation=inv, replyto=recruitment_note['note']['id'])

        assert recruitment_status
        assert recruitment_status[0].content['title']['value'] == 'Recruitment Status'
        assert 'Invited: 2 Action Editor(s).' in recruitment_status[0].content['comment']['value']
        assert 'No recruitment invitation was sent to the following users because they are already members of the Action Editor group:'

    def test_journal_reviewer_recruitment_by_ae(self, openreview_client, selenium, request_page, helpers, journal):

        #add aes to action editors group
        openreview_client.add_members_to_group(journal['journal_request_note']['content']['venue_id']['value']+ '/Action_Editors', ['ae_journal1@mail.com', 'ae_journal2@mail.com'])

        helpers.create_user('ae_journal1@mail.com', 'First', 'AE')
        ae_client = OpenReviewClient(username='ae_journal1@mail.com', password='1234')

        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(journal['journal_request_note']['id']), ae_client.token, by=By.CLASS_NAME, wait_for_element='reply_row')
        recruitment_div = selenium.find_element_by_id('note_{}'.format(journal['journal_request_note']['id']))
        assert recruitment_div
        reply_row = recruitment_div.find_element_by_class_name('reply_row')
        assert reply_row
        buttons = reply_row.find_elements_by_class_name('btn-xs')
        assert [btn for btn in buttons if btn.text == 'Reviewer Recruitment by AE']

        recruitment_note = ae_client.post_note_edit(
            invitation = '{}/Journal_Request{}/-/Reviewer_Recruitment_by_AE'.format(journal['suppot_group_id'],journal['journal_request_note']['number']),
            signatures = ['~First_AE1'],
            note = Note(
                content = {
                    'invitee_name': { 'value': 'New Reviewer'},
                    'invitee_email': { 'value': 'new_reviewer@mail.com'},
                    'email_subject': { 'value': '[' + journal['journal_request_note']['content']['abbreviated_venue_name']['value'] + '] Invitation to act as Reviewer for ' + journal['journal_request_note']['content']['abbreviated_venue_name']['value']},
                    'email_content': {'value': 'Dear {name},\n\nYou have been nominated to serve as reviewer for TJ22 by {inviter}.\n\nACCEPT LINK:\n{accept_url}\n\nDECLINE LINK:\n{decline_url}\n\nCheers!\n{inviter}'}
                },
                forum = journal['journal_request_note']['forum'],
                replyto = journal['journal_request_note']['forum'],
                signatures = ['~First_AE1']
            ))
        assert recruitment_note

        helpers.await_queue(openreview_client)
        process_logs = openreview_client.get_process_logs(id = recruitment_note['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/Journal_Request{}/-/Reviewer_Recruitment_by_AE'.format(journal['suppot_group_id'],journal['journal_request_note']['number'])

        messages = openreview_client.get_messages(to = 'new_reviewer@mail.com', subject = '[TJ22] Invitation to act as Reviewer for TJ22')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('<p>Dear New Reviewer,</p>\n<p>You have been nominated to serve as reviewer for TJ22 by First AE.</p>')
        assert messages[0]['content']['replyTo'] == 'ae_journal1@mail.com'

        inv = '{}/Journal_Request{}/-/Comment'.format(journal['suppot_group_id'],journal['journal_request_note']['number'])
        recruitment_status = ae_client.get_notes(invitation=inv, replyto=recruitment_note['note']['id'])

        assert recruitment_status
        assert recruitment_status[0].content['title']['value'] == 'Recruitment Status'
        assert 'Invited: 1 reviewer' in recruitment_status[0].content['comment']['value']

        helpers.create_user('ae_journal2@mail.com', 'Second', 'AE')
        ae2_client = OpenReviewClient(username='ae_journal2@mail.com', password='1234')

        #re-invite reviewer by another AE
        recruitment_note = ae2_client.post_note_edit(
            invitation = '{}/Journal_Request{}/-/Reviewer_Recruitment_by_AE'.format(journal['suppot_group_id'],journal['journal_request_note']['number']),
            signatures = ['~Second_AE1'],
            note = Note(
                content = {
                    'invitee_name': { 'value': 'New Reviewer'},
                    'invitee_email': { 'value': 'new_reviewer@mail.com'},
                    'email_subject': { 'value': '[' + journal['journal_request_note']['content']['abbreviated_venue_name']['value'] + '] Invitation to act as Reviewer for ' + journal['journal_request_note']['content']['abbreviated_venue_name']['value']},
                    'email_content': {'value': 'Dear {name},\n\nYou have been nominated to serve as reviewer for TJ22 by {inviter}.\n\nACCEPT LINK:\n{accept_url}\n\nDECLINE LINK:\n{decline_url}\n\nCheers!\n{inviter}'}
                },
                forum = journal['journal_request_note']['forum'],
                replyto = journal['journal_request_note']['forum'],
                signatures = ['~Second_AE1']
            ))
        assert recruitment_note

        helpers.await_queue(openreview_client)
        process_logs = openreview_client.get_process_logs(id = recruitment_note['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/Journal_Request{}/-/Reviewer_Recruitment_by_AE'.format(journal['suppot_group_id'],journal['journal_request_note']['number'])

        messages = openreview_client.get_messages(to = 'new_reviewer@mail.com', subject = '[TJ22] Invitation to act as Reviewer for TJ22')
        assert len(messages) == 2
        assert messages[1]['content']['text'].startswith('<p>Dear New Reviewer,</p>\n<p>You have been nominated to serve as reviewer for TJ22 by Second AE.</p>')
        assert messages[1]['content']['replyTo'] == 'ae_journal2@mail.com'

        inv = '{}/Journal_Request{}/-/Comment'.format(journal['suppot_group_id'],journal['journal_request_note']['number'])
        recruitment_status = ae2_client.get_notes(invitation=inv, replyto=recruitment_note['note']['id'])

        assert recruitment_status
        assert recruitment_status[0].content['title']['value'] == 'Recruitment Status'
        assert 'Invited: 1 reviewer' in recruitment_status[0].content['comment']['value']

        #decline reviewer invitation
        text = messages[0]['content']['text']
        accept_url = re.search('href="https://.*response=No"', text).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
        request_page(selenium, accept_url, alert=True)

        helpers.await_queue(openreview_client)

        #check recruitment response posted as reply of lastest recruitment note
        recruitment_response = openreview_client.get_notes(invitation=inv, replyto=recruitment_note['note']['id'], sort='tcdate:desc')[0]
        assert recruitment_response
        assert 'The user new_reviewer@mail.com has declined an invitation to be a reviewer for TJ22.' in recruitment_response.content['comment']['value']

        #check email sent only to latest AE to invite this reviewer
        messages = openreview_client.get_messages(subject = 'A new recruitment response has been posted to your journal request: Test Journal 2022')
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'ae_journal2@mail.com'
        assert 'The user <a href="mailto:new_reviewer@mail.com">new_reviewer@mail.com</a> has declined an invitation to be a reviewer for TJ22.' in messages[0]['content']['text']

        recruitment_note = ae2_client.post_note_edit(
            invitation = '{}/Journal_Request{}/-/Reviewer_Recruitment_by_AE'.format(journal['suppot_group_id'],journal['journal_request_note']['number']),
            signatures = ['~Second_AE1'],
            note = Note(
                content = {
                    'invitee_name': { 'value': 'New Reviewer'},
                    'invitee_email': { 'value': 'new_reviewer@mail.com'},
                    'email_subject': { 'value': '[' + journal['journal_request_note']['content']['abbreviated_venue_name']['value'] + '] Invitation to act as Reviewer for ' + journal['journal_request_note']['content']['abbreviated_venue_name']['value']},
                    'email_content': {'value': 'Dear {name},\n\nYou have been nominated to serve as reviewer for TJ22 by {inviter}.\n\nACCEPT LINK:\n{accept_url}\n\nDECLINE LINK:\n{decline_url}\n\nCheers!\n{inviter}'}
                },
                forum = journal['journal_request_note']['forum'],
                replyto = journal['journal_request_note']['forum'],
                signatures = ['~Second_AE1']
            ))
        assert recruitment_note

        helpers.await_queue(openreview_client)
        process_logs = openreview_client.get_process_logs(id = recruitment_note['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'
        assert process_logs[0]['invitation'] == '{}/Journal_Request{}/-/Reviewer_Recruitment_by_AE'.format(journal['suppot_group_id'],journal['journal_request_note']['number'])

        #check reviewer received another invitation even after declining
        messages = openreview_client.get_messages(to = 'new_reviewer@mail.com', subject = '[TJ22] Invitation to act as Reviewer for TJ22')
        assert len(messages) == 3
        assert messages[2]['content']['text'].startswith('<p>Dear New Reviewer,</p>\n<p>You have been nominated to serve as reviewer for TJ22 by Second AE.</p>')
        assert messages[2]['content']['replyTo'] == 'ae_journal2@mail.com'