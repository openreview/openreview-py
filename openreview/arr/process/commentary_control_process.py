def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    sender = domain.get_content_value('message_sender')
    authors_name = domain.get_content_value('authors_name')
    submission_name = domain.get_content_value('submission_name')
    reviewers_name = domain.get_content_value('reviewers_name')
    area_chairs_name = domain.get_content_value('area_chairs_name')
    senior_area_chairs_name = domain.get_content_value('senior_area_chairs_name')
    reviewers_submitted_name = domain.get_content_value('reviewers_submitted_name')
    review_name = domain.get_content_value('review_name')

    submission = client.get_note(invitation.content['forum']['value'])
    paper_number = submission.number
    comment_invitation = client.get_invitation(id=f"{venue_id}/Submission{paper_number}/-/Official_Comment")

    if 'yes' in edit.note.content['enable_author_commentary']['value'].lower():
        new_participants = ['Authors']
    else:
        new_participants = []
    
    readers_to_ids = {
        "Assigned Reviewers": f"{venue_id}/Submission{paper_number}/Reviewers",
        "Assigned Submitted Reviewers": f"{venue_id}/Submission{paper_number}/Reviewers/Submitted",
        "Authors": f"{venue_id}/Submission{paper_number}/Authors"
    }
    required_invitees = [readers_to_ids[r] for r in new_participants]
    missing_invitees = set(required_invitees).difference(set(comment_invitation.invitees))
    extra_invitees = (set(comment_invitation.invitees).intersection(set(readers_to_ids.values()))).difference(set(required_invitees))
    
    final_invitees = [i for i in comment_invitation.invitees if i not in extra_invitees] + list(missing_invitees)
    print(missing_invitees)
    print(extra_invitees)
    print(final_invitees)
    
    readers_to_prefix = {
        "Assigned Reviewers": f"{venue_id}/Submission{paper_number}/Reviewer_.*",
        "Assigned Submitted Reviewers": f"{venue_id}/Submission{paper_number}/Reviewer_.*",
        "Authors": f"{venue_id}/Submission{paper_number}/Authors"
    }
    required_signatures = [readers_to_prefix[r] for r in new_participants]
    signatures = [item['prefix'] if 'prefix' in item else item['value'] for item in comment_invitation.edit['signatures']['param']['items']]
    missing_signatures = set(required_signatures).difference(set(signatures))
    extra_signatures = (set(signatures).intersection(set(readers_to_prefix.values()))).difference(set(required_signatures))
    
    final_signatures = []
    for item in comment_invitation.edit['signatures']['param']['items']:
        value = item['prefix'] if 'prefix' in item else item['value']
        if value not in extra_signatures:
            final_signatures.append(item)
    for signature in missing_signatures:
        if signature.endswith('.*'):
            final_signatures.append({
                'prefix': signature,
                'optional': True
            })
        else:
            final_signatures.append({
                'value': signature,
                'optional': True
            })
    
    print(missing_signatures)
    print(extra_signatures)
    print(final_signatures)
    
    possible_readers = set(readers_to_prefix.values()).union(set(readers_to_ids.values()))
    required_readers = set(required_signatures).union(required_invitees)
    readers = comment_invitation.edit['note']['readers']['param']['enum']
    missing_readers = required_readers.difference(set(readers))
    extra_readers = (set(readers).intersection(possible_readers)).difference(required_readers)
    
    final_readers = [r for r in readers if r not in extra_readers] + list(missing_readers)
    
    print(missing_readers)
    print(extra_readers)
    print(final_readers)
    
    client.post_invitation_edit(
        invitations=meta_invitation_id,
        readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=openreview.api.Invitation(
            id=comment_invitation.id,
            signatures=[venue_id],
            invitees=final_invitees,
            edit={
                'signatures': {
                    'param': {
                        'items': final_signatures
                    }
                },
                'note': {
                    'readers': {
                        'param': {
                            'enum': final_readers
                        }
                    }
                }
            }
        )
    )