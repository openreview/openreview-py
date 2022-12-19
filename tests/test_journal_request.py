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
    def journal(self, openreview_client):

        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'venue_id': 'TJ22' })

        return JournalRequest.get_journal(openreview_client, requests[0].id)

    @pytest.fixture(scope='class')
    def journal_number(self, openreview_client):

        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Journal_Request', content={ 'venue_id': 'TJ22' })

        return requests[0].number

    def test_journal_setup(self, openreview_client, helpers, journal_request):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        assert journal_request.support_group.id == support_group_id
        journal_request_invitation = openreview_client.get_invitation(id = support_group_id + '/-/Journal_Request')
        assert journal_request_invitation

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

        helpers.await_queue_edit(openreview_client, request_form['id'])        

    def test_journal_deployment(self, openreview_client, test_client, selenium, request_page, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

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

        helpers.await_queue_edit(openreview_client, request_form['id'])
        request_page(selenium, 'http://localhost:3030/forum?id=' + request_form['note']['id'], openreview_client.token)

        helpers.create_user('support_role@mail.com', 'Support', 'Role')
        test_client = OpenReviewClient(username='support_role@mail.com', password='1234')

        request_page(selenium, 'http://localhost:3030/forum?id=' + request_form['note']['id'], openreview_client.token, by=By.CLASS_NAME, wait_for_element='invitations-container')
        invitations_container = selenium.find_element_by_class_name('invitations-container')
        invitation_buttons = invitations_container.find_element_by_class_name('invitation-buttons')
        buttons = invitation_buttons.find_elements_by_tag_name('button')
        assert len(buttons) ==  4
        assert [btn for btn in buttons if btn.text == 'Comment']

        #check request form id is added to AE console
        AE_group = openreview_client.get_group('{}/Action_Editors'.format(request_form['note']['content']['venue_id']['value']))
        assert "var JOURNAL_REQUEST_ID = '{}';".format(request_form['note']['id']) in AE_group.web

    def test_journal_reviewer_recruitment(self, openreview_client, selenium, request_page, helpers, journal_request, journal, journal_number):

        rev_template = '''Hi {{fullname}},

Greetings! You have been nominated by the program chair committee of TJ22 to serve as reviewer.

ACCEPT LINK:
{{accept_url}}

DECLINE LINK:
{{decline_url}}

Cheers!
TJ22 Editors-in-Chief
'''
        journal_request.setup_recruitment_invitations(journal.request_form_id, reviewer_template=rev_template)

        test_client = OpenReviewClient(username='support_role@mail.com', password='1234')

        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(journal.request_form_id), test_client.token, by=By.CLASS_NAME, wait_for_element='invitations-container')
        invitations_container = selenium.find_element_by_class_name('invitations-container')
        invitation_buttons = invitations_container.find_element_by_class_name('invitation-buttons')
        buttons = invitation_buttons.find_elements_by_tag_name('button')
        assert len(buttons) ==  3

        assert [btn for btn in buttons if btn.text == 'Reviewer Recruitment']

        invitation = test_client.get_invitation(id=f'openreview.net/Support/Journal_Request{journal_number}/-/Reviewer_Recruitment')
        assert 'Hi {{fullname}},\n\nGreetings! You have been nominated by the program chair committee of TJ22' in invitation.edit['note']['content']['email_content']['value']['param']['default']

        helpers.create_user('reviewer_journal2@mail.com', 'Second', 'Reviewer')

        #add reviewer to invited group
        openreview_client.add_members_to_group('TJ22/Reviewers/Invited', 'reviewer_journal3@mail.com')

        reviewer_details = { 'value': '''reviewer_journal1@mail.com, First Reviewer\n~Second_Reviewer1\nreviewer_journal3@mail.com'''}
        recruitment_note = test_client.post_note_edit(
            invitation = f'openreview.net/Support/Journal_Request{journal_number}/-/Reviewer_Recruitment',
            signatures = ['~Support_Role1'],
            note = Note(
                content = {
                    'title': { 'value': 'Recruitment' },
                    'invitee_details': reviewer_details,
                    'email_subject': { 'value': '[TJ22] Invitation to serve as Reviewer for TJ22'},
                    'email_content': {'value': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of TJ22 to serve as reviewer.\n\nACCEPT LINK:\n{{accept_url}}\n\nDECLINE LINK:\n{{decline_url}}\n\nCheers!'}
                },
                forum = journal.request_form_id,
                replyto = journal.request_form_id,
                signatures = ['~Support_Role1']
            ))
        assert recruitment_note

        helpers.await_queue_edit(openreview_client, recruitment_note['id'])

        invited_group = openreview_client.get_group('TJ22/Reviewers/Invited')
        assert invited_group
        assert len(invited_group.members) == 3
        assert 'reviewer_journal1@mail.com' in invited_group.members
        assert '~Second_Reviewer1' in invited_group.members
        assert 'reviewer_journal3@mail.com' in invited_group.members

        messages = openreview_client.get_messages(to = 'reviewer_journal1@mail.com', subject = '[TJ22] Invitation to serve as Reviewer for TJ22')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('Dear First Reviewer,\n\nYou have been nominated by the program chair committee of TJ22 to serve as reviewer.')

        messages = openreview_client.get_messages(to = 'reviewer_journal2@mail.com', subject = '[TJ22] Invitation to serve as Reviewer for TJ22')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('Dear Second Reviewer,\n\nYou have been nominated by the program chair committee of TJ22 to serve as reviewer.')

        messages = openreview_client.get_messages(to = 'reviewer_journal3@mail.com')
        assert not messages

        inv = f'openreview.net/Support/Journal_Request{journal_number}/-/Comment'
        recruitment_status = openreview_client.get_notes(invitation=inv, replyto=recruitment_note['note']['id'])

        assert recruitment_status
        assert recruitment_status[0].content['title']['value'] == 'Recruitment Status'
        assert 'Invited: 2 Reviewer(s).' in recruitment_status[0].content['comment']['value']

    def test_journal_action_editor_recruitment(self, openreview_client, selenium, request_page, helpers, journal, journal_number):

        test_client = OpenReviewClient(username='support_role@mail.com', password='1234')

        invitation = test_client.get_invitation(id=f'openreview.net/Support/Journal_Request{journal_number}/-/Action_Editor_Recruitment')
        assert 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of TJ22' in invitation.edit['note']['content']['email_content']['value']['param']['default']

        #add ae to invited group
        openreview_client.add_members_to_group('TJ22/Action_Editors/Invited', 'ae_journal1@mail.com')

        #add ae to action editors group
        openreview_client.add_members_to_group('TJ22/Action_Editors', 'already_actioneditor@mail.com')

        ae_details = { 'value': '''ae_journal1@mail.com, First AE\nae_journal2@mail.com, Second AE\nae_journal3@mail.com, Third AE\nalready_actioneditor@mail.com, Action Editor\nnewactioneditor@mail.com;, New AE'''}
        recruitment_note = test_client.post_note_edit(
            invitation = f'openreview.net/Support/Journal_Request{journal_number}/-/Action_Editor_Recruitment',
            signatures = ['~Support_Role1'],
            note = Note(
                content = {
                    'title': { 'value': 'Recruitment' },
                    'invitee_details': ae_details,
                    'email_subject': { 'value': '[TJ22] Invitation to serve as {{role}} for TJ22' },
                    'email_content': {'value': 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of TJ22 to serve as action editor.\n\nACCEPT LINK:\n{{accept_url}}\n\nDECLINE LINK:\n{{decline_url}}\n\nCheers!'}
                },
                forum = journal.request_form_id,
                replyto = journal.request_form_id,
                signatures = ['~Support_Role1']
            ))
        assert recruitment_note

        helpers.await_queue_edit(openreview_client, recruitment_note['id'])

        messages = openreview_client.get_messages(to = 'ae_journal1@mail.com')
        assert len(messages) == 0

        messages = openreview_client.get_messages(to = 'already_actioneditor@mail.com')
        assert len(messages) == 0

        messages = openreview_client.get_messages(to = 'ae_journal2@mail.com', subject = '[TJ22] Invitation to serve as Action Editor for TJ22')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('Dear Second AE,\n\nYou have been nominated by the program chair committee of TJ22 to serve as action editor.')

        messages = openreview_client.get_messages(to = 'ae_journal3@mail.com', subject = '[TJ22] Invitation to serve as Action Editor for TJ22')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('Dear Third AE,\n\nYou have been nominated by the program chair committee of TJ22 to serve as action editor.')

        inv = f'openreview.net/Support/Journal_Request{journal_number}/-/Comment'
        recruitment_status = openreview_client.get_notes(invitation=inv, replyto=recruitment_note['note']['id'])

        assert recruitment_status
        assert recruitment_status[0].content['title']['value'] == 'Recruitment Status'
        assert 'Invited: 2 Action Editor(s).' in recruitment_status[0].content['comment']['value']
        assert 'No recruitment invitation was sent to the following users because they are already members of the Action Editor group:'
        assert "'name': 'NotFoundError', 'message': 'Group Not Found: newactioneditor@mail.com;'"

    def test_journal_reviewer_recruitment_by_ae(self, openreview_client, selenium, request_page, helpers, journal, journal_number):

        #add aes to action editors group
        openreview_client.add_members_to_group('TJ22/Action_Editors', ['ae_journal1@mail.com', 'ae_journal2@mail.com'])

        helpers.create_user('ae_journal1@mail.com', 'First', 'AE')
        ae_client = OpenReviewClient(username='ae_journal1@mail.com', password='1234')

        request_page(selenium, 'http://localhost:3030/forum?id={}'.format(journal.request_form_id), ae_client.token, by=By.CLASS_NAME, wait_for_element='invitations-container')
        invitations_container = selenium.find_element_by_class_name('invitations-container')
        invitation_buttons = invitations_container.find_element_by_class_name('invitation-buttons')
        buttons = invitation_buttons.find_elements_by_tag_name('button')
        assert len(buttons) == 1
        assert [btn for btn in buttons if btn.text == 'Reviewer Recruitment by AE']

        recruitment_note = ae_client.post_note_edit(
            invitation = f'openreview.net/Support/Journal_Request{journal_number}/-/Reviewer_Recruitment_by_AE',
            signatures = ['~First_AE1'],
            note = Note(
                content = {
                    'invitee_name': { 'value': 'New Reviewer'},
                    'invitee_email': { 'value': 'new_reviewer@mail.com'},
                    'email_subject': { 'value': '[TJ22] Invitation to act as Reviewer for TJ22'},
                    'email_content': {'value': 'Dear {{fullname}},\n\nYou have been nominated to serve as reviewer for TJ22 by {{inviter}}.\n\nACCEPT LINK:\n{{accept_url}}\n\nDECLINE LINK:\n{{decline_url}}\n\nCheers!\n{{inviter}}'}
                },
                forum = journal.request_form_id,
                replyto = journal.request_form_id,
                signatures = ['~First_AE1']
            ))
        helpers.await_queue_edit(openreview_client, recruitment_note['id'])

        recruitment_note = openreview_client.get_note(recruitment_note['note']['id'])
        assert recruitment_note.readers == ['openreview.net/Support', 'TJ22', '~First_AE1']

        messages = openreview_client.get_messages(to = 'new_reviewer@mail.com', subject = '[TJ22] Invitation to act as Reviewer for TJ22')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('Dear New Reviewer,\n\nYou have been nominated to serve as reviewer for TJ22 by First AE.')
        assert messages[0]['content']['replyTo'] == 'ae_journal1@mail.com'

        inv = f'openreview.net/Support/Journal_Request{journal_number}/-/Comment'
        recruitment_status = ae_client.get_notes(invitation=inv, replyto=recruitment_note.id)

        assert recruitment_status
        assert recruitment_status[0].content['title']['value'] == 'Recruitment Status'
        assert 'Invited: 1 reviewer' in recruitment_status[0].content['comment']['value']
        assert recruitment_status[0].readers == ['openreview.net/Support', 'TJ22', '~First_AE1']

        # catch group not found error
        recruitment_note = ae_client.post_note_edit(
            invitation = f'openreview.net/Support/Journal_Request{journal_number}/-/Reviewer_Recruitment_by_AE',
            signatures = ['~First_AE1'],
            note = Note(
                content = {
                    'invitee_name': { 'value': 'New Reviewer'},
                    'invitee_email': { 'value': 'new_reviewer@mail.com;'},
                    'email_subject': { 'value': '[TJ22] Invitation to act as Reviewer for TJ22'},
                    'email_content': {'value': 'Dear {{fullname}},\n\nYou have been nominated to serve as reviewer for TJ22 by {{inviter}}.\n\nACCEPT LINK:\n{{accept_url}}\n\nDECLINE LINK:\n{{decline_url}}\n\nCheers!\n{{inviter}}'}
                },
                forum = journal.request_form_id,
                replyto = journal.request_form_id,
                signatures = ['~First_AE1']
            ))
        helpers.await_queue_edit(openreview_client, recruitment_note['id'])

        recruitment_note = openreview_client.get_note(recruitment_note['note']['id'])
        assert recruitment_note.readers == ['openreview.net/Support', 'TJ22', '~First_AE1']

        inv = f'openreview.net/Support/Journal_Request{journal_number}/-/Comment'
        recruitment_status = ae_client.get_notes(invitation=inv, replyto=recruitment_note.id)

        assert recruitment_status
        assert recruitment_status[0].content['title']['value'] == 'Recruitment Status'
        assert 'Invited: 0 reviewer' in recruitment_status[0].content['comment']['value']
        assert "'name': 'NotFoundError', 'message': 'Group Not Found: new_reviewer@mail.com;'"
        assert recruitment_status[0].readers == ['openreview.net/Support', 'TJ22', '~First_AE1']

        helpers.create_user('ae_journal2@mail.com', 'Second', 'AE')
        ae2_client = OpenReviewClient(username='ae_journal2@mail.com', password='1234')

        #re-invite reviewer by another AE
        recruitment_note = ae2_client.post_note_edit(
            invitation = f'openreview.net/Support/Journal_Request{journal_number}/-/Reviewer_Recruitment_by_AE',
            signatures = ['~Second_AE1'],
            note = Note(
                content = {
                    'invitee_name': { 'value': 'New Reviewer'},
                    'invitee_email': { 'value': 'new_reviewer@mail.com'},
                    'email_subject': { 'value': '[TJ22] Invitation to act as Reviewer for TJ22'},
                    'email_content': {'value': 'Dear {{fullname}},\n\nYou have been nominated to serve as reviewer for TJ22 by {{inviter}}.\n\nACCEPT LINK:\n{{accept_url}}\n\nDECLINE LINK:\n{{decline_url}}\n\nCheers!\n{{inviter}}'}
                },
                forum = journal.request_form_id,
                replyto = journal.request_form_id,
                signatures = ['~Second_AE1']
            ))
        assert recruitment_note

        helpers.await_queue_edit(openreview_client, recruitment_note['id'])

        recruitment_note = openreview_client.get_note(recruitment_note['note']['id'])
        assert recruitment_note.readers == ['openreview.net/Support', 'TJ22', '~Second_AE1']

        messages = openreview_client.get_messages(to = 'new_reviewer@mail.com', subject = '[TJ22] Invitation to act as Reviewer for TJ22')
        assert len(messages) == 2
        assert messages[1]['content']['text'].startswith('Dear New Reviewer,\n\nYou have been nominated to serve as reviewer for TJ22 by Second AE.')
        assert messages[1]['content']['replyTo'] == 'ae_journal2@mail.com'

        inv = f'openreview.net/Support/Journal_Request{journal_number}/-/Comment'
        recruitment_status = ae2_client.get_notes(invitation=inv, replyto=recruitment_note.id)

        assert recruitment_status
        assert recruitment_status[0].content['title']['value'] == 'Recruitment Status'
        assert 'Invited: 1 reviewer' in recruitment_status[0].content['comment']['value']
        assert recruitment_status[0].readers == ['openreview.net/Support', 'TJ22', '~Second_AE1']

        #decline reviewer invitation
        text = messages[0]['content']['text']
        decline_url = re.search('https://.*response=No', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
        request_page(selenium, decline_url, alert=True)

        recruitment_response = openreview_client.get_notes(invitation = 'TJ22/Reviewers/-/Recruitment', content={ 'user': 'new_reviewer@mail.com'}, sort='tcdate:desc')[0]
        helpers.await_queue_edit(openreview_client, edit_id = openreview_client.get_note_edits(note_id=recruitment_response.id)[0].id)

        #check recruitment response posted as reply of lastest recruitment note
        # recruitment_response = openreview_client.get_notes(invitation=inv, replyto=recruitment_note['note']['id'], sort='tcdate:desc')[0]
        # assert recruitment_response
        # assert 'The user new_reviewer@mail.com has declined an invitation to be a reviewer for TJ22.' in recruitment_response.content['comment']['value']

        #check email sent only to latest AE to invite this reviewer
        messages = openreview_client.get_messages(subject = 'A new recruitment response has been posted to your journal request: Test Journal 2022')
        assert len(messages) == 1
        assert messages[0]['content']['to'] == 'ae_journal2@mail.com'
        assert 'The user new_reviewer@mail.com has declined an invitation to be a reviewer for TJ22.' in messages[0]['content']['text']

        recruitment_note = ae2_client.post_note_edit(
            invitation = f'openreview.net/Support/Journal_Request{journal_number}/-/Reviewer_Recruitment_by_AE',
            signatures = ['~Second_AE1'],
            note = Note(
                content = {
                    'invitee_name': { 'value': 'New Reviewer'},
                    'invitee_email': { 'value': 'new_reviewer@mail.com'},
                    'email_subject': { 'value': '[TJ22] Invitation to act as Reviewer for TJ22'},
                    'email_content': {'value': 'Dear {{fullname}},\n\nYou have been nominated to serve as reviewer for TJ22 by {{inviter}}.\n\nACCEPT LINK:\n{{accept_url}}\n\nDECLINE LINK:\n{{decline_url}}\n\nCheers!\n{{inviter}}'}
                },
                forum = journal.request_form_id,
                replyto = journal.request_form_id,
                signatures = ['~Second_AE1']
            ))
        assert recruitment_note

        helpers.await_queue_edit(openreview_client, recruitment_note['id'])

        #check reviewer received another invitation even after declining
        messages = openreview_client.get_messages(to = 'new_reviewer@mail.com', subject = '[TJ22] Invitation to act as Reviewer for TJ22')
        assert len(messages) == 3
        assert messages[2]['content']['text'].startswith('Dear New Reviewer,\n\nYou have been nominated to serve as reviewer for TJ22 by Second AE.')
        assert messages[2]['content']['replyTo'] == 'ae_journal2@mail.com'

        #accept reviewer invitation
        text = messages[0]['content']['text']
        accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
        request_page(selenium, accept_url, alert=True)

        helpers.await_queue_edit(openreview_client, invitation = 'TJ22/Reviewers/-/Recruitment')

        #check recruitment response posted as reply of lastest recruitment note
        recruitment_response = openreview_client.get_notes(invitation=inv, replyto=recruitment_note['note']['id'], sort='tcdate:desc')
        assert recruitment_response and len(recruitment_response) == 2
        assert recruitment_response[1].content['title']['value'] == 'Recruitment Status'
        assert recruitment_response[0].content['title']['value'] == 'New Recruitment Response'
        assert 'The user new_reviewer@mail.com has accepted an invitation to be a reviewer for TJ22.' in recruitment_response[0].content['comment']['value']

        #check AC was notified
        ae_messages = openreview_client.get_messages(subject = 'A new recruitment response has been posted to your journal request: Test Journal 2022')
        assert len(ae_messages) == 2
        assert ae_messages[1]['content']['to'] == 'ae_journal2@mail.com'
        assert 'The user new_reviewer@mail.com has accepted an invitation to be a reviewer for TJ22.' in ae_messages[1]['content']['text']

        #accept reviewer invitation again
        text = messages[0]['content']['text']
        accept_url = re.search('https://.*response=Yes', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
        request_page(selenium, accept_url, alert=True)

        helpers.await_queue_edit(openreview_client, invitation = 'TJ22/Reviewers/-/Recruitment')

        # #check no new note was posted
        recruitment_response = openreview_client.get_notes(invitation=inv, replyto=recruitment_note['note']['id'], sort='tcdate:desc')
        assert recruitment_response and len(recruitment_response) == 2
        assert recruitment_response[0].content['title']['value'] == 'New Recruitment Response'
        assert recruitment_response[0].readers == ['openreview.net/Support', 'TJ22', '~Second_AE1']
        assert 'The user new_reviewer@mail.com has accepted an invitation to be a reviewer for TJ22.' in recruitment_response[0].content['comment']['value']
        edits = openreview_client.get_note_edits(recruitment_response[0].id)
        assert edits and len(edits) == 1

        #check AC was NOT notified
        ae_messages = openreview_client.get_messages(subject = 'A new recruitment response has been posted to your journal request: Test Journal 2022')
        assert len(ae_messages) == 2

        #decline reviewer invitation
        text = messages[0]['content']['text']
        accept_url = re.search('https://.*response=No', text).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
        request_page(selenium, accept_url, alert=True)

        #check recruitment response was updated
        recruitment_response = openreview_client.get_notes(invitation=inv, replyto=recruitment_note['note']['id'], sort='tcdate:desc')
        assert recruitment_response and len(recruitment_response) == 2
        assert recruitment_response[1].content['title']['value'] == 'Recruitment Status'
        assert recruitment_response[0].content['title']['value'] == 'New Recruitment Response'
        assert recruitment_response[0].readers == ['openreview.net/Support', 'TJ22', '~Second_AE1']
        assert 'The user new_reviewer@mail.com has declined an invitation to be a reviewer for TJ22.' in recruitment_response[0].content['comment']['value']
        references = openreview_client.get_note_edits(recruitment_response[0].id)
        assert references and len(references) == 2

        #check AC was notified
        ae_messages = openreview_client.get_messages(subject = 'A new recruitment response has been posted to your journal request: Test Journal 2022')
        assert len(ae_messages) == 3
        assert ae_messages[2]['content']['to'] == 'ae_journal2@mail.com'
        assert 'The user new_reviewer@mail.com has declined an invitation to be a reviewer for TJ22.' in ae_messages[2]['content']['text']