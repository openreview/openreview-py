def process(client, invitation):

    print('Remind invited reviewers')
    journal = openreview.journal.Journal()
    grouped_edges = client.get_grouped_edges(invitation=journal.get_reviewer_invite_assignment_id(), label='Invitation Sent', groupby='id', domain=journal.venue_id)
    
    if len(grouped_edges) == 0:
        return
    
    edges = [openreview.api.Edge.from_json(edge['values'][0]) for edge in grouped_edges]

    recruitment_invitation_id = journal.get_reviewer_assignment_recruitment_id()
    invite_assignment_template = client.get_group(journal.get_reviewers_id()).content['invitation_assignment_email_template_script']['value']

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
            user_id = user_profile.id if user_profile else user
            user_preferred_name = user_profile.get_preferred_name(pretty=True) if user_profile else user

            last_modified = datetime.timedelta(milliseconds=edge.tmdate - edge.tcdate)

            if last_modified < one_week:
                print(f"remind: {edge.tail}")
                hashkey = openreview.tools.get_user_hash_key(user, journal.secret_key)
                invitation_url = f'https://openreview.net/invitation?id={recruitment_invitation_id}&user={user}&key={hashkey}&submission_id={submission.id}&inviter={edge.signatures[0]}'
                invitation_links = f'''Please respond the invitation clicking the following link:

{invitation_url}'''
                message = invite_assignment_template.format(
                    user_preferred_name=user_preferred_name,
                    submission_number=submission.number,
                    submission_title=submission.content['title']['value'],
                    submission_abstract=submission.content['abstract']['value'],
                    invitation_links=invitation_links,
                    inviter_id=openreview.tools.pretty_id(edge.signatures[0]),
                    inviter_preferred_name=''
                )
                reminder_subject = f'[{journal.short_name}] Reminder: Invitation to review paper titled "{submission.content["title"]["value"]}"'
                client.post_message(reminder_subject, [user_id], message, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())
                ## update edge to reset the reminder counter
                client.post_edge(edge)
            else:
                print('User was just reminded!')