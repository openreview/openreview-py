def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_name = domain.content['subtitle']['value']
    contact = domain.content['contact']['value']
    authors_name = domain.content['authors_name']['value']
    submission_name = domain.content['submission_name']['value']
    sender = domain.get_content_value('message_sender')

    submission = client.get_note(edit.note.id)

    subject = f'''{short_name} has received a new revision of your submission titled {submission.content['title']['value']}'''

    abstract_string = f'''
Abstract {submission.content['abstract']['value']}
''' if 'abstract' in submission.content else ''

    message = f'''Your new revision of the submission to {short_name} has been posted.

Title: {submission.content['title']['value']}
{abstract_string}
To view your submission, click here: https://openreview.net/forum?id={submission.forum}'''

    submission_authors = submission.authorids
    authors_group_id = f'{venue_id}/{submission_name}{submission.number}/{authors_name}'

    if submission_authors:
        author_group = openreview.tools.get_group(client, authors_group_id)
        if author_group and set(author_group.members) != set(submission_authors):
            client.post_group_edit(
                invitation=meta_invitation_id,
                readers = [venue_id],
                writers = [venue_id],
                signatures = [venue_id],
                group = openreview.api.Group(
                    id = author_group.id,
                    members = submission_authors
                )
            )

    client.post_message(
        invitation=meta_invitation_id,
        subject=subject,
        recipients=[authors_group_id],
        message=message,
        replyTo=contact,
        signature=venue_id,
        sender=sender
    )

    # Update BibTeX if submission is public and already has a bibtex field
    if submission.readers == ['everyone'] and '_bibtex' in submission.content:
        # Determine paper status based on venueid
        status_by_venueid = {
            submission.domain: 'accepted',
            domain.content['submission_venue_id']['value']: 'under review'
        }
        
        paper_status = status_by_venueid.get(submission.content['venueid']['value'], 'rejected')
        
        # Check if authors field has readers restrictions (anonymous if restricted)
        anonymous = 'readers' in submission.content['authors'] and len(submission.content['authors']['readers']) > 0
        
        # Get year from submission publication date (pdate or odate)
        year = datetime.datetime.fromtimestamp(submission.pdate / 1000).year if submission.pdate else datetime.datetime.fromtimestamp(submission.odate / 1000).year if submission.odate else datetime.datetime.now().year
        
        content = {}
        content['_bibtex'] = {
            'value': openreview.tools.generate_bibtex(
                note=submission,
                venue_fullname=domain.content['title']['value'],
                year=str(year),
                url_forum=submission.forum,
                paper_status=paper_status,
                anonymous=anonymous
            )
        }

        client.post_note_edit(
            invitation=meta_invitation_id,
            signatures=[venue_id],
            note=openreview.api.Note(
                id=submission.id,
                content=content
            )
        )
