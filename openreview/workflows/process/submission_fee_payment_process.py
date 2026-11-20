def process_update(client, payment, invitation, existing_payment):

    is_new_payment = existing_payment is None
    was_open = existing_payment is not None and existing_payment.status in ['pending', 'expired']
    is_paid = payment.status == 'paid' and (is_new_payment or was_open)
    is_waived = payment.status == 'waived' and is_new_payment

    if not is_paid and not is_waived:
        return

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    sender = domain.get_content_value('message_sender')
    submission_name = domain.get_content_value('submission_name')
    authors_name = domain.get_content_value('authors_name')

    submission = client.get_note(payment.note)
    authors_group_id = f'{venue_id}/{submission_name}{submission.number}/{authors_name}'

    if is_paid:
        client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            recipients=[authors_group_id],
            replyTo=contact,
            sender=sender,
            subject=f'[{short_name}] The submission fee has been paid for submission number {submission.number}',
            message=f'''Hi {{{{fullname}}}},

The submission fee of your submission to {short_name} has been paid. No further payment is due for this submission.

Submission Number: {submission.number}

Title: {submission.content['title']['value']}

Amount: {payment.amount / 100:.2f} {payment.currency}

Paid by: {openreview.tools.pretty_id(payment.signature)}

Submission fees are non-refundable.

To view your submission, click here: https://openreview.net/forum?id={submission.id}'''
        )
        return

    client.post_message(
        invitation=meta_invitation_id,
        signature=venue_id,
        recipients=[authors_group_id],
        replyTo=contact,
        sender=sender,
        subject=f'[{short_name}] The submission fee has been waived for submission number {submission.number}',
        message=f'''Hi {{{{fullname}}}},

The submission fee of your submission to {short_name} has been waived. No payment is due for this submission.

Submission Number: {submission.number}

Title: {submission.content['title']['value']}

To view your submission, click here: https://openreview.net/forum?id={submission.id}'''
    )
