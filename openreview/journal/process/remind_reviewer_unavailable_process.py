def process(client, invitation):
    
    print('Remind reviewers')
    journal = openreview.journal.Journal()
    grouped_edges = client.get_grouped_edges(invitation=journal.get_reviewer_availability_id(), label='Unavailable', groupby='head')
    if len(grouped_edges) == 0:
        return
    
    edges = [openreview.api.Edge.from_json(e) for e in grouped_edges[0]['values']]
    reminder_period = openreview.tools.datetime_millis(datetime.datetime.utcnow() - datetime.timedelta(weeks = journal.unavailable_reminder_period))

    subject=f'[{journal.short_name}] Consider updating your availability for {journal.short_name}'

    message=f'''Hi {{{{fullname}}}},

It has been a few weeks since you've marked yourself as unavailable to participate in the reviewing process of {journal.short_name}. 

If you are now ready to get back to supporting {journal.short_name}'s review process, please visit the following page to adjust your availability accordingly:

https://openreview.net/group?id={journal.get_reviewers_id()}

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
'''

    print('reminder_period', reminder_period)
    for edge in edges:
        is_reviewer = client.get_groups(member=edge.tail, id=journal.get_reviewers_id())
        if not is_reviewer:
            continue        
        if edge.tmdate < reminder_period:
            print(f"remind: {edge.tail}")
            recipients=[edge.tail]
            client.post_message(subject, recipients, message, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())
            ## update edge to reset the reminder counter
            client.post_edge(edge)

