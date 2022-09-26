def process(client, edit, invitation):
    SHORT_PHRASE = ''
    PROGRAM_CHAIRS_ID = ''
    PAPER_AUTHORS_ID = ''
    PAPER_REVIEWERS_ID = ''
    PAPER_REVIEWERS_SUBMITTED_ID = ''
    PAPER_AREA_CHAIRS_ID = ''
    PAPER_SENIOR_AREA_CHAIRS_ID = ''

    submission = client.get_note(edit.note.forum)
    comment = client.get_note(edit.note.id)

    PAPER_AUTHORS_ID = PAPER_AUTHORS_ID.replace('{number}', str(submission.number))
    PAPER_REVIEWERS_ID = PAPER_REVIEWERS_ID.replace('{number}', str(submission.number))
    PAPER_REVIEWERS_SUBMITTED_ID = PAPER_REVIEWERS_SUBMITTED_ID.replace('{number}', str(submission.number))
    PAPER_AREA_CHAIRS_ID = PAPER_AREA_CHAIRS_ID.replace('{number}', str(submission.number))
    PAPER_SENIOR_AREA_CHAIRS_ID = PAPER_SENIOR_AREA_CHAIRS_ID.replace('{number}', str(submission.number))
    
    ignore_groups = comment.nonreaders if comment.nonreaders else []
    ignore_groups.append(edit.tauthor)

    signature = comment.signatures[0].split('/')[-1]
    pretty_signature = openreview.tools.pretty_id(signature)
    pretty_signature = 'An author' if pretty_signature == 'Authors' else pretty_signature

    content = f'''
    
Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

Comment title: {comment.content['title']['value']}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}'''

    if PROGRAM_CHAIRS_ID and (PROGRAM_CHAIRS_ID in comment.readers or 'everyone' in comment.readers):
        client.post_message(
            recipients=[PROGRAM_CHAIRS_ID],
            ignoreRecipients = ignore_groups,
            subject=f'''{SHORT_PHRASE} {pretty_signature} commented on a paper. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Program Chair.{content}'''
        )

    email_SAC = len(comment.readers)==3 and PAPER_SENIOR_AREA_CHAIRS_ID in comment.readers and PROGRAM_CHAIRS_ID in comment.readers
    if PAPER_SENIOR_AREA_CHAIRS_ID and email_SAC:
        client.post_message(
            recipients=[PAPER_SENIOR_AREA_CHAIRS_ID],
            ignoreRecipients = ignore_groups,
            subject=f'''{SHORT_PHRASE} {pretty_signature} commented on a paper in your area. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Senior Area Chair.{content}'''
        )

    if PAPER_AREA_CHAIRS_ID and (PAPER_AREA_CHAIRS_ID in comment.readers or 'everyone' in comment.readers):
        client.post_message(
            recipients=[PAPER_AREA_CHAIRS_ID],
            ignoreRecipients=ignore_groups,
            subject=f'''{SHORT_PHRASE} {pretty_signature} commented on a paper in your area. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Area Chair.{content}'''
        )

    if 'everyone' in comment.readers or PAPER_REVIEWERS_ID in comment.readers:
        client.post_message(
            recipients=[PAPER_REVIEWERS_ID],
            ignoreRecipients=ignore_groups,
            subject=f'''{SHORT_PHRASE} {pretty_signature} commented on a paper you are reviewing. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Reviewer.{content}'''
        )
    elif PAPER_REVIEWERS_SUBMITTED_ID in comment.readers:
        client.post_message(
            recipients=[PAPER_REVIEWERS_SUBMITTED_ID],
            ignoreRecipients=ignore_groups,
            subject=f'''{SHORT_PHRASE} {pretty_signature} commented on a paper you are reviewing. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Reviewer.{content}'''
        )
    else:
        anon_reviewers = [reader for reader in comment.readers if reader.find('Reviewer_') >=0]
        if anon_reviewers:
            client.post_message(
                recipients=anon_reviewers,
                ignoreRecipients=ignore_groups,
                subject=f'''{SHORT_PHRASE} {pretty_signature} commented on a paper you are reviewing. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
                message=f'''{pretty_signature} commented on a paper for which you are serving as Reviewer.{content}'''
            )

    #send email to author of comment
    client.post_message(
        recipients=[edit.tauthor],
        subject=f'''{SHORT_PHRASE} Your comment was received on Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
        message=f'''Your comment was received on a submission to {SHORT_PHRASE}.{content}'''
    )

    #send email to paper authors
    if PAPER_AUTHORS_ID in comment.readers or 'everyone' in comment.readers:
        client.post_message(
            recipients=submission.content['authorids']['value'],
            ignoreRecipients=ignore_groups,
            subject=f'''{SHORT_PHRASE} {pretty_signature} commented on your submission. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on your submission.{content}'''
        )
