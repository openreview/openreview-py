// Webfield component
const VENUE_ID = ''
const SHORT_PHRASE = ''
const SUBMISSION_ID = ''
const REVIEWERS_NAME = ''
const AREA_CHAIRS_NAME = ''
const OFFICIAL_REVIEW_NAME = ''
const META_REVIEW_NAME = ''
const SUBMISSION_NAME = ''
const REVIEW_RATING_NAME = 'rating'
const REVIEW_CONFIDENCE_NAME = 'confidence'
const META_REVIEW_CONFIDENCE_NAME = 'recommendation'
const reviewerAssignmentTitle=null

const areaChairsId=`${VENUE_ID}/${AREA_CHAIRS_NAME}`
const reviewerGroup=`${VENUE_ID}/${REVIEWERS_NAME}`

return {
  component: 'AreaChairConsole',
  version: 1,
  properties: {
    header: {
      "title": "Area Chairs Console",
      "instructions": "<p class=\"dark\">This page provides information and status updates for the " + SHORT_PHRASE + ". It will be regularly updated as the conference progresses, so please check back frequently.</p>", "schedule": "<h4>Coming Soon</h4><p><em><strong>Please check back later for updates.</strong></em></p>"
    },
    apiVersion:2,
    venueId: VENUE_ID,
    reviewerAssignment: {
      showEdgeBrowserUrl: false,
      proposedAssignmentTitle: '',      
      edgeBrowserProposedUrl:`/edges/browse?start=${areaChairsId}/-/Assignment,tail:${user.id}&traverse=${reviewerGroup}/-/Proposed_Assignment,label:${reviewerAssignmentTitle}&edit=${reviewerGroup}/-/Proposed_Assignment,label:${reviewerAssignmentTitle};${reviewerGroup}/-/Invite_Assignment&browse=${reviewerGroup}/-/Aggregate_Score,label:${reviewerAssignmentTitle};${reviewerGroup}/-/Affinity_Score;${reviewerGroup}/-/Bid;${reviewerGroup}/-/Custom_Max_Papers,head:ignore&hide=${reviewerGroup}/-/Conflict&maxColumns=2&referrer=[AC Console](/group?id=${areaChairsId})`,
      edgeBrowserDeployedUrl:`/edges/browse?start=${areaChairsId}/-/Assignment,tail:${user.id}&traverse=${reviewerGroup}/-/Assignment&edit=${reviewerGroup}/-/Invite_Assignment&browse=${reviewerGroup}/-/Affinity_Score;${reviewerGroup}/-/Bid;${reviewerGroup}/-/Custom_Max_Papers,head:ignore;${reviewerGroup}/-/Reviews_Submitted,head:ignore&hide=${reviewerGroup}/-/Conflict&maxColumns=2&referrer=[AC Console](/group?id=${areaChairsId})`,
    },
    submissionInvitationId: SUBMISSION_ID,
    seniorAreaChairsId:'',
    areaChairName: AREA_CHAIRS_NAME,
    submissionName: SUBMISSION_NAME,
    officialReviewName: OFFICIAL_REVIEW_NAME,
    reviewRatingName: REVIEW_RATING_NAME,
    reviewConfidenceName: REVIEW_CONFIDENCE_NAME,
    officialMetaReviewName: META_REVIEW_NAME,
    metaReviewContentField: META_REVIEW_CONFIDENCE_NAME,
    shortPhrase: SHORT_PHRASE,
    enableQuerySearch: true
  }
}