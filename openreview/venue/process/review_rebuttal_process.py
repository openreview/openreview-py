def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    submission_name = domain.get_content_value('submission_name')
    program_chairs_id = domain.get_content_value('program_chairs_id')
    super_invitation = client.get_invitation(invitation.invitations[0])
    email_pcs = super_invitation.get_content_value('email_program_chairs', super_invitation.get_content_value('rebuttal_email_pcs', False))
    email_acs = super_invitation.get_content_value('email_area_chairs', super_invitation.get_content_value('rebuttal_email_acs', False))
    sender = domain.get_content_value('message_sender')
    
    submission = client.get_note(edit.note.forum)
    rebuttal = client.get_note(edit.note.id)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'
    ignore_groups = [edit.tauthor]

    if rebuttal.tcdate != rebuttal.tmdate:
        return   

    action = 'posted'

    content = f'''To view the rebuttal, click here: https://openreview.net/forum?id={submission.forum}&noteId={rebuttal.id}'''

    author_message = f'''An author rebuttal has been {action} on your submission to {short_name}.

Submission Number: {submission.number}

Title: {submission.content['title']['value']} 

{content}'''

    #send email to author of comment
    client.post_message(
        invitation=meta_invitation_id,
        recipients=[edit.tauthor] if edit.tauthor != 'OpenReview.net' else [],
        subject=f'''[{short_name}] Your author rebuttal was {action} on Submission Number: {submission.number}, Submission Title: "{submission.content['title']['value']}"''',
        message=author_message,
        replyTo=contact,
        signature=venue_id,
        sender=sender
    )

    #send email to paper authors
    client.post_message(
        invitation=meta_invitation_id,
        recipients=submission.content['authorids']['value'],
        ignoreRecipients=ignore_groups,
        subject=f'''[{short_name}] An author rebuttal was {action} on Submission Number: {submission.number}, Submission Title: "{submission.content['title']['value']}"''',
        message=author_message,
        replyTo=contact,
        signature=venue_id,
        sender=sender
    )

    if email_pcs:
        client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            sender=sender,
            recipients=[program_chairs_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] An author rebuttal was {action} on Submission Number: {submission.number}, Submission Title: "{submission.content['title']['value']}"''',
            message=f'''An author rebuttal was {action} on a submission to {short_name}.
            
Submission Number: {submission.number}

Title: {submission.content['title']['value']}
    
{content}'''
        )

    # email ACs
    area_chairs_name = domain.get_content_value('area_chairs_name')
    paper_area_chairs_id = f'{paper_group_id}/{area_chairs_name}'
    if email_acs and area_chairs_name and (paper_area_chairs_id in rebuttal.readers or 'everyone' in rebuttal.readers):
        client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            sender=sender,
            recipients=[paper_area_chairs_id],
            ignoreRecipients=ignore_groups,
            replyTo=contact,
            subject=f'''[{short_name}] An author rebuttal was {action} on Submission Number: {submission.number}, Submission Title: "{submission.content['title']['value']}"''',
            message=f'''An author rebuttal was {action} on a submission for which you are serving as Area Chair.

Submission Number: {submission.number}

Title: {submission.content['title']['value']}

{content}'''
        )

    reviewer_subject = f'''[{short_name}] An author rebuttal was {action} on Submission Number: {submission.number}, Submission Title: "{submission.content['title']['value']}"'''
    reviewer_message = f'''An author rebuttal was {action} on a submission for which you are serving as Reviewer.

Submission Number: {submission.number}

Title: {submission.content['title']['value']}

{content}'''

    # email reviewers
    reviewers_name = domain.get_content_value('reviewers_name')
    paper_reviewers_id = f'{paper_group_id}/{reviewers_name}'
    reviewers_submitted_name = domain.get_content_value('reviewers_submitted_name')
    paper_reviewers_submitted_id = f'{paper_reviewers_id}/{reviewers_submitted_name}'
    if 'everyone' in rebuttal.readers or paper_reviewers_id in rebuttal.readers:
        client.post_message(
            invitation=meta_invitation_id,
            recipients=[paper_reviewers_id],
            ignoreRecipients=ignore_groups,
            subject=reviewer_subject,
            message=reviewer_message,
            replyTo=contact,
            signature=venue_id,
            sender=sender
        )
    elif paper_reviewers_submitted_id in rebuttal.readers:
        client.post_message(
            invitation=meta_invitation_id,
            recipients=[paper_reviewers_submitted_id],
            ignoreRecipients=ignore_groups,
            subject=reviewer_subject,
            message=reviewer_message,
            replyTo=contact,
            signature=venue_id,
            sender=sender
        )

    #create children invitation if applicable
    venue_invitations = [i for i in client.get_all_invitations(prefix=venue_id + '/-/', type='invitation') if i.is_active()]

    for invitation in venue_invitations:
        print('processing invitation: ', invitation.id)
        review_reply = invitation.content.get('reply_to', {}).get('value', False) if invitation.content else False
        content_keys = invitation.edit.get('content', {}).keys()
        if 'rebuttals' == review_reply and 'replyto' in content_keys and len(content_keys) >= 4:
            print('create invitation: ', invitation.id)
            content  = {
                'noteId': { 'value': rebuttal.forum },
                'noteNumber': { 'value': submission.number },
                'replyto': { 'value': rebuttal.id }
            }
            if 'replytoSignatures' in content_keys:
                content['replytoSignatures'] = { 'value': rebuttal.signatures[0] }
            if 'replyNumber' in content_keys:
                content['replyNumber'] = { 'value': rebuttal.number }
            if 'invitationPrefix' in content_keys:
                content['invitationPrefix'] = { 'value': rebuttal.invitations[0].replace('/-/', '/') + str(rebuttal.number) }
            if 'replytoReplytoSignatures' in content_keys:
                content['replytoReplytoSignatures'] = { 'value': client.get_note(rebuttal.replyto).signatures[0] } 
            client.post_invitation_edit(invitations=invitation.id,
                content=content,
                invitation=openreview.api.Invitation()
            )        

    
