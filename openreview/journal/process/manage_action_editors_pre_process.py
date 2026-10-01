def process(client, edit, invitation):
    import openreview
    from openreview.journal.tracks import track_context, validate_action_editor_update
    journal = openreview.journal.Journal()
    return validate_action_editor_update(client, track_context(journal, True), edit)
