def process(client, edit, invitation):

    support_user = 'openreview.net/Support'
    domain = invitation.domain

    note = client.get_note(edit.note.id)
    venue = openreview.helpers.get_venue(client, note.id, support_user, setup=True)
    venue.create_submission_stage()
    venue.create_submission_edit_invitations()
    venue.create_review_stage()
    venue.create_review_edit_invitations()
    venue.edit_invitation_builder.set_edit_stage_invitation()
    venue.invitation_builder.set_group_matching_setup_invitations(venue.get_reviewers_id())
    if venue.use_area_chairs:
        venue.invitation_builder.set_group_matching_setup_invitations(venue.get_area_chairs_id())
    if venue.use_senior_area_chairs:
        venue.invitation_builder.set_group_matching_setup_invitations(venue.get_senior_area_chairs_id())

    # remove PC access to editing the note
    client.post_note_edit(
        invitation=f'{domain}/-/Edit',
        signatures=[venue.id],
        note = openreview.api.Note(
            id = note.id,
            writers = [],
            readers = [support_user,
                       venue.id
            ],
            content = {
                'title': { 'value': openreview.tools.pretty_id(venue.id) },
            }
        )
    )