def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    submission_name = domain.get_content_value('submission_name')
    payment_name = client.get_invitation(invitation.invitations[0]).get_content_value('payment_name')

    submission = client.get_note(invitation.edit['note']['forum'])
    payment_invitation_id = f'{domain.id}/{submission_name}{submission.number}/-/{payment_name}'

    settled_payments = [p for p in client.get_all_payments(note=submission.id, invitation=payment_invitation_id) if p.status in ['paid', 'waived']]
    if settled_payments:
        raise openreview.OpenReviewException(f'The submission fee of this submission is already {settled_payments[0].status}, no waiver is needed.')
