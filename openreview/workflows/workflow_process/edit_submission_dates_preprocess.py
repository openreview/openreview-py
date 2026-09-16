def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    full_submission_invitation_id = domain.get_content_value('full_submission_invitation_id', '')
    expdate = edit.invitation.expdate

    if full_submission_invitation_id:
        full_submission_invitation = openreview.tools.get_invitation(client, full_submission_invitation_id)
        # Ignore check if the full submission invitation has been disabled or deleted
        if not full_submission_invitation or full_submission_invitation.ddate:
            return
        if full_submission_invitation.cdate and expdate > full_submission_invitation.cdate:
            raise openreview.OpenReviewException('Submission expiration date must be less than or equal to the Full Submission activation date. Please update the Full Submission dates first or select an earlier date.')
