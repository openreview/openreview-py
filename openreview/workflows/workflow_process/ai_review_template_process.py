def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    ai_review_invitation_id = f'{domain.id}/-/{stage_name}'

    edit_invitations_builder.set_edit_dates_invitation(ai_review_invitation_id, include_due_date=False, include_expiration_date=False)
    edit_invitations_builder.set_edit_email_settings_invitation(ai_review_invitation_id)
    edit_invitations_builder.set_edit_prompt_invitation(ai_review_invitation_id)

    client.post_group_edit(
        invitation=meta_invitation_id,
        readers=[domain.id],
        writers=[domain.id],
        signatures=[domain.id],
        group=openreview.api.Group(
            id=f'{domain.id}/AI_Reviewer',
            readers=[domain.id],
            writers=[domain.id],
            signatories=[domain.id],
            signatures=[domain.id]
        )
    )