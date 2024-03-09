def process(client, invitation):

    from openreview.venue import matching
    from collections import defaultdict

    def replace_edge(existing_edge=None, edge_inv=None, new_weight=None, submission_id=None, profile_id=None, edge_readers=None):
        client.delete_edges(
            invitation=edge_inv,
            id=existing_edge['id'],
            wait_to_finish=True,
            soft_delete=True
        )
        client.post_edge(
            openreview.api.Edge(
                invitation=edge_inv,
                head=submission_id,
                tail=profile_id,
                weight=new_weight,
                readers=edge_readers,
                writers=[venue_id],
                signatures=[venue_id]
            )
        )


    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    request_form_id = domain.content['request_form_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    previous_url_field = 'previous_URL'
    ae_reassignment_field = 'reassignment_request_action_editor'
    rev_reassignment_field = 'reassignment_request_reviewers'
    ae_affinity_inv = domain.content['area_chairs_affinity_score_id']['value']
    rev_affinity_inv = domain.content['reviewers_affinity_score_id']['value']
    reviewers_id = domain.content['reviewers_id']['value']
    area_chairs_id = domain.content['area_chairs_id']['value']
    senior_area_chairs_id = domain.content['senior_area_chairs_id']['value']
    tracks_field_name = 'research_area'

    tracks_inv_name = 'Research_Area'
    registration_name = 'Registration'
    max_load_name = 'Max_Load_And_Unavailability_Request'

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    request_form = client_v1.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue_stage_invitations = client_v1.get_all_invitations(regex=f"{support_group}/-/Request{request_form.number}.*")
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)
    invitation_builder = openreview.arr.InvitationBuilder(venue)
    submissions = venue.get_submissions()

    resubmissions = filter(
        lambda s: len(s.content[previous_url_field]['value']) > 0, 
        submissions
    )

    # Fetch profiles and map names to profile IDs - account for change in preferred names
    all_profiles = []
    name_to_id = {}
    for role_id in [reviewers_id, area_chairs_id, senior_area_chairs_id]:
        all_profiles.extend(openreview.tools.get_profiles(client, client.get_group(role_id).members))
    for profile in all_profiles:
        filtered_names = filter(
            lambda obj: 'username' in obj and len(obj['username']) > 0,
            profile.content.get('names', [])
        )
        for name_obj in filtered_names:
            name_to_id[name_obj['username']] = profile.id

    # Build track map
    track_to_ids = {}
    for role_id in [reviewers_id, area_chairs_id, senior_area_chairs_id]:
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
        reviewers_id: [venue_id, senior_area_chairs_id, area_chairs_id],
        area_chairs_id: [venue_id, senior_area_chairs_id],
        senior_area_chairs_id: [venue_id]
    }

    for submission in resubmissions:
        # 1) Find all reassignments and reassignment requests -> 0 out or set to 3
        if 'is not a' in submission.content[rev_reassignment_field]['value'] or \
            'is not a' in submission.content[rev_reassignment_field]['value']:
            continue
        wants_new_reviewers = submission.content[rev_reassignment_field]['value'].startswith('Yes')
        wants_new_ae = submission.content[ae_reassignment_field]['value'].startswith('Yes')
        previous_id = submission.content[previous_url_field].split('?id=')[1].split('&')[0]
        try:
            previous_submission = client_v1.get_note(previous_id)
            previous_venue_id = previous_submission.invitation.split('/-/')[0]
            previous_reviewers = client_v1.get_group(f"{previous_venue_id}/Reviewers/Submitted")
            previous_ae = client_v1.get_group(f"{previous_venue_id}/Area_Chairs") # NOTE: May be problematic when we switch to Action_Editors
            current_client = client_v1
        except:
            previous_submission = client.get_note(previous_id)
            previous_venue_id = previous_submission.domain
            previous_reviewers = client.get_group(f"{previous_venue_id}/Reviewers/Submitted")
            previous_ae = client.get_group(f"{previous_venue_id}/Area_Chairs") # NOTE: May be problematic when we switch to Action_Editors
            current_client = client

        ae_scores = {
            g['id']['tail'] : g['values']
            for g in client.get_grouped_edges(invitation=ae_affinity_inv, head=submission.id, select='tail,id,weight')
        }
        rev_scores = {
            g['id']['tail'] : g['values']
            for g in client.get_grouped_edges(invitation=rev_affinity_inv, head=submission.id, select='tail,id,weight')
        }
        
        # Handle reviewer reassignment
        for reviewer in previous_reviewers.members:
            if reviewer not in name_to_id or name_to_id[reviewer] not in rev_scores:
                continue
            reviewer_id = name_to_id[reviewer]
            reviewer_edge = rev_scores[reviewers_id]

            if wants_new_reviewers:
                updated_weight = 0
            else:
                updated_weight = 3

            replace_edge(
                existing_edge=reviewer_edge,
                edge_inv=rev_affinity_inv,
                new_weight=updated_weight,
                submission_id=submission.id,
                profile_id=reviewer_id,
                edge_readers=[venue_id, senior_area_chairs_id, area_chairs_id, reviewer_id]
            )

        # Handle AE reassignment
        for ae in previous_ae.members:
            if ae not in name_to_id or name_to_id[ae] not in ae_scores:
                continue
            ae_id = name_to_id[ae]
            ae_edge = ae_scores[ae_id]

            if wants_new_ae:
                updated_weight = 0
            else:
                updated_weight = 3

            replace_edge(
                existing_edge=ae_edge,
                edge_inv=ae_affinity_inv,
                new_weight=updated_weight,
                submission_id=submission.id,
                profile_id=ae_id,
                edge_readers=[venue_id, senior_area_chairs_id, ae_id]
            )

        # 2) Grant readership to previous submissions
        current_client.add_members_to_group(previous_ae, venue.get_area_chairs_id(number=submission.number))
        current_client.add_members_to_group(previous_reviewers, venue.get_reviewers_id(number=submission.number, submitted=True))

    # 3) Post track edges
    for role_id, track_to_members in track_to_ids.items():
        track_edges_to_post = []

        for submission in submissions:
            submission_track = submission.content[tracks_field_name]['value']
            members = track_to_members[submission_track]

            for member in members:
                track_edges_to_post.append(
                    openreview.api.Edge(
                        invitation=f"{role_id}/-/{tracks_inv_name}",
                        head=submission.id,
                        tail=member,
                        weight=1,
                        readers=track_edge_readers[role_id],
                        writers=[venue_id],
                        signatures=[venue_id]
                    )
                )

        client.delete_edges(
            invitation=f"{role_id}/-/{tracks_inv_name}",
            wait_to_finish=True
        )
        openreview.tools.post_bulk_edges(client=client, edges=track_edges_to_post)

