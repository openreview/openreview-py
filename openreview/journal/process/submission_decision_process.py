def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note=edit.note

    if note.content['recommendation']['value'] != 'Reject':
        journal.invitation_builder.set_camera_ready_revision_invitation(journal, note)

    duedate = openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(days = 7))
    submission = client.get_note(note.forum)
    journal.invitation_builder.set_acceptance_invitation(journal, submission, note.content.get('certifications', {}).get('value', []), duedate)
