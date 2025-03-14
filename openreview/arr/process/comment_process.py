def process(client, edit, invitation):

    def get_thread_id(tree, comment_id, forum):
        thread_id = comment_id
        while tree[thread_id] != forum:
            thread_id = tree[thread_id]
        return thread_id

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    authors_name = domain.get_content_value('authors_name')
    submission_name = domain.get_content_value('submission_name')
    reviewers_name = domain.get_content_value('reviewers_name')
    reviewers_anon_name = domain.get_content_value('reviewers_anon_name')
    reviewers_submitted_name = domain.get_content_value('reviewers_submitted_name')
    sender = domain.get_content_value('message_sender')
    comment_threshold = domain.get_content_value('comment_notification_threshold')

    submission = client.get_note(edit.note.forum, details='replies')
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

    # Count comments between reviewer and authors
    replyto_tree = {
        reply['id']: reply['replyto'] for reply in submission.details['replies']
    }
    reply_id_to_thread = {
        reply['id']: get_thread_id(replyto_tree, reply['id'], submission.id) for reply in submission.details['replies']
    }
    comment_count = 0
    signed_by_reviewer = 'Reviewer' in signature
    signed_by_author = 'Authors' in signature

    official_comments = [r for r in submission.details['replies'] if r['invitations'][0].endswith('Official_Comment')]
    rebuttal_comments = [
        r for r in official_comments if any('Authors' in mem for mem in r['readers']) and any('Reviewer' in mem for mem in r['readers'])
    ]
    rebuttal_comments_in_thread = [
        r for r in rebuttal_comments if reply_id_to_thread[r['id']] == reply_id_to_thread[comment.id]
    ]

    for reply in rebuttal_comments_in_thread:
        readable_by_signature = any(comment.signatures[0] in r for r in reply['readers'])
        if signed_by_reviewer:
            readable_by_signature = readable_by_signature or any('Reviewers' in r for r in reply['readers'])

        comment_by_author = any('Authors' in r for r in reply['signatures'])
        comment_by_reviewer = any('Reviewer' in r for r in reply['signatures'])
        comment_by_signature = comment.signatures[0] == reply['signatures'][0]

        ## Comments are readable by both authors and at least 1 reviewer
        
        # if new comment by reviewer, and (reply from author is readable by reviewer) or reply written by reviewer
        if signed_by_reviewer and ((comment_by_author and readable_by_signature) or comment_by_signature):
            comment_count += 1
        # if new comment by author and reply written by author, or reply written by reviewer
        elif signed_by_author and (comment_by_signature or comment_by_reviewer):
            comment_count += 1

    print(f"{signature} -> {comment_count}")

    content = f'''
    
Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}'''

    if comment_threshold is None or (signed_by_author and comment_count <= comment_threshold) or (signed_by_reviewer and comment_count <= comment_threshold) or not (signed_by_author or signed_by_reviewer):
        program_chairs_id = domain.get_content_value('program_chairs_id')
        minimum_number_of_readers = 3 if domain.get_content_value('senior_area_chairs_name') else 2
        email_PC = domain.get_content_value('comment_email_pcs') or (domain.get_content_value('direct_comment_email_pcs') and len(comment.readers) == minimum_number_of_readers)
        if email_PC and (program_chairs_id in comment.readers or 'everyone' in comment.readers):
            client.post_message(
                invitation=meta_invitation_id,
                recipients=[program_chairs_id],
                ignoreRecipients = ignore_groups,
                subject=f'''[{short_name}] {pretty_signature} commented on a paper. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
                message=f'''{pretty_signature} commented on a paper for which you are serving as Program Chair.{content}''',
                signature=venue_id,
                sender=sender
            )

        senior_area_chairs_name = domain.get_content_value('senior_area_chairs_name')
        paper_senior_area_chairs_id = f'{paper_group_id}/{senior_area_chairs_name}'
        paper_senior_area_chairs_group = openreview.tools.get_group(client, paper_senior_area_chairs_id)

        email_SAC = ((len(comment.readers)==3 and paper_senior_area_chairs_id in comment.readers and program_chairs_id in comment.readers) or domain.get_content_value('comment_email_sacs'))
        if paper_senior_area_chairs_group and senior_area_chairs_name and email_SAC:
            client.post_message(
                invitation=meta_invitation_id,
                recipients=[paper_senior_area_chairs_id],
                ignoreRecipients = ignore_groups,
                subject=f'''[{short_name}] {pretty_signature} commented on a paper in your area. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
                message=f'''{pretty_signature} commented on a paper for which you are serving as Senior Area Chair.{content}''',
                replyTo=contact,
                signature=venue_id,
                sender=sender
            )

        area_chairs_name = domain.get_content_value('area_chairs_name')
        paper_area_chairs_id = f'{paper_group_id}/{area_chairs_name}'
        paper_area_chairs_group = openreview.tools.get_group(client, paper_area_chairs_id)
        if paper_area_chairs_group and area_chairs_name and (paper_area_chairs_id in comment.readers or 'everyone' in comment.readers):
            client.post_message(
                invitation=meta_invitation_id,
                recipients=[paper_area_chairs_id],
                ignoreRecipients=ignore_groups,
                subject=f'''[{short_name}] {pretty_signature} commented on a paper in your area. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
                message=f'''{pretty_signature} commented on a paper for which you are serving as Area Chair.{content}''',
                replyTo=contact,
                signature=venue_id,
                sender=sender
            )

    paper_reviewers_id = f'{paper_group_id}/{reviewers_name}'
    paper_reviewers_group = openreview.tools.get_group(client, paper_reviewers_id)
    paper_reviewers_submitted_id = f'{paper_reviewers_id}/{reviewers_submitted_name}'
    paper_reviewers_submitted_group = openreview.tools.get_group(client, paper_reviewers_submitted_id)
    if paper_reviewers_group and ('everyone' in comment.readers or paper_reviewers_id in comment.readers):
        client.post_message(
            invitation=meta_invitation_id,
            recipients=[paper_reviewers_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] {pretty_signature} commented on a paper you are reviewing. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Reviewer.{content}''',
            replyTo=contact,
            signature=venue_id,
            sender=sender
        )
    elif paper_reviewers_submitted_group and paper_reviewers_submitted_id in comment.readers:
        client.post_message(
            invitation=meta_invitation_id,
            recipients=[paper_reviewers_submitted_id],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] {pretty_signature} commented on a paper you are reviewing. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on a paper for which you are serving as Reviewer.{content}''',
            replyTo=contact,
            signature=venue_id,
            sender=sender
        )
    else:
        anon_reviewers = [reader for reader in comment.readers if reader.find(reviewers_anon_name) >=0]
        anon_reviewers_group = client.get_groups(prefix=f'{paper_group_id}/{reviewers_anon_name}.*')
        if anon_reviewers_group and anon_reviewers:
            client.post_message(
                invitation=meta_invitation_id,
                recipients=anon_reviewers,
                ignoreRecipients=ignore_groups,
                subject=f'''[{short_name}] {pretty_signature} commented on a paper you are reviewing. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
                message=f'''{pretty_signature} commented on a paper for which you are serving as Reviewer.{content}''',
                replyTo=contact,
                signature=venue_id,
                sender=sender
            )

    #send email to author of comment
    client.post_message(
        invitation=meta_invitation_id,
        recipients=[edit.tauthor] if edit.tauthor != 'OpenReview.net' else [],
        subject=f'''[{short_name}] Your comment was received on Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
        message=f'''Your comment was received on a submission to {short_name}.{content}''',
        replyTo=contact,
        signature=venue_id,
        sender=sender
    )

    #send email to paper authors
    paper_authors_id = f'{paper_group_id}/{authors_name}'
    if paper_authors_id in comment.readers or 'everyone' in comment.readers:
        client.post_message(
            invitation=meta_invitation_id,
            recipients=submission.content['authorids']['value'],
            ignoreRecipients=ignore_groups,
            subject=f'''[{short_name}] {pretty_signature} commented on your submission. Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''{pretty_signature} commented on your submission.{content}''',
            replyTo=contact,
            signature=venue_id,
            sender=sender
        )
