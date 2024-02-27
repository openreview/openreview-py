ae_assignment_email_template = '''Hi {{{{fullname}}}},

With this email, we request that you manage the review process for a new {short_name} submission "{submission_number}: {submission_title}".

As a reminder, {short_name} Action Editors (AEs) are **expected to accept all AE requests** to manage submissions that fall within your expertise and quota. Reasonable exceptions are 1) situations where exceptional personal circumstances (e.g. vacation, health problems) render you incapable of fully performing your AE duties or 2) you have a conflict of interest with one of the authors. If any such exception applies to you, contact us at {contact_info}.

Your first task is to make sure the submitted preprint is appropriate for {short_name} and respects our submission guidelines. Clear cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified {short_name} stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication). If you suspect but are unsure about whether a submission might need to be desk rejected for any other reasons (e.g. lack of fit with the scope of {short_name} or lack of technical depth), please email us.

Please follow this link to perform this task: {invitation_url}

If you think the submission can continue through {short_name}'s review process, click the button "Under Review". Otherwise, click on "Desk Reject". Once the submission has been confirmed, then the review process will begin, and your next step will be to assign {number_of_reviewers} reviewers to the paper. You will get a follow up email when OpenReview is ready for you to assign these {number_of_reviewers} reviewers.

We thank you for your essential contribution to {short_name}!

The {short_name} Editors-in-Chief
'''

ae_unassignment_email_template = '''Hi {{{{fullname}}}},

We recently informed you that your help was requested to manage the review process for a new {short_name} submission "{submission_number}: {submission_title}".

However, we've just determined that your help was no longer needed for this submission and have unassigned you as the AE for it.

Apologies for the change and thank you for your continued involvement with {short_name}!

The {short_name} Editors-in-Chief
'''

ae_assignment_eic_as_author_email_template = '''Hi {{{{fullname}}}},

You have just been assigned a submission that is authored by one (or more) {short_name} Editors-in-Chief. OpenReview is set up such that the EIC in question will not have access through OpenReview to the identity of the reviewers you'll be assigning. 

However, be mindful not to discuss the submission by email through {short_name}'s EIC mailing lists ({contact_info} or {editors_in_chief_email}), since all EICs receive these emails. Instead, if you need to reach out to EICs by email, only contact the non-conflicted EICs, directly.

We thank you for your cooperation.

The {short_name} Editors-in-Chief
'''

ae_camera_ready_verification_email_template = '''Hi {{{{fullname}}}},

The authors of {short_name} paper {submission_number}: {submission_title} have now submitted the deanonymized camera ready version of their work.

As your final task for this submission, please verify that the camera ready manuscript complies with the {short_name} stylefile, with all author information inserted in the manuscript as well as the link to the OpenReview page for the submission.

Moreover, if the paper was accepted with minor revision, verify that the changes requested have been followed.

Visit the following link to perform this task: {invitation_url}

If any correction is needed, you may contact the authors directly by email or through OpenReview.

The {short_name} Editors-in-Chief
'''

ae_official_recommendation_starts_email_template = '''Hi {{{{fullname}}}},

This email is to let you know, as AE for {short_name} submission "{submission_number}: {submission_title}", that the reviewers for the submission must now submit their official recommendation for the submission, within the next {recommendation_period_length} weeks ({recommendation_duedate}). They have received a separate email from us, informing them of this task.

For more details and guidelines on performing your review, visit {website}.

We thank you for your essential contribution to {short_name}!

The {short_name} Editors-in-Chief
'''

ae_official_recommendation_ends_email_template = '''Hi {{{{fullname}}}},

Thank you for overseeing the review process for {short_name} submission "{submission_number}: {submission_title}".

All reviewers have submitted their official recommendation of a decision for the submission. Therefore it is now time for you to determine a decision for the submission. Before doing so:

- Make sure you have sufficiently discussed with the authors (and possibly the reviewers) any concern you may have about the submission.
- Rate the quality of the reviews submitted by the reviewers. **You will not be able to submit your decision until these ratings have been submitted**. To rate a review, go on the submission's page and click on button "Rating" for each of the reviews.

We ask that you submit your decision **within {decision_period_length} week** ({decision_duedate}). To do so, please follow this link: {invitation_url}

The possible decisions are:
- **Accept as is**: once its camera ready version is submitted, the manuscript will be marked as accepted.
- **Accept with minor revision**: to use if you wish to request some specific revisions to the manuscript, to be specified explicitly in your decision comments. These revisions will be expected from the authors when they submit their camera ready version.
- **Reject**: the paper is rejected, but you may indicate whether you would be willing to consider a significantly revised version of the manuscript. Such a revised submission will need to be entered as a new submission, that will also provide a link to this rejected submission as well as a description of the changes made since.

Your decision may also include certification(s) recommendations for the submission (in case of an acceptance).

For more details and guidelines on performing your review, visit {website}.

We thank you for your essential contribution to {short_name}!

The {short_name} Editors-in-Chief
'''

ae_discussion_starts_email_template = '''Hi {{{{fullname}}}},

Now that {number_of_reviewers} reviews have been submitted for submission {submission_number}: {submission_title}, all reviews have been made {review_visibility} and authors and reviewers have been notified that the discussion phase has begun. Please read the reviews and oversee the discussion between the reviewers and the authors. The goal of the reviewers should be to gather all the information they need to be comfortable submitting a decision recommendation to you for this submission. Reviewers will be able to submit their formal decision recommendation starting in **{discussion_period_length} weeks**.

You will find the OpenReview page for this submission at this link: https://openreview.net/forum?id={submission_id}

For more details and guidelines on the {short_name} review process, visit {website}.

We thank you for your essential contribution to {short_name}!

The {short_name} Editors-in-Chief
'''

ae_discussion_too_many_reviewers_email_template = '''Hi {{{{fullname}}}},

It appears that, while submission {submission_number}: {submission_title} now has its minimum of {number_of_reviewers} reviews submitted, there are some additional assigned reviewers who have pending reviews. This may be because you had assigned additional emergency reviewers, e.g. because some of the initially assigned reviewers were late or unresponsive. If that is the case, or generally if these additional reviews are no longer needed, please unassign the extra reviewers and let them know that their review is no longer needed.

Additionally, if any extra reviewer corresponds to a reviewer who was unresponsive, please consider submitting a reviewer report, so we can track such undesirable behavior. You can submit a report through link "Reviewers Report" at the top of your AE console.

For more details and guidelines on the {short_name} review process, visit {website}.

We thank you for your essential contribution to {short_name}!

The {short_name} Editors-in-Chief
'''

ae_reviewer_assignment_starts_email_template = '''Hi {{{{fullname}}}},

With this email, we request that you assign {number_of_reviewers} reviewers to your assigned {short_name} submission "{submission_number}: {submission_title}". The assignments must be completed **within {reviewer_assignment_period_length} week** ({reviewer_assignment_duedate}). To do so, please follow this link: {invitation_url} and click on "Edit Assignment" for that paper in your "Assigned Papers" console.

As a reminder, up to their annual quota of {reviewers_max_papers} reviews per year, reviewers are expected to review all assigned submissions that fall within their expertise. Acceptable exceptions are 1) if they have an unsubmitted review for another {short_name} submission or 2) situations where exceptional personal circumstances (e.g. vacation, health problems) render them incapable of fully performing their reviewing duties.

Once assigned, reviewers will be asked to acknowledge on OpenReview their responsibility to review this submission. This acknowledgement will be made visible to you on the OpenReview page of the submission. If the reviewer has not acknowledged their responsibility a couple of days after their assignment, consider reaching out to them directly to confirm.

We thank you for your essential contribution to {short_name}!

The {short_name} Editors-in-Chief
'''

author_ae_recommendation_email_template = '''Hi {{{{fullname}}}},

Thank you for submitting your work titled "{submission_title}" to {short_name}.

Before the review process starts, you need to submit three or more recommendations for an Action Editor that you believe has the expertise to oversee the evaluation of your work.

To do so, please follow this link: {invitation_url} or check your tasks in the Author Console: https://openreview.net/group?id={venue_id}/Authors

For more details and guidelines on the {short_name} review process, visit {website}.

The {short_name} Editors-in-Chief
'''

author_discussion_starts_email_template = '''Hi {{{{fullname}}}},

Now that {number_of_reviewers} reviews have been submitted for your submission  {submission_number}: {submission_title}, all reviews have been made {review_visibility}. If you haven't already, please read the reviews and start engaging with the reviewers to attempt to address any concern they may have about your submission.

You will have {discussion_period_length} weeks to respond to the reviewers. To maximise the period of interaction and discussion, please respond as soon as possible. The reviewers will be using this time period to hear from you and gather all the information they need. In about {discussion_period_length} weeks ({discussion_cdate}), and no later than {recommendation_period_length} weeks ({recommendation_duedate}), reviewers will submit their formal decision recommendation to the Action Editor in charge of your submission.

Visit the following link to respond to the reviews: https://openreview.net/forum?id={submission_id}

For more details and guidelines on the {short_name} review process, visit {website}.

The {short_name} Editors-in-Chief
note: replies to this email will go to the AE, {assigned_action_editor}.
'''

author_decision_accept_as_is_email_template = '''Hi {{{{fullname}}}},

We are happy to inform you that, based on the evaluation of the reviewers and the recommendation of the assigned Action Editor, your {short_name} submission "{submission_number}: {submission_title}" is accepted as is.

To know more about the decision and submit the deanonymized camera ready version of your manuscript, please follow this link and click on button "Camera Ready Revision": https://openreview.net/forum?id={submission_id}. Please submit the final version of your paper within {camera_ready_period_length} weeks ({camera_ready_duedate}).

In addition to your final manuscript, we strongly encourage you to submit a link to 1) code associated with your and 2) a short video presentation of your work. You can provide these links to the corresponding entries on the revision page.

For more details and guidelines on the {short_name} review process, visit {website}.

We thank you for your contribution to {short_name} and congratulate you for your successful submission!

The {short_name} Editors-in-Chief
'''


author_decision_accept_revision_email_template = '''Hi {{{{fullname}}}},

We are happy to inform you that, based on the evaluation of the reviewers and the recommendation of the assigned Action Editor, your {short_name} submission "{submission_number}: {submission_title}" is accepted with minor revision.

To know more about the decision and submit the deanonymized camera ready version of your manuscript, please follow this link and click on button "Camera Ready Revision": https://openreview.net/forum?id={submission_id}. Please submit the final version of your paper, including the minor revisions requested by the Action Editor, within {camera_ready_period_length} weeks ({camera_ready_duedate}).

The Action Editor responsible for your submission will have provided a description of the revision expected for accepting your final manuscript.

In addition to your final manuscript, we strongly encourage you to submit a link to 1) code associated with your and 2) a short video presentation of your work. You can provide these links to the corresponding entries on the revision page.

For more details and guidelines on the {short_name} review process, visit {website}.

We thank you for your contribution to {short_name} and congratulate you for your successful submission!

The {short_name} Editors-in-Chief
'''

author_decision_reject_email_template = '''Hi {{{{fullname}}}},

We are sorry to inform you that, based on the evaluation of the reviewers and the recommendation of the assigned Action Editor, your {short_name} submission "{submission_number}: {submission_title}" is rejected.

To know more about the decision, please follow this link: https://openreview.net/forum?id={submission_id}

The action editor might have indicated that they would be willing to consider a significantly revised version of the manuscript. If so, a revised submission will need to be entered as a new submission, that must also provide a link to this previously rejected submission as well as a description of the changes made since.

In any case, your submission will remain publicly available on OpenReview. You may decide to reveal your identity and deanonymize your submission on the OpenReview page. Doing so will however preclude you from submitting any revised version of the manuscript to {short_name}.

For more details and guidelines on the {short_name} review process, visit {website}.

The {short_name} Editors-in-Chief
'''

author_desk_reject_email_template = '''Hi {{{{fullname}}}},

We are sorry to inform you that, after consideration by the {role}, your {short_name} submission "{submission_number}: {submission_title}" has been rejected without further review.

Cases of desk rejection include submissions that are not anonymized, submissions that do not use the unmodified {short_name} stylefile and submissions that clearly overlap with work already published in proceedings (or currently under review for publication).

To know more about the decision, please follow this link: https://openreview.net/forum?id={submission_id}

For more details and guidelines on the {short_name} review process, visit {website}.

The {short_name} Editors-in-Chief
'''

reviewer_assignment_email_template = '''Hi {{{{fullname}}}},

With this email, we request that you submit, within {review_period_length} weeks ({review_duedate}) a review for your newly assigned {short_name} submission "{submission_number}: {submission_title}".{submission_length}

Please acknowledge on OpenReview that you have received this review assignment by following this link: {ack_invitation_url}

As a reminder, reviewers are **expected to accept all assignments** for submissions that fall within their expertise and annual quota ({reviewers_max_papers} papers). Acceptable exceptions are 1) if you have an active, unsubmitted review for another {short_name} submission or 2) situations where exceptional personal circumstances (e.g. vacation, health problems) render you incapable of performing your reviewing duties. Based on the above, if you think you should not review this submission, contact your AE directly (you can do so by leaving a comment on OpenReview, with only the Action Editor as Reader).

To submit your review, please follow this link: {invitation_url} or check your tasks in the Reviewers Console: https://openreview.net/group?id={venue_id}/Reviewers#reviewer-tasks

Once submitted, your review will become privately visible to the authors and AE. Then, as soon as {number_of_reviewers} reviews have been submitted, all reviews will become {review_visibility}. For more details and guidelines on performing your review, visit {website}.

We thank you for your essential contribution to {short_name}!

The {short_name} Editors-in-Chief
note: replies to this email will go to the AE, {assigned_action_editor}.
'''

reviewer_unassignment_email_template = '''Hi {{{{fullname}}}},

We recently informed you that your help was requested to review a {short_name} submission "{submission_number}: {submission_title}".

However, it was just determined that your help is no longer needed for this submission and you have been unassigned as a reviewer for it.

If you have any questions, don't hesitate to reach out directly to the Action Editor (AE) for the submission, for example by leaving a comment readable by the AE only, on the OpenReview page for the submission: https://openreview.net/forum?id={submission_id}

Apologies for the change and thank you for your continued involvement with {short_name}!

The {short_name} Editors-in-Chief
note: replies to this email will go to the AE, {assigned_action_editor}.
'''

reviewer_discussion_starts_email_template = '''Hi {{{{fullname}}}},

There are now {number_of_reviewers} reviews that have been submitted for your assigned submission "{submission_number}: {submission_title}" and all reviews have been made {review_visibility}. Please read the other reviews and start engaging with the authors (and possibly the other reviewers and AE) in order to address any concern you may have about the submission. Your goal should be to gather all the information you need **within the next {discussion_period_length} weeks** to be comfortable submitting a decision recommendation for this paper. You will receive an upcoming notification on how to enter your recommendation in OpenReview.

You will find the OpenReview page for this submission at this link: https://openreview.net/forum?id={submission_id}

For more details and guidelines on the {short_name} review process, visit {website}.

We thank you for your essential contribution to {short_name}!

The {short_name} Editors-in-Chief
note: replies to this email will go to the AE, {assigned_action_editor}.
'''

reviewer_official_recommendation_starts_email_template = '''Hi {{{{fullname}}}},

Thank you for submitting your review and engaging with the authors of {short_name} submission "{submission_number}: {submission_title}".

You may now submit your official recommendation for the submission. Before doing so, make sure you have sufficiently discussed with the authors (and possibly the other reviewers and AE) any concerns you may have about the submission.

We ask that you submit your recommendation within {recommendation_period_length} weeks ({recommendation_duedate}). To do so, please follow this link: {invitation_url}

For more details and guidelines on performing your review, visit {website}.

We thank you for your essential contribution to {short_name}!

The {short_name} Editors-in-Chief
note: replies to this email will go to the AE, {assigned_action_editor}.
'''

eic_new_submission_template = '''Hi {{{{fullname}}}},

A new submission has been received for {short_name}.

To view the submission, click here: https://openreview.net/forum?id={submission_id}
'''

author_new_submission_email_template = '''Hi {{{{fullname}}}},

Your submission to {short_name} has been received.

Submission Number: {submission_number}

Title: {submission_title}

To view the submission, click here: https://openreview.net/forum?id={submission_id}
'''

author_official_recommendation_starts_email_template = '''Hi {{{{fullname}}}},

The discussion period has ended and the reviewers will submit their recommendations, after which the AE will enter their final recommendation.

The {short_name} Editors-in-Chief
note: replies to this email will go to the AE, {assigned_action_editor}.
'''