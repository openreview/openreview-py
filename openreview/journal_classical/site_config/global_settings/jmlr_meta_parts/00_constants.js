// webfield_template

/* globals $: false */
/* globals _: false */
/* globals Webfield2: false */

var VENUE_ID = 'JMLR';
var VENUE_DISPLAY_NAME = {{VENUE_DISPLAY_NAME_JSON}};
var SHORT_PHRASE = {{VENUE_SHORT_NAME_JSON}};
var SUBMISSION_ID = VENUE_ID + '/-/Submission';
var ACTION_EDITOR_ID = VENUE_ID + '/Action_Editors';
var REVIEWERS_ID = VENUE_ID + '/Reviewers';
var EDITORS_IN_CHIEF_ID = VENUE_ID + '/Editors_In_Chief';
var PRODUCTION_EDITORS_ID = VENUE_ID + '/Production_Editors';
var EXPERT_REVIEWERS_ID = VENUE_ID + '/Expert_Reviewers';
var OSS_ACTION_EDITORS_ID = VENUE_ID + '/OSS_Action_Editors';
var OSS_ACTION_EDITORS_ENABLED = {{OSS_ACTION_EDITORS_ENABLED_JSON}};
var SUPPORT_JOURNAL_REQUEST_ID = 'OpenReview.net/Support/Journal_Request7';
var JOURNAL_REQUEST_ID = 'ZHVA1iLGAf';
var REVIEWER_RECRUITMENT_ID = REVIEWERS_ID + '/-/Recruitment';
var ACTION_EDITOR_RECRUITMENT_ID = ACTION_EDITOR_ID + '/-/Recruitment';
var EDITORS_IN_CHIEF_EMAIL = '{{EDITORS_IN_CHIEF_EMAIL}}';
var REVIEWERS_AVAILABILITY_ID = REVIEWERS_ID + '/-/Assignment_Availability';
var ACTION_EDITORS_AVAILABILITY_ID = ACTION_EDITOR_ID + '/-/Assignment_Availability';
var BULK_RECRUITMENT_NO_RESPONSE_EXPIRATION_DAYS = {{BULK_RECRUITMENT_NO_RESPONSE_EXPIRATION_DAYS}};
var BULK_INVITE_HASH_SEED = '4567';
var BULK_INVITE_REVIEWER_TEMPLATE_KEY = 'bulk_invite_reviewer_email_template_script';
var BULK_INVITE_ACTION_EDITOR_TEMPLATE_KEY = 'bulk_invite_action_editor_email_template_script';

var PEOPLE_MANAGEMENT_URL = '/group?id=' + encodeURIComponent(VENUE_ID) + '&peopleManagement=1';

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
      'The JMLR editorial team'
    ].join('\n')
  },
  actionEditor: {
    label: 'Action Editors',
    invitationId: ACTION_EDITOR_RECRUITMENT_ID,
    subject: '[JMLR] Invitation to serve as Action Editor for JMLR',
    content: [
      'Dear {{fullname}},',
      '',
      'You have been invited to serve as an Action Editor for the Journal of Machine Learning Research (JMLR).',
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
      'The JMLR editorial team'
    ].join('\n')
  }
};

var jmlrRoleAssignmentState = {};
var jmlrBulkInviteTemplates = {};
var jmlrPeopleManagementSignature = EDITORS_IN_CHIEF_ID;

var ROLE_CONSOLES = [
  {
    groupId: VENUE_ID + '/Authors',
    label: 'Author Console',
    description: 'Manage author tasks.'
  },
  {
    groupId: VENUE_ID + '/Reviewers',
    label: 'Reviewer Console',
    description: 'Manage review assignments and reviewer tasks.'
  },
  {
    groupId: VENUE_ID + '/Action_Editors',
    label: 'Action Editor Console',
    description: 'Manage assigned papers, reviewers, decisions, and camera-ready checks.'
  },
  {
    groupId: VENUE_ID + '/Editors_In_Chief',
    label: 'Editors-in-Chief Console',
    description: 'Manage editorial workflow, roles, assignments, and exceptions.'
  },
  {
    groupId: VENUE_ID + '/Production_Editors',
    label: 'Production Editor Console',
    description: 'Inspect papers and handle publication operations.'
  }
];

var INSTRUCTIONS = [
  'The Journal of Machine Learning Research (JMLR) publishes papers on the theory and methods of machine learning.',
  'For journal information, author guidelines, and published papers, visit <a href="https://www.jmlr.org/" target="_blank" rel="noopener noreferrer">www.jmlr.org</a>.'
].join(' ');
