def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    submission_venue_id = domain.get_content_value('submission_venue_id')
    submission_name = domain.get_content_value('submission_name')
    authors_name = domain.get_content_value('authors_name')
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    sender = domain.get_content_value('message_sender')

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.edit['invitation']['cdate'] if 'cdate' in invitation.edit['invitation'] else invitation.cdate

    if now < cdate + 60 * 60 * 1000:
        print('The submission fees opened less than an hour ago, so their invitations may still be being created', cdate)
        return

    due_date = datetime.datetime.fromtimestamp(invitation.edit['invitation']['duedate'] / 1000, datetime.timezone.utc).strftime('%b %d %Y %I:%M%p') + ' UTC-0'
    expiration_date = datetime.datetime.fromtimestamp(invitation.edit['invitation']['expdate'] / 1000, datetime.timezone.utc).strftime('%b %d %Y %I:%M%p') + ' UTC-0'

    submissions = { submission.id: submission for submission in client.get_all_notes(content={ 'venueid': submission_venue_id }, domain=venue_id) }
    closed_note_ids = { payment.note for payment in client.get_all_payments(domain=venue_id) if payment.status in ['paid', 'waived', 'disputed', 'refunded'] }

    reminder_messages = []
    for fee_invitation in client.get_all_invitations(invitation=invitation.id, domain=venue_id):
        submission = submissions.get(fee_invitation.edit['payment']['note'])
        amount = fee_invitation.get_content_value('amount')
        if not submission or not amount or submission.id in closed_note_ids or (fee_invitation.expdate and fee_invitation.expdate <= now):
            continue

        reminder_messages.append({
            'recipients': [f'{venue_id}/{submission_name}{submission.number}/{authors_name}'],
            'subject': f'[{short_name}] Reminder: the submission fee is due for submission number {submission.number}',
            'message': f'''Hi {{{{fullname}}}},

This is a reminder that the submission fee of your submission to {short_name} has not been paid yet. It is due by {due_date}.

Submission Number: {submission.number}

Title: {submission.content['title']['value']}

Amount: {amount / 100:.2f} {fee_invitation.get_content_value('currency')}

To pay the fee, click here: https://openreview.net/forum?id={submission.id}

To pay the fees of several submissions at once, go to https://openreview.net/payments

Payments close on {expiration_date}. Submission fees are non-refundable.'''
        })

    openreview.tools.concurrent_requests(lambda message: client.post_message(
        invitation=meta_invitation_id,
        signature=venue_id,
        recipients=message['recipients'],
        replyTo=contact,
        sender=sender,
        subject=message['subject'],
        message=message['message']
    ), reminder_messages, desc='submission_fee_reminder_process')
    print(f'{len(reminder_messages)} submission fee reminders sent')
