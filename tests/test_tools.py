import openreview
import pytest
import datetime
import random
import types
import sys
import os

from openreview import OpenReviewException
from openreview.tools import concurrent_requests

class TestTools():
    def test_concurrent_requests(self, client):
        def post_random_group(number):
            return client.post_group(
                openreview.Group(
                    id = f'NewGroup{number}',
                    members = [],
                    signatures = ['~Super_User1'],
                    signatories = ['NewGroup'],
                    readers = ['everyone'],
                    writers =['NewGroup']
                ))

        params = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        results = openreview.tools.concurrent_requests(post_random_group, params)
        assert len(results) == len(params)

        def get_random_group(number):
            return client.get_group(f'NewGroup{number}')

        groups = openreview.tools.concurrent_requests(get_random_group, params)
        assert len(groups) == len(params)

        for number, group in enumerate(groups):
            assert group.id == f'NewGroup{number}'

    def test_add_members_to_group(self, client):
        new_group = client.post_group(
            openreview.Group(
                id = 'NewGroup',
                members = [],
                signatures = ['~Super_User1'],
                signatories = ['NewGroup'],
                readers = ['everyone'],
                writers =['NewGroup']
            ))
        assert new_group

        # Test that add_members_to_group works while passing it a Group object and one member of type string
        posted_group = client.add_members_to_group(new_group, 'test_subject_x@mail.com')
        assert posted_group
        assert len(posted_group.members) == 1
        assert 'test_subject_x@mail.com' in posted_group.members

        # Test that add_members_to_group works while passing it a Group object and a list of members each of type string
        posted_group = client.add_members_to_group(posted_group, ['test_subject_y1@mail.com', 'test_subject_y2@mail.com'])
        assert posted_group
        assert len(posted_group.members) == 3
        assert 'test_subject_x@mail.com' in posted_group.members
        assert 'test_subject_y1@mail.com' in posted_group.members
        assert 'test_subject_y2@mail.com' in posted_group.members

        # Test that add_members_to_group works while passing it a Group id string and one member of type string
        posted_group = client.add_members_to_group(posted_group.id, 'test_subject_x2@mail.com')
        assert posted_group
        assert len(posted_group.members) == 4
        assert 'test_subject_x@mail.com' in posted_group.members
        assert 'test_subject_y1@mail.com' in posted_group.members
        assert 'test_subject_y2@mail.com' in posted_group.members
        assert 'test_subject_x2@mail.com' in posted_group.members

        # Test that add_members_to_group works while passing it a Group id string and a list of members each of type string
        posted_group = client.add_members_to_group(posted_group, ['test_subject_y2_1@mail.com', 'test_subject_y2_2@mail.com'])
        assert posted_group
        assert len(posted_group.members) == 6
        assert 'test_subject_x@mail.com' in posted_group.members
        assert 'test_subject_y1@mail.com' in posted_group.members
        assert 'test_subject_y2@mail.com' in posted_group.members
        assert 'test_subject_x2@mail.com' in posted_group.members
        assert 'test_subject_y2_1@mail.com' in posted_group.members
        assert 'test_subject_y2_2@mail.com' in posted_group.members

        # Test that adding an existing member should not have any effect
        posted_group = client.add_members_to_group(posted_group, ['test_subject_y2_1@mail.com', 'test_subject_y2_2@mail.com'])
        assert posted_group
        assert len(posted_group.members) == 6

    def test_remove_members_from_group(self, client):
        new_group = client.post_group(
            openreview.Group(
                id = 'NewGroup',
                members = [],
                signatures = ['~Super_User1'],
                signatories = ['NewGroup'],
                readers = ['everyone'],
                writers =['NewGroup']
            ))
        assert new_group
        assert len(new_group.members) == 0

        posted_group = client.add_members_to_group(new_group.id, ['test_subject_x@mail.com', 'test_subject_y@mail.com', 'test_subject_z@mail.com'])
        assert posted_group
        assert len(posted_group.members) == 3

        # Test that remove_members_from_group works while passing it a Group object and one member of type string
        posted_group = client.remove_members_from_group(posted_group, 'test_subject_x@mail.com')
        assert posted_group
        assert len(posted_group.members) == 2
        assert 'test_subject_x@mail.com' not in posted_group.members

        # Test that remove_members_from_group works while passing it a Group object and and a list of members each of type string
        posted_group = client.remove_members_from_group(posted_group, ['test_subject_x@mail.com', 'test_subject_y@mail.com', 'test_subject_z@mail.com'])
        assert posted_group
        assert len(posted_group.members) == 0

        posted_group = client.add_members_to_group(posted_group.id, ['test_subject_a@mail.com', 'test_subject_b@mail.com', 'test_subject_x@mail.com', 'test_subject_y@mail.com', 'test_subject_z@mail.com'])
        assert posted_group
        assert len(posted_group.members) == 5

        # Test that remove_members_from_group works while passing it a Group id string and one member of type string
        posted_group = client.remove_members_from_group(posted_group.id, 'test_subject_x@mail.com')
        assert posted_group
        assert len(posted_group.members) == 4
        assert 'test_subject_x@mail.com' not in posted_group.members
        assert 'test_subject_a@mail.com' in posted_group.members
        assert 'test_subject_b@mail.com' in posted_group.members
        assert 'test_subject_y@mail.com' in posted_group.members
        assert 'test_subject_z@mail.com' in posted_group.members

        # Test that remove_members_from_group works while passing it a Group id string and a list of members each of type string
        posted_group = client.remove_members_from_group(posted_group.id, ['test_subject_y@mail.com', 'test_subject_z@mail.com'])
        assert posted_group
        assert len(posted_group.members) == 2
        assert 'test_subject_a@mail.com' in posted_group.members
        assert 'test_subject_b@mail.com' in posted_group.members

        # Test that remove_members_from_group does not affect the group if the input member/members are already not in group.members
        posted_group = client.remove_members_from_group(posted_group.id, ['test_subject_y@mail.com', 'test_subject_z@mail.com'])
        assert posted_group
        assert len(posted_group.members) == 2
        assert 'test_subject_a@mail.com' in posted_group.members
        assert 'test_subject_b@mail.com' in posted_group.members

    # def test_get_all_venues(self, client):
    #     venues = openreview.tools.get_all_venues(client)
    #     assert venues, "Venues could not be retrieved"

    def test_iterget_notes(self, client):
        iter_group = client.post_group(
            openreview.Group(
                id = 'IterGroup',
                members = [],
                signatures = ['~Super_User1'],
                signatories = ['IterGroup'],
                readers = ['everyone'],
                writers =['IterGroup']
            ))
        assert iter_group

        invitation = openreview.Invitation(
            id = 'IterGroup/-/Submission',
            readers = ['everyone'],
            writers = ['~Super_User1'],
            signatures = ['~Super_User1'],
            invitees = ['everyone'],
            reply = {
                'readers': { 'values': ['everyone'] },
                'writers': { 'values': ['~Super_User1'] },
                'signatures': {'values-regex': '~.*'},
                'content': {
                    'title': { 'value-regex': '.*' }
                }
            }
        )
        client.post_invitation(invitation)

        note = openreview.Note(
            invitation = 'IterGroup/-/Submission',
            readers = ['everyone'],
            writers = ['~Super_User1'],
            signatures = ['~Super_User1'],
            content = {
                'title': 'Test Note'
            }
        )
        note = client.post_note(note)

        notes_iterator = openreview.tools.iterget_notes(client, invitation='IterGroup/-/Submission')
        assert notes_iterator

    def test_get_all_notes(self, client):
        get_all_group = client.post_group(
            openreview.Group(
                id = 'GetAllNotes',
                members = [],
                signatures = ['~Super_User1'],
                signatories = ['GetAllNotes'],
                readers = ['everyone'],
                writers =['GetAllNotes']
            ))
        assert get_all_group

        invitation = openreview.Invitation(
            id = 'GetAllNotes/-/Submission',
            readers = ['everyone'],
            writers = ['~Super_User1'],
            signatures = ['~Super_User1'],
            invitees = ['everyone'],
            reply = {
                'readers': { 'values': ['everyone'] },
                'writers': { 'values': ['~Super_User1'] },
                'signatures': {'values-regex': '~.*'},
                'content': {
                    'title': { 'value-regex': '.*' }
                }
            }
        )
        client.post_invitation(invitation)

        def post_note(number):
            note = openreview.Note(
                invitation = 'GetAllNotes/-/Submission',
                readers = ['everyone'],
                writers = ['~Super_User1'],
                signatures = ['~Super_User1'],
                content = {
                    'title': 'Test Note ' + str(number)
                }
            )
            note = client.post_note(note)

        num_array = range(1, 1334)
        openreview.tools.concurrent_requests(post_note, num_array)

        notes = client.get_all_notes(invitation='GetAllNotes/-/Submission')
        assert notes
        assert len(notes) == 1333

    def test_get_all_refs(self, client):
        refs_iterator = openreview.tools.iterget_references(client, invitation='GetAllNotes/-/Submission')
        assert refs_iterator

    def test_get_all_tags(self, client):
        tag_iterator = openreview.tools.iterget_tags(client)
        assert tag_iterator

    def test_get_all_invitations(self, client):
        invitations_iterator = openreview.tools.iterget_invitations(client)
        assert invitations_iterator

    def test_get_all_groups(self, client):
        group_iterator = openreview.tools.iterget_groups(client, id='~')
        assert group_iterator

    def test_get_grouped_edges(self, client):
        group_iterator = openreview.tools.iterget_grouped_edges(client)
        assert group_iterator

    def test_get_preferred_name(self, client, test_client):
        superuser_profile = client.get_profile('test@mail.com')
        preferred_name = openreview.tools.get_preferred_name(superuser_profile)
        assert preferred_name, "preferred name not found"
        assert preferred_name == 'SomeFirstName User'

    def test_create_authorid_profiles(self, client):
        authors = [
            'Ada Lovelace',
            'Alan Turing',
            'Edsger W. Dijkstra',
            'Grace Hopper'
        ]

        authorids = [
            'ada@lovelacemanor.org',
            'turing@princeton.edu',
            'ed.dijkstra@uva.nl',
            'ghopper@yale.edu'
        ]

        note = openreview.Note.from_json({
            'id': 'MOCK_NOTE',
            'content': {
                'authors': authors,
                'authorids': authorids
            }
        })

        openreview.tools.create_authorid_profiles(client, note)

        for author, email in zip(authors, authorids):
            result = client.search_profiles(term=author)
            assert any([email in p.content['emails'] for p in result])

    def test_subdomains(self):
        # ensure that two part top-level domains are handled appropriately
        # e.g. "edu.cn", "ac.uk"
        assert openreview.tools.subdomains('mails.tsinghua.edu.cn') == ['mails.tsinghua.edu.cn', 'tsinghua.edu']
        assert openreview.tools.subdomains('robots.ox.ac.uk') == ['oxford.ac.uk', 'robots.ox.ac.uk']
        assert openreview.tools.subdomains('eng.ox.ac.uk') == ['eng.ox.ac.uk', 'oxford.ac.uk']
        assert openreview.tools.subdomains('ground.ai') == ['ground.ai']
        assert openreview.tools.subdomains('cs.umass.edu') == ['cs.umass.edu', 'umass.edu']
        assert openreview.tools.subdomains('   ') == []

    def test_replace_members_with_ids(self, client, test_client):
        test_client.post_profile(openreview.Profile(
            referent='~SomeFirstName_User1',
            signatures = ['~SomeFirstName_User1'],
            content={
                'names': [
                    {
                    'first': 'Another',
                    'last': 'Name'
                    }
                ],
                'emails': ['alternate@mail.com']
            }
        ))

        profile = client.get_profile('~SomeFirstName_User1')
        assert len(profile.content['names']) == 2
        assert profile.content['names'][1]['first'] == 'Another'
        assert profile.content['names'][1]['last'] == 'Name'
        assert profile.content['names'][1]['username'] == '~Another_Name1'

        posted_group = client.post_group(openreview.Group(id='test.org',
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            signatories=['~Super_User1'],
            members=['test@mail.com', '~SomeFirstName_User1', '~Another_Name1', 'NewGroup']
        ))
        assert posted_group

        replaced_group = openreview.tools.replace_members_with_ids(client, posted_group)
        assert replaced_group
        assert replaced_group.members == ['~SomeFirstName_User1', 'NewGroup']

        posted_group = client.post_group(openreview.Group(id='test.org',
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            signatories=['~Super_User1'],
            members=['~Super_User1', '~Another_Name1', 'noprofile@mail.com']
        ))
        replaced_group = openreview.tools.replace_members_with_ids(client, posted_group)
        assert replaced_group
        assert replaced_group.members == ['~Super_User1', '~SomeFirstName_User1', 'noprofile@mail.com']

        # Test to assert that an exception is raised while running replace members on a group has a member that is an invalid profile
        invalid_member_group = client.add_members_to_group(replaced_group, '~Invalid_Profile1')
        assert len(invalid_member_group.members) == 4
        assert '~Invalid_Profile1' in invalid_member_group.members

        with pytest.raises(OpenReviewException) as ex:
            replaced_group = openreview.tools.replace_members_with_ids(client, invalid_member_group)

        assert 'Profile Not Found' in ex.value.args[0]

        ## Replace emails with only profile with confirmed emails
        posted_group = client.post_group(openreview.Group(id='test.org',
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            signatories=['~Super_User1'],
            members=['~Super_User1', 'alternate@mail.com', 'noprofile@mail.com']
        ))
        replaced_group = openreview.tools.replace_members_with_ids(client, posted_group)
        assert replaced_group
        assert replaced_group.members == ['~Super_User1', 'alternate@mail.com', 'noprofile@mail.com']

    def test_get_profile_info(self, client, helpers):

        profile1 = openreview.Profile(
            id = '~Test_Conflict1',
            content = {
                'emails': ['user@cmu.edu', 'wrong_email'],
                'history': [{
                    'institution': {
                        'domain': '126.com'
                    }
                }]
            }
        )

        info = openreview.tools.get_profile_info(profile1)
        assert info['emails'] == set(['user@cmu.edu'])
        assert info['domains'] == set(['cmu.edu', '126.com'])
        assert info['id'] == '~Test_Conflict1'
        assert info['relations'] == set([])
        assert info['publications'] == set([])

        profile1 = openreview.Profile(
            id = '~Test_Conflict1',
            content = {
                'emails': ['user@cmu.edu', 'wrong_email'],
                'history': [{
                    'institution': {
                        'domain': '126.com'
                    }
                }],
                'publications': [openreview.Note(
                    id='1234',
                    invitation='',
                    readers=[],
                    writers=[],
                    signatures=[],
                    cdate=999999999999999,
                    content={
                        'year': '12023'
                    }
                )],
            }
        )

        info = openreview.tools.get_profile_info(profile1)
        assert info['emails'] == set(['user@cmu.edu'])
        assert info['domains'] == set(['cmu.edu', '126.com'])
        assert info['id'] == '~Test_Conflict1'
        assert info['relations'] == set([])
        assert info['publications'] == set([])        

    
    def test_get_conflicts(self, client, helpers):

        helpers.create_user('user@gmail.com', 'First', 'Last')
        user_profile = client.get_profile(email_or_id='user@gmail.com')

        conflicts = openreview.tools.get_conflicts([user_profile], user_profile)
        assert conflicts
        assert conflicts[0] == 'user@gmail.com'

        helpers.create_user('user@qq.com', 'First', 'Last')
        user_profile = client.get_profile(email_or_id='user@qq.com')

        conflicts = openreview.tools.get_conflicts([user_profile], user_profile)
        assert conflicts
        assert conflicts[0] == 'user@qq.com'

        helpers.create_user('user2@qq.com', 'First', 'Last')
        user2_profile = client.get_profile(email_or_id='user2@qq.com')

        conflicts = openreview.tools.get_conflicts([user2_profile], user_profile)
        assert len(conflicts) == 0

        user2_profile.content['relations'] = [{
            'relation': 'Advisor',
            'name': 'First Last',
            'username': '~First_Last2',
            'start': 2015,
            'end': None
        },
        {
            'relation': 'Coauthor',
            'name': 'Some NAme',
            'email': 'test@mail.com',
            'start': 2015,
            'end': None
        }]
        user2_profile.content['dblp'] = 'https://dblp.org/pid/l/Last:First'
        user2_profile.content['history'] = [{
            'position': 'Professor',
            'institution': {
                'domain': 'cmu.edu'
            },
            'start': 2015,
            'end': None
        }]
        user2_profile = client.post_profile(user2_profile)

        conflicts = openreview.tools.get_conflicts([user2_profile], user_profile)
        
        assert len(conflicts) == 1
        assert conflicts[0] == '~First_Last2'

        conflicts = openreview.tools.get_conflicts([user_profile], user2_profile)

        assert len(conflicts) == 1
        assert conflicts[0] == '~First_Last2'

        test_profile = openreview.tools.get_profiles(client, ['test@mail.com'], with_relations=True)[0]
        user_profiles = openreview.tools.get_profiles(client, ['user2@qq.com'], with_relations=True)
        conflicts = openreview.tools.get_conflicts(user_profiles, test_profile, policy='NeurIPS', n_years=5)

        assert len(conflicts) == 1
        assert conflicts[0] == '~SomeFirstName_User1'

        guest_client = openreview.Client()
        user_profile = guest_client.get_profile(email_or_id='user@qq.com')
        user2_profile = guest_client.get_profile(email_or_id='user2@qq.com')

        with pytest.raises(OpenReviewException) as error:
            openreview.tools.get_conflicts([user2_profile], user_profile)
        assert "You do not have the required permissions as some emails are obfuscated" in error.value.args[0]

        profile1 = openreview.Profile(
            id = '~Test_Conflict1',
            content = {
                'emails': ['user@cmu.edu'],
                'history': [{
                    'institution': {
                        'domain': '126.com'
                    }
                }]
            }
        )

        profile2 = openreview.Profile(
            id = '~Test_Conflict2',
            content = {
                'emails': ['user2@126.com', 'wrong_email'],
                'history': [
                    {
                        'institution': {
                            'domain': 'cmu.edu'
                        }
                    },
                    {
                        'institution': {
                            'domain': 'umass.edu'
                        }
                    }
                ]
            }
        )

        intern_profile = openreview.Profile(
            id='~Test_Conflict3',
            content={
                'emails': ['user3@345.com', 'wrong_email'],
                'history': [{
                    'position': 'Intern',
                    'institution': {
                        'domain': 'umass.edu'
                    }
                },
                {
                    'position': None,
                    'institution': {
                        'domain': 'cmu.edu'
                    }
                }
                ]
            }
        )

        conflicts = openreview.tools.get_conflicts([profile1, intern_profile], profile2)
        assert len(conflicts) == 2
        assert 'cmu.edu' in conflicts
        assert 'umass.edu' in conflicts

        neurips_conflicts = openreview.tools.get_conflicts([intern_profile], profile2, policy='NeurIPS')
        assert len(neurips_conflicts) == 1
        assert 'cmu.edu' in conflicts

        conflicts = openreview.tools.get_conflicts([profile1, intern_profile], profile2, policy=openreview.tools.get_profile_info)
        assert len(conflicts) == 2
        assert 'cmu.edu' in conflicts
        assert 'umass.edu' in conflicts

        neurips_conflicts = openreview.tools.get_conflicts([intern_profile], profile2, policy=openreview.tools.get_neurips_profile_info)
        assert len(neurips_conflicts) == 1
        assert 'cmu.edu' in conflicts

        def cmu_is_a_never_conflict(profile, n_years=None):
            domains = set()
            emails = set()
            relations = set()
            publications = set()

            ## Emails section
            for email in profile.content['emails']:
                # split email
                domain = email.split('@')[1]
                if domain != 'cmu.edu':
                    domains.add(domain)
                    emails.add(email)

            ## Institution section
            for history in profile.content.get('history', []):
                try:
                    end = int(history.get('end', 0) or 0)
                except:
                    end = 0
                if not end:
                    domain = history.get('institution', {}).get('domain', '')
                    if domain != 'cmu.edu':
                        domains.add(domain)

            return {
                'id': profile.id,
                'domains': domains,
                'emails': emails,
                'relations': relations,
                'publications': publications
            }
        
        with pytest.raises(Exception) as error:
            conflicts = openreview.tools.get_conflicts([profile1, intern_profile], profile2, policy=cmu_is_a_never_conflict)
        assert  str(error.value) == 'list index out of range'

        def cmu_is_a_never_conflict_updated(profile, n_years=None):
            domains = set()
            emails = set()
            relations = set()
            publications = set()

            ## Emails section
            for email in profile.content['emails']:
                # split email
                if '@' in email:
                    domain = email.split('@')[1]
                    if domain != 'cmu.edu':
                        domains.add(domain)
                        emails.add(email)
                else:
                    print('Profile with invalid email:', profile.id, email)

            ## Institution section
            for history in profile.content.get('history', []):
                try:
                    end = int(history.get('end', 0) or 0)
                except:
                    end = 0
                if not end:
                    domain = history.get('institution', {}).get('domain', '')
                    if domain != 'cmu.edu':
                        domains.add(domain)

            return {
                'id': profile.id,
                'domains': domains,
                'emails': emails,
                'relations': relations,
                'publications': publications
            }

        conflicts = openreview.tools.get_conflicts([profile1, intern_profile], profile2, policy=cmu_is_a_never_conflict_updated)
        assert len(conflicts) == 1
        assert 'umass.edu' in conflicts

    def test_group(self, client):

        assert openreview.tools.get_group(client, '~Super_User1')
        assert openreview.tools.get_group(client, '~Super_User2') == None

        guest_client = openreview.Client()

        with pytest.raises(openreview.OpenReviewException) as openReviewError:
            openreview.tools.get_group(guest_client, '~Super_User1')
        assert openReviewError.value.args[0].get('name') == 'ForbiddenError'

    def test_get_profiles_as_dict(self, client, test_client):
        client.add_members_to_group(client.get_group('~SomeFirstName_User1'), 'alternate@mail.com')
        client.add_members_to_group(client.get_group('alternate@mail.com'), '~SomeFirstName_User1')
        profiles = openreview.tools.get_profiles(
            client, ids_or_emails=['~SomeFirstName_User1', '~Another_Name1', 'user@gmail.com', 'test_user@mail.com', 'test@mail.com', 'alternate@mail.com', '~Test_Name1'], as_dict=True
        )

        assert isinstance(profiles, dict)
        assert profiles['~SomeFirstName_User1']
        assert profiles['~Another_Name1']
        assert profiles['~SomeFirstName_User1'].id == profiles['~Another_Name1'].id
        assert profiles['user@gmail.com']
        assert profiles['test@mail.com'].id == '~SomeFirstName_User1'
        assert profiles['alternate@mail.com'].id == '~SomeFirstName_User1'
        assert profiles['test_user@mail.com'].id == 'test_user@mail.com'
        assert profiles['~Test_Name1'] is None


    def test_filter_by_publications(self, client, test_client):
        
        publications = [
            openreview.Note(
                id = '1',
                pdate = openreview.tools.datetime_millis(datetime.datetime(2014, 4, 30)),
                content = {
                    'year': '2017'
                },
                invitation = 'test/-/Submission',
                readers=[],
                writers=[],
                signatures=[]
            ),
            openreview.Note(
                id = '2',
                tcdate = openreview.tools.datetime_millis(datetime.datetime(2015, 4, 30)),
                content = {

                },
                invitation = 'test/-/Submission',
                readers=[],
                writers=[],
                signatures=[]
            ),
            openreview.Note(
                id = '3',
                cdate = openreview.tools.datetime_millis(datetime.datetime(2016, 4, 30)),
                content = {

                },
                invitation = 'test/-/Submission',
                readers=[],
                writers=[],
                signatures=[]
            ),
            openreview.Note(
                id = '4',
                content = {
                    'year': '2017'
                },
                invitation = 'test/-/Submission',
                readers=[],
                writers=[],
                signatures=[]
            ),
            openreview.api.Note(
                id = '5',
                content = {
                    'year': { 'value': 2017 }
                }
            ),
            openreview.api.Note(
                id = '6',
                pdate = 111111111111111111111,
                content = {
                    'year': { 'value': 2018 }
                }
            )
        ]

        filtered_publications = openreview.tools.filter_publications_by_year(publications, 2013)
        assert len(filtered_publications) == 6
        
        filtered_publications = openreview.tools.filter_publications_by_year(publications, 2014)
        assert len(filtered_publications) == 5
        
        filtered_publications = openreview.tools.filter_publications_by_year(publications, 2015)
        assert len(filtered_publications) == 4

        filtered_publications = openreview.tools.filter_publications_by_year(publications, 2016)
        assert len(filtered_publications) == 3

        filtered_publications = openreview.tools.filter_publications_by_year(publications, 2017)
        assert len(filtered_publications) == 1

        filtered_publications = openreview.tools.filter_publications_by_year(publications, 2018)
        assert len(filtered_publications) == 0
