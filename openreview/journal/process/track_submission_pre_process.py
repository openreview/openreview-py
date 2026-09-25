def process(client, edit, invitation):
    # journal-track-preprocess-owner-v2
    import openreview
    from openreview.journal.tracks import track_context, validate_track_submission
    journal = openreview.journal.Journal()
    return validate_track_submission(client, track_context(journal), edit)
