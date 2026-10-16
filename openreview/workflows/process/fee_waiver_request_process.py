def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_name = domain.get_content_value('submission_name')
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')

    super_invitation = client.get_invitation(invitation.invitations[0])
    payment_name = super_invitation.get_content_value('payment_name')

    if not super_invitation.get_content_value('auto_grant_waivers'):
        print('Waivers are not granted automatically, the request is left to OpenReview support')
        return

    submission = client.get_note(invitation.edit['note']['forum'])
    requester = edit.signatures[0]
    payment_invitation_id = f'{venue_id}/{submission_name}{submission.number}/-/{payment_name}'

    ## A co-author may have paid, or had a waiver granted, since this request was filed
    settled_payments = [p for p in client.get_all_payments(note=submission.id, invitation=payment_invitation_id) if p.status in ['paid', 'waived']]
    if settled_payments:
        print(f'The submission fee is already {settled_payments[0].status}')
        return

    ## A waiver settles the fee through the same invitation as a payment: a waived payment of the fee,
    ## signed by the group the payment invitation requires, OpenReview support
    payment_invitation = client.get_invitation(payment_invitation_id)
    support_group_id = payment_invitation.edit['signature']['param']['const']
    client.post_payment_edit(
        invitation=payment_invitation_id,
        signature=support_group_id,
        payment=openreview.api.Payment(
            note=submission.id,
            amount=payment_invitation.get_content_value('amount'),
            currency=payment_invitation.get_content_value('currency'),
            status='waived',
            signatures=[support_group_id]
        )
    )

    client.post_message(
        invitation=f'{support_group_id}/-/Edit',
        signature=support_group_id,
        recipients=[requester],
        replyTo=contact,
        subject=f'[{short_name}] Your fee waiver request has been granted for submission number {submission.number}',
        message=f'''Hi {{{{fullname}}}},

Your request to waive the submission fee of your submission to {short_name} has been granted. No payment is due for this submission.

Submission Number: {submission.number}

Title: {submission.content['title']['value']}

To view your submission, click here: https://openreview.net/forum?id={submission.id}

Please note that responding to this email will direct your reply to {contact}.
'''
    )
