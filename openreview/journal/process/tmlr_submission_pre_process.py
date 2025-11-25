def process(client, edit, invitation):
    
    if 'Beyond PDF submission' in edit.note.content.get('submission_length', {}).get('value', []) and not edit.note.content.get('beyond_pdf', {}).get('value'):
        raise openreview.OpenReviewException(f'You must upload a Beyond PDF zip file for the submission if you select "Beyond PDF submission" as the submission type.')
    
    if edit.note.content.get('beyond_pdf', {}).get('value') and 'Beyond PDF submission' not in edit.note.content.get('submission_length', {}).get('value', []):
        raise openreview.OpenReviewException(f'You must select "Beyond PDF submission" as the submission type if your submission contains a Beyond PDF zip file.')