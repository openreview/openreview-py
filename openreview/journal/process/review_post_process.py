def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    review_note=client.get_note(edit.note.id)
    print('Review id:', review_note.id)

    ## Decrease pending reviews counter
    signature_group = client.get_group(id=review_note.signatures[0])
    reviewer_profile = openreview.tools.get_profile(client, signature_group.members[0])
    print('reviewer profile:', reviewer_profile.id)
    edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=(reviewer_profile.id if reviewer_profile else signature_group.members[0]))

    if edges and edges[0].weight > 0:
        pending_review_edge = edges[0]
        if not review_note.ddate and journal.get_assignment_delay_after_submitted_review() > 0:
            print('Decreasing pending review count!')
            pending_review_edge.weight -= 1
            client.post_edge(pending_review_edge)