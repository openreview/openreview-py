def process(client, tag, invitation):

    vouchee_id = invitation.content['vouchee_id']['value']

    ## Activate the vouchee if they are still rejected; skip otherwise (idempotent re-posts)
    vouchee_profile = openreview.tools.get_profile(client, vouchee_id)
    if vouchee_profile and getattr(vouchee_profile, 'state', None) == 'Rejected':
        client.moderate_profile(vouchee_profile.id, 'accept')

    ## Rewrite the label with the confirmed information (names, institution, url) and the
    ## masked form of the email the profile page uses, so the permanent public label never
    ## carries the plaintext email.
    import json
    email = invitation.content['email']['value']
    masked_label = json.dumps({
        'names': invitation.content['names']['value'],
        'institution': invitation.content['institution']['value'],
        'url': invitation.content.get('url', {}).get('value'),
        'email': '****@' + email.split('@')[-1]
    })
    if tag.label != masked_label:
        ## Re-post with only the schema fields: the tag in the process context carries
        ## server-assigned properties (cdate, parentInvitations, ...) that a POST rejects.
        client.post_tag(openreview.api.Tag(
            id=tag.id,
            invitation=tag.invitation,
            signature=tag.signature,
            profile=tag.profile,
            label=masked_label
        ))
