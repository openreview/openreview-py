def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    full_submission_invitation_id = domain.get_content_value('full_submission_invitation_id', '')
    expdate = edit.invitation.expdate

    if full_submission_invitation_id:
        full_submission_invitation = openreview.tools.get_invitation(client, full_submission_invitation_id)
        # Ignore check if the full submission invitation has been disabled or deleted
        if full_submission_invitation and not full_submission_invitation.ddate:
            if full_submission_invitation.cdate and expdate > full_submission_invitation.cdate:
                raise openreview.OpenReviewException('Submission expiration date must be less than or equal to the Full Submission activation date. Please update the Full Submission dates first or select an earlier date.')
            return

    submission_fee_payment_id = domain.get_content_value('submission_fee_payment_id')
    submission_fee_payment_invitation = openreview.tools.get_invitation(client, submission_fee_payment_id) if submission_fee_payment_id else None
    payment_duedate = submission_fee_payment_invitation.edit['invitation'].get('duedate') if submission_fee_payment_invitation else None
    if expdate and payment_duedate and expdate > payment_duedate:
        raise openreview.OpenReviewException('Submission expiration date must be earlier than or equal to the submission fee due date. Please update the submission fee dates first or select an earlier date.')
