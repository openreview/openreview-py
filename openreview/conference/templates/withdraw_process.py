def process_update(client, note, invitation, existing_note):
    from datetime import datetime
    CONFERENCE_ID = ''
    CONFERENCE_SHORT_NAME = ''
    CONFERENCE_NAME = ''
    CONFERENCE_YEAR = ''
    PAPER_AUTHORS_ID = ''
    PAPER_REVIEWERS_ID = ''
    PAPER_AREA_CHAIRS_ID = ''
    PAPER_SENIOR_AREA_CHAIRS_ID = ''
    PROGRAM_CHAIRS_ID = ''
    CONFERENCE_ROLES = []
    WITHDRAWN_SUBMISSION_ID = ''
    BLIND_SUBMISSION_ID = ''
    SUBMISSION_READERS = []
    REVEAL_AUTHORS_ON_WITHDRAW = False
    REVEAL_SUBMISSIONS_ON_WITHDRAW = False
    EMAIL_PROGRAM_CHAIRS = False
    HIDE_FIELDS = []

    forum_note = client.get_note(note.forum)
    for i in range(len(SUBMISSION_READERS)):
        SUBMISSION_READERS[i] = SUBMISSION_READERS[i].format(number=forum_note.number)

    PAPER_AUTHORS_ID = PAPER_AUTHORS_ID.format(number=forum_note.number)
    PAPER_REVIEWERS_ID = PAPER_REVIEWERS_ID.format(number=forum_note.number)
    PAPER_AREA_CHAIRS_ID = PAPER_AREA_CHAIRS_ID.format(number=forum_note.number)
    PAPER_SENIOR_AREA_CHAIRS_ID = PAPER_SENIOR_AREA_CHAIRS_ID.format(number=forum_note.number)

    committee = [PAPER_AUTHORS_ID, PAPER_REVIEWERS_ID]
    if PAPER_AREA_CHAIRS_ID:
        committee.append(PAPER_AREA_CHAIRS_ID)
    if PAPER_SENIOR_AREA_CHAIRS_ID:
        committee.append(PAPER_SENIOR_AREA_CHAIRS_ID)
    committee.append(PROGRAM_CHAIRS_ID)

    if note.ddate:
        ## Undo withdraw submission
        print('undo withdraw submission')
        if forum_note.invitation == WITHDRAWN_SUBMISSION_ID:
            forum_note.invitation = BLIND_SUBMISSION_ID
            if forum_note.original:
                print('is double blind')
                forum_note.content = {
                    'authors': ['Anonymous'],
                    'authorids': [PAPER_AUTHORS_ID],
                    # '_bibtex': bibtex Solve this later
                }
                for field in HIDE_FIELDS:
                    forum_note.content[field] = ''

            forum_note.readers = SUBMISSION_READERS
            forum_note = client.post_note(forum_note)

            #restore assignment edges
            conference_roles = '|'.join(CONFERENCE_ROLES)
            paper_groups = client.get_groups(regex=f'{CONFERENCE_ID}/Paper{forum_note.number}/({conference_roles})$')
            members = []
            for group in paper_groups:
                members.extend(group.members)

            for role in CONFERENCE_ROLES:
                edges = client.get_edges(invitation=f'{CONFERENCE_ID}/{role}/-/Assignment', head=forum_note.id, trash=True)
                for edge in edges:
                    if edge.tail in members:
                        print('Restoring edge:', edge.id)
                        edge.ddate = None
                        client.post_edge(edge)

            # Restore review, meta-review and decision invitations
            invitation_ids = ','.join([
                f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Official_Review',
                f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Meta_Review',
                f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Decision',
                f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Revision',
                f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Desk_Reject',
                f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Withdraw',
                f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Supplementary_Material',
                f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Official_Comment',
                f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Public_Comment'
            ])
            all_paper_invitations = openreview.tools.iterget_invitations(client, ids=invitation_ids, expired=True)
            for invitation in all_paper_invitations:
                invitation.expdate = None
                client.post_invitation(invitation)

            client.add_members_to_group(CONFERENCE_ID + '/Authors', PAPER_AUTHORS_ID)
    else:
        forum_note.invitation = WITHDRAWN_SUBMISSION_ID
        original_note = None
        if forum_note.original:
            original_note = client.get_note(id=forum_note.original)

        if REVEAL_SUBMISSIONS_ON_WITHDRAW:
            forum_note.readers = ['everyone']
        else:
            forum_note.readers = committee

        bibtex = openreview.tools.generate_bibtex(
            note=original_note if original_note is not None else forum_note,
            venue_fullname=CONFERENCE_NAME,
            url_forum=forum_note.id,
            paper_status='rejected',
            year=CONFERENCE_YEAR,
            anonymous=not(REVEAL_AUTHORS_ON_WITHDRAW),
            baseurl='https://openreview.net')

        if original_note:
            if REVEAL_AUTHORS_ON_WITHDRAW:
                forum_note.content = {
                    '_bibtex': bibtex,
                    'venue': '',
                    'venueid': ''
                }
            else:
                forum_note.content = {
                    'authors': ['Anonymous'],
                    'authorids': ['Anonymous'],
                    '_bibtex': bibtex,
                    'venue': '',
                    'venueid': ''
                }
        else:
            forum_note.content['_bibtex'] = bibtex
            forum_note.content['venue'] = ''
            forum_note.content['venueid'] = ''

        for field in HIDE_FIELDS:
            forum_note.content[field] = ''

        forum_note = client.post_note(forum_note)

        # Delete any assignment and proposed assignment edges
        def delete_edges(invitation_id):
            try:
                client.delete_edges(invitation=invitation_id, head=forum_note.id, soft_delete=True)
            except openreview.OpenReviewException as ex:
                if ex.args[0].get('name') == 'NotFoundError':
                    print(f"Invitation {invitation_id} not found. Skipping.")
                else:
                    raise ex
        for role in CONFERENCE_ROLES:
            role_id = CONFERENCE_ID + '/' + role
            delete_edges(invitation_id=role_id + '/-/Proposed_Assignment')
            delete_edges(invitation_id=role_id + '/-/Assignment')

        # Expire review, meta-review and decision invitations
        invitation_ids = ','.join([
            f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Official_Review',
            f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Meta_Review',
            f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Decision',
            f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Revision',
            f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Supplementary_Material',
            f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Official_Comment',
            f'{CONFERENCE_ID}/Paper{str(forum_note.number)}/-/Public_Comment'
        ])
        all_paper_invitations = client.get_all_invitations(ids=invitation_ids)
        now = openreview.tools.datetime_millis(datetime.utcnow())
        for invitation in all_paper_invitations:
            invitation.expdate = now
            client.post_invitation(invitation)

        client.remove_members_from_group(CONFERENCE_ID + '/Authors', PAPER_AUTHORS_ID)
        client.remove_members_from_group(CONFERENCE_ID + '/Authors/Accepted', PAPER_AUTHORS_ID)

    # Mail Authors, Reviewers, ACs (if present) and PCs
    action = 'restored' if note.ddate else 'withdrawn'
    email_subject = '''{CONFERENCE_SHORT_NAME}: Paper #{paper_number} {action} by paper authors'''.format(
        CONFERENCE_SHORT_NAME=CONFERENCE_SHORT_NAME,
        paper_number=forum_note.number,
        action=action
    )
    email_body = '''The {CONFERENCE_SHORT_NAME} paper "{paper_title_or_num}" has been {action} by the paper authors.'''.format(
        CONFERENCE_SHORT_NAME=CONFERENCE_SHORT_NAME,
        paper_title_or_num=forum_note.content.get('title', '#'+str(forum_note.number)),
        action=action
    )

    if not EMAIL_PROGRAM_CHAIRS:
        committee.remove(PROGRAM_CHAIRS_ID)
    client.post_message(email_subject, committee, email_body)
