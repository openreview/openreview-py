def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')

    group_id = edit.group.id
    track = client.get_group(group_id).content.get('track', {}).get('value')

    ## restrict every matching invitation of this group to the group's track,
    ## or lift the restriction when the track is removed
    for name in ['Affinity_Score', 'Conflict', 'Proposed_Assignment', 'Assignment', 'Aggregate_Score']:
        edge_invitation = openreview.tools.get_invitation(client, f'{group_id}/-/{name}')
        if not edge_invitation:
            continue

        head_param = edge_invitation.edit.get('head', {}).get('param', {})
        if head_param.get('type') != 'note':
            continue

        if track:
            head_param['withContent'] = { 'track': track }
        else:
            head_param.pop('withContent', None)

        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=edge_invitation
        )

    ## the matcher reads the submissions to assign from the configuration note
    config_invitation = openreview.tools.get_invitation(client, f'{group_id}/-/Assignment_Configuration')
    if config_invitation:
        submission_id = domain.get_content_value('submission_id', f'{venue_id}/-/Submission')
        submission_venue_id = domain.get_content_value('submission_venue_id', f'{venue_id}/Submission')
        paper_invitation = f'{submission_id}&content.venueid={submission_venue_id}'
        if track:
            paper_invitation = f'{paper_invitation}&content.track={track}'

        config_invitation.edit['note']['content']['paper_invitation']['value']['param']['default'] = paper_invitation

        client.post_invitation_edit(
            invitations=meta_invitation_id,
            signatures=[venue_id],
            invitation=config_invitation
        )
