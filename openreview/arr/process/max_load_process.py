def process(client, note, invitation):
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
    user = note.signatures[0]

    edge_readers = [CONFERENCE_ID]
    if '/Reviewers' in invitation.id:
        edge_readers += [SAC_ID, AC_ID]
        role = domain.content['reviewers_id']['value']
    elif '/Area_Chairs' in invitation.id:
        edge_readers += [AC_ID]
        role = domain.content['area_chairs_id']['value']
    elif '/Senior_Area_Chairs' in invitation.id:
        role = domain.content['senior_area_chairs_id']['value']
    else:
        raise openreview.OpenReviewException('Invalid role for Custom Max Papers edges')
    edge_readers += [user]

    CUSTOM_MAX_PAPERS_ID = f"{role}/-/Custom_Max_Papers"
    

    client.delete_edges(
          invitation=CUSTOM_MAX_PAPERS_ID,
          head=user,
          tail=role
    )
  
    client.post_edge(
      openreview.api.Edge(
        invitation=CUSTOM_MAX_PAPERS_ID,
        readers=edge_readers,
        writers=[CONFERENCE_ID],
        signatures=[CONFERENCE_ID],
        head=role,
        tail=user,
        weight=int(note.content['maximum_load'])
      )
    )

    if note.ddate:
        client.delete_edges(
          invitation=CUSTOM_MAX_PAPERS_ID,
          head=role,
          tail=user
        )
    