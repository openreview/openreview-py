def process(client, tag, invitation):

    profiles = client.get_profiles(id=tag.profile, with_blocked=True)

    if not profiles:
        print('No profiles found for tag', tag.id)
        return
    profile = profiles[0]
    print('Processing tag', tag.id, 'for profile', profile.id)

    venues = {m:m for m in client.get_group(id='venues').members}

    memberships = client.get_groups(member=profile.id)

    domains = set([m.domain for m in memberships if m.domain in venues and m not in tag.readers])

    if not domains:
        print('No new domains found for profile', profile.id)
        return
    
    print('Add the following domains to the tag readers:', domains)
    tag.readers = tag.readers + list(domains)

    client.post_tag(tag)