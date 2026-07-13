def refresh_reviewer_rating_launcher(client, journal, submission, extra_rated_invitation_ids=None):
    import datetime
    import html
    import json
    import urllib.parse

    focus_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/rating/reviewer_rating_focus.py}}", focus_namespace)
    reviewer_rating_focus_url = focus_namespace['reviewer_rating_focus_url']
    helper_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/rating/reviewer_rating_helpers.py}}", helper_namespace)
    content_value = helper_namespace['rating_content_value']
    review_html = helper_namespace['reviewer_rating_review_html']
    status_and_action = helper_namespace['reviewer_rating_status_and_action']
    identity_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_identity_continuity.py}}", identity_namespace)

    editors_in_chief_id = journal.get_editors_in_chief_id()
    action_editors_id = journal.get_action_editors_id(submission.number)
    launcher_invitation_id = f'{journal.venue_id}/Paper{submission.number}/-/Reviewer_Rating'

    def site_url():
        configured_site_url = "{{SITE_URL}}".rstrip("/")
        if not configured_site_url.startswith("{{"):
            return configured_site_url
        api_url = (
            getattr(client, 'baseurl', None)
            or getattr(client, 'base_url', None)
            or getattr(client, 'baseUrl', None)
            or configured_site_url
        ).rstrip("/")
        return (
            api_url
            .replace('https://api2.', 'https://')
            .replace('https://api.', 'https://')
        )

    def active_rating_invitations():
        try:
            return [
                rating_invitation
                for rating_invitation in client.get_all_invitations(prefix=f'{journal.venue_id}/Paper{submission.number}/Reviewer_')
                if rating_invitation.id.endswith('/-/Rating') and not getattr(rating_invitation, 'ddate', None)
            ]
        except Exception as error:
            print(f'Could not load reviewer rating invitations for Paper{submission.number}: {error}')
            return []

    def rated_invitation_ids():
        try:
            submission_with_replies = client.get_note(submission.id, details='replies')
            ids = {
                reply['invitations'][0]
                for reply in submission_with_replies.details.get('replies', [])
                if reply.get('invitations') and reply['invitations'][0].endswith('/-/Rating')
            }
        except Exception as error:
            print(f'Could not load reviewer rating replies for Paper{submission.number}: {error}')
            ids = set()
        ids.update(extra_rated_invitation_ids or [])
        return ids

    def review_note_for(rating_invitation):
        review_note_id = content_value(rating_invitation, 'reviewNoteId')
        if not review_note_id:
            return None
        try:
            return client.get_note(review_note_id)
        except Exception as error:
            print(f'Could not load review note {review_note_id}: {error}')
            return None

    def stable_reviewer_label(rating_invitation, reviewer_anon_id):
        return identity_namespace['reviewer_display_label'](
            submission,
            reviewer_profile_id=content_value(rating_invitation, 'reviewerProfileId'),
            current_anon_id=reviewer_anon_id
        )

    base_site_url = site_url()
    paper_label = f'Paper {submission.number}'
    already_rated_invitation_ids = rated_invitation_ids()
    pending_rating_invitations = [
        rating_invitation
        for rating_invitation in active_rating_invitations()
        if rating_invitation.id not in already_rated_invitation_ids
    ]
    now = openreview.tools.datetime_millis(datetime.datetime.now())

    if not pending_rating_invitations:
        try:
            client.post_invitation_edit(
                invitations=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                invitation=openreview.api.Invitation(
                    id=launcher_invitation_id,
                    signatures=[journal.venue_id],
                    expdate=now,
                    ddate=now
                ),
                replacement=False
            )
        except Exception as error:
            print(f'Could not expire reviewer rating launcher for Paper{submission.number}: {error}')
        return

    item_html = []
    for rating_invitation in sorted(pending_rating_invitations, key=lambda item: item.id):
        reviewer_anon_id = content_value(rating_invitation, 'reviewerAnonId') or rating_invitation.id.split('/Reviewer_')[-1].split('/')[0]
        reviewer_label = stable_reviewer_label(rating_invitation, reviewer_anon_id)
        default_timeliness = content_value(rating_invitation, 'defaultTimeliness')
        review = review_note_for(rating_invitation)
        status_label, action_label = status_and_action(review, default_timeliness)
        rating_url = reviewer_rating_focus_url(base_site_url, rating_invitation)
        item_html.append(
            '<section class="reviewer-rating-item">'
            '<h5>' + html.escape(str(reviewer_label)) + '</h5>'
            '<p class="small text-muted">' + html.escape(status_label) + '</p>'
            + review_html(review, reviewer_label)
            + '<p class="reviewer-rating-actions"><a class="btn btn-primary" target="_blank" rel="noopener noreferrer" href="'
            + html.escape(rating_url)
            + '">'
            + html.escape(action_label)
            + '</a></p>'
            '</section>'
        )

    forum_url = f'{base_site_url}/forum?' + urllib.parse.urlencode({'id': submission.id})
    launcher_template = "{{PYTHON_SCRIPT_JSON:invitations/venue/rating/reviewer_rating_launcher_web.js}}"
    launcher_web = (
        launcher_template
        .replace('__JMLR_RATING_LAUNCHER_ITEMS_HTML_JSON__', json.dumps(''.join(item_html)))
        .replace('__JMLR_RATING_LAUNCHER_FORUM_URL_JSON__', json.dumps(forum_url))
        .replace('__JMLR_RATING_LAUNCHER_PAPER_LABEL_JSON__', json.dumps(paper_label))
    )
    description = (
        f'<p>Rate reviewers for JMLR Paper {submission.number}. '
        'The launcher shows submitted reviews and no-review reviewer cases on one page.</p>'
    )
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        readers=[editors_in_chief_id, action_editors_id],
        writers=[journal.venue_id],
        invitation=openreview.api.Invitation(
            id=launcher_invitation_id,
            signatures=[journal.venue_id],
            readers=[editors_in_chief_id, action_editors_id],
            writers=[journal.venue_id],
            invitees=[action_editors_id],
            description=description,
            web=launcher_web,
            edit={
                'signatures': [action_editors_id],
                'readers': [editors_in_chief_id, action_editors_id],
                'writers': [journal.venue_id],
                'note': {
                    'forum': submission.id,
                    'replyto': submission.id,
                    'signatures': [action_editors_id],
                    'readers': [editors_in_chief_id, action_editors_id],
                    'writers': [journal.venue_id],
                    'content': {
                        'reviewer_rating_page': {
                            'order': 1,
                            'description': 'Open the paper reviewer rating page.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const': f'{base_site_url}/forum?id={urllib.parse.quote(submission.id)}&invitationId={urllib.parse.quote(launcher_invitation_id)}',
                                    'hidden': True
                                }
                            }
                        }
                    }
                }
            },
            process=(
                'def process(client, edit, invitation):\n'
                '    import datetime\n'
                '    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")\n'
                '    helper_note = client.get_note(edit.note.id)\n'
                '    client.post_note_edit(\n'
                '        invitation=journal.get_meta_invitation_id(),\n'
                '        signatures=[journal.venue_id],\n'
                '        note=openreview.api.Note(\n'
                '            id=helper_note.id,\n'
                '            readers=helper_note.readers or [],\n'
                '            writers=[journal.venue_id],\n'
                '            ddate=openreview.tools.datetime_millis(datetime.datetime.now())\n'
                '        )\n'
                '    )\n'
            )
        ),
        replacement=True
    )
