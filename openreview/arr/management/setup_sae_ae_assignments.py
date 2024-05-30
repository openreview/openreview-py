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

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    request_form = client_v1.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)

    conference_matching = matching.Matching(venue, client.get_group(venue.get_area_chairs_id()), None)

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