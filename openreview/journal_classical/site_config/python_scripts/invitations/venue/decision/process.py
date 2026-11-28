def process(client, edit, invitation):
    """Run the native Journal decision process, then apply JMLR approval policy."""
    from openreview.journal.process import submission_decision_process

    journal = openreview.journal.JournalRequest.get_journal(
        client, "{{PROD_JOURNAL_ID}}"
    )
    submission_decision_process.openreview = openreview
    journal_constructor = openreview.journal.Journal
    try:
        # Generated Journal processes normally substitute JournalRequest at
        # build time. Bind the raw upstream module to this resolved journal so
        # its implementation remains the single source of native behavior.
        openreview.journal.Journal = lambda: journal
        submission_decision_process.process(client, edit, invitation)
    finally:
        openreview.journal.Journal = journal_constructor

    if "{{AUTOMATIC_DECISION_APPROVAL_JSON}}" != "true":
        return

    decision = client.get_note(edit.note.id)
    submission = client.get_note(decision.forum)
    action_editor_prefix = journal.get_action_editors_id(
        number=submission.number, anon=True
    )
    if not any(
        signature.startswith(action_editor_prefix)
        for signature in (decision.signatures or [])
    ):
        return
    approval_id = journal.get_decision_approval_id(number=submission.number)
    helper_namespace = {'openreview': openreview}
    exec(
        "{{PYTHON_SCRIPT_JSON:invitations/venue/automatic_eic_approval.py}}",
        helper_namespace,
    )
    approval_result = helper_namespace['post_standard_eic_approval'](
        client=client,
        approval_invitation_id=approval_id,
        forum_id=submission.id,
        replyto_id=decision.id,
        eic_signature=journal.get_editors_in_chief_id(),
        expected_approval_value="I approve the AE's decision.",
        comment_field='comment_to_the_AE',
        comment_text=(
            'Automatically approved per JMLR policy. This approval uses the '
            'standard Journal decision-approval value.'
        ),
        authoritative_existing_values=(
            "I don't approve the AE's decision. The AE needs to revise their decision.",
        ),
        readback_error='Automatic decision approval readback failed.',
    )

    if approval_result['approval_value'] != "I approve the AE's decision.":
        return

    recommendation = decision.content.get('recommendation', {}).get('value')
    if recommendation not in ('Accept as is', 'Accept with minor revision'):
        return

    guidance_namespace = {}
    exec(
        "{{PYTHON_SCRIPT_JSON:invitations/venue/decision/camera_ready_guidance.py}}",
        guidance_namespace,
    )
    guidance_namespace['apply_camera_ready_guidance'](
        client, journal, submission, decision
    )
