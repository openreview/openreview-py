import openreview
import openreview.tools
import time

class TestEdges:

    def test_save_bulk (self, client):
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2020/Workshop/MLITS')
        builder.set_submission_stage(public=True)
        conference = builder.get_result()

        # Edge invitation
        inv1 = openreview.Invitation(id=conference.id + '/-/affinity', signatures=['~Super_User1'], reply={
            'content': {
                'head': {
                    'type': 'Note'
                },
                'tail': {
                    'type': 'Profile',
                },
                'label': {
                    'value-radio': ['Very High', 'High', 'Neutral', 'Low', 'Very Low']
                },
                'weight': {
                    'value-regex': r'[0-9]+\.[0-9]'
                }
            }
        })
        inv1 = client.post_invitation(inv1)

        # Sample note
        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = [conference.id],
            writers = [conference.id],
            signatures = ['~Super_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com'],
                'authors': ['Test User'],
                'pdf': '/pdf/22234qweoiuweroi22234qweoiuweroi12345678.pdf'
            }
        )
        note = client.post_note(note)

        # Edges
        edges = []
        for _ in range(1000):
            edge1 = openreview.Edge(head=note.id, tail='~Super_User1', label='High', weight='0.5',
                invitation=inv1.id, readers=['everyone'], writers=[conference.id],
                signatures=['~Super_User1'])
            
            edge2 = openreview.Edge(head=note.id, tail='~Super_User1', label='Very High', weight='1.0',
                invitation=inv1.id, readers=['everyone'], writers=[conference.id],
                signatures=['~Super_User1'])
            
            edges.extend([edge1, edge2])

        openreview.tools.post_bulk_edges(client, edges)
        posted_edges = list(openreview.tools.iterget_edges(client, invitation=inv1.id))
        assert len(edges) == len(posted_edges)

    def test_get_edges(self, client):
        invitation_id = 'NIPS.cc/2020/Workshop/MLITS/-/affinity'
        all_edges = client.get_edges(invitation=invitation_id)
        assert len(all_edges) == 1000
        some_edges = client.get_edges(invitation=invitation_id, limit=500)
        assert len(some_edges) == 500
        super_user_edges = client.get_edges(tail='~Super_User1')
        assert len(super_user_edges) == 1000

    def test_get_edges_count(self, client):
        invitation_id = 'NIPS.cc/2020/Workshop/MLITS/-/affinity'
        count = client.get_edges_count(invitation=invitation_id)
        assert count == 2000

    def test_delete_edges(self, client):
        edges_before = list(openreview.tools.iterget_edges(client, invitation='NIPS.cc/2020/Workshop/MLITS/-/affinity', label='High'))
        assert len(edges_before) == 1000
        client.delete_edges(invitation='NIPS.cc/2020/Workshop/MLITS/-/affinity', label='High')
        time.sleep(0.5)
        edges_after = list(openreview.tools.iterget_edges(client, invitation='NIPS.cc/2020/Workshop/MLITS/-/affinity', label='High'))
        assert len(edges_after) == 0

        client.delete_edges(invitation='NIPS.cc/2020/Workshop/MLITS/-/affinity')
        time.sleep(0.5)
        edges_after2 = list(openreview.tools.iterget_edges(client, invitation='NIPS.cc/2020/Workshop/MLITS/-/affinity'))
        assert len(edges_after2) == 0

