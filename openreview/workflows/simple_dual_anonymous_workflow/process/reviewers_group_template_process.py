def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']

    domain = client.get_group(venue_id)

    reviewers_name = edit.content['reviewers_name']['value']
    reviewers_anon_name = f'{reviewers_name[:-1] if reviewers_name.endswith("s") else reviewers_name}_'

    client.post_group_edit(
        invitation=domain.content['meta_invitation_id']['value'],
        signatures=['~Super_User1'],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'reviewers_id': { 'value': edit.group.id },
                'reviewers_name': { 'value': reviewers_name },
                'reviewers_anon_name': { 'value': reviewers_anon_name },
                'reviewers_submitted_name': { 'value': 'Submitted' },
            }
        )
    )