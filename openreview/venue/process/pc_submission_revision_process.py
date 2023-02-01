def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_name = domain.content['subtitle']['value']
    authors_name = domain.content['authors_name']['value']
    submission_name = domain.content['submission_name']['value']

    submission = client.get_note(edit.note.id)

    subject = f'''{short_name} has received a new revision of your submission titled {submission.content['title']['value']}'''

    message = f'''Your new revision of the submission to {short_name} has been posted.

Title: {submission.content['title']['value']}

Abstract {submission.content['abstract']['value']}

To view your submission, click here: https://openreview.net/forum?id={submission.forum}'''

    client.post_message(
        subject=subject,
        recipients=submission.content['authorids']['value'],
        message=message
    )

    if 'authorids' in submission.content:
        author_group = openreview.tools.get_group(client, f'{venue_id}/{submission_name}{submission.number}/{authors_name}')
        submission_authors = submission.content['authorids']['value']
        if author_group and set(author_group.members) != set(submission_authors):
            client.post_group_edit(
                invitation=meta_invitation_id,
                readers = [venue_id],
                writers = [venue_id],
                signatures = [venue_id],
                group = openreview.api.Group(
                    id = author_group.id,
                    members = submission_authors
                )
            )