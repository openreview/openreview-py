def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    submission_name = domain.get_content_value('submission_name')
    authors_name = domain.get_content_value('authors_name')

    reveal_authors = edit.invitation.content['reveal_author_identities']['value']

    if reveal_authors:
        authors_readers = { 'param': { 'const': { 'delete': True } } }
    else:
        authors_readers = [venue_id, f'{venue_id}/{submission_name}' + '${{4/id}/number}' + f'/{authors_name}']

    super_invitation = client.get_invitation(edit.invitation.id)
    content = {
        'authors': {
            'readers': authors_readers
        }
    }
    if 'authorids' in super_invitation.edit['note']['content']:
        content['authorids'] = {
            'readers': authors_readers
        }

    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=edit.invitation.id,
            signatures=[venue_id],
            edit={
                'note': {
                    'content': content
                }
            }
        )
    )
