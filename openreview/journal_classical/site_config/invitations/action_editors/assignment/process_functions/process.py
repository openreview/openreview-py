def process(client, edge, invitation):
    import datetime

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    editors_in_chief_id = f'{journal.venue_id}/Editors_In_Chief'
    action_editor_anonymity_enabled = "{{AE_ANONYMITY_JSON}}" != "false"
    ae_assignment_id = getattr(invitation, "id", None)
    assignment_conflict_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/assignment_conflicts.py}}", assignment_conflict_namespace)
    reviewer_identity_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_identity_continuity.py}}", reviewer_identity_namespace)
    invitation_edit_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/invitation_edit_helpers.py}}", invitation_edit_namespace)

    def post_paper_super_invitation_child_edit(invitation_id, content):
        return client.post_invitation_edit(
            invitations=invitation_id,
            content=content,
            readers=[journal.venue_id],
            writers=[journal.venue_id],
            signatures=[journal.venue_id]
        )

    def refresh_review_invitation(note):
        duedate = journal.get_due_date(weeks=journal.get_review_period_length(note))
        return post_paper_super_invitation_child_edit(
            journal.get_review_id(),
            {
                'noteId': {'value': note.id},
                'noteNumber': {'value': note.number},
                'duedate': {'value': openreview.tools.datetime_millis(duedate)}
            }
        )

    def refresh_decision_invitation_from_super(note, cdate, duedate):
        super_child_namespace = {
            'openreview': openreview,
            'datetime': datetime
        }
        exec("{{PYTHON_SCRIPT_JSON:invitations/venue/super_invitation_child_edit.py}}", super_child_namespace)
        return super_child_namespace['refresh_decision_invitation_from_super'](client, journal, note, cdate, duedate)

    def normalize_decision_invitation_signatures(note):
        decision_invitation_id = journal.get_ae_decision_id(number=note.number)
        try:
            decision_invitation = client.get_invitation(decision_invitation_id)
        except Exception as error:
            print(f'Could not load decision invitation {decision_invitation_id} for signature normalization: {error}')
            return
        if not isinstance(decision_invitation.edit, dict):
            decision_invitation.edit = {}
        decision_invitation.signatures = [journal.venue_id]
        decision_invitation.edit['signatures'] = {
            'param': {
                'items': [
                    {
                        'value': journal.get_editors_in_chief_id(),
                        'optional': True
                    },
                    {
                        'prefix': f'{journal.venue_id}/Paper{note.number}/Action_Editor_',
                        'optional': True
                    }
                ]
            }
        }
        try:
            client.post_invitation_edit(
                invitations=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                invitation=decision_invitation,
                replacement=True
            )
        except Exception as error:
            print(f'Could not normalize decision invitation signatures for Paper{note.number}: {error}')

    def expire_invitation_with_deactivation(invitation_id):
        try:
            client.get_invitation(invitation_id)
        except Exception:
            return
        now = openreview.tools.datetime_millis(datetime.datetime.now())
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=openreview.api.Invitation(
                id=invitation_id,
                signatures=[journal.venue_id],
                expdate=now,
                ddate=now
            ),
            replacement=True
        )

    def invitation_exists_and_active(invitation_id):
        try:
            invitation_to_check = client.get_invitation(invitation_id)
            return not getattr(invitation_to_check, 'ddate', None)
        except Exception:
            return False

    def setup_under_review_submission_with_eic_child_readers(note):
        refresh_review_invitation(note)
        journal.invitation_builder.set_note_solicit_review_invitation(note)
        journal.invitation_builder.release_submission_history(note)
        expire_invitation_with_deactivation(journal.get_review_approval_id(note.number))
        paper_prefix = f'{journal.venue_id}/Paper{note.number}'
        expire_invitation_with_deactivation(f'{paper_prefix}/-/Official_Recommendation_Enabling')
        expire_invitation_with_deactivation(f'{paper_prefix}/-/Official_Recommendation')
        expire_invitation_with_deactivation(journal.get_official_recommendation_enabling_id(note.number))
        expire_invitation_with_deactivation(journal.get_reviewer_recommendation_id(note.number))

    def setup_paper_reviewer_assignment_overlay(note, active_action_editor_tail=None):
        reviewer_overlay_namespace = {"openreview": openreview}
        exec(
            "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/paper_reviewer_assignment_overlay.py}}",
            reviewer_overlay_namespace,
        )
        reviewer_overlay_namespace["setup_paper_reviewer_assignment_overlay"](
            client,
            journal,
            note,
            active_action_editor_tail=active_action_editor_tail,
        )

    def run_under_review_setup_process(note):
        under_review_invitation = client.get_invitation(journal.get_under_review_id())
        funcs = {
            'openreview': openreview,
            'datetime': datetime
        }
        exec(under_review_invitation.process, funcs)
        under_review_edit = type('UnderReviewEdit', (), {})()
        under_review_edit.note = openreview.api.Note(id=note.id)
        funcs['process'](client, under_review_edit, under_review_invitation)

    def under_review_stage_invitations_ready(note):
        return (
            invitation_exists_and_active(f'{journal.venue_id}/Paper{note.number}/-/Editorial_Comment')
        )

    def set_invitation_expiration_date(invitation_id, expiration_date):
        invitation_edit_namespace['set_invitation_expiration_date'](client, journal, invitation_id, expiration_date)

    def get_assignment_edges(**kwargs):
        return client.get_edges(invitation=ae_assignment_id, **kwargs)

    def active_reviewer_assignment_tails(submission):
        reviewer_assignment_invitation_ids = [
            journal.get_reviewer_assignment_id(number=submission.number),
            journal.get_reviewer_assignment_id(),
        ]
        assigned_tails = set()
        for reviewer_assignment_invitation_id in reviewer_assignment_invitation_ids:
            try:
                assigned_tails.update(
                    reviewer_assignment.tail
                    for reviewer_assignment in client.get_edges(
                        invitation=reviewer_assignment_invitation_id,
                        head=submission.id
                    )
                    if getattr(reviewer_assignment, "tail", None) and not getattr(reviewer_assignment, "ddate", None)
                )
            except Exception as error:
                print(f"Could not load reviewer assignments for Paper{submission.number} from {reviewer_assignment_invitation_id}: {error}")
        return assigned_tails

    def reviewer_assignment_invitation_for_post(submission):
        return journal.get_reviewer_assignment_id(number=submission.number)

    def post_selected_previous_reviewer_assignments(submission):
        if not is_resubmission_assignment:
            return previous_reviewer_assignment_prep_results
        try:
            refreshed_submission = client.get_note(submission.id)
        except Exception:
            refreshed_submission = submission
        try:
            prep_results = reviewer_identity_namespace['prepare_selected_previous_reviewers_for_assignment'](
                client,
                journal,
                refreshed_submission,
            )
        except Exception as error:
            print(f'Could not prepare selected previous reviewers for Paper{refreshed_submission.number}: {error}')
            return previous_reviewer_assignment_prep_results
        candidates = prep_results.get('candidates', []) if prep_results else []
        if not candidates:
            return prep_results or {}
        assigned_tails = active_reviewer_assignment_tails(refreshed_submission)
        posted = []
        for candidate in candidates:
            reviewer_profile_id = candidate.get('reviewer_profile_id')
            if not reviewer_profile_id or reviewer_profile_id in assigned_tails:
                continue
            has_openreview_conflict = assignment_conflict_namespace['has_assignment_conflict'](
                client,
                journal,
                refreshed_submission,
                reviewer_profile_id,
                conflict_type='openreview'
            )
            edge_kwargs = {'label': 'Previous Reviewer Conflict Override'} if has_openreview_conflict else {}
            try:
                posted_edge = client.post_edge(openreview.api.Edge(
                    invitation=reviewer_assignment_invitation_for_post(refreshed_submission),
                    signatures=[journal.venue_id],
                    head=refreshed_submission.id,
                    tail=reviewer_profile_id,
                    weight=1,
                    **edge_kwargs,
                ))
                posted.append(posted_edge)
                assigned_tails.add(reviewer_profile_id)
            except Exception as error:
                print(
                    "Could not auto-assign selected previous reviewer "
                    f"{reviewer_profile_id} for Paper{refreshed_submission.number}: {error}"
                )
        posted_tails = [
            getattr(posted_edge, 'tail', None)
            for posted_edge in posted
            if getattr(posted_edge, 'tail', None)
        ]
        try:
            reviewer_identity_namespace['mark_previous_reviewers_auto_assigned'](
                client,
                journal,
                refreshed_submission,
                posted_tails,
            )
            if not posted_tails:
                reviewer_identity_namespace['refresh_current_reviewer_identity_metadata'](client, journal, refreshed_submission)
        except Exception as error:
            print(f'Could not mark previous reviewer auto-assignment metadata for Paper{refreshed_submission.number}: {error}')
        prep_results['posted_edges'] = posted_tails
        return prep_results

    def ensure_author_contact_ae_invitation(submission):
        contact_invitation_id = f'{journal.venue_id}/Paper{submission.number}/-/Contact_AE'
        paper_authors_id = journal.get_authors_id(number=submission.number)
        paper_action_editors_id = journal.get_action_editors_id(number=submission.number)
        try:
            client.get_invitation(contact_invitation_id)
            return
        except Exception:
            pass
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=openreview.api.Invitation(
                id=contact_invitation_id,
                readers=[paper_authors_id, paper_action_editors_id, journal.get_editors_in_chief_id()],
                writers=[journal.venue_id],
                invitees=[paper_authors_id],
                signatures=[journal.venue_id],
                edit={
                    'signatures': [paper_authors_id],
                    'readers': [paper_authors_id, paper_action_editors_id, journal.get_editors_in_chief_id()],
                    'writers': [journal.get_editors_in_chief_id(), paper_authors_id],
                    'note': {
                        'id': {'param': {'withInvitation': contact_invitation_id, 'optional': True}},
                        'forum': submission.id,
                        'replyto': submission.id,
                        'signatures': [paper_authors_id],
                        'readers': [paper_authors_id, paper_action_editors_id, journal.get_editors_in_chief_id()],
                        'writers': [journal.get_editors_in_chief_id(), paper_authors_id],
                        'content': {
                            'title': {
                                'order': 1,
                                'description': 'Brief subject for the AE.',
                                'value': {'param': {'type': 'string', 'maxLength': 250}}
                            },
                            'message': {
                                'order': 2,
                                'description': 'Private author note to the AE. This will also notify the handling AE by email.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 10000,
                                        'input': 'textarea',
                                        'markdown': True
                                    }
                                }
                            }
                        }
                    }
                },
                process=f'''def process(client, edit, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    note = client.get_note(edit.note.id)
    submission = client.get_note(note.forum)
    author_group_id = journal.get_authors_id(number=submission.number)
    if note.signatures[0] != author_group_id:
        raise openreview.OpenReviewException('Only paper authors can send this private note to the AE.')
    required_readers = [
        author_group_id,
        journal.get_action_editors_id(number=submission.number),
        journal.get_editors_in_chief_id()
    ]
    missing_required_readers = [reader for reader in required_readers if reader not in (note.readers or [])]
    if missing_required_readers:
        raise openreview.OpenReviewException('Author note is missing required paper-note readers.')
    ae_group = client.get_group(journal.get_action_editors_id())
    template = ae_group.content.get('author_contact_email_template_script', {{}}).get('value')
    contact_title = note.content.get('title', {{}}).get('value', 'Author note')
    contact_message = note.content.get('message', {{}}).get('value', '')
    if not template:
        template = """An author sent a private note for {{short_name}} submission {{submission_number}}: {{submission_title}}.

Title: {{contact_title}}

{{contact_message}}

View the note: {{contact_note_url}}
"""
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f"[{{journal.short_name}}] Author note for Action Editor on paper {{submission.number}}: {{submission.content['title']['value']}}",
        message=template.format(
            short_name=journal.short_name,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            contact_title=contact_title,
            contact_message=contact_message,
            contact_note_url=f'{{SITE_URL}}/forum?id={{submission.id}}&noteId={{note.id}}'
        ),
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
'''
            ),
            replacement=True
        )

    latest_edge = client.get_edge(edge.id, True)
    if latest_edge.ddate and not edge.ddate:
        return

    ae_group = client.get_group(journal.get_action_editors_id())
    note = client.get_note(edge.head)
    group = client.get_group(journal.get_action_editors_id(number=note.number))

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

    def add_reader_to_note(note_to_update, reader_id):
        readers = list(note_to_update.readers or [])
        if reader_id in readers or 'everyone' in readers:
            return
        readers.append(reader_id)
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            note=openreview.api.Note(id=note_to_update.id, readers=readers)
        )

    def bridge_previous_version_access_for_action_editors(submission):
        current_action_editors_group_id = journal.get_action_editors_id(number=submission.number)
        for previous_note in get_previous_submission_chain(submission):
            add_reader_to_note(previous_note, current_action_editors_group_id)
            previous_decisions = client.get_notes(
                forum=previous_note.id,
                invitation=journal.get_ae_decision_id(number=previous_note.number)
            )
            previous_reviews = client.get_notes(
                forum=previous_note.id,
                invitation=journal.get_review_id(number=previous_note.number)
            )
            for previous_material in previous_decisions + previous_reviews:
                add_reader_to_note(previous_material, current_action_editors_group_id)

    if action_editor_anonymity_enabled and not group.anonids:
        print(f'Enable anonymous action editor ids for {group.id}')
        try:
            client.post_group_edit(
                invitation=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                readers=[journal.venue_id],
                writers=[journal.venue_id],
                group=openreview.api.Group(
                    id=group.id,
                    signatures=[journal.venue_id],
                    anonids=True
                )
            )
            group = client.get_group(group.id)
        except Exception as error:
            print(f'Could not enable anonymous action editor ids for {group.id}: {error}')

    def notify_action_editor_unassigned(action_editor_id):
        recipients = [action_editor_id]
        subject = f'[{journal.short_name}] You have been unassigned from {journal.short_name} submission {note.number}: {note.content["title"]["value"]}'
        message = ae_group.content['unassignment_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_number=note.number,
            submission_title=note.content['title']['value'],
            contact_info=journal.contact_info,
        )
        client.post_message(
            subject,
            recipients,
            message,
            parentGroup=group.id,
            replyTo=journal.contact_info,
            invitation=journal.get_meta_invitation_id(),
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

    def notify_action_editor_assigned(action_editor_id, is_resubmission, previous_reviewer_assignment_prep_results=None):
        template_key = 'resubmission_assignment_email_template_script' if is_resubmission else 'assignment_email_template_script'
        template = ae_group.content.get(template_key, {}).get('value')
        if not template:
            return
        previous_reviewer_assignment_prep_text = reviewer_identity_namespace['format_previous_reviewer_assignment_prep_for_email'](previous_reviewer_assignment_prep_results or {})
        subject = f'[{journal.short_name}] Assignment to manage {journal.short_name} submission {note.number}: {note.content["title"]["value"]}'
        if is_resubmission:
            subject = f'[{journal.short_name}] Resubmission assignment for {journal.short_name} submission {note.number}: {note.content["title"]["value"]}'
        message = template.format(
            short_name=journal.short_name,
            submission_number=note.number,
            submission_title=note.content['title']['value'],
            contact_info=journal.contact_info,
            invitation_url=f'{{SITE_URL}}/forum?id={note.id}&role_context=ae',
            number_of_reviewers=journal.get_number_of_reviewers(),
            previous_reviewer_assignment_prep_section=previous_reviewer_assignment_prep_text
        )
        client.post_message(
            subject,
            [action_editor_id],
            message,
            parentGroup=group.id,
            replyTo=journal.contact_info,
            invitation=journal.get_meta_invitation_id(),
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

    def expire_action_editor_assignment(active_assignment, now):
        print(f'Expire previous action editor assignment {active_assignment.tail} for {group.id}')
        client.post_edge(openreview.api.Edge(
            id=active_assignment.id,
            invitation=getattr(active_assignment, 'invitation', None) or ae_assignment_id,
            signatures=active_assignment.signatures or [journal.get_editors_in_chief_id()],
            head=active_assignment.head,
            tail=active_assignment.tail,
            weight=active_assignment.weight,
            label=active_assignment.label,
            ddate=now
        ))

    def remove_action_editor_member(action_editor_id):
        if action_editor_id not in group.members:
            return
        print(f'Remove member {action_editor_id} from {group.id}')
        notify_action_editor_unassigned(action_editor_id)
        client.remove_members_from_group(group.id, action_editor_id)

    def ensure_no_current_action_editor_assignment():
        active_assignment_edges = [
            assignment for assignment in get_assignment_edges(head=edge.head)
            if not assignment.ddate and assignment.id != edge.id
        ]
        current_action_editor_ids = set(
            assignment.tail
            for assignment in active_assignment_edges
            if getattr(assignment, 'tail', None) and assignment.tail != edge.tail
        )
        current_action_editor_ids.update(
            action_editor_id
            for action_editor_id in list(group.members or [])
            if action_editor_id != edge.tail
        )
        if current_action_editor_ids:
            raise openreview.OpenReviewException(
                'This paper already has an Action Editor assigned. '
                'Unassign the current Action Editor before assigning another.'
            )

    def add_action_editor_assignment():
        ensure_no_current_action_editor_assignment()
        if edge.tail not in group.members:
            print(f'Add member {edge.tail} to {group.id}')
            client.add_members_to_group(group.id, edge.tail)
            return True
        return False

    if edge.ddate and edge.tail in group.members:
        remove_action_editor_member(edge.tail)

        content = {}
        if 'assigned_action_editor' in note.content and note.content['assigned_action_editor']['value'] == edge.tail:
            content['assigned_action_editor'] = {'delete': True}

        if content and journal.assigned_AE_venue_id == note.content['venueid']['value']:
            content['venueid'] = {'value': journal.assigning_AE_venue_id}
            content['venue'] = {'value': f'{journal.short_name} Assigning AE'}

        if content:
            client.post_note_edit(
                invitation=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                note=openreview.api.Note(
                    id=note.id,
                    content=content
                )
            )
        return

    if not edge.ddate:
        was_submitted_stage = note.content.get('venueid', {}).get('value') != journal.under_review_venue_id
        add_action_editor_assignment()
        is_resubmission_assignment = bool(get_previous_submission_chain(note))
        previous_reviewer_assignment_prep_results = {}

        print('Expire AE recommendation')
        set_invitation_expiration_date(
            journal.get_ae_recommendation_id(number=note.number),
            openreview.tools.datetime_millis(datetime.datetime.now())
        )

        content = {}
        if 'assigned_action_editor' in note.content:
            content['assigned_action_editor'] = {'delete': True}

        if journal.assigning_AE_venue_id == note.content['venueid']['value']:
            content['venueid'] = {'value': journal.assigned_AE_venue_id}
            content['venue'] = {'value': f'{journal.short_name} Assigned AE'}

        if content:
            client.post_note_edit(
                invitation=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                readers=[journal.venue_id, editors_in_chief_id, journal.get_action_editors_id(number=note.number)],
                note=openreview.api.Note(
                    id=note.id,
                    content=content
                )
            )

        ensure_author_contact_ae_invitation(note)
        bridge_previous_version_access_for_action_editors(note)

        reviewer_assignment_invitation_id = journal.get_reviewer_assignment_id(number=note.number)
        decision_invitation_id = journal.get_ae_decision_id(number=note.number)
        reviewer_assignment_invitation_exists = invitation_exists_and_active(reviewer_assignment_invitation_id)
        decision_invitation_exists = invitation_exists_and_active(decision_invitation_id)

        if was_submitted_stage and decision_invitation_exists:
            print('Deactivate submitted-stage decision invitation')
            try:
                client.post_invitation_edit(
                    invitations=journal.get_meta_invitation_id(),
                    signatures=[journal.venue_id],
                    invitation=openreview.api.Invitation(
                        id=decision_invitation_id,
                        signatures=[journal.venue_id],
                        ddate=openreview.tools.datetime_millis(datetime.datetime.now())
                    ),
                    replacement=True
                )
                decision_invitation_exists = False
            except Exception as error:
                print(f'Could not deactivate submitted-stage decision invitation for Paper{note.number}: {error}')

        if note.content.get('venueid', {}).get('value') == journal.under_review_venue_id and reviewer_assignment_invitation_exists and decision_invitation_exists:
            decision_duedate = datetime.datetime.now() + datetime.timedelta(
                weeks=(
                    journal.get_reviewer_assignment_period_length() +
                    journal.get_review_period_length() +
                    journal.get_discussion_period_length() +
                    journal.get_recommendation_period_length() +
                    journal.get_decision_period_length()
                )
            )
            refresh_decision_invitation_from_super(note, datetime.datetime.now(), decision_duedate)
            if not under_review_stage_invitations_ready(note):
                try:
                    run_under_review_setup_process(note)
                except Exception as error:
                    print(f'Could not repair missing under-review stage invitations for submission {note.id}: {error}')
            setup_paper_reviewer_assignment_overlay(note, active_action_editor_tail=edge.tail)
            previous_reviewer_assignment_prep_results = post_selected_previous_reviewer_assignments(note)
            notify_action_editor_assigned(edge.tail, is_resubmission_assignment, previous_reviewer_assignment_prep_results)
            return

        print('Set up submission for review')
        posted_under_review_transition = False
        try:
            client.post_note_edit(
                invitation=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                note=openreview.api.Note(
                    id=note.id,
                    content={
                        '_bibtex': {'value': journal.get_bibtex(note, journal.under_review_venue_id)},
                        'venueid': {'value': journal.under_review_venue_id},
                        'venue': {'value': f'Under review for {journal.short_name}'}
                    }
                )
            )
            posted_under_review_transition = True
        except Exception as error:
            print(f'Could not post under-review transition for submission {note.id}: {error}')

        if not posted_under_review_transition and note.content.get('venueid', {}).get('value') != journal.under_review_venue_id:
            client.post_note_edit(
                invitation=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                readers=[journal.venue_id, editors_in_chief_id, journal.get_action_editors_id(number=note.number)],
                note=openreview.api.Note(
                    id=note.id,
                    content={
                        'venueid': {'value': journal.under_review_venue_id},
                        'venue': {'value': f'Under review for {journal.short_name}'}
                    }
                )
            )

        note = client.get_note(edge.head)
        if note.content.get('venueid', {}).get('value') != journal.under_review_venue_id:
            raise openreview.OpenReviewException(
                f'Could not transition Paper{note.number} to under review after Action Editor assignment.'
            )
        try:
            run_under_review_setup_process(note)
        except Exception as error:
            print(f'Could not run under-review setup process for submission {note.id}: {error}')

        try:
            setup_under_review_submission_with_eic_child_readers(note)
            client.post_invitation_edit(
                invitations=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                invitation=openreview.api.Invitation(
                    id=f'{journal.venue_id}/Paper{note.number}/-/Review_Approval',
                    signatures=[journal.venue_id],
                    ddate=openreview.tools.datetime_millis(datetime.datetime.now())
                ),
                replacement=True
            )
        except Exception as error:
            print(f'Could not complete built-in under-review setup for submission {note.id}: {error}')

        reviewer_assignment_duedate = journal.get_due_date(weeks=journal.get_reviewer_assignment_period_length())
        decision_duedate = datetime.datetime.now() + datetime.timedelta(
            weeks=(
                journal.get_reviewer_assignment_period_length() +
                journal.get_review_period_length() +
                journal.get_discussion_period_length() +
                journal.get_recommendation_period_length() +
                journal.get_decision_period_length()
            )
        )

        if not reviewer_assignment_invitation_exists:
            journal.invitation_builder.set_reviewer_assignment_invitation(note, reviewer_assignment_duedate)
        refresh_decision_invitation_from_super(note, datetime.datetime.now(), decision_duedate)
        setup_paper_reviewer_assignment_overlay(note, active_action_editor_tail=edge.tail)
        previous_reviewer_assignment_prep_results = post_selected_previous_reviewer_assignments(note)
        notify_action_editor_assigned(edge.tail, is_resubmission_assignment, previous_reviewer_assignment_prep_results)
