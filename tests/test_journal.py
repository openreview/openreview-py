import openreview
import pytest
import time
import json
import datetime
import random
import os
import re

class TestJournal():


    @pytest.fixture(scope="class")
    def journal(self):
        venue_id = '.TMLR'
        fabian_client=openreview.Client(username='fabian@mail.com', password='1234')
        journal=openreview.journal.Journal(fabian_client, venue_id, '1234')
        return journal

    def test_setup(self, client, helpers):

        venue_id = '.TMLR'

        ## Support Role
        helpers.create_user('fabian@mail.com', 'Fabian', 'Pedregosa')

        ## Editors in Chief
        helpers.create_user('raia@mail.com', 'Raia', 'Hadsell')
        helpers.create_user('kyunghyun@mail.com', 'Kyunghyun', 'Cho')

        ## Action Editors
        helpers.create_user('joelle@mail.com', 'Joelle', 'Pineau')
        ryan_client = helpers.create_user('yan@mail.com', 'Ryan', 'Adams')
        samy_client = helpers.create_user('samy@mail.com', 'Samy', 'Bengio')
        yoshua_client = helpers.create_user('yoshua@mail.com', 'Yoshua', 'Bengio')
        corinna_client = helpers.create_user('corinna@mail.com', 'Corinna', 'Cortes')
        ivan_client = helpers.create_user('ivan@mail.com', 'Ivan', 'Titov')
        shakir_client = helpers.create_user('shakir@mail.com', 'Shakir', 'Mohamed')
        silvia_client = helpers.create_user('silvia@mail.com', 'Silvia', 'Villa')

        ## Reviewers
        david_client=helpers.create_user('david@mail.com', 'David', 'Belanger')
        javier_client=helpers.create_user('javier@mail.com', 'Javier', 'Burroni')
        carlos_client=helpers.create_user('carlos@mail.com', 'Carlos', 'Mondragon')
        andrew_client = helpers.create_user('andrewmc@mail.com', 'Andrew', 'McCallum')
        hugo_client = helpers.create_user('hugo@mail.com', 'Hugo', 'Larochelle')

        journal=openreview.journal.Journal(client, venue_id, '1234')
        journal.setup(support_role='fabian@mail.com', editors=['~Raia_Hadsell1', '~Kyunghyun_Cho1'])

    def test_invite_action_editors(self, journal, client, request_page, selenium, helpers):

        res=journal.invite_action_editors(message='Test {name},  {accept_url}, {decline_url}', subject='Invitation to be an Action Editor', invitees=['user@mail.com', 'joelle@mail.com', '~Ryan_Adams1', '~Samy_Bengio1', '~Yoshua_Bengio1', '~Corinna_Cortes1', '~Ivan_Titov1', '~Shakir_Mohamed1', '~Silvia_Villa1'])
        assert res.id == '.TMLR/Action_Editors/Invited'
        assert res.members == ['user@mail.com', '~Joelle_Pineau1', '~Ryan_Adams1', '~Samy_Bengio1', '~Yoshua_Bengio1', '~Corinna_Cortes1', '~Ivan_Titov1', '~Shakir_Mohamed1', '~Silvia_Villa1']

        messages = client.get_messages(subject = 'Invitation to be an Action Editor')
        assert len(messages) == 9

        messages = client.get_messages(subject = 'Invitation to be an Action Editor', to='joelle@mail.com')
        assert len(messages) == 1
        text = messages[0]['content']['text']
        accept_url = re.search('href="https://.*response=Yes"', text).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
        request_page(selenium, accept_url, alert=True)

        helpers.await_queue()

        group = client.get_group('.TMLR/Action_Editors')
        assert len(group.members) == 1
        assert '~Joelle_Pineau1' in group.members

    def test_invite_reviewers(self, journal, client, request_page, selenium, helpers):

        res=journal.invite_reviewers(message='Test {name},  {accept_url}, {decline_url}', subject='Invitation to be a Reviewer', invitees=['zach@mail.com', '~David_Belanger1', 'javier@mail.com', '~Carlos_Mondragon1', '~Andrew_McCallum1', '~Hugo_Larochelle1'])
        assert res.id == '.TMLR/Reviewers/Invited'
        assert res.members == ['zach@mail.com', '~David_Belanger1', '~Javier_Burroni1', '~Carlos_Mondragon1', '~Andrew_McCallum1', '~Hugo_Larochelle1']

        messages = client.get_messages(subject = 'Invitation to be a Reviewer')
        assert len(messages) == 6

        for message in messages:
            text = message['content']['text']
            accept_url = re.search('href="https://.*response=Yes"', text).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')
            request_page(selenium, accept_url, alert=True)
            helpers.await_queue()

        group = client.get_group('.TMLR/Reviewers')
        assert len(group.members) == 6
        assert '~Javier_Burroni1' in group.members

