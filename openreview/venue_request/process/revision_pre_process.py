def process(client, note, invitation):

    request_form = client.get_note(note.forum)
    print(request_form.content['Author and Reviewer Anonymity'])
    print(note.content.get('desk_rejected_submissions_author_anonymity'), '')

    if 'Double-blind' not in request_form.content['Author and Reviewer Anonymity']:
        if 'No' in note.content.get('withdrawn_submissions_author_anonymity', ''):
            raise openreview.OpenReviewException('Author identities of withdrawn submissions can only be anonymized for double-blind submissions')

        if 'No' in note.content.get('desk_rejected_submissions_author_anonymity', ''):
            raise openreview.OpenReviewException('Author identities of desk-rejected submissions can only be anonymized for double-blind submissions')