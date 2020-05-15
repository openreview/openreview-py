def process_update(client, note, invitation, existing_note):

    ## Notify authors and editor
    author_subject = 'Agora Covid-19 has received your submission titled "{title}"'.format(title=note.content['title'])
    action = 'posted'
    if existing_note:
        action = 'deleted' if note.ddate else 'updated'

    author_message = '''Your submission to Agora Covid-19 has been {action}.

Title: {title}
Your submission will be examined by the Editor-in-Chief of the venue and then you will receive an email with a response.
To view your submission, click here: https://openreview.net/forum?id={forum}'''.format(action=action, title=note.content['title'], forum=note.forum)

    coauthor_message = author_message + '\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at {tauthor}'.format(tauthor=note.tauthor)

    client.post_message(subject=author_subject,
        recipients=[note.tauthor],
        message=author_message,
        ignoreRecipients=None,
        sender=None
    )

    client.post_message(subject=author_subject,
        recipients=note.content['authorids'],
        message=coauthor_message,
        ignoreRecipients=[note.tauthor],
        sender=None
    )

    support = 'OpenReview.net/Support'
    editor = '-Agora/Covid-19/Editors'
    superuser = 'OpenReview.net'

    client.post_message(subject='Agora Covid-19 has received a submission titled "{title}"'.format(title=note.content['title']),
        recipients=[editor, support],
        message=author_message,
        ignoreRecipients=None,
        sender=None
    )

    ## Create submission groups
    submission_group = openreview.Group(
        id='-Agora/Covid-19/Submission{}'.format(note.number),
        readers=['everyone'],
        writers=[support],
        signatures=[support],
        signatories=[support],
        members=[],
    )
    client.post_group(submission_group)

    authors_group_id = '{}/Authors'.format(submission_group.id)
    authors_group = openreview.Group(
        id=authors_group_id,
        readers=['everyone'],
        writers=[support],
        signatures=[support],
        signatories=[authors_group_id],
        members=note.content['authorids'],
    )
    client.post_group(authors_group)

    moderate_invitation = openreview.Invitation(
        id = '{}/-/Moderate'.format(submission_group.id),
        super = '-Agora/Covid-19/-/Moderate',
        writers = [support],
        signatures = [superuser],
        reply = {
            'forum': note.forum,
            'replyto': note.forum,
            'readers': {
                'values': [support, editor, authors_group_id]
            },
            'writers': {
                'values': [support]
            },
            'signatures': {
                'values-regex': '~.*'
            }
        }
    )
    client.post_invitation(moderate_invitation)


