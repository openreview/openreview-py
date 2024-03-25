    if 'i agree' in note.content.get('Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement', {}).get('value', 'not agree').lower(): 
        client.post_note_edit(
            invitation=f"{venue_id}/Submission{note.number}/-/Blind_Submission_License_Agreement",
            signatures=[program_chairs_id],
            note=openreview.api.Note(
                content={
                    "Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement": note.content['Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement'],
                    "section_2_permission_to_publish_peer_reviewers_content_agreement": note.content['section_2_permission_to_publish_peer_reviewers_content_agreement']
                }
            )
        )

    client.add_members_to_group(domain.content['reviewers_id']['value'], note.content.get('reviewing_volunteers').get('value'))