def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    review_release_invitation_id = f'{domain.id}/-/{stage_name}'

    cdate = edit.content['activation_date']['value']-1800000 # 30 min before cdate

    edit_invitations_builder.set_review_release_reply_readers_invitation(review_release_invitation_id, due_date=cdate)
    edit_invitations_builder.set_edit_dates_one_level_invitation(review_release_invitation_id, due_date=cdate)