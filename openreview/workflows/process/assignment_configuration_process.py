def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')

    assignment_title = edit.note.content['title']['value']

    match_name_invitation = client.get_invitation(f'{venue_id}/-/Deploy_Reviewer_Assignment/Match')

    all_assignment_titles = match_name_invitation.edit['content']['match_name']['value']['param'].get('enum', [])
    all_assignment_titles.append(assignment_title)

    client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=match_name_invitation.id,
                edit={
                    'content': {
                        'match_name': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': all_assignment_titles
                                }
                            }
                        }
                    }
                }
            )
        )



