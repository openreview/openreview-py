def process(client, invitation):

    print('Remind invited reviewers')
    journal = openreview.journal.Journal()
    grouped_edges = client.get_grouped_edges(invitation=journal.get_reviewer_invite_assignment_id(), label='Invitation Sent', groupby='id')
    
    if len(grouped_edges) == 0:
        return
    
    edges = [openreview.api.Edge.from_json(edge['values'][0]) for edge in grouped_edges]

    start_reminder_period = openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(weeks = journal.invite_assignment_reminder_period, days=1))
    end_reminder_period = openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(weeks = journal.invite_assignment_reminder_period))
    one_week = datetime.timedelta(weeks=1)
    
    print(f'reminder period between {start_reminder_period} and {end_reminder_period}')
    for edge in edges:
        if start_reminder_period < edge.tcdate and edge.tcdate < end_reminder_period:

            notes=client.get_notes(id=edge.head)
            if not notes:
                continue
            submission=notes[0]
            user = edge.tail
            user_profile=openreview.tools.get_profile(client, user)

            if not user_profile:
                user_profile=openreview.Profile(id=user,
                    content={
                        'names': [],
                        'emails': [user],
                        'preferredEmail': user
                    })
                
            last_modified = datetime.timedelta(milliseconds=edge.tmdate - edge.tcdate)

            if last_modified < one_week:
                subject=f'[{journal.short_name}] Invitation to review paper titled "{submission.content["title"]["value"]}"'

                previous_message = client.get_messages(to=user_profile.get_preferred_email(), subject=subject)
                if previous_message:
                    print(f"remind: {edge.tail}")
                    reminder_subject = f'[{journal.short_name}] Reminder: Invitation to review paper titled "{submission.content["title"]["value"]}"'
                    replace_sentence = f'''Please note that responding to this email will direct your reply to {previous_message[0]['content']['replyTo']}.'''
                    message = previous_message[0]['content']['text'].replace(replace_sentence, '')
                    client.post_message(reminder_subject, [user_profile.id], message, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, replyTo=previous_message[0]['content']['replyTo'], sender=journal.get_message_sender())
                    ## update edge to reset the reminder counter
                    client.post_edge(edge)
            else:
                print('User was just reminded!')