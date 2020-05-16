def process_update(client, note, invitation, existing_note):

    article = client.get_note(note.forum)

    support = 'OpenReview.net/Support'
    article_group_id = invitation.id.split('/-/')[0]
    editors_group_id = '{}/Editors'.format(article_group_id)

    existent_group = openreview.tools.get_group(client, editors_group_id)
    existent_editors = []
    if existent_group:
        existent_editors = existent_group.members

    editors_group = openreview.Group(
        id=editors_group_id,
        readers=['everyone'],
        writers=[support],
        signatures=[support],
        signatories=[editors_group_id],
        members=note.content.get('assigned_editors', [])
    )
    client.post_group(editors_group)

    new_editors = list(set(note.content.get('assigned_editors', [])) - set(existent_editors))

    if new_editors:

        client.post_message(subject='[Agora/Covid-19] You have been assigned to be an editor of the article titled "{title}"'.format(title=article.content['title']),
            recipients=new_editors,
            message='''You have been assigned to be an editor of the paper titled "{title}" by {signature}, Editor-in-Chief of the Agora Covid-19 venue.
Your can start assigning reviewers now.

To view the article, click here: https://openreview.net/forum?id={forum}'''.format(title=article.content['title'], signature=note.signatures[0], forum=note.forum),
            ignoreRecipients=None,
            sender=None
        )

        client.post_message(subject='[Agora/Covid-19] An editor has been assigned to your article titled "{title}"'.format(title=article.content['title']),
            recipients=article.content['authorids'],
            message='''A new editor/s have been assigned to your paper titled "{title}" by {signature}, the Editor-in-Chief of this venue.

To view the article, click here: https://openreview.net/forum?id={forum}'''.format(title=article.content['title'], signature=note.signatures[0], forum=note.forum),
            ignoreRecipients=None,
            sender=None
        )
