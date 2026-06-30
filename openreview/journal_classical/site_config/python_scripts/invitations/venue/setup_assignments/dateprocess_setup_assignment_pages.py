def process(client, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    venue_id = journal.venue_id
    setup_invitation_id = f"{venue_id}/-/Setup_Assignments"
    setup_state_namespace = {"openreview": openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/setup_assignments/setup_state.py}}", setup_state_namespace)
    classify_assignment_setup_state = setup_state_namespace["classify_assignment_setup_state"]
    content_value = setup_state_namespace["content_value"]

    def active_ae_for_paper(note):
        assignment_id = f"{venue_id}/Paper{note.number}/Action_Editors/-/Assignment"
        try:
            edges = client.get_edges(invitation=assignment_id, head=note.id, domain=venue_id)
        except Exception:
            edges = []
        active = [edge for edge in edges or [] if not getattr(edge, "ddate", None)]
        return active[0].tail if active else None

    note_id = content_value(invitation, "noteId", "")
    note_number = content_value(invitation, "noteNumber", "")
    try:
        note = client.get_note(note_id) if note_id else None
    except Exception as error:
        print(f"Could not load submission {note_id} for assignment setup dateprocess: {error}")
        return
    if not note:
        print(f"Assignment setup dateprocess skipped because automation invitation {invitation.id} has no noteId.")
        return
    if note_number and str(note_number) != str(note.number):
        print(
            f"Assignment setup dateprocess skipped because noteNumber {note_number} "
            f"does not match Paper{note.number}."
        )
        return
    venueid = content_value(note, "venueid", "")
    if venueid != f"{venue_id}/Submitted":
        print(f"Assignment setup dateprocess skipped Paper{note.number}; venueid is {venueid or 'missing'}.")
        return
    active_ae = active_ae_for_paper(note)
    if active_ae:
        print(f"Assignment setup dateprocess skipped Paper{note.number}; active AE already exists: {active_ae}.")
        return
    setup_state = classify_assignment_setup_state(client, journal, note)
    if setup_state.get("status") == "complete":
        print(f"Assignment setup dateprocess skipped Paper{note.number}; setup is already complete.")
        return
    if setup_state.get("status") in {"in_progress", "stale_in_progress", "failed"}:
        print(
            f"Assignment setup dateprocess skipped Paper{note.number}; setup state is {setup_state.get('status')}. "
            "Use the EIC console or maintenance script for manual recovery."
        )
        return
    client.post_note_edit(
        invitation=setup_invitation_id,
        signatures=[venue_id],
        note=openreview.api.Note(
            signatures=[venue_id],
            content={
                "note_id": {"value": note.id},
                "paper_number": {"value": note.number},
            },
        ),
        await_process=True,
    )
    print(
        f"Assignment setup dateprocess posted setup request for Paper{note.number} "
        f"from state {setup_state.get('status')}."
    )
