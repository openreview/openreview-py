def process(client, edit, invitation):
    import datetime

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    super_child_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/super_invitation_child_edit.py}}", super_child_namespace)
    rating_prompt_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/rating/status_prompt.py}}", rating_prompt_namespace)
    rating_launcher_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/rating/reviewer_rating_launcher.py}}", rating_launcher_namespace)
    rating_page_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/rating/reviewer_rating_page.py}}", rating_page_namespace)
    decision_refresh_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/decision_refresh.py}}", decision_refresh_namespace)
    due_date_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/review_due_date_helpers.py}}", due_date_namespace)
    note = client.get_note(edit.note.id)

    ## On update or delete return
    if note.tcdate != note.tmdate:
        return

    submission = client.get_note(note.forum, details='replies')
    review_invitation = client.get_invitation(journal.get_review_id(number=submission.number))
    review_note_id = note.content.get('review_note_id', {}).get('value')
    review = None
    if review_note_id:
        try:
            review = client.get_note(review_note_id)
        except Exception as error:
            print(f'Could not load review note {review_note_id}: {error}')
    if not review and note.replyto != submission.id:
        try:
            candidate = client.get_note(note.replyto)
            if candidate.invitations and candidate.invitations[0] == journal.get_review_id(number=submission.number):
                review = candidate
        except Exception as error:
            print(f'Could not load rating reply target {note.replyto}: {error}')

    def note_content_value(field_name):
        value = note.content.get(field_name)
        if isinstance(value, dict) and 'value' in value:
            return value.get('value')
        return value

    def reviewer_effective_due_date(review_invitation, reviewer_profile_id=None):
        return due_date_namespace['effective_review_due_date_for_reviewer'](
            client,
            journal,
            submission,
            reviewer_profile_id,
            fallback_due_date=getattr(review_invitation, 'duedate', None)
        )

    decisions = client.get_notes(forum=submission.id, invitation=journal.get_ae_decision_id(number=submission.number))
    decision_times = [decision.tcdate for decision in decisions if decision.tcdate]
    first_decision_time = min(decision_times) if decision_times else None
    effective_review_due_date = reviewer_effective_due_date(
        review_invitation,
        reviewer_profile_id=note_content_value('reviewer_profile_id')
    )
    timeliness_grace_period_millis = 7 * 24 * 60 * 60 * 1000
    effective_review_due_date_with_grace = effective_review_due_date + timeliness_grace_period_millis if effective_review_due_date else None
    decision_before_due = first_decision_time and effective_review_due_date and first_decision_time <= effective_review_due_date
    if not review:
        timeliness = 'Review not expected' if decision_before_due else 'Past due'
    elif decision_before_due and review.tcdate > first_decision_time:
        timeliness = 'Review not expected'
    else:
        timeliness = 'Past due' if effective_review_due_date_with_grace and review.tcdate > effective_review_due_date_with_grace else 'On time'
    rating_content_update = {}
    if not note.content.get('rating', {}).get('value'):
        rating_content_update['rating'] = { 'value': 'No rating' }
    if not note.content.get('timeliness', {}).get('value'):
        rating_content_update['timeliness'] = { 'value': timeliness }
    if rating_content_update:
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            readers=[journal.venue_id],
            writers=[journal.venue_id],
            note=openreview.api.Note(
                id=note.id,
                content=rating_content_update
            )
        )

    active_rating_invitations = [
        rating_invitation
        for rating_invitation in client.get_all_invitations(prefix=f'{journal.venue_id}/Paper{submission.number}/Reviewer_')
        if rating_invitation.id.endswith('/-/Rating') and not getattr(rating_invitation, 'ddate', None)
    ]
    rating_notes = [r for r in submission.details['replies'] if r['invitations'][0].endswith('/-/Rating')]
    if note.invitations and note.invitations[0].endswith('/-/Rating'):
        rating_notes.append({
            'id': note.id,
            'invitations': note.invitations
        })
    now = openreview.tools.datetime_millis(datetime.datetime.now())
    if note.invitations and note.invitations[0].endswith('/-/Rating'):
        rating_page_namespace['expire_reviewer_rating_page'](client, journal, note.invitations[0], now)
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=openreview.api.Invitation(
                id=note.invitations[0],
                signatures=[journal.venue_id],
                expdate=now,
                ddate=now
            ),
            replacement=False
        )
    rating_prompt_namespace['refresh_pending_reviewer_rating_prompt'](
        client,
        journal,
        submission,
        extra_rated_invitation_ids=note.invitations or []
    )
    rating_launcher_namespace['refresh_reviewer_rating_launcher'](
        client,
        journal,
        submission,
        extra_rated_invitation_ids=note.invitations or []
    )
    try:
        decision_refresh_namespace['add_resubmission_reviewer_auto_assignment_fields'](
            client,
            journal,
            submission
        )
    except Exception as error:
        print(f'Could not refresh decision reviewer rating status for Paper{submission.number}: {error}')

    if active_rating_invitations and len(rating_notes) >= len(active_rating_invitations):
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=openreview.api.Invitation(
                id=f'{journal.venue_id}/Paper{submission.number}/-/Reviewer_Rating',
                signatures=[journal.venue_id],
                expdate=now,
                ddate=now
            ),
            replacement=False
        )

    ## Keep compatibility for older papers whose decision invitation was not
    ## created when the paper entered under review.
    reviews = [r for r in submission.details['replies'] if r['invitations'][0] == journal.get_review_id(number=submission.number)]
    ratings = [r for r in submission.details['replies'] if r['invitations'][0].endswith('Rating')]
    decision_invitation = openreview.tools.get_invitation(client, journal.get_ae_decision_id(number=submission.number))
    if len(reviews) == len(ratings) and not decision_invitation and not decisions:
        super_child_namespace['refresh_decision_invitation_from_super'](
            client,
            journal,
            submission,
            datetime.datetime.fromtimestamp(invitation.cdate / 1000.0),
            datetime.datetime.fromtimestamp(invitation.duedate / 1000.0)
        )
