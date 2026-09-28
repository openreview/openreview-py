def process(client, edit, invitation):
    # journal-resubmission-preprocess-owner-v2
    import openreview
    from openreview.journal.resubmission import validate_resubmission_submission_edit
    journal = openreview.journal.Journal()
    return validate_resubmission_submission_edit(client, journal, edit, invitation)
