def process(client, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(invitation.edit['note']['forum'])
    assigned_action_editor = submission.content.get('assigned_action_editor', {}).get('value')
    duedate = datetime.datetime.fromtimestamp(invitation.duedate/1000)
    now = datetime.datetime.utcnow()
    task = invitation.pretty_id()

    late_invitees = journal.get_late_invitees(invitation.id)

    if len(late_invitees) == 0:
      return

    if days_late_map:
        days_late = days_late_map.get(str(date_index), abs((now - duedate).days))
    else:
        days_late = abs((now - duedate).days)

    reviews = client.get_notes(forum=submission.id, invitation=invitation.id)

    if len(reviews) < journal.get_number_of_reviewers():
        print(f'Not enough reviews ({len(reviews)}) for {submission.id}, check ACK count')
        ACK_replies = [ r for r in client.get_notes(forum=submission.id) if 'Assignment/Acknowledgement' in r.invitations[0]]
        if len(ACK_replies) < journal.get_number_of_reviewers():
            print(f'Not enough ACKs ({len(ACK_replies)}) for {submission.id}, send reminders to EICs')
            client.post_message(
                invitation=journal.get_meta_invitation_id(),
                recipients=[journal.get_editors_in_chief_id()],
                subject=f'''[{journal.short_name}] Fewer than {journal.get_number_of_reviewers()} ACKs for the paper {submission.number}: {submission.content['title']['value']}''',
                message=f'''Hi {{{{fullname}}}},

This submission has fewer than {journal.get_number_of_reviewers()} reviews and fewer than {journal.get_number_of_reviewers()} ACKs. 

Task: {task}
Submission: {submission.content['title']['value']}
Number of days late: {days_late}
Link: https://openreview.net/forum?id={submission.id}

        ''',
                replyTo=journal.contact_info, 
                signature=journal.venue_id,
                sender=journal.get_message_sender()
            )      

    