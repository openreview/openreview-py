def process(client, invitation):
    
    print('Remind action editors')
    journal = openreview.journal.Journal()
    edges = client.get_edges(invitation=journal.get_ae_availability_id(), label='Unavailable')
    reminder_period = openreview.tools.datetime_millis(datetime.datetime.utcnow() - datetime.timedelta(weeks = journal.unavailable_reminder_period))

    subject=f'[{journal.short_name}] Unavailable reminder'

    message=f'''Hi {{{{fullname}}}},

Remember to become available again!

The {journal.short_name} Editors-in-Chief
'''


    for edge in edges:
        if edge.tcdate < reminder_period:
            print(f"remind: {edge.tail}")
            recipients=[edge.tail]
            client.post_message(subject, recipients, message, replyTo=journal.contact_info)            

