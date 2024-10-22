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
                'desk_rejected_venue_id': { 'value': f'{domain.id}/Desk_Rejected_{submission_name}' },
                'public_desk_rejected_submissions': { 'value': False },
                'desk_rejected_submission_id': { 'value': f'{domain.id}/-/Desk_Rejected_{submission_name}' },
                'desk_rejected_submission_reveal_authors': { 'value': False },
                'desk_reject_expiration_id': { 'value': f'{domain.id}/-/Desk_Reject_Expiration' },
                'desk_rejection_reversion_id': { 'value': f'{domain.id}/-/Desk_Rejection_Reversion' },
                'desk_reject_committee': { 
                    'value': [
                        domain.id + '/Program_Chairs',
                        f'{domain.id}/{submission_name}/' + '{number}/Reviewers',
                        f'{domain.id}/{submission_name}/' + '{number}/Authors'
                    ] 
                },
                'desk_rejection_name': { 'value': 'Desk_Rejection' },
                'desk_rejection_email_pcs': { 'value': False }
            }
        )
    )