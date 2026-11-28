def process(client, edit, invitation):
    """Apply JMLR camera-ready guidance after a native manual approval."""
    journal = openreview.journal.JournalRequest.get_journal(
        client, "{{PROD_JOURNAL_ID}}"
    )
    approval = client.get_note(edit.note.id)
    if approval.tcdate != approval.tmdate:
        return

    approval_value = approval.content.get('approval', {}).get('value')
    if approval_value != "I approve the AE's decision.":
        return

    decision = client.get_note(approval.replyto)
    recommendation = decision.content.get('recommendation', {}).get('value')
    if recommendation not in ('Accept as is', 'Accept with minor revision'):
        return

    submission = client.get_note(decision.forum)
    guidance_namespace = {}
    exec(
        "{{PYTHON_SCRIPT_JSON:invitations/venue/decision/camera_ready_guidance.py}}",
        guidance_namespace,
    )
    guidance_namespace['apply_camera_ready_guidance'](
        client, journal, submission, decision
    )
