def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    submission_id = domain.get_content_value('submission_id')
    cdate = edit.invitation.edit.get('invitation', {}).get('cdate')
    expdate = edit.invitation.edit.get('invitation', {}).get('expdate')

    if submission_id and cdate:
        submission_invitation = openreview.tools.get_invitation(client, submission_id)
        if submission_invitation and submission_invitation.expdate and submission_invitation.expdate > cdate:
            raise openreview.OpenReviewException('Full Submission activation date must be later than or equal to the Submission deadline + grace period (30 minutes). Please update the Submission dates first or select a later date.')

    submission_fee_payment_id = domain.get_content_value('submission_fee_payment_id')
    submission_fee_payment_invitation = openreview.tools.get_invitation(client, submission_fee_payment_id) if submission_fee_payment_id else None
    payment_duedate = submission_fee_payment_invitation.edit['invitation'].get('duedate') if submission_fee_payment_invitation else None
    if expdate and payment_duedate and expdate > payment_duedate:
        raise openreview.OpenReviewException('Full Submission expiration date must be earlier than or equal to the submission fee due date. Please update the submission fee dates first or select an earlier date.')
