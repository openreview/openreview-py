def process(client, invitation):
    import openreview
    from openreview.arr.helpers import flag_submission
    from openreview.arr.arr import ROOT_DOMAIN
    from openreview.arr.invitation import InvitationBuilder

    MAX_LOAD_AND_UNAVAILABILITY_NAME = InvitationBuilder.MAX_LOAD_AND_UNAVAILABILITY_NAME

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    authors_name = domain.get_content_value('authors_name')
    submission_name = domain.get_content_value('submission_name')
    reviewers_name = domain.get_content_value('reviewers_name')
    reviewers_anon_name = domain.get_content_value('reviewers_anon_name')
    reviewers_submitted_name = domain.get_content_value('reviewers_submitted_name')
    sender = domain.get_content_value('message_sender')
    comment_threshold = domain.get_content_value('comment_notification_threshold')

    senior_area_chairs_id = domain.content['senior_area_chairs_id']['value']
    area_chairs_id = domain.content['area_chairs_id']['value']
    reviewers_id = domain.content['reviewers_id']['value']
    ethics_chairs_id = domain.content['ethics_chairs_id']['value']
    ethics_reviewers_id = f"{venue_id}/{domain.content['ethics_reviewers_name']['value']}"

    track_edge_readers = {
        senior_area_chairs_id: [venue_id],
        area_chairs_id: [venue_id, senior_area_chairs_id],
        reviewers_id: [venue_id, senior_area_chairs_id, area_chairs_id],
        ethics_reviewers_id: [venue_id, senior_area_chairs_id, area_chairs_id, ethics_chairs_id],
    }

    cycle_committee_id = invitation.id.split('/-/')[0]
    custom_max_papers_id = f"{cycle_committee_id}/-/Custom_Max_Papers"
    group_name = cycle_committee_id.split('/')[-1]
    root_group_id = f"{ROOT_DOMAIN}/{group_name}"
    root_members = client.get_group(root_group_id).members
    cycle_members = client.get_group(cycle_committee_id).members
    all_member_ids = list(set(root_members + cycle_members))
    all_profiles = openreview.tools.get_profiles(client, all_member_ids)

    name_to_profile_map = {}
    for profile in all_profiles:
        for name in profile.content['names']:
            if 'username' in name:
                name_to_profile_map[name['username']] = profile

    root_notes = client.get_all_notes(invitation=f"{root_group_id}/-/{MAX_LOAD_AND_UNAVAILABILITY_NAME}")
    id_to_load = {}
    for note in root_notes:
        if note.signatures[0] not in name_to_profile_map:
            continue
        id_to_load[name_to_profile_map[note.signatures[0]].id] = note.content['maximum_load_this_cycle']['value']

    edges_to_post = []
    for cycle_member in cycle_members:
        profile = name_to_profile_map.get(cycle_member)
        if not profile:
            continue
        load = id_to_load.get(profile.id)
        weight = load if load else 0
        edges_to_post.append(
            openreview.api.Edge(
                invitation=custom_max_papers_id,
                head=cycle_committee_id,
                tail=profile.id,
                weight=weight,
                readers=track_edge_readers[cycle_committee_id] + [profile.id],
                writers=[venue_id],
                signatures=[venue_id]
            )
        )

    client.delete_edges(
        invitation=custom_max_papers_id,
        soft_delete=True,
        wait_to_finish=True
    )
    openreview.tools.post_bulk_edges(client=client, edges=edges_to_post)