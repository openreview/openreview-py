def process(client, edit, invitation):
    venue_id = ''
    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    ## setup author submission invitations
    journal.setup_author_submission(note)

    ## send email to authors
    client.post_message(
        recipients=note.signatures,
        subject=journal.get_message('author_submission_subject'),
        message=journal.get_message('author_submission_message', { 
            '{{submission_title}}': note.content['title']['value'], 
            '{{action_editor_recommendation_id}}': journal.get_ae_recommendation_id(number=note.number)
        }),
        replyTo=journal.contact_info
    )