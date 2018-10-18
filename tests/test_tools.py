import openreview
import random
import types
import sys



class TestTools():

    def test_get_submission_invitations(self, client):
        invitations = openreview.tools.get_submission_invitations(client)
        assert len(invitations) == 0, "Invitations could not be retrieved"

    def test_get_all_venues(self, client):
        venues = openreview.tools.get_all_venues(client)
        assert len(venues) == 0, "Venues could not be retrieved"

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
