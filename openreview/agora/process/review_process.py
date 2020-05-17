def process_update(client, note, invitation, existing_note):

    covid_group_id = '-Agora/COVID-19'
    support = 'OpenReview.net/Support'
    article_group_id = invitation.id.split('/-/')[0]
    editors_group_id = '{}/Editors'.format(article_group_id)
    submission = client.get_note(note.forum)

    action = 'posted'
    if existing_note:
        action = 'deleted' if note.ddate else 'updated'


    client.post_message(subject='[Agora/COVID-19] Review {action} to your article titled "{title}"'.format(action=action, title=submission.content['title']),
        recipients=submission.content['authorids'],
        message='''A review has been {action} to your article titled "{title}".

The review can be viewed on OpenReview here: https://openreview.net/forum?id={forum}&noteId={id}'''.format(action=action, title=submission.content['title'], forum=note.forum, id=note.id),
        ignoreRecipients=None,
        sender=None
    )

    client.post_message(subject='[Agora/COVID-19] Your review has been {action} on your assigned article titled "{title}"'.format(action=action, title=submission.content['title']),
        recipients=note.signatures,
        message='''Your review has been {action} to your assigned article titled "{title}".

The review can be viewed on OpenReview here: https://openreview.net/forum?id={forum}&noteId={id}'''.format(action=action, title=submission.content['title'], forum=note.forum, id=note.id),
        ignoreRecipients=None,
        sender=None
    )

    client.post_message(subject='[Agora/COVID-19] A review has been {action} on the article titled "{title}"'.format(action=action, title=submission.content['title']),
        recipients=[editors_group_id],
        message='''A review has been {action} to the article titled "{title}" where you are an assigned editor.

The review can be viewed on OpenReview here: https://openreview.net/forum?id={forum}&noteId={id}'''.format(action=action, title=submission.content['title'], forum=note.forum, id=note.id),
        ignoreRecipients=None,
        sender=None
    )