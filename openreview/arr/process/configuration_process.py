def process(client, note, invitation):
    import traceback
    import json
    from openreview.stages.arr_content import (
        arr_registration_task_forum,
        arr_registration_task,
        arr_content_license_task_forum,
        arr_content_license_task,
        arr_reviewer_ac_recognition_task_forum,
        arr_reviewer_ac_recognition_task,
        arr_max_load_task_forum,
        arr_reviewer_max_load_task,
        arr_ac_max_load_task,
        arr_sac_max_load_task,
        arr_reviewer_emergency_load_task_forum,
        arr_reviewer_emergency_load_task,
        arr_ac_emergency_load_task_forum,
        arr_ac_emergency_load_task,
        arr_reviewer_checklist,
        arr_ae_checklist,
        arr_desk_reject_verification,
        arr_reviewer_consent_content,
        arr_official_review_content,
        arr_metareview_content,
        arr_ethics_review_content,
        arr_review_rating_content,
        arr_author_consent_content,
        arr_metareview_license_task,
        arr_metareview_license_task_forum,
        hide_fields_from_public
    )
    from openreview.arr.helpers import ARRStage
    from openreview.venue import matching
    from datetime import datetime

    client_v2 = openreview.api.OpenReviewClient(
        baseurl=openreview.tools.get_base_urls(client)[1],
        token=client.token
    )

    SUPPORT_GROUP = invitation.id.split('/-/')[0]
    invitation_type = invitation.id.split('/')[-1]
    forum_note = client.get_note(note.forum)

    comment_readers = [forum_note.content.get('venue_id') + '/Program_Chairs', SUPPORT_GROUP]
    venue_id = forum_note.content.get('venue_id')
    domain = client_v2.get_group(venue_id)
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    request_form_id = domain.content['request_form_id']['value']
    request_form = client.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue = openreview.helpers.get_conference(client, request_form_id, support_group)
    invitation_builder = openreview.arr.InvitationBuilder(venue)
    
    request_form = client.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue_stage_invitations = client.get_all_invitations(regex=f"{support_group}/-/Request{request_form.number}.*")
    venue = openreview.helpers.get_conference(client, request_form_id, support_group)
    invitation_builder = openreview.arr.InvitationBuilder(venue)

    # Set stages
    def build_preprint_release_edit(client, venue, builder, request_form):
        venue_id = venue.id
        submission_stage = venue.submission_stage

        submission_id = submission_stage.get_submission_id(venue)

        hidden_field_names = hide_fields_from_public
        committee_members = venue.get_committee(number='${{4/id}/number}', with_authors=True)
        note_content = { f: { 'readers': committee_members } for f in hidden_field_names }

        edit = {
            'signatures': [venue_id],
            'readers': [venue_id, venue.get_authors_id('${{2/note/id}/number}')],
            'writers': [venue_id],
            'note': {
                'id': {
                    'param': {
                        'withInvitation': submission_id,
                        'optional': True
                    }
                },
                'odate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'signatures': [ venue.get_authors_id('${{2/id}/number}') ],
                'readers': ['everyone'],
                'writers': [venue_id, venue.get_authors_id('${{2/id}/number}')],
            }
        }

        note_content['_bibtex'] = {
            'value': {
                'param': {
                    'type': 'string',
                    'maxLength': 200000,
                    'input': 'textarea',
                    'optional': True
                }
            }
        }

        if note_content:
            edit['note']['content'] = note_content

        return {'edit': edit}
        
    def extend_desk_reject_verification(client, venue, builder, request_form):
        invitation_builder.set_verification_flag_invitation()

    def extend_consent(client, venue, builder, request_form):
        consent_invitation = openreview.api.Invitation(
            id = f"{venue.id}/-/Consent",
            edit = {
                'invitation': {
                    'edit': {}
                },
                'content': {}
            }
        )
        consent_invitation.edit['content']['replytoSignatures'] = {
            "value": {
                "param": {
                    "regex": ".*",
                    "type": "string"
                }
            }
        }
        consent_invitation.edit['invitation']['invitees'] = [
        "aclweb.org/ACL/ARR/2023/August/Program_Chairs",
        "${3/content/replytoSignatures/value}"
        ]
        consent_invitation.edit['invitation']['edit']['signatures'] = {
            "param": {
                "items": [
                    {
                    "prefix": "aclweb.org/ACL/ARR/2023/August/Submission${7/content/noteNumber/value}/Reviewer_.*",
                    "optional": True
                    }
                ]
            }
        }
        client_v2.post_invitation_edit(invitations=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            replacement=False,
            invitation=consent_invitation
        )

    def extend_ae_checklist(client, venue, builder, request_form):
        ae_checklist_invitation = openreview.api.Invitation(
            id = f"{venue.id}/-/Action_Editor_Checklist",
            content = {
            "review_readers": {
                "value": [
                        venue.id + "/Program_Chairs",
                        venue.id + "/Submission{number}/Senior_Area_Chairs",
                        venue.id + "/Submission{number}/Area_Chairs",
                        venue.id + "/Submission{number}/Reviewers/Submitted"
                    ]
                }
            },
            edit = {
                'content':  {
                    "noteNumber": {
                        "value": {
                            "param": {
                                "regex": ".*",
                                "type": "integer"
                            }
                        }
                    },
                    "noteId": {
                        "value": {
                            "param": {
                                "regex": ".*",
                                "type": "string"
                            }
                        }
                    },
                    "noteReaders": {
                        "value": {
                            "param": {
                                "type": "string[]",
                                "regex": f"{venue.id}/.*|everyone"
                            }
                        }
                    }
                },
                'invitation': {
                    "edit": {
                        "note": {
                            "readers": ['${5/content/noteReaders/value}']
                        }
                    }
                }
            }
        )
        ae_checklist_invitation.edit['invitation']['edit']['note']['readers'] = ['${5/content/noteReaders/value}']
        client_v2.post_invitation_edit(invitations=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            replacement=False,
            invitation=ae_checklist_invitation
        )

    def extend_reviewer_checklist(client, venue, builder, request_form):
        reviewer_checklist_invitation = openreview.api.Invitation(
            id = f"{venue.id}/-/Reviewer_Checklist",
            content = {
            "review_readers": {
                "value": [
                        venue.id + "/Program_Chairs",
                        venue.id + "/Submission{number}/Senior_Area_Chairs",
                        venue.id + "/Submission{number}/Area_Chairs",
                        venue.id + "/Submission{number}/Reviewers/Submitted"
                    ]
                }
            },
            edit = {
                'content':  {
                        "noteNumber": {
                        "value": {
                            "param": {
                                "regex": ".*",
                                "type": "integer"
                            }
                        }
                    },
                    "noteId": {
                        "value": {
                            "param": {
                                "regex": ".*",
                                "type": "string"
                            }
                        }
                    },
                    "noteReaders": {
                        "value": {
                            "param": {
                                "type": "string[]",
                                "regex": f"{venue.id}/.*|everyone"
                            }
                        }
                    }
                },
                'invitation': {
                    "edit": {
                        "note": {
                            "readers": ['${5/content/noteReaders/value}']
                        }
                    }
                }
            }
        )
        client_v2.post_invitation_edit(invitations=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            replacement=False,
            invitation=reviewer_checklist_invitation
        )

    workflow_stages = [
        ARRStage(
            type=ARRStage.Type.PROCESS_INVITATION,
            required_fields=['preprint_release_submission_date'],
            super_invitation_id=f"{venue_id}/-/Preprint_Release_{venue.submission_stage.name}",
            stage_arguments={},
            start_date=note.content.get('preprint_release_submission_date'),
            process='process/preprint_release_submission_process.py',
            build_edit=build_preprint_release_edit
        ),
        ARRStage(
            type=ARRStage.Type.PROCESS_INVITATION,
            required_fields=['setup_shared_data_date', 'previous_cycle'],
            super_invitation_id=f"{venue_id}/-/Share_Data",
            stage_arguments={
                'content': {
                    'previous_cycle': {'value': note.content.get('previous_cycle')}
                }
            },
            start_date=note.content.get('setup_shared_data_date'),
            process='management/setup_shared_data.py'
        ),
        ARRStage(
            type=ARRStage.Type.PROCESS_INVITATION,
            required_fields=['sae_affinity_scores'],
            super_invitation_id=f"{venue_id}/-/Setup_SAE_Matching",
            stage_arguments={
                'content': {
                    'sae_affinity_scores': {'value': note.content.get('sae_affinity_scores')},
                    'configuration_note_id': {'value': note.id}
                }
            },
            start_date=ARRStage.immediate_start_date(),
            process='management/setup_matching.py'
        ),
        ARRStage(
            type=ARRStage.Type.PROCESS_INVITATION,
            required_fields=['setup_tracks_and_reassignment_date'],
            super_invitation_id=f"{venue_id}/-/Setup_Tracks_And_Reassignments",
            stage_arguments={},
            start_date=note.content.get('setup_tracks_and_reassignment_date'),
            process='management/setup_reassignment_data.py'
        ),
        ARRStage(
            type=ARRStage.Type.PROCESS_INVITATION,
            required_fields=['setup_sae_ae_assignment_date'],
            super_invitation_id=f"{venue_id}/-/Enable_SAE_AE_Assignments",
            stage_arguments={},
            start_date=note.content.get('setup_sae_ae_assignment_date'),
            process='management/setup_sae_ae_assignments.py'
        ),
        ARRStage(
            type=ARRStage.Type.PROCESS_INVITATION,
            required_fields=['setup_review_release_date'],
            super_invitation_id=f"{venue_id}/-/Release_Official_Reviews",
            stage_arguments={},
            start_date=note.content.get('setup_review_release_date'),
            process='management/setup_review_release.py'
        ),
        ARRStage(
            type=ARRStage.Type.PROCESS_INVITATION,
            required_fields=['setup_meta_review_release_date'],
            super_invitation_id=f"{venue_id}/-/Release_Meta_Reviews",
            stage_arguments={},
            start_date=note.content.get('setup_meta_review_release_date'),
            process='management/setup_metareview_release.py'
        ),
        ARRStage(
            type=ARRStage.Type.PROCESS_INVITATION,
            required_fields=['setup_author_response_date'],
            super_invitation_id=f"{venue_id}/-/Enable_Author_Response",
            stage_arguments={},
            start_date=note.content.get('setup_author_response_date'),
            process='management/setup_rebuttal_start.py'
        ),
        ARRStage(
            type=ARRStage.Type.PROCESS_INVITATION,
            required_fields=['close_author_response_date'],
            super_invitation_id=f"{venue_id}/-/Close_Author_Response",
            stage_arguments={},
            start_date=note.content.get('close_author_response_date'),
            process='management/setup_rebuttal_end.py'
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_reviewers_id(),
            required_fields=['registration_due_date', 'form_expiration_date'],
            super_invitation_id=f"{venue.get_reviewers_id()}/-/{invitation_builder.REGISTRATION_NAME}",
            stage_arguments={
                'committee_id': venue.get_reviewers_id(),
                'name': invitation_builder.REGISTRATION_NAME,
                'instructions': arr_registration_task_forum['instructions'],
                'title': venue.get_reviewers_name() + ' ' + arr_registration_task_forum['title'],
                'additional_fields': arr_registration_task
            },
            exp_date=note.content.get('form_expiration_date')
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_reviewers_id(),
            required_fields=['form_expiration_date'],
            super_invitation_id=f"{venue.get_reviewers_id()}/-/{invitation_builder.RECOGNITION_NAME}",
            stage_arguments={
                'committee_id': venue.get_reviewers_id(),
                'name': invitation_builder.RECOGNITION_NAME,
                'instructions': arr_reviewer_ac_recognition_task_forum['instructions'],
                'title': venue.get_reviewers_name() + ' ' + arr_reviewer_ac_recognition_task_forum['title'],
                'additional_fields': arr_reviewer_ac_recognition_task,
                'remove_fields': ['profile_confirmed', 'expertise_confirmed']
            },
            exp_date=note.content.get('form_expiration_date')
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_reviewers_id(),
            required_fields=['form_expiration_date'],
            super_invitation_id=f"{venue.get_reviewers_id()}/-/{invitation_builder.REVIEWER_LICENSE_NAME}",
            stage_arguments={
                'committee_id': venue.get_reviewers_id(),
                'name': invitation_builder.REVIEWER_LICENSE_NAME,
                'instructions': arr_content_license_task_forum['instructions'],
                'title': arr_content_license_task_forum['title'],
                'additional_fields': arr_content_license_task,
                'remove_fields': ['profile_confirmed', 'expertise_confirmed']
            },
            exp_date=note.content.get('form_expiration_date')
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_area_chairs_id(),
            required_fields=['registration_due_date', 'form_expiration_date'],
            super_invitation_id=f"{venue.get_area_chairs_id()}/-/{invitation_builder.REGISTRATION_NAME}",
            stage_arguments={
                'committee_id': venue.get_area_chairs_id(),
                'name': invitation_builder.REGISTRATION_NAME,
                'instructions': arr_registration_task_forum['instructions'],
                'title': venue.get_area_chairs_name() + ' ' + arr_registration_task_forum['title'],
                'additional_fields': arr_registration_task
            },
            exp_date=note.content.get('form_expiration_date')
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_area_chairs_id(),
            required_fields=['form_expiration_date'],
            super_invitation_id=f"{venue.get_area_chairs_id()}/-/{invitation_builder.RECOGNITION_NAME}",
            stage_arguments={
                'committee_id': venue.get_area_chairs_id(),
                'name': invitation_builder.RECOGNITION_NAME,
                'instructions': arr_reviewer_ac_recognition_task_forum['instructions'],
                'title': venue.get_area_chairs_name() + ' ' + arr_reviewer_ac_recognition_task_forum['title'],
                'additional_fields': arr_reviewer_ac_recognition_task,
                'remove_fields': ['profile_confirmed', 'expertise_confirmed']
            },
            exp_date=note.content.get('form_expiration_date')
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_area_chairs_id(),
            required_fields=['form_expiration_date'],
            super_invitation_id=f"{venue.get_area_chairs_id()}/-/{invitation_builder.METAREVIEWER_LICENSE_NAME}",
            stage_arguments={
                'committee_id': venue.get_area_chairs_id(),
                'name': invitation_builder.METAREVIEWER_LICENSE_NAME,
                'instructions': arr_metareview_license_task_forum['instructions'],
                'title': venue.get_area_chairs_name() + ' ' + arr_metareview_license_task_forum['title'],
                'additional_fields': arr_metareview_license_task,
                'remove_fields': ['profile_confirmed', 'expertise_confirmed']
            },
            exp_date=note.content.get('form_expiration_date')
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_senior_area_chairs_id(),
            required_fields=['registration_due_date', 'form_expiration_date'],
            super_invitation_id=f"{venue.get_senior_area_chairs_id()}/-/{invitation_builder.REGISTRATION_NAME}",
            stage_arguments={
                'committee_id': venue.get_senior_area_chairs_id(),
                'name': invitation_builder.REGISTRATION_NAME,
                'instructions': arr_registration_task_forum['instructions'],
                'title': venue.senior_area_chairs_name.replace('_', ' ') + ' ' + arr_registration_task_forum['title'],
                'additional_fields': arr_registration_task
            },
            exp_date=note.content.get('form_expiration_date')
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_reviewers_id(),
            required_fields=['maximum_load_due_date', 'maximum_load_exp_date'],
            super_invitation_id=f"{venue.get_reviewers_id()}/-/{invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME}",
            stage_arguments={
                'committee_id': venue.get_reviewers_id(),
                'name': invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME,
                'instructions': arr_max_load_task_forum['instructions'],
                'title': venue.get_reviewers_name() + ' ' + arr_max_load_task_forum['title'],
                'additional_fields': arr_reviewer_max_load_task,
                'remove_fields': ['profile_confirmed', 'expertise_confirmed']
            },
            due_date=note.content.get('maximum_load_due_date'),
            exp_date=note.content.get('maximum_load_exp_date'),
            process='process/max_load_process.py',
            preprocess='process/max_load_preprocess.py'
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_area_chairs_id(),
            required_fields=['maximum_load_due_date', 'maximum_load_exp_date'],
            super_invitation_id=f"{venue.get_area_chairs_id()}/-/{invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME}",
            stage_arguments={
                'committee_id': venue.get_area_chairs_id(),
                'name': invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME,
                'instructions': arr_max_load_task_forum['instructions'],
                'title': venue.get_area_chairs_name() + ' ' + arr_max_load_task_forum['title'],
                'additional_fields': arr_ac_max_load_task,
                'remove_fields': ['profile_confirmed', 'expertise_confirmed']
            },
            due_date=note.content.get('maximum_load_due_date'),
            exp_date=note.content.get('maximum_load_exp_date'),
            process='process/max_load_process.py',
            preprocess='process/max_load_preprocess.py'
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_senior_area_chairs_id(),
            required_fields=['maximum_load_due_date', 'maximum_load_exp_date'],
            super_invitation_id=f"{venue.get_senior_area_chairs_id()}/-/{invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME}",
            stage_arguments={   
                'committee_id': venue.get_senior_area_chairs_id(),
                'name': invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME,
                'instructions': arr_max_load_task_forum['instructions'],
                'title': venue.senior_area_chairs_name.replace('_', ' ') + ' ' + arr_max_load_task_forum['title'],
                'additional_fields': arr_sac_max_load_task,
                'remove_fields': ['profile_confirmed', 'expertise_confirmed']
            },
            due_date=note.content.get('maximum_load_due_date'),
            exp_date=note.content.get('maximum_load_exp_date'),
            process='process/max_load_process.py',
            preprocess='process/max_load_preprocess.py'
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_reviewers_id(),
            required_fields=['emergency_reviewing_start_date', 'emergency_reviewing_due_date', 'emergency_reviewing_due_date'],
            super_invitation_id=f"{venue.get_reviewers_id()}/-/{invitation_builder.EMERGENCY_REVIEWING_NAME}",
            stage_arguments={   
                'committee_id': venue.get_reviewers_id(),
                'name': invitation_builder.EMERGENCY_REVIEWING_NAME,
                'instructions': arr_reviewer_emergency_load_task_forum['instructions'],
                'title': venue.get_reviewers_name() + ' ' + arr_reviewer_emergency_load_task_forum['title'],
                'additional_fields': arr_reviewer_emergency_load_task,
                'remove_fields': ['profile_confirmed', 'expertise_confirmed']
            },
            start_date=note.content.get('emergency_reviewing_start_date'),
            due_date=note.content.get('emergency_reviewing_due_date'),
            exp_date=note.content.get('emergency_reviewing_due_date'),
            process='process/emergency_load_process.py',
            preprocess='process/emergency_load_preprocess.py'
        ),
        ARRStage(
            type=ARRStage.Type.REGISTRATION_STAGE,
            group_id=venue.get_area_chairs_id(),
            required_fields=['emergency_metareviewing_start_date', 'emergency_metareviewing_due_date', 'emergency_metareviewing_due_date'],
            super_invitation_id=f"{venue.get_area_chairs_id()}/-/{invitation_builder.EMERGENCY_METAREVIEWING_NAME}",
            stage_arguments={   
                'committee_id': venue.get_area_chairs_id(),
                'name': invitation_builder.EMERGENCY_METAREVIEWING_NAME,
                'instructions': arr_ac_emergency_load_task_forum['instructions'],
                'title': venue.get_area_chairs_name() + ' ' + arr_ac_emergency_load_task_forum['title'],
                'additional_fields': arr_ac_emergency_load_task,
                'remove_fields': ['profile_confirmed', 'expertise_confirmed']
            },
            start_date=note.content.get('emergency_metareviewing_start_date'),
            due_date=note.content.get('emergency_metareviewing_due_date'),
            exp_date=note.content.get('emergency_metareviewing_due_date'),
            process='process/emergency_load_process.py',
            preprocess='process/emergency_load_preprocess.py'
        ),
        ARRStage(
            type=ARRStage.Type.CUSTOM_STAGE,
            required_fields=['author_consent_due_date', 'form_expiration_date'],
            super_invitation_id=f"{venue_id}/-/Blind_Submission_License_Agreement",
            stage_arguments={
                'name': 'Blind_Submission_License_Agreement',
                'reply_to': openreview.stages.CustomStage.ReplyTo.FORUM,
                'source': openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
                'invitees': [openreview.stages.CustomStage.Participants.AUTHORS],
                'readers': [],
                'content': arr_author_consent_content,
                'notify_readers': False,
                'email_sacs': False
            },
            due_date=note.content.get('author_consent_due_date'),
            exp_date=note.content.get('form_expiration_date')   
        ),
        ARRStage(
            type=ARRStage.Type.CUSTOM_STAGE,
            required_fields=['reviewer_checklist_due_date', 'reviewer_checklist_exp_date'],
            super_invitation_id=f"{venue_id}/-/Reviewer_Checklist",
            stage_arguments={
                'name': 'Reviewer_Checklist',
                'reply_to': openreview.stages.CustomStage.ReplyTo.FORUM,
                'source': openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
                'invitees': [openreview.stages.CustomStage.Participants.REVIEWERS_ASSIGNED],
                'readers': [
                    openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED,
                    openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED,
                    openreview.stages.CustomStage.Participants.REVIEWERS_ASSIGNED
                ],
                'content': arr_reviewer_checklist,
                'notify_readers': False,
                'email_sacs': False
            },
            due_date=note.content.get('reviewer_checklist_due_date'),
            exp_date=note.content.get('reviewer_checklist_exp_date'),
            process='process/checklist_process.py',
            preprocess='process/checklist_preprocess.py',
            extend=extend_reviewer_checklist
        ),
        ARRStage(
            type=ARRStage.Type.CUSTOM_STAGE,
            required_fields=['ae_checklist_due_date', 'ae_checklist_exp_date'],
            super_invitation_id=f"{venue_id}/-/Action_Editor_Checklist",
            stage_arguments={
                'name': 'Action_Editor_Checklist',
                'reply_to': openreview.stages.CustomStage.ReplyTo.FORUM,
                'source': openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
                'invitees': [openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED],
                'readers': [
                    openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED,
                    openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED
                ],
                'content': arr_ae_checklist,
                'notify_readers': False,
                'email_sacs': False
            },
            due_date=note.content.get('ae_checklist_due_date'),
            exp_date=note.content.get('ae_checklist_exp_date'),
            process='process/checklist_process.py',
            preprocess='process/checklist_preprocess.py',
            extend=extend_ae_checklist
        ),
        ARRStage(
            type=ARRStage.Type.CUSTOM_STAGE,
            required_fields=['form_expiration_date'],
            super_invitation_id=f"{venue_id}/-/Desk_Reject_Verification",
            stage_arguments={
                'name': 'Desk_Reject_Verification',
                'reply_to': openreview.stages.CustomStage.ReplyTo.FORUM,
                'source': openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
                'invitees': [],
                'readers': [],
                'content': arr_desk_reject_verification,
                'notify_readers': False,
                'email_sacs': False
            },
            exp_date=note.content.get('form_expiration_date'),
            process='process/verification_process.py',
            extend=extend_desk_reject_verification
        ),
        ARRStage(
            type=ARRStage.Type.CUSTOM_STAGE,
            required_fields=['form_expiration_date'],
            super_invitation_id=f"{venue_id}/-/Consent",
            stage_arguments={
                'name': 'Consent',
                'reply_to': openreview.stages.CustomStage.ReplyTo.REVIEWS,
                'source': openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
                'reply_type': openreview.stages.CustomStage.ReplyType.REPLY,
                'invitees': [],
                'readers': [],
                'content': arr_reviewer_consent_content,
                'notify_readers': False,
                'email_sacs': False
            },
            exp_date=note.content.get('form_expiration_date'),
            extend=extend_consent
        ),
        ARRStage(
            type=ARRStage.Type.CUSTOM_STAGE,
            required_fields=['review_rating_start_date', 'review_rating_exp_date'],
            super_invitation_id=f"{venue_id}/-/Review_Rating",
            stage_arguments={
                'name': 'Review_Rating',
                'reply_to': openreview.stages.CustomStage.ReplyTo.REVIEWS,
                'source': openreview.stages.CustomStage.Source.ALL_SUBMISSIONS,
                'invitees': [openreview.stages.CustomStage.Participants.AUTHORS],
                'readers': [
                    openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED,
                    openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED
                ],
                'content': arr_review_rating_content,
                'notify_readers': False,
                'email_sacs': False
            },
            start_date=note.content.get('review_rating_start_date'),
            exp_date=note.content.get('review_rating_exp_date')
        ),
        ARRStage(
            type=ARRStage.Type.STAGE_NOTE,
            required_fields=['comment_start_date', 'comment_end_date'],
            super_invitation_id=f"{venue_id}/-/Official_Comment",
            stage_arguments={
                'content': {
                    'participants': [
                        'Program Chairs',
                        'Assigned Senior Area Chairs',
                        'Assigned Area Chairs',
                        'Assigned Reviewers',
                        'Assigned Submitted Reviewers'
                    ],
                    'additional_readers':['Program Chairs'],
                    'email_program_chairs_about_official_comments': 'No, do not email PCs for each official comment made in the venue'
                },
                'forum': request_form_id,
                'invitation': '{}/-/Request{}/Comment_Stage'.format(support_group, request_form.number),
                'readers': ['{}/Program_Chairs'.format(venue_id), support_group],
                'referent': request_form_id,
                'replyto': request_form_id,
                'signatures': ['~Super_User1'],
                'writers': []
            },
            start_date=note.content.get('comment_start_date'),
            exp_date=note.content.get('comment_end_date'),
        ),
        ARRStage(
            type=ARRStage.Type.STAGE_NOTE,
            required_fields=['reviewing_start_date', 'reviewing_due_date', 'reviewing_exp_date'],
            super_invitation_id=f"{venue_id}/-/Official_Review",
            stage_arguments={
                'content': {
                    'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
                    'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                    'release_reviews_to_reviewers': 'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                    'remove_review_form_options': 'title,rating,review',
                    'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
                    'review_rating_field_name': 'overall_assessment',
                    'additional_review_form_options': arr_official_review_content
                },
                'forum': request_form_id,
                'invitation': '{}/-/Request{}/Review_Stage'.format(support_group, request_form.number),
                'readers': ['{}/Program_Chairs'.format(venue_id), support_group],
                'referent': request_form_id,
                'replyto': request_form_id,
                'signatures': ['~Super_User1'],
                'writers': []
            },
            start_date=note.content.get('reviewing_start_date'),
            due_date=note.content.get('reviewing_due_date'),
            exp_date=note.content.get('reviewing_exp_date'),
        ),
        ARRStage(
            type=ARRStage.Type.STAGE_NOTE,
            required_fields=['metareviewing_start_date', 'metareviewing_due_date', 'metareviewing_exp_date'],
            super_invitation_id=f"{venue_id}/-/Meta_Review",
            stage_arguments={
                'content': {
                    'make_meta_reviews_public': 'No, meta reviews should NOT be revealed publicly when they are posted',
                    'release_meta_reviews_to_authors': 'No, meta reviews should NOT be revealed when they are posted to the paper\'s authors',
                    'release_meta_reviews_to_reviewers': 'Meta reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
                    'additional_meta_review_form_options': arr_metareview_content,
                    'remove_meta_review_form_options': ['recommendation', 'confidence']
                },
                'forum': request_form_id,
                'invitation': '{}/-/Request{}/Meta_Review_Stage'.format(support_group, request_form.number),
                'readers': ['{}/Program_Chairs'.format(venue_id), support_group],
                'referent': request_form_id,
                'replyto': request_form_id,
                'signatures': ['~Super_User1'],
                'writers': []
            },
            start_date=note.content.get('metareviewing_start_date'),
            due_date=note.content.get('metareviewing_due_date'),
            exp_date=note.content.get('metareviewing_exp_date'),
        ),
        ARRStage(
            type=ARRStage.Type.STAGE_NOTE,
            required_fields=['ethics_reviewing_start_date', 'ethics_reviewing_due_date', 'ethics_reviewing_exp_date'],
            super_invitation_id=f"{venue_id}/-/Ethics_Review",
            stage_arguments={
                'content': {
                    'make_ethics_reviews_public': 'No, ethics reviews should NOT be revealed publicly when they are posted',
                    'release_ethics_reviews_to_authors': 'No, ethics reviews should NOT be revealed when they are posted to the paper\'s authors',
                    'release_ethics_reviews_to_reviewers': 'Ethics reviews should be immediately revealed to the paper\'s reviewers and ethics reviewers',
                    'additional_ethics_review_form_options': arr_ethics_review_content,
                    'remove_ethics_review_form_options': 'ethics_review',
                    "release_submissions_to_ethics_reviewers": "We confirm we want to release the submissions and reviews to the ethics reviewers",
                    'enable_comments_for_ethics_reviewers': 'Yes, enable commenting for ethics reviewers.',
                },
                'forum': request_form_id,
                'invitation': '{}/-/Request{}/Ethics_Review_Stage'.format(support_group, request_form.number),
                'readers': ['{}/Program_Chairs'.format(venue_id), support_group],
                'referent': request_form_id,
                'replyto': request_form_id,
                'signatures': ['~Super_User1'],
                'writers': []
            },
            start_date=note.content.get('ethics_reviewing_start_date'),
            due_date=note.content.get('ethics_reviewing_due_date'),
            exp_date=note.content.get('ethics_reviewing_exp_date'),
        )
    ]

    for stage in workflow_stages:
        print(f"checking {stage.super_invitation_id}")
        if all(field in note.content for field in stage.required_fields):
            print(f"building {stage.super_invitation_id}")
            stage.set_stage(
                client, client_v2, venue, invitation_builder, request_form
            )

    # Create custom max papers, load and area invitations
    venue_roles = [
        venue.get_reviewers_id(),
        venue.get_area_chairs_id(),
        venue.get_senior_area_chairs_id()
    ]
    edge_invitation_names = [
        'Custom_Max_Papers',
        'Registered_Load',
        'Emergency_Load',
        'Emergency_Area',
        'Available', # Post "only for resubmissions",
        'Author_In_Current_Cycle',
        'Seniority'
    ]
    for role in venue_roles:
        m = matching.Matching(venue, venue.client.get_group(role), None, None)
        if not openreview.tools.get_invitation(client_v2, venue.get_custom_max_papers_id(role)):
            m._create_edge_invitation(venue.get_custom_max_papers_id(m.match_group.id))
        
        if not openreview.tools.get_invitation(client_v2, f"{role}/-/Status"): # Hold "Requested" or "Reassigned", head=submission ID
            m._create_edge_invitation(f"{role}/-/Status")

        for name in edge_invitation_names:
            if not openreview.tools.get_invitation(client_v2, f"{role}/-/{name}"):
                cmp_inv = client_v2.get_invitation(venue.get_custom_max_papers_id(m.match_group.id))
                cmp_inv.id = f"{role}/-/{name}"
                cmp_inv.edit['id']['param']['withInvitation'] = f"{role}/-/{name}"
                cmp_inv.edit['weight']['param']['optional'] = True
                cmp_inv.edit['label'] = {
                    "param": {
                        "regex": ".*",
                        "optional": True,
                        "deletable": True
                    }
                }
                client_v2.post_invitation_edit(
                    invitations=meta_invitation_id,
                    readers=[venue_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    invitation=cmp_inv
                )