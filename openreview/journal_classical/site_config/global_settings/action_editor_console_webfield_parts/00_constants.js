// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var VENUE_ID = 'JMLR';
var SHORT_PHRASE = {{VENUE_SHORT_NAME_JSON}};
var SUBMISSION_ID = 'JMLR/-/Submission';
var CONSOLE_FETCH_LIMIT = 100000;
var ACTION_EDITOR_NAME = 'Action_Editors';
var REVIEWERS_NAME = 'Reviewers';
var ACTION_EDITOR_ID = VENUE_ID + '/' + ACTION_EDITOR_NAME;
var REVIEW_NAME = 'Review';
var SUBMISSION_GROUP_NAME = 'Paper';
var DECISION_NAME = 'Decision';
var UNDER_REVIEW_STATUS = VENUE_ID + '/Under_Review';
var JOURNAL_REQUEST_ID = 'ZHVA1iLGAf';
var NUMBER_OF_REVIEWERS = 3;
var PREFERRED_EMAILS_ID = 'JMLR/-/Preferred_Emails';
var ACTION_EDITORS_MAX_PAPERS = {{ACTION_EDITORS_MAX_PAPERS}};
var ACTION_EDITOR_NEW_ASSIGNMENT_COOLDOWN_DAYS = {{ACTION_EDITOR_NEW_ASSIGNMENT_COOLDOWN_DAYS}};

var REVIEWERS_ID = VENUE_ID + '/' + REVIEWERS_NAME;
var REVIEWERS_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Assignment';
var REVIEWERS_RECRUITMENT_ID = REVIEWERS_ID + '/-/Recruitment';
var REVIEWERS_INVITE_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Invite_Assignment';
var REVIEWERS_CONFLICT_ID = REVIEWERS_ID + '/-/Conflict';
var REVIEWERS_AFFINITY_SCORE_ID = REVIEWERS_ID + '/-/Affinity_Score';
var REVIEWERS_CUSTOM_MAX_PAPERS_ID = REVIEWERS_ID + '/-/Custom_Max_Papers';
var REVIEWERS_PENDING_REVIEWS_ID = REVIEWERS_ID + '/-/Pending_Reviews';
var ACTION_EDITORS_EXPERTISE_SELECTION_ID = ACTION_EDITOR_ID + '/-/Expertise_Selection';
var CUSTOM_MAX_PAPERS_NAME = 'Custom_Max_Papers';
var AVAILABILITY_NAME = 'Assignment_Availability';
var REVIEWERS_AVAILABILITY_ID = REVIEWERS_ID + '/-/' + AVAILABILITY_NAME;


var SUBMISSION_GROUP_NAME = 'Paper';
var RECOMMENDATION_NAME = 'Recommendation';
var REVIEW_NAME = 'Review';
var DECISION_NAME = 'Decision';
var DECISION_APPROVAL_NAME = 'Decision_Approval';
var CAMERA_READY_REVISION_NAME = 'Camera_Ready_Revision';
var CAMERA_READY_VERIFICATION_NAME = 'Camera_Ready_Verification';
var CAMERA_READY_APPROVED_STATUS = VENUE_ID + '/Camera_Ready_Approved';
var CAMERA_READY_PUBLISHED_STATUS = VENUE_ID + '/Camera_Ready_Published';
var PUBLICATION_RETRACTED_STATUS = VENUE_ID + '/Publication_Retracted';
var ASSIGNED_AE_STATUS = VENUE_ID + '/Assigned_AE';
var UNDER_REVIEW_STATUS = VENUE_ID + '/Under_Review';
var SUBMITTED_STATUS = VENUE_ID + '/Submitted';

var referrerUrl = encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + ')');
var HEADER = {
  title: SHORT_PHRASE + ' Action Editor Console',
  instructions: 'Visit the JMLR website for action-editor guidance.'
};
