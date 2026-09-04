def process(client, edit, invitation):

    SUPPORT_GROUP = ''

    note = client.get_note(edit.note.id)

    ## create the Revision invitation so the editors can edit their pending request
    journal_request = openreview.journal.JournalRequest(client, SUPPORT_GROUP)
    journal_request.setup_revision_invitation(note.id)

    baseurl = openreview.tools.get_site_url(client)

    client.post_message(
        invitation=f'{SUPPORT_GROUP}/-/Edit',
        signature=SUPPORT_GROUP,
        recipients=note.content['editors']['value'],
        subject='Your journal request has been received.',
        message=f'''Thank you for choosing OpenReview to host your journal. We are reviewing your request and will contact you when the journal is deployed.

You can access your request here: {baseurl}/forum?id={note.id}

Best,

The OpenReview Team'''
    )
