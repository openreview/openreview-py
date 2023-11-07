def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    venue_name = domain.content['title']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return
    group = edit.group
    from_group_id, to_group_id = group.content['original_group']['value'], group.id
    from_group_members = client.get_group(from_group_id).members
    to_group = client.get_group(to_group_id)
    client.add_members_to_group(to_group, from_group_members)

    # Expire this invitation
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=invitation.id,
            expdate=now
        )
    )