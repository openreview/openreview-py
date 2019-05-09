import openreview
import openreview.tools
import random

class TestEdges:

    def test_save_bulk (self, client):
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        conference = builder.get_result()
        inv = openreview.Invitation(id='NIPS.cc/2018/Workshop/MLITS/-/affinity')
        inv = client.post_invitation(inv)
        edges = []
        for p in range(1000):
            for r in range(200):
                score = random.random()
                rev = 'reviewer-'+str(r)
                edge = openreview.Edge(head='paper-'+str(p), tail=rev, weight=score,
                            invitation='NIPS.cc/2018/Workshop/MLITS/-/affinity',
                            readers=['everyone'], writers=['NIPS.cc/2018/Workshop/MLITS'], signatures=[rev])
                edges.append(edge)

        client.post_bulk_edges(edges)
        them = list(openreview.tools.iterget_edges(client, invitation='NIPS.cc/2018/Workshop/MLITS/-/affinity'))
        assert len(edges) == len(them)