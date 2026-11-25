def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    activation_date = edit.content['activation_date']['value']

    full_submission_invitation_id = domain.get_content_value('full_submission_invitation_id')
    full_submission_invitation = openreview.tools.get_invitation(client, full_submission_invitation_id) if full_submission_invitation_id else None
    if full_submission_invitation and full_submission_invitation.ddate:
        full_submission_invitation = None

    if full_submission_invitation:
        deadline_name = 'Full Submission'
        submission_closes = full_submission_invitation.edit['invitation'].get('expdate')
    else:
        deadline_name = 'Submission'
        submission_invitation = openreview.tools.get_invitation(client, domain.get_content_value('submission_id'))
        submission_closes = submission_invitation.expdate if submission_invitation else None

    if submission_closes and activation_date < submission_closes:
        raise openreview.OpenReviewException(f'The submission fee activation date must be later than or equal to the {deadline_name} deadline + grace period (30 minutes). Please update the {deadline_name} dates first or select a later date.')
