def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    authors_name = domain.get_content_value('authors_name')
    submission_name = domain.get_content_value('submission_name')
    reviewers_name = domain.get_content_value('reviewers_name')
    reviewers_anon_name = domain.get_content_value('reviewers_anon_name')
    reviewers_submitted_name = domain.get_content_value('reviewers_submitted_name')

    submission = client.get_note(edit.note.forum)
    comment = client.get_note(edit.note.id)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'

    ### TODO: Fix this, we should notify the use when the review is updated
    if comment.tcdate != comment.tmdate:
        return    

    ignore_groups = comment.nonreaders if comment.nonreaders else []
    ignore_groups.append(edit.tauthor)

    signature = comment.signatures[0].split('/')[-1]
    pretty_signature = openreview.tools.pretty_id(signature)
    pretty_signature = 'An author' if pretty_signature == 'Authors' else pretty_signature

    content = f'''
    
Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}'''

    program_chairs_id = domain.get_content_value('program_chairs_id')
    if domain.get_content_value('comment_email_pcs') and (program_chairs_id in comment.readers or 'everyone' in comment.readers):
        client.post_message(
            recipients=[program_chairs_id],
            ignoreRecipients = ignore_groups,
            subject=f'''[{short_name}] {pretty_signature} commented on a paper. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Program Chair.{content}'''
        )

    senior_area_chairs_name = domain.get_content_value('senior_area_chairs_name')
    paper_senior_area_chairs_id = f'{paper_group_id}/{senior_area_chairs_name}'
    paper_senior_area_chairs_group = openreview.tools.get_group(client, paper_senior_area_chairs_id)
    email_SAC = len(comment.readers)==3 and paper_senior_area_chairs_id in comment.readers and program_chairs_id in comment.readers
    if paper_senior_area_chairs_group and senior_area_chairs_name and email_SAC:
        client.post_message(
            recipients=[paper_senior_area_chairs_id],
            ignoreRecipients = ignore_groups,
            subject=f'''[{short_name}] {pretty_signature} commented on a paper in your area. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Senior Area Chair.{content}''',
            replyTo=contact
        )

    area_chairs_name = domain.get_content_value('area_chairs_name')
    paper_area_chairs_id = f'{paper_group_id}/{area_chairs_name}'
    paper_area_chairs_group = openreview.tools.get_group(client, paper_area_chairs_id)
    if paper_area_chairs_group and area_chairs_name and (paper_area_chairs_id in comment.readers or 'everyone' in comment.readers):
        client.post_message(
            recipients=[paper_area_chairs_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] {pretty_signature} commented on a paper in your area. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Area Chair.{content}''',
            replyTo=contact
        )

    paper_reviewers_id = f'{paper_group_id}/{reviewers_name}'
    paper_reviewers_group = openreview.tools.get_group(client, paper_reviewers_id)
    paper_reviewers_submitted_id = f'{paper_reviewers_id}/{reviewers_submitted_name}'
    paper_reviewers_submitted_group = openreview.tools.get_group(client, paper_reviewers_submitted_id)
    if paper_reviewers_group and ('everyone' in comment.readers or paper_reviewers_id in comment.readers):
        client.post_message(
            recipients=[paper_reviewers_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] {pretty_signature} commented on a paper you are reviewing. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Reviewer.{content}''',
            replyTo=contact
        )
    elif paper_reviewers_submitted_group and paper_reviewers_submitted_id in comment.readers:
        client.post_message(
            recipients=[paper_reviewers_submitted_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] {pretty_signature} commented on a paper you are reviewing. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Reviewer.{content}''',
            replyTo=contact
        )
    else:
        anon_reviewers = [reader for reader in comment.readers if reader.find(reviewers_anon_name) >=0]
        anon_reviewers_group = client.get_groups(prefix=f'{paper_group_id}/{reviewers_anon_name}.*')
        if anon_reviewers_group and anon_reviewers:
            client.post_message(
                recipients=anon_reviewers,
                ignoreRecipients=ignore_groups,
                subject=f'''[{short_name}] {pretty_signature} commented on a paper you are reviewing. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
                message=f'''{pretty_signature} commented on a paper for which you are serving as Reviewer.{content}''',
                replyTo=contact
            )

    #send email to author of comment
    client.post_message(
        recipients=[edit.tauthor] if edit.tauthor != 'OpenReview.net' else [],
        subject=f'''[{short_name}] Your comment was received on Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
        message=f'''Your comment was received on a submission to {short_name}.{content}''',
        replyTo=contact
    )

    #send email to paper authors
    paper_authors_id = f'{paper_group_id}/{authors_name}'
    if paper_authors_id in comment.readers or 'everyone' in comment.readers:
        client.post_message(
            recipients=submission.content['authorids']['value'],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] {pretty_signature} commented on your submission. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on your submission.{content}''',
            replyTo=contact
        )
