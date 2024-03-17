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
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)
    latest_reference = client_v1.get_references(referent=request_form_id, invitation=f"{support_group}/-/Request{request_form.number}/Review_Stage")[0]

    latest_content = latest_reference.content
    latest_content['release_reviews_to_authors'] = 'Yes, reviews should be revealed when they are posted to the paper\'s authors'

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
