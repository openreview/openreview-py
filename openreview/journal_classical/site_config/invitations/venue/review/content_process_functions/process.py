def process(client, edit, invitation):
    import datetime

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    status_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/status/paper_status_refresh.py}}", status_namespace)
    editors_in_chief_id = f'{journal.venue_id}/Editors_In_Chief'
    release_namespace = {
        'openreview': openreview,
        'client': client,
        'journal': journal,
        'editors_in_chief_id': editors_in_chief_id
    }
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/release_helpers.py}}", release_namespace)
    unique_values = release_namespace['unique_values']
    release_reviews_and_comments = release_namespace['release_reviews_and_comments']
    rating_page_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/rating/reviewer_rating_page.py}}", rating_page_namespace)
    refresh_reviewer_rating_page = rating_page_namespace['refresh_reviewer_rating_page']
    decision_refresh_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/decision_refresh.py}}", decision_refresh_namespace)
    identity_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_identity_continuity.py}}", identity_namespace)
    due_date_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/review_due_date_helpers.py}}", due_date_namespace)
    required_reviewers_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/required_reviewers.py}}", required_reviewers_namespace)

    def active_reviewer_assignment_count(submission):
        active_reviewer_assignments = []
        try:
            active_reviewer_assignments.extend([
                edge for edge in client.get_edges(invitation=journal.get_reviewer_assignment_id(), head=submission.id)
                if not edge.ddate
            ])
        except Exception as error:
            print(f'Could not load reviewer assignments for Paper{submission.number}: {error}')
        try:
            active_reviewer_assignments.extend([
                edge for edge in client.get_edges(invitation=journal.get_reviewer_assignment_id(number=submission.number), head=submission.id)
                if not edge.ddate
            ])
        except Exception as error:
            print(f'Could not load paper-scoped reviewer assignments for Paper{submission.number}: {error}')
        return len(unique_values([edge.tail for edge in active_reviewer_assignments if edge.tail]))

    def validate_assigned_reviewer_signature(submission, review_note):
        review_signature = (review_note.signatures or [None])[0]
        paper_reviewers_group = client.get_group(journal.get_reviewers_id(number=submission.number))
        assigned_reviewer_signatures = set(paper_reviewers_group.anon_members or [])
        if review_signature not in assigned_reviewer_signatures:
            raise openreview.OpenReviewException(
                f'Review must be signed with an assigned anonymous reviewer signature for Paper{submission.number}.'
            )

    def review_progress_content(submission, reviews):
        assigned_reviewers_count = active_reviewer_assignment_count(submission)
        required_reviewers = required_reviewers_namespace['get_required_reviewers'](client, journal, submission)
        return {
            'reviews_submitted_count': {'value': len(reviews)},
            'reviews_assigned_count': {'value': assigned_reviewers_count},
            'reviews_required_count': {'value': required_reviewers}
        }

    def update_review_progress(submission, reviews):
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            note=openreview.api.Note(
                id=submission.id,
                content=review_progress_content(submission, reviews)
            )
        )

    def update_review_reviewer_identity_display(submission, review_note, reviewer_profile_id):
        reviewer_anon_id = identity_namespace['reviewer_anon_id_from_signature']((review_note.signatures or [''])[0])
        reviewer_label = identity_namespace['reviewer_display_label'](
            submission,
            reviewer_profile_id=reviewer_profile_id,
            current_anon_id=reviewer_anon_id
        )
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            note=openreview.api.Note(
                id=review_note.id,
                content={
                    'title': {
                        'value': f'Review of Paper{submission.number} by {reviewer_label}',
                        'readers': release_namespace['release_review_readers'](submission)
                    },
                    'reviewer_identity': {
                        'value': reviewer_label,
                        'readers': release_namespace['release_review_readers'](submission)
                    }
                }
            )
        )
        return reviewer_label

    def effective_review_due_date(review_invitation, reviewer_profile_id=None):
        if reviewer_profile_id:
            for edge in due_date_namespace['active_reviewer_assignment_edges'](client, journal, submission):
                if edge.tail == reviewer_profile_id:
                    return due_date_namespace['effective_review_due_date_for_edge'](
                        client,
                        journal,
                        submission,
                        edge
                    )
        return getattr(review_invitation, 'duedate', None)

    def derive_reviewer_timeliness(review_note, review_invitation, decision_time=None, reviewer_profile_id=None):
        timeliness_grace_period_millis = 7 * 24 * 60 * 60 * 1000
        review_due_date = effective_review_due_date(review_invitation, reviewer_profile_id=reviewer_profile_id)
        review_due_date_with_grace = review_due_date + timeliness_grace_period_millis if review_due_date else None
        decision_before_due = decision_time and review_due_date and decision_time <= review_due_date
        if not review_note:
            return 'Review not expected' if decision_before_due else 'Past due'
        if decision_before_due and review_note.tcdate > decision_time:
            return 'Review not expected'
        return 'Past due' if review_due_date_with_grace and review_note.tcdate > review_due_date_with_grace else 'On time'

    def set_reviewer_rating_defaults(rating_invitation_id, default_timeliness):
        try:
            rating_invitation = client.get_invitation(rating_invitation_id)
            note_content = rating_invitation.edit['note']['content']
            note_content.setdefault('resubmission_auto_assignment', {
                'order': 4,
                'description': 'Select this reviewer for automatic assignment if the paper is resubmitted.',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': [
                            'Select this reviewer for automatic assignment if the paper is resubmitted.'
                        ],
                        'input': 'checkbox',
                        'optional': True,
                        'deletable': True
                    }
                }
            })
            note_content['rating']['value']['param']['default'] = 'No rating'
            note_content['timeliness']['value']['param']['default'] = default_timeliness
            note_content['resubmission_auto_assignment']['value']['param'].pop('default', None)
            note_content['reviewer_anon_id']['value']['param']['default'] = rating_invitation_id.split('/Reviewer_')[-1].split('/')[0]
            note_content['reviewer_profile_id']['value']['param']['default'] = reviewer_profile_id or ''
            note_content['review_note_id']['value']['param']['default'] = review_note.id
            client.post_invitation_edit(
                invitations=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                invitation=rating_invitation,
                replacement=True
            )
            refresh_reviewer_rating_page(client, journal, submission, rating_invitation, review_note)
        except Exception as error:
            print(f'Could not set reviewer rating defaults for {rating_invitation_id}: {error}')

    def create_reviewer_rating_invitation(submission, review_note, reviewer_profile_id):
        if not review_note.signatures:
            return
        reviewer_signature = review_note.signatures[0]
        if '/Reviewer_' not in reviewer_signature:
            return
        reviewer_anon_id = reviewer_signature.split('/Reviewer_')[-1]
        rating_duedate = openreview.tools.datetime_millis(datetime.datetime.now()) + 7 * 24 * 60 * 60 * 1000
        default_timeliness = derive_reviewer_timeliness(
            review_note,
            review_invitation,
            reviewer_profile_id=reviewer_profile_id
        )
        rating_invitation_id = f'{reviewer_signature}/-/Rating'
        client.post_invitation_edit(
            invitations=f'{journal.venue_id}/-/Rating',
            signatures=[journal.venue_id],
            content={
                'noteNumber': { 'value': submission.number },
                'noteId': { 'value': submission.id },
                'replytoId': { 'value': review_note.id },
                'signature': { 'value': reviewer_signature },
                'duedate': { 'value': rating_duedate },
                'reviewerAnonId': { 'value': reviewer_anon_id },
                'reviewerProfileId': { 'value': reviewer_profile_id or '' },
                'reviewNoteId': { 'value': review_note.id },
                'defaultTimeliness': { 'value': default_timeliness }
            },
            replacement=True
        )
        set_reviewer_rating_defaults(rating_invitation_id, default_timeliness)

    def send_review_submitted_email_to_ae(submission, reviews, reviewer_label):
        ae_group = client.get_group(journal.get_action_editors_id())
        required_reviewers = required_reviewers_namespace['get_required_reviewers'](client, journal, submission)
        assigned_reviewers_count = active_reviewer_assignment_count(submission) or required_reviewers
        review_status = f'{len(reviews)} submitted / {assigned_reviewers_count} assigned; automatic release threshold {required_reviewers}'
        message = ae_group.content['review_submitted_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            reviewer_label=reviewer_label,
            review_status=review_status,
            paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
            contact_info=journal.contact_info
        )
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_action_editors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Review submitted for {journal.short_name} paper {submission.number}: {submission.content['title']['value']}''',
            message=message,
            replyTo=journal.contact_info,
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

    review_note=client.get_note(edit.note.id)
    submission = client.get_note(review_note.forum)
    validate_assigned_reviewer_signature(submission, review_note)

    ## increase pending review if review is deleted
    signature_group = client.get_group(id=review_note.signatures[0])
    reviewer_profile = openreview.tools.get_profile(client, signature_group.members[0])
    edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=(reviewer_profile.id if reviewer_profile else signature_group.members[0]))
    if edges and edges[0].weight > 0:
        pending_review_edge = edges[0]
        if review_note.ddate:
            pending_review_edge.weight += 1
            client.post_edge(pending_review_edge)

    review_invitation_id = (review_note.invitations or [journal.get_review_id(number=submission.number)])[0]
    reviews=client.get_notes(forum=review_note.forum, invitation=review_invitation_id)
    if not review_note.ddate and not any(review.id == review_note.id for review in reviews):
        reviews.append(review_note)
    update_review_progress(submission, reviews)
    reviewer_profile_id = reviewer_profile.id if reviewer_profile else signature_group.members[0]
    reviewer_label = update_review_reviewer_identity_display(submission, review_note, reviewer_profile_id)

    if journal.get_release_review_id(number=submission.number) in review_note.invitations:
        print('Review already released, exit')
        return

    review_invitation = client.get_invitation(journal.get_review_id(number=submission.number))
    processed_signatures = set(list(getattr(review_invitation, 'noninvitees', []) or []))
    review_signatures = list(review_note.signatures or getattr(edit.note, 'signatures', []) or [])
    if review_note.ddate or (review_signatures and all(signature in processed_signatures for signature in review_signatures)):
        print('Review already processed or deleted, exit')
        return

    print('Send review-submitted email to AE')
    send_review_submitted_email_to_ae(submission, reviews, reviewer_label)

    print('Close submitted review to reviewer edits')
    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        note=openreview.api.Note(
            id=review_note.id,
            writers=[journal.venue_id]
        )
    )
    print('Expire review action for submitting reviewer')
    review_invitation.noninvitees = unique_values(list(getattr(review_invitation, 'noninvitees', []) or []) + review_signatures)
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=review_invitation,
        replacement=True
    )
    try:
        print('Create reviewer rating action for submitted review')
        create_reviewer_rating_invitation(
            submission,
            review_note,
            reviewer_profile_id
        )
    except Exception as error:
        print(f'Could not create reviewer rating action for Paper{submission.number}: {error}')
    try:
        decision_refresh_namespace['add_resubmission_reviewer_auto_assignment_fields'](
            client,
            journal,
            submission
        )
    except Exception as error:
        print(f'Could not refresh decision reviewer auto-assignment fields for Paper{submission.number}: {error}')

    print(f'Reviews found {len(reviews)}')
    number_of_reviewers = required_reviewers_namespace['get_required_reviewers'](client, journal, submission)
    number_of_released_reviews = len(client.get_notes(invitation=journal.get_release_review_id(number=submission.number)))
    flag_review_released = number_of_released_reviews!=0
    if len(reviews) >= number_of_reviewers and not flag_review_released:
        release_reviews_and_comments(submission, reviews)
    status_namespace['refresh_paper_status_note'](client, journal, submission)
