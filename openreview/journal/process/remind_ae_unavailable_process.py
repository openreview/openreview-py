def process(client, invitation):
    
    print('Remind action editors')
    journal = openreview.journal.Journal()
    edges = client.get_edges(invitation=journal.get_ae_availability_id(), label='Unavailable')
    reminder_period = openreview.tools.datetime_millis(datetime.datetime.utcnow() - datetime.timedelta(weeks = journal.unavailable_reminder_period))

    subject=f'[{journal.short_name}] Consider updating your availability for {journal.short_name}'

    message=f'''Hi {{{{fullname}}}},

It has been a few weeks since you've marked yourself as unavailable to participate in the reviewing process of {journal.short_name}. 

If you are now ready to get back to supporting {journal.short_name}'s review process, please visit the following page to adjust your availability accordingly:

https://openreview.net/group?id={journal.get_action_editors_id()}

We thank you for your cooperation.

The {journal.short_name} Editors-in-Chief
'''

    print('reminder_period', reminder_period)
    for edge in edges:
        if edge.tmdate < reminder_period:
            print(f"remind: {edge.tail}")
            recipients=[edge.tail]
            client.post_message(subject, recipients, message, replyTo=journal.contact_info)
            ## update edge to reset the reminder counter
            client.post_edge(edge)


