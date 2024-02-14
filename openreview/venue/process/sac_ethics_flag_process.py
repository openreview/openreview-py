def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    ethics_review_name = domain.content.get('ethics_review_name', {}).get('value')
    ethics_reviewers_name = domain.get_content_value('ethics_reviewers_name')
    ethics_chairs_id = domain.get_content_value('ethics_chairs_id')
    conflict_policy = domain.content.get('reviewers_conflict_policy', {}).get('value', 'Default')
    conflict_n_years = domain.content.get('reviewers_conflict_n_years', {}).get('value')
    senior_area_chairs_name = domain.content.get('senior_area_chairs_name', {}).get('value')
    submission_name = domain.get_content_value('submission_name')

    flag_note = client.get_note(edit.note.id)
    submission = client.get_note(flag_note.forum)

    if flag_note.content['ethics_review_flag']['value'] == 'Yes':

        # compute conflicts with ethics chairs
        authorids = submission.content['authorids']['value']
        author_profiles = openreview.tools.get_profiles(client, authorids, with_publications=True, with_relations=True)
        members_without_conflict = []
        ethics_chairs = client.get_group(ethics_chairs_id).members
        if ethics_chairs:
            for chair in ethics_chairs:
                user_profile=openreview.tools.get_profiles(client, [chair], with_publications=True, with_relations=True)[0]
                conflicts=openreview.tools.get_conflicts(author_profiles, user_profile, policy=conflict_policy, n_years=conflict_n_years)
                if not conflicts:
                    members_without_conflict.append(user_profile.id)

            paper_senior_area_chairs = f'{venue_id}/{submission_name}{submission.number}/{senior_area_chairs_name}'
            client.add_members_to_group(paper_senior_area_chairs, members_without_conflict)

        # create Custom User Demand edge
        client.post_edge(openreview.api.Edge(
                head=submission.id,
                tail=f'{venue_id}/{ethics_reviewers_name}',
                invitation=f'{venue_id}/{ethics_reviewers_name}/-/Custom_User_Demands',
                readers=[
                    venue_id,
                    ethics_chairs_id,
                    f'{venue_id}/{ethics_reviewers_name}'
                ],
                writers=[venue_id],
                signatures=[venue_id],
                weight=2
            ))

        # flag paper
        client.post_note_edit(
            invitation=f'{venue_id}/-/{ethics_review_name}_Flag',
            note=openreview.api.Note(
                id=submission.id,
                content = {
                    'flagged_for_ethics_review': { 'value': True }
                }
            ),
            signatures=[venue_id]
        )