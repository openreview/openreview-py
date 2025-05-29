def process(client, edit, invitation):

    if edit.note.content.get('recommendation', {}).get('value') == 'Reject' and edit.note.content.get('certifications', {}).get('value', []):
        raise openreview.OpenReviewException(f'Decision Reject can not have certifications')

    if edit.note.content.get('claims_and_evidence', {}).get('value') == 'Yes' and edit.note.content.get('audience', {}).get('value') == 'Yes':
        if edit.note.content.get('recommendation', {}).get('value') == 'Reject':
            raise openreview.OpenReviewException('Decision should be "Accept as is" or "Accept with minor revision" if you answered "Yes" to both TMLR criteria')

    if edit.note.content.get('claims_and_evidence', {}).get('value') == 'No' or edit.note.content.get('audience', {}).get('value') == 'No':
        if edit.note.content.get('recommendation', {}).get('value') == 'Accept as is':
            raise openreview.OpenReviewException('Decision should not be "Accept as is" if you answered "No" to either of the two TMLR criteria')