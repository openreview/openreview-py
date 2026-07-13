def process(client, edit, invitation):

    import datetime

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    venue_id = journal.venue_id
    submission = client.get_note(edit.note.forum)
    invitation_edit_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/invitation_edit_helpers.py}}", invitation_edit_namespace)

    def get_content_value(note, field_name):
        return note.content.get(field_name, {}).get('value')

    def publication_urls(note):
        metadata = get_content_value(note, 'publication_metadata') or {}
        paper_id = metadata.get('id')
        volume = metadata.get('volume')
        if not paper_id or not volume:
            raise openreview.OpenReviewException('Publication metadata must include id and volume before marking the paper as published.')
        return {
            'abstract': f'https://www.jmlr.org/papers/v{volume}/{paper_id}.html',
            'pdf': f'https://www.jmlr.org/papers/volume{volume}/{paper_id}/{paper_id}.pdf'
        }

    def set_invitation_expiration_date(invitation_id, expiration_date):
        invitation_edit_namespace['set_invitation_expiration_date'](client, journal, invitation_id, expiration_date)

    def set_retract_publication_invitation():
        client.post_invitation_edit(
            invitations=f'{venue_id}/-/Retract_Publication',
            readers=[journal.get_editors_in_chief_id()],
            writers=[venue_id],
            signatures=[venue_id],
            content={
                'noteNumber': {'value': submission.number},
                'noteId': {'value': submission.id}
            }
        )

    def public_file_content():
        content = {
            'pdf': {
                'readers': {'delete': True}
            }
        }
        if get_content_value(submission, 'supplementary_material'):
            content['supplementary_material'] = {
                'readers': {'delete': True}
            }
        return content

    if submission.content.get('venueid', {}).get('value') != f'{venue_id}/Camera_Ready_Approved':
        raise openreview.OpenReviewException('Only camera-ready approved papers can be marked as published.')
    urls = publication_urls(submission)
    now = openreview.tools.datetime_millis(datetime.datetime.now())

    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        readers=['everyone'],
        nonreaders=[],
        writers=[venue_id],
        signatures=[venue_id],
        note=openreview.api.Note(
            id=submission.id,
            readers=['everyone'],
            nonreaders=[],
            odate=now if submission.odate is None else None,
            pdate=now if submission.pdate is None else None,
            content={
                'venue': {
                    'value': f'Camera-ready published in {journal.short_name}'
                },
                'venueid': {
                    'value': f'{venue_id}/Camera_Ready_Published'
                },
                'download_publication_files_action': {
                    'delete': True
                }
            }
        )
    )
    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        note=openreview.api.Note(
            id=submission.id,
            content=public_file_content()
        )
    )

    try:
        legacy_mark_published_suffix = 'Mark_' + 'Camera_Ready_Published'
        for mark_published_invitation_id in [
            f'{venue_id}/Paper{submission.number}/-/Mark_as_Published',
            f'{venue_id}/Paper{submission.number}/-/{legacy_mark_published_suffix}',
            f'{venue_id}/Paper{submission.number}/-/Download_Publication_Files',
        ]:
            set_invitation_expiration_date(mark_published_invitation_id, now)
    except Exception as error:
        print(f'Could not expire mark-published invitation: {error}')

    try:
        set_retract_publication_invitation()
    except Exception as error:
        print(f'Could not create retract-publication invitation: {error}')

    try:
        author_group = client.get_group(journal.get_authors_id())
        template = author_group.content['publication_published_email_template_script']['value']
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Paper {submission.number} has been published: {submission.content['title']['value']}''',
            message=template.format(
                short_name=journal.short_name,
                submission_id=submission.id,
                submission_number=submission.number,
                submission_title=submission.content['title']['value'],
                paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
                jmlr_publication_url=urls['abstract'],
                jmlr_pdf_url=urls['pdf'],
                contact_info=journal.contact_info
            ),
            replyTo=journal.contact_info,
            signature=venue_id,
            sender=journal.get_message_sender()
        )
    except Exception as error:
        print(f'Could not send publication email to authors: {error}')
