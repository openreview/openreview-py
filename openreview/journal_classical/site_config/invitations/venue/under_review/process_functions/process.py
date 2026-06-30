def process(client, edit, invitation):
    script = None
    parent_invitation_ids = [invitation.id] + list(invitation.invitations or [])
    for parent_invitation_id in parent_invitation_ids:
        parent_invitation = client.get_invitation(parent_invitation_id)
        parent_content = getattr(parent_invitation, 'content', {}) or {}
        if 'process_script' in parent_content:
            script = parent_content['process_script']['value']
            break
    if script is None:
        raise openreview.OpenReviewException(f'Under Review invitation {invitation.id} has no content.process_script.')
    funcs = {
        'openreview': openreview
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
