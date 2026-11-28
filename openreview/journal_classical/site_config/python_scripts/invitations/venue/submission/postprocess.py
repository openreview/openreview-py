def process(client, edit, invitation):
    # OpenReview detects the postprocess language from its first token. Shared
    # helper definitions are appended below and are available when this runs.
    # JMLR delta: Journal weights continuity later; JMLR attempts it immediately.
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    note = client.get_note(edit.note.id)
    # The Journal setup process runs concurrently with this postprocess. The
    # Revision invitation is cosmetic here (track immutability is enforced by
    # preprocess), so update it only when setup has already created it.
    revision = openreview.tools.get_invitation(
        client, journal.get_revision_id(number=note.number)
    )
    if revision:
        revision.edit.get('note', {}).get('content', {}).pop('track_id', None)
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(), signatures=[journal.venue_id],
            invitation=revision, replacement=True,
        )
    edits = client.get_note_edits(note_id=note.id, sort='tcdate:asc')
    if not edits or edit.id != edits[0].id:
        return

    previous_url = note.content.get('previous_JMLR_submission_url', {}).get('value')
    if not previous_url:
        return
    previous_id = previous_url.split('?id=')[-1].split('&')[0]
    previous = client.get_note(previous_id)
    wait_for_native_groups(client, (
        journal.get_authors_id(number=note.number),
        journal.get_action_editors_id(number=note.number),
    ))
    ensure_previous_submission_access_for_current_ae(client, journal, note)
    expected_link = f'[Paper {previous.number}]({previous_url})'
    if note.content.get('previous_JMLR_submission', {}).get('value') != expected_link:
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            note=openreview.api.Note(
                id=note.id,
                content={'previous_JMLR_submission': {'value': expected_link}},
            ),
            await_process=True,
        )
        note = client.get_note(note.id)

    prior = []
    for assignment_id in (
        journal.get_ae_assignment_id(),
        journal.get_ae_assignment_id(archived=True),
    ):
        prior.extend(client.get_edges(invitation=assignment_id, head=previous_id))
    if not prior:
        return

    base_members = set(client.get_group(journal.get_action_editors_id()).members or [])
    for edge in sorted(prior, key=lambda item: item.tcdate or 0, reverse=True):
        candidate = edge.tail
        if candidate not in base_members:
            continue
        if journal.assignment.compute_conflicts(note, candidate):
            continue
        if client.get_edges(invitation=journal.get_ae_assignment_id(), head=note.id):
            return
        client.post_edge(openreview.api.Edge(
            invitation=journal.get_ae_assignment_id(),
            signatures=[journal.get_editors_in_chief_id()],
            head=note.id,
            tail=candidate,
            weight=1,
            label='Resubmission continuity',
        ))
        return


def wait_for_native_groups(client, group_ids, timeout=30, poll_interval=1):
    """Wait for concurrent native paper-group setup without hiding API errors."""
    import time

    pending = list(dict.fromkeys(group_ids))
    deadline = time.monotonic() + timeout
    while pending:
        for group_id in list(pending):
            try:
                client.get_group(group_id)
                pending.remove(group_id)
            except Exception as error:
                status = getattr(error, 'status_code', None)
                if status is None:
                    status = getattr(
                        getattr(error, 'response', None), 'status_code', None
                    )
                structured = error.args[0] if len(error.args) == 1 else None
                if status is None and isinstance(structured, dict):
                    status = structured.get('status')
                name = structured.get('name') if isinstance(structured, dict) else None
                if status != 404 or name not in (None, 'NotFoundError'):
                    raise
        if not pending:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise openreview.OpenReviewException(
                'Linked submission setup did not become ready.'
            )
        time.sleep(min(poll_interval, remaining))


# {{PYTHON_SCRIPT_FILE:invitations/venue/previous_submission_ae_reader_bridge.py}}
