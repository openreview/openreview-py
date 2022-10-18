def process_update(client, note, invitation, existing_note):

    CONFERENCE_ID = ''
    SHORT_PHRASE = ''
    PROGRAM_CHAIRS_ID = ''
    AREA_CHAIRS_ID = ''
    OFFICIAL_REVIEW_NAME = ''
    CREATE_GROUPS = False
    ANON_IDS = False
    DEANONYMIZERS = []

    author_subject = f'''{SHORT_PHRASE} has received your submission titled {note.content['title']}'''
    note_abstract = f'''\n\nAbstract: {note.content['abstract']}''' if 'abstract' in note.content else ''
    action = 'delete' if note.ddate else 'posted'
    if existing_note:
        action = 'updated'
    author_message = f'''Your submission to {SHORT_PHRASE} has been {action}.

Submission Number: {note.number} 

Title: {note.content['title']} {note_abstract} 

To view your submission, click here: https://openreview.net/forum?id={note.forum}'''

    SUBMISSION_EMAIL = ''

    if SUBMISSION_EMAIL:
        author_message = SUBMISSION_EMAIL

    if CREATE_GROUPS and action == 'posted':
        committee = [CONFERENCE_ID]
        if (AREA_CHAIRS_ID):
            committee.append(AREA_CHAIRS_ID)
        client.post_group(openreview.Group(
            id=f'{CONFERENCE_ID}/Paper{note.number}',
            signatures=[CONFERENCE_ID],
            writers=committee,
            members=[],
            readers=committee,
            signatories=committee
        ))

        members = note.content['authorids']
        members.append(note.signatures[0])
        authors_id=f'{CONFERENCE_ID}/Paper{note.number}/Authors'
        client.post_group(openreview.Group(
            id=authors_id,
            signatures=[CONFERENCE_ID],
            writers=[CONFERENCE_ID],
            members=members,
            readers=[CONFERENCE_ID, authors_id],
            signatories=[CONFERENCE_ID, authors_id]
        ))

        reviewers_id=f'{CONFERENCE_ID}/Paper{note.number}/Reviewers'
        readers = committee
        readers.append(reviewers_id)
        client.post_group(openreview.Group(
            id=reviewers_id,
            signatures=[CONFERENCE_ID],
            writers=committee,
            members=[],
            readers=readers,
            signatories=committee,
            nonreaders = [authors_id],
            anonids= ANON_IDS,
            deanonymizers = [group.replace('{number}', str(note.number)) for group in DEANONYMIZERS]
        ))

        reviewers_submitted_id=f'{CONFERENCE_ID}/Paper{note.number}/Reviewers/Submitted'
        readers = committee
        readers.append(reviewers_submitted_id)
        client.post_group(openreview.Group(
            id=reviewers_submitted_id,
            signatures=[CONFERENCE_ID],
            writers=committee,
            members=[],
            readers=readers,
            signatories=committee,
            nonreaders = [authors_id]
        ))

        if OFFICIAL_REVIEW_NAME:
            client.post_invitation(openreview.Invitation(
                id=f'{CONFERENCE_ID}/Paper{note.number}/-/{OFFICIAL_REVIEW_NAME}',
                super=f'{CONFERENCE_ID}/-/{OFFICIAL_REVIEW_NAME}',
                signatures=[CONFERENCE_ID],
                writers=[CONFERENCE_ID],
                invitees = [reviewers_id],
                reply={
                    'forum': note.id,
                    'replyto': note.id,
                    'readers': {
                        'values': ['everyone'],
                        'description': "User groups that should be able to read this review."
                    },
                    'writers': {
                        'values-regex': f'{CONFERENCE_ID}/Paper{note.number}/Reviewer_.*' if ANON_IDS else f'{CONFERENCE_ID}/Paper{note.number}/AnonReviewer.*'
                    },
                    'signatures': {
                        'values-regex': f'{CONFERENCE_ID}/Paper{note.number}/Reviewer_.*' if ANON_IDS else f'{CONFERENCE_ID}/Paper{note.number}/AnonReviewer.*'
                    }
                }
            ))


    #send tauthor email
    client.post_message(
        subject=author_subject,
        message=author_message,
        recipients=[note.tauthor]
    )

    #send co-author emails
    if ('authorids' in note.content and len(note.content['authorids'])):
        author_message += f'''\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at {note.tauthor}'''
        client.post_message(
            subject=author_subject,
            message=author_message,
            recipients=note.content['authorids'],
            ignoreRecipients=[note.tauthor]
        )

    #send PC emails
    if PROGRAM_CHAIRS_ID and action == 'posted':
        client.post_message(
            subject=f'''{SHORT_PHRASE} has received a new submission titled {note.content['title']}''',
            message=f'''A submission to {SHORT_PHRASE} has been posted.
            
Submission Number: {note.number}
Title: {note.content['title']} {note_abstract}
            
To view the submission, click here: https://openreview.net/forum?id={note.forum}''',
            recipients=[PROGRAM_CHAIRS_ID]
        )