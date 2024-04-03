def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    from openreview.venue import matching

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    request_form_id = domain.content['request_form_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']

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
    compute_affinity_scores = client_v1.get_attachment(id=invitation.content['configuration_note_id']['value'], field_name='sae_affinity_scores')

    conference_matching.setup(compute_affinity_scores=compute_affinity_scores, compute_conflicts=True)

    # Replace SAC process function
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=f"{venue_id}/Senior_Area_Chairs/-/Assignment",
            process=invitation_builder.get_process_content('process/sac_assignment_process.py'),
            signatures=[venue_id]
        )
    )