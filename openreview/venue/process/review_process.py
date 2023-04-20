def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_name = domain.get_content_value('subtitle')
    authors_name = domain.get_content_value('authors_name')
    submission_name = domain.get_content_value('submission_name')
    reviewers_name = domain.get_content_value('reviewers_name')
    area_chairs_name = domain.get_content_value('area_chairs_name')
    senior_area_chairs_name = domain.get_content_value('senior_area_chairs_name')
    reviewers_submitted_name = domain.get_content_value('reviewers_submitted_name')
    review_name = domain.get_content_value('review_name')

    submission = client.get_note(edit.note.forum)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'
    paper_reviewers_id = f'{paper_group_id}/{reviewers_name}'
    paper_reviewers_submitted_id = f'{paper_reviewers_id}/{reviewers_submitted_name}'
    paper_area_chairs_id = f'{paper_group_id}/{area_chairs_name}'
    paper_senior_area_chairs_id = f'{paper_group_id}/{senior_area_chairs_name}'        

    review = client.get_note(edit.note.id)

    ### TODO: Fix this, we should notify the use when the review is updated
    if review.tcdate != review.tmdate:
        return
    
    def create_group(group_id, members=[]):
        readers=[venue_id]
        if senior_area_chairs_name:
            readers.append(paper_senior_area_chairs_id)
        if area_chairs_name:
            readers.append(paper_area_chairs_id)
        readers.append(group_id)
        client.post_group_edit(
            invitation=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            group=openreview.api.Group(id=group_id,
                readers=readers,
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id],
                members={
                    'append': members
                }
            )
        )

    capital_review_name = review_name.replace('_', ' ')
    review_name = capital_review_name.lower()

    ignore_groups = review.nonreaders if review.nonreaders else []
    ignore_groups.append(edit.tauthor)    

    content = f'To view the {review_name}, click here: https://openreview.net/forum?id={submission.id}&noteId={edit.note.id}'

    if domain.get_content_value('review_email_pcs'):
        client.post_message(
            recipients=[domain.get_content_value('program_chairs_id')],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] A {review_name} has been received on Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''We have received a review on a submission to {short_name}.
            
{content}
'''
        )

    client.post_message(
        recipients=review.signatures,
        subject=f'''[{short_name}] Your {review_name} has been received on your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
        message=f''''We have received a review on a submission to {short_name}.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}        
        
{content}
''')                  

    if area_chairs_name and ('everyone' in review.readers or paper_area_chairs_id in review.readers):
        client.post_message(
            recipients=[paper_area_chairs_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''A submission to {short_name}, for which you are an official area chair, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )

    create_group(paper_reviewers_submitted_id, [review.signatures[0]])
    if 'everyone' in review.readers or paper_reviewers_id in review.readers:
        client.post_message(
            recipients=[paper_reviewers_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''A submission to {short_name}, for which you are a reviewer, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )
    elif paper_reviewers_submitted_id in review.readers:
        client.post_message(
            recipients=[paper_reviewers_submitted_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''A submission to {short_name}, for which you are a reviewer, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )

    paper_authors_id = f'{paper_group_id}/{authors_name}'
    if 'everyone' in  review.readers or paper_authors_id in review.readers:
        client.post_message(
            recipients=[paper_authors_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] {capital_review_name} posted to your submission - Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''Your submission to {short_name} has received a review.

{content}
'''
        )        
    

    #create children invitation if applicable
    venue_invitations = [i for i in client.get_all_invitations(prefix=venue_id + '/-/', type='invitation') if i.is_active()]

    for invitation in venue_invitations:
        print('processing invitation: ', invitation.id)
        review_reply = invitation.content.get('reply_to', {}).get('value', False) if invitation.content else False
        content_keys = invitation.edit.get('content', {}).keys()
        if 'reviews' == review_reply and 'replytoSignatures' in content_keys and 'replyto' in content_keys and len(content_keys) == 4:
            print('create invitation: ', invitation.id)
            client.post_invitation_edit(invitations=invitation.id,
                content={
                    'noteId': { 'value': review.forum },
                    'noteNumber': { 'value': submission.number },
                    'replytoSignatures': { 'value': review.signatures[0] },
                    'replyto': { 'value': review.id }
                },
                invitation=openreview.api.Invitation()
            )