// Webfield component
const committee_name = entity.id.split('/').slice(-1)[0]
const committee_ac_name = committee_name.replace(domain.content.senior_area_chairs_name?.value, domain.content.area_chairs_name?.value)
const committee_reviewer_name = committee_ac_name.replace(domain.content.area_chairs_name?.value, domain.content.reviewers_name?.value)
const replaceAreaChairName = (invitationId) => invitationId.replace(domain.content.area_chairs_name?.value, committee_ac_name)
const replaceReviewerName = (invitationId) => invitationId.replace(domain.content.reviewers_name?.value, committee_reviewer_name)
const startParam = `${replaceAreaChairName(domain.content.area_chairs_assignment_id?.value)},tail:{ac.profile.id}`
const traverseParam = `${replaceReviewerName(domain.content.reviewers_assignment_id?.value)}`
const editParam = `${replaceReviewerName(domain.content.reviewers_invite_assignment_id?.value)}`
const browseInvitations = []
const assignmentInvitation = domain.content.sac_paper_assignments?.value ? null : domain.content.senior_area_chairs_assignment_id?.value

if (domain.content.reviewers_affinity_score_id?.value) {
  browseInvitations.push(replaceReviewerName(domain.content.reviewers_affinity_score_id?.value))
}
if (domain.content.bid_name?.value) {
  browseInvitations.push(replaceReviewerName(`${domain.content.reviewers_id?.value}/-/${domain.content.bid_name?.value}`))
}
if (domain.content.reviewers_custom_max_papers_id?.value) {
  browseInvitations.push(replaceReviewerName(`${domain.content.reviewers_custom_max_papers_id?.value},head:ignore`))
}

const otherParams = `&hide=${replaceReviewerName(domain.content.reviewers_conflict_id?.value)}&maxColumns=2&version=2&referrer=[Senior Area Chair Console](/group?id=${entity.id})`

const start = `${domain.content.senior_area_chairs_assignment_id?.value},tail:${user.profile.id}`
const traverse = `${domain.content.area_chairs_assignment_id?.value}`
const edit = `${domain.content.area_chairs_assignment_id?.value};${domain.content.area_chairs_assignment_id?.value.replace('Assignment', 'Invite_Assignment')}`
const browse = [
    `${domain.content.area_chairs_id?.value}/-/Agreggate_Score`,
    domain.content.area_chairs_affinity_score_id?.value, 
    `${domain.content.area_chairs_id?.value}/-/Research_Area`,
    `${domain.content.area_chairs_custom_max_papers_id?.value},head:ignore`,
    `${domain.content.area_chairs_id?.value}/-/Registered_Load,head:ignore`,
    `${domain.content.area_chairs_id?.value}/-/Emergency_Load,head:ignore`,
    `${domain.content.area_chairs_id?.value}/-/Emergency,head:ignore`,
    `${domain.content.area_chairs_id?.value}/-/Emergency_Area,head:ignore`,
    
]
const other = `hide=${domain.content.area_chairs_conflict_id?.value}&maxColumns=2&version=2&referrer=[Senior Area Chair Console](/group?id=${entity.id})`

const edgeBrowserLink = `/edges/browse?start=${start}&traverse=${traverse}&edit=${edit}&browse=${browse.join(';')}&${other}`

const assignmentUrls = {}
const reviewersId = domain.content.reviewers_id?.value
const areaChairsId = domain.content.area_chairs_id?.value
const automaticAssignment = domain.content.automatic_reviewer_assignment?.value

const browseReviewerInvitations = [
  domain.content.reviewers_affinity_score_id?.value,
  domain.content.reviewers_conflict_id?.value,
  `${reviewersId}/-/Research_Area`,
  `${reviewersId}/-/Status`,
].join(';')

const headBrowseInvitations = [
  `${reviewersId}/-/Registered_Load`,
  `${reviewersId}/-/Emergency_Load`,
  `${reviewersId}/-/Emergency_Area`,
  `${reviewersId}/-/Reviewing_Resubmissions`,
  `${reviewersId}/-/Author_In_Current_Cycle`,
  `${reviewersId}/-/Seniority`,
].map(invitationId => `${invitationId},head:ignore`).join(';')

const allBrowseInvitations = [
  browseReviewerInvitations,
  headBrowseInvitations,
].join(';')

const manualReviewerAssignmentUrl = `/edges/browse?traverse=${domain.content.reviewers_assignment_id?.value}&edit=${domain.content.reviewers_assignment_id?.value};${domain.content.reviewers_invite_assignment_id?.value}&browse=${allBrowseInvitations}&version=2`
assignmentUrls[domain.content.reviewers_name?.value] = {
  manualAssignmentUrl: manualReviewerAssignmentUrl,
  automaticAssignment: automaticAssignment
}

return {
  component: 'SeniorAreaChairConsole',
  version: 1,
  properties: {
    header: {
      title: `${committee_name.replaceAll('_', ' ')} Console`,
      instructions: `<p class="dark">This page provides information and status updates for the ${domain.content.subtitle?.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p><br><strong>AE Assignment Browser:</strong><a id="edge_browser_url" href="` + edgeBrowserLink + `"> Modify AE Assignments</a>`
    },
    venueId: domain.id,
    assignmentInvitation: assignmentInvitation,
    messageSubmissionReviewersInvitationId: domain.content.reviewers_message_submission_id?.value,
    messageAreaChairsInvitationId: domain.content.area_chairs_message_id?.value,
    submissionId: domain.content.submission_id?.value,
    submissionVenueId: domain.content.submission_venue_id?.value,
    withdrawnVenueId: domain.content.withdrawn_venue_id?.value,
    deskRejectedVenueId: domain.content.desk_rejected_venue_id?.value,
    submissionName: domain.content.submission_name?.value,
    reviewerName: domain.content.reviewers_name?.value,
    assignmentUrls: assignmentUrls,
    reviewersId: reviewersId,
    anonReviewerName: domain.content.reviewers_anon_name?.value,
    areaChairName: domain.content.area_chairs_name?.value,
    areaChairsId: areaChairsId,
    anonAreaChairName: domain.content.area_chairs_anon_name?.value,
    secondaryAreaChairName: domain.content.secondary_area_chairs_name?.value,
    secondaryAnonAreaChairName: domain.content.secondary_area_chairs_anon_name?.value, 
    seniorAreaChairName: domain.content.senior_area_chairs_name?.value,
    reviewRatingName: domain.content.review_rating?.value,
    reviewConfidenceName: domain.content.review_confidence?.value,
    officialReviewName: domain.content.review_name?.value,
    officialMetaReviewName: domain.content.meta_review_name?.value,
    decisionName: domain.content.decision_name?.value,
    metaReviewRecommendationName: domain.content.meta_review_recommendation?.value || 'recommendation',
    shortPhrase: domain.content.subtitle?.value,
    enableQuerySearch: true,
    emailReplyTo: domain.content.contact?.value,
    edgeBrowserDeployedUrl: `/edges/browse?start=${startParam}&traverse=${traverseParam}&edit=${editParam}&browse=${browseInvitations.join(';')}${otherParams}`,
    filterFunction: entity.content?.track?.value && `return note.content?.track?.value==="${entity.content?.track?.value}"`,
    propertiesAllowed: {
      reviewerChecklistCount: `
      console.log(row);
      const invitationToCheck="Reviewer_Checklist"; 
      const checklistReplies = row.note?.details?.replies.filter(reply => {
        const hasReply = reply.invitations.some(invitation => invitation.includes(invitationToCheck)); 
        return hasReply;
      })
      return checklistReplies?.length??0;
      `,
      actionEditorChecklistCount: `
      const invitationToCheck="Action_Editor_Checklist"; 
      const checklistReplies = row.note?.details?.replies.filter(reply => {
        const hasReply = reply.invitations.some(invitation => invitation.includes(invitationToCheck)); 
        return hasReply;
      })
      return checklistReplies?.length??0;
      `
    }
  }
}