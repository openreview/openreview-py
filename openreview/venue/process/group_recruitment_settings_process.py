def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    reviewers_name = domain.get_content_value('reviewers_name')
    reviewers_id = domain.get_content_value('reviewers_id')
    area_chairs_name = domain.get_content_value('area_chairs_name')
    area_chairs_id = domain.get_content_value('area_chairs_id')
    senior_area_chairs_name = domain.get_content_value('senior_area_chairs_name')
    meta_invitation_id = domain.content['meta_invitation_id']['value']

    committee_group_id = edit.group.id.replace('/Invited', '')
    committee_name = reviewers_name if reviewers_id == committee_group_id else area_chairs_name if area_chairs_id == committee_group_id else senior_area_chairs_name
    recruitment_invitation_id = domain.get_content_value(f'{committee_name.lower()}_recruitment_id')

    allow_overlap = edit.group.content.get('allow_overlap', {}).get('value', False)

    invitation_content = {}
    if not allow_overlap:
        if committee_name == reviewers_name and area_chairs_name:
            invitation_content['overlap_committee_name'] = { 'value': area_chairs_name }
            invitation_content['overlap_committee_id'] = { 'value': area_chairs_id }
        elif committee_name == area_chairs_name:
            invitation_content['overlap_committee_name'] = { 'value': reviewers_name }
            invitation_content['overlap_committee_id'] = { 'value': reviewers_id }
    else:
            invitation_content['overlap_committee_name'] = { 'delete': True }
            invitation_content['overlap_committee_id'] = { 'delete': True  }


    client.post_invitation_edit(
        invitations=meta_invitation_id,
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=recruitment_invitation_id,
            content=invitation_content
        )
    )
        
