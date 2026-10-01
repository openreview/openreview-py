def process(client, edit, invitation):
    import openreview
    from openreview.journal.tracks import track_context, validate_track_update
    journal = openreview.journal.Journal()
    return validate_track_update(client, track_context(journal), edit)
