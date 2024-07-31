// Webfield component
const committee_name = entity.id.split('/').slice(-1)[0]
const committee_reviewer_name = committee_name.replace(domain.content.area_chairs_name?.value, domain.content.reviewers_name?.value)
const committee_sac_name = committee_name.replace(domain.content.area_chairs_name?.value, domain.content.senior_area_chairs_name?.value)
const replaceAreaChairName = (invitationId) => invitationId.replace(domain.content.area_chairs_name?.value, committee_name)
const replaceReviewerName = (invitationId) => invitationId.replace(domain.content.reviewers_name?.value, committee_reviewer_name)
const preferredEmailInvitationId = domain.content.preferred_emails_id?.value

const reviewerAssignmentTitle = domain.content.reviewers_proposed_assignment_title?.value
const reviewerGroup = replaceReviewerName(domain.content.reviewers_id?.value)
const startParam = `${replaceAreaChairName(domain.content.area_chairs_assignment_id?.value)},tail:${user.profile.id}`
const traverseProposedParam = `${replaceReviewerName(domain.content.reviewers_proposed_assignment_id?.value)},label:${reviewerAssignmentTitle}`
const traverseParam = `${replaceReviewerName(domain.content.reviewers_assignment_id?.value)}`
const browseInvitations = []
const browseProposedInvitations = [`${reviewerGroup}/-/Aggregate_Score,label:${reviewerAssignmentTitle}`]

if (domain.content.reviewers_affinity_score_id?.value) {
  browseInvitations.push(replaceReviewerName(domain.content.reviewers_affinity_score_id?.value))
  browseProposedInvitations.push(replaceReviewerName(domain.content.reviewers_affinity_score_id?.value))
}

if (domain.content.bid_name?.value) {
  browseInvitations.push(`${reviewerGroup}/-/${domain.content.bid_name?.value}`)
  browseProposedInvitations.push(`${reviewerGroup}/-/${domain.content.bid_name?.value}`)
}

if (domain.content.reviewers_custom_max_papers_id?.value) {
  browseInvitations.push(`${replaceReviewerName(domain.content.reviewers_custom_max_papers_id?.value)},head:ignore`)
  browseProposedInvitations.push(`${replaceReviewerName(domain.content.reviewers_custom_max_papers_id?.value)},head:ignore`)
}

const otherParams = `&hide=${replaceReviewerName(domain.content.reviewers_conflict_id?.value)}&maxColumns=2&preferredEmailInvitationId=${preferredEmailInvitationId}&version=2&referrer=[${committee_name.replaceAll('_', ' ')} Console](/group?id=${entity.id})`

return {
  component: 'AreaChairConsole',
  version: 1,
  properties: {
    header: {
      title: `${committee_name.replaceAll('_', ' ')} Console`,
      instructions: `<p class="dark">This page provides information and status updates for the ${domain.content.subtitle?.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p>`,
    },
    venueId: domain.id,
    reviewerAssignment: {
      showEdgeBrowserUrl: domain.content.enable_reviewers_reassignment?.value,
      proposedAssignmentTitle: reviewerAssignmentTitle,
      edgeBrowserProposedUrl: `/edges/browse?start=${startParam}&traverse=${traverseProposedParam}&edit=${replaceReviewerName(domain.content.reviewers_proposed_assignment_id?.value)},label:${reviewerAssignmentTitle};${replaceReviewerName(domain.content.reviewers_invite_assignment_id?.value)}&browse=${browseProposedInvitations.join(';')}${otherParams}`,
      edgeBrowserDeployedUrl: `/edges/browse?start=${startParam}&traverse=${traverseParam}&edit=${replaceReviewerName(domain.content.reviewers_invite_assignment_id?.value)}&browse=${browseInvitations.join(';')}${otherParams}`,
    },
    submissionInvitationId: domain.content.submission_id?.value,
    messageSubmissionReviewersInvitationId: domain.content.reviewers_message_submission_id?.value,
    seniorAreaChairsId: domain.content.senior_area_chairs_id?.value,
    areaChairName: domain.content.area_chairs_name?.value,
    secondaryAreaChairName: domain.content.secondary_area_chairs_name?.value,
    submissionName: domain.content.submission_name?.value,
    officialReviewName: domain.content.review_name?.value,
    reviewRatingName: domain.content.review_rating?.value,
    reviewConfidenceName: domain.content.review_confidence?.value,
    officialMetaReviewName: domain.content.meta_review_name?.value,
    metaReviewRecommendationName: domain.content.meta_review_recommendation?.value || 'recommendation',
    shortPhrase: domain.content.subtitle?.value,
    enableQuerySearch: true,
    emailReplyTo: domain.content.contact?.value,
    reviewerName: domain.content.reviewers_name?.value,
    anonReviewerName: domain.content.reviewers_anon_name?.value,
    preferredEmailInvitationId: preferredEmailInvitationId,
    ithenticateInvitationId: (domain.content.iThenticate_plagiarism_check_committee_readers?.value || []).includes(domain.content.area_chairs_name?.value) ? domain.content.iThenticate_plagiarism_check_invitation_id?.value : null,
  }
}
