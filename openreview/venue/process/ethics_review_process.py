def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    ethics_chairs_name = domain.get_content_value('ethics_chairs_name')
    ethics_chairs_id = domain.get_content_value('ethics_chairs_id')
    authors_name = domain.get_content_value('authors_name')
    submission_name = domain.get_content_value('submission_name')
    ethics_reviewers_name = domain.get_content_value('ethics_reviewers_name')
    sender = domain.get_content_value('message_sender')
    contact = domain.get_content_value('contact')
    short_name = domain.get_content_value('subtitle')
    ethics_review_name = domain.get_content_value('ethics_review_name')

    submission = client.get_note(edit.note.forum)
    paper_group_id = f'{venue_id}/{submission_name}{submission.number}'
    paper_authors_id = f'{paper_group_id}/{authors_name}'
    paper_reviewers_submitted_id = f'{paper_group_id}/{ethics_reviewers_name}/Submitted'
    
    ethics_review = client.get_note(edit.note.id)

    def create_group(group_id, members=[]):
        readers=[venue_id]
        if ethics_chairs_name:
            readers.append(ethics_chairs_id)
        client.post_group_edit(
            invitation=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            group=openreview.api.Group(id=group_id,
                readers=readers,
                nonreaders=[paper_authors_id],
                writers=readers,
                signatures=[venue_id],
                signatories=[venue_id],
                members={
                    'append': members
                }
            )
        )

    create_group(paper_reviewers_submitted_id, [ethics_review.signatures[0]])

    capital_ethics_review_name = ethics_review_name.replace('_', ' ')
    ethics_review_name = capital_ethics_review_name.lower()

    ignore_groups = ethics_review.nonreaders if ethics_review.nonreaders else []
    ignore_groups.append(edit.tauthor)  

    content = f'To view the {ethics_review_name}, click here: https://openreview.net/forum?id={submission.id}&noteId={edit.note.id}'

    # email tauthor
    client.post_message(
        invitation=meta_invitation_id,
        signature=venue_id,
        sender=sender,
        recipients=ethics_review.signatures,
        replyTo=contact,
        subject=f'''[{short_name}] Your {ethics_review_name} has been received on your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
        message=f''''We have received an ethics review on a submission to {short_name}.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}        
        
{content}
''')
    
    # email ethics chairs
    client.post_message(
            invitation=meta_invitation_id,
            signature=venue_id,
            sender=sender,
            recipients=[ethics_chairs_id],
            ignoreRecipients=ignore_groups,
            replyTo=contact,
            subject=f'''[{short_name}] {capital_ethics_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''A submission to {short_name}, for which you are an official ethics chair, has received an ethics review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )