def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    review_note=client.get_note(edit.note.id)
    review_edits = client.get_note_edits(note_id=review_note.id, sort='tcdate:asc')
    print('Review id:', review_note.id)

    # run post-process only if this is the first edit of the review
    if edit.id != review_edits[0].id:
        print('Review edited, exit')
        return

    ## Decrease pending reviews counter
    signature_group = client.get_group(id=review_note.signatures[0])
    reviewer_profile = openreview.tools.get_profile(client, signature_group.members[0])
    print('reviewer profile:', reviewer_profile.id)
    edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=(reviewer_profile.id if reviewer_profile else signature_group.members[0]))

    if edges and edges[0].weight > 0:
        pending_review_edge = edges[0]
        if not review_note.ddate:
            print('Decreasing pending review count!')
            pending_review_edge.weight -= 1
            client.post_edge(pending_review_edge)