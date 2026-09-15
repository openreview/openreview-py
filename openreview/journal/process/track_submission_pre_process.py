# journal-managed-track-validation
def process(client, edit, invitation):
    journal = openreview.journal.Journal()
    track_id = edit.note.content.get('track_id', {}).get('value')
    journal.validate_submission_track(track_id)
