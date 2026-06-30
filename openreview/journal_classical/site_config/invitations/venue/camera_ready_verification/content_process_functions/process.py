def format_openreview_month_year(timestamp_millis):
    date = datetime.datetime.fromtimestamp(timestamp_millis / 1000.0, datetime.timezone.utc)
    return f'{date.month}/{date.year % 100:02d}'


invitation_edit_namespace = {'openreview': openreview}
exec("{{PYTHON_SCRIPT_JSON:invitations/venue/invitation_edit_helpers.py}}", invitation_edit_namespace)
set_invitation_expiration_date = invitation_edit_namespace['set_invitation_expiration_date']


def get_content_value(note, field_name):
    return note.content.get(field_name, {}).get('value')


def get_previous_submission_from_url(client, previous_url):
    if not previous_url or previous_url == 'N/A' or 'forum?id=' not in previous_url:
        return None
    note_id = previous_url.split('forum?id=', 1)[1].split('&', 1)[0]
    if not note_id:
        return None
    return client.get_note(note_id)


def get_submission_chain(client, submission):
    chain = [submission]
    seen_note_ids = {submission.id}
    current = submission
    while True:
        previous_url = get_content_value(current, 'previous_JMLR_submission_URL')
        try:
            previous = get_previous_submission_from_url(client, previous_url)
        except Exception as error:
            print(f'Could not resolve previous submission for camera-ready dates: {error}')
            return chain
        if not previous or previous.id in seen_note_ids:
            return chain
        chain.append(previous)
        seen_note_ids.add(previous.id)
        current = previous


def build_openreview_dates_block(client, submission, decision):
    metadata = build_openreview_date_metadata(client, submission, decision)
    paper_id = build_jmlr_publication_id(metadata['year'], submission.number)
    return (
        '\\jmlropenreviewdates{\n'
        f'  submitted = {{{metadata["submitted"]}}},\n'
        f'  revised = {{{metadata["revised"]}}},\n'
        f'  accepted = {{{metadata["accepted"]}}},\n'
        f'  paperid = {{{paper_id}}}\n'
        '}'
    )


def build_openreview_date_metadata(client, submission, decision):
    chain = get_submission_chain(client, submission)
    original_submission = chain[-1]
    first_revision = chain[-2] if len(chain) > 1 else None
    accepted_timestamp = decision.tcdate or decision.cdate
    submitted = format_openreview_month_year(original_submission.tcdate or original_submission.cdate)
    revised = format_openreview_month_year((first_revision.tcdate or first_revision.cdate) if first_revision else accepted_timestamp)
    accepted = format_openreview_month_year(accepted_timestamp)
    return {
        'submitted': submitted,
        'revised': revised,
        'accepted': accepted,
        'accepted_timestamp': accepted_timestamp,
        'year': datetime.datetime.fromtimestamp(accepted_timestamp / 1000.0, datetime.timezone.utc).year
    }


def split_final_author_list(value):
    import re
    return [part.strip() for part in str(value or '').split(',') if part.strip()]


def build_jmlr_publication_id(year, paper_number):
    return f'{year % 100:02d}-{paper_number % 100000:05d}'


def build_publication_metadata(client, submission, decision):
    date_metadata = build_openreview_date_metadata(client, submission, decision)
    year = date_metadata['year']
    final_authors = split_final_author_list(get_content_value(submission, 'final_publication_author_list'))
    authorids = get_content_value(submission, 'authorids') or []
    return {
        'id': build_jmlr_publication_id(year, submission.number),
        'issue': submission.number,
        'volume': (year % 100) + 1,
        'title': get_content_value(submission, 'title') or '',
        'abstract': get_content_value(submission, 'abstract') or '',
        'authors': final_authors,
        'emails': ['' for _ in final_authors] if final_authors else ['' for _ in authorids],
        'pages': [1, None],
        'year': year,
        'submitted': date_metadata['submitted'],
        'revised': date_metadata['revised'],
        'accepted': date_metadata['accepted']
    }


camera_ready_metadata_namespace = {'datetime': datetime}
exec("{{PYTHON_SCRIPT_JSON:invitations/venue/camera_ready_publication_metadata.py}}", camera_ready_metadata_namespace)
build_openreview_date_metadata = camera_ready_metadata_namespace['build_openreview_date_metadata']
build_openreview_dates_block = camera_ready_metadata_namespace['build_openreview_dates_block']
build_jmlr_publication_id = camera_ready_metadata_namespace['build_jmlr_publication_id']
build_publication_metadata = camera_ready_metadata_namespace['build_publication_metadata']
split_final_author_list = camera_ready_metadata_namespace['split_final_author_list']
publication_export_enabled = "{{PUBLICATION_EXPORT_ENABLED_JSON}}" == "true"
openreview_publication_enabled = "{{OPENREVIEW_PUBLICATION_ENABLED_JSON}}" == "true"


def production_editor_camera_ready_instructions():
    if publication_export_enabled and openreview_publication_enabled:
        return 'Open the paper forum from this email or from the Pending Publication queue. Download the final files and metadata from the paper forum, publish the paper on the JMLR website, then submit Mark as Published to finish the OpenReview publication step.'
    if publication_export_enabled:
        return 'Open the paper forum from this email or from the Pending Publication queue. Download the final files and metadata from the paper forum for publication processing.'
    if openreview_publication_enabled:
        return 'Open the paper forum from this email or from the Pending Publication queue, then submit Mark as Published when the OpenReview publication step is ready to finish.'
    return 'Open the paper forum from this email or from the Pending Publication queue to inspect the camera-ready approved paper.'


def final_author_content(submission):
    final_authors = split_final_author_list(get_content_value(submission, 'final_publication_author_list'))
    if not final_authors:
        return {}
    return {
        'authors': {'value': final_authors},
        'authorids': {'value': final_authors},
        'author_list': {'value': ', '.join(final_authors)}
    }


def update_camera_ready_revision_guidance(client, journal, submission, decision):
    invitation_id = f'{journal.venue_id}/Paper{submission.number}/-/Camera_Ready_Revision'
    dates_block = build_openreview_dates_block(client, submission, decision)
    latex_guidance = (
        '\n\nLaTeX metadata:\n'
        '- In your LaTeX source, use this generated OpenReview metadata block exactly as shown:\n\n'
        f'{dates_block}\n\n'
        '- The JMLR publication number uses the accepted year and the last five digits of the OpenReview paper number.\n'
        '- Your camera-ready version requires approval from your Action Editor before publication.'
    )
    try:
        revision_invitation = client.get_invitation(invitation_id)
        pdf_field = revision_invitation.edit['note']['content']['pdf']
        base_description = pdf_field.get('description', '').split('\n\nLaTeX metadata:', 1)[0]
        base_description = base_description.split(' In your LaTeX source, use this generated OpenReview metadata block exactly as shown:', 1)[0].rstrip()
        pdf_field['description'] = base_description + latex_guidance
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=revision_invitation,
            replacement=True
        )
    except Exception as error:
        print(f'Could not update camera-ready LaTeX guidance for {invitation_id}: {error}')


def camera_ready_revision_action_content(journal, submission):
    author_group_id = journal.get_authors_id(number=submission.number)
    invitation_id = journal.get_camera_ready_revision_id(number=submission.number)
    action_url = (
        f'{{SITE_URL}}/forum?id={submission.id}'
        f'&noteId={submission.id}'
        f'&invitationId={invitation_id}'
        f'&role_context={author_group_id}'
    )
    return {
        'camera_ready_revision_action': {
            'value': f'[Camera Ready Revision]({action_url})',
            'readers': [author_group_id]
        }
    }


def download_publication_files_action_content(journal, submission):
    invitation_id = f'{journal.venue_id}/Paper{submission.number}/-/Download_Publication_Files'
    action_url = f'{{SITE_URL}}/invitation?id={invitation_id}'
    return {
        'download_publication_files_action': {
            'value': f'[Download publication files]({action_url})',
            'readers': [
                journal.get_editors_in_chief_id(),
                f'{journal.venue_id}/Production_Editors'
            ]
        }
    }


def set_mark_camera_ready_published_invitation(client, journal, submission, publication_metadata=None):
    client.post_invitation_edit(
        invitations=f'{journal.venue_id}/-/Mark_Camera_Ready_Published',
        readers=[journal.get_editors_in_chief_id()],
        writers=[journal.venue_id],
        signatures=[journal.venue_id],
        content={
            'noteNumber': {'value': submission.number},
            'noteId': {'value': submission.id}
        }
    )
    publication_metadata = publication_metadata or get_content_value(submission, 'publication_metadata') or {}
    if not publication_metadata:
        return
    invitation_id = f'{journal.venue_id}/Paper{submission.number}/-/Mark_as_Published'
    volume = publication_metadata.get('volume')
    year = publication_metadata.get('year')
    paper_id = publication_metadata.get('id')
    submitted = publication_metadata.get('submitted')
    revised = publication_metadata.get('revised')
    accepted = publication_metadata.get('accepted')
    if not all([volume, year, paper_id, submitted, revised, accepted]):
        return
    try:
        mark_published_invitation = client.get_invitation(invitation_id)
        published_field = mark_published_invitation.edit['note']['content']['published']
        base_description = published_field.get('description', '').split(' The entire rendered first-page header should match:', 1)[0]
        published_field['description'] = (
            base_description
            + f' The entire rendered first-page header should match: Journal of Machine Learning Research {volume} ({year}) '
            + f'1-[last page] ... Submitted {submitted}; Revised {revised}; Published {accepted}. '
            + 'Check that [last page] is the actual final page number of the uploaded PDF. '
            + 'Check that the author names and order shown in the PDF match the approved Final Publication Author List recorded on this OpenReview paper. '
            + f'The rendered first-page footer should include the attribution URL http://jmlr.org/papers/v{volume}/{paper_id}.html.'
        )
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=mark_published_invitation,
            replacement=True
        )
    except Exception as error:
        print(f'Could not update mark-published verification guidance for {invitation_id}: {error}')


def set_download_publication_files_invitation(client, journal, submission, publication_metadata=None):
    publication_metadata = publication_metadata or get_content_value(submission, 'publication_metadata') or {}
    client.post_invitation_edit(
        invitations=f'{journal.venue_id}/-/Download_Publication_Files',
        readers=[journal.get_editors_in_chief_id()],
        writers=[journal.venue_id],
        signatures=[journal.venue_id],
        content={
            'noteNumber': {'value': submission.number},
            'noteId': {'value': submission.id},
            'publicationMetadata': {'value': publication_metadata}
        }
    )


def process(client, edit, invitation):

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    venue_id = journal.venue_id
    production_editors_id = f'{venue_id}/Production_Editors'
    super_child_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/super_invitation_child_edit.py}}", super_child_namespace)

    def production_editor_readers(readers):
        if readers == ['everyone']:
            return [production_editors_id]
        return readers + [production_editors_id] if production_editors_id not in readers else readers

    def grant_production_editor_forum_readers(submission):
        forum_notes = client.get_notes(forum=submission.id, sort='tcdate:asc')
        for forum_note in forum_notes:
            updated_readers = production_editor_readers(forum_note.readers or [])
            if updated_readers == (forum_note.readers or []):
                continue
            client.post_note_edit(
                invitation=journal.get_meta_invitation_id(),
                readers=updated_readers,
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=forum_note.id,
                    readers=updated_readers
                )
            )

    def publication_file_reader_content(submission):
        content = {}
        for field_name in ['pdf', 'supplementary_material']:
            field = submission.content.get(field_name, {}) or {}
            if not field.get('value'):
                continue
            field_readers = field.get('readers') or journal.get_under_review_submission_readers(submission.number)
            content[field_name] = {'readers': production_editor_readers(field_readers)}
        return content

    note = client.get_note(edit.note.id)
    if note.tcdate != note.tmdate:
        return

    submission = client.get_note(note.forum)
    latest_submission_update = getattr(submission, 'tmdate', None) or getattr(submission, 'tcdate', None) or 0
    if (getattr(note, 'tcdate', 0) or 0) < latest_submission_update:
        raise openreview.OpenReviewException('This camera-ready verification is stale because the authors submitted a newer camera-ready upload. Please verify the latest camera-ready version.')

    decisions = client.get_notes(invitation=journal.get_ae_decision_id(number=submission.number))
    if not decisions:
        return

    decision = decisions[0]
    verification = note.content.get('verification', {}).get('value')
    revision_comments = note.content.get('revision_comments', {}).get('value', '').strip()

    if verification == 'Request camera-ready revision':
        if not revision_comments:
            raise openreview.OpenReviewException('Revision comments are required when requesting a camera-ready revision.')

        super_child_namespace['refresh_camera_ready_revision_invitation'](
            client,
            journal,
            submission,
            journal.get_due_date(weeks=journal.get_camera_ready_period_length())
        )
        update_camera_ready_revision_guidance(client, journal, submission, decision)
        try:
            set_invitation_expiration_date(
                client,
                journal,
                f'{venue_id}/Paper{submission.number}/-/Camera_Ready_Verification',
                openreview.tools.datetime_millis(datetime.datetime.now())
            )
        except Exception as error:
            print(f'Could not expire camera-ready verification invitation: {error}')

        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            readers=journal.get_under_review_submission_readers(submission.number),
            writers=[venue_id],
            signatures=[venue_id],
            note=openreview.api.Note(
                id=submission.id,
                writers=[venue_id, journal.get_authors_id(number=submission.number)],
                content={
                    **camera_ready_revision_action_content(journal, submission),
                    'venue': {
                        'value': f'Camera-ready revision pending for {journal.short_name}'
                    },
                    'venueid': {
                        'value': f'{venue_id}/Camera_Ready_Revision_Pending'
                    }
                }
            )
        )

        author_group = client.get_group(journal.get_authors_id())
        message = author_group.content['camera_ready_revision_requested_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            revision_comments=revision_comments,
            paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
            openreview_dates_block=build_openreview_dates_block(client, submission, decision),
            contact_info=journal.contact_info
        )

        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'[{journal.short_name}] Camera-ready revision requested for submission {submission.number}: {submission.content["title"]["value"]}',
            message=message,
            replyTo=journal.contact_info,
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )
        return

    if verification != 'Approve camera-ready version':
        raise openreview.OpenReviewException('Select whether to approve the camera-ready version or request revision.')

    recommendation_mapping = journal.has_journal_to_conference_certification()
    certifications = decision.content.get('certifications', {}).get('value', [])

    if journal.get_certifications():
        if recommendation_mapping:
            ae_score = recommendation_mapping[decision.content.get('recommendation_to_conference_track', decision.content.get('recommendation_to_iclr_track', {})).get('value')]
            if ae_score >= 3:
                scores = [ae_score]
                if sum(scores) / len(scores) >= 3:
                    certifications.append(journal.get_journal_to_conference_certification())

    publication_metadata_enabled = publication_export_enabled or openreview_publication_enabled
    publication_metadata = build_publication_metadata(client, submission, decision) if publication_metadata_enabled else {}

    content = {
        '_bibtex': {
            'value': journal.get_bibtex(submission, journal.accepted_venue_id, certifications=certifications)
        },
        'camera_ready_revision_action': {
            'delete': True
        }
    }
    if publication_metadata_enabled:
        content['publication_metadata'] = {
            'value': publication_metadata,
            'readers': [venue_id]
        }
    if publication_export_enabled:
        content.update(publication_file_reader_content(submission))
        content.update(download_publication_files_action_content(journal, submission))
    content.update(final_author_content(submission))

    if certifications:
        content['certifications'] = {'value': certifications}

    approved_readers = production_editor_readers(journal.get_under_review_submission_readers(submission.number))

    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        readers=approved_readers,
        writers=[venue_id],
        signatures=[venue_id],
        note=openreview.api.Note(
            id=submission.id,
            readers=approved_readers,
            pdate=decision.tcdate,
            content=content
        )
    )
    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        readers=approved_readers,
        writers=[venue_id],
        signatures=[venue_id],
        note=openreview.api.Note(
            id=submission.id,
            readers=approved_readers,
            content={
                'venue': {
                    'value': f'Camera-ready approved for {journal.short_name}'
                },
                'venueid': {
                    'value': f'{venue_id}/Camera_Ready_Approved'
                }
            }
        )
    )

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    try:
        set_invitation_expiration_date(client, journal, f'{venue_id}/Paper{submission.number}/-/Camera_Ready_Revision', now)
    except Exception as error:
        print(f'Could not expire camera-ready revision invitation: {error}')
    try:
        set_invitation_expiration_date(client, journal, f'{venue_id}/Paper{submission.number}/-/Camera_Ready_Verification', now)
    except Exception as error:
        print(f'Could not expire camera-ready verification invitation: {error}')

    if openreview_publication_enabled:
        try:
            set_mark_camera_ready_published_invitation(client, journal, submission, publication_metadata)
        except Exception as error:
            print(f'Could not create mark-published invitation: {error}')

    if publication_export_enabled:
        try:
            set_download_publication_files_invitation(client, journal, submission, publication_metadata)
        except Exception as error:
            print(f'Could not create download-publication-files invitation: {error}')

    try:
        grant_production_editor_forum_readers(submission)
    except Exception as error:
        print(f'Could not grant production-editor forum readers: {error}')

    print('Send email to Authors')
    author_group = client.get_group(journal.get_authors_id())
    author_message_template = author_group.content['camera_ready_approved_email_template_script']['value']
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_authors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Camera-ready version accepted for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=author_message_template.format(
            short_name=journal.short_name,
            submission_id=submission.id,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
            contact_info=journal.contact_info
        ),
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )

    try:
        production_editor_group = client.get_group(production_editors_id)
        message_template = production_editor_group.content.get('camera_ready_approved_email_template_script', {}).get('value')
        if message_template:
            client.post_message(
                invitation=journal.get_meta_invitation_id(),
                recipients=[production_editors_id],
                subject=f'''[{journal.short_name}] Camera-ready approved for publication processing: submission {submission.number}: {submission.content['title']['value']}''',
                message=message_template.format(
                    short_name=journal.short_name,
                    submission_id=submission.id,
                    submission_number=submission.number,
                    submission_title=submission.content['title']['value'],
                    paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
                    publication_processing_instructions=production_editor_camera_ready_instructions(),
                    contact_info=journal.contact_info
                ),
                replyTo=journal.contact_info,
                signature=journal.venue_id,
                sender=journal.get_message_sender()
            )
    except Exception as error:
        print(f'Could not notify production editors of camera-ready approval: {error}')
