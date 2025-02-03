def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']

    # Update webfields
    label_to_share = invitation.content['reviewer_assignments_title']['value']

    client.post_group_edit(invitation=meta_invitation_id,
        readers = [venue_id],
        writers = [venue_id],
        signatures = [venue_id],
        group = openreview.api.Group(
            id = venue_id,
            content = {
                'enable_reviewers_reassignment': { 'value': True },
                'reviewers_proposed_assignment_title': { 'value': label_to_share }
            }
        )
    )