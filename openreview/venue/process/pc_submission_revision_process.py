def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_name = domain.content['subtitle']['value']
    contact = domain.content['contact']['value']
    authors_name = domain.content['authors_name']['value']
    submission_name = domain.content['submission_name']['value']
    sender = domain.get_content_value('message_sender')

    submission = client.get_note(edit.note.id)

    subject = f'''{short_name} has received a new revision of your submission titled {submission.content['title']['value']}'''

    abstract_string = f'''
Abstract: {submission.content['abstract']['value']}
''' if 'abstract' in submission.content else ''

    message = f'''Your new revision of the submission to {short_name} has been posted.

Title: {submission.content['title']['value']}
{abstract_string}
To view your submission, click here: https://openreview.net/forum?id={submission.forum}'''

    client.post_message(
        invitation=meta_invitation_id,
        subject=subject,
        recipients=submission.content['authorids']['value'],
        message=message,
        replyTo=contact,
        signature=venue_id,
        sender=sender
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

    invitation_invitations = [i for i in client.get_all_invitations(prefix=f'{venue_id}/-/', type='invitation') if i.is_active()]

    for venue_invitation in invitation_invitations:
        print('processing invitation: ', venue_invitation.id)
        authorids = venue_invitation.edit['invitation'].get('edit', {}).get('note', {}).get('content', {}).get('authorids', {}).get('value', [])
        if '${{4/id}/content/authorids/value}' in authorids:
            print('post invitation edit: ', venue_invitation.id)
            client.post_invitation_edit(invitations=venue_invitation.id,
                content={
                    'noteId': { 'value': submission.id },
                    'noteNumber': { 'value': submission.number }
                },
                invitation=openreview.api.Invitation()
            )