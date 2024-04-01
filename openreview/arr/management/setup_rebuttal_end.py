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
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)
    latest_reference = client_v1.get_references(referent=request_form_id, invitation=f"{support_group}/-/Request{request_form.number}/Comment_Stage")[0]

    latest_content = latest_reference.content
    latest_content['participants'] = [
        'Program Chairs',
        'Assigned Senior Area Chairs',
        'Assigned Area Chairs',
        'Assigned Reviewers',
        'Assigned Submitted Reviewers'
    ]
    stage_note = openreview.Note(
        content = latest_content,
        forum = latest_reference.forum,
        invitation = latest_reference.invitation,
        readers = latest_reference.readers,
        referent = latest_reference.referent,
        replyto = latest_reference.replyto,
        signatures = ['~Super_User1'],
        writers = []
    )
    client_v1.post_note(stage_note)
