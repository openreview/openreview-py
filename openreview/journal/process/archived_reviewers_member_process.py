def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    members = edit.group.members.get('append', [])

    print('Added archived reviewers', members)

    for member in members:
        print('Delete edges for member', member)
        client.delete_edges(invitation=journal.get_reviewer_availability_id(), tail=member, soft_delete=True)
        client.delete_edges(invitation=journal.get_reviewer_pending_review_id(), tail=member, soft_delete=True)
        client.delete_edges(invitation=journal.get_reviewer_custom_max_papers_id(), tail=member, soft_delete=True)


    print('Remove members from the reviewers group')
    client.remove_members_from_group(journal.get_reviewers_id(), members)