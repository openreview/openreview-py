def process(client, edge, invitation):
    import openreview
    from openreview.journal.tracks import track_context, validate_eligibility
    journal = openreview.journal.Journal()
    return validate_eligibility(client, track_context(journal, True), edge, True)
