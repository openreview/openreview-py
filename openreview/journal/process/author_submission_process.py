def process(client, edit, invitation):
    venue_id = '.TMLR'
    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()

    ## setup author submission invitations
    journal.setup_author_submission(note)

    ## send email to authors
    client.post_message(
        recipients=note.signatures,
        subject=f'[{journal.short_name}] Suggest candidate Action Editor for your new TMLR submission',
        message=f'''Hi {{{{fullname}}}},

Thank you for submitting to TMLR your work titled "{note.content['title']['value']}".

Before the review process starts, we need you to submit one or more recommendations for an Action Editor that you believe has the expertise to oversee the evaluation of your work.

To do so, please follow this link: https://openreview.net/invitation?id={journal.get_ae_recommendation_id(number=note.number)} or check your tasks in the Author Console: https://openreview.net/group?id=.TMLR/Authors

For more details and guidelines on the TMLR review process, visit jmlr.org/tmlr.

The TMLR Editors-in-Chief
''',
        replyTo=journal.contact_info
    )