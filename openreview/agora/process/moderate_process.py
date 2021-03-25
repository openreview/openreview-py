def process(client, note, invitation):

    covid_group_id = '-Agora/COVID-19'
    support = 'OpenReview.net/Support'
    submission = client.get_note(note.forum)

    if 'Accept' in note.content.get('resolution', ''):

        submission.readers = ['everyone']
        submission.writers = [support]
        submission.invitation = '{}/-/Article'.format(covid_group_id)

        client.post_note(submission)

        client.post_message(subject='[Agora/COVID-19] Your submission has been accepted',
            recipients=submission.content['authorids'],
            message='''Congratulations, your submission titled "{title}" has been accepted by {signature}, the Editor-in-Chief of this venue.
Your article is now visible to the public and an editor will be assigned soon based on your suggestions.

The article can be viewed on OpenReview here: https://openreview.net/forum?id={forum}'''.format(title=submission.content['title'], signature=note.signatures[0], forum=note.forum),
            ignoreRecipients=None,
            sender=None
        )

    if 'Desk-Reject' in note.content.get('resolution', ''):

        submission.invitation = '{}/-/Desk_Rejected'.format(covid_group_id)

        client.post_note(submission)

        client.post_message(subject='[Agora/COVID-19] Your submission has been rejected',
            recipients=submission.content['authorids'],
            message='Unfortunately your submission has been desk-rejected by the Editor-in-Chief of this venue.\n\nFor more information, see their comment on the OpenReview submission forum here: https://openreview.net/forum?id={forum}&noteId={id}'.format(forum=note.forum, id=note.id),
            ignoreRecipients=None,
            sender=None
        )
