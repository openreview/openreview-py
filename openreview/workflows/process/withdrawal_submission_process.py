def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    withdrawal_invitation_id = domain.content['withdrawal_invitation_id']['value']
    venue_name = domain.content['title']['value']
    reveal_authors = domain.content['withdrawn_submission_reveal_authors']['value']
    withdrawn_venue_id = domain.content['withdrawn_venue_id']['value']

    submission = client.get_note(edit.note.forum)

    return client.post_note_edit(invitation=withdrawal_invitation_id,
                            signatures=[venue_id],
                            note=openreview.api.Note(
                                id=submission.id,
                                content={
                                    'venue': {
                                        'value': openreview.tools.pretty_id(withdrawn_venue_id)
                                    },
                                    '_bibtex':{
                                        'value':openreview.tools.generate_bibtex(
                                            note=submission,
                                            venue_fullname=venue_name,
                                            year=str(datetime.datetime.now().year),
                                            url_forum=submission.forum,
                                            paper_status='rejected',
                                            anonymous=not reveal_authors
                                        )
                                    }
                                }
                            ))