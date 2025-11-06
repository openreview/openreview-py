def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    authors_name = domain.get_content_value('authors_name')
    submission_name = domain.get_content_value('submission_name')
    reviewers_name = domain.get_content_value('reviewers_name')
    area_chairs_name = domain.get_content_value('area_chairs_name')
    senior_area_chairs_name = domain.get_content_value('senior_area_chairs_name')
    reviewers_submitted_name = domain.get_content_value('reviewers_submitted_name')
    sender = domain.get_content_value('message_sender')

    parent_invitation = client.get_invitation(invitation.invitations[0])
    invitation_name = invitation.id.split('/-/')[-1]

    users_to_notify = parent_invitation.get_content_value('users_to_notify', [])
    email_pcs = 'program_chairs' in users_to_notify
    email_area_chairs = 'submission_area_chairs' in users_to_notify
    email_reviewers = 'submission_reviewers' in users_to_notify
    email_authors = 'submission_authors' in users_to_notify

    submission = client.get_note(edit.note.forum)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'
    paper_reviewers_id = f'{paper_group_id}/{reviewers_name}'
    paper_reviewers_submitted_id = f'{paper_reviewers_id}/{reviewers_submitted_name}'
    paper_area_chairs_id = f'{paper_group_id}/{area_chairs_name}'
    paper_senior_area_chairs_id = f'{paper_group_id}/{senior_area_chairs_name}'

    llm_pdf_response = client.get_note(edit.note.id)

    ## run process function for the first edit only
    review_edits = client.get_note_edits(note_id=llm_pdf_response.id, invitation=invitation.id, sort='tcdate:asc')
    if edit.id != review_edits[0].id:
        print('not first edit, exiting...')
        return

    capital_response_name = invitation_name.replace('_', ' ')
    llm_pdf_response_name = capital_response_name.lower()

    ignore_groups = llm_pdf_response.nonreaders if llm_pdf_response.nonreaders else []

    content = f'To view the {capital_response_name}, click here: https://openreview.net/forum?id={submission.id}&noteId={edit.note.id}'

    if email_pcs:
        client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            sender=sender,
            recipients=[domain.get_content_value('program_chairs_id')],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] An {capital_response_name} has been received on Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f'''We have received an {capital_response_name} on a submission to {short_name}.
            
{content}
'''
        )

    # always email tauthor
    client.post_message(
        invitation=meta_invitation_id,
        signature=venue_id,
        sender=sender,
        recipients=llm_pdf_response.signatures,
        replyTo=contact,
        subject=f'''[{short_name}] Your {invitation_name} has been received on your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
        message=f'''We have received an {capital_response_name} on a submission to {short_name}.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}        
        
{content}
''')                  

    if area_chairs_name and email_area_chairs and ('everyone' in llm_pdf_response.readers or paper_area_chairs_id in llm_pdf_response.readers):
        client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            sender=sender,
            recipients=[paper_area_chairs_id],
            ignoreRecipients=ignore_groups,
            replyTo=contact,
            subject=f'''[{short_name}] {capital_response_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f'''A submission to {short_name}, for which you are an official area chair, has received an {capital_response_name}.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )

    if email_reviewers:
        if 'everyone' in llm_pdf_response.readers or paper_reviewers_id in llm_pdf_response.readers:
            client.post_message(
                invitation=meta_invitation_id,
                signature=venue_id,
                sender=sender,
                recipients=[paper_reviewers_id],
                ignoreRecipients=ignore_groups,
                replyTo=contact,
                subject=f'''[{short_name}] {capital_response_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
                message=f'''A submission to {short_name}, for which you are a reviewer, has received an {capital_response_name}.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
            )
        elif paper_reviewers_submitted_id in llm_pdf_response.readers:
            print('emailing reviewers who have submitted')
            if openreview.tools.get_group(client, paper_reviewers_submitted_id):
                client.post_message(
                    invitation=meta_invitation_id,
                    signature=venue_id,
                    sender=sender,
                    recipients=[paper_reviewers_submitted_id],
                    ignoreRecipients=ignore_groups,
                    replyTo=contact,
                    subject=f'''[{short_name}] {capital_response_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
                    message=f'''A submission to {short_name}, for which you are a reviewer, has received an {capital_response_name}.

    Paper number: {submission.number}

    Paper title: {submission.content['title']['value']}

    {content}
    '''
                )

    paper_authors_id = f'{paper_group_id}/{authors_name}'
    if email_authors and 'everyone' in llm_pdf_response.readers or paper_authors_id in llm_pdf_response.readers:
        client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            sender=sender,
            recipients=[paper_authors_id],
            ignoreRecipients=ignore_groups,
            replyTo=contact,
            subject=f'''[{short_name}] {capital_response_name} posted to your submission - Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f'''Your submission to {short_name} has received an {capital_response_name}.

{content}
'''
        )

    #create children invitation if applicable
    openreview.tools.create_replyto_invitations(client, submission, llm_pdf_response)