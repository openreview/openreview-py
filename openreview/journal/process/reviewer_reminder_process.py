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

    ## send email to reviewers
    if date_index == 0 or date_index == 1:
        print('send email to reviewers', late_invitees)
        client.post_message(
            recipients=late_invitees,
            subject=f'''[{journal.short_name}] You are late in performing a task for assigned paper {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

Our records show that you are late on the current reviewing task:

Task: {task}
Submission: {submission.content['title']['value']}
Number of days late: {abs((now - duedate).days)}
Link: https://openreview.net/forum?id={submission.id}

Please follow the provided link and complete your task ASAP.

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
''',
            replyTo=assigned_action_editor if assigned_action_editor else journal.contact_info
        )

    if date_index == 1 or date_index == 2:
        ## get preferred names
        profiles = openreview.tools.get_profiles(client, late_invitees)
        days_late = 'one week' if date_index == 1 else 'one month'
        ## send email to action editors
        print('send email to action editors')
        for profile in profiles:
            client.post_message(
                recipients=[journal.get_action_editors_id(number=submission.number)],
                subject=f'''[{journal.short_name}] Reviewer is late in performing a task for assigned paper {submission.content['title']['value']}''',
                message=f'''Hi {{{{fullname}}}},

Our records show that a reviewer on a paper you are the AE for is *{days_late}* late on a reviewing task:

Task: {task}
Reviewer: {profile.get_preferred_name(pretty=True)}
Submission: {submission.content['title']['value']}
Link: https://openreview.net/forum?id={submission.id}

Please follow up directly with the reviewer in question to ensure they complete their task ASAP.

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
''',
                replyTo=journal.contact_info
        )

    if date_index == 2:
        profiles = openreview.tools.get_profiles(client, late_invitees)
        for profile in profiles:
            client.post_message(
                recipients=[journal.get_editors_in_chief_id()],
                subject=f'''[{journal.short_name}] Reviewer is late in performing a task for assigned paper {submission.content['title']['value']}''',
                message=f'''Hi {{{{fullname}}}},

Our records show that a reviewer is *one month* late on a reviewing task:

Task: {task}
Reviewer: {profile.get_preferred_name(pretty=True)}
Submission: {submission.content['title']['value']}
Link: https://openreview.net/forum?id={submission.id}

OpenReview Team
''',
                replyTo=journal.contact_info
        )        

    