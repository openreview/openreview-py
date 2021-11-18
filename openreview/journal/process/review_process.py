def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    note=edit.note
    submission = client.get_note(note.forum)
    venue_id = journal.venue_id

    review_note=client.get_note(note.id)
    if review_note.readers == ['everyone']:
        return

    reviews=client.get_notes(forum=note.forum, invitation=edit.invitation)
    if len(reviews) == 3:
        ## Release the reviews to everyone
        invitation = client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=journal.get_release_review_id(number=submission.number),
                bulk=True,
                invitees=[venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                edit={
                    'signatures': { 'values': [venue_id ] },
                    'readers': { 'values': [ venue_id, journal.get_action_editors_id(number=submission.number), '${{note.id}.signatures}' ] },
                    'writers': { 'values': [ venue_id ] },
                    'note': {
                        'id': { 'value-invitation': edit.invitation },
                        'readers': { 'values': [ 'everyone' ] }
                    }
                }
        ))

        ## Release the comments to everyone
        official_comment_invitation_id = journal.get_official_comment_id(number=submission.number)
        release_comment_invitation_id = journal.get_release_comment_id(number=submission.number)
        invitation = client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=release_comment_invitation_id,
                invitees=[venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                edit={
                    'signatures': { 'values': [venue_id ] },
                    'readers': { 'values': [ venue_id, '${{note.id}.signatures}' ] },
                    'writers': { 'values': [ venue_id ] },
                    'note': {
                        'id': { 'value-invitation': official_comment_invitation_id },
                        'readers': { 'values': [ 'everyone' ] }
                    }
                }
        ))

        print(f'Get comments from invitation {official_comment_invitation_id}')
        comments = client.get_notes(invitation=official_comment_invitation_id)
        authors_id = journal.get_authors_id(number=submission.number)
        anon_reviewers_id = journal.get_reviewers_id(number=submission.number, anon=True)
        print(f'Releasing {len(comments)} comments...')
        for comment in comments:
            if authors_id in comment.readers and [r for r in comment.readers if anon_reviewers_id in r]:
                client.post_note_edit(invitation=release_comment_invitation_id,
                    signatures=[ venue_id ],
                    note=openreview.api.Note(
                        id=comment.id
                    )
                )

        ## Enable official recommendation
        print('Enable official recommendations')
        cdate = datetime.datetime.utcnow() + datetime.timedelta(weeks = 2)
        duedate = cdate + datetime.timedelta(weeks = 2)
        journal.invitation_builder.set_official_recommendation_invitation(journal, submission, cdate, duedate)

        ## Send email notifications to authors
        print('Send emails to authors')
        now = datetime.datetime.utcnow()
        duedate = now + datetime.timedelta(weeks = 2)
        late_duedate = now + datetime.timedelta(weeks = 4)
        client.post_message(
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Reviewer responses and discussion for your TMLR submission {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

Now that 3 reviews have been submitted for your submission, all reviews have been made public. If you haven’t already, please read the reviews and start engaging with the reviewers to attempt to address any concern they may have about your submission.

In 2 weeks ({duedate.strftime("%b %d")}), no later than in 4 weeks ({late_duedate.strftime("%b %d")}), reviewers will be able to submit a formal decision recommendation to the Action Editor in charge of your submission. The reviewers’ goal will be to gather all the information they need to submit their decision recommendation.

Visit the following link to respond to the reviews: https://openreview.net/forum?id={submission.id}

For more details and guidelines on the TMLR review process, visit jmlr.org/tmlr .

The TMLR Editors-in-Chief
''',
            replyTo=journal.contact_info
        )

        ## Send email notifications to reviewers
        print('Send emails to reviewers')
        client.post_message(
            recipients=[journal.get_reviewers_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Start of author discussion for TMLR submission {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

Thank you for submitting your review for TMLR submission "{submission.content['title']['value']}".

Now that 3 reviews have been submitted for the submission, all reviews have been made public. Please read the other reviews and start engaging with the authors (and possibly the other reviewers and AE) in order to address any concern you may have about the submission. Your goal should be to gather all the information you need **within the next 2 weeks** to be comfortable submitting a decision recommendation for this paper. You will receive an upcoming notification on how to enter your recommendation in OpenReview.

You will find the OpenReview page for this submission at this link: https://openreview.net/forum?id={submission.id}

For more details and guidelines on the TMLR review process, visit jmlr.org/tmlr .

We thank you for your essential contribution to TMLR!

The TMLR Editors-in-Chief
''',
            replyTo=journal.contact_info
        )

        ## Send email notifications to the action editor
        print('Send emails to action editor')
        client.post_message(
            recipients=[journal.get_action_editors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Start of author discussion for TMLR submission {submission.content['title']['value']}''',
            message=f'''Hi {{{{fullname}}}},

Now that 3 reviews have been submitted for submission {submission.content['title']['value']}, all reviews have been made public. Please read the reviews and oversee the discussion between the reviewers and the authors. The goal of the reviewers should be to gather all the information they need to be comfortable submitting a decision recommendation to you for this submission. Reviewers will be able to submit their formal decision recommendation starting in **2 weeks**.

You will find the OpenReview page for this submission at this link: https://openreview.net/forum?id={submission.id}

For more details and guidelines on the TMLR review process, visit jmlr.org/tmlr .

We thank you for your essential contribution to TMLR!

The TMLR Editors-in-Chief
''',
            replyTo=journal.contact_info
        )