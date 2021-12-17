def process(client, edit, invitation):

    if edit.note.content.get('recommendation', {}).get('value') == 'Reject' and edit.note.content.get('certifications', {}).get('value', []):
        raise openreview.OpenReviewException(f'Decision Reject can not have certifications')

