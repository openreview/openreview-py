import openreview
import openreview.tools

class TestEdges:

    def test_save_bulk (self, client):
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('NIPS.cc/2020/Workshop/MLITS')
        builder.set_submission_stage(public=True)
        conference = builder.get_result()

        # Edge invitation
        inv1 = openreview.Invitation(id=conference.id + '/-/affinity', reply={
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
            readers = ['everyone'],
            writers = [conference.id],
            signatures = ['~Super_User1'],
            content = {
                'title': 'Paper title',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com'],
                'authors': ['Test User'],
                'pdf': '/pdf/link_to_pdf'
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

        openreview.tools.post_bulk_edges(client, edges)
        them = list(openreview.tools.iterget_edges(client, invitation=inv1.id))
        assert len(edges) == len(them)
