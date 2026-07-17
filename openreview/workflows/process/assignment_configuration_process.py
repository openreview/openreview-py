def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    committee_name = invitation.get_content_value('committee_name')
    reviewers_roles = domain.get_content_value('reviewers_roles')
    area_chairs_name = domain.get_content_value('area_chairs_name')

    assignment_title = edit.note.content['title']['value']

    match_name_invitation = client.get_invitation(f'{venue_id}/-/{committee_name}_Assignment_Deployment/Match')

    all_assignment_titles = match_name_invitation.edit['content']['match_name']['value']['param'].get('enum', [])
    if assignment_title not in all_assignment_titles:
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

    # if reviewer assignment was created, add it to list of possible reviewer assignment titles that ACs could edit
    if committee_name in reviewers_roles and area_chairs_name:
        edit_invitation_id = f'{venue_id}/{area_chairs_name}/-/Reviewer_Reassignment'
        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=edit_invitation_id,
                edit={
                    'content': {
                        'reviewers_proposed_assignment_title': {
                            'order': 2,
                            'description': 'If you would like area chairs to edit reviewer proposed assignments, select the title of the matching that you would like them to edit. If area chairs should edit deployed assignments, leave empty.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': all_assignment_titles,
                                    'optional': True,
                                    'deletable': True
                                }
                            }
                        }
                    },
                    'group': {
                        'content': {
                            'reviewers_proposed_assignment_title': {
                                'value': '${4/content/reviewers_proposed_assignment_title/value?}'
                            }
                        }
                    }
                }
            )
        )