// Webfield component
const committee_name = entity.id.split('/').slice(-1)[0]
const committee_ac_name = committee_name.replace(domain.content.senior_area_chairs_name?.value, domain.content.area_chairs_name?.value)
const committee_reviewer_name = committee_ac_name.replace(domain.content.area_chairs_name?.value, domain.content.reviewers_name?.value)
const replaceAreaChairName = (invitationId) => invitationId.replace(domain.content.area_chairs_name?.value, committee_ac_name)
const replaceReviewerName = (invitationId) => invitationId.replace(domain.content.reviewers_name?.value, committee_reviewer_name)
const preferredEmailInvitationId = domain.content.preferred_emails_id?.value
const startParam = `${replaceAreaChairName(domain.content.area_chairs_assignment_id?.value)},tail:{ac.profile.id}`
const traverseParam = `${replaceReviewerName(domain.content.reviewers_assignment_id?.value)}`
const editParam = `${replaceReviewerName(domain.content.reviewers_invite_assignment_id?.value)}`
const browseInvitations = []
const assignmentInvitation = domain.content.sac_paper_assignments?.value ? null : domain.content.senior_area_chairs_assignment_id?.value
const automaticAssignment = domain.content.automatic_reviewer_assignment?.value
const assignmentUrls = {}

if (domain.content.reviewers_affinity_score_id?.value) {
  browseInvitations.push(replaceReviewerName(domain.content.reviewers_affinity_score_id?.value))
}
if (domain.content.bid_name?.value) {
  browseInvitations.push(replaceReviewerName(`${domain.content.reviewers_id?.value}/-/${domain.content.bid_name?.value}`))
}
if (domain.content.reviewers_custom_max_papers_id?.value) {
  browseInvitations.push(replaceReviewerName(`${domain.content.reviewers_custom_max_papers_id?.value},head:ignore`))
}

const otherParams = `&hide=${replaceReviewerName(domain.content.reviewers_conflict_id?.value)}&maxColumns=2&preferredEmailInvitationId=${preferredEmailInvitationId}&version=2&referrer=[${committee_name.replaceAll('_', ' ')} Console](/group?id=${entity.id})`

const manualReviewerAssignmentUrl = `/edges/browse?traverse=${traverseParam}&edit=${editParam}&browse=${browseInvitations.join(';')}${otherParams}`
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
      instructions: `<p class="dark">This page provides information and status updates for the ${domain.content.subtitle?.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p>`
    },
    venueId: domain.id,
    assignmentInvitation: assignmentInvitation,
    messageSubmissionReviewersInvitationId: domain.content.reviewers_message_submission_id?.value,
    messageSubmissionAreaChairsInvitationId: domain.content.area_chairs_message_submission_id?.value,
    messageAreaChairsInvitationId: domain.content.area_chairs_message_id?.value,
    submissionId: domain.content.submission_id?.value,
    submissionVenueId: domain.content.submission_venue_id?.value,
    withdrawnVenueId: domain.content.withdrawn_venue_id?.value,
    deskRejectedVenueId: domain.content.desk_rejected_venue_id?.value,
    submissionName: domain.content.submission_name?.value,
    reviewerName: domain.content.reviewers_name?.value,
    reviewersId: domain.content.reviewers_id?.value,
    reviewerAssignmentId: domain.content.reviewers_assignment_id?.value,
    assignmentUrls: assignmentUrls,    
    anonReviewerName: domain.content.reviewers_anon_name?.value,
    areaChairName: domain.content.area_chairs_name?.value,
    areaChairsId: domain.content.area_chairs_id?.value,
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
    preferredEmailInvitationId: preferredEmailInvitationId,
    ithenticateInvitationId: (domain.content.iThenticate_plagiarism_check_committee_readers?.value || []).includes(domain.content.senior_area_chairs_name?.value) ? domain.content.iThenticate_plagiarism_check_invitation_id?.value : null,
  }
}
