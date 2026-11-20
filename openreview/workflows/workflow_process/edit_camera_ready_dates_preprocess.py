def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    decision_name = domain.get_content_value('decision_name', 'Decision')
    cdate = edit.invitation.cdate

    if not cdate:
        return

    decision_release_invitation = openreview.tools.get_invitation(client, f'{domain.id}/-/{decision_name}_Release')
    # Ignore check if the decision release invitation does not exist or has been disabled or deleted
    if not decision_release_invitation or decision_release_invitation.ddate or not decision_release_invitation.cdate:
        return

    if cdate <= decision_release_invitation.cdate:
        revision_name = edit.invitation.id.split('/-/')[-1].replace('_', ' ')
        release_name = f'{decision_name}_Release'.replace('_', ' ')
        raise openreview.OpenReviewException(f'{revision_name} activation date must be after the {release_name} activation date. Please update the {release_name} dates first or select a later date.')
