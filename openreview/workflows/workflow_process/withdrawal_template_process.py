def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')
    submission_name = edit.content['submission_name']['value']

    stage_name = edit.content['name']['value']

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[invitation.domain],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'withdrawn_venue_id': { 'value': f'{domain.id}/Withdrawn_{submission_name}' },
                'public_withdrawn_submissions': { 'value': False },
                'withdrawal_invitation_id': { 'value': f'{domain.id}/-/Withdrawal' },
                'withdrawn_submission_reveal_authors': { 'value': False },
                'withdraw_expiration_id': { 'value': f'{domain.id}/-/Withdraw_Expiration' },
                'withdraw_reversion_id': { 'value': f'{domain.id}/-/Unwithdrawal' },
                'withdraw_committee': { 
                    'value': [
                        domain.id + '/Program_Chairs',
                        f'{domain.id}/{submission_name}' + '{number}/Reviewers',
                        f'{domain.id}/{submission_name}' + '{number}/Authors'
                    ] 
                },
                'withdrawal_name': { 'value': stage_name },
                'withdrawal_email_program_chairs': { 'value': False }
            }
        )
    )

    withdrawal_invitation_id = f'{domain.id}/-/{stage_name}'
    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    edit_invitations_builder.set_edit_dates_invitation(withdrawal_invitation_id, process_file='workflow_process/edit_withdrawal_cdate_process.py', include_activation_date=True, include_due_date=False)

    withdrawn_submission_invitation_id = f'{domain.id}/-/Withdrawal'
    edit_invitations_builder.set_edit_readers_one_level_invitation(withdrawn_submission_invitation_id)