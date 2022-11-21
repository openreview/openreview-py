def process(client, edit, invitation):

    SHORT_PHRASE = ''
    CONFERENCE_ID = ''
    AUTHORS_NAME = ''
    SUBMISSION_NAME = ''

    submission = client.get_note(edit.note.id)

    subject = f'''{SHORT_PHRASE} has received a new revision of your submission titled {submission.content['title']['value']}'''

    message = f'''Your new revision of the submission to {SHORT_PHRASE} has been posted.

Title: {submission.content['title']['value']}

Abstract {submission.content['abstract']['value']}

To view your submission, click here: https://openreview.net/forum?id={submission.forum}'''

    client.post_message(
        subject=subject,
        recipients=submission.content['authorids']['value'],
        message=message
    )

    if 'authorids' in submission.content:
        author_group = openreview.tools.get_group(client, f'{CONFERENCE_ID}/{SUBMISSION_NAME}{submission.number}/{AUTHORS_NAME}')
        submission_authors = submission.content['authorids']['value']
        if author_group and set(author_group.members) != set(submission_authors):
            client.post_group_edit(
                invitation=f'{CONFERENCE_ID}/-/Edit',
                readers = [CONFERENCE_ID],
                writers = [CONFERENCE_ID],
                signatures = [CONFERENCE_ID],
                group = openreview.api.Group(
                    id = author_group.id,
                    members = submission_authors
                )
            )