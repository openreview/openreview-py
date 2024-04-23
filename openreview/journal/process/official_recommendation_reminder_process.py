def process(client, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(invitation.edit['note']['forum']['value'])
    duedate = datetime.datetime.fromtimestamp(invitation.duedate/1000)
    now = datetime.datetime.utcnow()
    task = 'Official Recommendation'

    reviews = client.get_notes(forum=submission.id, invitation=invitation.id)
    signatures = [r.signatures[0] for r in reviews]

    ## send email to reviewers
    print('send email to reviewers')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_reviewers_id(number=submission.number)],
        ignoreRecipients=signatures,
        subject=f'''[{journal.short_name}] You are late in performing a task for assigned paper {submission.number}: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

Our records show that you are late on the current reviewing task:

  Task: {task}
  Submission: {submission.content['title']['value']}
  Number of days late: {abs((now - duedate).days)}
  Link: https://openreview/forum?id={submission.id}

Please follow the provided link and complete your task ASAP.

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info, 
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )