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

    ## release each track's submissions only to that track's committee: rebuild the per-track
    ## submission change invitations of every track, so a track that was moved or removed from
    ## a group is updated as well
    submission_invitation = client.get_invitation(domain.get_content_value('submission_id', f'{venue_id}/-/Submission'))
    track_options = submission_invitation.edit['note']['content'].get('track', {}).get('value', {}).get('param', {}).get('enum', [])
    tracks = [option['value'] if isinstance(option, dict) else option for option in track_options]

    support_user = domain.content['request_form_invitation']['value'].split('/Venue_Request')[0]
    venue = openreview.venue.helpers.get_venue(client, venue_id, support_user)

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    submission_change_names = ['Submission_Change_Before_Bidding', 'Submission_Change_Before_Reviewing']
    has_track_invitations = False

    roles_by_track = venue.invitation_builder.get_committee_roles_by_track()

    for track in tracks:
        track_roles = roles_by_track.get(track)
        has_committee = track_roles is not None

        for name in submission_change_names:
            track_invitation_id = f'{venue_id}/-/{track}_{name}'
            track_invitation = openreview.tools.get_invitation(client, track_invitation_id)

            if not has_committee:
                ## no group is restricted to this track any more
                if track_invitation:
                    client.post_invitation_edit(
                        invitations=meta_invitation_id,
                        signatures=[venue_id],
                        invitation=openreview.api.Invitation(
                            id=track_invitation_id,
                            ddate=now,
                            signatures=[venue_id]
                        )
                    )
                continue

            ## keep the activation date already set on this track, otherwise take the one of another
            ## track or of the venue-wide invitation this one replaces
            activation_date = None
            for invitation_id in [track_invitation_id] + [f'{venue_id}/-/{other_track}_{name}' for other_track in tracks if other_track != track] + [f'{venue_id}/-/{name}']:
                existing_invitation = track_invitation if invitation_id == track_invitation_id else openreview.tools.get_invitation(client, invitation_id)
                if existing_invitation and existing_invitation.cdate:
                    activation_date = existing_invitation.cdate
                    break

            if activation_date is None:
                print(f'No activation date found for {track_invitation_id}, skipping')
                continue

            has_track_invitations = True

            ## every Track edit runs this process, so leave alone the tracks whose committee did not change
            if track_invitation and track_invitation.edit['note']['readers'] == venue.invitation_builder.get_track_submission_change_readers(name, track_roles):
                continue

            venue.invitation_builder.set_submission_change_invitation(name, activation_date, track=track, track_roles=track_roles)

    ## two invitations setting the readers of the same submission would overwrite each other,
    ## so the per-track invitations replace the venue-wide ones
    if has_track_invitations:
        for name in submission_change_names:
            venue_invitation = openreview.tools.get_invitation(client, f'{venue_id}/-/{name}')
            if venue_invitation and not venue_invitation.ddate:
                client.post_invitation_edit(
                    invitations=meta_invitation_id,
                    signatures=[venue_id],
                    invitation=openreview.api.Invitation(
                        id=venue_invitation.id,
                        ddate=now,
                        signatures=[venue_id]
                    )
                )
