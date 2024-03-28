def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    from openreview.venue import matching

    domain = client.get_group(invitation.domain)
    request_form_id = domain.content['request_form_id']['value']

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    request_form = client_v1.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)

    compute_affinity_scores = client_v1.get_attachment(id=invitation.content['configuration_note_id']['value'], field_name='sae_affinity_scores')

    venue.setup_committee_matching(
        committee_id=venue.get_senior_area_chairs_id(),
        compute_affinity_scores=compute_affinity_scores,
        compute_conflicts=True
    )