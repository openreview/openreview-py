def process(client, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    venue_id = journal.venue_id
    setup_state_namespace = {"openreview": openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/setup_assignments/setup_state.py}}", setup_state_namespace)
    content_value = setup_state_namespace["content_value"]

    note_id = content_value(invitation, "noteId", "")
    note_number = content_value(invitation, "noteNumber", "")
    try:
        note = client.get_note(note_id) if note_id else None
    except Exception as error:
        print(f"Previous continuity dateprocess skipped; could not load submission {note_id}: {error}")
        return
    if not note:
        print(f"Previous continuity dateprocess skipped because automation invitation {invitation.id} has no noteId.")
        return
    if note_number and str(note_number) != str(note.number):
        print(
            f"Previous continuity dateprocess skipped because noteNumber {note_number} "
            f"does not match Paper{note.number}."
        )
        return

    client.post_note_edit(
        invitation=f"{venue_id}/-/Previous_Continuity_Assignment",
        signatures=[venue_id],
        note=openreview.api.Note(
            signatures=[venue_id],
            readers=[journal.get_editors_in_chief_id()],
            writers=[journal.get_editors_in_chief_id()],
            content={
                "note_id": {"value": note.id},
                "paper_number": {"value": note.number},
                "trigger_source": {"value": "dateprocess"},
            },
        ),
        await_process=True,
    )
