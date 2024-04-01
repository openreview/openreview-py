def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    from openreview.venue import matching
    import random
    import string

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    request_form_id = domain.content['request_form_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    reviewer_id = domain.content['reviewers_id']['value']
    ac_id = domain.content['area_chairs_id']['value']
    sac_id = domain.content['senior_area_chairs_id']['value']
    pc_id = domain.content['program_chairs_id']['value']
    sac_name = domain.content['senior_area_chairs_name']['value']

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    request_form = client_v1.get_note(request_form_id)
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

    web = client.get_group(pc_id).web
    web_lines = web.split('\n')
    dst_lines = []
    for line in web_lines:
        if 'const manualReviewerAssignmentUrl' in line:
            browse_line = line.split(' = ')[1].split('&')[-2]
            for inv in group_invs:
                if f"/-/{inv}" not in browse_line:
                    browse_line += ';${domain.content.reviewers_id?.value}' + f"/-/{inv},head:ignore"
            if '/-/Status' not in web:
                browse_line += ';${domain.content.reviewers_id?.value}' + f"/-/Status"
            if '/-/Research_Area' not in web:
                browse_line += ';${domain.content.reviewers_id?.value}' + f"/-/Research_Area"

            after_assignment = line.split(' = ')[1]
            param_list = after_assignment.split('&')
            param_list[-2] = browse_line
            line = line.replace(after_assignment, '&'.join(param_list))
            dst_lines.append(line)
        elif 'const manualAreaChairAssignmentUrl' in line:
            browse_line = line.split(' = ')[1].split('&')[-2]
            for inv in group_invs:
                if f"/-/{inv}" not in browse_line:
                    browse_line += ';${domain.content.area_chairs_id?.value}' + f"/-/{inv},head:ignore"
            if '/-/Status' not in web:
                browse_line += ';${domain.content.area_chairs_id?.value}' + f"/-/Status"
            if '/-/Research_Area' not in web:
                browse_line += ';${domain.content.area_chairs_id?.value}' + f"/-/Research_Area"
            after_assignment = line.split(' = ')[1]
            param_list = after_assignment.split('&')
            param_list[-2] = browse_line
            line = line.replace(after_assignment, '&'.join(param_list))
            dst_lines.append(line)
        else:
            dst_lines.append(line)
    client.post_group_edit(invitation=meta_invitation_id,
        readers = [venue_id],
        writers = [venue_id],
        signatures = [venue_id],
        group = openreview.api.Group(
            id = pc_id,
            web='\n'.join(dst_lines)
        )
    )