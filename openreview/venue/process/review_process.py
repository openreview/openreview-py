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
    review_name = domain.get_content_value('review_name')
    sender = domain.get_content_value('message_sender')

    parent_invitation = client.get_invitation(invitation.invitations[0])

    users_to_notify = parent_invitation.get_content_value('users_to_notify', [])
    email_pcs = parent_invitation.get_content_value('email_program_chairs') or 'program_chairs' in users_to_notify
    email_area_chairs = parent_invitation.get_content_value('email_area_chairs') or 'submission_area_chairs' in users_to_notify
    email_reviewers = parent_invitation.get_content_value('email_reviewers') or 'submission_reviewers' in users_to_notify
    email_authors = parent_invitation.get_content_value('email_authors') or 'submission_authors' in users_to_notify

    # The roles this review invitation is wired to (set in set_review_invitation).
    # Falls back to the umbrella reviewers_name for back-compat with older invitations.
    reviewer_roles = parent_invitation.get_content_value('reviewer_roles', [reviewers_name])

    submission = client.get_note(edit.note.forum)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'
    paper_reviewers_ids = [f'{paper_group_id}/{role}' for role in reviewer_roles]
    paper_reviewers_submitted_ids = [f'{paper_reviewers_id}/{reviewers_submitted_name}' for paper_reviewers_id in paper_reviewers_ids]
    paper_area_chairs_id = f'{paper_group_id}/{area_chairs_name}'
    paper_senior_area_chairs_id = f'{paper_group_id}/{senior_area_chairs_name}'

    review = client.get_note(edit.note.id)

    ## run process function for the first edit only
    review_edits = client.get_note_edits(note_id=review.id, invitation=invitation.id, sort='tcdate:asc')
    if edit.id != review_edits[0].id:
        print('not first edit, exiting...')
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
                    'add': members
                }
            )
        )

    # Match the anon signature to its role by prefix: e.g.
    # 'venue/Submission1/Expert_Reviewer_XYCV' belongs to role 'Expert_Reviewers'.
    for role in reviewer_roles:
        anon_prefix = f'{paper_group_id}/{role[:-1] if role.endswith("s") else role}_'
        if review.signatures[0].startswith(anon_prefix):
            create_group(f'{paper_group_id}/{role}/{reviewers_submitted_name}', [review.signatures[0]])
            break

    capital_review_name = review_name.replace('_', ' ')
    review_name = capital_review_name.lower()

    ignore_groups = review.nonreaders if review.nonreaders else []
    ignore_groups.append(edit.tauthor)    

    content = f'To view the {review_name}, click here: https://openreview.net/forum?id={submission.id}&noteId={edit.note.id}'

    if email_pcs:
        client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            sender=sender,
            recipients=[domain.get_content_value('program_chairs_id')],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] A {review_name} has been received on Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f'''We have received a review on a submission to {short_name}.
            
{content}
'''
        )

    # always email tauthor
    client.post_message(
        invitation=meta_invitation_id,
        signature=venue_id,
        sender=sender,
        recipients=review.signatures,
        replyTo=contact,
        subject=f'''[{short_name}] Your {review_name} has been received on your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
        message=f'''We have received a review on a submission to {short_name}.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}        
        
{content}
''')                  

    if area_chairs_name and email_area_chairs and ('everyone' in review.readers or paper_area_chairs_id in review.readers):
        client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            sender=sender,
            recipients=[paper_area_chairs_id],
            ignoreRecipients=ignore_groups,
            replyTo=contact,
            subject=f'''[{short_name}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f'''A submission to {short_name}, for which you are an official area chair, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )

    if email_reviewers:
        role_recipients = [role_id for role_id in paper_reviewers_ids if role_id in review.readers]
        submitted_recipients = [submitted_id for submitted_id in paper_reviewers_submitted_ids if submitted_id in review.readers]
        if 'everyone' in review.readers or role_recipients:
            recipients = role_recipients if role_recipients else paper_reviewers_ids
            client.post_message(
                invitation=meta_invitation_id,
                signature=venue_id,
                sender=sender,
                recipients=recipients,
                ignoreRecipients=ignore_groups,
                replyTo=contact,
                subject=f'''[{short_name}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
                message=f'''A submission to {short_name}, for which you are a reviewer, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
            )
        elif submitted_recipients:
            print('emailing reviewers who have submitted')
            client.post_message(
                invitation=meta_invitation_id,
                signature=venue_id,
                sender=sender,
                recipients=submitted_recipients,
                ignoreRecipients=ignore_groups,
                replyTo=contact,
                subject=f'''[{short_name}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
                message=f'''A submission to {short_name}, for which you are a reviewer, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
            )

    paper_authors_id = f'{paper_group_id}/{authors_name}'
    if email_authors and 'everyone' in review.readers or paper_authors_id in review.readers:
        client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            sender=sender,
            recipients=[paper_authors_id],
            ignoreRecipients=ignore_groups,
            replyTo=contact,
            subject=f'''[{short_name}] {capital_review_name} posted to your submission - Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f'''Your submission to {short_name} has received a review.

{content}
'''
        )        
    

    #create children invitation if applicable
    openreview.tools.create_replyto_invitations(client, submission, review)