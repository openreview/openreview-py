def process_update(client, note, invitation, existing_note):

    support = 'OpenReview.net/Support'
    editor = '-Agora/Covid-19/Editors'

    ## Create article groups
    article_group = openreview.Group(
        id='-Agora/Covid-19/Article{}'.format(note.number),
        readers=['everyone'],
        writers=[support],
        signatures=[support],
        signatories=[support],
        members=[],
    )
    client.post_group(article_group)

    authors_group_id = '{}/Authors'.format(article_group.id)
    authors_group = openreview.Group(
        id=authors_group_id,
        readers=['everyone'],
        writers=[support],
        signatures=[support],
        signatories=[authors_group_id],
        members=note.content['authorids'],
    )
    client.post_group(authors_group)

    editors_group_id = '{}/Editors'.format(article_group.id)
    editors_group = openreview.Group(
        id=editors_group_id,
        readers=['everyone'],
        writers=[support],
        signatures=[support],
        signatories=[editors_group_id],
        members=[],
    )
    client.post_group(editors_group)

    reviewers_group_id = '{}/Reviewers'.format(article_group.id)
    reviewers_group = openreview.Group(
        id=reviewers_group_id,
        readers=['everyone'],
        writers=[support],
        signatures=[support],
        signatories=[reviewers_group_id],
        members=[],
    )
    client.post_group(reviewers_group)

    ## Create invitations
    revision_invitation = openreview.Invitation(
        id = '{}/-/Revision'.format(article_group.id),
        super = '-Agora/Covid-19/-/Revision',
        invitees = [authors_group_id, support],
        writers = [support],
        signatures = [support],
        reply = {
            'forum': note.forum,
            'referent': note.forum,
            'writers': {
                'values': [authors_group_id, support]
            },
            'signatures': {
                'values-regex': '{}|{}'.format(authors_group_id, support)
            }
        }
    )
    client.post_invitation(revision_invitation)

    assign_editor_invitation = openreview.Invitation(
        id = '{}/-/Assign_Editor'.format(article_group.id),
        super = '-Agora/Covid-19/-/Assign_Editor',
        invitees = [editor, support],
        writers = [support],
        signatures = [support],
        reply = {
            'forum': note.forum,
            'referent': note.forum,
            'writers': {
                'values': [editor, support]
            },
            'signatures': {
                'values-regex': '~.*|{}'.format(support)
            }
        }
    )
    client.post_invitation(assign_editor_invitation)

    assign_reviewer_invitation = openreview.Invitation(
        id = '{}/-/Assign_Reviewer'.format(article_group.id),
        super = '-Agora/Covid-19/-/Assign_Reviewer',
        invitees = [editors_group_id, support],
        writers = [support],
        signatures = [support],
        reply = {
            'forum': note.forum,
            'referent': note.forum,
            'writers': {
                'values': [editors_group_id, support]
            },
            'signatures': {
                'values-regex': '~.*|{}'.format(support)
            }
        }
    )
    client.post_invitation(assign_reviewer_invitation)

    review_invitation = openreview.Invitation(
        id = '{}/-/Review'.format(article_group.id),
        super = '-Agora/Covid-19/-/Review',
        invitees = [reviewers_group_id, support],
        writers = [support],
        signatures = [support],
        reply = {
            'forum': note.forum,
            'replyto': note.forum,
            'readers': {
                # 'values-dropdown': [
                #    'everyone',
                #     editor,
                #     editors_group_id,
                #     reviewers_group_id
                # ],
                # Temporally use everyone only.
                'values': ['everyone'],
                'default': ['everyone']
            },
            'writers': {
                'values-copied': ['{signatures}', support]
            },
            'signatures': {
                'values-regex': '~.*|{}'.format(support)
            }
        }
    )
    client.post_invitation(review_invitation)

    suggest_reviewer_invitation = openreview.Invitation(
        id = '{}/-/Suggest_Reviewer'.format(article_group.id),
        super = '-Agora/Covid-19/-/Suggest_Reviewer',
        invitees = ['~'],
        writers = [support],
        signatures = [support],
        reply = {
            'forum': note.forum,
            'replyto': note.forum,
            'readers': {
                'values': ['everyone']
            },
            'writers': {
                'values-copied': ['{signatures}', support]
            },
            'signatures': {
                'values-regex': '~.*|{}'.format(support)
            }
        }
    )
    client.post_invitation(suggest_reviewer_invitation)

    comment_invitation = openreview.Invitation(
        id = '{}/-/Comment'.format(article_group.id),
        super = '-Agora/Covid-19/-/Comment',
        invitees = [support, editor, editors_group_id, reviewers_group_id],
        writers = [support],
        signatures = [support],
        reply = {
            'forum': note.forum,
            'readers': {
                'values': ['everyone']
            },
            'writers': {
                'values-copied': ['{signatures}', support]
            },
            'signatures': {
                'values-regex': '~.*|{}'.format(support)
            }
        }
    )
    client.post_invitation(comment_invitation)


