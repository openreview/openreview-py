def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    venue_name = domain.content['title']['value']
    request_form_id = domain.content['request_form_id']['value']

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    request_form = client_v1.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue_stage_invitations = client_v1.get_all_invitations(regex=f"{support_group}/-/Request{request_form.number}.*")
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)
    invitation_builder = openreview.arr.InvitationBuilder(venue)
    venue_stage_invitations = [i for i in venue_stage_invitations if '/Revision' in i.id]
    for invitation in venue_stage_invitations:
        invitation.process = invitation_builder.get_process_content('process/revisionProcess.py')
        client_v1.post_invitation(invitation)

    print([i.id for i in venue_stage_invitations]) # We use: review, meta-review, comment, revision, ethics review, rev/ac registration, 