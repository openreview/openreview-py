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
    sac_name = domain.content['senior_area_chairs_name']['value']

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    request_form = client_v1.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue_stage_invitations = client_v1.get_all_invitations(regex=f"{support_group}/-/Request{request_form.number}.*")
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)
    invitation_builder = openreview.arr.InvitationBuilder(venue)

    conference_matching = matching.Matching(venue, client.get_group(venue.get_senior_area_chairs_id()), None)

    # Deploy the SAE assignments if they are not deployed
    submissions = venue.get_submissions()
    sac_groups = {
        int(g.id.split('/')[5].replace('Submission', '')): g
        for g in filter(lambda g: g.id.endswith(f"/{sac_name}"), client.get_all_groups(prefix=f"aclweb.org/ACL/ARR/2023/August/Submission.*"))
    }
    assignment_edges = { g['id']['head']: [e['tail'] for e in g['values']] for g in client.get_grouped_edges(invitation=venue.get_assignment_id(sac_id), groupby='head', select='tail')}
    for submission in submissions:
        if submission.id in assignment_edges:
            submission_group = sac_groups[submission.number]
            missing_members = set(assignment_edges[submission.id]).difference(set(submission_group.members))
            if len(missing_members) > 0:
                client.add_members_to_group(submission_group, list(missing_members))

    # Enable outside reviewers
    hash_seed=''.join(random.choices(string.ascii_uppercase + string.digits, k = 8))
    conference_matching.setup_invite_assignment(hash_seed=hash_seed, invited_committee_name=f'Emergency_{venue.get_area_chairs_name(pretty=False)}')

    client.post_group_edit(
        invitation = meta_invitation_id,
        readers = [venue_id],
        writers = [venue_id],
        signatures = [venue_id],
        group = openreview.api.Group(id=f"{venue_id}/Emergency_Area_Chairs",
            readers=[venue_id, f"{venue_id}/Emergency_Area_Chairs"],
            writers=[venue_id],
            signatures=[venue_id],
            signatories=[venue_id, f"{venue_id}/Emergency_Area_Chairs"],
            members=[]
        )
    )   

    client.post_group_edit(
        invitation = meta_invitation_id,
        readers = [venue_id],
        writers = [venue_id],
        signatures = [venue_id],
        group = openreview.api.Group(id=f"{venue_id}/Emergency_Area_Chairs/Invited",
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            signatories=[venue_id, f"{venue_id}/Emergency_Area_Chairs/Invited"],
            members=[]
        )
    )