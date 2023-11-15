def process(client, note, invitation):

    request_note = client.get_note(note.referent)
    if request_note.content.get('status') != 'Pending':
        raise openreview.OpenReviewException(f'Request Status is not Pending, current status is {request_note.content.get("status")}')