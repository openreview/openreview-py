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
    
    ## send email to reviewers
    print('send email to authors', late_invitees)
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=late_invitees,
        subject=f'''[{journal.short_name}] You are late in performing a task for your paper {submission.number}: {submission.content['title']['value']}''',
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
        replyTo=assigned_action_editor if assigned_action_editor else journal.contact_info, 
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )

    ## send email to AE
    if date_index > 0:
        ## get preferred names
        profiles = openreview.tools.get_profiles(client, late_invitees)
        ## send email to action editors
        print('send email to action editors')
        for profile in profiles:
            client.post_message(
                invitation=journal.get_meta_invitation_id(),
                recipients=[journal.get_action_editors_id(number=submission.number)],
                subject=f'''[{journal.short_name}] Authors are late in performing a task for their paper {submission.number}: {submission.content['title']['value']}''',
                message=f'''Hi {{{{fullname}}}},

Our records show that authors of a paper you are the AE for are *{days_late}* late on a task:

Task: {task}
Reviewer: {profile.get_preferred_name(pretty=True)}
Submission: {submission.content['title']['value']}
Link: https://openreview.net/forum?id={submission.id}

Please follow up directly with the authors in question to ensure they complete their task ASAP.

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
''',
                replyTo=journal.contact_info, 
                signature=journal.venue_id,
                sender=journal.get_message_sender()
        )

    ## send email to EICs
    if date_index > 2 or days_late == 'one month':
        profiles = openreview.tools.get_profiles(client, late_invitees)
        for profile in profiles:
            client.post_message(
                invitation=journal.get_meta_invitation_id(),
                recipients=[journal.get_editors_in_chief_id()],
                ignoreRecipients=[journal.get_authors_id(number=submission.number)],
                subject=f'''[{journal.short_name}] Authors are late in performing a task for their paper {submission.number}: {submission.content['title']['value']}''',
                message=f'''Hi {{{{fullname}}}},

Our records show that authors are *{days_late}* late on a task:

Task: {task}
Reviewer: {profile.get_preferred_name(pretty=True)}
Submission: {submission.content['title']['value']}
Link: https://openreview.net/forum?id={submission.id}

OpenReview Team
''',
                replyTo=journal.contact_info, 
                signature=journal.venue_id,
                sender=journal.get_message_sender()
        )        

    