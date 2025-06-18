def process(client, tag, invitation):

    profile = client.get_profile(tag.profile)

    venues = {m:m for m in client.get_group(id='venues').members}

    memberships = client.get_groups(member=profile.id)

    domains = set([m.domain for m in memberships if m.domain in venues])

    print('Add the following domains to the tag readers:', domains)

    tag.readers = tag.readers + list(domains)
    
    client.post_tag(tag)