def process(client, invitation):

    journal = openreview.journal.Journal()

    forum = client.get_note(invitation.edit['note']['forum'])
    duedate = datetime.datetime.fromtimestamp(invitation.duedate/1000)
    now = datetime.datetime.now()
    task = invitation.pretty_id()

    late_invitees = journal.get_late_invitees(invitation.id)

    if len(late_invitees) == 0:
      return

    if days_late_map:
        days_late = days_late_map.get(str(date_index), abs((now - duedate).days))
    else:
        days_late = abs((now - duedate).days)

    invitee = late_invitees[0]
    official_reviewer = client.get_groups(member=invitee, id=journal.get_reviewers_id())

    if not official_reviewer:
        print('Reviewer is no longer an official reviewer')
        return
    
    ## send email to reviewers
    print('send email to reviewers', late_invitees)
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=late_invitees,
        subject=f'''[{journal.short_name}] You are late in performing a task: {task}''',
        message=f'''Hi {{{{fullname}}}},

Our records show that you are late on the current task:

Task: {task}
Number of days late: {days_late}
Link: https://openreview.net/forum?id={forum.id}

Please follow the provided link and complete your task ASAP.

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )