def process_update(client, payment, invitation, existing_payment):

    if payment.status != 'paid':
        return

    if existing_payment and existing_payment.status not in ['pending', 'expired']:
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
    payer = openreview.tools.pretty_id(payment.signature)
    amount = f'{payment.amount / 100:.2f} {payment.currency}'

    client.post_message(
        invitation=meta_invitation_id,
        signature=venue_id,
        recipients=[f'{venue_id}/{submission_name}{submission.number}/{authors_name}'],
        replyTo=contact,
        sender=sender,
        subject=f'[{short_name}] The submission fee has been paid for submission number {submission.number}',
        message=f'''Hi {{{{fullname}}}},

The submission fee of your submission to {short_name} has been paid. No further payment is due for this submission.

Submission Number: {submission.number}

Title: {submission.content['title']['value']}

Amount: {amount}

Paid by: {payer}

Submission fees are non-refundable.

To view your submission, click here: https://openreview.net/forum?id={submission.id}'''
    )
