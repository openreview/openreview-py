def process(client, invitation):

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
    
    # 1) Find all reassignments and reassignment requests -> 0 out or set to 3

    # 2) Grant readership to previous submissions

    # 3) Post track edges
        