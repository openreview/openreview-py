import openreview
import random
import types
import sys

def do_work(value):
    return value.id

class TestTools():

    def test_get_submission_invitations(self, client):
        invitations = openreview.tools.get_submission_invitations(client)
        assert len(invitations) == 22, "Invitations could not be retrieved"

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

    def test_get_all_venues(self, client):
        venues = openreview.tools.get_all_venues(client)
        assert len(venues) == 13, "Venues could not be retrieved"

    def test_iterget_notes(self, client):
        notes_iterator = openreview.tools.iterget_notes(client)
        assert notes_iterator

    def test_get_all_refs(self, client):
        refs_iterator = openreview.tools.iterget_references(client)
        assert refs_iterator

    def test_get_all_tags(self, client):
        tag_iterator = openreview.tools.iterget_tags(client)
        assert tag_iterator

    def test_get_all_invitations(self, client):
        invitations_iterator = openreview.tools.iterget_invitations(client)
        assert invitations_iterator

    def test_get_all_groups(self, client):
        group_iterator = openreview.tools.iterget_groups(client)
        assert group_iterator

    def test_get_grouped_edges(self, client):
        group_iterator = openreview.tools.iterget_grouped_edges(client)
        assert group_iterator

    def test_get_preferred_name(self, client):
        superuser_profile = client.get_profile('openreview.net')
        preferred_name = openreview.tools.get_preferred_name(superuser_profile)
        assert preferred_name, "preferred name not found"
        assert preferred_name == 'Super User'

    def test_parallel_exec(self, client):
        values = client.get_groups(limit=10)
        results = openreview.tools.parallel_exec(values, do_work)
        assert len(results) == len(values)

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
        assert openreview.tools.subdomains('michael@mails.tsinghua.edu.cn') == ['mails.tsinghua.edu.cn', 'tsinghua.edu.cn']
        assert openreview.tools.subdomains('michael@robots.ox.ac.uk') == ['robots.ox.ac.uk', 'ox.ac.uk']
        assert openreview.tools.subdomains('michael@eng.ox.ac.uk') == ['eng.ox.ac.uk', 'ox.ac.uk']
        assert openreview.tools.subdomains('michael@ground.ai') == ['ground.ai']
        assert openreview.tools.subdomains('michael@cs.umass.edu') == ['cs.umass.edu', 'umass.edu']
        assert openreview.tools.subdomains('   ') == []

    def test_replace_members_with_ids(self, client, test_client):

        posted_group = client.post_group(openreview.Group(id='test.org',
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            signatories=['~Super_User1'],
            members=['test@mail.com', '~Test_User1', '~Another_Name1']
        ))
        assert posted_group

        client.post_profile(openreview.Profile(
            referent='~Test_User1',
            signatures = ['~Test_User1'],
            content={
                'names': [
                    {
                    'first': 'Another',
                    'last': 'Name',
                    'username': '~Another_Name1'
                    }
                ]
            }
        ))

        replaced_group = openreview.tools.replace_members_with_ids(client, posted_group)
        assert replaced_group
        assert replaced_group.members == ['~Test_User1']

        posted_group = client.post_group(openreview.Group(id='test.org',
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            signatories=['~Super_User1'],
            members=['~Super_User1', '~Another_Name1', 'noprofile@mail.com']
        ))
        replaced_group = openreview.tools.replace_members_with_ids(client, posted_group)
        assert replaced_group
        assert replaced_group.members == ['~Super_User1', '~Test_User1', 'noprofile@mail.com']

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

        profile1 = openreview.Profile(
            id = 'Test_Conflict1',
            content = {
                'emails': ['user@cmu.edu'],
                'history': [{
                    'institution': {
                        'domain': 'user@126.com'
                    }
                }]
            }
        )

        profile2 = openreview.Profile(
            id = 'Test_Conflict2',
            content = {
                'emails': ['user2@126.com'],
                'history': [{
                    'institution': {
                        'domain': 'user2@cmu.edu'
                    }
                }]
            }
        )

        conflicts = openreview.tools.get_conflicts([profile1], profile2)
        assert len(conflicts) == 1
        assert conflicts[0] == 'cmu.edu'
