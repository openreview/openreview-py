def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    reviewer_id = edit.note.content['reviewer_id']['value']

    client.add_members_to_group(journal.get_reviewers_reported_id(), reviewer_id)
