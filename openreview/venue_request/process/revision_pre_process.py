def process(client, note, invitation):

    request_form = client.get_note(note.forum)

    if 'Double-blind' not in request_form.content['Author and Reviewer Anonymity']:
        if 'No' in note.content.get('withdrawn_submissions_author_anonymity', ''):
            raise openreview.OpenReviewException('Author identities of withdrawn submissions can only be anonymized for double-blind submissions')

        if 'No' in note.content.get('desk_rejected_submissions_author_anonymity', ''):
            raise openreview.OpenReviewException('Author identities of desk-rejected submissions can only be anonymized for double-blind submissions')

    if 'hide_fields' in note.content:
        submission_fields = ['TLDR', 'abstract', 'keywords', 'pdf']
        if 'Additional Submission Options' in note.content:
            submission_fields.extend(list(note.content['Additional Submission Options'].keys()))
        for field in note.content['hide_fields']:
            if field not in submission_fields:
                raise openreview.OpenReviewException('Invalid field to hide: ' + field)