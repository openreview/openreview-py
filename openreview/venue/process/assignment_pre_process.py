def process_update(client, edge, invitation, existing_edge):

    REVIEW_INVITATION_ID = ''
    ANON_REVIEWER_REGEX = ''

    if edge.ddate:
        paper=client.get_note(edge.head)

        reviews=client.get_notes(invitation=REVIEW_INVITATION_ID.replace('{number}', str(paper.number)))

        if not reviews:
            return

        groups=client.get_groups(regex=ANON_REVIEWER_REGEX.replace('{number}', str(paper.number)), signatory=edge.tail)

        if not groups:
            raise openreview.OpenReviewException(f'Can not remove assignment, signatory groups not found for {edge.tail}.')


        for review in reviews:
            if review.signatures[0] == groups[0].id:
                raise openreview.OpenReviewException(f'Can not remove assignment, the user {edge.tail} already posted a review.')

