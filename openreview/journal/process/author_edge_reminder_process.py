def process(client, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(invitation.edit['head']['const'])
    assigned_action_editor = submission.content.get('assigned_action_editor', {}).get('value')
    duedate = datetime.datetime.fromtimestamp(invitation.duedate/1000)
    now = datetime.datetime.utcnow()
    task = invitation.pretty_id()

    late_invitees = journal.get_late_invitees(invitation.id)

    if len(late_invitees) == 0:
      return

    ## send email to authors
    print('send email to reviewers', late_invitees)
    client.post_message(
        recipients=late_invitees,
        subject=f'''[{journal.short_name}] You are late in performing a task for your paper {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

Our records show that you are late on the current task:

  Task: {task}
  Submission: {submission.content['title']['value']}
  Number of days late: {abs((now - duedate).days)}
  Link: https://openreview.net/group?id={journal.get_authors_id()}#author-tasks

Please follow the provided link and complete your task ASAP.

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
''',
        replyTo=assigned_action_editor if assigned_action_editor else journal.contact_info
    )