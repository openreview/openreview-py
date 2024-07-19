def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    request_form_id = domain.get_content_value('request_form_id')
    reveal_authors = edit.content['reveal_authors']['value']
    if 'Withdrawal' in invitation.id:
        field_name = 'withdrawn_submission_id'
    else:
        field_name = 'desk_rejected_submission_id'
    invitation_id = domain.get_content_value(field_name)

    venue = openreview.helpers.get_venue(client, request_form_id, support_user)

    if reveal_authors:
        content = {
            'authors': {
                'readers': {
                    'delete': True
                }
            },
            'authorids': {
                'readers': {
                    'delete': True
                }
            }
        }
    else:
        content = {
            'authors': {
                'readers' : [venue_id, venue.get_authors_id('${{4/id}/number}')]
            },
            'authorids': {
                'readers' : [venue_id, venue.get_authors_id('${{4/id}/number}')]
            },
        }

    client.post_invitation_edit(
        invitations = meta_invitation_id,
        signatures = [venue_id],
        invitation = openreview.api.Invitation(
            id=invitation_id,
            edit = {
                'note': {
                    'content': content
                }
            }

        )
    )