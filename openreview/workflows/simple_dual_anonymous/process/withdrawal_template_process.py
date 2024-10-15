def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')
    submission_name = edit.content['submission_name']['value']

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[support_user],
        group=openreview.api.Group(
            id=domain.id,
            content={
                'withdrawn_venue_id': { 'value': f'{domain.id}/Withdrawn_{submission_name}' },
                'public_withdrawn_submissions': { 'value': False },
                'withdrawn_submission_id': { 'value': f'{domain.id}/-/Withdrawn_{submission_name}' },
                'withdrawn_submission_reveal_authors': { 'value': False },
                'withdraw_expiration_id': { 'value': f'{domain.id}/-/Withdraw_Expiration' },
                'withdraw_reversion_id': { 'value': f'{domain.id}/-/Withdrawal_Reversion' },
                'withdraw_committee': { 
                    'value': [
                        domain.id + '/Program_Chairs',
                        f'{domain.id}/{submission_name}/' + '{number}/Reviewers',
                        f'{domain.id}/{submission_name}/' + '{number}/Authors'
                    ] 
                },
                'withdrawal_name': { 'value': 'Withdrawal' },
                'withdrawal_email_program_chairs': { 'value': False }
            }
        )
    )