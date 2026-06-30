def refresh_pending_reviewer_rating_prompt(client, journal, submission, extra_rated_invitation_ids=None):
    focus_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/rating/reviewer_rating_focus.py}}", focus_namespace)
    reviewer_rating_focus_url = focus_namespace['reviewer_rating_focus_url']
    identity_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_identity_continuity.py}}", identity_namespace)

    prompt_start = '<!-- JMLR_PENDING_REVIEWER_RATING_PROMPT_START -->'
    prompt_end = '<!-- JMLR_PENDING_REVIEWER_RATING_PROMPT_END -->'
    old_prompt_start = '<!-- JMLR_REVIEWER_RATING_PROMPT_START -->'
    old_prompt_end = '<!-- JMLR_REVIEWER_RATING_PROMPT_END -->'

    def content_value(note_or_invitation, field_name):
        if not note_or_invitation:
            return ''
        field = (note_or_invitation.content or {}).get(field_name, {})
        return field.get('value') if isinstance(field, dict) else field

    def strip_prompt_block(status, start_marker, end_marker):
        if start_marker not in status:
            return status
        start_index = status.find(start_marker)
        end_index = status.find(end_marker, start_index)
        if end_index < 0:
            return status
        end_index += len(end_marker)
        head = status[:start_index].rstrip()
        tail = status[end_index:].strip()
        if head and tail:
            return head + '\n\n' + tail
        return head or tail

    def replace_prompt_block(submission_note, replacement):
        existing_status = submission_note.content.get('jmlr_editorial_status', {}).get('value') or ''
        existing_status = strip_prompt_block(existing_status, old_prompt_start, old_prompt_end)
        existing_status = strip_prompt_block(existing_status, prompt_start, prompt_end)
        content_update = {
            'jmlr_editorial_status': {
                'value': existing_status.strip(),
                'readers': [
                    journal.get_editors_in_chief_id(),
                    journal.get_action_editors_id(submission_note.number)
                ]
            },
            'reviewer_rating_reminder': {
                'value': '',
                'readers': [
                    journal.get_action_editors_id(submission_note.number)
                ]
            },
            'submission_reviewer_rating_reminder': {
                'value': '',
                'readers': [
                    journal.get_action_editors_id(submission_note.number)
                ]
            },
            'zz_reviewer_rating_reminder': {
                'value': '',
                'readers': [
                    journal.get_action_editors_id(submission_note.number)
                ]
            }
        }
        if 'submission_number' in submission_note.content:
            content_update['submission_number'] = submission_note.content['submission_number']
        content_update['submission_number_reviewer_rating_reminder'] = {
            'value': replacement,
            'readers': [
                journal.get_action_editors_id(submission_note.number)
            ]
        }
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            note=openreview.api.Note(
                id=submission_note.id,
                content=content_update
            )
        )

    replace_prompt_block(submission, '')
    return

    try:
        active_decisions = [
            decision for decision in client.get_notes(forum=submission.id, invitation=journal.get_ae_decision_id(number=submission.number))
            if not getattr(decision, 'ddate', None)
        ]
    except Exception as error:
        print(f'Could not load decisions for Paper{submission.number}: {error}')
        active_decisions = []

    if not active_decisions:
        replace_prompt_block(submission, '')
        return

    try:
        active_rating_invitations = [
            rating_invitation
            for rating_invitation in client.get_all_invitations(prefix=f'{journal.venue_id}/Paper{submission.number}/Reviewer_')
            if rating_invitation.id.endswith('/-/Rating') and not getattr(rating_invitation, 'ddate', None)
        ]
    except Exception as error:
        print(f'Could not load reviewer rating invitations for Paper{submission.number}: {error}')
        active_rating_invitations = []

    try:
        replies_submission = client.get_note(submission.id, details='replies')
        rating_notes = [
            reply for reply in replies_submission.details.get('replies', [])
            if reply.get('invitations') and reply['invitations'][0].endswith('/-/Rating')
        ]
    except Exception as error:
        print(f'Could not load reviewer rating replies for Paper{submission.number}: {error}')
        rating_notes = []

    rated_invitation_ids = {rating_note['invitations'][0] for rating_note in rating_notes}
    rated_invitation_ids.update(extra_rated_invitation_ids or [])
    pending_rating_invitations = []
    for rating_invitation in active_rating_invitations:
        if rating_invitation.id in rated_invitation_ids:
            continue
        pending_rating_invitations.append(rating_invitation)

    if not pending_rating_invitations:
        replace_prompt_block(submission, '')
        return

    site_url = "{{SITE_URL}}".rstrip("/")
    if site_url.startswith("{{"):
        api_url = (
            getattr(client, 'baseurl', None)
            or getattr(client, 'base_url', None)
            or getattr(client, 'baseUrl', None)
            or "{{API_URL}}"
        ).rstrip("/")
        site_url = (
            api_url
            .replace('https://api2.', 'https://')
            .replace('https://api.', 'https://')
        )
    prompt_lines = [
        prompt_start,
        '<div style="border: 1px solid #d6b100; background: #fff8cc; padding: 12px; margin: 12px 0;">',
        '<h4 style="margin: 0 0 8px 0;">Rate all reviewers</h4>',
        '<p style="margin: 0 0 10px 0;">Use these links to rate submitted reviews, report missing past-due reviews, or mark no rating when a review was not expected. Reviewers disappear after their rating is submitted.</p>'
    ]
    for rating_invitation in sorted(pending_rating_invitations, key=lambda item: item.id):
        reviewer_anon_id = content_value(rating_invitation, 'reviewerAnonId') or rating_invitation.id.split('/Reviewer_')[-1].split('/')[0]
        reviewer_label = identity_namespace['reviewer_display_label'](
            submission,
            reviewer_profile_id=content_value(rating_invitation, 'reviewerProfileId'),
            current_anon_id=reviewer_anon_id
        )
        review_note_id = content_value(rating_invitation, 'reviewNoteId')
        default_timeliness = content_value(rating_invitation, 'defaultTimeliness')
        replyto_id = (rating_invitation.edit or {}).get('note', {}).get('replyto')
        if review_note_id or (replyto_id and replyto_id != submission.id):
            review_label = 'submitted review'
            action_label = 'Rate review'
        elif default_timeliness == 'Past due':
            review_label = 'no submitted review, past due'
            action_label = 'Report problem'
        else:
            review_label = 'no submitted review, not expected'
            action_label = 'Mark no rating'
        rating_url = reviewer_rating_focus_url(site_url, rating_invitation)
        prompt_lines.append('<p style="margin: 6px 0; white-space: nowrap;"><strong>' + str(reviewer_label) + ':</strong> <span style="color: #555;">' + review_label + '</span> - [' + action_label + '](' + rating_url + ')</p>')
    prompt_lines.append('</div>')
    prompt_lines.append(prompt_end)
    replace_prompt_block(submission, '\n'.join(prompt_lines))
