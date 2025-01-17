def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    submission_name = domain.get_content_value('submission_name')
    program_chairs_id = domain.get_content_value('program_chairs_id')
    email_pcs = domain.get_content_value('rebuttal_email_pcs')
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
    if area_chairs_name and (paper_area_chairs_id in rebuttal.readers or 'everyone' in rebuttal.readers):
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

    
