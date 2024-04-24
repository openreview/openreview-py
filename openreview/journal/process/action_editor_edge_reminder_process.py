def process(client, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(invitation.edit['head']['param']['const'])
    duedate = datetime.datetime.fromtimestamp(invitation.duedate/1000)
    now = datetime.datetime.utcnow()
    task = "Reviewer Assignment"

    edges = client.get_edges(invitation=journal.get_reviewer_assignment_id(), head=submission.id)

    if len(edges) >= journal.get_number_of_reviewers():
      return

    if date_index == 0 or date_index == 1:
        print('send email to action editors')
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_action_editors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] You are late in performing a task for assigned paper {submission.number}: {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

Our records show that you are late on the current action editor task:

Task: {task}
Submission: {submission.content['title']['value']}
Number of days late: {abs((now - duedate).days)}
Link: https://openreview.net/group?id={journal.get_action_editors_id()}#action-editor-tasks

Please follow the provided link and complete your task ASAP.

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
''',
            replyTo=journal.contact_info,
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

    if date_index == 1 or date_index == 2:
      ## get preferred names
      action_editor_group = client.get_group(journal.get_action_editors_id(number=submission.number))
      profiles = openreview.tools.get_profiles(client, action_editor_group.members)
      days_late = 'one week' if date_index == 1 else 'one month'
      ## send email to editors in chief
      print('send email to editors in chief')
      for profile in profiles:
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_editors_in_chief_id()],
            ignoreRecipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] AE is late in performing a task for assigned paper {submission.number}: {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

Our records show that the AE for submission {submission.number}: {submission.content['title']['value']} is *{days_late}* late on an AE task::

Task: {task}
AE: {profile.get_preferred_name(pretty=True)}
Link: https://openreview.net/group?id={journal.get_action_editors_id()}#action-editor-tasks

OpenReview Team
''',
            replyTo=journal.contact_info,
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )