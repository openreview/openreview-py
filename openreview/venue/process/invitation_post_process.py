def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id

    print('update child invitations')
    print('post edit', edit['invitation'])