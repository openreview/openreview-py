def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    from openreview.venue import matching
    from openreview.arr.helpers import get_resubmissions
    from collections import defaultdict

    def get_title(profile):
        d = profile.content.get('history', [{}])
        if len(d) > 0:
            return d[0].get('position', 'Student')
        else:
            return ''

    def replace_edge(existing_edge=None, edge_inv=None, new_weight=None, submission_id=None, profile_id=None, edge_readers=None):
        if existing_edge:
            client.delete_edges(
                invitation=edge_inv,
                id=existing_edge['id'],
                wait_to_finish=True,
                soft_delete=True
            )
        if submission_id:
            print(f'{profile_id}->{submission_id},weight={new_weight}')
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
        else:
            group_id = edge_inv.split('/-/')[0]
            client.post_edge(
                openreview.api.Edge(
                    invitation=edge_inv,
                    head=group_id,
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
    ae_cmp_inv = domain.content['area_chairs_custom_max_papers_id']['value']
    rev_cmp_inv = domain.content['reviewers_custom_max_papers_id']['value']
    reviewers_id = domain.content['reviewers_id']['value']
    reviewers_group = client.get_group(reviewers_id).members
    area_chairs_id = domain.content['area_chairs_id']['value']
    area_chairs_group = client.get_group(area_chairs_id).members
    senior_area_chairs_id = domain.content['senior_area_chairs_id']['value']
    tracks_field_name = 'research_area'

    tracks_inv_name = 'Research_Area'
    registration_name = 'Registration'
    max_load_name = 'Max_Load_And_Unavailability_Request'
    availability_name = 'Reviewing_Resubmissions'
    status_name = 'Status'
    seniority_name = 'Seniority'
    authors_in_cycle_name = 'Author_In_Current_Cycle'

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

    resubmissions = get_resubmissions(submissions, previous_url_field)
    skip_scores = defaultdict(list)
    reassignment_status = defaultdict(list)
    only_resubmissions = []

    # Fetch profiles and map names to profile IDs - account for change in preferred names
    reviewer_profiles = []
    all_profiles = []
    name_to_id = {}
    for role_id in [reviewers_id, area_chairs_id, senior_area_chairs_id]:
        profiles = openreview.tools.get_profiles(client, client.get_group(role_id).members)
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
    for role_id in [reviewers_id, area_chairs_id, senior_area_chairs_id]:
        load_notes = client.get_all_notes(invitation=f"{role_id}/-/{max_load_name}") ## Assume only 1 note per user
        for note in load_notes:
            if note.signatures[0] not in name_to_id:
                continue
            note_signature_id = name_to_id[note.signatures[0]]
            id_to_load_note[note_signature_id] = note

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

    # Create reviewers submitted groups 
    for submission in submissions:
        if openreview.tools.get_group(client, venue.get_reviewers_id(number=submission.number, submitted=True)):
            continue

        readers=[
            venue_id,
            venue.get_senior_area_chairs_id(number=submission.number),
            venue.get_area_chairs_id(number=submission.number),
            venue.get_reviewers_id(number=submission.number, submitted=True)
        ]
        client.post_group_edit(
            invitation=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            group=openreview.api.Group(id=venue.get_reviewers_id(number=submission.number, submitted=True),
                readers=readers,
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id],
                members=[]
            )
        )

    # Reset custom max papers to ground truth notes
    for role_id in [reviewers_id, area_chairs_id, senior_area_chairs_id]:
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
    

    for submission in resubmissions:
        print(f"rewriting {submission.id}")
        # 1) Find all reassignments and reassignment requests -> 0 out or set to 3
        if 'is not a' in submission.content[rev_reassignment_field]['value'] or \
            'is not a' in submission.content[ae_reassignment_field]['value']:
            continue
        wants_new_reviewers = submission.content[rev_reassignment_field]['value'].startswith('Yes')
        wants_new_ae = submission.content[ae_reassignment_field]['value'].startswith('Yes')
        previous_id = submission.content[previous_url_field]['value'].split('?id=')[1].split('&')[0]
        try:
            previous_submission = client_v1.get_note(previous_id)
            previous_venue_id = previous_submission.invitation.split('/-/')[0]
            previous_reviewers = client_v1.get_group(f"{previous_venue_id}/Paper{previous_submission.number}/Reviewers/Submitted")
            previous_ae = client_v1.get_group(f"{previous_venue_id}/Paper{previous_submission.number}/Area_Chairs") # NOTE: May be problematic when we switch to Action_Editors
            current_client = client_v1
        except:
            previous_submission = client.get_note(previous_id)
            previous_venue_id = previous_submission.domain
            previous_reviewers = client.get_group(f"{previous_venue_id}/Submission{previous_submission.number}/Reviewers/Submitted")
            previous_ae = client.get_group(f"{previous_venue_id}/Submission{previous_submission.number}/Area_Chairs") # NOTE: May be problematic when we switch to Action_Editors
            current_client = client

        print(f"previous submission {submission.id}\nreviewers {wants_new_reviewers}\nae {wants_new_ae}")

        ae_scores = {
            g['id']['tail'] : g['values'][0]
            for g in current_client.get_grouped_edges(invitation=ae_affinity_inv, head=submission.id, select='tail,id,weight', groupby='tail')
        }
        rev_scores = {
            g['id']['tail'] : g['values'][0]
            for g in current_client.get_grouped_edges(invitation=rev_affinity_inv, head=submission.id, select='tail,id,weight', groupby='tail')
        }
        
        # Handle reviewer reassignment
        for reviewer in previous_reviewers.members:
            if previous_venue_id not in reviewer and not reviewer.startswith('~'): # Must be previous venue anon id or a profile ID
                continue

            if previous_venue_id in reviewer:
                reviewer = current_client.get_group(reviewer).members[0] ## De-anonymize
            
            if reviewer not in name_to_id or reviewer not in reviewers_group:
                continue
            
            rev_cmp = {
                g['id']['tail'] : g['values'][0]
                for g in current_client.get_grouped_edges(invitation=rev_cmp_inv, select='id,weight', groupby='tail')
            }

            reviewer_id = name_to_id[reviewer]
            reviewer_edge = rev_scores[reviewer_id] if reviewer_id in rev_scores else None

            if wants_new_reviewers:
                updated_weight = 0
                skip_scores[submission.id].append(reviewer_id)
                reassignment_status[submission.id].append(
                    {
                        'role': reviewers_id,
                        'head': submission.id,
                        'tail': reviewer_id,
                        'label': 'Reassigned'
                    }
                )
            else:
                updated_weight = 3
                reassignment_status[submission.id].append(
                    {
                        'role': reviewers_id,
                        'head': submission.id,
                        'tail': reviewer_id,
                        'label': 'Requested'
                    }
                )
                # Handle case where user has max load 0 but accepts resubmissions
                if id_to_load_note.get(reviewer_id) and int(id_to_load_note[reviewer_id].content['maximum_load_this_cycle']['value']) == 0 and 'Yes' in id_to_load_note[reviewer_id].content['maximum_load_this_cycle_for_resubmissions']['value']:
                    only_resubmissions.append({
                        'role': reviewers_id,
                        'name': reviewer_id
                    })
                    reviewer_cmp_edge = rev_cmp[reviewer_id] ##note implies cmp edge
                    replace_edge(
                        existing_edge=reviewer_cmp_edge,
                        edge_inv=rev_cmp_inv,
                        new_weight=reviewer_cmp_edge['weight'] + 1,
                        profile_id=reviewer_id,
                        edge_readers=[venue_id, senior_area_chairs_id, area_chairs_id, reviewer_id]
                    )

            replace_edge(
                existing_edge=reviewer_edge,
                edge_inv=rev_affinity_inv,
                new_weight=updated_weight,
                submission_id=submission.id,
                profile_id=reviewer_id,
                edge_readers=[venue_id, senior_area_chairs_id, area_chairs_id, reviewer_id]
            )

        # Handle AE reassignments
        for ae in previous_ae.members:
            if previous_venue_id not in ae and not ae.startswith('~'): # Must be previous venue anon id or a profile ID
                continue

            if previous_venue_id in ae:
                ae = current_client.get_group(ae).members[0] ## De-anonymize

            if ae not in name_to_id or ae not in area_chairs_group:
                continue

            ae_cmp = {
                g['id']['tail'] : g['values'][0]
                for g in current_client.get_grouped_edges(invitation=ae_cmp_inv, select='id,weight', groupby='tail')
            }

            ae_id = name_to_id[ae]
            ae_edge = ae_scores[ae_id] if ae_id in ae_scores else None

            if wants_new_ae:
                updated_weight = 0
                skip_scores[submission.id].append(ae_id)
                reassignment_status[submission.id].append(
                    {
                        'role': area_chairs_id,
                        'head': submission.id,
                        'tail': ae_id,
                        'label': 'Reassigned'
                    }
                )
            else:
                updated_weight = 3
                reassignment_status[submission.id].append(
                    {
                        'role': area_chairs_id,
                        'head': submission.id,
                        'tail': ae_id,
                        'label': 'Requested'
                    }
                )
                # Handle case where user has max load 0 but accepts resubmissions
                if id_to_load_note.get(ae_id) and int(id_to_load_note[ae_id].content['maximum_load_this_cycle']['value']) == 0 and 'Yes' in id_to_load_note[ae_id].content['maximum_load_this_cycle_for_resubmissions']['value']:
                    only_resubmissions.append({
                        'role': area_chairs_id,
                        'name': ae_id
                    })
                    ae_cmp_edge = ae_cmp[ae_id] ##note implies cmp edge
                    replace_edge(
                        existing_edge=ae_cmp_edge,
                        edge_inv=ae_cmp_inv,
                        new_weight=ae_cmp_edge['weight'] + 1,
                        profile_id=ae_id,
                        edge_readers=[venue_id, senior_area_chairs_id, ae_id]
                    )

            replace_edge(
                existing_edge=ae_edge,
                edge_inv=ae_affinity_inv,
                new_weight=updated_weight,
                submission_id=submission.id,
                profile_id=ae_id,
                edge_readers=[venue_id, senior_area_chairs_id, ae_id]
            )

        # 2) Grant readership to previous submissions
        if venue.get_area_chairs_id(number=submission.number) not in previous_ae.members:
            current_client.add_members_to_group(previous_ae, venue.get_area_chairs_id(number=submission.number))
        if venue.get_reviewers_id(number=submission.number, submitted=True) not in previous_reviewers.members:
            current_client.add_members_to_group(previous_reviewers, venue.get_reviewers_id(number=submission.number, submitted=True))

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

    # 5) Post status edges
    for head, edges in reassignment_status.items():
        for edge_info in edges:
            role = edge_info['role']
            status_inv = f"{role}/-/{status_name}"
            client.delete_edges(
                invitation=status_inv,
                tail=edge_info['tail'],
                head=head,
                wait_to_finish=True,
                soft_delete=True
            )
            client.post_edge(
                openreview.api.Edge(
                    invitation=status_inv,
                    head=head,
                    tail=edge_info['tail'],
                    label=edge_info['label'],
                    readers=track_edge_readers[role] + [edge_info['tail']],
                    writers=[venue_id],
                    signatures=[venue_id]
                )
            )

    # 6) Post seniority edges
    seniority_edges = []
    seniority_inv = f"{reviewers_id}/-/{seniority_name}"
    for profile in reviewer_profiles:
        if 'student' not in get_title(profile).lower():
            seniority_edges.append(
                openreview.api.Edge(
                    invitation=seniority_inv,
                    head=reviewers_id,
                    tail=profile.id,
                    label='Senior',
                    weight=1,
                    readers=track_edge_readers[reviewers_id] + [profile.id],
                    writers=[venue_id],
                    signatures=[venue_id]
                )
            )
    client.delete_edges(invitation=seniority_inv, wait_to_finish=True, soft_delete=True)
    openreview.tools.post_bulk_edges(client, seniority_edges)

    ## Save code for later
    # 7) Post author in cycle edges
    # authors = set()
    # authors_inv = f"{reviewers_id}/-/{authors_in_cycle_name}"
    # for submission in submissions:
    #     if len(submission.content.get('reviewing_volunteers', {}).get('value', [])) > 0:
    #         authors.update(
    #             set(
    #                 [name_to_id[name] for name in submission.content['reviewing_volunteers']['value']]
    #             )
    #         )
    # author_edges = [
    #     openreview.api.Edge(
    #         invitation=authors_inv,
    #         head=reviewers_id,
    #         tail=user,
    #         readers=track_edge_readers[reviewers_id] + [user],
    #         writers=[venue_id],
    #         signatures=[venue_id]
    #     ) for user in authors
    # ]
    # client.delete_edges(invitation=authors_inv, wait_to_finish=True, soft_delete=True)
    # openreview.tools.post_bulk_edges(client, author_edges)
