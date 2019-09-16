import openreview
import random
import types
import sys

def do_work(value):
    return value.id

class TestTools():

    def test_get_submission_invitations(self, client):
        invitations = openreview.tools.get_submission_invitations(client)
        assert len(invitations) == 12, "Invitations could not be retrieved"

    def test_get_all_venues(self, client):
        venues = openreview.tools.get_all_venues(client)
        assert len(venues) == 9, "Venues could not be retrieved"

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

    def test_get_preferred_name(self, client):
        superuser_profile = client.get_profile('openreview.net')
        preferred_name = openreview.tools.get_preferred_name(superuser_profile)
        assert preferred_name, "preferred name not found"
        assert preferred_name == 'Super User'

    def test_parallel_exec(self, client):
        values = client.get_groups(limit=10)
        results = openreview.tools.parallel_exec(values, do_work)
        assert len(results) == len(values)

    def test_match_authors_to_emails(self):
        correct_pairs = [
            ('Ada Lovelace', 'ada@lovelacemanor.org'),
            ('Alan Turing', 'turing@princeton.edu'),
            ('Edsger W. Dijkstra', 'ed.dijkstra@uva.nl'),
            ('Grace Hopper', 'ghopper@yale.edu')
        ]

        shuffled_names = random.sample(
            [p[0] for p in correct_pairs], len(correct_pairs))

        shuffled_emails = random.sample(
            [p[1] for p in correct_pairs], len(correct_pairs))

        result = openreview.tools.match_authors_to_emails(
            shuffled_names, shuffled_emails)

        for name, email in correct_pairs:
            assert result[name] == email

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

        profiles_created = openreview.tools.create_authorid_profiles(
            client, note)

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


