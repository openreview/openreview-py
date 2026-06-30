def process(client, edge, invitation):
    import datetime

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    reviewer_sync_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_sync.py}}", reviewer_sync_namespace)
    reviewer_identity_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_identity_continuity.py}}", reviewer_identity_namespace)
    required_reviewers_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/required_reviewers.py}}", required_reviewers_namespace)
    reviewer_assignment_edges_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_assignment_edges.py}}", reviewer_assignment_edges_namespace)

    latest_edge = client.get_edge(edge.id, True)
    if latest_edge.ddate and not edge.ddate:
        return
    edge = latest_edge

    venue_id = journal.venue_id
    note = client.get_note(edge.head)
    assignment_invitation_id = getattr(edge, 'invitation', None) or getattr(invitation, 'id', None) or journal.get_reviewer_assignment_id()
    paper_assignment_invitation_id = journal.get_reviewer_assignment_id(number=note.number)
    group = client.get_group(journal.get_reviewers_id(number=note.number))
    reviewer_group = client.get_group(journal.get_reviewers_id())
    official_reviewer = client.get_groups(member=edge.tail, id=journal.get_reviewers_id())

    assigned_action_editor = None
    assigned_action_editor_id = None
    assigned_action_editors = client.get_group(journal.get_action_editors_id(number=note.number)).members
    if assigned_action_editors:
        assigned_action_editor_id = assigned_action_editors[0]
    if assigned_action_editor_id:
        try:
            assigned_action_editor = openreview.tools.get_profiles(
                client,
                ids_or_emails=[assigned_action_editor_id.split(',')[0]],
                with_preferred_emails=journal.get_preferred_emails_invitation_id()
            )[0]
        except Exception as error:
            print(f'Could not load assigned action editor profile {assigned_action_editor_id}: {error}')

    pending_review_edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=edge.tail)
    pending_review_edge = pending_review_edges[0] if pending_review_edges else None

    def parse_forum_id(url):
        if not url or url == "N/A":
            return None
        try:
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(str(url))
            forum_ids = parse_qs(parsed.query).get("id")
            if forum_ids and forum_ids[0]:
                return forum_ids[0]
        except Exception:
            pass
        try:
            return str(url).split("forum?id=", 1)[1].split("&", 1)[0]
        except Exception:
            return None

    def previous_forum_id_from_list(submission):
        import re
        value = submission.content.get("previous_JMLR_submissions", {}).get("value") or ""
        match = re.search(r"forum\?id=([A-Za-z0-9_-]+)", str(value))
        return match.group(1) if match else None

    def get_previous_forum_id(submission):
        previous_submission_url = submission.content.get("previous_JMLR_submission_URL", {}).get("value")
        if previous_submission_url and previous_submission_url != "N/A":
            return parse_forum_id(previous_submission_url)
        previous_submission_number = submission.content.get("previous_JMLR_submission_number", {}).get("value")
        if not previous_submission_number or str(previous_submission_number).strip().upper() == "N/A":
            return previous_forum_id_from_list(submission)
        try:
            previous_notes = client.get_notes(
                invitation=f"{journal.venue_id}/-/Submission",
                number=int(str(previous_submission_number).strip())
            )
            return previous_notes[0].id if previous_notes else None
        except Exception:
            return None

    def get_previous_submission_chain(submission):
        previous_notes = []
        seen_note_ids = {submission.id}
        current_note = submission
        while True:
            previous_forum_id = get_previous_forum_id(current_note)
            if not previous_forum_id or previous_forum_id in seen_note_ids:
                return previous_notes
            seen_note_ids.add(previous_forum_id)
            try:
                previous_note = client.get_note(previous_forum_id)
            except Exception as error:
                print(f'Could not load previous submission {previous_forum_id}: {error}')
                return previous_notes
            previous_notes.append(previous_note)
            current_note = previous_note

    def is_resubmission_reviewer_assignment(submission, reviewer_id):
        previous_forum_id = get_previous_forum_id(submission)
        if not previous_forum_id:
            return False
        previous_assignment_invitations = [
            journal.get_reviewer_assignment_id(),
            journal.get_reviewer_assignment_id(archived=True)
        ]
        try:
            previous_note = client.get_note(previous_forum_id)
            previous_assignment_invitations.append(journal.get_reviewer_assignment_id(number=previous_note.number))
        except Exception:
            pass
        for previous_assignment_invitation in previous_assignment_invitations:
            try:
                previous_assignments = client.get_edges(
                    invitation=previous_assignment_invitation,
                    head=previous_forum_id,
                    tail=reviewer_id
                )
            except Exception:
                continue
            if any(not previous_assignment.ddate for previous_assignment in previous_assignments):
                return True
        return False

    def add_reader_to_note(note_to_update, reader_id):
        readers = list(note_to_update.readers or [])
        if reader_id in readers or 'everyone' in readers:
            return
        readers.append(reader_id)
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[venue_id],
            note=openreview.api.Note(id=note_to_update.id, readers=readers)
        )

    def is_released_previous_note(note_to_check, previous_note):
        readers = set(note_to_check.readers or [])
        return (
            'everyone' in readers
            or journal.get_authors_id(number=previous_note.number) in readers
            or journal.get_reviewers_id(number=previous_note.number) in readers
        )

    def bridge_previous_version_access_for_reviewers(submission):
        current_reviewers_group_id = journal.get_reviewers_id(number=submission.number)
        for previous_note in get_previous_submission_chain(submission):
            add_reader_to_note(previous_note, current_reviewers_group_id)
            previous_decisions = client.get_notes(
                forum=previous_note.id,
                invitation=journal.get_ae_decision_id(number=previous_note.number)
            )
            for decision_note in previous_decisions:
                add_reader_to_note(decision_note, current_reviewers_group_id)
            previous_reviews = client.get_notes(
                forum=previous_note.id,
                invitation=journal.get_review_id(number=previous_note.number)
            )
            for previous_review_note in previous_reviews:
                if is_released_previous_note(previous_review_note, previous_note):
                    add_reader_to_note(previous_review_note, current_reviewers_group_id)

    class SafeTemplateValues(dict):
        def __missing__(self, key):
            print(f'Missing reviewer assignment email template value: {key}')
            return '{' + key + '}'

    def format_reviewer_assignment_template(template, **values):
        return template.format_map(SafeTemplateValues(values))

    def int_or_none(value):
        if value is None:
            return None
        try:
            return int(value)
        except Exception:
            return None

    def reviewer_due_date_edge_invitation_id():
        return f'{journal.venue_id}/Reviewers/-/Review_Due_Date'

    def active_reviewer_due_date_edge(assignment_edge):
        try:
            edges = client.get_edges(
                invitation=reviewer_due_date_edge_invitation_id(),
                head=assignment_edge.head,
                tail=assignment_edge.tail
            )
        except Exception as error:
            print(f'Could not load reviewer due-date edge for Paper{note.number}, {assignment_edge.tail}: {error}')
            return None
        active_edges = [due_date_edge for due_date_edge in edges if not getattr(due_date_edge, 'ddate', None)]
        if not active_edges:
            return None
        return sorted(
            active_edges,
            key=lambda due_date_edge: getattr(due_date_edge, 'cdate', None) or getattr(due_date_edge, 'tcdate', None) or 0,
            reverse=True
        )[0]

    def store_reviewer_assignment_due_date(assignment_edge):
        due_date_edge = active_reviewer_due_date_edge(assignment_edge)
        stored_due_date = int_or_none(getattr(due_date_edge, 'weight', None))
        if stored_due_date is None:
            stored_due_date = int_or_none(getattr(assignment_edge, 'duedate', None))
        if stored_due_date is not None:
            return int(stored_due_date)
        review_period_length = journal.get_review_period_length(note)
        assignment_cdate = getattr(assignment_edge, 'cdate', None)
        if assignment_cdate:
            reviewer_assignment_due_date = assignment_cdate + int(review_period_length * 7 * 24 * 60 * 60 * 1000)
        else:
            reviewer_assignment_due_date = openreview.tools.datetime_millis(
                journal.get_due_date(weeks=review_period_length)
            )
        client.post_edge(openreview.api.Edge(
            id=getattr(due_date_edge, 'id', None),
            invitation=reviewer_due_date_edge_invitation_id(),
            signatures=[venue_id],
            head=assignment_edge.head,
            tail=assignment_edge.tail,
            weight=reviewer_assignment_due_date,
            label='Review Due Date'
        ))
        return reviewer_assignment_due_date

    def active_assignment_edges_for_submission():
        all_assignments = reviewer_assignment_edges_namespace['reviewer_assignment_edges_for_submission'](
            client,
            journal,
            note,
            active_only=True,
        )
        assignments = []
        seen_tails = set()
        for assignment in all_assignments:
            tail = reviewer_assignment_edges_namespace['active_reviewer_assignment_tail'](assignment, journal)
            if not tail or tail in seen_tails:
                continue
            assignments.append(assignment)
            seen_tails.add(tail)
        return assignments

    def refresh_review_invitation_due_date_and_reminders():
        try:
            review_invitation = client.get_invitation(journal.get_review_id(number=note.number))
            due_date_namespace = {
                'openreview': openreview,
                'datetime': datetime,
                'REVIEW_REMINDER_SCRIPT': "{{PYTHON_SCRIPT_JSON:invitations/venue/review/dateprocess_review_reminder.py}}"
            }
            exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/review_due_date_helpers.py}}", due_date_namespace)
            review_invitation = due_date_namespace['update_review_invitation_due_date_and_reminders'](
                client,
                journal,
                note,
                review_invitation
            )
            client.post_invitation_edit(
                invitations=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                invitation=review_invitation,
                replacement=True
            )
        except Exception as error:
            print(f'Could not refresh review due date/reminders for Paper{note.number}: {error}')

    head_assignment_edges = [
        assignment for assignment in active_assignment_edges_for_submission()
        if not assignment.ddate
    ]
    try:
        review_notes = client.get_notes(forum=note.id, invitation=journal.get_review_id(number=note.number))
    except Exception as error:
        print(f'Could not load reviews for Paper{note.number}: {error}')
        review_notes = []
    required_reviewers_namespace['refresh_required_reviewers_edge_invitation'](client, journal, note)
    number_of_reviewers = required_reviewers_namespace['get_required_reviewers'](client, journal, note)
    required_reviewers_namespace['refresh_required_reviewers_aggregate'](
        client,
        journal,
        note,
        submitted_count=len(review_notes),
        assigned_count=len(head_assignment_edges)
    )

    def refresh_reviewer_assignment_task():
        try:
            active_head_assignment_edges = active_assignment_edges_for_submission()
            if assignment_invitation_id == paper_assignment_invitation_id:
                return
            submission_task_edges = [
                assignment for assignment in client.get_edges(invitation=paper_assignment_invitation_id, head=note.id)
                if not assignment.ddate
            ]
            if len(active_head_assignment_edges) >= number_of_reviewers:
                if not submission_task_edges:
                    print('Mark reviewer assignment task complete')
                    client.post_edge(openreview.api.Edge(
                        invitation=paper_assignment_invitation_id,
                        signatures=[journal.get_action_editors_id(number=note.number)],
                        head=note.id,
                        tail=journal.get_reviewers_id(),
                        weight=1
                    ))
            elif submission_task_edges:
                print('Mark reviewer assignment task incomplete')
                submission_task_edge = submission_task_edges[0]
                client.post_edge(openreview.api.Edge(
                    id=submission_task_edge.id,
                    invitation=paper_assignment_invitation_id,
                    signatures=submission_task_edge.signatures,
                    head=submission_task_edge.head,
                    tail=submission_task_edge.tail,
                    weight=submission_task_edge.weight,
                    ddate=openreview.tools.datetime_millis(datetime.datetime.now())
                ))
        except Exception as error:
            print(f'Could not refresh reviewer assignment task for Paper{note.number}: {error}')

    def refresh_reviewer_identity_for_assignment():
        try:
            reviewer_identity_namespace['ensure_stable_reviewer_number_for_assignment'](client, journal, note, edge.tail)
            reviewer_identity_namespace['refresh_current_reviewer_identity_metadata'](client, journal, note)
            reviewer_sync_namespace['refresh_paper_reviewer_sync_surfaces'](client, journal, note)
        except Exception as error:
            print(f'Could not refresh reviewer identity continuity metadata for Paper{note.number}: {error}')

    if edge.ddate and edge.tail in group.members:
        reviewer_sync_namespace['sync_remove_paper_reviewer'](client, journal, note, edge.tail)
        refresh_reviewer_assignment_task()
        refresh_review_invitation_due_date_and_reminders()

        if pending_review_edge and pending_review_edge.weight > 0:
            client.post_edge(openreview.api.Edge(
                id=pending_review_edge.id,
                invitation=journal.get_reviewer_pending_review_id(),
                signatures=pending_review_edge.signatures,
                head=pending_review_edge.head,
                tail=pending_review_edge.tail,
                weight=pending_review_edge.weight - 1
            ))

        template = reviewer_group.content.get('unassignment_email_template_script', {}).get('value')
        if template:
            assigned_action_editor_name = assigned_action_editor.get_preferred_name(pretty=True) if assigned_action_editor else assigned_action_editor_id
            reply_to = assigned_action_editor.get_preferred_email() if assigned_action_editor else journal.contact_info
            client.post_message(
                f'[{journal.short_name}] You have been unassigned from {journal.short_name} submission {note.number}: {note.content["title"]["value"]}',
                [edge.tail],
                format_reviewer_assignment_template(
                    template,
                    short_name=journal.short_name,
                    submission_id=note.id,
                    submission_number=note.number,
                    submission_title=note.content['title']['value'],
                    website=journal.website,
                    contact_info=journal.contact_info,
                    assigned_action_editor=assigned_action_editor_name
                ),
                invitation=journal.get_meta_invitation_id(),
                signature=venue_id,
                parentGroup=group.id,
                replyTo=reply_to,
                sender=journal.get_message_sender()
            )
        return

    if not edge.ddate and edge.tail not in group.members:
        reviewer_sync_namespace['sync_add_paper_reviewer'](client, journal, note, edge.tail)
        refresh_reviewer_identity_for_assignment()
        refresh_reviewer_assignment_task()
        bridge_previous_version_access_for_reviewers(note)
        reviewer_assignment_due_date_millis = store_reviewer_assignment_due_date(edge)

        if pending_review_edge:
            client.post_edge(openreview.api.Edge(
                id=pending_review_edge.id,
                invitation=journal.get_reviewer_pending_review_id(),
                signatures=pending_review_edge.signatures,
                head=pending_review_edge.head,
                tail=pending_review_edge.tail,
                weight=pending_review_edge.weight + 1
            ))
        elif official_reviewer:
            client.post_edge(openreview.api.Edge(
                invitation=journal.get_reviewer_pending_review_id(),
                signatures=[venue_id],
                head=journal.get_reviewers_id(),
                tail=edge.tail,
                weight=1
            ))

        review_period_length = journal.get_review_period_length(note)
        review_duedate = journal.get_due_date(weeks=review_period_length)
        reviewer_assignment_due_date = datetime.datetime.fromtimestamp(reviewer_assignment_due_date_millis / 1000)
        refresh_review_invitation_due_date_and_reminders()

        is_resubmission_assignment = is_resubmission_reviewer_assignment(note, edge.tail)
        template_key = 'resubmission_assignment_email_template_script' if is_resubmission_assignment else 'assignment_email_template_script'
        template = reviewer_group.content.get(template_key, {}).get('value')
        if official_reviewer and template:
            assigned_action_editor_name = assigned_action_editor.get_preferred_name(pretty=True) if assigned_action_editor else assigned_action_editor_id
            reply_to = assigned_action_editor.get_preferred_email() if assigned_action_editor else journal.contact_info
            review_visibility = 'publicly visible' if journal.is_submission_public() else 'visible to all the reviewers'
            submission_length = ' If the submission is longer than 12 pages (excluding any appendix), you may request more time to the AE.' if journal.get_submission_length() else ''
            subject = f'''[{journal.short_name}] Assignment to review new {journal.short_name} submission {note.number}: {note.content['title']['value']}'''
            if is_resubmission_assignment:
                subject = f'''[{journal.short_name}] Assignment to review revised {journal.short_name} submission {note.number}: {note.content['title']['value']}'''
            client.post_message(
                subject,
                [edge.tail],
                format_reviewer_assignment_template(
                    template,
                    short_name=journal.short_name,
                    venue_id=venue_id,
                    submission_id=note.id,
                    submission_number=note.number,
                    submission_title=note.content['title']['value'],
                    submission_length=submission_length,
                    website=journal.website,
                    contact_info=journal.contact_info,
                    review_period_length=review_period_length,
                    review_duedate=reviewer_assignment_due_date.strftime("%b %d"),
                    invitation_url=f'{{SITE_URL}}/forum?id={note.id}&invitationId={journal.get_review_id(number=note.number)}',
                    paper_url=f'{{SITE_URL}}/forum?id={note.id}',
                    reviewer_tasks_url=f'{{SITE_URL}}/group?id={venue_id}/Reviewers#reviewer-tasks',
                    number_of_reviewers=number_of_reviewers,
                    review_visibility=review_visibility,
                    reviewers_max_papers=journal.get_reviewers_max_papers(),
                    assigned_action_editor=assigned_action_editor_name
                ),
                invitation=journal.get_meta_invitation_id(),
                signature=venue_id,
                parentGroup=group.id,
                replyTo=reply_to,
                sender=journal.get_message_sender()
            )

    if not edge.ddate and edge.tail in group.members:
        store_reviewer_assignment_due_date(edge)
        refresh_reviewer_identity_for_assignment()
        refresh_reviewer_assignment_task()
        return

    if not edge.ddate:
        reviewer_sync_namespace['refresh_paper_reviewer_sync_surfaces'](client, journal, note)
        refresh_reviewer_assignment_task()
    else:
        reviewer_sync_namespace['refresh_paper_reviewer_sync_surfaces'](client, journal, note)
        refresh_reviewer_assignment_task()
