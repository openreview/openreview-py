def process(client, edit, invitation):
    import time
    
    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    venue_name = domain.content['title']['value']

    CONFERENCE_ID = domain.id
    SAC_ID = domain.content['senior_area_chairs_id']['value']
    AC_ID = domain.content['area_chairs_id']['value']
    REV_ID = domain.content['reviewers_id']['value']
    ETHICS_REV_ID = domain.content['ethics_chairs_id']['value'].replace(
      domain.content['ethics_chairs_name']['value'],
      domain.content['ethics_reviewers_name']['value']
    )
    user = client.get_profile(edit.signatures[0]).id

    edge_readers = [CONFERENCE_ID]
    inv_role = invitation.id.split('/')[-3]
    role = None
    for venue_role in [SAC_ID, AC_ID, REV_ID, ETHICS_REV_ID]:
      if f"/{inv_role}" in venue_role:
        role = venue_role
        if venue_role == AC_ID:
          edge_readers += [SAC_ID]
        elif venue_role == REV_ID:
          edge_readers += [SAC_ID, AC_ID]

    if not role:
      raise openreview.OpenReviewException('Invalid role for Custom Max Papers edges')

    edge_readers += [user]

    CUSTOM_MAX_PAPERS_ID = f"{role}/-/Custom_Max_Papers"
    AVAILABILITY_ID = f"{role}/-/Reviewing_Resubmissions"

    if edit.note.ddate:
      client.delete_edges(
        invitation=CUSTOM_MAX_PAPERS_ID,
        head=role,
        tail=user
      )
      client.delete_edges(
        invitation=AVAILABILITY_ID,
        head=role,
        tail=user
      )
      return
    

    client.delete_edges(
      invitation=CUSTOM_MAX_PAPERS_ID,
      head=role,
      tail=user,
      wait_to_finish=True,
      soft_delete=True
    )
  
    client.post_edge(
      openreview.api.Edge(
        invitation=CUSTOM_MAX_PAPERS_ID,
        writers=[CONFERENCE_ID],
        signatures=[CONFERENCE_ID],
        head=role,
        tail=user,
        weight=int(edit.note.content['maximum_load_this_cycle']['value'])
      )
    )

    if role == SAC_ID or role == ETHICS_REV_ID:
      return

    client.delete_edges(
      invitation=AVAILABILITY_ID,
      head=role,
      tail=user,
      wait_to_finish=True,
      soft_delete=True
    )

    availability_label = None
    if 'yes' in edit.note.content['maximum_load_this_cycle_for_resubmissions']['value'].lower() and int(edit.note.content['maximum_load_this_cycle']['value']) == 0:
      availability_label = 'Only Reviewing Resubmissions'
    elif 'yes' in edit.note.content['maximum_load_this_cycle_for_resubmissions']['value'].lower():
      availability_label = 'Yes'
    elif 'no' in edit.note.content['maximum_load_this_cycle_for_resubmissions']['value'].lower():
      availability_label = 'No'

    client.post_edge(
      openreview.api.Edge(
        invitation=AVAILABILITY_ID,
        writers=[CONFERENCE_ID],
        signatures=[CONFERENCE_ID],
        head=role,
        tail=user,
        label=availability_label
      )
    )
    