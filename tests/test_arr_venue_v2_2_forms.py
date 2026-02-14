import time
import openreview
import pytest
import datetime
import re
import random
import os
import csv
import sys
from copy import deepcopy
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openreview.venue import matching
from arr_v2_test_bootstrap import ensure_all_methods, ensure_prior_methods
from test_arr_venue_v2_1_workflow import (
    TestARRVenueV2Workflow as _WorkflowBootstrapClass,
    WORKFLOW_COMPLETED_METHODS,
    WORKFLOW_TEST_ORDER,
)
from openreview.stages.arr_content import (
    arr_submission_content,
    arr_withdrawal_content,
    hide_fields,
    hide_fields_from_public,
    arr_registration_task_forum,
    arr_registration_task,
    arr_content_license_task_forum,
    arr_content_license_task,
    arr_max_load_task_forum,
    arr_reviewer_max_load_task,
    arr_ac_max_load_task,
    arr_sac_max_load_task
)

FORMS_TEST_ORDER = [
    'test_checklists',
    'test_official_review_flagging',
    'test_author_response',
    'test_changing_deadlines',
    'test_meta_review_flagging_and_ethics_review',
    'test_emergency_reviewing_forms',
    'test_review_issue_forms',
    'test_reviewer_management_forms',
    'test_email_options',
]
FORMS_COMPLETED_METHODS = set()

@pytest.fixture(autouse=True)
def _ensure_forms_prerequisites(request, client, openreview_client, helpers, test_client, request_page, selenium):
    current_method = request.function.__name__
    if request.instance and current_method in FORMS_TEST_ORDER:
        fixture_values = {
            'client': client,
            'openreview_client': openreview_client,
            'helpers': helpers,
            'test_client': test_client,
            'request_page': request_page,
            'selenium': selenium
        }
        ensure_all_methods(
            instance=_WorkflowBootstrapClass(),
            ordered_methods=WORKFLOW_TEST_ORDER,
            completed_methods=WORKFLOW_COMPLETED_METHODS,
            fixture_values=fixture_values
        )
        ensure_prior_methods(
            instance=request.instance,
            ordered_methods=FORMS_TEST_ORDER,
            completed_methods=FORMS_COMPLETED_METHODS,
            current_method=current_method,
            fixture_values=fixture_values
        )
    yield
    if current_method in FORMS_TEST_ORDER:
        FORMS_COMPLETED_METHODS.add(current_method)

# API2 template from ICML
class TestARRVenueV2Forms():

    def test_checklists(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        violation_fields = ['appropriateness', 'formatting', 'length', 'anonymity', 'responsible_checklist', 'limitations'] # TODO: move to domain or somewhere?
        format_field = {
            'appropriateness': 'Appropriateness',
            'formatting': 'Formatting',
            'length': 'Length',
            'anonymity': 'Anonymity',
            'responsible_checklist': 'Responsible Checklist',
            'limitations': 'Limitations'
        }
        only_required_fields = ['number_of_assignments', 'diversity']

        default_fields = {field: True for field in violation_fields + only_required_fields}
        default_fields['need_ethics_review'] = False
        test_submission = submissions[1]

        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@aclrollingreview.com', password=helpers.strong_password)
        reviewer_two_client = openreview.api.OpenReviewClient(username = 'reviewer2@aclrollingreview.com', password=helpers.strong_password)
        ac_client = openreview.api.OpenReviewClient(username = 'ac1@aclrollingreview.com', password=helpers.strong_password)

        # Add reviewers to submission 2
        openreview_client.add_members_to_group(venue.get_reviewers_id(number=2), ['~Reviewer_ARROne1', '~Reviewer_ARRTwo1'])

        test_data_templates = {
            'aclweb.org/ACL/ARR/2023/August/Reviewers': {
                'checklist_invitation': 'aclweb.org/ACL/ARR/2023/August/Submission2/-/Reviewer_Checklist',
                'user': reviewer_client.get_groups(prefix='aclweb.org/ACL/ARR/2023/August/Submission2/Reviewer_', signatory='~Reviewer_ARROne1')[0].id,
                'client': reviewer_client
            },
            'aclweb.org/ACL/ARR/2023/August/Area_Chairs': {
                'checklist_invitation': 'aclweb.org/ACL/ARR/2023/August/Submission2/-/Action_Editor_Checklist',
                'user': ac_client.get_groups(prefix='aclweb.org/ACL/ARR/2023/August/Submission2/Area_Chair_', signatory='~AC_ARROne1')[0].id,
                'client': ac_client
            }
        }

        def post_checklist(chk_client, chk_inv, user, tested_field=None, ddate=None, existing_note=None, override_fields=None):
            def generate_checklist_content(tested_field=None):
                ret_content = {field: {'value':'Yes'} if default_fields[field] else {'value':'No'} for field in default_fields}
                ret_content['potential_violation_justification'] = {'value': 'There are no violations with this submission'}
                ret_content['ethics_review_justification'] = {'value': 'N/A (I answered no to the previous question)'}

                if tested_field:
                    ret_content[tested_field] = {'value':'Yes'} if not default_fields[tested_field] else {'value':'No'}
                    ret_content['ethics_review_justification'] = {'value': 'There is an issue'}
                    ret_content['potential_violation_justification'] = {'value': 'There are violations with this submission'}

                if 'Reviewer' in chk_inv:
                    for field in only_required_fields:
                        del ret_content[field]

                return ret_content
            
            if not existing_note:
                content = generate_checklist_content(tested_field=tested_field)
            if existing_note:
                content = existing_note['content']
                if tested_field:
                    content[tested_field] = {'value':'Yes'} if not default_fields[tested_field] else {'value':'No'}
                    content['ethics_review_justification'] = {'value': 'There is an issue'}
                    content['potential_violation_justification'] = {'value': 'There are violations with this submission'}

            if override_fields:
                for field in override_fields.keys():
                    content[field] = override_fields[field]
            
            chk_edit = chk_client.post_note_edit(
                invitation=chk_inv,
                signatures=[user],
                note=openreview.api.Note(
                    id=None if not existing_note else existing_note['id'],
                    content = content,
                    ddate=ddate
                )
            )

            helpers.await_queue_edit(openreview_client, edit_id=chk_edit['id'])

            time.sleep(2) ## Wait for flag process functions

            return chk_edit, pc_client_v2.get_note(test_submission.id)
        
        def now():
            return openreview.tools.datetime_millis(datetime.datetime.now())

        checklist_inv = test_data_templates[venue.get_reviewers_id()]['checklist_invitation']
        user = test_data_templates[venue.get_reviewers_id()]['user']
        user_client = test_data_templates[venue.get_reviewers_id()]['client']

        # Test checklist pre-process
        force_justifications = {
                'potential_violation_justification': {'value': 'There are no violations with this submission'},
                'ethics_review_justification': {'value': 'N/A (I answered no to the previous question)'}
        }
        with pytest.raises(openreview.OpenReviewException, match=r'You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging.'):
            post_checklist(user_client, checklist_inv, user, tested_field='need_ethics_review', override_fields=force_justifications)
        for field in violation_fields:
            with pytest.raises(openreview.OpenReviewException, match=rf'You have indicated a potential violation with the following fields: {format_field[field]}. Please enter a brief explanation under \"Potential Violation Justification\"'):
                post_checklist(user_client, checklist_inv, user, tested_field=field, override_fields=force_justifications)
                
        # Post checklist with no ethics flag and no violation field - check that flags are not there
        edit, test_submission = post_checklist(user_client, checklist_inv, user)
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' not in test_submission.content
        assert test_submission.content['number_of_reviewer_checklists']['value'] == 1

        # Assert that the checklist is visible to the user
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers' in edit['note']['readers']
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Reviewers/Submitted' not in edit['note']['readers']

        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=edit['note'])
        assert test_submission.content['number_of_reviewer_checklists']['value'] == 0
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        # Post checklist with no ethics flag and a violation field - check for DSV flag
        edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field=violation_fields[0])
        assert test_submission.content['number_of_reviewer_checklists']['value'] == 1
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate > now()
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        # Delete checklist - check DSV flag is False, invitation is expired
        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        # Re-post with no ethics flag and a violation field - check DSV flag is True
        violation_edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field=violation_fields[1])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate > now()
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        # Edit with no ethics flag and no violation field - check DSV flag is False
        violation_edit['note']['content'][violation_fields[1]]['value'] = 'Yes'
        _, test_submission = post_checklist(user_client, checklist_inv, user, existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        # Edit with ethics flag and no violation field - check DSV flag is false and ethics flag exists and is True
        _, test_submission = post_checklist(user_client, checklist_inv, user, tested_field='need_ethics_review', existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()
        assert test_submission.readers == ['everyone']
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers
        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been flagged for ethics reviewing')) == 1

        # Delete checklist - check both flags False
        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers
        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been unflagged for ethics reviewing')) == 1

        # Re-post with no flag - check both flags false
        reviewer_edit, test_submission = post_checklist(user_client, checklist_inv, user)
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        # Test checklists for AEs
        checklist_inv = test_data_templates[venue.get_area_chairs_id()]['checklist_invitation']
        user = test_data_templates[venue.get_area_chairs_id()]['user']
        user_client = test_data_templates[venue.get_area_chairs_id()]['client']

        assert user_client.get_invitation(
            'aclweb.org/ACL/ARR/2023/August/Submission2/-/Action_Editor_Checklist'
        ).edit['note']['content']['resubmission_reassignments']['description'] == "If this is a resubmission, has the authors' request regarding keeping or changing reviewers been respected? If not, answer 'No' and please modify the assignments"

        # Post checklist with no ethics flag and no violation field - check that flags are not there
        edit, test_submission = post_checklist(user_client, checklist_inv, user)
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert test_submission.content['number_of_action_editor_checklists']['value'] == 1
        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=edit['note'])
        assert test_submission.content['number_of_action_editor_checklists']['value'] == 0

        # Post checklist with no ethics flag and a violation field - check for DSV flag
        edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field=violation_fields[2])
        assert test_submission.content['number_of_action_editor_checklists']['value'] == 1
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate > now()

        # Delete checklist - check DSV flag is False, invitation is expired
        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=edit['note'])
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()

        # Re-post with no ethics flag and a violation field - check DSV flag is True
        violation_edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field=violation_fields[3])
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate > now()

        # Edit with no ethics flag and no violation field - check DSV flag is False
        violation_edit['note']['content'][violation_fields[3]]['value'] = 'Yes'
        _, test_submission = post_checklist(user_client, checklist_inv, user, existing_note=violation_edit['note'])
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()

        # Edit with ethics flag and no violation field - check DSV flag is false and ethics flag exists and is True
        _, test_submission = post_checklist(user_client, checklist_inv, user, tested_field='need_ethics_review', existing_note=violation_edit['note'])
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()
        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been flagged for ethics reviewing')) == 2

        # Delete checklist - check both flags False
        _, test_submission = post_checklist(user_client, checklist_inv, user, ddate=now(), existing_note=violation_edit['note'])
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been unflagged for ethics reviewing')) == 2

        # Re-post with no flag - check both flags false
        ae_edit, test_submission = post_checklist(user_client, checklist_inv, user)
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Desk_Reject_Verification').expdate < now()

        # Test un_flagged consensus
        reviewer_inv = test_data_templates[venue.get_reviewers_id()]['checklist_invitation']
        reviewer = test_data_templates[venue.get_reviewers_id()]['user']
        reviewer_client = test_data_templates[venue.get_reviewers_id()]['client']

        # First set both flags, then unflag 1, then unflag both
        ae_edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field='need_ethics_review', existing_note=ae_edit['note'])
        reviewer_edit, test_submission = post_checklist(reviewer_client, reviewer_inv, reviewer, tested_field='need_ethics_review', existing_note=reviewer_edit['note'])
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert test_submission.content['flagged_for_ethics_review']['value']
        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been flagged for ethics reviewing')) == 3

        reviewer_edit, test_submission = post_checklist(reviewer_client, reviewer_inv, reviewer, existing_note=reviewer_edit['note'], override_fields={'need_ethics_review': {'value': 'No'}})
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert test_submission.content['flagged_for_ethics_review']['value']

        ae_edit, test_submission = post_checklist(user_client, checklist_inv, user, existing_note=ae_edit['note'], override_fields={'need_ethics_review': {'value': 'No'}})
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been unflagged for ethics reviewing')) == 3

        # Repeat for desk reject verification
        ae_edit, test_submission = post_checklist(user_client, checklist_inv, user, tested_field=violation_fields[4], existing_note=ae_edit['note'])
        reviewer_edit, test_submission = post_checklist(reviewer_client, reviewer_inv, reviewer, tested_field=violation_fields[4], existing_note=reviewer_edit['note'])
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']

        reviewer_edit, test_submission = post_checklist(reviewer_client, reviewer_inv, reviewer, existing_note=reviewer_edit['note'], override_fields={violation_fields[4]: {'value': 'Yes'}})
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']

        ae_edit, test_submission = post_checklist(user_client, checklist_inv, user, existing_note=ae_edit['note'], override_fields={violation_fields[4]: {'value': 'Yes'}})
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']

        # Check readers
        ae_chk = openreview_client.get_note(ae_edit['note']['id'])
        ae_chk_inv = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Action_Editor_Checklist')
        rev_chk = openreview_client.get_note(reviewer_edit['note']['id'])
        rev_chk_inv = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission2/-/Reviewer_Checklist')

        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in ae_chk.readers
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in rev_chk.readers
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in ae_chk_inv.edit['readers']
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in ae_chk_inv.edit['note']['readers']
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in rev_chk_inv.edit['readers']
        assert 'aclweb.org/ACL/ARR/2023/August/Submission2/Ethics_Reviewers' in rev_chk_inv.edit['note']['readers']

    def test_official_review_flagging(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        ethics_client = openreview.api.OpenReviewClient(username = 'reviewerethics@aclrollingreview.com', password=helpers.strong_password)
        violation_fields = ['Knowledge_of_or_educated_guess_at_author_identity']

        default_fields = {}
        default_fields['Knowledge_of_or_educated_guess_at_author_identity'] = False
        default_fields['needs_ethics_review'] = False
        test_submission = submissions[2]

        review_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Official_Review')
        assert review_invitation.preprocess
        assert review_invitation.process
        super_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Official_Review')
        assert 'Knowledge_of_or_educated_guess_at_author_identity' in super_invitation.content['review_process_script']['value']
        assert 'You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging' in super_invitation.content['review_preprocess_script']['value']

        openreview_client.add_members_to_group(venue.get_reviewers_id(number=3), ['~Reviewer_ARROne1'])

        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@aclrollingreview.com', password=helpers.strong_password)

        test_data_templates = {
            'aclweb.org/ACL/ARR/2023/August/Reviewers': {
                'review_invitation': 'aclweb.org/ACL/ARR/2023/August/Submission3/-/Official_Review',
                'user': reviewer_client.get_groups(prefix='aclweb.org/ACL/ARR/2023/August/Submission3/Reviewer_', signatory='~Reviewer_ARROne1')[0].id,
                'client': reviewer_client
            }
        }

        def post_official_review(rev_client, rev_inv, user, tested_field=None, ddate=None, existing_note=None, override_fields=None):
            def generate_official_review_content(tested_field=None):
                ret_content = {
                    "confidence": { "value": 5 },
                    "paper_summary": { "value": 'some summary' },
                    "summary_of_strengths": { "value": 'some strengths' },
                    "summary_of_weaknesses": { "value": 'some weaknesses' },
                    "comments_suggestions_and_typos": { "value": 'some comments' },
                    "soundness": { "value": 1 },
                    "excitement": { "value": 1.5 },
                    "overall_assessment": { "value": 1 },
                    "ethical_concerns": { "value": "N/A" },
                    "reproducibility": { "value": 1 },
                    "datasets": { "value": 1 },
                    "software": { "value": 1 },
                    "needs_ethics_review": {'value': 'No'},
                    "Knowledge_of_or_educated_guess_at_author_identity": {"value": "No"},
                    "Knowledge_of_paper": {"value": "After the review process started"},
                    "Knowledge_of_paper_source": {"value": ["A research talk"]},
                    "impact_of_knowledge_of_paper": {"value": "A lot"},
                    "reviewer_certification": {"value": "Yes"},
                    "secondary_reviewer": {"value": ["~Reviewer_ARRTwo1"]},
                    "publication_ethics_policy_compliance": {"value": "I did not use any generative AI tools for this review"}
                }
                ret_content['ethical_concerns'] = {'value': 'There are no concerns with this submission'}

                if tested_field:
                    ret_content[tested_field] = {'value':'Yes'}
                    ret_content['ethical_concerns'] = {'value': 'There are concerns with this submission'}

                return ret_content
            
            if not existing_note:
                content = generate_official_review_content(tested_field=tested_field)
            if existing_note:
                content = {}
                for key, value in existing_note['content'].items():
                    content[key] = { 'value': value['value'] }
                if tested_field:
                    content[tested_field] = {'value':'Yes'}
                    content['ethical_concerns'] = {'value': 'There are concerns with this submission'}

            if override_fields:
                for field in override_fields.keys():
                    content[field] = override_fields[field]
            
            rev_edit = rev_client.post_note_edit(
                invitation=rev_inv,
                signatures=[user],
                note=openreview.api.Note(
                    id=None if not existing_note else existing_note['id'],
                    content = content,
                    ddate=ddate
                )
            )

            helpers.await_queue_edit(openreview_client, edit_id=rev_edit['id'])

            time.sleep(2) ## Wait for flag process functions

            review = pc_client_v2.get_note(id=rev_edit['note']['id'])
            assert 'readers' not in review.content['reviewer_certification']
            assert 'readers' in review.content['secondary_reviewer']
            assert review.content['secondary_reviewer']['readers'] == [
                'aclweb.org/ACL/ARR/2023/August/Program_Chairs',
                'aclweb.org/ACL/ARR/2023/August/Submission3/Senior_Area_Chairs',
                'aclweb.org/ACL/ARR/2023/August/Submission3/Area_Chairs',
                user
            ]

            return rev_edit, pc_client_v2.get_note(test_submission.id)
        
        def now():
            return openreview.tools.datetime_millis(datetime.datetime.now())

        review_inv = test_data_templates[venue.get_reviewers_id()]['review_invitation']
        user = test_data_templates[venue.get_reviewers_id()]['user']
        user_client = test_data_templates[venue.get_reviewers_id()]['client']

        # Test checklist pre-process
        force_justifications = {
                'ethical_concerns': {'value': 'There are no concerns with this submission'}
        }
        with pytest.raises(openreview.OpenReviewException, match=r'You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging.'):
            post_official_review(user_client, review_inv, user, tested_field='needs_ethics_review', override_fields=force_justifications)
                
        # Post checklist with no ethics flag and no violation field - check that flags are not there
        edit, test_submission = post_official_review(user_client, review_inv, user)
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' not in test_submission.content
        _, test_submission = post_official_review(user_client, review_inv, user, ddate=now(), existing_note=edit['note'])

        # Post checklist with no ethics flag and a violation field - check for DSV flag
        edit, test_submission = post_official_review(user_client, review_inv, user, tested_field=violation_fields[0])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate > now()
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        # Delete checklist - check DSV flag is False, invitation is expired
        _, test_submission = post_official_review(user_client, review_inv, user, ddate=now(), existing_note=edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate < now()
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        # Re-post with no ethics flag and a violation field - check DSV flag is True
        violation_edit, test_submission = post_official_review(user_client, review_inv, user, tested_field=violation_fields[0])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate > now()
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        # Edit with no ethics flag and no violation field - check DSV flag is False
        violation_edit['note']['content'][violation_fields[0]]['value'] = 'No'
        _, test_submission = post_official_review(user_client, review_inv, user, existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate < now()
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        # Edit with ethics flag and no violation field - check DSV flag is false and ethics flag exists and is True
        _, test_submission = post_official_review(user_client, review_inv, user, tested_field='needs_ethics_review', existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate < now()
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' in test_submission.readers
        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been flagged for ethics reviewing')) == 4

        comment_inv = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Official_Comment')
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' in comment_inv.invitees
        assert 'aclweb.org/ACL/ARR/2023/August/Submission3/Ethics_Reviewers' in comment_inv.invitees

        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/-/Ethics_Review_Flag', count=7)

        openreview_client.add_members_to_group(venue.get_ethics_reviewers_id(number=3), ['~EthicsReviewer_ARROne1'])

        # Post an ethics review
        ethics_anon_id = ethics_client.get_groups(prefix='aclweb.org/ACL/ARR/2023/August/Submission3/Ethics_Reviewer_', signatory='~EthicsReviewer_ARROne1')[0].id
        assert ethics_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Ethics_Review')
        ethics_review_edit = ethics_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Submission3/-/Ethics_Review',
            signatures=[ethics_anon_id],
            note=openreview.api.Note(
                content={
                    'recommendation': {'value': 'a recommendation'},
                    'issues': {'value': ['1.2 Avoid harm']},
                    'explanation': {'value': 'an explanation'}
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=ethics_review_edit['id'])
        messages = openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] Ethics Review posted to your assigned Paper number: 3, Paper title: "Paper title 3"')
        assert messages and len(messages) == 1

        messages = openreview_client.get_messages(to='reviewerethics@aclrollingreview.com', subject='[ARR - August 2023] Your ethics review has been received on your assigned Paper number: 3, Paper title: "Paper title 3"')
        assert messages and len(messages) == 1

        # allow ethics chairs to invite ethics reviewers
        conference_matching = matching.Matching(venue, openreview_client.get_group(venue.get_ethics_reviewers_id()), None)
        conference_matching.setup_invite_assignment(hash_seed='1234', invited_committee_name=f'Emergency_{venue.get_ethics_reviewers_name(pretty=False)}')
        venue.group_builder.set_external_reviewer_recruitment_groups(name=f'Emergency_{venue.get_ethics_reviewers_name(pretty=False)}', is_ethics_reviewer=True)

        group = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Emergency_Ethics_Reviewers')
        assert group
        assert group.readers == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs', 'aclweb.org/ACL/ARR/2023/August/Emergency_Ethics_Reviewers']
        assert group.writers == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs']

        group = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Emergency_Ethics_Reviewers/Invited')
        assert group
        assert group.readers == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs']
        assert group.writers == ['aclweb.org/ACL/ARR/2023/August', 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs']


        invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Ethics_Reviewers/-/Invite_Assignment')
        assert invitation
        assert 'is_ethics_reviewer' in invitation.content and invitation.content['is_ethics_reviewer']['value'] == True

        ethics_chair_client = openreview.api.OpenReviewClient(username='ec1@aclrollingreview.com', password=helpers.strong_password)
        edge = ethics_chair_client.post_edge(
            openreview.api.Edge(invitation=invitation.id,
                signatures=['aclweb.org/ACL/ARR/2023/August/Ethics_Chairs'],
                head=test_submission.id,
                tail='celeste@arrethics.cc',
                label='Invitation Sent',
                weight=1
        ))
        helpers.await_queue_edit(openreview_client, edge.id)

        messages = openreview_client.get_messages(to='celeste@arrethics.cc', subject=f'''[ARR - August 2023] Invitation to serve as ethics reviewer for paper titled "{test_submission.content['title']['value']}"''')
        assert messages and len(messages) == 1
        invitation_url = re.search('https://.*\n', messages[0]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]

        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/Ethics_Reviewers/-/Assignment_Recruitment', count=1)

        messages = openreview_client.get_messages(to='celeste@arrethics.cc', subject='[ARR - August 2023] Ethics Reviewer Invitation accepted for paper 3, assignment pending')
        assert len(messages) == 1

        # desk-reject paper
        desk_reject_edit = pc_client_v2.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Rejection',
            signatures=['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            note=openreview.api.Note(
                content={
                    'desk_reject_comments': { 'value': 'No pdf.' },
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=desk_reject_edit['id'])
        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/-/Desk_Rejected_Submission')

        checklist_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Reviewer_Checklist')
        assert checklist_invitation.ddate < now()
        checklist_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Action_Editor_Checklist')
        assert checklist_invitation.ddate < now()
        comment_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Author-Editor_Confidential_Comment')
        assert comment_invitation.ddate < now()

        submission = openreview_client.get_note(desk_reject_edit['note']['forum'])
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' in submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Ethics_Reviewers' not in submission.readers

        assert openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023]: Paper #3 desk-rejected by Program Chairs')

        desk_rejection_reversion_note = pc_client_v2.post_note_edit(invitation='aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Rejection_Reversion',
                                    signatures=['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
                                    note=openreview.api.Note(
                                        content={
                                            'revert_desk_rejection_confirmation': { 'value': 'We approve the reversion of desk-rejected submission.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_rejection_reversion_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Rejection_Reversion')

        # Delete checklist - check both flags False
        _, test_submission = post_official_review(user_client, review_inv, user, ddate=now(), existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been unflagged for ethics reviewing')) == 4
        assert openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been unflagged for ethics reviewing')

        # Re-post with no flag - check both flags false
        reviewer_edit, test_submission = post_official_review(user_client, review_inv, user)
        assert 'flagged_for_ethics_review' in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert not test_submission.content['flagged_for_ethics_review']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/-/Desk_Reject_Verification').expdate < now()
        assert 'aclweb.org/ACL/ARR/2023/August/Ethics_Chairs' not in test_submission.readers
        assert f'aclweb.org/ACL/ARR/2023/August/Submission{test_submission.number}/Ethics_Reviewers' not in test_submission.readers

        # Check mixed AE Checklist and Official Review flagging
        _, test_submission = post_official_review(user_client, review_inv, user, tested_field='needs_ethics_review', existing_note=reviewer_edit['note'])
        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been flagged for ethics reviewing')) == 5

        ac_client = openreview.api.OpenReviewClient(username = 'ac2@aclrollingreview.com', password=helpers.strong_password)
        ac_sig = openreview_client.get_groups(
            prefix=f'aclweb.org/ACL/ARR/2023/August/Submission3/Area_Chair_',
            signatory='~AC_ARRTwo1'
        )[0]
        chk_content = {
            "appropriateness" : { "value" : "Yes" },
            "formatting" : { "value" : "Yes" },
            "length" : { "value" : "Yes" },
            "anonymity" : { "value" : "Yes" },
            "responsible_checklist" : { "value" : "Yes" },
            "limitations" : { "value" : "Yes" },
            "number_of_assignments" : { "value" : "Yes" },
            "diversity" : { "value" : "Yes" },
            "need_ethics_review" : { "value" : "Yes" },
            "potential_violation_justification" : { "value" : "There are no violations with this submission" },
            "ethics_review_justification" : { "value" : "There is an issue" }
        }
        chk_edit = ac_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Submission3/-/Action_Editor_Checklist',
            signatures=[ac_sig.id],
            note=openreview.api.Note(
                content = chk_content
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=chk_edit['id'])
        ## No change
        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been flagged for ethics reviewing')) == 5

        chk_content['need_ethics_review'] = { "value" : "No"}
        chk_content['ethics_review_justification'] = { "value" : "There is no issue" }
        chk_edit = ac_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Submission3/-/Action_Editor_Checklist',
            signatures=[ac_sig.id],
            note=openreview.api.Note(
                id = chk_edit['note']['id'],
                content = chk_content
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=chk_edit['id'])

        ## Unflagging only AE should not affect ethics review flag and should not send an email
        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been unflagged for ethics reviewing')) == 4
        _, test_submission = post_official_review(user_client, review_inv, user, existing_note=reviewer_edit['note'])
        ## Unflagging official review + AE checklist will unflag and send an email
        assert len(openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been unflagged for ethics reviewing')) == 5

        ## Delete checklist to keep email option data consistent
        chk_edit = ac_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Submission3/-/Action_Editor_Checklist',
            signatures=[ac_sig.id],
            note=openreview.api.Note(
                id = chk_edit['note']['id'],
                content = chk_content,
                ddate = now()
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=chk_edit['id'])

        # Edit with ethics flag to double check that authors are present
        _, test_submission = post_official_review(user_client, review_inv, user, tested_field='needs_ethics_review', existing_note=reviewer_edit['note'])
        assert 'flagged_for_ethics_review' in test_submission.content

        # Make reviews public
        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_review_release_date': (openreview.tools.datetime.datetime.now() - datetime.timedelta(minutes=3)).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Release_Official_Reviews-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Official_Review-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Ethics_Review-0-1', count=3)

        review = openreview_client.get_note(reviewer_edit['note']['id'])
        assert 'aclweb.org/ACL/ARR/2023/August/Submission3/Authors' in review.readers
        assert 'readers' not in review.content['reviewer_certification']

        ethics_review = openreview_client.get_note(ethics_review_edit['note']['id'])
        assert 'aclweb.org/ACL/ARR/2023/August/Submission3/Authors' in ethics_review.readers

    def test_author_response(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        submissions = venue.get_submissions(sort='tmdate')

        # Open author response
        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_author_response_date': (datetime.datetime.now() - datetime.timedelta(minutes=3)).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()
        time.sleep(3)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Enable_Author_Response-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Official_Comment-0-1', count=5)

        for s in submissions:
            comment_invitees = openreview_client.get_invitation(f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/-/Official_Comment").invitees
            comment_readers = openreview_client.get_invitation(f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/-/Official_Comment").edit['note']['readers']['param']['enum']
            comment_signatures = [o['value'] for o in openreview_client.get_invitation(f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/-/Official_Comment").edit['signatures']['param']['items'] if 'value' in o]

            assert f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/Authors" in comment_invitees
            assert f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/Authors" in comment_readers
            assert f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/Authors" in comment_signatures

        comment_edit = pc_client_v2.post_note_edit(
            invitation=f"aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/-/Official_Comment",
            writers=['aclweb.org/ACL/ARR/2023/August'],
            signatures=['aclweb.org/ACL/ARR/2023/August/Program_Chairs'],
            note=openreview.api.Note(
                replyto=submissions[0].id,
                readers=[
                    'aclweb.org/ACL/ARR/2023/August/Program_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Senior_Area_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[0].number}/Area_Chairs'
                ],
                content={
                    "comment": { "value": "This is a comment"}
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        # Test author response threshold
        test_client = openreview.api.OpenReviewClient(token=test_client.token)
        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer2@aclrollingreview.com', password=helpers.strong_password)
        anon_id = reviewer_client.get_groups(prefix=f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Reviewer_', signatory='~Reviewer_ARRTwo1')[0].id
        ac_client = openreview.api.OpenReviewClient(username = 'ac1@aclrollingreview.com', password=helpers.strong_password)
        clients = [reviewer_client, test_client]
        signatures = [anon_id, f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Authors']
        root_note_id = None
        all_comment_ids = []

        for i in range(1, 5):
            client = clients[i % 2]
            signature = signatures[i % 2]
            comment_edit = client.post_note_edit(
                invitation=f"aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/-/Official_Comment",
                writers=['aclweb.org/ACL/ARR/2023/August'],
                signatures=[signature],
                note=openreview.api.Note(
                    replyto=submissions[1].id if i == 1 else root_note_id,
                    readers=[
                        'aclweb.org/ACL/ARR/2023/August/Program_Chairs',
                        f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Senior_Area_Chairs',
                        f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Area_Chairs',
                        f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Reviewers',
                        f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Authors'
                    ],
                    content={
                        "comment": { "value": "This is a comment"}
                    }
                )
            )
            helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])
            all_comment_ids.append(comment_edit['note']['id'])
            if i == 1:
                root_note_id = comment_edit['note']['id']

        assert len(
            openreview_client.get_messages(
                to='ac1@aclrollingreview.com',
                subject=f'[ARR - August 2023] Reviewer {anon_id.split("_")[-1]} commented on a paper in your area. Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 1
        assert len(
            openreview_client.get_messages(
                to='ac1@aclrollingreview.com',
                subject=f'[ARR - August 2023] An author commented on a paper in your area. Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 2
        assert len(
            openreview_client.get_messages(
                to='reviewer2@aclrollingreview.com',
                subject=f'[ARR - August 2023] An author commented on a paper you are reviewing. Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 2
        assert len(
            openreview_client.get_messages(
                to='reviewer2@aclrollingreview.com',
                subject=f'[ARR - August 2023] Your comment was received on Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 2
        assert len(
            openreview_client.get_messages(
                to='test@mail.com',
                subject=f'[ARR - August 2023] Reviewer {anon_id.split("_")[-1]} commented on your submission. Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 2
        assert len(
            openreview_client.get_messages(
                to='test@mail.com',
                subject=f'[ARR - August 2023] Your comment was received on Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 2

        # Create an orphan comment
        parent_comment_id = all_comment_ids[-2]
        parent_comment = openreview_client.get_note(parent_comment_id)
        now_millis = openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(minutes=3))
        delete_comment_edit = openreview_client.post_note_edit(
            invitation=f"aclweb.org/ACL/ARR/2023/August/-/Edit",
            readers=['aclweb.org/ACL/ARR/2023/August/'],
            writers=['aclweb.org/ACL/ARR/2023/August'],
            signatures=['aclweb.org/ACL/ARR/2023/August'],
            note=openreview.api.Note(
                id=parent_comment_id,
                ddate=now_millis
            )
        )

        # Reply to orphan comment
        comment_edit = test_client.post_note_edit(
            invitation=f"aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/-/Official_Comment",
            writers=['aclweb.org/ACL/ARR/2023/August'],
            signatures=[f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Authors'],
            note=openreview.api.Note(
                replyto=parent_comment_id,
                readers=[
                    'aclweb.org/ACL/ARR/2023/August/Program_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Senior_Area_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Area_Chairs',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Reviewers',
                    f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Authors'
                ],
                content={
                    "comment": { "value": "This is a comment by the authors"}
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

        # Test new thread
        for i in range(1, 5):
            client = clients[i % 2]
            signature = signatures[i % 2]
            comment_edit = client.post_note_edit(
                invitation=f"aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/-/Official_Comment",
                writers=['aclweb.org/ACL/ARR/2023/August'],
                signatures=[signature],
                note=openreview.api.Note(
                    replyto=submissions[1].id if i == 1 else root_note_id,
                    readers=[
                        'aclweb.org/ACL/ARR/2023/August/Program_Chairs',
                        f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Senior_Area_Chairs',
                        f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Area_Chairs',
                        f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Reviewers',
                        f'aclweb.org/ACL/ARR/2023/August/Submission{submissions[1].number}/Authors'
                    ],
                    content={
                        "comment": { "value": "This is a comment, thread2"}
                    }
                )
            )
            helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])
            if i == 1:
                root_note_id = comment_edit['note']['id']

        assert len(
            openreview_client.get_messages(
                to='ac1@aclrollingreview.com',
                subject=f'[ARR - August 2023] Reviewer {anon_id.split("_")[-1]} commented on a paper in your area. Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 2
        assert len(
            openreview_client.get_messages(
                to='ac1@aclrollingreview.com',
                subject=f'[ARR - August 2023] An author commented on a paper in your area. Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 5
        assert len(
            openreview_client.get_messages(
                to='reviewer2@aclrollingreview.com',
                subject=f'[ARR - August 2023] An author commented on a paper you are reviewing. Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 5
        assert len(
            openreview_client.get_messages(
                to='reviewer2@aclrollingreview.com',
                subject=f'[ARR - August 2023] Your comment was received on Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 4
        assert len(
            openreview_client.get_messages(
                to='test@mail.com',
                subject=f'[ARR - August 2023] Reviewer {anon_id.split("_")[-1]} commented on your submission. Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 4
        assert len(
            openreview_client.get_messages(
                to='test@mail.com',
                subject=f'[ARR - August 2023] Your comment was received on Paper Number: 2, Paper Title: "Paper title 2"'
            )
        ) == 5


        assert openreview_client.get_messages(to='sac2@aclrollingreview.com', subject='[ARR - August 2023] Program Chairs commented on a paper in your area. Paper Number: 3, Paper Title: "Paper title 3"')   

        # Close author response
        pc_client.post_note(
            openreview.Note(
                content={
                    'close_author_response_date': (datetime.datetime.now() - datetime.timedelta(minutes=6)).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()
        time.sleep(6)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Close_Author_Response-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Official_Comment-0-1', count=6)

        for s in submissions:
            comment_invitees = openreview_client.get_invitation(f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/-/Official_Comment").invitees
            comment_readers = openreview_client.get_invitation(f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/-/Official_Comment").edit['note']['readers']['param']['enum']

            assert f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/Authors" not in comment_invitees
            assert f"aclweb.org/ACL/ARR/2023/August/Submission{s.number}/Authors" not in comment_readers

    def test_changing_deadlines(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form_note=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form_note.id, 'openreview.net/Support')
        registration_name = 'Registration'
        max_load_name = 'Max_Load_And_Unavailability_Request'

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=5)

        # Original due dates were at +3, now at +5
        reviewer_max_load_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/{max_load_name}').duedate
        ac_max_load_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/{max_load_name}').duedate
        sac_max_load_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/{max_load_name}').duedate

        reviewer_max_load_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/{max_load_name}').expdate
        ac_max_load_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/{max_load_name}').expdate
        sac_max_load_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/{max_load_name}').expdate

        reviewer_checklist_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Reviewer_Checklist').edit['invitation']['duedate']
        reviewer_checklist_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Reviewer_Checklist').edit['invitation']['expdate']

        ae_checklist_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Action_Editor_Checklist').edit['invitation']['duedate']
        ae_checklist_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Action_Editor_Checklist').edit['invitation']['expdate']

        reviewing_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Official_Review').edit['invitation']['duedate']
        reviewing_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Official_Review').edit['invitation']['expdate']

        meta_reviewing_due_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Meta_Review').edit['invitation']['duedate']
        meta_reviewing_exp_date = openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Meta_Review').edit['invitation']['expdate']

        pc_client.post_note(
            openreview.Note(
                content={
                    'form_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'maximum_load_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'maximum_load_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'ae_checklist_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'ae_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'ae_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'reviewer_checklist_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'review_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'review_deadline': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'review_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'meta_review_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'meta_review_deadline': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'meta_review_expiration_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                },
                invitation=f'openreview.net/Support/-/Request{request_form_note.number}/ARR_Configuration',
                forum=request_form_note.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form_note.id,
                replyto=request_form_note.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()

        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/{max_load_name}').duedate > reviewer_max_load_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Reviewers/-/{max_load_name}').expdate > reviewer_max_load_exp_date
        
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/{max_load_name}').duedate > ac_max_load_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/{max_load_name}').expdate > ac_max_load_exp_date

        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/{max_load_name}').duedate > sac_max_load_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/Senior_Area_Chairs/-/{max_load_name}').expdate > sac_max_load_exp_date

        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Reviewer_Checklist').edit['invitation']['duedate'] > reviewer_checklist_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Reviewer_Checklist').edit['invitation']['expdate'] > reviewer_checklist_exp_date

        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Action_Editor_Checklist').edit['invitation']['duedate'] > ae_checklist_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Action_Editor_Checklist').edit['invitation']['expdate'] > ae_checklist_exp_date
        
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Official_Review').edit['invitation']['duedate'] > reviewing_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Official_Review').edit['invitation']['expdate'] > reviewing_exp_date

        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Meta_Review').edit['invitation']['duedate'] > meta_reviewing_due_date
        assert openreview_client.get_invitation(f'aclweb.org/ACL/ARR/2023/August/-/Meta_Review').edit['invitation']['expdate'] > meta_reviewing_exp_date

    def test_meta_review_flagging_and_ethics_review(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        submissions = pc_client_v2.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        violation_fields = ['author_identity_guess']

        messages = openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been flagged for ethics reviewing')
        flagged_messages = len(messages)
        messages = openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been unflagged for ethics reviewing')
        unflagged_messages = len(messages)

        default_fields = {}
        default_fields['author_identity_guess'] = 1
        default_fields['needs_ethics_review'] = False
        test_submission = submissions[3]

        review_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Meta_Review')
        assert review_invitation.preprocess
        assert review_invitation.process
        super_invitation = openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Meta_Review')
        assert 'violation_fields' in super_invitation.content['metareview_process_script']['value']
        assert 'You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging' in super_invitation.content['metareview_preprocess_script']['value']

        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment',
            head = test_submission.id,
            tail = '~AC_ARROne1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Submission4/Senior_Area_Chairs'],
            weight = 1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        ac_client = openreview.api.OpenReviewClient(username = 'ac1@aclrollingreview.com', password=helpers.strong_password)
        ethics_client = openreview.api.OpenReviewClient(username = 'reviewerethics@aclrollingreview.com', password=helpers.strong_password)

        test_data_templates = {
            'aclweb.org/ACL/ARR/2023/August/Area_Chairs': {
                'review_invitation': 'aclweb.org/ACL/ARR/2023/August/Submission4/-/Meta_Review',
                'user': ac_client.get_groups(prefix='aclweb.org/ACL/ARR/2023/August/Submission4/Area_Chair_', signatory='~AC_ARROne1')[0].id,
                'client': ac_client
            }
        }

        def post_meta_review(rev_client, rev_inv, user, tested_field=None, ddate=None, existing_note=None, override_fields=None):
            def generate_official_review_content(tested_field=None):
                ret_content = {
                    "metareview": { "value": 'a metareview' },
                    "summary_of_reasons_to_publish": { "value": 'some summary' },
                    "summary_of_suggested_revisions": { "value": 'some strengths' },
                    "overall_assessment": { "value": 1 },
                    "ethical_concerns": { "value": "There are no concerns with this submission" },
                    "author_identity_guess": { "value": 1 },
                    "needs_ethics_review": {'value': 'No'},
                    "reported_issues": {'value': ['No']},
                    "publication_ethics_policy_compliance": {"value": "I did not use any generative AI tools for this review"}
                }
                ret_content['ethical_concerns'] = {'value': 'There are no concerns with this submission'}

                if tested_field:
                    ret_content[tested_field] = {'value':'Yes'}
                    ret_content['ethical_concerns'] = {'value': 'There are concerns with this submission'}

                return ret_content
            
            if not existing_note:
                content = generate_official_review_content(tested_field=tested_field)
            if existing_note:
                content = existing_note['content']
                if tested_field:
                    content[tested_field] = {'value':'Yes'}
                    content['ethical_concerns'] = {'value': 'There are concerns with this submission'}

            if override_fields:
                for field in override_fields.keys():
                    content[field] = override_fields[field]
            
            #review_edits = openreview_client.get_process_logs(invitation=rev_inv)

            rev_edit = rev_client.post_note_edit(
                invitation=rev_inv,
                signatures=[user],
                note=openreview.api.Note(
                    id=None if not existing_note else existing_note['id'],
                    content = content,
                    ddate=ddate
                )
            )

            helpers.await_queue_edit(openreview_client, edit_id=rev_edit['id'])

            time.sleep(2) ## Wait for flag process functions

            return rev_edit, pc_client_v2.get_note(test_submission.id)
        
        def now():
            return openreview.tools.datetime_millis(datetime.datetime.now())

        review_inv = test_data_templates[venue.get_area_chairs_id()]['review_invitation']
        user = test_data_templates[venue.get_area_chairs_id()]['user']
        user_client = test_data_templates[venue.get_area_chairs_id()]['client']

        # Test checklist pre-process
        force_justifications = {
                'ethical_concerns': {'value': 'There are no concerns with this submission'}
        }
        with pytest.raises(openreview.OpenReviewException, match=r'You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging.'):
            post_meta_review(user_client, review_inv, user, tested_field='needs_ethics_review', override_fields=force_justifications)
                
        # Post checklist with no ethics flag and no violation field - check that flags are not there
        edit, test_submission = post_meta_review(user_client, review_inv, user)
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' not in test_submission.content
        _, test_submission = post_meta_review(user_client, review_inv, user, ddate=now(), existing_note=edit['note'])

        # Post checklist with no ethics flag and a violation field - check for DSV flag
        edit, test_submission = post_meta_review(user_client, review_inv, user, override_fields={'author_identity_guess': {'value': 5}})
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate > now()

        # Delete checklist - check DSV flag is False, invitation is expired
        _, test_submission = post_meta_review(user_client, review_inv, user, ddate=now(), existing_note=edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate < now()

        # Re-post with no ethics flag and a violation field - check DSV flag is True
        violation_edit, test_submission = post_meta_review(user_client, review_inv, user, override_fields={'author_identity_guess': {'value': 5}})
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate > now()

        # Edit with no ethics flag and no violation field - check DSV flag is False
        violation_edit['note']['content'][violation_fields[0]]['value'] = 1
        _, test_submission = post_meta_review(user_client, review_inv, user, existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate < now()

        # Check that ethics reviewing is not available
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation aclweb.org/ACL/ARR/2023/August/Submission4/-/Ethics_Review was not found'):
            ethics_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Ethics_Review')

        # Edit with ethics flag and no violation field - check DSV flag is false and ethics flag exists and is True
        _, test_submission = post_meta_review(user_client, review_inv, user, tested_field='needs_ethics_review', existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate < now()

        # Delete checklist - check both flags False
        _, test_submission = post_meta_review(user_client, review_inv, user, ddate=now(), existing_note=violation_edit['note'])
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']

        # Ethics reviewing disabled
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation aclweb.org/ACL/ARR/2023/August/Submission4/-/Ethics_Review was not found'):
            ethics_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Ethics_Review')

        # Re-post with no flag - check both flags false
        reviewer_edit, test_submission = post_meta_review(user_client, review_inv, user)
        assert 'flagged_for_ethics_review' not in test_submission.content
        assert 'flagged_for_desk_reject_verification' in test_submission.content
        assert not test_submission.content['flagged_for_desk_reject_verification']['value']
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/-/Desk_Reject_Verification').expdate < now()

        # Make reviews public
        pc_client.post_note(
            openreview.Note(
                content={
                    'setup_meta_review_release_date': (openreview.tools.datetime.datetime.now() - datetime.timedelta(minutes=6)).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Release_Meta_Reviews-0-1', count=1)
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Meta_Review-0-1', count=3)

        review = openreview_client.get_note(reviewer_edit['note']['id'])
        assert len(review.readers) - len(reviewer_edit['note']['readers']) == 1
        assert 'aclweb.org/ACL/ARR/2023/August/Submission4/Authors' in review.readers

        # Check to make sure no emails were sent
        messages = openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been flagged for ethics reviewing')
        assert len(messages) == flagged_messages
        messages = openreview_client.get_messages(to='ec1@aclrollingreview.com', subject='[ARR - August 2023] A submission has been unflagged for ethics reviewing')
        assert len(messages) == unflagged_messages

    def test_emergency_reviewing_forms(self, client, openreview_client, helpers):
        # Update the process functions for each of the unavailability forms, set up the custom max papers
        # invitations and test that each note posts an edge

        # Load the venues
        now = datetime.datetime.now()
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        invitation_builder = openreview.arr.InvitationBuilder(venue)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        pc_client.post_note(
            openreview.Note(
                content={
                    'emergency_reviewing_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'emergency_reviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'emergency_reviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'emergency_metareviewing_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'emergency_metareviewing_due_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'emergency_metareviewing_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Registered_Load')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Emergency_Load')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Reviewers/-/Emergency_Area')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Registered_Load')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Emergency_Load')
        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Emergency_Area')
        
        # Test posting new notes and finding the edges
        reviewer_client = openreview.api.OpenReviewClient(username = 'reviewer1@aclrollingreview.com', password=helpers.strong_password)
        ac_client = openreview.api.OpenReviewClient(username = 'ac2@aclrollingreview.com', password=helpers.strong_password)

        reviewer_note_edit = reviewer_client.post_note_edit( ## Reviewer 1 will have an original load
            invitation=f'{venue.get_reviewers_id()}/-/{invitation_builder.MAX_LOAD_AND_UNAVAILABILITY_NAME}',
            signatures=['~Reviewer_Alternate_ARROne1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 4 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                    'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' },
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=reviewer_note_edit['id'])
        assert len(openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Custom_Max_Papers', tail='~Reviewer_ARROne1')) == 1
        assert openreview_client.get_all_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Custom_Max_Papers', tail='~Reviewer_ARROne1')[0].weight == 4

        test_cases = [
            {   
                'role': venue.get_reviewers_id(),
                'invitation_name': invitation_builder.EMERGENCY_REVIEWING_NAME,
                'client': reviewer_client,
                'user': '~Reviewer_ARROne1',
                'signature': '~Reviewer_Alternate_ARROne1'
            },
            {   
                'role': venue.get_area_chairs_id(),
                'invitation_name': invitation_builder.EMERGENCY_METAREVIEWING_NAME,
                'client': ac_client,
                'user': '~AC_ARRTwo1',
                'signature': '~AC_ARRTwo1'
            }
        ]

        assert len(pc_client_v2.get_edges(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Emergency_Score', tail='~Reviewer_ARROne1')) == 0
        assert len(pc_client_v2.get_edges(invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Emergency_Score', tail='~Reviewer_ARROne1')) == 0

        for case in test_cases:
            role, inv_name, user_client, user, signature = case['role'], case['invitation_name'], case['client'], case['user'], case['signature']

            # Test preprocess
            with pytest.raises(openreview.OpenReviewException, match=r'You have agreed to emergency reviewing, please enter the additional load that you want to be assigned.'):
                user_note_edit = user_client.post_note_edit(
                    invitation=f'{role}/-/{inv_name}',
                    signatures=[signature],
                    note=openreview.api.Note(
                        content = {
                            'emergency_load': { 'value': 0 },
                            'emergency_reviewing_agreement': { 'value': 'Yes' },
                            'research_area': { 'value': ['Code Models'] }
                        }
                    )
                )
            with pytest.raises(openreview.OpenReviewException, match=r'You have agreed to emergency reviewing, please enter your closest relevant research areas.'):
                user_note_edit = user_client.post_note_edit(
                    invitation=f'{role}/-/{inv_name}',
                    signatures=[signature],
                    note=openreview.api.Note(
                        content = {
                            'emergency_reviewing_agreement': { 'value': 'Yes' },
                            'emergency_load': { 'value': 2 },
                        }
                    )
                )

            # Test valid note and check for edges
            user_note_edit = user_client.post_note_edit(
                invitation=f'{role}/-/{inv_name}',
                signatures=[signature],
                note=openreview.api.Note(
                    content = {
                        'emergency_reviewing_agreement': { 'value': 'Yes' },
                        'emergency_load': { 'value': 2 },
                        'research_area': { 'value': ['Code Models'] }
                    }
                )
            )
            
            helpers.await_queue_edit(openreview_client, edit_id=user_note_edit['id'])

            cmp_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Custom_Max_Papers", groupby='tail', select='weight')}
            reg_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Registered_Load", groupby='tail', select='weight')}
            emg_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Load", groupby='tail', select='weight')}
            area_edges = {o['id']['tail']: [j['label'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Area", groupby='tail', select='label')}

            assert all(user in edges for edges in [cmp_edges, reg_edges, emg_edges, area_edges])
            assert all(len(edges[user]) == 1 for edges in [cmp_edges, reg_edges, emg_edges, area_edges])
            cmp_original, reg_original, emg_original = cmp_edges[user][0], reg_edges[user][0], emg_edges[user][0]
    
            if 'Reviewer' in user:
                assert cmp_edges[user][0] == 6
            assert cmp_original == reg_original + emg_original
            assert len(area_edges[user]) == 1
            assert area_edges[user][0] == 'Code Models'

            aggregate_score_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Aggregate_Score", groupby='tail', select='weight')}
            score_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Score", groupby='tail', select='weight')}
            assert all(weight < 10 for weight in score_edges[user])
            assert all(weight < 10 for weight in aggregate_score_edges[user])
            assert len(score_edges[user]) == 101

            # Test editing note
            user_note_edit = user_client.post_note_edit(
                invitation=f'{role}/-/{inv_name}',
                signatures=[user],
                note=openreview.api.Note(
                    id=user_note_edit['note']['id'],
                    content = {
                        'emergency_reviewing_agreement': { 'value': 'Yes' },
                        'emergency_load': { 'value': 4 },
                        'research_area': { 'value': ['Code Models', 'Machine Translation'] }
                    }
                )
            )
            
            helpers.await_queue_edit(openreview_client, edit_id=user_note_edit['id'])

            cmp_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Custom_Max_Papers", groupby='tail', select='weight')}
            reg_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Registered_Load", groupby='tail', select='weight')}
            emg_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Load", groupby='tail', select='weight')}
            area_edges = {o['id']['tail']: [j['label'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Area", groupby='tail', select='label')}

            assert all(user in edges for edges in [cmp_edges, reg_edges, emg_edges, area_edges])
            assert all(len(edges[user]) == 1 for edges in [cmp_edges, reg_edges, emg_edges])
            if 'Reviewer' in user:
                assert cmp_edges[user][0] == 8
            assert cmp_edges[user][0] != cmp_original
            assert reg_edges[user][0] == reg_original
            assert emg_edges[user][0] != emg_original
            assert cmp_edges[user][0] == reg_edges[user][0] + emg_edges[user][0]
            assert len(area_edges[user]) == 2
            assert area_edges[user][0] == 'Code Models'
            assert area_edges[user][1] == 'Machine Translation'

            aggregate_score_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Aggregate_Score", groupby='tail', select='weight')}
            score_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Score", groupby='tail', select='weight')}
            assert all(weight < 10 for weight in score_edges[user])
            assert all(weight < 10 for weight in aggregate_score_edges[user])
            assert len(score_edges[user]) == 101

            # Test set agreement to no
            user_note_edit = user_client.post_note_edit(
                invitation=f'{role}/-/{inv_name}',
                signatures=[user],
                note=openreview.api.Note(
                    id=user_note_edit['note']['id'],
                    content = {
                        'emergency_load': { 'value': 0 },
                        'emergency_reviewing_agreement': { 'value': 'No' }
                    }
                )
            )
            
            helpers.await_queue_edit(openreview_client, edit_id=user_note_edit['id'])

            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Custom_Max_Papers", tail=user) == 1
            cmp_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Custom_Max_Papers", groupby='tail', select='weight')}
            assert cmp_edges[user][0] == reg_edges[user][0] ## New custom max papers should just be what was registered with
            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Registered_Load", tail=user) == 0
            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Emergency_Load", tail=user) == 0
            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Emergency_Area", tail=user) == 0

            aggregate_score_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Aggregate_Score", groupby='tail', select='weight')}
            score_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Score", groupby='tail', select='weight')}
            assert user not in score_edges
            assert all(weight < 10 for weight in aggregate_score_edges[user])
            
            # Test deleting note
            user_note_edit = user_client.post_note_edit(
                invitation=f'{role}/-/{inv_name}',
                signatures=[user],
                note=openreview.api.Note(
                    id=user_note_edit['note']['id'],
                    ddate=openreview.tools.datetime_millis(now),
                    content = {
                        'emergency_reviewing_agreement': { 'value': 'Yes' },
                        'emergency_load': { 'value': 4 },
                        'research_area': { 'value': ['Code Models', 'Machine Translation'] }
                    }
                )
            )
            
            helpers.await_queue_edit(openreview_client, edit_id=user_note_edit['id'])

            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Custom_Max_Papers", tail=user) == 1
            cmp_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Custom_Max_Papers", groupby='tail', select='weight')}
            assert cmp_edges[user][0] == reg_edges[user][0] ## New custom max papers should just be what was registered with
            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Registered_Load", tail=user) == 0
            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Emergency_Load", tail=user) == 0
            assert pc_client_v2.get_edges_count(invitation=f"{role}/-/Emergency_Area", tail=user) == 0

            aggregate_score_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Aggregate_Score", groupby='tail', select='weight')}
            score_edges = {o['id']['tail']: [j['weight'] for j in o['values']] for o in pc_client_v2.get_grouped_edges(invitation=f"{role}/-/Emergency_Score", groupby='tail', select='weight')}
            assert user not in score_edges
            assert all(weight < 10 for weight in aggregate_score_edges[user])

    def test_review_issue_forms(self, client, openreview_client, helpers, test_client):
        now = datetime.datetime.now()
        pc_client=openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        venue = openreview.helpers.get_conference(client, request_form.id, 'openreview.net/Support')
        invitation_builder = openreview.arr.InvitationBuilder(venue)
        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        pc_client.post_note(
            openreview.Note(
                content={
                    'review_issue_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'review_issue_exp_date': (due_date).strftime('%Y/%m/%d %H:%M'),
                    'metareview_issue_start_date': (now).strftime('%Y/%m/%d %H:%M'),
                    'metareview_issue_exp_date': (due_date).strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                forum=request_form.id,
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                referent=request_form.id,
                replyto=request_form.id,
                signatures=['~Program_ARRChair1'],
                writers=[],
            )
        )

        helpers.await_queue()

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Review_Issue_Report')

        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Review_Issue_Report-0-1')

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission3/Official_Review4/-/Review_Issue_Report')

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/-/Meta-Review_Issue_Report')
        
        helpers.await_queue_edit(openreview_client, 'aclweb.org/ACL/ARR/2023/August/-/Meta-Review_Issue_Report-0-1')

        assert openreview_client.get_invitation('aclweb.org/ACL/ARR/2023/August/Submission4/Meta_Review4/-/Meta-Review_Issue_Report')

        rating_edit = test_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Submission3/Official_Review4/-/Review_Issue_Report',
            signatures=['aclweb.org/ACL/ARR/2023/August/Submission3/Authors'],
            note=openreview.api.Note(
                content = {
                    "I1_not_specific": {"value": 'The review is not specific enough.'},
                    "I2_reviewer_heuristics": {"value": 'The review exhibits one or more of the reviewer heuristics discussed in the ARR reviewer guidelines: https://aclrollingreview.org/reviewertutorial'},
                    "I3_score_mismatch": {"value": 'The review score(s) do not match the text of the review.'},
                    "I4_unprofessional_tone": {"value": 'The tone of the review does not conform to professional conduct standards.'},
                    "I5_expertise": {"value": 'The review does not evince expertise.'},
                    "I6_type_mismatch": {"value": "The review does not match the type of paper."},
                    "I7_contribution_mismatch": {"value": "The review does not match the type of contribution."},
                    "I8_missing_review": {"value": "The review is missing or is uninformative."},
                    "I9_late_review": {"value": "The review was late."},
                    "I10_unreasonable_requests": {"value": "The reviewer requests experiments that are not needed to demonstrate the stated claim."},
                    "I11_non_response": {"value": "The review does not acknowledge critical evidence in the author response."},
                    "I12_revisions_unacknowledged": {"value": "The review does not acknowledge the revisions"},
                    "I13_other": {"value": "Some other technical violation of the peer review process."},
                    "justification": {"value": "required justification"},
                }
            )
        )

        assert test_client.get_note(rating_edit['note']['id'])

        meta_review_rating_edit = test_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Submission4/Meta_Review4/-/Meta-Review_Issue_Report',
            signatures=['aclweb.org/ACL/ARR/2023/August/Submission4/Authors'],
            note=openreview.api.Note(
                content = {
                    "MI1_not_specific": {"value": 'The meta-review is not specific enough.'},
                    "MI2_technical_problem": {"value": 'The meta-review has a technical issue'},
                    "MI3_guidelines_violation": {"value": 'The meta-review has a serious procedural violation of AC guidelines.'},
                    "MI4_unprofessional_tone": {"value": 'The tone of the meta-review does not conform to professional conduct standards.'},
                    "MI5_author_response": {"value": 'The meta-review does not acknowledge a key aspect of author response.'},
                    "MI6_review_issue_ignored": {"value": "The meta-review fails to take into account a serious review issue."},
                    "MI7_score_mismatch": {"value": "The meta-review score does not match the text."},
                    "MI8_revisions_unacknowledged": {"value": "The meta-review does not acknowledge the revisions."},
                    "MI9_other": {"value": "Some other technical violation of the meta review process."},
                    "metareview_rating_justification": {"value": "required justification"},
                }
            )
        )

        assert test_client.get_note(meta_review_rating_edit['note']['id'])

    def test_reviewer_management_forms(self, client, openreview_client, helpers, test_client):
        """Test all new reviewer management forms: delay notifications, emergency declarations, and performance ratings"""
        
        # Setup clients
        pc_client = openreview.Client(username='pc@aclrollingreview.org', password=helpers.strong_password)
        venue_id = 'aclweb.org/ACL/ARR/2023/August'
        
        # Get submissions for testing
        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        submission = submissions[1]  # Use second submission for testing

        reviewer_group = openreview_client.get_group(f'{venue_id}/Submission{submission.number}/Reviewers')
        reviewer = reviewer_group.members[0]
        anon_rev_groups = openreview_client.get_groups(
            prefix=f'aclweb.org/ACL/ARR/2023/August/Submission{submission.number}/Reviewer_',
            signatory=reviewer
        )
        anon_reviewer_group = anon_rev_groups[0].id
        
        # Get existing reviewers and area chairs
        reviewer_client = openreview.api.OpenReviewClient(username='openreview.net', password=helpers.strong_password)
        reviewer_client.impersonate(reviewer)
        
        # Get venue configuration
        request_form = pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[1]
        
        # Configure dates
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        
        # Enable all new forms via ARR Configuration
        pc_client.post_note(
            openreview.Note(
                content={
                    'delay_notification_start_date': now.strftime('%Y/%m/%d %H:%M'),
                    'delay_notification_exp_date': due_date.strftime('%Y/%m/%d %H:%M'),
                    'emergency_declaration_start_date': now.strftime('%Y/%m/%d %H:%M'),
                    'emergency_declaration_exp_date': due_date.strftime('%Y/%m/%d %H:%M'),
                    'great_or_irresponsible_reviewer_start_date': now.strftime('%Y/%m/%d %H:%M'),
                    'great_or_irresponsible_reviewer_exp_date': due_date.strftime('%Y/%m/%d %H:%M'),
                    'great_or_irresponsible_AC_start_date': now.strftime('%Y/%m/%d %H:%M'),
                    'great_or_irresponsible_AC_exp_date': due_date.strftime('%Y/%m/%d %H:%M')
                },
                forum=request_form.id,
                referent=request_form.id,
                invitation=f'openreview.net/Support/-/Request{request_form.number}/ARR_Configuration',
                readers=['aclweb.org/ACL/ARR/2023/August/Program_Chairs', 'openreview.net/Support'],
                signatures=['~Program_ARRChair1'],
                writers=[]
            )
        )
        
        helpers.await_queue()
        
        # Test 1: Delay Notification Form (Reviewer submitting delay notification)
        assert openreview_client.get_invitation(f'{venue_id}/-/Delay_Notification')
        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/-/Delay_Notification')
        
        # Reviewer submits delay notification for their review
        delay_edit = reviewer_client.post_note_edit(
            invitation=f'{venue_id}/Submission{submission.number}/-/Delay_Notification',
            signatures=[anon_reviewer_group],
            note=openreview.api.Note(
                content={
                    'notification': {'value': 'My review will be submitted on December 25, 2023 at 11:59 PM EST. I have a family emergency that requires immediate attention.'}
                }
            )
        )
        
        assert reviewer_client.get_note(delay_edit['note']['id'])
        delay_note = openreview_client.get_note(delay_edit['note']['id'])
        assert delay_note.content['notification']['value']
        assert 'December 25' in delay_note.content['notification']['value']
        
        # Test 2: Emergency Declaration Form (Reviewer declaring emergency)
        assert openreview_client.get_invitation(f'{venue_id}/-/Emergency_Declaration')
        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/-/Emergency_Declaration')
        
        emergency_edit = reviewer_client.post_note_edit(
            invitation=f'{venue_id}/Submission{submission.number}/-/Emergency_Declaration',
            signatures=[anon_reviewer_group],
            note=openreview.api.Note(
                content={
                    'declaration': {'value': 'Medical'},
                    'explanation': {'value': 'I have been hospitalized and will be unable to complete my review for at least 2 weeks.'}
                }
            )
        )
        
        assert reviewer_client.get_note(emergency_edit['note']['id'])
        emergency_note = openreview_client.get_note(emergency_edit['note']['id'])
        assert emergency_note.content['declaration']['value'] == 'Medical'
        assert 'hospitalized' in emergency_note.content['explanation']['value']
        
        # Test 3: Great or Irresponsible Reviewer Report (AC evaluating reviewer)
        assert openreview_client.get_invitation(f'{venue_id}/-/Great_or_Irresponsible_Reviewer_Report')
        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/-/Great_or_Irresponsible_Reviewer_Report')

        ac_client = openreview.api.OpenReviewClient(username='ac2@aclrollingreview.com', password=helpers.strong_password)
        sac_client = openreview.api.OpenReviewClient(username='sac2@aclrollingreview.com', password=helpers.strong_password)
        ac_group = openreview_client.get_group(f'{venue_id}/Submission3/Area_Chairs')
        ac = ac_group.members[0]
        anon_ac_groups = openreview_client.get_groups(
            prefix=f'aclweb.org/ACL/ARR/2023/August/Submission3/Area_Chair_',
            signatory=ac
        )
        anon_ac_group = anon_ac_groups[0].id
        sac_group = openreview_client.get_group(f'{venue_id}/Submission3/Senior_Area_Chairs')
        
        # AC rates reviewer as great
        great_reviewer_edit = ac_client.post_note_edit(
            invitation=f'{venue_id}/Submission3/Official_Review4/-/Great_or_Irresponsible_Reviewer_Report',
            signatures=[anon_ac_group],
            note=openreview.api.Note(
                content={
                    'rating': {'value': '0: This review merits a \'great reviewer\' award'},
                    'justification': {'value': 'Exceptionally thorough review with constructive feedback and deep engagement with the paper.'}
                }
            )
        )
        
        assert ac_client.get_note(great_reviewer_edit['note']['id'])
        great_reviewer_note = openreview_client.get_note(great_reviewer_edit['note']['id'])
        assert '0:' in great_reviewer_note.content['rating']['value']
        assert 'thorough' in great_reviewer_note.content['justification']['value']
        
        # SAC also evaluates a reviewer as irresponsible
        poor_reviewer_edit = sac_client.post_note_edit(
            invitation=f'{venue_id}/Submission3/Official_Review4/-/Great_or_Irresponsible_Reviewer_Report',
            signatures=[sac_group.id],
            note=openreview.api.Note(
                content={
                    'rating': {'value': '1: This review is unacceptable in quality'},
                    'justification': {'value': 'Review was only two sentences and showed no understanding of the paper.'}
                }
            )
        )
        
        assert sac_client.get_note(poor_reviewer_edit['note']['id'])
        poor_reviewer_note = openreview_client.get_note(poor_reviewer_edit['note']['id'])
        assert '1:' in poor_reviewer_note.content['rating']['value']
        
        # Test 4: Great or Irresponsible AC Report (SAC evaluating AC)
        # Add SAC to Submission 4
        sac_group = openreview_client.get_group(f'{venue_id}/Submission4/Senior_Area_Chairs')
        openreview_client.add_members_to_group(
            f'{venue_id}/Submission4/Senior_Area_Chairs',
            ['~SAC_ARRTwo1']
        )
        
        assert openreview_client.get_invitation(f'{venue_id}/-/Great_or_Irresponsible_AC_Report')
        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/-/Great_or_Irresponsible_AC_Report')
        
        great_ac_edit = sac_client.post_note_edit(
            invitation=f'{venue_id}/Submission4/Meta_Review4/-/Great_or_Irresponsible_AC_Report',
            signatures=[sac_group.id],
            note=openreview.api.Note(
                content={
                    'rating': {'value': '0: This meta-review merits a \'great area chair\' award'},
                    'justification': {'value': 'AC went above and beyond in managing the review process and providing synthesis.'}
                }
            )
        )
        
        assert sac_client.get_note(great_ac_edit['note']['id'])
        great_ac_note = openreview_client.get_note(great_ac_edit['note']['id'])
        assert '0:' in great_ac_note.content['rating']['value']
        assert 'above and beyond' in great_ac_note.content['justification']['value']
    
    def test_email_options(self, client, openreview_client, helpers, test_client, request_page, selenium):
        pc_client = openreview.api.OpenReviewClient(username='pc@aclrollingreview.org', password=helpers.strong_password)
        submissions = pc_client.get_notes(invitation='aclweb.org/ACL/ARR/2023/August/-/Submission', sort='number:asc')
        submissions_by_number = {s.number : s for s in submissions}
        submissions_by_id = {s.id : s for s in submissions}
        now = datetime.datetime.now()
        now_millis = openreview.tools.datetime_millis(now)
    
        ## Build missing data
        # Reviewer who is available and responded to emergency form
        helpers.create_user('reviewer7@aclrollingreview.com', 'Reviewer', 'ARRSeven')
        helpers.create_user('reviewer8@aclrollingreview.com', 'Reviewer', 'ARREight')
        openreview_client.add_members_to_group('aclweb.org/ACL/ARR/2023/August/Reviewers', ['~Reviewer_ARRSeven1', '~Reviewer_ARREight1'])
        rev_client = openreview.api.OpenReviewClient(username = 'reviewer7@aclrollingreview.com', password=helpers.strong_password)
        rev_two_client = openreview.api.OpenReviewClient(username = 'reviewer2@aclrollingreview.com', password=helpers.strong_password)
        rev_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Max_Load_And_Unavailability_Request',
            signatures=['~Reviewer_ARRSeven1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 6 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'Yes' },
                    'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' }
                }
            )
        )
        rev_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Emergency_Reviewer_Agreement',
            signatures=['~Reviewer_ARRSeven1'],
            note=openreview.api.Note(
                content = {
                    'emergency_reviewing_agreement': { 'value': 'Yes' },
                    'emergency_load': { 'value': 4 },
                    'research_area': { 'value': ['Code Models', 'Machine Translation'] }
                }
            )
        )
        rev_client = openreview.api.OpenReviewClient(username = 'reviewer8@aclrollingreview.com', password=helpers.strong_password)
        rev_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Max_Load_And_Unavailability_Request',
            signatures=['~Reviewer_ARREight1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 6 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'Yes' },
                    'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' }
                }
            )
        )

        # Update reviewer two's fields to cover more cases
        load_note = rev_two_client.get_all_notes(invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Max_Load_And_Unavailability_Request')[0]
        openreview_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/-/Edit',
            readers=['aclweb.org/ACL/ARR/2023/August'],
            writers=['aclweb.org/ACL/ARR/2023/August'],
            signatures=['aclweb.org/ACL/ARR/2023/August'],
            note=openreview.api.Note(
                id=load_note.id,
                ddate=now_millis,
            )
        )
        rev_two_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Max_Load_And_Unavailability_Request',
            signatures=['~Reviewer_ARRTwo1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 6 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'Yes' },
                    'meta_data_donation': { 'value': 'Yes, I consent to donating anonymous metadata of my review for research.' }
                }
            )
        )
        rev_two_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Reviewers/-/Emergency_Reviewer_Agreement',
            signatures=['~Reviewer_ARRTwo1'],
            note=openreview.api.Note(
                content = {
                    'emergency_reviewing_agreement': { 'value': 'Yes' },
                    'emergency_load': { 'value': 4 },
                    'research_area': { 'value': ['Code Models', 'Machine Translation'] }
                }
            )
        )
        
    
        ## Build missing data
        # AC that has been assigned 2 papers and responded to 1 (checklist) - paper 4 and 5
        helpers.create_user('ac4@aclrollingreview.com', 'AC', 'ARRFour')
        helpers.create_user('ac5@aclrollingreview.com', 'AC', 'ARRFive')
        helpers.create_user('ac6@aclrollingreview.com', 'AC', 'ARRSix')
        openreview_client.add_members_to_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs', [
            '~AC_ARRFour1',
            '~AC_ARRFive1',
            '~AC_ARRSix1'
        ])
        ac_client = openreview.api.OpenReviewClient(username = 'ac4@aclrollingreview.com', password=helpers.strong_password)
        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment',
            head = submissions[4].id,
            tail = '~AC_ARRFour1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Submission5/Senior_Area_Chairs'],
            weight = 1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation = 'aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment',
            head = submissions[5].id,
            tail = '~AC_ARRFour1',
            signatures = ['aclweb.org/ACL/ARR/2023/August/Submission6/Senior_Area_Chairs'],
            weight = 1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        ac_sig = openreview_client.get_groups(
            prefix=f'aclweb.org/ACL/ARR/2023/August/Submission6/Area_Chair_',
            signatory='~AC_ARRFour1'
        )[0]
        chk_edit = ac_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Submission6/-/Action_Editor_Checklist',
            signatures=[ac_sig.id],
            note=openreview.api.Note(
                content = {
                    "appropriateness" : { "value" : "Yes" },
                    "formatting" : { "value" : "Yes" },
                    "length" : { "value" : "Yes" },
                    "anonymity" : { "value" : "Yes" },
                    "responsible_checklist" : { "value" : "Yes" },
                    "limitations" : { "value" : "Yes" },
                    "number_of_assignments" : { "value" : "Yes" },
                    "diversity" : { "value" : "Yes" },
                    "need_ethics_review" : { "value" : "No" },
                    "potential_violation_justification" : { "value" : "There are no violations with this submission" },
                    "ethics_review_justification" : { "value" : "There is an issue" }
                }
            )
        )

        # AC with load no assignment and responded emergency
        ac_client = openreview.api.OpenReviewClient(username = 'ac5@aclrollingreview.com', password=helpers.strong_password)
        ac_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Max_Load_And_Unavailability_Request',
            signatures=['~AC_ARRFive1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 6 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'Yes' }
                }
            )
        )
        # AC with load no assignment no emergency
        ac_client = openreview.api.OpenReviewClient(username = 'ac6@aclrollingreview.com', password=helpers.strong_password)
        ac_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Max_Load_And_Unavailability_Request',
            signatures=['~AC_ARRSix1'],
            note=openreview.api.Note(
                content = {
                    'maximum_load_this_cycle': { 'value': 6 },
                    'maximum_load_this_cycle_for_resubmissions': { 'value': 'Yes' }
                }
            )
        )
        ac_client.post_note_edit(
            invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Emergency_Metareviewer_Agreement',
            signatures=['~AC_ARRSix1'],
            note=openreview.api.Note(
                content = {
                    'emergency_reviewing_agreement': { 'value': 'Yes' },
                    'emergency_load': { 'value': 4 },
                    'research_area': { 'value': ['Code Models'] }
                }
            )
        )

        def send_email(email_option, role):
            role_tab_id_format = role.replace('_', '-')
            role_message_id_format = role.replace('_', '')
            request_page(selenium, f"http://localhost:3030/group?id=aclweb.org/ACL/ARR/2023/August/Program_Chairs#{role_tab_id_format}-status", pc_client, wait_for_element='header')
            status_table = selenium.find_element(By.ID, f'{role_tab_id_format}-status')
            reviewer_msg_div = status_table.find_element(By.CLASS_NAME, 'ac-status-menu').find_element(By.ID, f'message-{role_message_id_format}s')
            modal_content = reviewer_msg_div.find_element(By.CLASS_NAME, 'modal-dialog').find_element(By.CLASS_NAME, 'modal-content')
            modal_body = modal_content.find_element(By.CLASS_NAME, 'modal-body')
            modal_form = modal_body.find_element(By.CLASS_NAME, 'form-group')
            message_button = status_table.find_element(By.CLASS_NAME, 'message-button')
            message_button.click()
            message_dropdown = message_button.find_element(By.CLASS_NAME, 'message-button-dropdown')
            message_menu = message_dropdown.find_element(By.CLASS_NAME, 'dropdown-select__menu-list')

            custom_funcs = message_menu.find_elements(By.XPATH, '*')

            opts = [e for e in custom_funcs if e.text == email_option][0].click()
            reviewer_msg_div = WebDriverWait(selenium, 10).until(
                lambda driver: driver.find_element(By.ID, f'{role_tab_id_format}-status')
                                .find_element(By.CLASS_NAME, 'ac-status-menu')
                                .find_element(By.ID, f'message-{role_message_id_format}s')
            )
            modal_content = reviewer_msg_div.find_element(By.CLASS_NAME, 'modal-dialog').find_element(By.CLASS_NAME, 'modal-content')
            modal_body = modal_content.find_element(By.CLASS_NAME, 'modal-body')
            modal_form = modal_body.find_element(By.CLASS_NAME, 'form-group')
            
            # Wait for textarea to be interactable and handle the error
            email_body = WebDriverWait(selenium, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'textarea.form-control.message-body[name="message"]'))
            )
            
            # Scroll into view and focus the element
            selenium.execute_script("arguments[0].scrollIntoView(true);", email_body)
            selenium.execute_script("arguments[0].focus();", email_body)
            time.sleep(1)  # Brief pause to ensure element is ready
            
            modal_footer = modal_content.find_element(By.CLASS_NAME, 'modal-footer')
            
            # Send keys to the textarea
            email_body.send_keys(email_option)  
            
            next_buttons = modal_footer.find_element(By.CLASS_NAME, 'btn-primary')
            next_buttons.click()
            next_buttons.click()

            time.sleep(0.5)     

        def users_with_message(email_option, members):
            profile_ids = set()
            email_map = { email : profile.id
                for profile in openreview.tools.get_profiles(
                    openreview_client,
                    members
                )
                for email in profile.content['emails']
            }
            for email, id in email_map.items():
                if any(message['content']['text'].startswith(email_option) for message in openreview_client.get_messages(to=email)):
                    profile_ids.add(id)
            return profile_ids

        reviewer_email_options = [
            'Available Reviewers with No Assignments',
            'Available Reviewers with No Assignments and No Emergency Reviewing Response'
        ]

        reviewers = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Reviewers').members
    
        send_email('Reviewers with assignments', 'reviewer')
        assert users_with_message('Reviewers with assignments', reviewers) == {
            '~Reviewer_ARRTwo1',
            '~Reviewer_ARROne1'
        }

        send_email('Reviewers with at least one incomplete checklist', 'reviewer')
        assert users_with_message('Reviewers with at least one incomplete checklist', reviewers) == {
            '~Reviewer_ARROne1',
            '~Reviewer_ARRTwo1',
            '~Reviewer_ARRFour1'
        }

        send_email('Reviewers with assignments who have submitted 0 reviews', 'reviewer')
        assert users_with_message('Reviewers with assignments who have submitted 0 reviews', reviewers) == {
            '~Reviewer_ARRTwo1'
        }

        send_email('Available reviewers with less than max cap assignments', 'reviewer')
        assert users_with_message('Available reviewers with less than max cap assignments', reviewers) == {
            '~Reviewer_ARRTwo1',
            '~Reviewer_ARROne1'
        }

        send_email('Available reviewers with less than max cap assignments and signed up for emergencies', 'reviewer')
        assert users_with_message('Available reviewers with less than max cap assignments and signed up for emergencies', reviewers) == {
            '~Reviewer_ARRTwo1'
        }

        send_email('Unavailable reviewers (are not in the cycle and without assignments)', 'reviewer')
        assert users_with_message('Unavailable reviewers (are not in the cycle and without assignments)', reviewers) == {
            '~Reviewer_ARRNA1',
            '~Reviewer_ARRSix1',
            '~Reviewer_ARRThree1'
        }

        ac_email_options = [
            'ACs with assigned checklists, none completed',
            'ACs with assigned checklists, not all completed',
        ]

        area_chairs = openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs').members

        ## Test 'Available ACs with No Assignments and No Emergency Metareviewing Response'
        send_email('Available ACs with No Assignments and No Emergency Metareviewing Response', 'area_chair')
        assert users_with_message('Available ACs with No Assignments and No Emergency Metareviewing Response', area_chairs) == {'~AC_ARRFive1'}

        ## Test 'Available Area Chairs with No Assignments'
        send_email('Available ACs with No Assignments', 'area_chair')
        assert users_with_message('Available ACs with No Assignments', area_chairs) == {'~AC_ARRFive1', '~AC_ARRSix1'}

        ## Test 'ACs with any submitted meta-review'
        send_email('ACs with any submitted meta-review', 'area_chair')
        assert users_with_message('ACs with any submitted meta-review', area_chairs) == {'~AC_ARROne1'}

        ## Test 'ACs with assigned checklists, not all completed'
        send_email('ACs with assigned checklists, not all completed', 'area_chair')
        emailed_users = users_with_message('ACs with assigned checklists, not all completed', area_chairs)

        assignment_edges = {
            group['id']['tail']: [edge['head'] for edge in group['values']] for group in openreview_client.get_grouped_edges(
                invitation='aclweb.org/ACL/ARR/2023/August/Area_Chairs/-/Assignment',
                groupby='tail',
                select='head'
            )
        }

        acs_with_missing_checklists = set()
        # Check note data directly
        for ac in area_chairs:
            try:
                assigned_ids = assignment_edges[ac]
            except KeyError:
                continue
            missing_checklists = False

            for sub_id in assigned_ids:
                paper_number = submissions_by_id[sub_id].number
                anon_groups = openreview_client.get_groups(
                    prefix=f'aclweb.org/ACL/ARR/2023/August/Submission{paper_number}/Area_Chair_',
                    signatory=ac
                )
                assert len(anon_groups) == 1
                anon_sig = anon_groups[0]
                checklists = openreview_client.get_all_notes(
                    invitation=f"aclweb.org/ACL/ARR/2023/August/Submission{paper_number}/-/Action_Editor_Checklist",
                    signature=anon_sig.id
                )
                if len(checklists) <= 0:
                    missing_checklists = True
            
            if missing_checklists:
                acs_with_missing_checklists.add(ac)

        assert emailed_users == acs_with_missing_checklists
        assert emailed_users == {'~AC_ARROne1', '~AC_ARRFour1', '~AC_ARRTwo1'}

        ## Test 'ACs with assigned checklists, none completed'
        send_email('ACs with assigned checklists, none completed', 'area_chair')
        emailed_users = users_with_message('ACs with assigned checklists, none completed', area_chairs)

        acs_with_zero_submitted_checklists = set()
        for ac in openreview_client.get_group('aclweb.org/ACL/ARR/2023/August/Area_Chairs').members:
            try:
                assigned_ids = assignment_edges[ac]
            except KeyError:
                continue
            zero_submitted_checklists = True

            for sub_id in assigned_ids:
                paper_number = submissions_by_id[sub_id].number
                anon_groups = openreview_client.get_groups(
                    prefix=f'aclweb.org/ACL/ARR/2023/August/Submission{paper_number}/Area_Chair_',
                    signatory=ac
                )
                assert len(anon_groups) == 1
                anon_sig = anon_groups[0]
                checklists = openreview_client.get_all_notes(
                    invitation=f"aclweb.org/ACL/ARR/2023/August/Submission{paper_number}/-/Action_Editor_Checklist",
                    signature=anon_sig.id
                )
                if len(checklists) > 0:
                    zero_submitted_checklists = False
            
            if zero_submitted_checklists:
                acs_with_zero_submitted_checklists.add(ac)
        print(acs_with_zero_submitted_checklists)

        assert emailed_users == {'~AC_ARRTwo1'}
        assert emailed_users == acs_with_zero_submitted_checklists
