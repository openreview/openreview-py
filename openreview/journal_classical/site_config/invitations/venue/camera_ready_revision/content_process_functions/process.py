def process(client, edit, invitation):

    import datetime

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    venue_id = journal.venue_id
    editors_in_chief_id = f'{venue_id}/Editors_In_Chief'
    super_child_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/super_invitation_child_edit.py}}", super_child_namespace)
    camera_ready_metadata_namespace = {'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/camera_ready_publication_metadata.py}}", camera_ready_metadata_namespace)
    invitation_edit_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/invitation_edit_helpers.py}}", invitation_edit_namespace)

    def set_invitation_expiration_date(invitation_id, expiration_date):
        invitation_edit_namespace['set_invitation_expiration_date'](client, journal, invitation_id, expiration_date)

    def editor_readers(readers):
        if readers == ['everyone']:
            return [editors_in_chief_id]
        return readers + [editors_in_chief_id] if editors_in_chief_id not in readers else readers

    def format_openreview_month_year(timestamp_millis):
        date = datetime.datetime.fromtimestamp(timestamp_millis / 1000.0, datetime.timezone.utc)
        return f'{date.month}/{date.year % 100:02d}'

    def get_content_value(note, field_name):
        return note.content.get(field_name, {}).get('value')

    def split_final_author_list(value):
        import re
        return [part.strip() for part in str(value or '').split(',') if part.strip()]

    def final_author_content(submission):
        final_authors = split_final_author_list(get_content_value(submission, 'final_publication_author_list'))
        if not final_authors:
            return {}
        return {
            'authors': {'value': final_authors},
            'authorids': {'value': final_authors},
            'author_list': {'value': ', '.join(final_authors)}
        }

    def get_previous_submission_from_url(previous_url):
        if not previous_url or previous_url == 'N/A' or 'forum?id=' not in previous_url:
            return None
        note_id = previous_url.split('forum?id=', 1)[1].split('&', 1)[0]
        if not note_id:
            return None
        return client.get_note(note_id)

    def get_submission_chain(submission):
        chain = [submission]
        seen_note_ids = {submission.id}
        current = submission
        while True:
            previous_url = get_content_value(current, 'previous_JMLR_submission_URL')
            try:
                previous = get_previous_submission_from_url(previous_url)
            except Exception as error:
                print(f'Could not resolve previous submission for camera-ready verification guidance: {error}')
                return chain
            if not previous or previous.id in seen_note_ids:
                return chain
            chain.append(previous)
            seen_note_ids.add(previous.id)
            current = previous

    def build_jmlr_publication_id(year, paper_number):
        return f'{year % 100:02d}-{paper_number % 100000:05d}'

    def build_openreview_dates_block(submission, decision):
        chain = get_submission_chain(submission)
        original_submission = chain[-1]
        first_revision = chain[-2] if len(chain) > 1 else None
        accepted_timestamp = decision.tcdate or decision.cdate
        submitted = format_openreview_month_year(original_submission.tcdate or original_submission.cdate)
        revised = format_openreview_month_year((first_revision.tcdate or first_revision.cdate) if first_revision else accepted_timestamp)
        accepted = format_openreview_month_year(accepted_timestamp)
        year = datetime.datetime.fromtimestamp(accepted_timestamp / 1000.0, datetime.timezone.utc).year
        paper_id = build_jmlr_publication_id(year, submission.number)
        volume = (year % 100) + 1
        return {
            'block': (
            '\\jmlropenreviewdates{\n'
            f'  submitted = {{{submitted}}},\n'
            f'  revised = {{{revised}}},\n'
            f'  accepted = {{{accepted}}},\n'
            f'  paperid = {{{paper_id}}}\n'
            '}'
            ),
            'submitted': submitted,
            'revised': revised,
            'accepted': accepted,
            'paper_id': paper_id,
            'volume': volume,
            'year': year
        }

    def update_camera_ready_verification_guidance(submission):
        decisions = client.get_notes(invitation=journal.get_ae_decision_id(number=submission.number))
        if not decisions:
            return
        decision = decisions[0]
        invitation_id = f'{venue_id}/Paper{submission.number}/-/Camera_Ready_Verification'
        metadata = camera_ready_metadata_namespace['build_openreview_date_metadata'](client, submission, decision)
        guidance = (
            '\n\nPaper-specific first-page checks:\n'
            f'- Header: Journal of Machine Learning Research {metadata["volume"]} ({metadata["year"]}) '
            f'1-[last page] ... Submitted {metadata["submitted"]}; Revised {metadata["revised"]}; Published {metadata["accepted"]}.\n'
            '- Dates and paper id: use the generated OpenReview-aware JMLR metadata; the Published date is the acceptance decision date.\n'
            '- Page range: page numbers start from 1 and [last page] is the actual final page number of the uploaded PDF.\n'
            '- Author line: author names and order match the approved Final Publication Author List recorded on this OpenReview paper.\n'
            f'- Footer URL: http://jmlr.org/papers/v{metadata["volume"]}/{metadata["paper_id"]}.html.'
        )
        try:
            verification_invitation = client.get_invitation(invitation_id)
            verification_field = verification_invitation.edit['note']['content']['verification']
            base_description = verification_field.get('description', '').split('\n\nPaper-specific first-page checks:', 1)[0]
            base_description = base_description.split(' The entire rendered first-page header should match:', 1)[0].rstrip()
            verification_field['description'] = base_description + guidance
            client.post_invitation_edit(
                invitations=journal.get_meta_invitation_id(),
                signatures=[venue_id],
                invitation=verification_invitation,
                replacement=True
            )
        except Exception as error:
            print(f'Could not update camera-ready verification guidance for {invitation_id}: {error}')

    duedate = journal.get_due_date(weeks=journal.get_camera_ready_verification_period_length())
    submission = client.get_note(edit.note.id)

    if not journal.is_submission_public() and journal.has_publication_chairs():
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            note=openreview.api.Note(
                id=submission.id,
                readers={
                    'add': [journal.get_publication_chairs_id()]
                }
            )
        )

    print('Enable Camera Ready Verification')
    now = openreview.tools.datetime_millis(datetime.datetime.now())
    try:
        set_invitation_expiration_date(f'{venue_id}/Paper{submission.number}/-/Camera_Ready_Revision', now)
    except Exception as error:
        print(f'Could not expire current camera-ready revision invitation: {error}')
    try:
        set_invitation_expiration_date(f'{venue_id}/Paper{submission.number}/-/Camera_Ready_Verification', now)
    except Exception as error:
        print(f'Could not expire previous camera-ready verification invitation: {error}')
    super_child_namespace['refresh_camera_ready_verification_invitation'](client, journal, submission, duedate)
    update_camera_ready_verification_guidance(submission)

    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        readers=editor_readers(journal.get_under_review_submission_readers(submission.number)),
        writers=[venue_id],
        signatures=[venue_id],
        note=openreview.api.Note(
            id=submission.id,
            writers=[editors_in_chief_id]
        )
    )

    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        readers=editor_readers(journal.get_under_review_submission_readers(submission.number)),
        writers=[venue_id],
        signatures=[venue_id],
        note=openreview.api.Note(
            id=submission.id,
            content={
                **final_author_content(submission),
                'camera_ready_revision_action': {
                    'delete': True
                },
                'venue': {
                    'value': f'Camera-ready check pending for {journal.short_name}'
                },
                'venueid': {
                    'value': f'{venue_id}/Camera_Ready_Check_Pending'
                }
            }
        )
    )

    print('Send email to AE')
    ae_group = client.get_group(journal.get_action_editors_id())
    message = ae_group.content['camera_ready_verification_email_template_script']['value'].format(
        short_name=journal.short_name,
        submission_number=submission.number,
        submission_title=submission.content['title']['value'],
        invitation_url=f'{{SITE_URL}}/forum?id={submission.id}&invitationId={journal.get_camera_ready_verification_id(number=submission.number)}',
        contact_info=journal.contact_info
    )
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Review camera ready version for {journal.short_name} paper {submission.number}: {submission.content['title']['value']}''',
        message=message,
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
