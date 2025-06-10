def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    from openreview.venue import matching
    from openreview.arr.helpers import get_resubmissions
    from openreview.arr.arr import SENIORITY_PUBLICATION_COUNT
    from collections import defaultdict

    def is_main_venue(link, pub):
        venueid = pub.content.get('venueid')
        if venueid is not None:
            if not isinstance(venueid, str):
                venueid = venueid.get("value")
            if venueid.startswith("dblp.org/conf/"):
                parts = venueid.split("/")
                conf = parts[2]
                if conf.lower() in [ "aacl", "acl", "cl", "conll", "eacl", "emnlp", "findings", "naacl", "tacl", "coling", "ijcnlp"]:
                    return True
        venue = pub.content.get('venue')
        if venue is not None:
            if not isinstance(venue, str):
                venue = venue.get("value")
            if 'withdraw' in venue.lower() or 'desk reject' in venue.lower():
                return False
            for token in venue.lower().split():
                if token in ["aacl", "acl", "cl", "conll", "eacl", "emnlp", "findings", "naacl", "tacl", "coling", "main", "ijcnlp", "short", "papers", "hlt", 'sem']:
                    return True
    
        if link.startswith("https://transacl.org"):
            return True
        ending = ''
        if "://aclanthology.org/" in link:
            ending = link.split('/')[3]
        elif "://aclweb.org/anthology/" in link:
            ending = link.split("/")[4]
        elif "://aclanthology.info/papers/" in link:
            ending = link.split("/")[4]
        else:
            return False

        if ending[0] in ["C", "D", "E", "I", "J", "K", "N", "P", "Q"]:
            return True
        elif '.' in ending and ending.split('.')[1].split("-")[0] in [ "aacl", "acl", "cl", "conll", "eacl", "emnlp", "findings", "naacl", "tacl", "coling", "ijcnlp"]:
            return True
        return False

    def is_recent(pub, recent=5):
        venueid = pub.content.get('venueid')
        if venueid is not None and (not isinstance(venueid, str)):
            venueid = venueid.get("value")
        venue = pub.content.get('venue')
        if venue is not None and (not isinstance(venue, str)):
            venue = venue.get("value")
        current = datetime.date.today().year
        for year in range(current - recent + 1, current + 1):
            if venue is not None and str(year) in venue:
                return True
            if venueid is not None and str(year) in venueid:
                return True
        return False

    def collect_pub_stats(publications):
        # Here 'publications' comes from the user profile:
        # profile.content.get("publications", [])
        acl_main_recent = 0
        for pub in publications:
            link = pub.content.get('pdf', '')
            if link == '' or isinstance(link, dict):
                link = pub.content.get('html', '')
                if isinstance(link, dict):
                    link = link.get('value', '')
            if is_recent(pub) and is_main_venue(link, pub) and 'everyone' in pub.readers:
                acl_main_recent += 1
        return acl_main_recent

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
    ae_reassignment_field = 'reassignment_request_area_chair'
    rev_reassignment_field = 'reassignment_request_reviewers'
    rev_affinity_inv = domain.content['reviewers_affinity_score_id']['value']
    rev_cmp_inv = domain.content['reviewers_custom_max_papers_id']['value']
    reviewers_id = domain.content['reviewers_id']['value']
    reviewers_group = client.get_group(reviewers_id).members
    area_chairs_id = domain.content['area_chairs_id']['value']
    #area_chairs_group = client.get_group(area_chairs_id).members
    senior_area_chairs_id = domain.content['senior_area_chairs_id']['value']
    tracks_field_name = 'research_area'

    tracks_inv_name = 'Research_Area'
    registration_name = 'Registration'
    max_load_name = 'Max_Load_And_Unavailability_Request'
    status_name = 'Status'
    seniority_name = 'Seniority'

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    if client.get_edges_count(invitation=f"{reviewers_id}/-/Affinity_Score") <= 0:
        print(f"no affinity scores for {reviewers_id}")
        return

    request_form = client_v1.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)
    submissions = venue.get_submissions()

    resubmissions = get_resubmissions(submissions, previous_url_field)
    skip_scores = defaultdict(list)
    reassignment_status = defaultdict(list)
    only_resubmissions = []

    # Fetch profiles and map names to profile IDs - account for change in preferred names
    reviewer_profiles = []
    all_profiles = []
    name_to_id = {}
    for role_id in [reviewers_id]:
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
    for role_id in [reviewers_id]:
        load_notes = client.get_all_notes(invitation=f"{role_id}/-/{max_load_name}") ## Assume only 1 note per user
        for note in load_notes:
            if note.signatures[0] not in name_to_id:
                continue
            note_signature_id = name_to_id[note.signatures[0]]
            id_to_load_note[note_signature_id] = note

    # Build track map
    track_to_ids = {}
    for role_id in [reviewers_id]:
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
        reviewers_id: [venue_id, senior_area_chairs_id, area_chairs_id]
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
    for role_id in [reviewers_id]:
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
    
    reviewer_exceptions = {}
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
            previous_parent_reviewers = client_v1.get_group(f"{previous_venue_id}/Paper{previous_submission.number}/Reviewers")
            previous_reviewers = openreview.tools.get_group(client_v1, f"{previous_venue_id}/Paper{previous_submission.number}/Reviewers/Submitted")
            previous_ae = client_v1.get_group(f"{previous_venue_id}/Paper{previous_submission.number}/Area_Chairs") # NOTE: May be problematic when we switch to Action_Editors
            current_client = client_v1
        except:
            previous_submission = client.get_note(previous_id)
            previous_venue_id = previous_submission.domain
            previous_parent_reviewers = client.get_group(f"{previous_venue_id}/Submission{previous_submission.number}/Reviewers")
            previous_reviewers = openreview.tools.get_group(client, f"{previous_venue_id}/Submission{previous_submission.number}/Reviewers/Submitted")
            previous_ae = client.get_group(f"{previous_venue_id}/Submission{previous_submission.number}/Area_Chairs") # NOTE: May be problematic when we switch to Action_Editors
            current_client = client

        print(f"previous submission {submission.id}\nreviewers {wants_new_reviewers}\nae {wants_new_ae}")

        if venue.get_reviewers_id(number=submission.number, submitted=wants_new_reviewers) not in previous_parent_reviewers.members:
            current_client.add_members_to_group(previous_parent_reviewers, venue.get_reviewers_id(number=submission.number, submitted=wants_new_reviewers))
            if previous_reviewers is not None:
                current_client.add_members_to_group(previous_reviewers, venue.get_reviewers_id(number=submission.number, submitted=wants_new_reviewers))

        if previous_reviewers is None:
            print(f"no previous reviewers for {submission.id}")
            continue

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
                if id_to_load_note.get(reviewer_id) and \
                    int(id_to_load_note[reviewer_id].content['maximum_load_this_cycle']['value']) == 0 and \
                        'Yes' in id_to_load_note[reviewer_id].content['maximum_load_this_cycle_for_resubmissions']['value']:
                    only_resubmissions.append({
                        'role': reviewers_id,
                        'name': reviewer_id
                    })
                    reviewer_cmp_edge = rev_cmp[reviewer_id] ##note implies cmp edge
                    if reviewer_id not in reviewer_exceptions:
                        reviewer_exceptions[reviewer_id] = 0
                    reviewer_exceptions[reviewer_id] += 1

                    replace_edge(
                        existing_edge=reviewer_cmp_edge,
                        edge_inv=rev_cmp_inv,
                        new_weight=reviewer_exceptions[reviewer_id],
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
        if collect_pub_stats(profile.content.get('publications', [])) >= SENIORITY_PUBLICATION_COUNT:
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