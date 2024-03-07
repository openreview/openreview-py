def process(client, invitation):

    from openreview.stages.arr_content import (
        arr_registration_task_forum,
        arr_registration_task,
        arr_content_license_task_forum,
        arr_content_license_task,
        arr_max_load_task_forum,
        arr_reviewer_max_load_task,
        arr_ac_max_load_task,
        arr_sac_max_load_task,
        arr_reviewer_checklist,
        arr_ae_checklist,
        arr_desk_reject_verification
    )
    from openreview.venue import matching
    from datetime import datetime

    def fetch_date(field_name):
        value = invitation.content.get(field_name, {}).get('value')
        if value == 0:
            return None
        return value

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    request_form_id = domain.content['request_form_id']['value']

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    request_form = client_v1.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue_stage_invitations = client_v1.get_all_invitations(regex=f"{support_group}/-/Request{request_form.number}.*")
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)
    invitation_builder = openreview.arr.InvitationBuilder(venue)
    venue_stage_invitations = [i for i in venue_stage_invitations if '/Revision' in i.id]
    for venue_invitation in venue_stage_invitations:
        venue_invitation.process = invitation_builder.get_process_content('process/revisionProcess.py')
        client_v1.post_invitation(venue_invitation)

    print([i.id for i in venue_stage_invitations]) # We use: review, meta-review, comment, revision, ethics review, rev/ac registration, 

    overall_exp = fetch_date('form_expiration_date') / 1000
    max_load_due = fetch_date('maximum_load_due_date') / 1000
    max_load_exp = (overall_exp if fetch_date('maximum_load_exp_date') is None else fetch_date('maximum_load_exp_date')) / 1000
    reviewer_checklist_due = fetch_date('reviewer_checklist_due_date')
    reviewer_checklist_exp = fetch_date('reviewer_checklist_exp_date')
    ae_checklist_due = fetch_date('ae_checklist_due_date')
    ae_checklist_exp = fetch_date('ae_checklist_exp_date')

    registration_name = 'Registration'
    max_load_name = 'Max_Load_And_Unavailability_Request'

    # Build Reviewer Tasks
    venue.registration_stages.append(
        openreview.stages.RegistrationStage(committee_id = venue.get_reviewers_id(),
        name = registration_name,
        start_date = None,
        expdate = datetime.fromtimestamp(overall_exp),
        instructions = arr_registration_task_forum['instructions'],
        title = venue.get_reviewers_name() + ' ' + arr_registration_task_forum['title'],
        additional_fields=arr_registration_task)
    )
    venue.registration_stages.append(
        openreview.stages.RegistrationStage(committee_id = venue.get_reviewers_id(),
        name = max_load_name,
        start_date = None,
        due_date = datetime.fromtimestamp(max_load_due),
        expdate = datetime.fromtimestamp(max_load_exp),
        instructions = arr_max_load_task_forum['instructions'],
        title = venue.get_reviewers_name() + ' ' + arr_max_load_task_forum['title'],
        additional_fields=arr_reviewer_max_load_task,
        remove_fields=['profile_confirmed', 'expertise_confirmed'])
    )
    venue.registration_stages.append(
        openreview.stages.RegistrationStage(committee_id = venue.get_reviewers_id(),
        name = 'License_Agreement',
        start_date = None,
        expdate = datetime.fromtimestamp(overall_exp),
        instructions = arr_content_license_task_forum['instructions'],
        title = arr_content_license_task_forum['title'],
        additional_fields=arr_content_license_task,
        remove_fields=['profile_confirmed', 'expertise_confirmed'])
    )

    # Build AC Tasks
    venue.registration_stages.append(
        openreview.stages.RegistrationStage(committee_id = venue.get_area_chairs_id(),
        name = registration_name,
        start_date = None,
        expdate = datetime.fromtimestamp(overall_exp),
        instructions = arr_registration_task_forum['instructions'],
        title = venue.get_area_chairs_name() + ' ' + arr_registration_task_forum['title'],
        additional_fields=arr_registration_task)
    )
    venue.registration_stages.append(
        openreview.stages.RegistrationStage(committee_id = venue.get_area_chairs_id(),
        name = max_load_name,
        start_date = None,
        due_date = datetime.fromtimestamp(max_load_due),
        expdate = datetime.fromtimestamp(max_load_exp),
        instructions = arr_max_load_task_forum['instructions'],
        title = venue.get_area_chairs_name() + ' ' + arr_max_load_task_forum['title'],
        additional_fields=arr_ac_max_load_task,
        remove_fields=['profile_confirmed', 'expertise_confirmed'])
    )

    # Build SAC Tasks
    venue.registration_stages.append(
        openreview.stages.RegistrationStage(committee_id = venue.get_senior_area_chairs_id(),
        name = registration_name,
        start_date = None,
        expdate = datetime.fromtimestamp(overall_exp),
        instructions = arr_registration_task_forum['instructions'],
        title = venue.senior_area_chairs_name.replace('_', ' ') + ' ' + arr_registration_task_forum['title'],
        additional_fields=arr_registration_task)
    )
    venue.registration_stages.append(
        openreview.stages.RegistrationStage(committee_id = venue.get_senior_area_chairs_id(),
        name = max_load_name,
        start_date = None,
        due_date = datetime.fromtimestamp(max_load_due),
        expdate = datetime.fromtimestamp(max_load_exp),
        instructions = arr_max_load_task_forum['instructions'],
        title = venue.senior_area_chairs_name.replace('_', ' ') + ' ' + arr_max_load_task_forum['title'],
        additional_fields=arr_sac_max_load_task,
        remove_fields=['profile_confirmed', 'expertise_confirmed'])
    )
    venue.create_registration_stages()

    # Create custom max papers invitations early
    venue_roles = [
        venue.get_reviewers_id(),
        venue.get_area_chairs_id(),
        venue.get_senior_area_chairs_id()
    ]
    for role in venue_roles:
        m = matching.Matching(venue, venue.client.get_group(role), None, None)
        m._create_edge_invitation(venue.get_custom_max_papers_id(m.match_group.id))

        client.post_invitation_edit(
            invitations=venue.get_meta_invitation_id(),
            readers=[venue.id],
            writers=[venue.id],
            signatures=[venue.id],
            invitation=openreview.api.Invitation(
                id=f"{role}/-/{max_load_name}",
                process=invitation_builder.get_process_content('process/max_load_process.py'),
                preprocess=invitation_builder.get_process_content('process/max_load_preprocess.py')
            )
        )

    # Create checklist custom stages and overwrite their process functions
    venue.custom_stage = openreview.stages.CustomStage(name='Reviewer_Checklist',
        reply_to=openreview.stages.CustomStage.ReplyTo.FORUM,
        source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
        due_date=reviewer_checklist_due,
        exp_date=reviewer_checklist_exp,
        invitees=[openreview.stages.CustomStage.Participants.REVIEWERS_ASSIGNED],
        readers=[
            openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED,
            openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED,
            openreview.stages.CustomStage.Participants.REVIEWERS_ASSIGNED
        ],
        content=arr_reviewer_checklist,
        notify_readers=False,
        email_sacs=False)

    invitation_builder.set_custom_stage_invitation(
        process_script = 'checklist_process.py',
        preprocess_script = 'checklist_preprocess.py'
    )

    venue.custom_stage = openreview.stages.CustomStage(name='Action_Editor_Checklist',
        reply_to=openreview.stages.CustomStage.ReplyTo.FORUM,
        source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
        due_date=ae_checklist_due,
        exp_date=ae_checklist_exp,
        invitees=[openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED],
        readers=[
            openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED,
            openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED
        ],
        content=arr_ae_checklist,
        notify_readers=False,
        email_sacs=False)

    invitation_builder.set_custom_stage_invitation(
        process_script = 'checklist_process.py',
        preprocess_script = 'checklist_preprocess.py'
    )

    # Create desk reject verification - will be active for all papers, only show flagged papers
    venue.custom_stage = openreview.stages.CustomStage(name='Desk_Reject_Verification',
        reply_to=openreview.stages.CustomStage.ReplyTo.FORUM,
        source=openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
        exp_date=overall_exp,
        invitees=[],
        readers=[],
        content=arr_desk_reject_verification,
        notify_readers=False,
        email_sacs=False)

    invitation_builder.set_custom_stage_invitation(
        process_script = None,
        preprocess_script = None
    )

    invitation_builder.set_verification_flag_invitation()