def process(client, note, invitation):

    if 'Double-blind' not in note.content['Author and Reviewer Anonymity']:
        if 'No' in note.content['withdrawn_submissions_author_anonymity']:
            raise openreview.OpenReviewException('Author identities of withdrawn submissions can only be anonymized for double-blind submissions')

        if 'No' in note.content['desk_rejected_submissions_author_anonymity']:
            raise openreview.OpenReviewException('Author identities of desk-rejected submissions can only be anonymized for double-blind submissions')

    if 'Double-blind' in note.content['Author and Reviewer Anonymity'] or 'Submissions and reviews should both be private.' in note.content['Open Reviewing Policy']:
        if 'submissions_visibility' in note.content and 'Yes' in note.content['submissions_visibility']:
            raise openreview.OpenReviewException('Submissions can only be immediately released to the public for non double-blind, public venues')