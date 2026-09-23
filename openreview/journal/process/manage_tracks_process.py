def process(client, edit, invitation):
    import openreview
    from openreview.journal.tracks import refresh_tracks, track_context
    journal = openreview.journal.Journal()
    return refresh_tracks(client, track_context(journal), edit)
