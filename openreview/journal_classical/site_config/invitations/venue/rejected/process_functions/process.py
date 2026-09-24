def process(client, edit, invitation):
    import urllib.parse

    # JMLR delta: Journal has one reject email; JMLR has terminal/permitted outcomes.
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(edit.note.id)
    decisions = client.get_notes(invitation=journal.get_ae_decision_id(number=submission.number))
    permitted = bool(decisions and decisions[0].content.get('resubmission_of_major_revision', {}).get('value'))
    template = (
        "{{EMAIL_TEMPLATE_JSON:author/decision_reject_with_resubmission.txt}}"
        if permitted else
        "{{EMAIL_TEMPLATE_JSON:author/decision_reject_without_resubmission.txt}}"
    )
    subject = "{{EMAIL_TEMPLATE_JSON:author/decision_subject.txt}}".format(
        short_name=journal.short_name,
        submission_number=submission.number,
        submission_title=submission.content['title']['value'],
    ).strip()
    client.post_message(
        invitation=journal.get_meta_invitation_id(), signature=journal.venue_id,
        recipients=[journal.get_authors_id(number=submission.number)],
        subject=subject,
        message=template.format(
            short_name=journal.short_name, submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            paper_url=f'{{SITE_URL}}/forum?id={submission.id}', website=journal.website,
        ),
        replyTo=journal.contact_info, sender=journal.get_message_sender(),
    )
    journal.invitation_builder.expire_paper_invitations(submission)
    journal.invitation_builder.set_note_authors_deanonymization_invitation(submission)
    if not permitted:
        return

    # Journal stores the choice but does not expose a paper-scoped author
    # resubmission action. JMLR adds only that missing navigation surface.
    authors_id = journal.get_authors_id(submission.number)
    readers = [
        journal.get_editors_in_chief_id(),
        journal.get_action_editors_id(submission.number),
        authors_id,
    ]
    previous_url = f'{{SITE_URL}}/forum?id={submission.id}'
    resubmission_id = f'{journal.venue_id}/Paper{submission.number}/-/Resubmission'
    resubmission_url = f'{{SITE_URL}}/invitation?' + urllib.parse.urlencode({'id': resubmission_id})
    existing_resubmission = openreview.tools.get_invitation(client, resubmission_id)
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        readers=readers,
        writers=[journal.venue_id],
        invitation=openreview.api.Invitation(
            id=resubmission_id,
            signatures=[journal.venue_id],
            readers=readers,
            writers=[journal.venue_id],
            invitees=[authors_id],
            description=(
                f'<p>Submit a revised version of JMLR Paper {submission.number}: '
                f'{submission.content["title"]["value"]}.</p>'
                f'<p><a class="btn btn-primary" href="{resubmission_url}">'
                'Start Resubmission</a></p>'
            ),
            web="{{PYTHON_SCRIPT_JSON:invitations/venue/resubmission/web.js}}",
            edit={
                'signatures': [authors_id],
                'readers': readers,
                'writers': [journal.venue_id],
                'note': {
                    'forum': submission.id,
                    'replyto': submission.id,
                    'signatures': [authors_id],
                    'readers': readers,
                    'writers': [journal.venue_id],
                    'content': {
                        'resubmission_url': {
                            'order': 1,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const': resubmission_url,
                                    'hidden': True,
                                }
                            },
                        }
                    },
                },
            },
        ),
        replacement=bool(existing_resubmission),
        await_process=True,
    )
    created_resubmission = client.get_invitation(resubmission_id)
    if created_resubmission.id != resubmission_id:
        raise openreview.OpenReviewException('Resubmission invitation readback failed.')
