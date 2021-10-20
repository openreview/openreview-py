def process(client, edit, invitation):
    venue_id='.TMLR'
    note=edit.note
    paper_group_id=edit.invitation.split('/-/')[0]
    journal = openreview.journal.Journal(client, venue_id, '1234')

    ## TODO: send message to the reviewer, AE confirming the review was posted

    ## Create invitation to rate reviews
    journal.invitation_builder.set_review_rating_invitation(journal, note)

    review_note=client.get_note(note.id)
    if review_note.readers == ['everyone']:
        return

    reviews=client.get_notes(forum=note.forum, invitation=edit.invitation)
    if len(reviews) == 3:
        ## Release the reviews to everyone
        invitation = client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=f'{paper_group_id}/-/Release_Review',
                bulk=True,
                invitees=[venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                edit={
                    'signatures': { 'values': [venue_id ] },
                    'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${{note.id}.signatures}' ] },
                    'writers': { 'values': [ venue_id ] },
                    'note': {
                        'id': { 'value-invitation': edit.invitation },
                        'readers': { 'values': [ 'everyone' ] }
                    }
                }
        ))
        ## Enable official recommendation
        submission = client.get_note(note.forum)
        duedate = openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(days = journal.default_offset_days))
        journal.invitation_builder.set_official_recommendation_invitation(journal, submission, duedate)