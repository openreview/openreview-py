def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    stage_name = edit.content['name']['value']
    submission_fee_payment_id = f'{venue_id}/-/{stage_name}'

    client.post_group_edit(
        invitation=meta_invitation_id,
        readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'submission_fee_payment_id': { 'value': submission_fee_payment_id }
            }
        )
    )

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, venue_id)
    edit_invitations_builder.set_edit_dates_invitation(submission_fee_payment_id, preprocess_file='workflow_process/edit_submission_fee_dates_pre_process.py')
    edit_invitations_builder.set_edit_payment_amount_invitation(submission_fee_payment_id)
    edit_invitations_builder.set_edit_payment_country_fees_invitation(submission_fee_payment_id, edit.signatures[0])
