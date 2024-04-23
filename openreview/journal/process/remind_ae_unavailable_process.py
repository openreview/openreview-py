def process(client, invitation):
    
    print('Remind action editors')
    journal = openreview.journal.Journal()
    grouped_edges = client.get_grouped_edges(invitation=journal.get_ae_availability_id(), label='Unavailable', groupby='head')
    
    if len(grouped_edges) == 0:
        return
    
    edges = [openreview.api.Edge.from_json(e) for e in grouped_edges[0]['values']]
    reminder_period = openreview.tools.datetime_millis(datetime.datetime.utcnow() - datetime.timedelta(weeks = journal.unavailable_reminder_period))
    back_to_available_period = openreview.tools.datetime_millis(datetime.datetime.utcnow() - datetime.timedelta(weeks = 2 * journal.unavailable_reminder_period))

    reminder_subject=f'[{journal.short_name}] Consider updating your availability for {journal.short_name}'

    reminder_message=f'''Hi {{{{fullname}}}},

It has been {journal.unavailable_reminder_period} weeks since you've marked yourself as unavailable to participate in the reviewing process of {journal.short_name}. 

If you are now ready to get back to supporting {journal.short_name}'s review process, please visit the following page to adjust your availability accordingly:

https://openreview.net/group?id={journal.get_action_editors_id()}

**Note that in {journal.unavailable_reminder_period} more weeks, if you are still unavailable, we will automatically revert back your status to available.**

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
'''

    available_subject=f'[{journal.short_name}] Your status has been changed to "Available"'
    available_message=f'''Hi {{{{fullname}}}},

It has been {2 * journal.unavailable_reminder_period} weeks since you've marked yourself as unavailable to participate in the reviewing process of {journal.short_name}. 

We have therefore automatically reverted you back to the Available status.

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
'''

    print('reminder_period', reminder_period)
    for edge in edges:
        is_ae = client.get_groups(member=edge.tail, id=journal.get_action_editors_id())
        if not is_ae:
            continue
        recipients=[edge.tail]
        if edge.tmdate < back_to_available_period:
            print(f"back to available: {edge.tail}")
            edge.label = 'Available'
            client.post_edge(edge)
            client.post_message(available_subject, recipients, available_message, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())
        elif edge.tmdate < reminder_period:
            print(f"check if we need to remind: {edge.tail}")
            profile = client.get_profile(edge.tail)
            messages = client.get_messages(to=profile.get_preferred_email(), subject=reminder_subject)
            if len(messages) > 0 and messages[0]['cdate'] > reminder_period:
                print(f"already reminded: {edge.tail} on {messages[0]['cdate']}, no action needed")
            else:
                print(f"remind: {edge.tail}")
                client.post_message(reminder_subject, recipients, reminder_message, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())


