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
    user = edit.signatures[0]

    edge_readers = [CONFERENCE_ID]
    inv_role = invitation.id.split('/')[-3]
    role = None
    for venue_role in [SAC_ID, AC_ID, REV_ID]:
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
        readers=edge_readers,
        writers=[CONFERENCE_ID],
        signatures=[CONFERENCE_ID],
        head=role,
        tail=user,
        weight=int(edit.note.content['maximum_load']['value'])
      )
    )

    if edit.note.ddate:
        client.delete_edges(
          invitation=CUSTOM_MAX_PAPERS_ID,
          head=role,
          tail=user
        )
    