def process_update(client, note, invitation, existing_note):

    covid_group_id = '-Agora/COVID-19'
    support = 'OpenReview.net/Support'
    editor = '{}/Editors'.format(covid_group_id)
    blocked = '{}/Blocked'.format(covid_group_id)

    ## Create article groups
    article_group = openreview.Group(
        id='{}/Article{}'.format(covid_group_id, note.number),
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
        super = '{}/-/Revision'.format(covid_group_id),
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
        id = '{}/-/Editors_Assignment'.format(article_group.id),
        super = '{}/-/Editors_Assignment'.format(covid_group_id),
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
        id = '{}/-/Reviewers_Assignment'.format(article_group.id),
        super = '{}/-/Reviewers_Assignment'.format(covid_group_id),
        invitees = [editor, editors_group_id, support],
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
        super = '{}/-/Review'.format(covid_group_id),
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
                # Temporarily use everyone only.
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

    meta_review_invitation = openreview.Invitation(
        id = '{}/-/Meta_Review'.format(article_group.id),
        super = '{}/-/Meta_Review'.format(covid_group_id),
        invitees = [editors_group_id, support],
        writers = [support],
        signatures = [support],
        reply = {
            'forum': note.forum,
            'replyto': note.forum,
            'readers': {
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
    client.post_invitation(meta_review_invitation)

    suggest_reviewer_invitation = openreview.Invitation(
        id = '{}/-/Reviewers_Suggestion'.format(article_group.id),
        super = '{}/-/Reviewers_Suggestion'.format(covid_group_id),
        invitees = ['everyone'],
        noninvitees = [blocked],
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
        super = '{}/-/Comment'.format(covid_group_id),
        invitees = [support, editor, editors_group_id, reviewers_group_id, authors_group_id],
        noninvitees = [blocked],
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
                'values-regex': '~.*|{}|{}'.format(support, authors_group_id)
            }
        }
    )
    client.post_invitation(comment_invitation)


