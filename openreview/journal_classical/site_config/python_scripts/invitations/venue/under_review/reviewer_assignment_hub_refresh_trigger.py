def trigger_reviewer_assignment_hub_refresh(client, journal, note, await_process=True, raise_on_error=True):
    try:
        client.post_note_edit(
            invitation=f'{journal.venue_id}/-/Reviewer_Assignment_Hub_Refresh',
            signatures=[journal.venue_id],
            note=openreview.api.Note(
                signatures=[journal.venue_id],
                readers=[journal.get_editors_in_chief_id()],
                writers=[journal.get_editors_in_chief_id()],
                content={
                    'note_id': {'value': note.id},
                    'paper_number': {'value': note.number}
                }
            ),
            await_process=await_process
        )
        return True
    except Exception as error:
        print(f"Could not trigger reviewer assignment hub refresh for submission {note.id}: {error}")
        if raise_on_error:
            raise
        return False
