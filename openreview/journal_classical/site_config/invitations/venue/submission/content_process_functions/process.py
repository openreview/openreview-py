def process(client, edit, invitation):
    import datetime
    import time

    note = client.get_note(edit.note.id)

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    site_url = "{{SITE_URL}}"
    previous_submission_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/submission/previous_submission_helpers.py}}", previous_submission_namespace)
    invitation_edit_namespace = {"openreview": openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/invitation_edit_helpers.py}}", invitation_edit_namespace)
    set_invitation_expiration_date = invitation_edit_namespace["set_invitation_expiration_date"]
    previous_note_from_content = previous_submission_namespace["previous_note_from_content"]
    previous_notes_from_list = previous_submission_namespace["previous_notes_from_list"]
    previous_submission_chain = previous_submission_namespace["previous_submission_chain"]
    previous_submissions_markdown = previous_submission_namespace["previous_submissions_markdown"]
    parse_forum_id = previous_submission_namespace["parse_forum_id"]

    def previous_submission_number_for_receipt():
        previous_submission = previous_note_from_content(client, journal, note.content or {})
        if previous_submission:
            return str(previous_submission.number)
        previous_notes = previous_notes_from_list(client, journal, note.content or {})
        if previous_notes:
            return str(previous_notes[0].number)
        previous_number = (note.content or {}).get("previous_JMLR_submission_number", {}).get("value")
        previous_number = str(previous_number or "").strip()
        if previous_number and previous_number.upper() != "N/A" and previous_number.isdigit():
            return previous_number
        return ""

    def send_author_submission_receipt():
        author_group = client.get_group(journal.get_authors_id())
        author_email_template = author_group.content.get('new_submission_email_template_script', {}).get('value')
        if not author_email_template:
            return
        receipt_previous_number = previous_submission_number_for_receipt()
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            subject=f'[{journal.short_name}] New submission to {journal.short_name}: {note.content["title"]["value"]}',
            recipients=note.content['authorids']['value'],
            message=author_email_template.format(
                short_name=journal.short_name,
                submission_id=note.id,
                submission_number=note.number,
                submission_title=note.content['title']['value'],
                paper_url=f'{{SITE_URL}}/forum?id={note.id}',
                receipt_intro=(
                    f"Your resubmission/revision of JMLR Paper {receipt_previous_number} has been received."
                    if receipt_previous_number
                    else f"Your submission to {journal.short_name} has been received."
                )
            ),
            replyTo=journal.contact_info,
            signature=journal.venue_id,
            sender=journal.get_message_sender()
        )

    def ensure_previous_submissions_list(previous_submission):
        if not note.content.get("previous_JMLR_submissions", {}).get("value"):
            client.post_note_edit(
                invitation=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                note=openreview.api.Note(
                    id=note.id,
                    content={
                        "previous_JMLR_submissions": {
                            "value": previous_submissions_markdown(client, journal, site_url, previous_submission)
                        }
                    }
                )
            )
        remove_previous_submission_scalar_fields()

    def remove_previous_submission_scalar_fields():
        content = {}
        if "previous_JMLR_submission_number" in (note.content or {}):
            content["previous_JMLR_submission_number"] = {"delete": True}
        if "previous_JMLR_submission_URL" in (note.content or {}):
            content["previous_JMLR_submission_URL"] = {"delete": True}
        if not content:
            return
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            readers=note.readers,
            writers=[journal.venue_id],
            note=openreview.api.Note(
                id=note.id,
                content=content
            )
        )

    def expire_previous_resubmission_invitation(previous_note):
        if not previous_note:
            return
        invitation_id = f"{journal.venue_id}/Paper{previous_note.number}/-/Resubmission"
        expiration_date = openreview.tools.datetime_millis(datetime.datetime.now())
        try:
            set_invitation_expiration_date(client, journal, invitation_id, expiration_date)
        except Exception as error:
            print(f"Could not expire previous resubmission invitation {invitation_id}: {error}")

    def expire_previous_resubmission_invitations(first_previous_note):
        previous_notes = []
        seen_note_ids = set()
        for previous_note in previous_submission_chain(client, journal, first_previous_note):
            if previous_note and previous_note.id not in seen_note_ids:
                previous_notes.append(previous_note)
                seen_note_ids.add(previous_note.id)
        for previous_note in previous_notes_from_list(client, journal, note.content or {}):
            if previous_note and previous_note.id not in seen_note_ids:
                previous_notes.append(previous_note)
                seen_note_ids.add(previous_note.id)
        for previous_note in previous_notes:
            expire_previous_resubmission_invitation(previous_note)

    def add_reader_to_note(note_to_update, reader_id):
        readers = list(note_to_update.readers or [])
        if not reader_id or reader_id in readers or "everyone" in readers:
            return
        readers.append(reader_id)
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            note=openreview.api.Note(id=note_to_update.id, readers=readers)
        )

    def is_released_previous_note(note_to_check, previous_note):
        readers = set(note_to_check.readers or [])
        return (
            "everyone" in readers
            or journal.get_authors_id(number=previous_note.number) in readers
            or journal.get_reviewers_id(number=previous_note.number) in readers
        )

    def bridge_previous_version_access_for_current_paper_roles(first_previous_note):
        current_authors_group_id = journal.get_authors_id(number=note.number)
        current_reviewers_group_id = journal.get_reviewers_id(number=note.number)
        current_action_editors_group_id = journal.get_action_editors_id(number=note.number)
        for previous_note in previous_submission_chain(client, journal, first_previous_note):
            add_reader_to_note(previous_note, current_authors_group_id)
            add_reader_to_note(previous_note, current_reviewers_group_id)
            add_reader_to_note(previous_note, current_action_editors_group_id)
            previous_decisions = client.get_notes(
                forum=previous_note.id,
                invitation=journal.get_ae_decision_id(number=previous_note.number)
            )
            for decision_note in previous_decisions:
                add_reader_to_note(decision_note, current_authors_group_id)
                add_reader_to_note(decision_note, current_reviewers_group_id)
                add_reader_to_note(decision_note, current_action_editors_group_id)
            previous_reviews = client.get_notes(
                forum=previous_note.id,
                invitation=journal.get_review_id(number=previous_note.number)
            )
            for previous_review_note in previous_reviews:
                add_reader_to_note(previous_review_note, current_action_editors_group_id)
                if is_released_previous_note(previous_review_note, previous_note):
                    add_reader_to_note(previous_review_note, current_authors_group_id)
                    add_reader_to_note(previous_review_note, current_reviewers_group_id)
            previous_author_notes = []
            for author_note_invitation_id in [
                f"{journal.venue_id}/Paper{previous_note.number}/-/Contact_AE",
                f"{journal.venue_id}/Paper{previous_note.number}/-/Author_Note_To_Action_Editor"
            ]:
                try:
                    previous_author_notes += client.get_notes(
                        forum=previous_note.id,
                        invitation=author_note_invitation_id
                    )
                except Exception:
                    pass
            for author_note in previous_author_notes:
                add_reader_to_note(author_note, current_authors_group_id)

    def setup_pre_ae_decision_invitation():
        venue_id = journal.venue_id
        paper_group_id = f"{venue_id}/Paper{note.number}"
        paper_author_group_id = f"{paper_group_id}/Authors"
        paper_action_editors_group_id = f"{paper_group_id}/Action_Editors"
        paper_reviewers_group_id = f"{paper_group_id}/Reviewers"
        editors_in_chief_id = journal.get_editors_in_chief_id()
        authorids = [
            authorid
            for authorid in note.content.get("authorids", {}).get("value", [])
            if authorid
        ]
        decision_invitation_id = f"{paper_group_id}/-/Decision"
        selected_signature_param = "$" + "{3/signatures}"
        now = datetime.datetime.now()

        def content_value(key, default=""):
            value = note.content.get(key, {}).get("value")
            return str(value if value is not None else default)

        try:
            client.get_invitation(decision_invitation_id)
        except Exception:
            client.post_invitation_edit(
                invitations=f"{venue_id}/-/Decision",
                signatures=[venue_id],
                readers=[editors_in_chief_id],
                writers=[venue_id],
                content={
                    "noteId": {"value": note.id},
                    "noteNumber": {"value": note.number},
                    "cdate": {"value": openreview.tools.datetime_millis(now)},
                    "duedate": {"value": openreview.tools.datetime_millis(now + datetime.timedelta(days=7))},
                },
                await_process=True,
            )

        decision_invitation = None
        for attempt in range(6):
            try:
                decision_invitation = client.get_invitation(decision_invitation_id)
                break
            except Exception:
                if attempt == 5:
                    raise
                time.sleep(0.5)
        early_rejection_comment = "{{MESSAGE_TEMPLATE_JSON:decision/pre_ae_rejection_comment_default.txt}}".format(
            submission_number=note.number,
            submission_title=content_value("title", f"Paper {note.number}"),
        )
        decision_invitation.invitations = [f"{venue_id}/-/Decision"]
        decision_invitation.readers = [editors_in_chief_id]
        decision_invitation.nonreaders = [paper_author_group_id] + authorids
        decision_invitation.writers = [venue_id]
        decision_invitation.invitees = [editors_in_chief_id]
        decision_invitation.signatures = [venue_id]
        decision_invitation.maxReplies = 1
        decision_invitation.minReplies = 1
        decision_invitation.edit = {
            "signatures": {"param": {"items": [{"value": editors_in_chief_id, "optional": True}]}},
            "readers": [editors_in_chief_id],
            "nonreaders": [paper_author_group_id] + authorids,
            "writers": [editors_in_chief_id],
            "note": {
                "forum": note.id,
                "replyto": note.id,
                "signatures": [selected_signature_param],
                "readers": [editors_in_chief_id, paper_action_editors_group_id, paper_reviewers_group_id],
                "nonreaders": [paper_author_group_id] + authorids,
                "writers": [editors_in_chief_id],
                "content": {
                    "recommendation": {
                        "order": 1,
                        "description": "Pre-assignment Decision. The only allowed recommendation before assigning the first Action Editor is Reject without resubmission.",
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": ["Reject without resubmission"],
                                "input": "radio",
                                "default": "Reject without resubmission",
                            }
                        },
                    },
                    "comment": {
                        "order": 2,
                        "description": "Decision comments to record the reason for not sending this paper to Action Editor assignment. The default text may be edited before submission.",
                        "value": {
                            "param": {
                                "type": "string",
                                "maxLength": 200000,
                                "input": "textarea",
                                "markdown": True,
                                "default": early_rejection_comment,
                            }
                        },
                    },
                },
            },
        }
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[venue_id],
            readers=[venue_id],
            writers=[venue_id],
            invitation=decision_invitation,
            replacement=True,
        )

    def setup_assignment_setup_automation_invitation(previous_submission=None):
        venue_id = journal.venue_id
        automation_invitation_id = f"{venue_id}/Paper{note.number}/-/Assignment_Setup_Automation"
        now = datetime.datetime.now()
        dateprocesses = [
            {
                "dates": [
                    openreview.tools.datetime_millis(now + datetime.timedelta(minutes={{ASSIGNMENT_SETUP_AUTOMATION_DELAY_MINUTES}})),
                ],
                "script": "{{PYTHON_SCRIPT_JSON:invitations/venue/setup_assignments/dateprocess_setup_assignment_pages.py}}",
            }
        ]
        if previous_submission:
            dateprocesses.append(
                {
                    "dates": [
                        openreview.tools.datetime_millis(now + datetime.timedelta(hours=2)),
                    ],
                    "script": "{{PYTHON_SCRIPT_JSON:invitations/venue/setup_assignments/dateprocess_auto_assign_previous_ae.py}}",
                }
            )
        automation_invitation = openreview.api.Invitation(
            id=automation_invitation_id,
            readers=[venue_id, journal.get_editors_in_chief_id()],
            writers=[venue_id],
            signatures=[venue_id],
            invitees=[],
            content={
                "noteId": {"value": note.id},
                "noteNumber": {"value": note.number},
                "setupInvitationId": {"value": f"{venue_id}/-/Setup_Assignments"},
            },
        )
        automation_invitation.dateprocesses = dateprocesses
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[venue_id],
            invitation=automation_invitation,
            replacement=True,
        )

    previous_submission = None
    previous_forum_id = None
    previous_submission_url = note.content.get("previous_JMLR_submission_URL", {}).get("value")
    if previous_submission_url and previous_submission_url != "N/A":
        try:
            previous_forum_id = parse_forum_id(previous_submission_url)
            if not previous_forum_id:
                raise ValueError("missing previous forum id")
            previous_submission = client.get_note(previous_forum_id)
        except Exception:
            raise openreview.OpenReviewException(
                'Failed to parse the Previous Submission Link. Please make sure your link includes the forum ID after "forum?id=".'
            )

        previous_decisions = client.get_notes(
            forum=previous_submission.id,
            invitation=getattr(journal, "get_decision_id", journal.get_ae_decision_id)(previous_submission.number)
        )
        if any(
            decision.content.get("recommendation", {}).get("value") == "Reject without resubmission"
            for decision in previous_decisions
        ):
            raise openreview.OpenReviewException(
                "This previous JMLR submission was rejected without resubmission, so it cannot be resubmitted to JMLR."
            )
        ensure_previous_submissions_list(previous_submission)
    else:
        previous_notes = previous_notes_from_list(client, journal, note.content or {})
        previous_submission = previous_notes[0] if previous_notes else None
        previous_forum_id = previous_submission.id if previous_submission else None
        if previous_submission:
            ensure_previous_submissions_list(previous_submission)
        else:
            remove_previous_submission_scalar_fields()

    ## setup paper-scoped groups and expertise without creating unsupported
    ## generic journal actions such as Withdrawal, Revision, Official_Comment,
    ## or reviewer Message.
    journal.group_builder.setup_submission_groups(note)
    send_author_submission_receipt()
    setup_pre_ae_decision_invitation()
    setup_assignment_setup_automation_invitation(previous_submission)
    journal.assignment.request_expertise(note, journal.get_action_editors_id())
    journal.assignment.request_expertise(note, journal.get_reviewers_id())

    if previous_submission:
        try:
            bridge_previous_version_access_for_current_paper_roles(previous_submission)
        except Exception as error:
            print(f"Previous submission role-group access was not bridged for Paper{note.number}: {error}")
        expire_previous_resubmission_invitations(previous_submission)

    def deactivate_unsupported_invitation(invitation_id):
        live_invitation = None
        for _ in range(6):
            try:
                live_invitation = client.get_invitation(invitation_id)
                break
            except Exception:
                time.sleep(0.5)
        if not live_invitation:
            return
        try:
            client.post_invitation_edit(
                invitations=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                invitation=openreview.api.Invitation(
                    id=invitation_id,
                    expdate=now - 1
                ),
                replacement=False
            )
        except Exception as error:
            print(f"Could not deactivate unsupported invitation {invitation_id}: {error}")

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    unsupported_invitation_ids = [
        f'{journal.venue_id}/Paper{note.number}/-/Revision',
        f'{journal.venue_id}/Paper{note.number}/-/Withdrawal',
        f'{journal.venue_id}/Paper{note.number}/-/Official_Comment',
        f'{journal.venue_id}/Paper{note.number}/-/Official_Recommendation_Enabling',
        f'{journal.venue_id}/Paper{note.number}/-/Official_Recommendation',
        f'{journal.venue_id}/Paper{note.number}/-/Message',
        journal.get_revision_id(number=note.number),
        journal.get_withdrawal_id(),
        journal.get_withdrawal_id(number=note.number),
        journal.get_official_comment_id(number=note.number),
        journal.get_official_recommendation_enabling_id(number=note.number),
        journal.get_reviewer_recommendation_id(number=note.number),
        journal.get_reviewers_message_id(number=note.number),
    ]
    for unsupported_invitation_id in unsupported_invitation_ids:
        deactivate_unsupported_invitation(unsupported_invitation_id)
