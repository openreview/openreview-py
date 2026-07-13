def process(client, edit, invitation):

    import json
    import html
    import datetime
    import re
    import time

    builder_namespace = {
        'openreview': openreview,
        'datetime': datetime,
        'json': json,
        'html': html,
        're': re,
    }
    for builder_script in [
        "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/signature_helpers.py}}",
        "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_invitation_refresh.py}}",
        "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_hub_refresh_trigger.py}}",
        "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/editorial_comment_refresh.py}}",
        "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/decision_refresh.py}}",
        "{{PYTHON_SCRIPT_JSON:invitations/venue/status/paper_status_refresh.py}}",
        "{{PYTHON_SCRIPT_JSON:invitations/venue/super_invitation_child_edit.py}}",
    ]:
        exec(builder_script, builder_namespace)

    note = client.get_note(edit.note.id)

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    editors_in_chief_id = f'{journal.venue_id}/Editors_In_Chief'

    now = openreview.tools.datetime_millis(datetime.datetime.now())

    def expire_unsupported_invitation(invitation_id):
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
            print(f'Could not deactivate unsupported under-review invitation {invitation_id}: {error}')

    paper_prefix = f'{journal.venue_id}/Paper{note.number}'
    for unsupported_invitation_id in [
        f'{paper_prefix}/-/Revision',
        f'{paper_prefix}/-/Withdrawal',
        f'{paper_prefix}/-/Official_Comment',
        f'{paper_prefix}/-/Official_Recommendation_Enabling',
        f'{paper_prefix}/-/Official_Recommendation',
        f'{paper_prefix}/-/Message',
        journal.get_revision_id(number=note.number),
        journal.get_withdrawal_id(number=note.number),
        journal.get_official_comment_id(number=note.number),
        journal.get_official_recommendation_enabling_id(number=note.number),
        journal.get_reviewer_recommendation_id(number=note.number),
        journal.get_reviewers_message_id(number=note.number),
    ]:
        expire_unsupported_invitation(unsupported_invitation_id)

    try:
        builder_namespace['setup_under_review_submission_with_eic_child_readers'](client, journal, note)
    except Exception as error:
        print(f"Could not complete built-in under-review setup for submission {note.id}: {error}")
    try:
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
        print(f'Could not deactivate hidden review approval invitation for Paper{note.number}: {error}')

    duedate = journal.get_due_date(weeks=journal.get_reviewer_assignment_period_length())
    decision_duedate = datetime.datetime.now() + datetime.timedelta(
        weeks=(
            journal.get_reviewer_assignment_period_length() +
            journal.get_review_period_length() +
            journal.get_discussion_period_length() +
            journal.get_recommendation_period_length() +
            journal.get_decision_period_length()
        )
    )
    number_of_reviewers = journal.get_number_of_reviewers()
    reviewers_max_papers = journal.get_reviewers_max_papers()

    try:
        journal.invitation_builder.set_reviewer_assignment_invitation(note, duedate)
    except Exception as error:
        print(f"Could not set reviewer assignment invitation for submission {note.id}: {error}")

    builder_namespace['refresh_reviewer_assignment_invitation'](
        client,
        journal,
        note,
        duedate
    )
    builder_namespace['trigger_reviewer_assignment_hub_refresh'](client, journal, note)
    builder_namespace['refresh_decision_invitation'](client, journal, note, decision_duedate, datetime)

    paper_authors_id = journal.get_authors_id(number=note.number)
    paper_action_editors_id = journal.get_action_editors_id(number=note.number)
    paper_reviewers_id = journal.get_reviewers_id(number=note.number)
    paper_authorids = [
        authorid for authorid in note.content.get('authorids', {}).get('value', [])
        if isinstance(authorid, str) and authorid
    ]
    author_nonreaders = [paper_authors_id] + paper_authorids

    def add_author_nonreaders(invitation_ids):
        for invitation_id in invitation_ids:
            try:
                live_invitation = client.get_invitation(invitation_id)
            except Exception as error:
                print(f'Could not load {invitation_id} for author nonreaders: {error}')
                continue
            live_invitation.nonreaders = author_nonreaders
            if isinstance(live_invitation.edit, dict):
                live_invitation.edit['nonreaders'] = author_nonreaders
            try:
                client.post_invitation_edit(
                    invitations=journal.get_meta_invitation_id(),
                    signatures=[journal.venue_id],
                    invitation=live_invitation,
                    replacement=True
                )
            except Exception as error:
                print(f'Could not update {invitation_id} with author nonreaders: {error}')

    paper_action_editor_group = client.get_group(id=journal.get_action_editors_id(number=note.number))
    fixed_action_editor_signature = None
    last_signature_error = None
    for _ in range(10):
        try:
            paper_action_editor_group = client.get_group(id=journal.get_action_editors_id(number=note.number))
            fixed_action_editor_signature = builder_namespace['resolve_active_action_editor_signature'](
                client,
                journal,
                note,
                paper_action_editor_group
            )
            break
        except Exception as error:
            last_signature_error = error
            time.sleep(0.5)
    if not fixed_action_editor_signature:
        raise openreview.OpenReviewException(
            f'Could not resolve active anonymous action editor signature for Paper{note.number}: {last_signature_error}'
        )
    action_editor_signatures = builder_namespace['paper_editorial_action_signatures'](journal, fixed_action_editor_signature)

    builder_namespace['refresh_editorial_comment_invitation'](
        client,
        journal,
        note,
        fixed_action_editor_signature,
        paper_authors_id,
        paper_reviewers_id
    )

    add_author_nonreaders([
        journal.get_reviewer_assignment_id(number=note.number),
        journal.get_ae_decision_id(number=note.number),
        f'{journal.venue_id}/Paper{note.number}/-/Editorial_Comment'
    ])

    def post_operational_conflict_notice():
        try:
            eic_members = set(client.get_group(journal.get_editors_in_chief_id()).members or [])
        except Exception:
            eic_members = set()
        try:
            me_members = set(client.get_group(editors_in_chief_id).members or [])
        except Exception:
            me_members = set()
        conflicted_authorids = sorted(set(paper_authorids).intersection(eic_members.union(me_members)))
        if not conflicted_authorids:
            return
        notice_title = 'JMLR Operational Conflict Notice'
        try:
            existing_notices = client.get_notes(forum=note.id)
        except Exception:
            existing_notices = []
        for existing_notice in existing_notices:
            if existing_notice.content.get('title', {}).get('value') == notice_title:
                return
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            note=openreview.api.Note(
                forum=note.id,
                replyto=note.id,
                signatures=[journal.venue_id],
                readers=[
                    paper_action_editors_id,
                    paper_reviewers_id
                ],
                writers=[journal.venue_id],
                content={
                    'title': {'value': notice_title},
                    'comment': {
                        'value': (
                            'Some authors have JMLR operational conflicts. '
                            'Reviewers should use Contact Action Editor; AEs should contact non-conflicted editors. '
                            'Do not use broad editor mailing lists for this paper.'
                        )
                    }
                }
            )
        )

    post_operational_conflict_notice()

    contact_action_editor_id = f'{journal.venue_id}/Paper{note.number}/-/Contact_Action_Editor'
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=openreview.api.Invitation(
            id=contact_action_editor_id,
            readers=[
                paper_action_editors_id,
                journal.get_editors_in_chief_id(),
                paper_reviewers_id
            ],
            nonreaders=author_nonreaders,
            writers=[journal.venue_id],
            invitees=[paper_reviewers_id],
            signatures=[journal.venue_id],
            edit={
                'signatures': {
                    'param': {
                        'items': [
                            {
                                'prefix': f'{journal.venue_id}/Paper{note.number}/Reviewer_'
                            }
                        ]
                    }
                },
                'readers': [
                    paper_action_editors_id,
                    journal.get_editors_in_chief_id(),
                    editors_in_chief_id,
                    '${2/signatures}'
                ],
                'nonreaders': author_nonreaders,
                'writers': [journal.get_editors_in_chief_id(), '${2/signatures}'],
                'note': {
                    'forum': note.id,
                    'replyto': note.id,
                    'signatures': ['${3/signatures}'],
                    'readers': [
                        journal.get_editors_in_chief_id(),
                        editors_in_chief_id,
                        paper_action_editors_id,
                        '${3/signatures}'
                    ],
                    'nonreaders': author_nonreaders,
                    'writers': [journal.venue_id],
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief subject for the Action Editor about requested or completed review changes.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 250
                                }
                            }
                        },
                        'message': {
                            'order': 2,
                            'description': 'Private reviewer note to the Action Editor explaining requested or completed changes. This will also notify the Action Editor by email.',
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
    reviewer_signature = note.signatures[0]
    expected_prefix = f'{{journal.venue_id}}/Paper{{submission.number}}/Reviewer_'
    if not reviewer_signature.startswith(expected_prefix):
        raise openreview.OpenReviewException('Only an assigned anonymous reviewer can contact the Action Editor.')
    required_readers = [
        journal.get_action_editors_id(number=submission.number),
        journal.get_editors_in_chief_id(),
        f'{{journal.venue_id}}/Editors_In_Chief',
        reviewer_signature
    ]
    missing_required_readers = [reader for reader in required_readers if reader not in (note.readers or [])]
    if missing_required_readers:
        raise openreview.OpenReviewException('Reviewer note is missing required paper-note readers.')
    ae_group = client.get_group(journal.get_action_editors_id())
    template = ae_group.content.get('reviewer_contact_email_template_script', {{}}).get('value')
    if not template:
        return
    contact_title = note.content.get('title', {{}}).get('value', 'Reviewer note about changes')
    contact_message = note.content.get('message', {{}}).get('value', '')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f"[{{journal.short_name}}] Reviewer note for Action Editor on paper {{submission.number}}: {{submission.content['title']['value']}}",
        message=template.format(
            short_name=journal.short_name,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            reviewer_signature=reviewer_signature.split('/')[-1].replace('_', ' ', 1),
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

    author_note_id = f'{journal.venue_id}/Paper{note.number}/-/Contact_AE'
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=openreview.api.Invitation(
            id=author_note_id,
            readers=[
                paper_authors_id,
                paper_action_editors_id,
                journal.get_editors_in_chief_id()
            ],
            writers=[journal.venue_id],
            invitees=[paper_authors_id],
            signatures=[journal.venue_id],
            edit={
                'signatures': [paper_authors_id],
                'readers': [
                    paper_authors_id,
                    paper_action_editors_id,
                    journal.get_editors_in_chief_id()
                ],
                'writers': [paper_authors_id],
                'note': {
                    'forum': note.id,
                    'replyto': note.id,
                    'signatures': [paper_authors_id],
                    'readers': [
                        paper_authors_id,
                        paper_action_editors_id,
                        journal.get_editors_in_chief_id()
                    ],
                    'writers': [journal.venue_id],
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief subject for the AE.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 250
                                }
                            }
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
        raise openreview.OpenReviewException('Only paper authors can send this private note to the Action Editor.')
    required_readers = [
        author_group_id,
        journal.get_action_editors_id(number=submission.number),
        journal.get_editors_in_chief_id()
    ]
    missing_required_readers = [reader for reader in required_readers if reader not in (note.readers or [])]
    if missing_required_readers:
        raise openreview.OpenReviewException('Author note is missing required paper-note readers.')
    if note.tcdate != note.tmdate:
        print('Author Contact AE note edited, exit')
        return
    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        note=openreview.api.Note(
            id=note.id,
            writers=[journal.venue_id]
        )
    )
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

    builder_namespace['refresh_paper_status_note'](client, journal, note)
