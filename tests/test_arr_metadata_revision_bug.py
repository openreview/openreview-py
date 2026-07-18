import openreview
import datetime
from copy import deepcopy
from openreview.stages.arr_content import arr_submission_content


class TestARRMetadataRevisionBug():

    def test_arr_config_creates_metadata_revision_with_customized_submission(self, client, openreview_client, helpers):
        """
        Regression test for the production bug where the Submission_Metadata_Revision
        invitation was not created when ARR_Config was posted because an earlier
        stage in ARRWorkflow.set_workflow (Blind_Submission_License_Agreement)
        crashed with NotMatchError.

        The crash happens whenever the venue's submission content diverges from
        the in-code `arr_submission_content`. This test simulates that by posting
        a Revision with `Additional Submission Options = arr_submission_content -
        {'justification_for_author_changes'}`. The fix sources
        `submission_revision_remove_options` from the venue's actual submission
        stage content, so the BSLA stage no longer references keys that the
        venue's submission does not have, and the workflow completes through
        Submission_Metadata_Revision.
        """

        now = datetime.datetime.now()
        submission_deadline = now + datetime.timedelta(days=3)
        author_consent_end = now + datetime.timedelta(days=2)
        metadata_edit_start = now + datetime.timedelta(days=1)
        metadata_edit_end = now + datetime.timedelta(days=5)

        helpers.create_user('pc-metadatabug@aclrollingreview.org', 'ProgramBug', 'ARRChair')
        pc_client = openreview.Client(username='pc-metadatabug@aclrollingreview.org', password=helpers.strong_password)

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~ProgramBug_ARRChair1'],
            readers=[
                'openreview.net/Support',
                '~ProgramBug_ARRChair1'
            ],
            writers=[],
            content={
                'title': 'ACL Rolling Review 2099 - MetadataBug',
                'Official Venue Name': 'ACL Rolling Review 2099 - MetadataBug',
                'Abbreviated Venue Name': 'ARR - MetadataBug 2099',
                'Official Website URL': 'http://aclrollingreview.org',
                'program_chair_emails': ['pc-metadatabug@aclrollingreview.org'],
                'contact_email': 'pc-metadatabug@aclrollingreview.org',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'senior_area_chairs_assignment': 'Submissions',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers',
                'publication_chairs': 'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2099/08/01',
                'Submission Deadline': submission_deadline.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '10',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'submission_license': ['CC BY-SA 4.0'],
                'venue_organizer_agreement': [
                    'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                    'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                    'When assembling our group of reviewers and meta-reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                    'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                    'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                    'We will treat the OpenReview staff with kindness and consideration.'
                ],
                'senior_area_chair_roles': ['Senior_Area_Chairs'],
                'area_chair_roles': ['Area_Chairs'],
                'reviewer_roles': ['Reviewers'],
            }))

        helpers.await_queue()

        venue_id = 'aclweb.org/ACL/ARR/2099/MetadataBug'

        client.post_note(openreview.Note(
            content={'venue_id': venue_id},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue_edit(
            client,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number)
        )

        # Post a Revision with `Additional Submission Options =
        # arr_submission_content - {'justification_for_author_changes'}`. The PCs
        # have customized the submission form for this cycle and dropped one
        # field. Before the fix, the BSLA stage in set_workflow would still build
        # `submission_revision_remove_options` from the full in-code
        # `arr_submission_content.keys()`, listing a key not in the venue's
        # submission stage -> NotMatchError -> the loop aborts -> the
        # Submission_Metadata_Revision stage is never built.
        customized_submission_content = deepcopy(arr_submission_content)
        customized_submission_content['software']['value']['param']['maxSize'] = 50
        del customized_submission_content['justification_for_author_changes']

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision',
            forum=request_form_note.id,
            readers=[f'{venue_id}/Program_Chairs', 'openreview.net/Support'],
            referent=request_form_note.id,
            replyto=request_form_note.id,
            signatures=['~ProgramBug_ARRChair1'],
            writers=[],
            content={
                'title': 'ACL Rolling Review 2099 - MetadataBug',
                'Official Venue Name': 'ACL Rolling Review 2099 - MetadataBug',
                'Abbreviated Venue Name': 'ARR - MetadataBug 2099',
                'Official Website URL': 'http://aclrollingreview.org',
                'program_chair_emails': ['pc-metadatabug@aclrollingreview.org'],
                'contact_email': 'pc-metadatabug@aclrollingreview.org',
                'Venue Start Date': '2099/08/01',
                'Submission Deadline': submission_deadline.strftime('%Y/%m/%d'),
                'publication_chairs': 'No, our venue does not have Publication Chairs',
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '10',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': customized_submission_content,
                'remove_submission_options': ['keywords'],
            }
        ))
        helpers.await_queue_edit(
            client,
            invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision'
        )

        # Sanity-check the divergence the fix is supposed to tolerate.
        assert 'justification_for_author_changes' in arr_submission_content
        submission_invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission')
        assert 'justification_for_author_changes' not in submission_invitation.edit['note']['content']

        # Post the ARR_Config with author_consent_* (so the BSLA stage runs) and
        # metadata_edit_* dates (the stage we want to verify is built).
        pc_client.post_note(
            openreview.Note(
                content={
                    'author_consent_start_date': now.strftime('%Y/%m/%d %H:%M'),
                    'author_consent_end_date': author_consent_end.strftime('%Y/%m/%d %H:%M'),
                    'metadata_edit_start_date': metadata_edit_start.strftime('%Y/%m/%d %H:%M'),
                    'metadata_edit_end_date': metadata_edit_end.strftime('%Y/%m/%d %H:%M')
                },
                invitation=f'openreview.net/Support/-/Request{request_form_note.number}/ARR_Configuration',
                forum=request_form_note.id,
                readers=[f'{venue_id}/Program_Chairs', 'openreview.net/Support'],
                referent=request_form_note.id,
                replyto=request_form_note.id,
                signatures=['~ProgramBug_ARRChair1'],
                writers=[],
            )
        )

        # ARR_Configuration should complete without error.
        helpers.await_queue()

        # The Submission_Metadata_Revision super invitation must be created with
        # the configured future cdate, and no per-submission child invitations
        # should exist yet (since cdate is in the future).
        metadata_super_invitation = openreview_client.get_invitation(
            f'{venue_id}/-/Submission_Metadata_Revision'
        )
        inner_cdate = metadata_super_invitation.edit['invitation']['cdate']
        assert inner_cdate > openreview.tools.datetime_millis(now)
        assert inner_cdate == openreview.tools.datetime_millis(
            datetime.datetime.strptime(
                metadata_edit_start.strftime('%Y/%m/%d %H:%M'), '%Y/%m/%d %H:%M'
            )
        )

        child_invitations = openreview_client.get_all_invitations(
            invitation=f'{venue_id}/-/Submission_Metadata_Revision'
        )
        assert child_invitations == [], (
            f'Expected no child invitations, found {[i.id for i in child_invitations]}'
        )

        # And the Blind_Submission_License_Agreement super invitation should also
        # have been built (proving the BSLA stage did not blow up).
        assert openreview_client.get_invitation(f'{venue_id}/-/Blind_Submission_License_Agreement')
