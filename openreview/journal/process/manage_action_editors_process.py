def process(client, edit, invitation):
    import openreview
    from openreview.journal.tracks import cleanup_action_editor_eligibility, track_context
    journal = openreview.journal.Journal()
    return cleanup_action_editor_eligibility(client, track_context(journal, True), edit)
