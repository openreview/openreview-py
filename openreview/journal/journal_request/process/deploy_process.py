def process(client, edit, invitation):

    SUPPORT_GROUP = ''

    forum = client.get_note(edit.note.id)
    venue_id = forum.content['venue_id']['value']
    secret_key = forum.content['secret_key']['value']
    contact_info = forum.content['contact_info']['value']
    full_name = forum.content['official_venue_name']['value']
    short_name = forum.content['abbreviated_venue_name']['value']
    support_role = forum.content['support_role']['value']
    editors = forum.content['editors']['value']

    journal = openreview.journal.Journal(client, venue_id, secret_key, contact_info, full_name, short_name)

    journal.setup(support_role, editors)

    journal_request = openreview.JournalRequest(client, SUPPORT_GROUP)
    journal_request.setup_recruitment_invitation(edit.note.id)