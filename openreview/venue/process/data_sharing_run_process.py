def process(client, edit, invitation):

    SUPPORT_GROUP = ''

    data_sharing = openreview.venue.VenueDataSharing(client, SUPPORT_GROUP)

    request = client.get_note(edit.note.id)
    job_id = edit.note.content.get('job_id', {}).get('value')

    data_sharing.run_dual_submission_check(request, job_id=job_id)
