def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)

    client.add_members_to_group(venue_id, edit.group.id)