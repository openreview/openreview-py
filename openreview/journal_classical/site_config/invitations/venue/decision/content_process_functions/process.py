def expire_post_decision_invitations(client, journal, submission):
    number = submission.number
    paper_prefix = f'{journal.venue_id}/Paper{number}'
    now = openreview.tools.datetime_millis(datetime.datetime.now())

    def set_invitation_expiration_date(invitation_id, expiration_date):
        # OpenReview-web still displays expired invitations to users with
        # details.writable. ddate removes final post-decision actions from
        # the forum surface instead of merely styling them as expired. Keep
        # expdate equal to ddate so audit/reporting has one terminal date.
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=openreview.api.Invitation(
                id=invitation_id,
                signatures=[journal.venue_id],
                expdate=expiration_date,
                ddate=expiration_date
            ),
            replacement=False
        )

    invitation_ids = {
        journal.get_review_id(number=number),
        journal.get_reviewer_assignment_id(number=number),
        journal.get_ae_decision_id(number=number),
        f'{paper_prefix}/Action_Editors/-/Assignment',
        f'{paper_prefix}/-/Assign_Action_Editor',
        f'{paper_prefix}/-/Reviewer_Rating',
        f'{paper_prefix}/-/Revision',
        f'{paper_prefix}/-/Contact_AE',
        f'{paper_prefix}/-/Withdrawal',
        f'{paper_prefix}/-/Official_Comment',
        f'{paper_prefix}/-/Official_Recommendation_Enabling',
        f'{paper_prefix}/-/Official_Recommendation',
        f'{paper_prefix}/-/Message',
        journal.get_revision_id(number=number),
        journal.get_withdrawal_id(number=number),
        journal.get_reviewers_message_id(number=number)
    }

    under_review_suffixes = (
        '/-/Review',
        '/Reviewers/-/Assignment',
        '/Action_Editors/-/Assignment',
        '/-/Assign_Action_Editor',
        '/-/Decision',
        '/-/Reviewer_Rating',
        '/-/Revision',
        '/-/Contact_AE',
        '/-/Withdrawal',
        '/-/Official_Comment',
        '/-/Official_Recommendation_Enabling',
        '/-/Official_Recommendation',
        '/-/Message'
    )

    try:
        for live_invitation in client.get_all_invitations(prefix=paper_prefix):
            if live_invitation.id.endswith(under_review_suffixes):
                invitation_ids.add(live_invitation.id)
    except Exception as error:
        print(f'Could not list post-decision invitations for {paper_prefix}: {error}')

    for invitation_id in sorted(invitation_ids):
        try:
            set_invitation_expiration_date(invitation_id, now)
        except Exception as error:
            print(f'Could not deactivate {invitation_id}: {error}')


def create_author_resubmission_invitation(client, journal, submission):
    import urllib.parse

    invitation_id = f'{journal.venue_id}/Paper{submission.number}/-/Resubmission'
    authors_id = journal.get_authors_id(submission.number)
    editors_in_chief_id = journal.get_editors_in_chief_id()
    action_editors_id = journal.get_action_editors_id(submission.number)
    resubmission_readers = [editors_in_chief_id, action_editors_id, authors_id]
    previous_url = f'{{SITE_URL}}/forum?id={submission.id}'
    resubmission_url = (
        f'{{SITE_URL}}/group?'
        + urllib.parse.urlencode({
            'id': journal.venue_id,
            'newSubmission': '1',
            'previous_JMLR_submission_number': str(submission.number),
            'previous_JMLR_submission_URL': previous_url
        })
        + '#new-submission'
    )
    description = (
        f'<p>Submit a revised version of JMLR Paper {submission.number}: '
        f'{submission.content["title"]["value"]}.</p>'
        '<p>Only author ordering changes are allowed for resubmissions. Adding, removing, replacing, '
        'renaming, or otherwise changing authors is not allowed. Impermissible author changes may cause '
        'desk rejection or later rejection at editorial discretion.</p>'
        f'<p><a class="btn btn-primary" href="{resubmission_url}">Start Resubmission</a></p>'
    )
    redirect_web = (
        'var JMLR_RESUBMISSION_URL = ' + repr(resubmission_url) + ';\n'
        'if (typeof window !== "undefined") { window.location.href = JMLR_RESUBMISSION_URL; }\n'
        'return "<p>Redirecting to the JMLR resubmission form.</p>" + '
        '"<p><a class=\\"btn btn-primary\\" href=\\"" + JMLR_RESUBMISSION_URL + "\\">Start Resubmission</a></p>";'
    )
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        readers=resubmission_readers,
        writers=[journal.venue_id],
        invitation=openreview.api.Invitation(
            id=invitation_id,
            signatures=[journal.venue_id],
            readers=resubmission_readers,
            writers=[journal.venue_id],
            invitees=[authors_id],
            description=description,
            web=redirect_web,
            edit={
                'signatures': [authors_id],
                'readers': resubmission_readers,
                'writers': [journal.venue_id],
                'note': {
                    'forum': submission.id,
                    'replyto': submission.id,
                    'signatures': [authors_id],
                    'readers': resubmission_readers,
                    'writers': [journal.venue_id],
                    'content': {
                        'resubmission_url': {
                            'order': 1,
                            'description': 'Open the JMLR resubmission form for this paper.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const': resubmission_url,
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

    def editor_readers(readers):
        if readers == ['everyone']:
            return [editors_in_chief_id]
        return readers + [editors_in_chief_id] if editors_in_chief_id not in readers else readers

    def decision_release_readers(submission):
        return unique_values([
            journal.get_editors_in_chief_id(),
            editors_in_chief_id,
            journal.get_action_editors_id(submission.number),
            journal.get_reviewers_id(submission.number),
            journal.get_authors_id(submission.number)
        ])

    def release_decision_note(submission, decision):
        readers = decision_release_readers(submission)
        release_invitation_id = journal.get_release_decision_id(number=submission.number)
        try:
            release_invitation = client.get_invitation(release_invitation_id)
        except Exception:
            release_invitation = openreview.api.Invitation(id=release_invitation_id)
        release_invitation.signatures = [journal.venue_id]
        release_invitation.readers = [journal.venue_id]
        release_invitation.writers = [journal.venue_id]
        release_invitation.invitees = [journal.venue_id]
        release_invitation.edit = getattr(release_invitation, 'edit', None) or {
            'signatures': [journal.venue_id],
            'readers': readers,
            'writers': [journal.venue_id],
            'note': {
                'id': {
                    'param': {
                        'withInvitation': journal.get_ae_decision_id(number=submission.number)
                    }
                }
            }
        }
        if hasattr(release_invitation, 'ddate'):
            release_invitation.ddate = None
        if hasattr(release_invitation, 'expdate'):
            release_invitation.expdate = None
        release_invitation.edit['readers'] = readers
        release_invitation.edit['nonreaders'] = []
        release_invitation.edit['note']['readers'] = readers
        release_invitation.edit['note']['nonreaders'] = []
        release_invitation.edit['note']['writers'] = [journal.venue_id]
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=release_invitation,
            replacement=True
        )
        client.post_note_edit(
            invitation=journal.get_release_decision_id(number=submission.number),
            signatures=[journal.venue_id],
            note=openreview.api.Note(id=decision.id)
        )

    note=client.get_note(edit.note.id)
    submission = client.get_note(note.forum)

    ## On update or delete return when OpenReview provides the edit id. Some direct
    ## paper-specific invitations do not expose edit.id reliably during process.
    if getattr(edit.note, 'ddate', None):
        return
    edit_id = getattr(edit, 'id', None)
    if edit_id:
        decision_edits = client.get_note_edits(note_id=note.id, sort='tcdate:asc', limit=1)
        if decision_edits and edit_id != decision_edits[0].id:
            existing_decision_approvals = client.get_notes(
                forum=submission.id,
                invitation=f'{journal.venue_id}/Paper{submission.number}/-/Decision_Approval'
            )
            if any(decision_approval.replyto == note.id for decision_approval in existing_decision_approvals):
                return

    expire_post_decision_invitations(client, journal, submission)
    status_namespace['refresh_paper_status_note'](client, journal, submission)

    reviews = client.get_notes(forum=submission.id, invitation=journal.get_review_id(number=submission.number))
    released_reviews = client.get_notes(invitation=journal.get_release_review_id(number=submission.number))
    if reviews and not released_reviews:
        release_reviews_and_comments(submission, reviews, context='after AE decision')

    recommendation = note.content.get('recommendation', {}).get('value', '')
    comment = note.content.get('comment', {}).get('value', '')
    ae_comment_invitation_id = f'{journal.venue_id}/Paper{submission.number}/-/Editorial_Comment'
    ae_comment_text = f'**Recommendation:** {recommendation}'
    if comment:
        ae_comment_text = f'{ae_comment_text}\n\n{comment}'

    try:
        client.post_note_edit(
            invitation=ae_comment_invitation_id,
            signatures=note.signatures,
            note=openreview.api.Note(
                forum=submission.id,
                replyto=submission.id,
                signatures=note.signatures,
                readers=[
                    journal.get_editors_in_chief_id(),
                    journal.get_action_editors_id(submission.number),
                    journal.get_reviewers_id(submission.number)
                ],
                writers=[
                    journal.venue_id,
                    note.signatures[0]
                ],
                content={
                    'title': {
                        'value': 'AE Decision Comments'
                    },
                    'comment': {
                        'value': ae_comment_text
                    }
                }
            )
        )
    except Exception as error:
        print(f'Official AE comment mirror was not created: {error}')

    ## Update submission and set the decision submitted status
    client.post_note_edit(
        invitation = journal.get_meta_invitation_id(),
        readers = editor_readers(journal.get_under_review_submission_readers(submission.number)),
        writers = [journal.venue_id],
        signatures = [journal.venue_id],
        note = openreview.api.Note(
            id = submission.id,
            content = {
                'venue': {
                    'value': f'Decision pending for {journal.short_name}'
                },
                'venueid': {
                    'value': journal.decision_pending_venue_id
                }
            }

        )

    )

    journal.invitation_builder.set_note_decision_approval_invitation(submission, note, journal.get_due_date(days = 7))
    client.post_note_edit(
        invitation=f'{journal.venue_id}/Paper{submission.number}/-/Decision_Approval',
        signatures=[journal.get_editors_in_chief_id()],
        note=openreview.api.Note(
            forum=submission.id,
            replyto=note.id,
            content={
                'approval': { 'value': 'I approve the AE\'s decision.' },
                'comment_to_the_AE': { 'value': 'Automatically approved per JMLR policy.' }
            }
        ),
        await_process=True
    )
