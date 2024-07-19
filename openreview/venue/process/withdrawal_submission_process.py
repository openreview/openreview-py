def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    withdrawn_submission_id = domain.content['withdrawn_submission_id']['value']
    venue_name = domain.content['title']['value']
    parent_invitation = client.get_invitation(invitation.invitations[0])
    reveal_authors = parent_invitation.get_content_value('reveal_authors', domain.get_content_value('withdrawn_submission_reveal_authors'))

    submission = client.get_note(edit.note.forum)

    return client.post_note_edit(invitation=withdrawn_submission_id,
                            signatures=[venue_id],
                            note=openreview.api.Note(
                                id=submission.id,
                                content={
                                    '_bibtex':{
                                        'value':openreview.tools.generate_bibtex(
                                            note=submission,
                                            venue_fullname=venue_name,
                                            year=str(datetime.datetime.utcnow().year),
                                            url_forum=submission.forum,
                                            paper_status='rejected',
                                            anonymous=not reveal_authors
                                        )
                                    }
                                }
                            ))