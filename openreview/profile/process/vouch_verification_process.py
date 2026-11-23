def process(client, assertion, invitation):

    if assertion.ddate:
        return

    vouchee = client.get_profile(assertion.profile['id'])
    if getattr(vouchee, 'state', None) not in ['Needs Moderation', 'Rejected']:
        return

    client.moderate_profile(vouchee.id, 'accept')
