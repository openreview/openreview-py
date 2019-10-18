def process(client, note, invitation):
    from datetime import datetime
    CONFERENCE_ID = ''
    AUTHORS_ID = ''
    REVIEWERS_ID = ''
    AREA_CHAIRS_ID = ''
    PROGRAM_CHAIRS_ID = ''
    DESK_REJECTED_SUBMISSION_ID = ''
    REVEAL_AUTHORS_ON_DESK_REJECT = False

    forum_note = client.get_note(note.forum)
    forum_note.invitation = DESK_REJECTED_SUBMISSION_ID
    if REVEAL_AUTHORS_ON_DESK_REJECT:
        # REVEAL_AUTHORS_ON_DESK_REJECT will only be True if this is a double blind conference
        original_note = client.get_note(id = blind_note.original)
        blind_note.content['authors'] = original_note.content['authors']
        blind_note.content['authorids'] = original_note.content['authorids']
    client.post_note(blind_note)

    # Expire review, meta-review and decision invitations
    paper_number = blind_note.number
    invitation_regex = CONFERENCE_ID + '/Paper' + str(paper_number) + '/-/(Official_Review|Meta_Review|Decision)$'
    all_paper_invitations = openreview.tools.get_invitations(client, regex = invitation_regex)
    for invitation in all_paper_invitations:
        invitation.expdate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
        client.post_invitation(invitation)

    # Mail Authors, Reviewers, ACs (if present) and PCs
    email_subject = '''{CONFERENCE_ID}: Paper {paper_title} has been marked desk rejected'''.format(CONFERENCE_ID = CONFERENCE_ID, )
    email_body = ''''''


