def process(client, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(invitation.edit['note']['forum'])
    duedate = datetime.datetime.fromtimestamp(invitation.duedate/1000)
    now = datetime.datetime.utcnow()
    task = invitation.pretty_id()

    replies = client.get_notes(invitation=invitation.id)

    if replies:
      return

    if days_late_map:
        days_late = days_late_map.get(str(date_index), abs((now - duedate).days))
    else:
        days_late = abs((now - duedate).days)
    
    ## send email to eics
    print('send email to eics')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_editors_in_chief_id()],
        subject=f'''[{journal.short_name}] You are late in performing a task for the paper {submission.number}: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

Our records show that you are late on the current task:

Task: {task}
Submission: {submission.content['title']['value']}
Number of days late: {days_late}
Link: https://openreview.net/forum?id={submission.id}

Please follow the provided link and complete your task ASAP.

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info, 
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )

       

    