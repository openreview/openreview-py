def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    ac_id = domain.content['area_chairs_id']['value']

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

    group_invs = [
        'Registered_Load',
        'Emergency_Load',
        'Emergency_Area',
        'Reviewing_Resubmissions',
        'Author_In_Current_Cycle',
        'Seniority'
    ]
    web = client.get_group(ac_id).web
    web_lines = web.split('\n')
    dst_lines = []

    for line in web_lines:
        dst_lines.append(line)
        if 'const otherParams' in line:
            for inv in group_invs:
                if f"/-/{inv}" not in web:
                    dst_lines.extend([
                        "browseInvitations.push(`${reviewerGroup}/-/" + inv + ',head:ignore`)',
                        "browseProposedInvitations.push(`${reviewerGroup}/-/" + inv + ',head:ignore`)'
                    ])
            if '/-/Status' not in web:
                dst_lines.extend([
                    "browseInvitations.push(`${reviewerGroup}/-/" + 'Status`)',
                    "browseProposedInvitations.push(`${reviewerGroup}/-/" + 'Status`)'
                ])
            if '/-/Research_Area' not in web:
                dst_lines.extend([
                    "browseInvitations.push(`${reviewerGroup}/-/" + 'Research_Area`)',
                    "browseProposedInvitations.push(`${reviewerGroup}/-/" + 'Research_Area`)'
                ])

    client.post_group_edit(invitation=meta_invitation_id,
        readers = [venue_id],
        writers = [venue_id],
        signatures = [venue_id],
        group = openreview.api.Group(
            id = ac_id,
            web='\n'.join(dst_lines)
        )
    )