from collections import defaultdict
import openreview
import datetime
import json

def get_venue(client, venue_note_id, support_user='OpenReview.net/Support', setup=False):
    
    note = client.get_note(venue_note_id)
    venue = openreview.venue.Venue(client, note.content['venue_id']['value'], support_user)
    venue.name = note.content['official_venue_name']['value']
    venue.short_name = note.content['abbreviated_venue_name']['value']
    venue.website = note.content['venue_website_url']['value']
    venue.contact = note.content['contact_email']['value']
    venue.location = note.content['location']['value']
    set_start_date(note, venue)
    venue.request_form_id = venue_note_id
    venue.use_area_chairs = 'Yes' in note.content.get('area_chairs_and_senior_area_chairs', {}).get('value','')
    venue.use_senior_area_chairs = note.content.get('area_chairs_and_senior_area_chairs', {}).get('value','') == 'Yes, our venue has Area Chairs and Senior Area Chairs'
    venue.use_secondary_area_chairs = note.content.get('secondary_area_chairs', {}).get('value','') == 'Yes, our venue has Secondary Area Chairs'
    venue.use_ethics_chairs = venue.use_ethics_reviewers = note.content.get('ethics_chairs_and_reviewers', {}).get('value', '') == 'Yes, our venue has Ethics Chairs and Reviewers'
    venue.use_publication_chairs = note.content.get('publication_chairs', {}).get('value', '') == 'Yes, our venue has Publication Chairs'
    
    set_initial_stages_v2(note, venue)
    venue.expertise_selection_stage = openreview.stages.ExpertiseSelectionStage(due_date = venue.submission_stage.due_date)
    if setup:
        venue.setup(note.content.get('program_chair_emails',{}).get('value'))
    return venue

def set_start_date(request_forum, venue):

    venue_start_date_str = 'TBD'
    venue_start_date = None
    start_date = request_forum.content.get('venue_start_date', {}).get('value', '').strip()
    if start_date:
        try:
            venue_start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            venue_start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d')
        venue_start_date_str = venue_start_date.strftime('%b %d %Y')

    venue.start_date = venue_start_date_str

def set_initial_stages_v2(request_forum, venue):

    readers_map = {
        'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)': [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.REVIEWERS],
        'All area chairs only': [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS],
        'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)': [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.REVIEWERS_ASSIGNED],
        'Program chairs and paper authors only': [],
        'Everyone (submissions are public)': [openreview.stages.SubmissionStage.Readers.EVERYONE],
        'Make accepted submissions public and hide rejected submissions': [openreview.stages.SubmissionStage.Readers.EVERYONE_BUT_REJECTED]
    }
    #readers = readers_map[request_forum.content.get('submission_readers', {}).get('value', [])]

    submission_start_date = request_forum.content.get('submission_start_date', {}).get('value', '').strip()

    submission_start_date_str = ''
    if submission_start_date:
        try:
            submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d')
        submission_start_date_str = submission_start_date.strftime('%b %d %Y %I:%M%p') + ' UTC-0'
    else:
        submission_start_date = None

    submission_deadline_str = 'TBD'
    abstract_due_date_str = ''
    submission_second_due_date = request_forum.content.get('submission_deadline', {}).get('value', '').strip()
    if submission_second_due_date:
        try:
            submission_second_due_date = datetime.datetime.strptime(submission_second_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_second_due_date = datetime.datetime.strptime(submission_second_due_date, '%Y/%m/%d')
        submission_deadline_str = submission_second_due_date.strftime('%b %d %Y %I:%M%p') + ' UTC-0'
        submission_due_date = request_forum.content.get('abstract_registration_deadline', {}).get('value', '').strip()
        if submission_due_date:
            try:
                submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d %H:%M')
            except ValueError:
                submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d')
            abstract_due_date_str = submission_due_date.strftime('%b %d %Y %I:%M%p') + ' UTC-0'
        else:
            submission_due_date = submission_second_due_date
            submission_second_due_date = None
    else:
        submission_second_due_date = submission_due_date = None

    date = 'Submission Start: ' + submission_start_date_str + ', ' if submission_start_date_str else ''
    if abstract_due_date_str:
        date += 'Abstract Registration: ' + abstract_due_date_str + ', '
    date += 'Submission Deadline: ' + submission_deadline_str
    venue.date = date

    venue.submission_stage =  openreview.stages.SubmissionStage(
        start_date=submission_start_date,
        due_date=submission_due_date,
        second_due_date=submission_second_due_date,
        #readers=readers,
        double_blind=request_forum.content.get('author_and_reviewer_anonymity', {}).get('value', '') == 'Double-blind',
        #email_pcs='Yes' in request_forum.content.get('email_pcs_for_new_submissions', {}).get('value', ''),
        #force_profiles='Yes' in request_forum.content.get('force_profiles_only', {}).get('value', '')
    )

    venue.review_stage = openreview.stages.ReviewStage(
        start_date = (submission_second_due_date if submission_second_due_date else submission_due_date) + datetime.timedelta(weeks=1),
        allow_de_anonymization = (request_forum.content.get('author_and_reviewer_anonymity', {}).get('value', 'No anonymity') == 'No anonymity'),
    )

def get_conference(client, request_form_id, support_user='OpenReview.net/Support', setup=False):

    note = client.get_note(request_form_id)
    if note.content.get('api_version') == '2':
        urls = openreview.tools.get_base_urls(client)
        openreview_client = openreview.api.OpenReviewClient(baseurl = urls[1], token=client.token)
        venue = openreview.venue.Venue(openreview_client, note.content['venue_id'], support_user)

        if note.content['venue_id'].startswith('aclweb.org/ACL/ARR'):
            venue = openreview.arr.ARR(openreview_client, note.content['venue_id'], support_user, venue=venue)

        venue_group = openreview.tools.get_group(openreview_client, note.content['venue_id'])
        venue_content = venue_group.content if venue_group and venue_group.content else {}
        
        ## Run test faster
        if 'openreview.net' in support_user:
            venue.invitation_builder.update_wait_time = 2000
            venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"

        venue.request_form_id = request_form_id
        venue.use_area_chairs = note.content.get('Area Chairs (Metareviewers)', '') == 'Yes, our venue has Area Chairs'
        venue.use_senior_area_chairs = note.content.get('senior_area_chairs') == 'Yes, our venue has Senior Area Chairs'
        venue.use_secondary_area_chairs = note.content.get('secondary_area_chairs') == 'Yes, our venue has Secondary Area Chairs'
        venue.use_ethics_chairs = note.content.get('ethics_chairs_and_reviewers') == 'Yes, our venue has Ethics Chairs and Reviewers'
        venue.use_ethics_reviewers = note.content.get('ethics_chairs_and_reviewers') == 'Yes, our venue has Ethics Chairs and Reviewers'
        venue.use_publication_chairs = note.content.get('publication_chairs', 'No, our venue does not have Publication Chairs') == 'Yes, our venue has Publication Chairs'
        venue.automatic_reviewer_assignment = note.content.get('submission_reviewer_assignment', '') == 'Automatic'
        venue.senior_area_chair_roles = note.content.get('senior_area_chair_roles', ['Senior_Area_Chairs'])
        venue.senior_area_chairs_name = venue.senior_area_chair_roles[0]
        venue.area_chair_roles = note.content.get('area_chair_roles', ['Area_Chairs'])
        venue.area_chairs_name = venue.area_chair_roles[0]
        venue.reviewer_roles = note.content.get('reviewer_roles', ['Reviewers'])
        venue.reviewers_name = venue.reviewer_roles[0]
        venue.allow_gurobi_solver = venue_content.get('allow_gurobi_solver', {}).get('value', False)
        venue.submission_license = note.content.get('submission_license', ['CC BY 4.0'])
        set_homepage_options(note, venue)
        venue.reviewer_identity_readers = get_identity_readers(note, 'reviewer_identity')
        venue.area_chair_identity_readers = get_identity_readers(note, 'area_chair_identity')
        venue.senior_area_chair_identity_readers = get_identity_readers(note, 'senior_area_chair_identity')
        venue.decision_heading_map = get_decision_heading_map(venue.short_name, note, venue_content.get('accept_decision_options', {}).get('value', []))
        venue.source_submissions_query_mapping = note.content.get('source_submissions_query_mapping', {})
        venue.sac_paper_assignments = note.content.get('senior_area_chairs_assignment', 'Area Chairs') == 'Submissions'
        venue.submission_assignment_max_reviewers = int(note.content.get('submission_assignment_max_reviewers')) if note.content.get('submission_assignment_max_reviewers') is not None else None
        venue.preferred_emails_groups = note.content.get('preferred_emails_groups', [])
        venue.iThenticate_plagiarism_check = note.content.get('iThenticate_plagiarism_check', 'No') == 'Yes'
        venue.iThenticate_plagiarism_check_api_key = note.content.get('iThenticate_plagiarism_check_api_key', '')
        venue.iThenticate_plagiarism_check_api_base_url = note.content.get('iThenticate_plagiarism_check_api_base_url', '')
        venue.iThenticate_plagiarism_check_committee_readers = note.content.get('iThenticate_plagiarism_check_committee_readers', '')

        venue.submission_stage = get_submission_stage(note, venue)
        venue.review_stage = get_review_stage(note)
        if 'bid_due_date' in note.content:
            venue.bid_stages = get_bid_stages(note, reviewers_id=venue.get_reviewers_id(), area_chairs_id=venue.get_area_chairs_id(), senior_area_chairs_id=venue.get_senior_area_chairs_id())
        venue.meta_review_stage = get_meta_review_stage(note)
        venue.comment_stage = get_comment_stage(note)
        venue.decision_stage = get_decision_stage(note)
        venue.submission_revision_stage = get_submission_revision_stage(note)
        venue.review_rebuttal_stage = get_rebuttal_stage(note)
        venue.registration_stages = get_registration_stages(note, venue)
        if 'ethics_review_deadline' in note.content:
            venue.ethics_review_stage = get_ethics_review_stage(note)
        venue.custom_stage = get_review_rating_stage(note)

        include_expertise_selection = note.content.get('include_expertise_selection', '') == 'Yes'
        venue.expertise_selection_stage = openreview.stages.ExpertiseSelectionStage(due_date = venue.submission_stage.due_date, include_option=include_expertise_selection)

        if isinstance(venue, openreview.arr.ARR):
            venue.copy_to_venue()

        if setup:
            venue.setup(note.content.get('program_chair_emails'), note.content.get('publication_chairs_emails'))
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

    if note.content.get('secondary_area_chairs') == 'Yes, our venue has Secondary Area Chairs':
        builder.has_secondary_area_chairs(True)

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
    email_pcs_on_desk_reject = 'Yes' in note.content.get('email_pcs_for_desk_rejected_submissions', '')
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

    force_profiles = 'Yes' in note.content.get('force_profiles_only', '')

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
        email_pcs_on_desk_reject=email_pcs_on_desk_reject,
        author_names_revealed=author_names_revealed,
        papers_released=papers_released,
        readers=readers,
        author_reorder_after_first_deadline=author_reorder_after_first_deadline,
        submission_email=submission_email,
        force_profiles=force_profiles)

    include_expertise_selection = note.content.get('include_expertise_selection', '') == 'Yes'
    builder.set_expertise_selection_stage(due_date=submission_due_date, include_option=include_expertise_selection)

    paper_matching_options = note.content.get('Paper Matching', [])
    
    if not paper_matching_options or 'Organizers will assign papers manually' in paper_matching_options or 'Manual' in note.content.get('submission_reviewer_assignment', ''):
        builder.enable_reviewer_reassignment(enable=True)

    ## Contact Emails is deprecated
    program_chair_ids = note.content.get('Contact Emails', []) + note.content.get('program_chair_emails', [])
    builder.set_conference_program_chairs_ids(program_chair_ids)
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
    builder.set_review_rebuttal_stage(get_rebuttal_stage(note))
    builder.set_ethics_review_stage(get_ethics_review_stage(note))
    builder.set_bid_stages(get_bid_stages(note, reviewers_id=builder.conference.get_reviewers_id(), area_chairs_id=builder.conference.get_area_chairs_id(), senior_area_chairs_id=builder.conference.get_senior_area_chairs_id()))
    builder.set_meta_review_stage(get_meta_review_stage(note))
    builder.set_comment_stage(get_comment_stage(note))
    builder.set_decision_stage(get_decision_stage(note))
    builder.set_submission_revision_stage(get_submission_revision_stage(note))

    decision_heading_map = note.content.get('home_page_tab_names')
    if decision_heading_map:
        builder.set_homepage_layout('decisions')
        builder.set_venue_heading_map(decision_heading_map)

    return builder

def set_homepage_options(request_forum, venue):
    homepage_override = request_forum.content.get('homepage_override', {})
    venue.name = homepage_override.get('title', request_forum.content.get('Official Venue Name'))  
    venue.short_name = homepage_override.get('subtitle', request_forum.content.get('Abbreviated Venue Name'))
    venue.website = homepage_override.get('website', request_forum.content.get('Official Website URL'))
    venue.contact = homepage_override.get('contact', request_forum.content.get('contact_email'))
    venue.location = homepage_override.get('location', request_forum.content.get('Location'))
    venue.instructions = homepage_override.get('instructions', '')

    venue_start_date_str = 'TBD'
    venue_start_date = None
    start_date = request_forum.content.get('Venue Start Date', '').strip()
    if start_date:
        try:
            venue_start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            venue_start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d')
        venue_start_date_str = venue_start_date.strftime('%b %d %Y')

    venue.start_date = venue_start_date_str

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

def get_decision_heading_map(short_name, request_forum, accept_options):
    map = request_forum.content.get('home_page_tab_names', {})
    decision_heading_map = {}
    for decision, tabName in map.items():
        decision_heading_map[openreview.tools.decision_to_venue(short_name, decision, accept_options)] = tabName

    return decision_heading_map

def get_submission_stage(request_forum, venue):

    name = request_forum.content.get('submission_name', 'Submission').strip()
    double_blind = (request_forum.content.get('Author and Reviewer Anonymity', '') == 'Double-blind')

    readers_map = {
        'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)': [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.REVIEWERS],
        'All area chairs only': [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS],
        'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)': [openreview.stages.SubmissionStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.AREA_CHAIRS_ASSIGNED, openreview.stages.SubmissionStage.Readers.REVIEWERS_ASSIGNED],
        'Program chairs and paper authors only': [],
        'Everyone (submissions are public)': [openreview.stages.SubmissionStage.Readers.EVERYONE],
        'Make accepted submissions public and hide rejected submissions': [openreview.stages.SubmissionStage.Readers.EVERYONE_BUT_REJECTED]
    }

    # Prioritize submission_readers over Open Reviewing Policy (because PCs can keep changing this)
    readers = readers_map[request_forum.content.get('submission_readers', [])]
    public = 'Everyone (submissions are public)' in readers

    submission_start_date = request_forum.content.get('Submission Start Date', '').strip()
    submission_start_date_str = ''
    if submission_start_date:
        try:
            submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_start_date = datetime.datetime.strptime(submission_start_date, '%Y/%m/%d')
        submission_start_date_str = submission_start_date.strftime('%b %d %Y %I:%M%p') + ' UTC-0'
    else:
        submission_start_date = None
        
    submission_deadline_str = 'TBD'
    abstract_due_date_str = ''
    submission_second_due_date = request_forum.content.get('Submission Deadline', '').strip()
    if submission_second_due_date:
        try:
            submission_second_due_date = datetime.datetime.strptime(submission_second_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            submission_second_due_date = datetime.datetime.strptime(submission_second_due_date, '%Y/%m/%d')
        submission_deadline_str = submission_second_due_date.strftime('%b %d %Y %I:%M%p') + ' UTC-0'
        submission_due_date = request_forum.content.get('abstract_registration_deadline', '').strip()
        if submission_due_date:
            try:
                submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d %H:%M')
            except ValueError:
                submission_due_date = datetime.datetime.strptime(submission_due_date, '%Y/%m/%d')
            abstract_due_date_str = submission_due_date.strftime('%b %d %Y %I:%M%p') + ' UTC-0'
        else:
            submission_due_date = submission_second_due_date
            submission_second_due_date = None
    else:
        submission_second_due_date = submission_due_date = None

    date = 'Submission Start: ' + submission_start_date_str + ', ' if submission_start_date_str else ''
    if abstract_due_date_str:
        date += 'Abstract Registration: ' + abstract_due_date_str + ', '
    date += 'Submission Deadline: ' + submission_deadline_str
    venue.date = date

    submission_additional_options = request_forum.content.get('Additional Submission Options', {})
    if isinstance(submission_additional_options, str):
        submission_additional_options = json.loads(submission_additional_options.strip())

    subject_areas = None
    if 'subject_areas' in submission_additional_options and 'value' in submission_additional_options['subject_areas']:
        subject_areas = submission_additional_options['subject_areas']['value'].get('param', {}).get('enum')

    submission_remove_options = request_forum.content.get('remove_submission_options', [])
    submission_release=(request_forum.content.get('submissions_visibility', '') == 'Yes, submissions should be immediately revealed to the public.')
    create_groups=(not double_blind) and public and submission_release

    author_names_revealed = 'Reveal author identities of all submissions to the public' in request_forum.content.get('reveal_authors', '') or 'Reveal author identities of only accepted submissions to the public' in request_forum.content.get('reveal_authors', '')
    papers_released = 'Release all submissions to the public'in request_forum.content.get('release_submissions', '') or 'Release only accepted submission to the public' in request_forum.content.get('release_submissions', '') or 'Make accepted submissions public and hide rejected submissions' in request_forum.content.get('submission_readers', '')

    email_pcs = 'Yes' in request_forum.content.get('email_pcs_for_new_submissions', '')
    submission_email = request_forum.content.get('submission_email', None)
    hide_fields = request_forum.content.get('hide_fields', [])
    force_profiles = 'Yes' in request_forum.content.get('force_profiles_only', '')

    author_reorder_map = {
        'Yes': openreview.stages.AuthorReorder.ALLOW_REORDER,
        'No': openreview.stages.AuthorReorder.ALLOW_EDIT,
        'Do not allow any changes to author lists': openreview.stages.AuthorReorder.DISALLOW_EDIT
    }
    author_reorder_after_first_deadline = author_reorder_map[request_forum.content.get('submission_deadline_author_reorder', 'No')]
    email_pcs_on_withdraw = 'Yes' in request_forum.content.get('email_pcs_for_withdrawn_submissions', '')
    email_pcs_on_desk_reject = 'Yes' in request_forum.content.get('email_pcs_for_desk_rejected_submissions', '')

    second_deadline_additional_fields = request_forum.content.get('second_deadline_additional_options', {})
    if isinstance(second_deadline_additional_fields, str):
        second_deadline_additional_fields = json.loads(second_deadline_additional_fields.strip())

    second_deadline_remove_fields = request_forum.content.get('second_deadline_remove_options', [])

    withdraw_submission_exp_date = request_forum.content.get('withdraw_submission_expiration', '').strip()
    if withdraw_submission_exp_date:
        try:
            withdraw_submission_exp_date = datetime.datetime.strptime(withdraw_submission_exp_date, '%Y/%m/%d %H:%M')
        except ValueError:
            withdraw_submission_exp_date = datetime.datetime.strptime(withdraw_submission_exp_date, '%Y/%m/%d')
    else:
        withdraw_submission_exp_date = None

    withdrawn_submission_public = 'Yes' in request_forum.content.get('withdrawn_submissions_visibility', '')
    desk_rejected_submission_public = 'Yes' in request_forum.content.get('desk_rejected_submissions_visibility', '')
    withdrawn_submission_reveal_authors = 'Yes' in request_forum.content.get('withdrawn_submissions_author_anonymity', '')
    desk_rejected_submission_reveal_authors = 'Yes' in request_forum.content.get('desk_rejected_submissions_author_anonymity', '')
    commitments_venue = request_forum.content.get('commitments_venue', 'No') == 'Yes'

    return openreview.stages.SubmissionStage(name = name,
        double_blind=double_blind,
        start_date=submission_start_date,
        due_date=submission_due_date,
        second_due_date=submission_second_due_date,
        additional_fields=submission_additional_options,
        remove_fields=submission_remove_options,
        hide_fields=hide_fields,
        subject_areas=subject_areas,
        create_groups=create_groups,
        withdraw_submission_exp_date=withdraw_submission_exp_date,
        withdrawn_submission_public=withdrawn_submission_public,
        withdrawn_submission_reveal_authors=withdrawn_submission_reveal_authors,
        desk_rejected_submission_public=desk_rejected_submission_public,
        desk_rejected_submission_reveal_authors=desk_rejected_submission_reveal_authors,
        author_names_revealed=author_names_revealed,
        papers_released=papers_released,
        readers=readers,
        email_pcs=email_pcs,
        email_pcs_on_withdraw=email_pcs_on_withdraw,
        email_pcs_on_desk_reject=email_pcs_on_desk_reject,
        author_reorder_after_first_deadline = author_reorder_after_first_deadline,
        submission_email=submission_email,
        force_profiles=force_profiles,
        second_deadline_additional_fields=second_deadline_additional_fields,
        second_deadline_remove_fields=second_deadline_remove_fields,
        commitments_venue=commitments_venue)

def get_bid_stages(request_forum, reviewers_id=None, area_chairs_id=None, senior_area_chairs_id=None):
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

    reviewer_bid_stage = openreview.stages.BidStage(reviewers_id, start_date = bid_start_date, due_date = bid_due_date, request_count = int(request_forum.content.get('bid_count', 50)))
    bid_stages = [reviewer_bid_stage]

    if 'Yes, our venue has Area Chairs' in request_forum.content.get('Area Chairs (Metareviewers)', ''):
        ac_bid_stage = openreview.stages.BidStage(area_chairs_id, start_date = bid_start_date, due_date = bid_due_date, request_count = int(request_forum.content.get('bid_count', 50)))
        bid_stages.append(ac_bid_stage)

    if 'Yes, our venue has Senior Area Chairs' in request_forum.content.get('senior_area_chairs', '') and 'Yes' in request_forum.content.get('sac_bidding', ''):
        sac_bid_stage = openreview.stages.BidStage(senior_area_chairs_id, start_date = bid_start_date, due_date = bid_due_date, request_count = int(request_forum.content.get('bid_count', 50)))
        bid_stages.append(sac_bid_stage)

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

    review_exp_date = request_forum.content.get('review_expiration_date', '').strip()
    if review_exp_date:
        try:
            review_exp_date = datetime.datetime.strptime(review_exp_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_exp_date = datetime.datetime.strptime(review_exp_date, '%Y/%m/%d')
    else:
        review_exp_date = None

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
        name = request_forum.content.get('review_name', 'Official_Review').strip(),
        child_invitations_name = request_forum.content.get('review_name', 'Official_Review').strip(),
        start_date = review_start_date,
        due_date = review_due_date,
        exp_date = review_exp_date,
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

def get_rebuttal_stage(request_forum):
    rebuttal_start_date = request_forum.content.get('rebuttal_start_date', '').strip()
    if rebuttal_start_date:
        try:
            rebuttal_start_date = datetime.datetime.strptime(rebuttal_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            rebuttal_start_date = datetime.datetime.strptime(rebuttal_start_date, '%Y/%m/%d')
    else:
        rebuttal_start_date = None

    rebuttal_due_date = request_forum.content.get('rebuttal_deadline', '').strip()
    if rebuttal_due_date:
        try:
            rebuttal_due_date = datetime.datetime.strptime(rebuttal_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            rebuttal_due_date = datetime.datetime.strptime(rebuttal_due_date, '%Y/%m/%d')
    else:
        rebuttal_due_date = None

    rebuttal_form_additional_options = request_forum.content.get('additional_rebuttal_form_options', {})

    single_rebuttal = 'One author rebuttal per paper' == request_forum.content.get('number_of_rebuttals')
    unlimited_rebuttal = 'Multiple author rebuttals per paper' == request_forum.content.get('number_of_rebuttals')

    rebuttal_readers = request_forum.content.get('rebuttal_readers', [])
    readers = []
    if 'All Senior Area Chairs' in rebuttal_readers:
        readers.append(openreview.stages.ReviewRebuttalStage.Readers.SENIOR_AREA_CHAIRS)
    if 'Assigned Senior Area Chairs' in rebuttal_readers:
        readers.append(openreview.stages.ReviewRebuttalStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED)

    if 'All Area Chairs' in rebuttal_readers:
        readers.append(openreview.stages.ReviewRebuttalStage.Readers.AREA_CHAIRS)
    if 'Assigned Area Chairs' in rebuttal_readers:
        readers.append(openreview.stages.ReviewRebuttalStage.Readers.AREA_CHAIRS_ASSIGNED)

    if 'All Reviewers' in rebuttal_readers:
        readers.append(openreview.stages.ReviewRebuttalStage.Readers.REVIEWERS)
    if 'Assigned Reviewers' in rebuttal_readers:
        readers.append(openreview.stages.ReviewRebuttalStage.Readers.REVIEWERS_ASSIGNED)
    if 'Assigned Reviewers who already submitted their review' in rebuttal_readers:
        readers.append(openreview.stages.ReviewRebuttalStage.Readers.REVIEWERS_SUBMITTED)

    if 'Everyone' in rebuttal_readers:
        readers = [openreview.stages.ReviewRebuttalStage.Readers.EVERYONE]

    email_pcs = 'Yes' in request_forum.content.get('email_program_chairs_about_rebuttals', '')

    return openreview.stages.ReviewRebuttalStage(
        start_date = rebuttal_start_date,
        due_date = rebuttal_due_date,
        email_pcs = email_pcs,
        additional_fields = rebuttal_form_additional_options,
        single_rebuttal = single_rebuttal,
        unlimited_rebuttals = unlimited_rebuttal,
        readers = readers
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

    review_exp_date = request_forum.content.get('ethics_review_expiration_date', '').strip()
    if review_exp_date:
        try:
            review_exp_date = datetime.datetime.strptime(review_exp_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_exp_date = datetime.datetime.strptime(review_exp_date, '%Y/%m/%d')
    else:
        review_exp_date = None

    review_form_additional_options = request_forum.content.get('additional_ethics_review_form_options', {})

    review_form_remove_options = request_forum.content.get('remove_ethics_review_form_options', '').replace(',', ' ').split()

    readers_map = {
        'Ethics reviews should be immediately revealed to all reviewers and ethics reviewers': openreview.stages.EthicsReviewStage.Readers.ALL_COMMITTEE,
        'Ethics reviews should be immediately revealed to the paper\'s reviewers and ethics reviewers': openreview.stages.EthicsReviewStage.Readers.ALL_ASSIGNED_COMMITTEE,
        'Ethics reviews should be immediately revealed to the paper\'s ethics reviewers': openreview.stages.EthicsReviewStage.Readers.ASSIGNED_ETHICS_REVIEWERS,
        'Ethics reviews should be immediately revealed to the paper\'s ethics reviewers who have already submitted their ethics review': openreview.stages.EthicsReviewStage.Readers.ETHICS_REVIEWERS_SUBMITTED,
        'Ethics Review should not be revealed to any reviewer, except to the author of the ethics review': openreview.stages.EthicsReviewStage.Readers.ETHICS_REVIEWER_SIGNATURE
    }
    release_to_reviewers = readers_map.get(request_forum.content.get('release_ethics_reviews_to_reviewers', ''), openreview.stages.EthicsReviewStage.Readers.ETHICS_REVIEWER_SIGNATURE)

    flagged_submissions = []
    if request_forum.content.get('ethics_review_submissions'):
        flagged_submissions = [int(number) for number in request_forum.content['ethics_review_submissions'].split(',')]

    compute_affinity_scores = False if request_forum.content.get('compute_affinity_scores', 'No') == 'No' else request_forum.content.get('compute_affinity_scores')

    return openreview.stages.EthicsReviewStage(
        start_date = review_start_date,
        due_date = review_due_date,
        exp_date = review_exp_date,
        release_to_public = (request_forum.content.get('make_ethics_reviews_public', None) == 'Yes, ethics reviews should be revealed publicly when they are posted'),
        release_to_authors = (request_forum.content.get('release_ethics_reviews_to_authors', '').startswith('Yes')),
        release_to_reviewers = release_to_reviewers,
        additional_fields = review_form_additional_options,
        remove_fields = review_form_remove_options,
        submission_numbers = flagged_submissions,
        enable_comments = (request_forum.content.get('enable_comments_for_ethics_reviewers', '').startswith('Yes')),
        release_to_chairs = (request_forum.content.get('release_submissions_to_ethics_chairs', '').startswith('Yes')),
        compute_affinity_scores = compute_affinity_scores
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

    metareview_exp_date = request_forum.content.get('meta_review_expiration_date', '').strip()
    if metareview_exp_date:
        try:
            metareview_exp_date = datetime.datetime.strptime(metareview_exp_date, '%Y/%m/%d %H:%M')
        except ValueError:
            metareview_exp_date = datetime.datetime.strptime(metareview_exp_date, '%Y/%m/%d')
    else:
        metareview_exp_date = None

    meta_review_form_additional_options = request_forum.content.get('additional_meta_review_form_options', {})
    options = request_forum.content.get('recommendation_options', '').strip()
    if options: #to keep backward compatibility
        if request_forum.content.get('api_version') == '2':
            if 'recommendation' in meta_review_form_additional_options and 'enum' in meta_review_form_additional_options['recommendation']['value']['param']:
                meta_review_form_additional_options['recommendation']['value']['param']['enum'] = [s.translate(str.maketrans('', '', '"\'')).strip() for s in options.split(',')]
            else:
                meta_review_form_additional_options['recommendation'] = {
                    'value': {
                        'param': {
                            'type': 'string',
                            'enum': [s.translate(str.maketrans('', '', '"\'')).strip() for s in options.split(',')]
                        }
                    }
                }
        else:
            if 'recommendation' in meta_review_form_additional_options and 'value-dropdown' in meta_review_form_additional_options['recommendation']:
                meta_review_form_additional_options['recommendation']['value-dropdown'] = [s.translate(str.maketrans('', '', '"\'')).strip() for s in options.split(',')]
            else:
                meta_review_form_additional_options['recommendation'] = {
                    'value-dropdown':[s.translate(str.maketrans('', '', '"\'')).strip() for s in options.split(',')],
                    'required': True
                }

    meta_review_form_remove_options = request_forum.content.get('remove_meta_review_form_options', [])

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
        exp_date = metareview_exp_date,
        public = request_forum.content.get('make_meta_reviews_public', '').startswith('Yes'),
        release_to_authors = (request_forum.content.get('release_meta_reviews_to_authors', '').startswith('Yes')),
        release_to_reviewers = release_to_reviewers,
        recommendation_field_name=request_forum.content.get('recommendation_field_name', 'recommendation'),
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
    accept_decision_options = request_forum.content.get('accept_decision_options', '').strip()
    decision_form_additional_options = request_forum.content.get('additional_decision_form_options', {})

    if decision_options:
        decision_options = [s.translate(str.maketrans('', '', '"\'')).strip() for s in decision_options.split(',')]

    if accept_decision_options:
        accept_decision_options = [s.translate(str.maketrans('', '', '"\'')).strip() for s in accept_decision_options.split(',')]

    decisions_file = request_forum.content.get('decisions_file')

    return openreview.stages.DecisionStage(
        options = decision_options,
        accept_options = accept_decision_options,
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

    author_reorder_map = {
        'Allow reorder of existing authors only': openreview.stages.AuthorReorder.ALLOW_REORDER,
        'Allow addition and removal of authors': openreview.stages.AuthorReorder.ALLOW_EDIT,
        'Do not allow any changes to author lists': openreview.stages.AuthorReorder.DISALLOW_EDIT
    }
    allow_author_reorder = author_reorder_map[request_forum.content.get('submission_author_edition', 'Allow addition and removal of authors')]

    if request_forum.content.get('api_version', '1') == '1':
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
    email_sacs = request_forum.content.get('email_senior_area_chairs_about_official_comments', '') == 'Yes, email SACs for each official comment made in the venue'

    enable_chat = request_forum.content.get('enable_chat_between_committee_members', '') == 'Yes, enable chat between committee members'

    return openreview.stages.CommentStage(
        start_date=commentary_start_date,
        end_date=commentary_end_date,
        allow_public_comments=allow_public_comments,
        anonymous=anonymous,
        reader_selection=True,
        email_pcs=email_pcs,
        email_sacs=email_sacs,
        check_mandatory_readers=True,
        readers=readers,
        invitees=invitees,
        enable_chat=enable_chat
    )

def get_registration_stages(request_forum, venue):

    def get_reviewer_registration_stage(request_forum, venue):
        start_date = request_forum.content.get('reviewer_registration_start_date', '').strip()
        if start_date:
            try:
                start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d %H:%M')
            except ValueError:
                start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d')
        else:
            start_date = None

        end_date = request_forum.content.get('reviewer_registration_deadline', '').strip()
        if end_date:
            try:
                end_date = datetime.datetime.strptime(end_date, '%Y/%m/%d %H:%M')
            except ValueError:
                end_date = datetime.datetime.strptime(end_date, '%Y/%m/%d')
        else:
            end_date = None

        exp_date = request_forum.content.get('reviewer_registration_expiration_date', '').strip()
        if exp_date:
            try:
                exp_date = datetime.datetime.strptime(exp_date, '%Y/%m/%d %H:%M')
            except ValueError:
                exp_date = datetime.datetime.strptime(exp_date, '%Y/%m/%d')
        else:
            exp_date = None

        name = request_forum.content.get('reviewer_registration_name')
        title = request_forum.content.get('reviewer_form_title')
        instructions = request_forum.content.get('reviewer_form_instructions')
        additional_options = request_forum.content.get('additional_reviewer_form_options', {})
        remove_fields = request_forum.content.get('remove_reviewer_form_options', [])

        return openreview.stages.RegistrationStage(
            committee_id=venue.get_reviewers_id(),
            name=name,
            start_date=start_date,
            due_date=end_date,
            expdate=exp_date,
            title=title,
            instructions=instructions,
            additional_fields=additional_options,
            remove_fields=remove_fields
        )

    def get_ac_registration_stage(request_forum, venue):
    
        start_date = request_forum.content.get('AC_registration_start_date', '').strip()
        if start_date:
            try:
                start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d %H:%M')
            except ValueError:
                start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d')
        else:
            start_date = None

        end_date = request_forum.content.get('AC_registration_deadline', '').strip()
        if end_date:
            try:
                end_date = datetime.datetime.strptime(end_date, '%Y/%m/%d %H:%M')
            except ValueError:
                end_date = datetime.datetime.strptime(end_date, '%Y/%m/%d')
        else:
            end_date = None

        exp_date = request_forum.content.get('AC_registration_expiration_date', '').strip()
        if exp_date:
            try:
                exp_date = datetime.datetime.strptime(exp_date, '%Y/%m/%d %H:%M')
            except ValueError:
                exp_date = datetime.datetime.strptime(exp_date, '%Y/%m/%d')
        else:
            exp_date = None

        name = request_forum.content.get('AC_registration_name')
        title = request_forum.content.get('AC_form_title')
        instructions = request_forum.content.get('AC_form_instructions')
        additional_options = request_forum.content.get('additional_AC_form_options', {})
        remove_fields = request_forum.content.get('remove_AC_form_options', [])

        return openreview.stages.RegistrationStage(
            committee_id=venue.get_area_chairs_id(),
            name=name,
            start_date=start_date,
            due_date=end_date,
            expdate=exp_date,
            title=title,
            instructions=instructions,
            additional_fields=additional_options,
            remove_fields=remove_fields
        )
    stages = []
    if 'reviewer_form_title' in request_forum.content:
        stages.append(get_reviewer_registration_stage(request_forum, venue))
    if 'Yes' in request_forum.content.get('Area Chairs (Metareviewers)') and 'AC_form_title' in request_forum.content:
        stages.append(get_ac_registration_stage(request_forum, venue))
    return stages

def get_review_rating_stage(request_forum):

    review_rating_start_date = request_forum.content.get('review_ratingstart_date', '').strip()
    if review_rating_start_date:
        try:
            review_rating_start_date = datetime.datetime.strptime(review_rating_start_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_rating_start_date = datetime.datetime.strptime(review_rating_start_date, '%Y/%m/%d')
    else:
        review_rating_start_date = None

    review_rating_due_date = request_forum.content.get('review_rating_deadline', '').strip()
    if review_rating_due_date:
        try:
            review_rating_due_date = datetime.datetime.strptime(review_rating_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_rating_due_date = datetime.datetime.strptime(review_rating_due_date, '%Y/%m/%d')
    else:
        review_rating_due_date = None

    review_rating_exp_date = request_forum.content.get('review_rating_expiration_date', '').strip()
    if review_rating_exp_date:
        try:
            review_rating_exp_date = datetime.datetime.strptime(review_rating_exp_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_rating_exp_date = datetime.datetime.strptime(review_rating_exp_date, '%Y/%m/%d')
    else:
        review_rating_exp_date = None

    readers = [openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED] if 'Yes' in request_forum.content.get('release_to_senior_area_chairs', 'No') else [openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED]

    default_content = {
        'review_quality': {
            'order': 1,
            'description': 'How helpful is this review?',
            'value': {
                'param': {
                    'type': 'integer',
                    'input': 'radio',
                    'enum': [
                        {'value': 0, 'description': '0: below expectations'},
                        {'value': 1, 'description': '1: meets expectations'},
                        {'value': 2, 'description': '2: exceeds expectations'}
                    ]
                }
            }
        }
    }
    content = request_forum.content.get('review_rating_form_options', default_content)

    return openreview.stages.CustomStage(name='Rating',
        reply_to=openreview.stages.CustomStage.ReplyTo.REVIEWS,
        source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
        reply_type=openreview.stages.CustomStage.ReplyType.REPLY,
        start_date=review_rating_start_date,
        due_date=review_rating_due_date,
        exp_date=review_rating_exp_date,
        invitees=[openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED],
        readers=readers,
        content=content)