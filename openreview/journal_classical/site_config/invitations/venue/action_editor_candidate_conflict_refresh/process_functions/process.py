def process(client, edit, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    trigger_note = client.get_note(edit.note.id)

    def content_value(key, default=None):
        return (trigger_note.content or {}).get(key, {}).get("value", default)

    note_id = content_value("note_id")
    paper_number = content_value("paper_number")
    candidate_id = content_value("candidate_id")
    if not note_id:
        raise openreview.OpenReviewException("Action Editor candidate conflict refresh requires note_id.")
    if not candidate_id or not isinstance(candidate_id, str) or not candidate_id.startswith("~"):
        raise openreview.OpenReviewException("Action Editor candidate conflict refresh requires an OpenReview profile candidate_id.")

    note = client.get_note(note_id)
    if paper_number and int(paper_number) != int(note.number):
        raise openreview.OpenReviewException("Action Editor candidate conflict refresh paper_number does not match note_id.")

    signatures = list(getattr(edit, "signatures", None) or [])
    signatures.extend(getattr(edit.note, "signatures", None) or [])
    signatures.extend(getattr(trigger_note, "signatures", None) or [])
    signatures = [signature for signature in signatures if isinstance(signature, str)]
    eic_signature = journal.get_editors_in_chief_id()
    if eic_signature not in signatures:
        raise openreview.OpenReviewException("Only Editors-in-Chief can refresh Action Editor candidate conflicts.")

    assignment_conflict_namespace = {"openreview": openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/assignment_conflicts.py}}", assignment_conflict_namespace)
    assignment_conflict_materialization_namespace = {"openreview": openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/assignment_conflict_materialization.py}}", assignment_conflict_materialization_namespace)

    counts = assignment_conflict_materialization_namespace["materialize_openreview_conflicts"](
        client,
        journal,
        note,
        journal.get_ae_conflict_id(),
        [candidate_id],
        "AE",
        assignment_conflict_namespace,
    )
    print(
        f"Action Editor candidate conflict refresh for Paper{note.number} "
        f"{candidate_id}: {counts}"
    )
