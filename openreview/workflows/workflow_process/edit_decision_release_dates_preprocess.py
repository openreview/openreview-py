def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    cdate = edit.invitation.cdate

    if not cdate:
        return

    decision_release_invitation = openreview.tools.get_invitation(client, edit.invitation.id)
    # Ignore check if the decision release invitation does not exist or has been disabled or deleted
    if not decision_release_invitation or decision_release_invitation.ddate:
        return

    invitations = client.get_all_invitations(prefix=f'{domain.id}/-/', type='invitation', domain=domain.id)
    for revision_invitation in invitations:
        if revision_invitation.ddate or not revision_invitation.cdate or not revision_invitation.content:
            continue
        if 'revision_process_script' not in revision_invitation.content:
            continue
        source = revision_invitation.get_content_value('source', {})
        if not isinstance(source, dict) or not source.get('with_decision_accept', False):
            continue
        if cdate >= revision_invitation.cdate:
            release_name = edit.invitation.id.split('/-/')[-1].replace('_', ' ')
            revision_name = revision_invitation.id.split('/-/')[-1].replace('_', ' ')
            raise openreview.OpenReviewException(f'{release_name} activation date must be before the {revision_name} activation date. Please update the {revision_name} dates first or select an earlier date.')
