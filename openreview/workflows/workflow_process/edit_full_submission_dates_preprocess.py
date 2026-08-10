def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    submission_id = domain.get_content_value('submission_id')
    cdate = edit.invitation.edit.get('invitation', {}).get('cdate')

    if submission_id and cdate:
        submission_invitation = openreview.tools.get_invitation(client, submission_id)
        if submission_invitation and submission_invitation.expdate and submission_invitation.expdate > cdate:
            raise openreview.OpenReviewException('Full Submission activation date must be later than or equal to the Submission expiration date. Please update the Submission dates first or select a later date.')
