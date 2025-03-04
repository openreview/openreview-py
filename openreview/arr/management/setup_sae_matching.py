def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    from openreview.venue import matching
    from openreview.arr.helpers import get_resubmissions
    from collections import defaultdict

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    request_form_id = domain.content['request_form_id']['value']
    previous_url_field = 'previous_URL'
    reviewers_id = domain.content['reviewers_id']['value']
    senior_area_chairs_id = domain.content['senior_area_chairs_id']['value']
    tracks_field_name = 'research_area'

    tracks_inv_name = 'Research_Area'
    registration_name = 'Registration'
    max_load_name = 'Max_Load_And_Unavailability_Request'

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    if client.get_edges_count(invitation=f"{senior_area_chairs_id}/-/Affinity_Score") <= 0:
        print(f"no affinity scores for {senior_area_chairs_id}")
        return

    request_form = client_v1.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)
    submissions = venue.get_submissions()

    skip_scores = defaultdict(list)

    # Fetch profiles and map names to profile IDs - account for change in preferred names
    reviewer_profiles = []
    all_profiles = []
    name_to_id = {}
    for role_id in [senior_area_chairs_id]:
        profiles = openreview.tools.get_profiles(client, client.get_group(role_id).members, with_publications=True)
        if role_id == reviewers_id:
            reviewer_profiles.extend(profiles) ## Cache reviewer profiles for seniority
        all_profiles.extend(profiles)
    for profile in all_profiles:
        filtered_names = filter(
            lambda obj: 'username' in obj and len(obj['username']) > 0,
            profile.content.get('names', [])
        )
        for name_obj in filtered_names:
            name_to_id[name_obj['username']] = profile.id

    # Build load map
    id_to_load_note = {}
    for role_id in [senior_area_chairs_id]:
        load_notes = client.get_all_notes(invitation=f"{role_id}/-/{max_load_name}") ## Assume only 1 note per user
        for note in load_notes:
            if note.signatures[0] not in name_to_id:
                continue
            note_signature_id = name_to_id[note.signatures[0]]
            id_to_load_note[note_signature_id] = note

    # Build track map
    track_to_ids = {}
    for role_id in [senior_area_chairs_id]:
        track_to_ids[role_id] = defaultdict(list)
        registration_notes = client.get_all_notes(invitation=f"{role_id}/-/{registration_name}")
        for note in registration_notes:
            if note.signatures[0] not in name_to_id:
                continue
            note_signature_id = name_to_id[note.signatures[0]]
            for track in note.content[tracks_field_name]['value']:
                track_to_ids[role_id][track].append(note_signature_id)

        # Build research area invitation
        matching.Matching(venue, client.get_group(role_id), None)._create_edge_invitation(
            edge_id=f"{role_id}/-/{tracks_inv_name}"
        )
    track_edge_readers = {
        senior_area_chairs_id: [venue_id]
    }

    # Reset custom max papers to ground truth notes
    for role_id in [senior_area_chairs_id]:
        cmp_to_post = []
        role_cmp_inv = f"{role_id}/-/Custom_Max_Papers"
        for id, note in id_to_load_note.items():
            load_invitation = [inv for inv in note.invitations if max_load_name in inv][0]
            if role_id not in load_invitation:
                continue

            cmp_to_post.append(
                openreview.api.Edge(
                    invitation=role_cmp_inv,
                    head=role_id,
                    tail=id,
                    weight=int(note.content['maximum_load_this_cycle']['value']),
                    readers=track_edge_readers[role_id] + [id],
                    writers=[venue_id],
                    signatures=[venue_id]
                )
            )
        client.delete_edges(
            invitation=role_cmp_inv,
            soft_delete=True,
            wait_to_finish=True
        )
        openreview.tools.post_bulk_edges(client=client, edges=cmp_to_post)

    # 3) Post track edges
    for role_id, track_to_members in track_to_ids.items():
        track_edges_to_post = []

        for submission in submissions:
            submission_track = submission.content[tracks_field_name]['value']
            members = track_to_members[submission_track]

            for member in members:
                if member in skip_scores.get(submission.id, []):
                    continue

                track_edges_to_post.append(
                    openreview.api.Edge(
                        invitation=f"{role_id}/-/{tracks_inv_name}",
                        head=submission.id,
                        tail=member,
                        weight=1,
                        label=submission_track,
                        readers=track_edge_readers[role_id] + [member],
                        writers=[venue_id],
                        signatures=[venue_id]
                    )
                )

        client.delete_edges(
            invitation=f"{role_id}/-/{tracks_inv_name}",
            wait_to_finish=True
        )
        openreview.tools.post_bulk_edges(client=client, edges=track_edges_to_post)