def process(client, edit, invitation):

    request_note = client.get_note(edit.note.id)
    if request_note.content.get('status').get('value') != 'Pending':
        raise openreview.OpenReviewException(f'Request Status is not Pending, current status is {request_note.content.get("status").get("value")}')