def process(client, invitation):
    import datetime
    import openreview
    from openreview.stages.arr_content import hide_fields, hide_fields_from_public

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    venue_name = domain.content['title']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    program_chairs_id = domain.content['program_chairs_id']['value']
    submission_name = domain.content['submission_name']['value']
    authors_name = domain.content['authors_name']['value']
    reviewers_name = domain.content['reviewers_name']['value']
    reviewers_submitted_name = domain.content['reviewers_submitted_name']['value']
    area_chairs_name = domain.content['area_chairs_name']['value']
    senior_area_chairs_name = domain.content['senior_area_chairs_name']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate and cdate > now:
        # invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    submissions = client.get_all_notes(content={'venueid': submission_venue_id})

    def is_preprint(note):
        return note.content.get('preprint', {}).get('value') == 'yes'

    preprints = []
    non_preprints = []
    for note in submissions:
        if is_preprint(note):
            preprints.append(note)
        else:
            non_preprints.append(note)

    print(f'Processing {len(non_preprints)} non-preprint submissions')
    print(f'Processing {len(preprints)} preprint submissions')

    def post_submission_edit(submission):
        updated_note = openreview.api.Note(id=submission.id)
        client.post_note_edit(
            invitation=invitation.id,
            note=updated_note,
            signatures=[venue_id]
        )

    def get_paper_authors_group_id(number):
        return f"{venue_id}/{submission_name}{number}/{authors_name}"

    def get_committee_readers(number, include_authors=True):
        readers = [
            program_chairs_id,
            f"{venue_id}/{submission_name}{number}/{senior_area_chairs_name}",
            f"{venue_id}/{submission_name}{number}/{area_chairs_name}",
            f"{venue_id}/{submission_name}{number}/{reviewers_name}"
        ]
        if include_authors:
            readers.append(get_paper_authors_group_id(number))
        return readers

    def get_explanation_of_revisions_readers(submission):
        """
        Always replace current-cycle Reviewers with Reviewers/Submitted for this field

        If previous_URL exists and author doesn't want new reviewers:
          include previous-cycle Reviewers/Submitted
        """
        readers = [
            program_chairs_id,
            f"{venue_id}/{submission_name}{submission.number}/{senior_area_chairs_name}",
            f"{venue_id}/{submission_name}{submission.number}/{area_chairs_name}",
            f"{venue_id}/{submission_name}{submission.number}/{reviewers_name}/{reviewers_submitted_name}",
            get_paper_authors_group_id(submission.number)
        ]

        paper_link = submission.content.get('previous_URL', {}).get('value')
        wants_new_reviewers = submission.content.get('reassignment_request_reviewers', {}).get('value', '').startswith('Yes')

        if paper_link and not wants_new_reviewers:
            paper_forum = paper_link.split('?id=')[-1]
            arr_submission_v1 = openreview.tools.get_note(client_v1, paper_forum)
            if arr_submission_v1:
                v1_domain = arr_submission_v1.invitation.split('/-/')[0]
                readers.append(f"{v1_domain}/Paper{arr_submission_v1.number}/{reviewers_name}/{reviewers_submitted_name}")
            arr_submission_v2 = openreview.tools.get_note(client, paper_forum)
            if arr_submission_v2:
                v2_domain = arr_submission_v2.domain
                readers.append(f"{v2_domain}/{submission_name}{arr_submission_v2.number}/{reviewers_name}/{reviewers_submitted_name}")

        return readers

    def release_preprint_submission(submission):
        authors_group_id = get_paper_authors_group_id(submission.number)
        committee_readers = get_committee_readers(submission.number, include_authors=True)

        # Build content with field-level readers
        content = {}

        # Authors and authorids are always readable only by venue and authors
        venue_authors_readers = [venue_id, authors_group_id]
        content['authors'] = {'readers': venue_authors_readers}
        content['authorids'] = {'readers': venue_authors_readers}

        for field in hide_fields:
            content[field] = {'readers': venue_authors_readers}

        # hide_fields_from_public -> committee_readers (with authors)
        for field in hide_fields_from_public:
            if field == 'explanation_of_revisions_PDF':
                content[field] = {'readers': get_explanation_of_revisions_readers(submission)}
            else:
                content[field] = {'readers': committee_readers}

        # Set _bibtex and odate only if not already set
        if submission.odate is None:
            content['_bibtex'] = {
                'value': openreview.tools.generate_bibtex(
                    note=submission,
                    venue_fullname=venue_name,
                    year=str(datetime.datetime.now().year),
                    url_forum=submission.forum,
                    paper_status='under review',
                    anonymous=True
                )
            }

        # Build the note edit
        updated_note = openreview.api.Note(
            id=submission.id,
            readers=['everyone'],
            content=content
        )

        # Set odate only if not already set
        if submission.odate is None:
            updated_note.odate = now

        client.post_note_edit(
            invitation=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            note=updated_note
        )

    openreview.tools.concurrent_requests(
        post_submission_edit,
        non_preprints,
        desc='arr_post_submission_non_preprints'
    )

    openreview.tools.concurrent_requests(
        release_preprint_submission,
        preprints,
        desc='arr_post_submission_preprints'
    )
