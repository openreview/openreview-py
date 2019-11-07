def process(client, note, invitation):
    from datetime import datetime
    CONFERENCE_ID = ''
    CONFERENCE_SHORT_NAME = ''
    PAPER_AUTHORS_ID = ''
    PAPER_REVIEWERS_ID = ''
    PAPER_AREA_CHAIRS_ID = ''
    PROGRAM_CHAIRS_ID = ''
    WITHDRAWN_SUBMISSION_ID = ''
    REVEAL_AUTHORS_ON_WITHDRAW = False

    forum_note = client.get_note(note.forum)
    forum_note.invitation = WITHDRAWN_SUBMISSION_ID
    if REVEAL_AUTHORS_ON_WITHDRAW:
        # REVEAL_AUTHORS_ON_WITHDRAW will only be True if this is a double blind conference
        original_note = client.get_note(id = forum_note.original)
        forum_note.content['authors'] = original_note.content['authors']
        forum_note.content['authorids'] = original_note.content['authorids']
    client.post_note(forum_note)

    # Expire review, meta-review and decision invitations
    invitation_regex = CONFERENCE_ID + '/Paper' + str(forum_note.number) + '/-/(Official_Review|Meta_Review|Decision|Revision|Withdraw)$'
    all_paper_invitations = openreview.tools.iterget_invitations(client, regex = invitation_regex)
    now = openreview.tools.datetime_millis(datetime.utcnow())
    for invitation in all_paper_invitations:
        invitation.expdate = now
        client.post_invitation(invitation)

    # Mail Authors, Reviewers, ACs (if present) and PCs
    email_subject = '''{CONFERENCE_SHORT_NAME}: Paper #{paper_number} withdrawn by paper authors'''.format(
        CONFERENCE_SHORT_NAME = CONFERENCE_SHORT_NAME,
        paper_number = forum_note.number
    )
    email_body = '''The {CONFERENCE_SHORT_NAME} paper title "{paper_title}" has been withdrawn by the paper authors.'''.format(
        CONFERENCE_SHORT_NAME = CONFERENCE_SHORT_NAME,
        paper_title = forum_note.content['title']
    )
    recipients = [PAPER_AUTHORS_ID, PAPER_REVIEWERS_ID, PROGRAM_CHAIRS_ID]
    if PAPER_AREA_CHAIRS_ID:
        recipients.append(PAPER_AREA_CHAIRS_ID)
    client.send_mail(email_subject, recipients, email_body)
