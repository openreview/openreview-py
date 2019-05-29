import openreview
import openreview.tools

class TestEdges:

    def test_save_bulk (self, client):
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2018/Workshop/MLITS')
        conference = builder.get_result()

        # Edge invitation
        inv1 = openreview.Invitation(id=conference.id + '/-/affinity', reply={
            'content': {
                'edge': {
                    'head': 'note',
                    'tail': 'profile',
                    'value-radio': [
                        ['Very High', 1], ['High', 0.5], ['Neutral', 0],
                        ['Low', -0.5], ['Very Low', -1]
                    ]
                }
            }
        })
        inv1 = client.post_invitation(inv1)

        # Submission invitation
        inv2 = openreview.Invitation(id=conference.id + '/-/submission')
        inv2 = client.post_invitation(inv2)

        # Sample note
        note = openreview.Note(invitation = inv2.id,
            readers = ['everyone'],
            writers = [conference.id],
            signatures = ['~Super_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com'],
                'authors': ['Test User'],
            }
        )
        note = client.post_note(note)

        # Edges
        edges = []
        for p in range(1000):
            edge = openreview.Edge(head=note.id, tail='~Super_User1', label='High', weight=0.5,
                invitation=inv1.id, readers=['everyone'], writers=[conference.id],
                signatures=['~Super_User1'])
            edges.append(edge)

        client.post_bulk_edges(edges)
        them = list(openreview.tools.iterget_edges(client, invitation=inv1.id))
        assert len(edges) == len(them)
