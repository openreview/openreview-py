import openreview
import openreview.api
import openreview.tools
import time

class TestEdges:

    def test_save_bulk (self, openreview_client, test_client):
        openreview_client.post_invitation_edit(
            'openreview.net/-/Edit',
            readers=['everyone'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            invitation=openreview.api.Invitation(
                id='openreview.net/-/Affinity',
                writers=['~Super_User1'],
                signatures=['~Super_User1'],
                invitees=['~Super_User1'],
                readers=['everyone'],
                edge={
                    'signatures': { 'param': { 'regex': '.*' } },
                    'readers': { 'param': { 'regex': '.*' } },
                    'writers': { 'param': { 'regex': '.*' } },
                    'head': { 'param': { 'type': 'note' } },
                    'tail': { 'param': { 'type': 'profile' } },
                    'label': { 'param': { 'enum': ['Very High', 'High', 'Neutral', 'Low', 'Very Low'] } },
                    'weight': { 'param': { 'enum': [5, 10] } }
                }
            )
        )

        note_edit = openreview_client.post_note_edit(
            'openreview.net/-/Edit',
            ['~Super_User1'],
            readers=['everyone'],
            writers=['~Super_User1'],
            note=openreview.api.Note(
                readers=['everyone'],
                writers=['~Super_User1'],
                signatures=['~Super_User1'],
                content={
                    'title': { 'value': 'Paper title' },
                    'abstract': { 'value': 'This is an abstract' },
                    'authorids': { 'value': ['test@mail.com'] },
                    'authors': { 'value': ['SomeFirstName User'] },
                    'pdf': { 'value': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf' },
                }
            )
        )

        note_id = note_edit['note']['id']

        # Edges
        edges = []
        for _ in range(1000):
            edge1 = openreview.Edge(head=note_id, tail='~Super_User1', label='High', weight=5,
                invitation='openreview.net/-/Affinity', readers=['everyone'], writers=['~Super_User1'],
                signatures=['~Super_User1'])

            edge2 = openreview.Edge(head=note_id, tail='~Super_User1', label='Very High', weight=10,
                invitation='openreview.net/-/Affinity', readers=['everyone'], writers=['~Super_User1'],
                signatures=['~Super_User1'])

            edges.extend([edge1, edge2])

        openreview.tools.post_bulk_edges(openreview_client, edges)
        posted_edges = list(openreview.tools.iterget_edges(openreview_client, invitation='openreview.net/-/Affinity', tail='~Super_User1'))
        assert len(edges) == len(posted_edges)
    
    def test_rename_edges(self, client, openreview_client, helpers):
        guest = openreview.api.OpenReviewClient()
        to_profile = guest.register_user(email = 'nadia@mail.com', fullname = 'Nadia L', password = helpers.strong_password)
        assert to_profile
        assert to_profile['id'] == '~Nadia_L1'
        super_user_edges = list(openreview.tools.iterget_edges(openreview_client, tail="~Super_User1"))
        openreview_client.rename_edges('~Super_User1', '~Nadia_L1')
        nadias_edges = list(openreview.tools.iterget_edges(openreview_client, tail="~Nadia_L1"))
        super_edges_ids = [edge.id for edge in super_user_edges]
        nadia_edges_ids = [edge.id for edge in nadias_edges]
        for edge in super_edges_ids:
            assert edge in nadia_edges_ids
        assert len(super_user_edges)==len(nadias_edges)
        super_user_edges = list(openreview.tools.iterget_edges(openreview_client, tail="~Super_User1"))
        assert len(super_user_edges) == 0
        openreview_client.rename_edges('~Nadia_L1','~Super_User1')
        
    def test_get_edges(self, client, openreview_client):
        invitation_id = 'openreview.net/-/Affinity'
        all_edges = openreview_client.get_edges(invitation=invitation_id, tail='~Super_User1')
        assert len(all_edges) == 1000
        some_edges = openreview_client.get_edges(invitation=invitation_id, tail='~Super_User1', limit=500)
        assert len(some_edges) == 500
        super_user_edges = openreview_client.get_edges(tail='~Super_User1')
        assert len(super_user_edges) == 1000

    def test_get_edges_count(self, client, openreview_client):
        invitation_id = 'openreview.net/-/Affinity'
        count = openreview_client.get_edges_count(invitation=invitation_id)
        assert count == 2000
    
    def test_delete_edges(self, client, openreview_client):
        edges_count_before = openreview_client.get_edges_count(invitation='openreview.net/-/Affinity', label='High')
        assert edges_count_before == 1000
        openreview_client.delete_edges(invitation='openreview.net/-/Affinity', label='High', wait_to_finish=True)
        edges_count_after = openreview_client.get_edges_count(invitation='openreview.net/-/Affinity', label='High')
        assert edges_count_after == 0

        openreview_client.delete_edges(invitation='openreview.net/-/Affinity', wait_to_finish=True)
        edges_count_after = openreview_client.get_edges_count(invitation='openreview.net/-/Affinity')
        assert edges_count_after == 0    
