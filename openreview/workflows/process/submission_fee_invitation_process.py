def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    submission_venue_id = domain.get_content_value('submission_venue_id')

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.edit['invitation']['cdate'] if 'cdate' in invitation.edit['invitation'] else invitation.cdate

    if cdate > now and not client.get_invitations(invitation=invitation.id, limit=1):
        print('The submission fee is not active yet', cdate)
        return

    amount = invitation.get_content_value('amount')
    country_fees = invitation.get_content_value('country_fees') or {}
    waiver_invitation_id = f'{venue_id}/-/{invitation.get_content_value("waiver_name")}'

    submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', domain=venue_id)

    fee_contents = []
    waiver_contents = {}
    for submission in submissions:
        authors = [author for author in submission.content.get('authors', {}).get('value', []) if isinstance(author, dict)]
        countries = [institution.get('country') for author in authors for institution in author.get('institutions') or []]
        every_author_has_an_institution = bool(authors) and all(author.get('institutions') for author in authors)
        every_country_has_a_fee = all(country in country_fees for country in countries)

        submission_amount = amount
        if every_author_has_an_institution and every_country_has_a_fee:
            submission_amount = min(amount, max(country_fees[country] for country in countries))

        if submission_amount == 0:
            waiver_contents[submission.id] = {
                'qualifying_authors': { 'value': [author['username'] for author in authors if author.get('username')] },
                'countries': { 'value': list(dict.fromkeys(countries)) }
            }

        fee_contents.append({
            'noteId': { 'value': submission.id },
            'noteNumber': { 'value': submission.number },
            'amount': { 'value': submission_amount }
        })

    current_fee_invitations = client.get_all_invitations(invitation=invitation.id, domain=venue_id)

    fee_invitation_edits = openreview.tools.concurrent_requests(lambda content: client.post_invitation_edit(
        invitations=invitation.id,
        readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        content=content,
        invitation=openreview.api.Invitation()
    ), fee_contents, desc='submission_fee_invitation_process', max_workers=128, retries=1)
    print(f'{len(fee_invitation_edits)} submission fee invitations created or updated')

    posted_fee_invitation_ids = { fee_invitation_edit['invitation']['id'] for fee_invitation_edit in fee_invitation_edits }
    fee_invitations_to_expire = [fee_invitation for fee_invitation in current_fee_invitations if fee_invitation.id not in posted_fee_invitation_ids and (not fee_invitation.expdate or fee_invitation.expdate > now)]
    openreview.tools.concurrent_requests(lambda fee_invitation: client.post_invitation_edit(
        invitations=meta_invitation_id,
        readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=fee_invitation.id,
            signatures=[venue_id],
            duedate=now if fee_invitation.duedate and fee_invitation.duedate > now else None,
            expdate=now
        )
    ), fee_invitations_to_expire, desc='expire_submission_fee_invitations', max_workers=128, retries=1)
    print(f'{len(fee_invitations_to_expire)} submission fee invitations of inactive submissions expired')

    if not waiver_contents:
        return

    if not openreview.tools.get_invitation(client, waiver_invitation_id):
        raise openreview.OpenReviewException(f'{len(waiver_contents)} submissions have a fee of 0, but {waiver_invitation_id} does not exist to waive them. Enable it and edit the submission fee dates to waive these fees.')

    settled_note_ids = { payment.note for payment in client.get_all_payments(domain=venue_id) if payment.status in ['paid', 'waived'] }
    waived_note_ids = { waiver_note.forum for waiver_note in client.get_all_notes(invitation=waiver_invitation_id) }

    waiver_note_ids = [note_id for note_id in waiver_contents if note_id not in settled_note_ids and note_id not in waived_note_ids]
    for note_id in waiver_note_ids:
        try:
            client.post_note_edit(
                invitation=waiver_invitation_id,
                signatures=[venue_id],
                note=openreview.api.Note(
                    forum=note_id,
                    replyto=note_id,
                    content=waiver_contents[note_id]
                )
            )
        except openreview.OpenReviewException as error:
            if 'The submission fee of this submission is already' not in str(error):
                raise error
            print(f'The fee of {note_id} is already settled or being waived')
    print(f'{len(waiver_note_ids)} submission fees waived')
