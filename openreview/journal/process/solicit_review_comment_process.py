def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    comment = client.get_note(edit.note.id)

    ## On update or delete return
    if comment.tcdate != comment.tmdate:
        return

    submission = client.get_note(comment.forum)

    ignore_groups = comment.nonreaders if comment.nonreaders else []
    ignore_groups.extend([journal.get_editors_in_chief_id(), edit.tauthor])

    subject = f'''[{journal.short_name}] Comment posted on submission {submission.number}: "{submission.content['title']['value']}" pertaining to volunteer reviewing'''

    tauthor_content = f'''Your comment pertaining to volunteer reviewing on a submission has been posted.

Submission: {submission.content['title']['value']}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}'''
    
    content = f'''A comment pertaining to volunteer reviewing on a submission has been posted.

Submission: {submission.content['title']['value']}

Comment: {comment.content['comment']['value']}

To view the comment, click here: https://openreview.net/forum?id={submission.id}&noteId={comment.id}'''
        
    # send email to tauthor
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=comment.signatures,
        subject=subject,
        message=tauthor_content,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )

    # send email to other reader
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=comment.readers,
        ignoreRecipients=ignore_groups,
        subject=subject,
        message=content,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )