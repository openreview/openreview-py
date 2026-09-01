def process(client, edit, invitation):
    # JMLR delta: Journal group editing cannot guard assigned AE removal.
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    changes = edit.group.members or {}
    removed = changes.get('remove', []) if isinstance(changes, dict) else []
    blocked = []
    for member in removed:
        for edge in client.get_edges(invitation=journal.get_ae_assignment_id(), tail=member):
            submission = client.get_note(edge.head)
            if journal.is_active_submission(submission):
                blocked.append(f'Paper{submission.number}')
    if blocked:
        papers = ', '.join(sorted(set(blocked)))
        raise openreview.OpenReviewException(
            f'Reassign active papers before removing this Action Editor: {papers}.'
        )
