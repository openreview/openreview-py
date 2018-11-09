import openreview
import random
import types
import sys



class TestTools():

    def setup_method(self, method):
        # Password should be saved in the environment variable OPENREVIEW_PASSWORD
        self.client = openreview.Client(username = "openreview.net", password = '1234')
        assert self.client is not None, "Client is none"

    def test_get_submission_invitations(self):
        invitations = openreview.tools.get_submission_invitations(self.client)
        assert len(invitations) == 0, "Invitations could not be retrieved"

    def test_get_all_venues(self):
        venues = openreview.tools.get_all_venues(self.client)
        assert len(venues) == 0, "Venues could not be retrieved"

    def test_iterget_notes(self):
        notes_iterator = openreview.tools.iterget_notes(self.client)
        assert notes_iterator

    def test_get_all_refs(self):
        refs_iterator = openreview.tools.iterget_references(self.client)
        assert refs_iterator

    def test_get_all_tags(self):
        tag_iterator = openreview.tools.iterget_tags(self.client)
        assert tag_iterator

    def test_get_all_invitations(self):
        invitations_iterator = openreview.tools.iterget_invitations(self.client)
        assert invitations_iterator

    def test_get_all_groups(self):
        group_iterator = openreview.tools.iterget_groups(self.client)
        assert group_iterator

    def test_get_preferred_name(self):
        superuser_profile = self.client.get_profile('openreview.net')
        preferred_name = openreview.tools.get_preferred_name(superuser_profile)
        assert preferred_name, "preferred name not found"
        assert preferred_name == 'Super User'

    def test_parallel_exec(self):

        def do_work(value):
            return self.client.get_note(value.id)

        results = openreview.tools.parallel_exec(self.client.get_notes(limit=10), do_work)
        assert len(results) == 10
