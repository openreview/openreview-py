def process(client, note, invitation):

    if note.content.get('api_version', '1') == '1' and 'Double-blind' not in note.content['Author and Reviewer Anonymity']:
        if 'No' in note.content['withdrawn_submissions_author_anonymity']:
            raise openreview.OpenReviewException('Author identities of withdrawn submissions can only be anonymized for double-blind submissions')

        if 'No' in note.content['desk_rejected_submissions_author_anonymity']:
            raise openreview.OpenReviewException('Author identities of desk-rejected submissions can only be anonymized for double-blind submissions')

    if 'Double-blind' in note.content['Author and Reviewer Anonymity'] or 'Submissions and reviews should both be private.' in note.content.get('Open Reviewing Policy', '') or 'Everyone' not in note.content.get('submission_readers', ''):
        if 'submissions_visibility' in note.content and 'Yes' in note.content['submissions_visibility']:
            raise openreview.OpenReviewException('Submissions can only be immediately released to the public for non double-blind, public venues')

    if 'Yes, our venue has Area Chairs' in note.content['Area Chairs (Metareviewers)'] and 'All Area Chairs' not in note.content['reviewer_identity'] and 'Assigned Area Chair' not in note.content['reviewer_identity']:
        raise openreview.OpenReviewException('Assigned area chairs must see the reviewer identity')

    if 'Yes, our venue has Senior Area Chairs' in note.content.get('senior_area_chairs', '') and 'All Senior Area Chairs' not in note.content['reviewer_identity'] and 'Assigned Senior Area Chair' not in note.content['reviewer_identity']:
        raise openreview.OpenReviewException('Assigned senior area chairs must see the reviewer identity')

    withdrawal_expiration = note.content.get('withdraw_submission_expiration')
    if withdrawal_expiration:
        try:
            withdrawal_expiration = datetime.datetime.strptime(withdrawal_expiration, '%Y/%m/%d %H:%M')
        except ValueError:
            withdrawal_expiration = datetime.datetime.strptime(withdrawal_expiration, '%Y/%m/%d')

        submission_deadline = note.content.get('Submission Deadline')
        try:
            submission_deadline = datetime.datetime.strptime(submission_deadline, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_deadline = datetime.datetime.strptime(submission_deadline, '%Y/%m/%d')

        if withdrawal_expiration < (submission_deadline + datetime.timedelta(minutes=30)):
            raise openreview.OpenReviewException('The withdrawal expiration date must be at least 30 minutes after the submission deadline')