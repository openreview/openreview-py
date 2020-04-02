def process(client, note, invitation):
    from datetime import datetime
    CONFERENCE_ID = ''
    CONFERENCE_SHORT_NAME = ''
    CONFERENCE_NAME = ''
    CONFERENCE_YEAR = ''
    PAPER_AUTHORS_ID = ''
    PAPER_REVIEWERS_ID = ''
    PAPER_AREA_CHAIRS_ID = ''
    PROGRAM_CHAIRS_ID = ''
    WITHDRAWN_SUBMISSION_ID = ''
    REVEAL_AUTHORS_ON_WITHDRAW = False
    REVEAL_SUBMISSIONS_ON_WITHDRAW = False
    EMAIL_PROGRAM_CHAIRS = False

    committee = [PAPER_AUTHORS_ID, PAPER_REVIEWERS_ID]
    if PAPER_AREA_CHAIRS_ID:
        committee.append(PAPER_AREA_CHAIRS_ID)
    committee.append(PROGRAM_CHAIRS_ID)

    forum_note = client.get_note(note.forum)
    forum_note.invitation = WITHDRAWN_SUBMISSION_ID

    original_note = None
    if forum_note.content['authors'] == ['Anonymous'] and REVEAL_AUTHORS_ON_WITHDRAW:
        original_note = client.get_note(forum_note.original)

    note = original_note if original_note else forum_note

    if REVEAL_SUBMISSIONS_ON_WITHDRAW:
        forum_note.readers = ['everyone']
    else:
        forum_note.readers = committee

    if REVEAL_AUTHORS_ON_WITHDRAW:
        forum_note.content = {
            '_bibtex': openreview.tools.get_bibtex(note = note, venue_fullname = CONFERENCE_NAME, url_forum = forum_note.id, year = CONFERENCE_YEAR, anonymous = not(REVEAL_AUTHORS_ON_WITHDRAW), baseurl = 'https://openreview.net')
        }
    else:
        forum_note.content = {
            'authors': forum_note.content['authors'],
            'authorids': forum_note.content['authorids'],
            '_bibtex': openreview.tools.get_bibtex(note = note, venue_fullname = CONFERENCE_NAME, url_forum = forum_note.id, year = CONFERENCE_YEAR, anonymous = not(REVEAL_AUTHORS_ON_WITHDRAW), baseurl = 'https://openreview.net')
        }

    forum_note = client.post_note(forum_note)

    # Expire review, meta-review and decision invitations
    invitation_regex = CONFERENCE_ID + '/Paper' + str(forum_note.number) + '/-/(Official_Review|Meta_Review|Decision|Revision|Withdraw|Supplementary_Material)$'
    all_paper_invitations = openreview.tools.iterget_invitations(client, regex = invitation_regex)
    now = openreview.tools.datetime_millis(datetime.utcnow())
    for invitation in all_paper_invitations:
        invitation.expdate = now
        client.post_invitation(invitation)

    client.remove_members_from_group(CONFERENCE_ID + '/Authors', PAPER_AUTHORS_ID)

    # Mail Authors, Reviewers, ACs (if present) and PCs
    email_subject = '''{CONFERENCE_SHORT_NAME}: Paper #{paper_number} withdrawn by paper authors'''.format(
        CONFERENCE_SHORT_NAME = CONFERENCE_SHORT_NAME,
        paper_number = forum_note.number
    )
    email_body = '''The {CONFERENCE_SHORT_NAME} paper "{paper_title_or_num}" has been withdrawn by the paper authors.'''.format(
        CONFERENCE_SHORT_NAME = CONFERENCE_SHORT_NAME,
        paper_title_or_num = forum_note.content.get('title', '#'+str(forum_note.number))
    )

    if not EMAIL_PROGRAM_CHAIRS:
        committee.remove(PROGRAM_CHAIRS_ID)
    client.post_message(email_subject, committee, email_body)
