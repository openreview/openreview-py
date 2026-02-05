def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(id=edit.note.forum)
    signatory_group_id = edit.note.signatures[0]

    reviews=client.get_notes(invitation=journal.get_review_id(number=submission.number))

    if not any(review.signatures[0]==signatory_group_id for review in reviews):
        raise openreview.OpenReviewException(f'You must submit your official review before submitting your recommendation')

    if journal.venue_id == 'TMLR':

        if edit.note.content.get('claims_and_evidence', {}).get('value') == 'Yes' and edit.note.content.get('audience', {}).get('value') == 'Yes':
            if 'Reject' in edit.note.content.get('decision_recommendation', {}).get('value', ''):
                raise openreview.OpenReviewException('Decision recommendation should be "Accept" or "Leaning Accept" if you answered "Yes" to both TMLR criteria. Please see the TMLR Acceptance Criteria: https://jmlr.org/tmlr/acceptance-criteria.html.')

        if edit.note.content.get('claims_and_evidence', {}).get('value') == 'No' or edit.note.content.get('audience', {}).get('value') == 'No':
            if 'Accept' in edit.note.content.get('decision_recommendation', {}).get('value', ''):
                raise openreview.OpenReviewException('Decision recommendation should not be "Accept" nor "Leaning Accept" if you answered "No" to either of the two TMLR criteria. Please see the TMLR Acceptance Criteria: https://jmlr.org/tmlr/acceptance-criteria.html.')