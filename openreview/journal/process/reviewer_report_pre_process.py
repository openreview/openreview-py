def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    reviewer_id=edit.note.content['reviewer_id']['value']

    if not client.get_groups(id=journal.get_reviewers_id(), member=reviewer_id):
        raise openreview.OpenReviewException(f'Invalid reviewer id {reviewer_id}, make sure the reviewer is part of the reviewers group')
