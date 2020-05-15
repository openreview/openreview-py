def process_update(client, note, invitation, existing_note):

    article = client.get_note(note.forum)

    support = 'OpenReview.net/Support'
    article_group_id = invitation.id.split('/-/')[0]
    reviewers_group_id = '{}/Reviewers'.format(article_group_id)
    reviewers_group = openreview.Group(
        id=reviewers_group_id,
        readers=['everyone'],
        writers=[support],
        signatures=[support],
        signatories=[reviewers_group_id],
        members=note.content.get('assigned_reviewers', []),
    )
    client.post_group(reviewers_group)

    assgined_reviewers = set(note.content.get('assigned_reviewers', [])) - set(article.content.get('assigned_reviewers')))

    if assgined_reviewers:
        client.post_message(subject='[Agora/Covid-19] You have been assigend to review the paper title: {title}'.format(title=article.content.get('title')),
            recipients=list(assgined_reviewers),
            message='Congratulations, your submission has been released to the public.\n\nTo view your article, click here: https://openreview.net/forum?id={forum}'.format(forum=article.forum),
            ignoreRecipients=None,
            sender=None
        )