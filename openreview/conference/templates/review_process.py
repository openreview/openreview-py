def process(client, note, invitation):

    CONFERENCE_ID = ''
    SHORT_PHRASE = ''
    OFFICIAL_REVIEW_NAME = ''
    AUTHORS_NAME = ''
    REVIEWERS_NAME = ''
    AREA_CHAIRS_NAME = ''
    PROGRAM_CHAIRS_ID = ''
    USE_AREA_CHAIRS = False
    ADD_SUBMITED = False

    forum = client.get_note(note.forum)

    capital_review_name = OFFICIAL_REVIEW_NAME.replace('_', ' ')
    review_name = capital_review_name.lower()

    AUTHORS_ID = CONFERENCE_ID + '/Paper' + str(forum.number) + '/' + AUTHORS_NAME
    REVIEWERS_ID = CONFERENCE_ID + '/Paper' + str(forum.number)  + '/' + REVIEWERS_NAME
    AREA_CHAIRS_ID = CONFERENCE_ID + '/Paper' + str(forum.number) + '/' + AREA_CHAIRS_NAME
    ignore_groups = note.nonreaders if note.nonreaders else []

    content = 'To view the ' + review_name + ', click here: https://openreview.net/forum?id=' + note.forum + '&noteId=' + note.id

    if PROGRAM_CHAIRS_ID:
        recipients = [PROGRAM_CHAIRS_ID]
        subject = '[' + SHORT_PHRASE + '] A ' + review_name + ' has been received on Paper number: ' + str(forum.number) + ', Paper title: "' + forum.content['title'] + '"'
        message = 'We have received a review on a submission to ' + SHORT_PHRASE + '.\n\n' + content
        client.post_message(subject=subject, recipients=recipients, message=message, ignoreRecipients=ignore_groups)

    recipients = note.signatures
    subject = '[' + SHORT_PHRASE + '] Your ' + review_name + ' has been received on your assigned Paper number: ' + str(forum.number)  + ', Paper title: "' + forum.content['title'] + '"'
    message = 'We have received your ' + review_name + ' on a submission to ' + SHORT_PHRASE + '.\n\nPaper number: ' + str(forum.number) + '\n\nPaper title: ' + forum.content['title'] + '\n\n' + content
    client.post_message(subject=subject, recipients=recipients, message=message)

    if USE_AREA_CHAIRS and ('everyone' in note.readers or AREA_CHAIRS_ID in note.readers):
        recipients = [AREA_CHAIRS_ID]
        subject = '[' + SHORT_PHRASE + '] ' + capital_review_name + ' posted to your assigned Paper number: ' + str(forum.number) + ', Paper title: "' + forum.content['title'] + '"'
        message = 'A submission to ' + SHORT_PHRASE + ', for which you are an official area chair, has received a review. \n\nPaper number: ' + str(forum.number) + '\n\nPaper title: ' + forum.content['title'] + '\n\n' + content
        client.post_message(subject=subject, recipients=recipients, message=message, ignoreRecipients=ignore_groups)

    reviewers_submitted = REVIEWERS_ID + '/Submitted'
    if 'everyone' in note.readers or REVIEWERS_ID in note.readers:
        recipients = [REVIEWERS_ID]
        subject = '[' + SHORT_PHRASE + '] ' + capital_review_name + ' posted to your assigned Paper number: ' + str(forum.number) + ', Paper title: "' + forum.content['title'] + '"'
        message = 'A submission to ' + SHORT_PHRASE + ', for which you are a reviewer, has received a review. \n\nPaper number: ' + str(forum.number) + '\n\nPaper title: ' + forum.content['title'] + '\n\n' + content
        client.post_message(subject=subject, recipients=recipients, message=message, ignoreRecipients=ignore_groups)
    elif reviewers_submitted in reviewers_submitted in note.readers:
        recipients = [reviewers_submitted]
        subject = '[' + SHORT_PHRASE + '] ' + capital_review_name + ' posted to your assigned Paper number: ' + str(forum.number) + ', Paper title: "' + forum.content['title'] + '"'
        message = 'A submission to ' + SHORT_PHRASE + ', for which you are a reviewer, has received a review. \n\nPaper number: ' + str(forum.number) + '\n\nPaper title: ' + forum.content['title'] + '\n\n' + content
        client.post_message(subject=subject, recipients=recipients, message=message, ignoreRecipients=ignore_groups)

    if 'everyone' in note.readers or AUTHORS_ID in note.readers:
        recipients = [AUTHORS_ID]
        subject = '[' + SHORT_PHRASE + '] ' + capital_review_name +' posted to your submission - Paper number: ' + str(forum.number) + ', Paper title: "' + forum.content['title'] + '"'
        message = 'Your submission to ' + SHORT_PHRASE + ' has received a review. \n\n' + content
        client.post_message(subject=subject, recipients=recipients, message=message, ignoreRecipients=ignore_groups)

    client.add_members_to_group(reviewers_submitted, note.signatures[0])
