import openreview
import datetime
import json

def get_conference(client, request_form_id, support_user='OpenReview.net/Support'):

    note = client.get_note(request_form_id)
    if note.content.get('api_version') == '2':
        openreview_client = openreview.api.OpenReviewClient(baseurl = 'http://localhost:3001', token=client.token)
        venue = openreview.venue.Venue(openreview_client, note.content['venue_id'])
        venue.request_form_id = request_form_id
        venue.support_user = support_user
        venue.use_area_chairs = note.content.get('Area Chairs (Metareviewers)', '') == 'Yes, our venue has Area Chairs'
        venue.use_senior_area_chairs = note.content.get('senior_area_chairs') == 'Yes, our venue has Senior Area Chairs'
        venue.short_name = note.content.get('Abbreviated Venue Name')
        venue.name = note.content.get('Official Venue Name')
        venue.website = note.content.get('Official Website URL')
        venue.contact = note.content.get('contact_email')
        venue.reviewer_identity_readers = get_identity_readers(note, 'reviewer_identity')
        venue.area_chair_identity_readers = get_identity_readers(note, 'area_chair_identity')
        venue.senior_area_chair_identity_readers = get_identity_readers(note, 'senior_area_chair_identity')

        venue.submission_stage = get_submission_stage(note)
        venue.review_stage = get_review_stage(note)
        venue.bid_stages = get_bid_stages(note)
        venue.meta_review_stage = get_meta_review_stage(note)
        venue.comment_stage = get_comment_stage(note)
        venue.decision_stage = get_decision_stage(note)

        venue.setup(note.content.get('program_chair_emails'))
        venue.create_submission_stage()
        return venue

    builder = get_conference_builder(client, request_form_id, support_user)
    return builder.get_result()

def get_conference_builder(client, request_form_id, support_user='OpenReview.net/Support'):

    note = client.get_note(request_form_id)

    if not note.invitation.lower() == 'OpenReview.net/Support/-/Request_Form'.lower():
        raise openreview.OpenReviewException('Invalid request form invitation')

    if not note.content.get('venue_id') and not note.content.get('conference_id'):
        raise openreview.OpenReviewException('venue_id is not set')

    support_user = note.invitation.split('/-/')[0]
    builder = openreview.conference.ConferenceBuilder(client, support_user)
    builder.set_request_form_id(request_form_id)

    conference_start_date_str = 'TBD'
    conference_start_date = None
    start_date = note.content.get('Venue Start Date', note.content.get('Conference Start Date', '')).strip()
    if start_date:
        try:
            conference_start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            conference_start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d')
        conference_start_date_str = conference_start_date.strftime('%b %d %Y')

    submission_start_date_str = ''
    submission_start_date = note.content.get('Submission Start Date', '').strip()
    if submission_start_date:
        try:
            submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d')
        submission_start_date_str = submission_start_date.strftime('%b %d %Y %I:%M%p')
    else:
        submission_start_date = None

    submission_due_date_str = 'TBD'
    abstract_due_date_str = ''
    submission_second_due_date = note.content.get('Submission Deadline', '').strip()
    if submission_second_due_date:
        try:
            submission_second_due_date = datetime.datetime.strptime(submission_second_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_second_due_date = datetime.datetime.strptime(submission_second_due_date, '%Y/%m/%d')
        submission_due_date = note.content.get('abstract_registration_deadline', '').strip()
        if submission_due_date:
            try:
                submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d %H:%M')
            except ValueError:
                submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d')
            abstract_due_date_str = submission_due_date.strftime('%b %d %Y %I:%M%p')
            submission_due_date_str = submission_second_due_date.strftime('%b %d %Y %I:%M%p')
        else:
            submission_due_date = submission_second_due_date
            submission_due_date_str = submission_due_date.strftime('%b %d %Y %I:%M%p')
            submission_second_due_date = None
    else:
        submission_second_due_date = submission_due_date = None

    builder.set_conference_id(note.content.get('venue_id') if note.content.get('venue_id', None) else note.content.get('conference_id'))
    builder.set_conference_name(note.content.get('Official Venue Name', note.content.get('Official Conference Name')))
    builder.set_conference_short_name(note.content.get('Abbreviated Venue Name', note.content.get('Abbreviated Conference Name')))
    if conference_start_date:
        builder.set_conference_year(conference_start_date.year)

    homepage_header = {
        'title': note.content['title'],
        'subtitle': note.content.get('Abbreviated Venue Name', note.content.get('Abbreviated Conference Name')),
        'deadline': 'Submission Start: ' + submission_start_date_str + ' UTC-0, End: ' + submission_due_date_str + ' UTC-0',
        'date': conference_start_date_str,
        'website': note.content['Official Website URL'],
        'location': note.content.get('Location'),
        'contact': note.content.get('contact_email')
    }

    if abstract_due_date_str:
        homepage_header['deadline'] = 'Submission Start: ' + submission_start_date_str + ' UTC-0, Abstract Registration: ' + abstract_due_date_str +' UTC-0, End: ' + submission_due_date_str + ' UTC-0'

    override_header = note.content.get('homepage_override', '')
    if override_header:
        for key in override_header.keys():
            homepage_header[key] = override_header[key]

    builder.set_homepage_header(homepage_header)

    if note.content.get('Area Chairs (Metareviewers)', '') in ['Yes, our venue has Area Chairs', 'Yes, our conference has Area Chairs']:
        builder.has_area_chairs(True)

    if note.content.get('senior_area_chairs') == 'Yes, our venue has Senior Area Chairs':
        builder.has_senior_area_chairs(True)

    if note.content.get('ethics_chairs_and_reviewers') == 'Yes, our venue has Ethics Chairs and Reviewers':
        builder.has_ethics_chairs(True)
        builder.has_ethics_reviewers(True)

    double_blind = (note.content.get('Author and Reviewer Anonymity', '') == 'Double-blind')

    readers_map = {
        'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)': [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.REVIEWERS],
        'All area chairs only': [openreview.stages.SubmissionStage.Readers.AREA_CHAIRS],
        'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)': [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.REVIEWERS_ASSIGNED],
        'Program chairs and paper authors only': [],
        'Everyone (submissions are public)': [openreview.stages.SubmissionStage.Readers.EVERYONE],
        'Make accepted submissions public and hide rejected submissions': [openreview.stages.SubmissionStage.Readers.EVERYONE_BUT_REJECTED]
    }

    # Prioritize submission_readers over Open Reviewing Policy (because PCs can keep changing this)
    if 'submission_readers' in note.content:
        readers = readers_map[note.content.get('submission_readers')]
        public = 'Everyone (submissions are public)' in readers
    else:
        public = (note.content.get('Open Reviewing Policy', '') in ['Submissions and reviews should both be public.', 'Submissions should be public, but reviews should be private.'])
        bidding_enabled = 'Reviewer Bid Scores' in note.content.get('Paper Matching', '') or 'Reviewer Recommendation Scores' in note.content.get('Paper Matching', '')
        if bidding_enabled and not public:
            readers = [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.REVIEWERS]
        elif public:
            readers = [openreview.stages.SubmissionStage.Readers.EVERYONE]
        else:
            readers = [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.REVIEWERS_ASSIGNED]

    submission_additional_options = note.content.get('Additional Submission Options', {})
    if isinstance(submission_additional_options, str):
        submission_additional_options = json.loads(submission_additional_options.strip())

    submission_remove_options = note.content.get('remove_submission_options', [])
    withdrawn_submission_public = 'Yes' in note.content.get('withdrawn_submissions_visibility', '')
    email_pcs_on_withdraw = 'Yes' in note.content.get('email_pcs_for_withdrawn_submissions', '')
    desk_rejected_submission_public = 'Yes' in note.content.get('desk_rejected_submissions_visibility', '')
    withdraw_submission_exp_date = note.content.get('withdraw_submission_expiration')
    if withdraw_submission_exp_date:
        try:
            withdraw_submission_exp_date = datetime.datetime.strptime(withdraw_submission_exp_date, '%Y/%m/%d %H:%M')
        except ValueError:
            withdraw_submission_exp_date = datetime.datetime.strptime(withdraw_submission_exp_date, '%Y/%m/%d')

    # Authors can not be anonymized only if venue is double-blind
    withdrawn_submission_reveal_authors = 'Yes' in note.content.get('withdrawn_submissions_author_anonymity', '')
    desk_rejected_submission_reveal_authors = 'Yes' in note.content.get('desk_rejected_submissions_author_anonymity', '')

    # Create review invitation during submission process function only when the venue is public, single blind and the review stage is setup.
    submission_release=(note.content.get('submissions_visibility', '') == 'Yes, submissions should be immediately revealed to the public.')
    create_groups=(not double_blind) and public and submission_release
    create_review_invitation = create_groups and note.content.get('make_reviews_public', None)

    author_names_revealed = 'Reveal author identities of all submissions to the public' in note.content.get('reveal_authors', '') or 'Reveal author identities of only accepted submissions to the public' in note.content.get('reveal_authors', '')
    papers_released = 'Release all submissions to the public'in note.content.get('release_submissions', '') or 'Release only accepted submission to the public' in note.content.get('release_submissions', '') or 'Make accepted submissions public and hide rejected submissions' in note.content.get('submission_readers', '')

    email_pcs = 'Yes' in note.content.get('email_pcs_for_new_submissions', '')

    name = note.content.get('submission_name', 'Submission').strip()

    author_reorder_after_first_deadline = note.content.get('submission_deadline_author_reorder', 'No') == 'Yes'

    submission_email = note.content.get('submission_email', None)

    builder.set_submission_stage(
        name=name,
        double_blind=double_blind,
        public=public,
        start_date=submission_start_date,
        due_date=submission_due_date,
        second_due_date=submission_second_due_date,
        additional_fields=submission_additional_options,
        remove_fields=submission_remove_options,
        email_pcs=email_pcs,
        create_groups=create_groups,
        create_review_invitation=create_review_invitation,
        withdraw_submission_exp_date=withdraw_submission_exp_date,
        withdrawn_submission_public=withdrawn_submission_public,
        withdrawn_submission_reveal_authors=withdrawn_submission_reveal_authors,
        email_pcs_on_withdraw=email_pcs_on_withdraw,
        desk_rejected_submission_public=desk_rejected_submission_public,
        desk_rejected_submission_reveal_authors=desk_rejected_submission_reveal_authors,
        author_names_revealed=author_names_revealed,
        papers_released=papers_released,
        readers=readers,
        author_reorder_after_first_deadline=author_reorder_after_first_deadline,
        submission_email=submission_email)

    paper_matching_options = note.content.get('Paper Matching', [])
    include_expertise_selection = note.content.get('include_expertise_selection', '') == 'Yes'
    if 'OpenReview Affinity' in paper_matching_options:
        builder.set_expertise_selection_stage(due_date=submission_due_date, include_option=include_expertise_selection)

    if not paper_matching_options or 'Organizers will assign papers manually' in paper_matching_options:
        builder.enable_reviewer_reassignment(enable=True)

    ## Contact Emails is deprecated
    program_chair_ids = note.content.get('Contact Emails', []) + note.content.get('program_chair_emails', [])
    builder.set_conference_program_chairs_ids(program_chair_ids)
    builder.use_legacy_anonids(note.content.get('reviewer_identity') is None)
    builder.use_recruitment_template(note.content.get('use_recruitment_template', 'No') == 'Yes')

    readers_map = {
        'Program Chairs': openreview.stages.IdentityReaders.PROGRAM_CHAIRS,
        'All Senior Area Chairs': openreview.stages.IdentityReaders.SENIOR_AREA_CHAIRS,
        'Assigned Senior Area Chair': openreview.stages.IdentityReaders.SENIOR_AREA_CHAIRS_ASSIGNED,
        'All Area Chairs': openreview.stages.IdentityReaders.AREA_CHAIRS,
        'Assigned Area Chair': openreview.stages.IdentityReaders.AREA_CHAIRS_ASSIGNED,
        'All Reviewers': openreview.stages.IdentityReaders.REVIEWERS,
        'Assigned Reviewers': openreview.stages.IdentityReaders.REVIEWERS_ASSIGNED
    }

    builder.set_reviewer_identity_readers(get_identity_readers(note, 'reviewer_identity'))
    builder.set_area_chair_identity_readers(get_identity_readers(note, 'area_chair_identity'))
    builder.set_senior_area_chair_identity_readers(get_identity_readers(note, 'senior_area_chair_identity'))
    builder.set_reviewer_roles(note.content.get('reviewer_roles', ['Reviewers']))
    builder.set_area_chair_roles(note.content.get('area_chair_roles', ['Area_Chairs']))
    builder.set_senior_area_chair_roles(note.content.get('senior_area_chair_roles', ['Senior_Area_Chairs']))
    builder.set_review_stage(get_review_stage(note))
    builder.set_ethics_review_stage(get_ethics_review_stage(note))
    builder.set_bid_stages(get_bid_stages(note))
    builder.set_meta_review_stage(get_meta_review_stage(note))
    builder.set_comment_stage(get_comment_stage(note))
    builder.set_decision_stage(get_decision_stage(note))
    builder.set_submission_revision_stage(get_submission_revision_stage(note))

    decision_heading_map = note.content.get('home_page_tab_names')
    if decision_heading_map:
        builder.set_homepage_layout('decisions')
        builder.set_venue_heading_map(decision_heading_map)

    return builder

def get_identity_readers(request_forum, field_name):

    readers_map = {
        'Program Chairs': openreview.stages.IdentityReaders.PROGRAM_CHAIRS,
        'All Senior Area Chairs': openreview.stages.IdentityReaders.SENIOR_AREA_CHAIRS,
        'Assigned Senior Area Chair': openreview.stages.IdentityReaders.SENIOR_AREA_CHAIRS_ASSIGNED,
        'All Area Chairs': openreview.stages.IdentityReaders.AREA_CHAIRS,
        'Assigned Area Chair': openreview.stages.IdentityReaders.AREA_CHAIRS_ASSIGNED,
        'All Reviewers': openreview.stages.IdentityReaders.REVIEWERS,
        'Assigned Reviewers': openreview.stages.IdentityReaders.REVIEWERS_ASSIGNED
    }

    return [readers_map[r] for r in request_forum.content.get(field_name, [])]    

def get_submission_stage(request_forum):

    name = request_forum.content.get('submission_name', 'Submission').strip()
    double_blind = (request_forum.content.get('Author and Reviewer Anonymity', '') == 'Double-blind')

    readers_map = {
        'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)': [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.REVIEWERS],
        'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)': [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.REVIEWERS_ASSIGNED],
        'Program chairs and paper authors only': [],
        'Everyone (submissions are public)': [openreview.stages.SubmissionStage.Readers.EVERYONE],
        'Make accepted submissions public and hide rejected submissions': [openreview.stages.SubmissionStage.Readers.EVERYONE_BUT_REJECTED]
    }

    # Prioritize submission_readers over Open Reviewing Policy (because PCs can keep changing this)
    if 'submission_readers' in request_forum.content:
        readers = readers_map[request_forum.content.get('submission_readers')]
        public = 'Everyone (submissions are public)' in readers
    else:
        public = (request_forum.content.get('Open Reviewing Policy', '') in ['Submissions and reviews should both be public.', 'Submissions should be public, but reviews should be private.'])
        bidding_enabled = 'Reviewer Bid Scores' in request_forum.content.get('Paper Matching', '') or 'Reviewer Recommendation Scores' in request_forum.content.get('Paper Matching', '')
        if bidding_enabled and not public:
            readers = [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.REVIEWERS]
        elif public:
            readers = [openreview.stages.SubmissionStage.Readers.EVERYONE]
        else:
            readers = [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.REVIEWERS_ASSIGNED]

    submission_start_date = request_forum.content.get('Submission Start Date', '').strip()
    if submission_start_date:
        try:
            submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d')
    else:
        submission_start_date = None

    submission_second_due_date = request_forum.content.get('Submission Deadline', '').strip()
    if submission_second_due_date:
        try:
            submission_second_due_date = datetime.datetime.strptime(submission_second_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_second_due_date = datetime.datetime.strptime(submission_second_due_date, '%Y/%m/%d')
        submission_due_date = request_forum.content.get('abstract_registration_deadline', '').strip()
        if submission_due_date:
            try:
                submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d %H:%M')
            except ValueError:
                submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d')
        else:
            submission_due_date = submission_second_due_date
            submission_second_due_date = None
    else:
        submission_second_due_date = submission_due_date = None

    submission_additional_options = request_forum.content.get('Additional Submission Options', {})
    if isinstance(submission_additional_options, str):
        submission_additional_options = json.loads(submission_additional_options.strip())

    submission_remove_options = request_forum.content.get('remove_submission_options', [])
    submission_release=(request_forum.content.get('submissions_visibility', '') == 'Yes, submissions should be immediately revealed to the public.')
    create_groups=(not double_blind) and public and submission_release

    return openreview.stages.SubmissionStage(name = name,
        double_blind=double_blind,
        start_date=submission_start_date,
        due_date=submission_due_date,
        second_due_date=submission_second_due_date,
        additional_fields=submission_additional_options,
        remove_fields=submission_remove_options,
        create_groups=create_groups,
        readers=readers)

def get_bid_stages(request_forum):
    bid_start_date = request_forum.content.get('bid_start_date', '').strip()
    if bid_start_date:
        try:
            bid_start_date = datetime.datetime.strptime(bid_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            bid_start_date = datetime.datetime.strptime(bid_start_date, '%Y/%m/%d')
    else:
        bid_start_date = None

    bid_due_date = request_forum.content.get('bid_due_date', '').strip()
    if bid_due_date:
        try:
            bid_due_date = datetime.datetime.strptime(bid_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            bid_due_date = datetime.datetime.strptime(bid_due_date, '%Y/%m/%d')
    else:
        bid_due_date = None

    reviewer_bid_stage = openreview.stages.BidStage(request_forum.content['venue_id'] + '/Reviewers', start_date = bid_start_date, due_date = bid_due_date, request_count = int(request_forum.content.get('bid_count', 50)))
    bid_stages = [reviewer_bid_stage]

    if 'Yes, our venue has Area Chairs' in request_forum.content.get('Area Chairs (Metareviewers)', ''):
        ac_bid_stage = openreview.stages.BidStage(request_forum.content['venue_id'] + '/Area_Chairs', start_date = bid_start_date, due_date = bid_due_date, request_count = int(request_forum.content.get('bid_count', 50)))
        bid_stages.append(ac_bid_stage)

    return bid_stages

def get_review_stage(request_forum):
    review_start_date = request_forum.content.get('review_start_date', '').strip()
    if review_start_date:
        try:
            review_start_date = datetime.datetime.strptime(review_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_start_date = datetime.datetime.strptime(review_start_date, '%Y/%m/%d')
    else:
        review_start_date = None

    review_due_date = request_forum.content.get('review_deadline', '').strip()
    if review_due_date:
        try:
            review_due_date = datetime.datetime.strptime(review_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_due_date = datetime.datetime.strptime(review_due_date, '%Y/%m/%d')
    else:
        review_due_date = None

    review_form_additional_options = request_forum.content.get('additional_review_form_options', {})

    review_form_remove_options = request_forum.content.get('remove_review_form_options', '').replace(',', ' ').split()

    readers_map = {
        'Reviews should be immediately revealed to all reviewers': openreview.stages.ReviewStage.Readers.REVIEWERS,
        'Reviews should be immediately revealed to the paper\'s reviewers': openreview.stages.ReviewStage.Readers.REVIEWERS_ASSIGNED,
        'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review': openreview.stages.ReviewStage.Readers.REVIEWERS_SUBMITTED,
        'Review should not be revealed to any reviewer, except to the author of the review': openreview.stages.ReviewStage.Readers.REVIEWER_SIGNATURE
    }
    reviewer_readers= request_forum.content.get('release_reviews_to_reviewers', '')

    #Deprecated
    if reviewer_readers.startswith('Yes'):
        release_to_reviewers = openreview.stages.ReviewStage.Readers.REVIEWERS_ASSIGNED
    else:
        release_to_reviewers = readers_map.get(reviewer_readers, openreview.stages.ReviewStage.Readers.REVIEWER_SIGNATURE)

    return openreview.stages.ReviewStage(
        start_date = review_start_date,
        due_date = review_due_date,
        allow_de_anonymization = (request_forum.content.get('Author and Reviewer Anonymity', None) == 'No anonymity'),
        public = (request_forum.content.get('make_reviews_public', None) == 'Yes, reviews should be revealed publicly when they are posted'),
        release_to_authors = (request_forum.content.get('release_reviews_to_authors', '').startswith('Yes')),
        release_to_reviewers = release_to_reviewers,
        email_pcs = (request_forum.content.get('email_program_chairs_about_reviews', '').startswith('Yes')),
        additional_fields = review_form_additional_options,
        remove_fields = review_form_remove_options,
        rating_field_name=request_forum.content.get('review_rating_field_name', 'rating'),
        confidence_field_name=request_forum.content.get('review_confidence_field_name', 'confidence')
    )

def get_ethics_review_stage(request_forum):
    review_start_date = request_forum.content.get('ethics_review_start_date', '').strip()
    if review_start_date:
        try:
            review_start_date = datetime.datetime.strptime(review_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_start_date = datetime.datetime.strptime(review_start_date, '%Y/%m/%d')
    else:
        review_start_date = None

    review_due_date = request_forum.content.get('ethics_review_deadline', '').strip()
    if review_due_date:
        try:
            review_due_date = datetime.datetime.strptime(review_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_due_date = datetime.datetime.strptime(review_due_date, '%Y/%m/%d')
    else:
        review_due_date = None

    review_form_additional_options = request_forum.content.get('additional_ethics_review_form_options', {})

    review_form_remove_options = request_forum.content.get('remove_ethics_review_form_options', '').replace(',', ' ').split()

    readers_map = {
        'Ethics reviews should be immediately revealed to all reviewers and ethics reviewers': openreview.stages.EthicsReviewStage.Readers.ALL_COMMITTEE,
        'Ethics reviews should be immediately revealed to the paper\'s reviewers and ethics reviewers': openreview.stages.EthicsReviewStage.Readers.ALL_ASSIGNED_COMMITTEE,
        'Ethics reviews should be immediately revealed to the paper\'s ethics reviewers': openreview.stages.EthicsReviewStage.Readers.ASSIGNED_ETHICS_REVIEWERS,
        'Ethics Review should not be revealed to any reviewer, except to the author of the ethics review': openreview.stages.EthicsReviewStage.Readers.ETHICS_REVIEWER_SIGNATURE
    }
    release_to_reviewers = readers_map.get(request_forum.content.get('release_ethics_reviews_to_reviewers', ''), openreview.stages.EthicsReviewStage.Readers.ETHICS_REVIEWER_SIGNATURE)

    flagged_submissions = []
    if request_forum.content.get('ethics_review_submissions'):
        flagged_submissions = [int(number) for number in request_forum.content['ethics_review_submissions'].split(',')]

    return openreview.stages.EthicsReviewStage(
        start_date = review_start_date,
        due_date = review_due_date,
        release_to_public = (request_forum.content.get('make_ethics_reviews_public', None) == 'Yes, ethics reviews should be revealed publicly when they are posted'),
        release_to_authors = (request_forum.content.get('release_ethics_reviews_to_authors', '').startswith('Yes')),
        release_to_reviewers = release_to_reviewers,
        additional_fields = review_form_additional_options,
        remove_fields = review_form_remove_options,
        submission_numbers = flagged_submissions
    )

def get_meta_review_stage(request_forum):
    meta_review_start_date = request_forum.content.get('meta_review_start_date', '').strip()
    if meta_review_start_date:
        try:
            meta_review_start_date = datetime.datetime.strptime(meta_review_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            meta_review_start_date = datetime.datetime.strptime(meta_review_start_date, '%Y/%m/%d')
    else:
        meta_review_start_date = None

    meta_review_due_date = request_forum.content.get('meta_review_deadline', '').strip()
    if meta_review_due_date:
        try:
            meta_review_due_date = datetime.datetime.strptime(meta_review_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            meta_review_due_date = datetime.datetime.strptime(meta_review_due_date, '%Y/%m/%d')
    else:
        meta_review_due_date = None

    meta_review_form_additional_options = request_forum.content.get('additional_meta_review_form_options', {})
    options = request_forum.content.get('recommendation_options', '').strip()
    if options:
        if request_forum.content.get('api_version') == '2':
            meta_review_form_additional_options['recommendation'] = {
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': [s.translate(str.maketrans('', '', '"\'')).strip() for s in options.split(',')]
                    }
                }
            }
        else:
            meta_review_form_additional_options['recommendation'] = {
                'value-dropdown':[s.translate(str.maketrans('', '', '"\'')).strip() for s in options.split(',')],
                'required': True}

    meta_review_form_remove_options = request_forum.content.get('remove_meta_review_form_options', '').replace(',', ' ').split()

    readers_map = {
        'Meta reviews should be immediately revealed to all reviewers': openreview.stages.MetaReviewStage.Readers.REVIEWERS,
        'Meta reviews should be immediately revealed to the paper\'s reviewers': openreview.stages.MetaReviewStage.Readers.REVIEWERS_ASSIGNED,
        'Meta reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review': openreview.stages.MetaReviewStage.Readers.REVIEWERS_SUBMITTED,
        'Meta review should not be revealed to any reviewer': openreview.stages.MetaReviewStage.Readers.NO_REVIEWERS
    }

    reviewer_readers= request_forum.content.get('release_meta_reviews_to_reviewers', '')

    release_to_reviewers = readers_map.get(reviewer_readers, openreview.stages.MetaReviewStage.Readers.NO_REVIEWERS)

    return openreview.stages.MetaReviewStage(
        start_date = meta_review_start_date,
        due_date = meta_review_due_date,
        public = request_forum.content.get('make_meta_reviews_public', '').startswith('Yes'),
        release_to_authors = (request_forum.content.get('release_meta_reviews_to_authors', '').startswith('Yes')),
        release_to_reviewers = release_to_reviewers,
        additional_fields = meta_review_form_additional_options,
        remove_fields = meta_review_form_remove_options
    )

def get_decision_stage(request_forum):
    decision_start_date = request_forum.content.get('decision_start_date', '').strip()
    if decision_start_date:
        try:
            decision_start_date = datetime.datetime.strptime(decision_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            decision_start_date = datetime.datetime.strptime(decision_start_date, '%Y/%m/%d')
    else:
        decision_start_date = None

    decision_due_date = request_forum.content.get('decision_deadline', '').strip()
    if decision_due_date:
        try:
            decision_due_date = datetime.datetime.strptime(decision_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            decision_due_date = datetime.datetime.strptime(decision_due_date, '%Y/%m/%d')
    else:
        decision_due_date = None

    decision_options = request_forum.content.get('decision_options', '').strip()
    decision_form_additional_options = request_forum.content.get('additional_decision_form_options', {})

    if decision_options:
        decision_options = [s.translate(str.maketrans('', '', '"\'')).strip() for s in decision_options.split(',')]

    decisions_file = request_forum.content.get('decisions_file')

    return openreview.stages.DecisionStage(
        options = decision_options,
        start_date = decision_start_date,
        due_date = decision_due_date,
        public = request_forum.content.get('make_decisions_public', '').startswith('Yes'),
        release_to_authors = request_forum.content.get('release_decisions_to_authors', '').startswith('Yes'),
        release_to_reviewers = request_forum.content.get('release_decisions_to_reviewers', '').startswith('Yes'),
        release_to_area_chairs = request_forum.content.get('release_decisions_to_area_chairs', '').startswith('Yes'),
        email_authors = request_forum.content.get('notify_authors', '').startswith('Yes'),
        additional_fields=decision_form_additional_options,
        decisions_file=decisions_file
    )

def get_submission_revision_stage(request_forum):
    revision_name = request_forum.content.get('submission_revision_name', '').strip()
    if revision_name:
        revision_name = '_'.join(revision_name.title().split(' '))
    else:
        revision_name='Revision'
    submission_revision_start_date = request_forum.content.get('submission_revision_start_date', '').strip()
    if submission_revision_start_date:
        try:
            submission_revision_start_date = datetime.datetime.strptime(submission_revision_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_revision_start_date = datetime.datetime.strptime(submission_revision_start_date, '%Y/%m/%d')
    else:
        submission_revision_start_date = None

    submission_revision_due_date = request_forum.content.get('submission_revision_deadline', '').strip()
    if submission_revision_due_date:
        try:
            submission_revision_due_date = datetime.datetime.strptime(submission_revision_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_revision_due_date = datetime.datetime.strptime(submission_revision_due_date, '%Y/%m/%d')
    else:
        submission_revision_due_date = None

    submission_revision_additional_options = request_forum.content.get('submission_revision_additional_options', {})
    if isinstance(submission_revision_additional_options, str):
        submission_revision_additional_options = json.loads(submission_revision_additional_options.strip())

    submission_revision_remove_options = request_forum.content.get('submission_revision_remove_options', [])

    only_accepted = False
    if request_forum.content.get('accepted_submissions_only', '') == 'Enable revision for accepted submissions only':
        only_accepted = True

    allow_author_reorder = request_forum.content.get('submission_author_edition', '') == 'Allow reorder of existing authors only'

    return openreview.stages.SubmissionRevisionStage(
        name=revision_name,
        start_date=submission_revision_start_date,
        due_date=submission_revision_due_date,
        additional_fields=submission_revision_additional_options,
        remove_fields=submission_revision_remove_options,
        only_accepted=only_accepted,
        allow_author_reorder=allow_author_reorder)

def get_comment_stage(request_forum):

    commentary_start_date = request_forum.content.get('commentary_start_date', '').strip()
    if commentary_start_date:
        try:
            commentary_start_date = datetime.datetime.strptime(commentary_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            commentary_start_date = datetime.datetime.strptime(commentary_start_date, '%Y/%m/%d')
    else:
        commentary_start_date = None

    commentary_end_date = request_forum.content.get('commentary_end_date', '').strip()
    if commentary_end_date:
        try:
            commentary_end_date = datetime.datetime.strptime(commentary_end_date, '%Y/%m/%d %H:%M')
        except ValueError:
            commentary_end_date = datetime.datetime.strptime(commentary_end_date, '%Y/%m/%d')
    else:
        commentary_end_date = None

    participants = request_forum.content.get('participants', [])
    additional_readers = request_forum.content.get('additional_readers', [])
    anonymous = 'Public (anonymously)' in participants
    allow_public_comments = anonymous or 'Public (non-anonymously)' in participants

    invitees = []
    readers = []
    if 'Assigned Reviewers' in participants:
        invitees.append(openreview.stages.CommentStage.Readers.REVIEWERS_ASSIGNED)
        readers.append(openreview.stages.CommentStage.Readers.REVIEWERS_ASSIGNED)
    elif 'Assigned Reviewers' in additional_readers:
        readers.append(openreview.stages.CommentStage.Readers.REVIEWERS_ASSIGNED)

    if 'Assigned Submitted Reviewers' in participants:
        invitees.append(openreview.stages.CommentStage.Readers.REVIEWERS_SUBMITTED)
        readers.append(openreview.stages.CommentStage.Readers.REVIEWERS_SUBMITTED)
    elif 'Assigned Submitted Reviewers' in additional_readers:
        readers.append(openreview.stages.CommentStage.Readers.REVIEWERS_SUBMITTED)

    if 'Assigned Area Chairs' in participants:
        invitees.append(openreview.stages.CommentStage.Readers.AREA_CHAIRS_ASSIGNED)
        readers.append(openreview.stages.CommentStage.Readers.AREA_CHAIRS_ASSIGNED)
    elif 'Assigned Area Chairs' in additional_readers:
        readers.append(openreview.stages.CommentStage.Readers.AREA_CHAIRS_ASSIGNED)

    if 'Assigned Senior Area Chairs' in participants:
        invitees.append(openreview.stages.CommentStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED)
        readers.append(openreview.stages.CommentStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED)
    elif 'Assigned Senior Area Chairs' in additional_readers:
        readers.append(openreview.stages.CommentStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED)

    if 'Authors' in participants:
        invitees.append(openreview.stages.CommentStage.Readers.AUTHORS)
        readers.append(openreview.stages.CommentStage.Readers.AUTHORS)
    elif 'Authors' in additional_readers:
        readers.append(openreview.stages.CommentStage.Readers.AUTHORS)

    if 'Public' in additional_readers:
        readers.append(openreview.stages.CommentStage.Readers.EVERYONE)

    email_pcs = request_forum.content.get('email_program_chairs_about_official_comments', '') == 'Yes, email PCs for each official comment made in the venue'

    return openreview.stages.CommentStage(
        start_date=commentary_start_date,
        end_date=commentary_end_date,
        allow_public_comments=allow_public_comments,
        anonymous=anonymous,
        reader_selection=True,
        email_pcs=email_pcs,
        check_mandatory_readers=True,
        readers=readers,
        invitees=invitees
    )