def process_update(client, note, invitation, existing_note):

    article = client.get_note(note.forum)

    support = 'OpenReview.net/Support'
    article_group_id = invitation.id.split('/-/')[0]
    reviewers_group_id = '{}/Reviewers'.format(article_group_id)

    existent_group = openreview.tools.get_group(client, reviewers_group_id)
    existent_reviewers = []
    if existent_group:
        existent_reviewers = existent_group.members

    reviewers_group = openreview.Group(
        id=reviewers_group_id,
        readers=['everyone'],
        writers=[support],
        signatures=[support],
        signatories=[reviewers_group_id],
        members=note.content.get('assigned_reviewers', []),
    )
    client.post_group(reviewers_group)

    new_reviewers = list(set(note.content.get('assigned_reviewers', [])) - set(existent_reviewers))

    if new_reviewers:

        client.post_message(subject='[Agora/COVID-19] You have been assigned as a reviewer of the article titled "{title}"'.format(title=article.content['title']),
            recipients=new_reviewers,
            message='''You have been assigned to be a reviewer of the paper titled "{title}" by {signature}, the editor of this article. You may start reviewing the article now.

The article can be viewed on OpenReview here: https://openreview.net/forum?id={forum}'''.format(title=article.content['title'], signature=note.signatures[0], forum=note.forum),
            ignoreRecipients=None,
            sender=None
        )

        client.post_message(subject='[Agora/COVID-19] A reviewer has been assigned to your article titled "{title}"'.format(title=article.content['title']),
            recipients=article.content['authorids'],
            message='''A new reviewer has been assigned to your paper titled "{title}" by {signature}, the editor of this article.

The article can be viewed on OpenReview here: https://openreview.net/forum?id={forum}'''.format(title=article.content['title'], signature=note.signatures[0], forum=note.forum),
            ignoreRecipients=None,
            sender=None
        )
