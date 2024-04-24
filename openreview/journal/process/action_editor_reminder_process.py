def process(client, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(invitation.edit['note']['forum'])
    duedate = datetime.datetime.fromtimestamp(invitation.duedate/1000)
    now = datetime.datetime.utcnow()
    task = invitation.pretty_id()

    late_invitees = journal.get_late_invitees(invitation.id)

    if len(late_invitees) == 0:
      return

    ## get preferred names
    profiles = openreview.tools.get_profiles(client, late_invitees)

    if date_index == 0 or date_index == 1:
        print('send email to action editors', late_invitees)
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=late_invitees,
            subject=f'''[{journal.short_name}] You are late in performing a task for assigned paper {submission.number}: {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

Our records show that you are late on the current action editor task:

Task: {task}
Submission: {submission.content['title']['value']}
Number of days late: {abs((now - duedate).days)}
Link: https://openreview.net/forum?id={submission.id}

Please follow the provided link and complete your task ASAP.

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
''',
            replyTo=journal.contact_info,
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

    if date_index == 1 or date_index == 2:
      ## send email to editors in chief
      print('send email to editors in chief')
      days_late = 'one week' if date_index == 1 else 'one month'
      for profile in profiles:
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_editors_in_chief_id()],
            ignoreRecipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] AE is late in performing a task for assigned paper {submission.number}: {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

Our records show that the AE for submission {submission.number}: {submission.content['title']['value']} is *{days_late}* late on an AE task:

Task: {task}
AE: {profile.get_preferred_name(pretty=True)}
Link: https://openreview.net/forum?id={submission.id}

OpenReview Team
''',
            replyTo=journal.contact_info,
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )                    



