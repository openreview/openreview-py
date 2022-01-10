import openreview
import pytest
import time
import json
import datetime
import random
import os
import re
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.journal import Journal

class TestJournal():


    @pytest.fixture(scope="class")
    def journal(self):
        venue_id = '.MELBA'
        support_client=OpenReviewClient(username='adalca@mit.edu', password='1234')
        support_client.impersonate('.MELBA/Editors_In_Chief')
        journal=Journal(support_client, venue_id, '1234', contact_info='editors@melba-journal.org', full_name='The Journal of Machine Learning for Biomedical Imaging', short_name='MELBA', website='melba-journal.org')
        return journal

    def test_setup(self, openreview_client, helpers):

        venue_id = '.MELBA'

        ## Support Role
        helpers.create_user('adalca@mit.edu', 'Adrian', 'Dalca')

        ## Editors in Chief
        helpers.create_user('msabuncu@cornell.edu', 'Mert', 'Sabuncu')

        ## Action Editors
        hoel_client = helpers.create_user('hoel@mail.com', 'Hoel', 'Hervadec')
        aasa_client = helpers.create_user('aasa@mail.com', 'Aasa', 'Feragen')
        xukun_client = helpers.create_user('xukun@mail.com', 'Xukun', 'Liu')
        melisa_client = helpers.create_user('melisa@mail.com', 'Melisa', 'Bok')

        ## Reviewers
        david_client=helpers.create_user('rev1@mailone.com', 'MELBARev', 'One')
        javier_client=helpers.create_user('rev2@mailtwo.com', 'MELBARev', 'Two')
        carlos_client=helpers.create_user('rev3@mailthree.com', 'MELBARev', 'Three')
        andrew_client = helpers.create_user('rev4@mailfour.com', 'MELBARev', 'Four')
        hugo_client = helpers.create_user('rev5@mailfive.com', 'MELBARev', 'Five')

        journal=Journal(openreview_client, venue_id, '1234', contact_info='editors@melba-journal.org', full_name='The Journal of Machine Learning for Biomedical Imaging', short_name='MELBA', website='melba-journal.org')
        journal.setup(support_role='adalca@mit.edu', editors=['~Mert_Sabuncu1'])

    def test_invite_action_editors(self, journal, openreview_client, request_page, selenium, helpers):

        venue_id = '.MELBA'
        journal=Journal(openreview_client, venue_id, '1234', contact_info='editors@melba-journal.org', full_name='The Journal of Machine Learning for Biomedical Imaging', short_name='MELBA', website='melba-journal.org')

        journal.invite_action_editors(message='Test {name},  {accept_url}, {decline_url}', subject='Invitation to be an Action Editor', invitees=['new_user@mail.com', 'hoel@mail.com', '~Xukun_Liu1', 'aasa@mail.com', '~Melisa_Bok1'])
        invited_group = openreview_client.get_group(f'{venue_id}/Action_Editors/Invited')
        assert invited_group.members == ['new_user@mail.com', '~Hoel_Hervadec1', '~Xukun_Liu1', '~Aasa_Feragen1', '~Melisa_Bok1']

        messages = openreview_client.get_messages(subject = 'Invitation to be an Action Editor')
        assert len(messages) == 5

        for message in messages:
            text = message['content']['text']
            accept_url = re.search('href="https://.*response=Yes"', text).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
            request_page(selenium, accept_url, alert=True)

        helpers.await_queue(openreview_client)

        group = openreview_client.get_group(f'{venue_id}/Action_Editors')
        assert len(group.members) == 5
        assert '~Aasa_Feragen1' in group.members

    def test_invite_reviewers(self, journal, openreview_client, request_page, selenium, helpers):

        venue_id = '.MELBA'
        journal=Journal(openreview_client, venue_id, '1234', contact_info='editors@melba-journal.org', full_name='The Journal of Machine Learning for Biomedical Imaging', short_name='MELBA', website='melba-journal.org')

        journal.invite_reviewers(message='Test {name},  {accept_url}, {decline_url}', subject='Invitation to be a Reviewer', invitees=['rev1@mailone.com', 'rev4@mailfour.com', 'rev3@mailthree.com', 'rev2@mailtwo.com', 'rev5@mailfive.com'])
        invited_group = openreview_client.get_group(f'{venue_id}/Reviewers/Invited')
        assert invited_group.members == ['~MELBARev_One1', '~MELBARev_Four1', '~MELBARev_Three1', '~MELBARev_Two1', '~MELBARev_Five1']

        messages = openreview_client.get_messages(subject = 'Invitation to be a Reviewer')
        assert len(messages) == 5

        for message in messages:
            text = message['content']['text']
            accept_url = re.search('href="https://.*response=Yes"', text).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
            request_page(selenium, accept_url, alert=True)

        helpers.await_queue(openreview_client)

        group = openreview_client.get_group(f'{venue_id}/Reviewers/Invited')
        assert len(group.members) == 5
        assert '~MELBARev_One1' in group.members

        status = journal.invite_reviewers(message='Test {name},  {accept_url}, {decline_url}', subject='Invitation to be a Reviewer', invitees=['rev1@mailone.com'])
        messages = openreview_client.get_messages(to = 'rev1@mailone.com', subject = 'Invitation to be a Reviewer')
        assert len(messages) == 1

        assert status.get('already_member')
        assert 'rev1@mailone.com' in status.get('already_member')

    def test_submission(self, journal, openreview_client, test_client, helpers):

        venue_id = journal.venue_id
        test_client = OpenReviewClient(username='test@mail.com', password='1234')

        ## Post the submission 1
        submission_note_1 = test_client.post_note_edit(invitation=f'{venue_id}/-/Author_Submission',
            signatures=['~SomeFirstName_User1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Test User', 'Celeste Martinez']},
                    'authorids': { 'value': ['~SomeFirstName_User1', 'celeste@mail.com']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'competing_interests': { 'value': 'None beyond the authors normal conflict of interests'},
                    'human_subjects_reporting': { 'value': 'Not applicable'}
                }
            ))

        helpers.await_queue(openreview_client)
        note_id_1=submission_note_1['note']['id']
        process_logs = openreview_client.get_process_logs(id = submission_note_1['id'])
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        messages = journal.client.get_messages(to = 'test@mail.com', subject = '[MELBA] Suggest candidate Action Editor for your new MELBA submission')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == '''<p>Hi SomeFirstName User,</p>
<p>Thank you for submitting your work titled &quot;Paper title&quot; to MELBA.</p>
<p>Before the review process starts, you need to submit one or more recommendations for an Action Editor that you believe has the expertise to oversee the evaluation of your work.</p>
<p>To do so, please follow this link: <a href=\"https://openreview.net/invitation?id=.MELBA/Paper1/Action_Editors/-/Recommendation\">https://openreview.net/invitation?id=.MELBA/Paper1/Action_Editors/-/Recommendation</a> or check your tasks in the Author Console: <a href=\"https://openreview.net/group?id=.MELBA/Authors\">https://openreview.net/group?id=.MELBA/Authors</a></p>
<p>For more details and guidelines on the MELBA review process, visit <a href=\"http://melba-journal.org\">melba-journal.org</a>.</p>
<p>The MELBA Editors-in-Chief</p>
'''