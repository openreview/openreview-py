import openreview
import random
import types
import sys



class TestTools():

    def setup_method(self, method):
    	self.baseurl = 'https://dev.openreview.net'
        # Password should be saved in the environment variable OPENREVIEW_PASSWORD
        self.client = openreview.Client(baseurl = self.baseurl, username = "OpenReview.net")
        assert self.client is not None, "Client is none"

    def test_get_submission_invitations(self):
        invitations = openreview.get_submission_invitations(self.client)
        assert invitations, "Invitations could not be retrieved"

    def test_get_all_venues(self):
        venues = openreview.get_all_venues(self.client)
        assert venues, "Venues could not be retrieved"

    def test_iterget(self):
        data_size = 1000
        queue = [random.random() for _ in range(data_size)]

        def mock_get(limit=100, offset=0):
            return queue[offset:offset+limit]

        assert data_size == len(list(openreview.tools.iterget(mock_get)))

        new_iterator = openreview.tools.iterget(mock_get)

        counter = 0
        for random_real in new_iterator:
            counter += 1

        assert counter == data_size

        notes_iterator = openreview.tools.iterget(self.client.get_notes)
        notes_list = list(notes_iterator)
        assert notes_list is not None, "Notes iterator failed"

    def test_iterget_notes(self):
        batch_size = 1000
        notes_iterator = openreview.tools.iterget_notes(self.client, None, batch_size=batch_size)
        assert type(notes_iterator) == types.GeneratorType
        assert type(notes_iterator.next()) == openreview.Note


    def test_get_all_refs(self):
        batch_size = 1000
        refs_iterator = openreview.tools.iterget_references(self.client, None, batch_size=batch_size)
        assert type(refs_iterator) == types.GeneratorType
        assert type(refs_iterator.next()) == openreview.Note

    def test_get_all_tags(self):
        batch_size = 1000
        tag_iterator = openreview.tools.iterget_tags(self.client, None, batch_size=batch_size)
        assert type(tag_iterator) == types.GeneratorType
        assert type(tag_iterator.next()) == openreview.Tag
