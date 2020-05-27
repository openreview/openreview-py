def process_update(client, note, invitation, existing_note):

    article = client.get_note(note.forum)

    support = 'OpenReview.net/Support'
    article_group_id = invitation.id.split('/-/')[0]
    editors_group_id = '{}/Editors'.format(article_group_id)
    reviewers_group_id = '{}/Reviewers'.format(article_group_id)
    submission = client.get_note(note.forum)

    action = 'posted'
    if existing_note:
        action = 'deleted' if note.ddate else 'updated'


    client.post_message(subject='[Agora/COVID-19] Your revision has been {action} on your article titled "{title}"'.format(action=action, title=submission.content['title']),
        recipients=note.signatures,
        message='''Your revision has been {action} to your article titled "{title}".

The revision can be viewed on OpenReview here: https://openreview.net/revisions?id={forum}'''.format(action=action, title=submission.content['title'], forum=note.forum),
        ignoreRecipients=None,
        sender=None
    )

    client.post_message(subject='[Agora/COVID-19] A revision has been {action} on the article titled "{title}"'.format(action=action, title=submission.content['title']),
        recipients=[editors_group_id],
        message='''A revision has been {action} to the article titled "{title}" where you are an assigned editor.

The revision can be viewed on OpenReview here: https://openreview.net/revisions?id={forum}'''.format(action=action, title=submission.content['title'], forum=note.forum),
        ignoreRecipients=None,
        sender=None
    )

    client.post_message(subject='[Agora/COVID-19] A revision has been {action} on the article titled "{title}"'.format(action=action, title=submission.content['title']),
        recipients=[reviewers_group_id],
        message='''A revision has been {action} to the article titled "{title}" where you are an assigned reviewer.

The revision can be viewed on OpenReview here: https://openreview.net/revisions?id={forum}'''.format(action=action, title=submission.content['title'], forum=note.forum),
        ignoreRecipients=None,
        sender=None
    )