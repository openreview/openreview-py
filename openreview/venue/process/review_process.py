def process(client, edit, invitation):
    SHORT_PHRASE = ''
    OFFICIAL_REVIEW_NAME = ''
    PROGRAM_CHAIRS_ID = ''
    USE_AREA_CHAIRS = False
    PAPER_AUTHORS_ID = ''
    PAPER_REVIEWERS_ID = ''
    PAPER_REVIEWERS_SUBMITTED_ID = ''
    PAPER_AREA_CHAIRS_ID = ''

    submission = client.get_note(edit.note.forum)
    review = client.get_note(edit.note.id)
    PAPER_REVIEWERS_ID = PAPER_REVIEWERS_ID.replace('{number}', str(submission.number))
    PAPER_REVIEWERS_SUBMITTED_ID = PAPER_REVIEWERS_SUBMITTED_ID.replace('{number}', str(submission.number))
    PAPER_AREA_CHAIRS_ID = PAPER_AREA_CHAIRS_ID.replace('{number}', str(submission.number))


    capital_review_name = OFFICIAL_REVIEW_NAME.replace('_', ' ')
    review_name = capital_review_name.lower()

    content = f'To view the {review_name}, click here: https://openreview.net/forum?id={submission.id}&noteId={edit.note.id}'

    if PROGRAM_CHAIRS_ID:
        client.post_message(
            recipients=[PROGRAM_CHAIRS_ID],
            subject=f'''[{SHORT_PHRASE}] A {review_name} has been received on Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''We have received a review on a submission to {SHORT_PHRASE}.
            
{content}
'''
        )        

    if USE_AREA_CHAIRS and 'everyone' in review.readers or PAPER_AREA_CHAIRS_ID in review.readers:
        client.post_message(
            recipients=[PAPER_AREA_CHAIRS_ID],
            subject=f'''[{SHORT_PHRASE}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''A submission to {SHORT_PHRASE}, for which you are an official area chair, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )

    if 'everyone' in review.readers or PAPER_REVIEWERS_ID in review.readers:
        client.post_message(
            recipients=[PAPER_REVIEWERS_ID],
            subject=f'''[{SHORT_PHRASE}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''A submission to {SHORT_PHRASE}, for which you are a reviewer, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )
    elif PAPER_REVIEWERS_SUBMITTED_ID in review.readers:
        client.post_message(
            recipients=[PAPER_REVIEWERS_SUBMITTED_ID],
            subject=f'''[{SHORT_PHRASE}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''A submission to {SHORT_PHRASE}, for which you are a reviewer, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )

    if 'everyone' in  review.readers or PAPER_AUTHORS_ID in review.readers:
        client.post_message(
            recipients=[PAPER_AUTHORS_ID],
            subject=f'''[{SHORT_PHRASE}] {capital_review_name} posted to your submission - Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''Your submission to {SHORT_PHRASE} has received a review.

{content}
'''
        )

    if PAPER_REVIEWERS_SUBMITTED_ID:
        client.add_members_to_group(PAPER_REVIEWERS_SUBMITTED_ID, review.signatures[0])
    

