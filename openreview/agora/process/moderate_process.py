def process(client, note, invitation):


    submission = client.get_note(note.forum)

    if 'Accept' in note.content.get('resolution', ''):

        submission.readers = ['everyone']
        submission.writers = ['OpenReview.net/Support']
        submission.invitation = '-Agora/Covid-19/-/Article'

        client.post_note(submission)

        client.post_message(subject='[Agora/Covid-19] Your submission has been accepted',
            recipients=submission.content['authorids'],
            message='Congratulations, your submission has been released to the public.\n\nTo view your article, click here: https://openreview.net/forum?id={forum}'.format(forum=note.forum),
            ignoreRecipients=None,
            sender=None
        )

    if 'Desk-Reject' in note.content.get('resolution', ''):

        submission.invitation = '-Agora/Covid-19/-/Desk-Reject'

        client.post_note(submission)

        client.post_message(subject='[Agora/Covid-19] Your submission has been desk-rejected',
            recipients=submission.content['authorids'],
            message='Unfortunately your submission has been desk-rejected.\n\nTo read the reason, click here: https://openreview.net/forum?id={forum}&noteId={id}'.format(forum=note.forum, id=note.id),
            ignoreRecipients=None,
            sender=None
        )
