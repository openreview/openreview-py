def unique_values(values):
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def release_review_readers(submission):
    return unique_values([
        journal.get_editors_in_chief_id(),
        editors_in_chief_id,
        journal.get_action_editors_id(submission.number),
        journal.get_reviewers_id(submission.number),
        journal.get_authors_id(submission.number)
    ])


def set_review_release_invitation(submission, readers):
    review_invitation = client.get_invitation(journal.get_review_id(number=submission.number))
    review_invitation.edit['note']['readers'] = readers
    review_invitation.edit['note']['nonreaders'] = []
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=review_invitation,
        replacement=True
    )
    release_invitation_id = journal.get_release_review_id(number=submission.number)
    try:
        release_invitation = client.get_invitation(release_invitation_id)
    except Exception:
        release_invitation = openreview.api.Invitation(id=release_invitation_id)
    release_invitation.signatures = [journal.venue_id]
    release_invitation.readers = [journal.venue_id]
    release_invitation.writers = [journal.venue_id]
    release_invitation.invitees = [journal.venue_id]
    release_invitation.edit = getattr(release_invitation, 'edit', None) or {
        'signatures': [journal.venue_id],
        'readers': readers,
        'writers': [journal.venue_id],
        'note': {
            'id': {
                'param': {
                    'withInvitation': journal.get_review_id(number=submission.number)
                }
            }
        }
    }
    if hasattr(release_invitation, 'ddate'):
        release_invitation.ddate = None
    if hasattr(release_invitation, 'expdate'):
        release_invitation.expdate = None
    release_invitation.edit['readers'] = readers
    release_invitation.edit['nonreaders'] = []
    release_invitation.edit['note']['readers'] = readers
    release_invitation.edit['note']['nonreaders'] = []
    release_invitation.edit['note']['writers'] = [journal.venue_id]
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=release_invitation,
        replacement=True
    )


def release_reviews_and_comments(submission, reviews, context=''):
    suffix = f' {context}' if context else ''
    print(f'Release reviews{suffix}...')
    readers = release_review_readers(submission)
    set_review_release_invitation(submission, readers)
    for review in reviews:
        client.post_note_edit(
            invitation=journal.get_release_review_id(number=submission.number),
            signatures=[journal.venue_id],
            note=openreview.api.Note(
                id=review.id,
                readers=readers,
                nonreaders=[],
                writers=[journal.venue_id]
            )
        )

    print(f'Release comments{suffix}...')
    journal.invitation_builder.set_note_release_comment_invitation(submission)
