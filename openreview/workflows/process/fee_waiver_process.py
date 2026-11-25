def process(client, edit, invitation):

    support_group_id = invitation.signatures[0]
    payment_name = invitation.get_content_value('payment_name')
    submission_id = edit.note.forum

    fee_invitations = [fee_invitation for fee_invitation in client.get_invitations(replyForum=submission_id, type='payment', expired=True) if fee_invitation.id.endswith(f'/-/{payment_name}')]
    if not fee_invitations:
        raise openreview.OpenReviewException(f'The submission {submission_id} has no submission fee to waive.')
    fee_invitation = fee_invitations[0]

    for pending_payment in client.get_all_payments(note=submission_id, status='pending'):
        print(f'Cancelling checkout {pending_payment.id}')
        try:
            client.cancel_payment(pending_payment.id)
        except openreview.OpenReviewException as error:
            print(f'The checkout {pending_payment.id} could not be cancelled: {error}')

    settled_payments = [payment for payment in client.get_all_payments(note=submission_id) if payment.status in ['paid', 'waived']]
    if settled_payments:
        print(f'The submission fee is already {settled_payments[0].status}')
        return

    client.post_payment_edit(
        invitation=fee_invitation.id,
        signature=support_group_id,
        payment=openreview.api.Payment(
            note=submission_id,
            amount=fee_invitation.get_content_value('amount'),
            currency=fee_invitation.get_content_value('currency'),
            status='waived',
            signature=support_group_id
        )
    )
