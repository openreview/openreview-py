def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    submission_name = domain.get_content_value('submission_name')
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    support_group_id = invitation.signatures[0]
    payment_name = invitation.get_content_value('payment_name')

    request = client.get_note(edit.note.id)
    requester = request.signatures[0]
    submission_group_id = request.invitations[0].split('/-/')[0]
    submission_number = submission_group_id.split('/')[-1].replace(submission_name, '')

    if request.content['status']['value'] == 'Rejected':
        client.post_message(
            invitation=f'{support_group_id}/-/Edit',
            signature=support_group_id,
            recipients=[requester],
            replyTo=contact,
            subject=f'[{short_name}] Your fee waiver request has been rejected for submission number {submission_number}',
            message=f'''Hi {{{{fullname}}}},

Your request to waive the submission fee of your submission to {short_name} has been rejected. The submission fee remains due.

Submission Number: {submission_number}

To view your submission, click here: https://openreview.net/forum?id={request.forum}'''
        )
        return

    settled_payments = [p for p in client.get_all_payments(note=request.forum) if p.status in ['paid', 'waived']]
    if settled_payments:
        print(f'The submission fee is already {settled_payments[0].status}')
        return

    payment_invitation_id = f'{submission_group_id}/-/{payment_name}'
    payment_invitation = client.get_invitation(payment_invitation_id)
    client.post_payment_edit(
        invitation=payment_invitation_id,
        signature=support_group_id,
        payment=openreview.api.Payment(
            note=request.forum,
            amount=payment_invitation.get_content_value('amount'),
            currency=payment_invitation.get_content_value('currency'),
            status='waived',
            signature=support_group_id
        )
    )

    client.post_message(
        invitation=f'{support_group_id}/-/Edit',
        signature=support_group_id,
        recipients=[requester],
        replyTo=contact,
        subject=f'[{short_name}] Your fee waiver request has been granted for submission number {submission_number}',
        message=f'''Hi {{{{fullname}}}},

Your request to waive the submission fee of your submission to {short_name} has been granted. No payment is due for this submission.

Submission Number: {submission_number}

To view your submission, click here: https://openreview.net/forum?id={request.forum}'''
    )
