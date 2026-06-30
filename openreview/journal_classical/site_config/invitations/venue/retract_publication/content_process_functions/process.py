def process(client, edit, invitation):

    import datetime

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    venue_id = journal.venue_id
    submission = client.get_note(edit.note.forum)
    invitation_edit_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/invitation_edit_helpers.py}}", invitation_edit_namespace)

    def set_invitation_expiration_date(invitation_id, expiration_date):
        invitation_edit_namespace['set_invitation_expiration_date'](client, journal, invitation_id, expiration_date)

    if submission.content.get('venueid', {}).get('value') != f'{venue_id}/Camera_Ready_Published':
        raise openreview.OpenReviewException('Only camera-ready published papers can be retracted.')

    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        readers=[
            f'{venue_id}/Editors_In_Chief',
            f'{venue_id}/Production_Editors',
            f'{venue_id}/Paper{submission.number}/Authors',
            f'{venue_id}/Paper{submission.number}/Action_Editors',
            f'{venue_id}/Paper{submission.number}/Reviewers'
        ],
        writers=[venue_id],
        signatures=[venue_id],
        note=openreview.api.Note(
            id=submission.id,
            content={
                'venue': {
                    'value': f'Publication retracted in {journal.short_name}'
                },
                'venueid': {
                    'value': f'{venue_id}/Publication_Retracted'
                }
            }
        )
    )

    try:
        set_invitation_expiration_date(
            f'{venue_id}/Paper{submission.number}/-/Retract_Publication',
            openreview.tools.datetime_millis(datetime.datetime.now())
        )
    except Exception as error:
        print(f'Could not expire retract-publication invitation: {error}')
