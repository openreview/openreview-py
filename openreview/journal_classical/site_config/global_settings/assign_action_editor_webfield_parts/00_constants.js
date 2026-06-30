// webfield_template
// Remove line above if you don't want this page to be overwriten

/* globals $: false */
/* globals view: false */
/* globals Handlebars: false */
/* globals Webfield2: false */

// Constants
var VENUE_ID = 'JMLR';
var SHORT_PHRASE = {{VENUE_SHORT_NAME_JSON}};
var SUBMISSION_ID = 'JMLR/-/Submission';
var CONSOLE_FETCH_LIMIT = 100000;
var EDITORS_IN_CHIEF_NAME = 'Editors_In_Chief';
var EDITORS_IN_CHIEF_EMAIL = '{{EDITORS_IN_CHIEF_EMAIL}}';
var REVIEWERS_NAME = 'Reviewers';
var ACTION_EDITOR_NAME = 'Action_Editors';
var JOURNAL_REQUEST_ID = 'ZHVA1iLGAf';
var SUPPORT_JOURNAL_REQUEST_ID = 'OpenReview.net/Support/Journal_Request7';
var NUMBER_OF_REVIEWERS = 3;
var PREFERRED_EMAILS_ID = 'JMLR/-/Preferred_Emails';
var ACTION_EDITOR_ID = VENUE_ID + '/' + ACTION_EDITOR_NAME;
var REVIEWERS_ID = VENUE_ID + '/' + REVIEWERS_NAME;
var EDITORS_IN_CHIEF_ID = VENUE_ID + '/' + EDITORS_IN_CHIEF_NAME;
var AUTHORS_ID = VENUE_ID + '/Authors';
var EXPERT_REVIEWERS_ID = VENUE_ID + '/Expert_Reviewers';
var OSS_ACTION_EDITORS_ID = VENUE_ID + '/OSS_Action_Editors';
var OSS_ACTION_EDITORS_ENABLED = {{OSS_ACTION_EDITORS_ENABLED_JSON}};
var PRODUCTION_EDITORS_ID = VENUE_ID + '/Production_Editors';
var AVAILABILITY_NAME = 'Assignment_Availability';

var REVIEWERS_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Assignment';
var REVIEWERS_INVITE_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Invite_Assignment';
var REVIEWERS_ARCHIVED_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Archived_Assignment';
var REVIEWERS_CONFLICT_ID = REVIEWERS_ID + '/-/Conflict';
var REVIEWERS_AFFINITY_SCORE_ID = REVIEWERS_ID + '/-/Affinity_Score';
var REVIEWERS_CUSTOM_MAX_PAPERS_ID = REVIEWERS_ID + '/-/Custom_Max_Papers';
var REVIEWERS_PENDING_REVIEWS_ID = REVIEWERS_ID + '/-/Pending_Reviews';
var REVIEWERS_AVAILABILITY_ID = REVIEWERS_ID + '/-/' + AVAILABILITY_NAME;
var ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT = typeof ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT !== 'undefined'
  ? ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT
  : {};
var PAPER_ACTION_EDITORS_ASSIGNMENT_ID = typeof ASSIGN_AE_ASSIGNMENT_INVITATION_ID !== 'undefined'
  ? ASSIGN_AE_ASSIGNMENT_INVITATION_ID
  : '';
var ACTION_EDITORS_ASSIGNMENT_ID = ACTION_EDITOR_ID + '/-/Assignment';
var ACTION_EDITORS_ARCHIVED_ASSIGNMENT_ID = ACTION_EDITOR_ID + '/-/Archived_Assignment';
var ACTION_EDITORS_CONFLICT_ID = ACTION_EDITOR_ID + '/-/Conflict';
var ACTION_EDITORS_AFFINITY_SCORE_ID = ACTION_EDITOR_ID + '/-/Affinity_Score';
var ACTION_EDITORS_CUSTOM_MAX_PAPERS_ID = ACTION_EDITOR_ID + '/-/Custom_Max_Papers';
var ACTION_EDITORS_RECOMMENDATION_ID = ACTION_EDITOR_ID + '/-/Recommendation';
var ACTION_EDITORS_AVAILABILITY_ID = ACTION_EDITOR_ID + '/-/' + AVAILABILITY_NAME;
var REVIEWER_RECRUITMENT_ID = REVIEWERS_ID + '/-/Recruitment';
var ACTION_EDITOR_RECRUITMENT_ID = ACTION_EDITOR_ID + '/-/Recruitment';
var ACTION_EDITORS_DEFAULT_MAX_PAPERS = {{ACTION_EDITORS_MAX_PAPERS}};
var OSS_ACTION_EDITORS_MAX_PAPERS = {{OSS_ACTION_EDITORS_MAX_PAPERS}};
var ACTION_EDITOR_NEW_ASSIGNMENT_COOLDOWN_DAYS = {{ACTION_EDITOR_NEW_ASSIGNMENT_COOLDOWN_DAYS}};
var EXPERTISE_MODEL = {{EXPERTISE_MODEL_JSON}};
var BULK_RECRUITMENT_NO_RESPONSE_EXPIRATION_DAYS = {{BULK_RECRUITMENT_NO_RESPONSE_EXPIRATION_DAYS}};
var BULK_INVITE_HASH_SEED = '4567';
var BULK_INVITE_REVIEWER_TEMPLATE_KEY = 'bulk_invite_reviewer_email_template_script';
var BULK_INVITE_ACTION_EDITOR_TEMPLATE_KEY = 'bulk_invite_action_editor_email_template_script';

var BULK_INVITE_TEMPLATES = {
  reviewer: {
    label: 'Reviewers',
    invitationId: REVIEWER_RECRUITMENT_ID,
    subject: '[JMLR] Invitation to serve as Reviewer for JMLR',
    content: [
      'Dear {{fullname}},',
      '',
      'You have been nominated by the JMLR editorial board to serve as a reviewer for the Journal of Machine Learning Research (JMLR) in recognition of your expertise and contributions to machine learning research.',
      '',
      'Serving as a JMLR reviewer is an important service to the community. We aim to keep the reviewing duty reasonable: the number of active assignments is limited, and reviewers may adjust their reviewing load when needed, including setting their load to zero at any time.',
      '',
      'JMLR also recognizes outstanding reviewers. Reviewers with strong records, based on the number and quality of completed reviews, will be listed as the JMLR editorial board of reviewers on the JMLR website. This list is updated periodically. Reviewers may opt out of public Top Reviewer listing from the Reviewer Console without affecting review assignments.',
      '',
      'If you are willing to serve as a JMLR reviewer, please accept below.',
      '',
      'Accepting this invitation requires signing in to OpenReview. If you already have an OpenReview account, please log in before opening the Accept link:',
      '',
      '{{SITE_URL}}/login',
      '',
      'If you do not yet have an OpenReview account, please create one, then log in and open the Accept link. OpenReview account sign-in is required to accept this invitation:',
      '',
      '{{SITE_URL}}/signup',
      '',
      'Accept:',
      '{{accept_url}}',
      '',
      'If you prefer not to serve as a reviewer at this time, you may decline below. Declining does not require OpenReview login.',
      '',
      'Decline:',
      '{{decline_url}}',
      '',
      'Thank you for considering this invitation.',
      '',
      'Best regards,',
      'The JMLR Editors-in-Chief'
    ].join('\n')
  },
  actionEditor: {
    label: 'Action Editors',
    invitationId: ACTION_EDITOR_RECRUITMENT_ID,
    subject: '[JMLR] Invitation to serve as Action Editor for JMLR',
    content: [
      'Dear {{fullname}},',
      '',
      'You have been invited by the JMLR Editors-in-Chief to serve as an Action Editor for the Journal of Machine Learning Research (JMLR).',
      '',
      'Action Editors handle assigned submissions, manage reviewer assignment and review progress, and submit editorial decisions according to JMLR policy. As a rough guide, an Action Editor would normally carry up to about {{ACTION_EDITORS_MAX_PAPERS}} active papers, with no two new paper assignments within {{ACTION_EDITOR_NEW_ASSIGNMENT_COOLDOWN_DAYS}} days. Resubmission reassignments may exceed this rough guidance.',
      '',
      'If you are willing to serve as a JMLR Action Editor, please accept below.',
      '',
      'Accepting this invitation requires signing in to OpenReview. If you already have an OpenReview account, please log in before opening the Accept link:',
      '',
      '{{SITE_URL}}/login',
      '',
      'If you do not yet have an OpenReview account, please create one, then log in and open the Accept link. OpenReview account sign-in is required to accept this invitation:',
      '',
      '{{SITE_URL}}/signup',
      '',
      'Accept:',
      '{{accept_url}}',
      '',
      'If you prefer not to serve as an Action Editor at this time, you may decline below. Declining does not require OpenReview login.',
      '',
      'Decline:',
      '{{decline_url}}',
      '',
      'Thank you for considering this invitation.',
      '',
      'Best regards,',
      'The JMLR Editors-in-Chief'
    ].join('\n')
  }
};

var REVIEWER_RATING_MAP = {
  "No rating": 0,
  "Exceeds expectations": 1,
  "Meets expectations": 0,
  "Falls below expectations": -1,
  "Report problem": -2
}
var jmlrRoleAssignmentState = {};
var jmlrBulkInviteTemplates = {};

var HEADER = {
  title: 'Assign Action Editor',
  instructions: ''
};
var JMLR_VENUE_REFERRER = encodeURIComponent('[Go to JMLR homepage](/group?id=' + VENUE_ID + ')');
var SUBMISSION_GROUP_NAME = 'Paper';
var RECOMMENDATION_NAME = 'Recommendation';
var REVIEW_NAME = 'Review';
var DECISION_NAME = 'Decision';
var DECISION_APPROVAL_NAME = 'Decision_Approval';
var CAMERA_READY_REVISION_NAME = 'Camera_Ready_Revision';
var CAMERA_READY_VERIFICATION_NAME = 'Camera_Ready_Verification';
var RETRACTION_NAME = 'Retraction';
var RETRACTION_APPROVAL_NAME = 'Retraction_Approval';
var UNDER_REVIEW_STATUS = VENUE_ID + '/Under_Review';
var SUBMITTED_STATUS = VENUE_ID + '/Submitted';
var ASSIGNING_AE_STATUS = VENUE_ID + '/Assigning_AE';
var ASSIGNED_AE_STATUS = VENUE_ID + '/Assigned_AE';
var RETRACTED_STATUS = VENUE_ID + '/Retracted_Acceptance';
var REJECTED_STATUS = VENUE_ID + '/Rejected';
var DECISION_PENDING_STATUS = VENUE_ID + '/Decision_Pending';
var DAY_MS = 24 * 60 * 60 * 1000;
var DECISION_WITHIN_SIX_MONTHS_MS = 183 * DAY_MS;
var DECISION_WITHIN_NINE_MONTHS_MS = 274 * DAY_MS;
var DECISION_OVER_TWELVE_MONTHS_MS = 365 * DAY_MS;

HEADER.instructions = '';
var institutionDomains = [];
