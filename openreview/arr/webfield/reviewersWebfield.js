// Webfield component
const committee_name = entity.id.split('/').slice(-1)[0].replaceAll('_', ' ')
return {
  component: 'ReviewerConsole',
  version: 1,
  properties: {
    header: {
      title: `${committee_name} Console`,
      instructions: `<p class="dark">This page provides information and status updates for ${domain.content.subtitle?.value}. It will be regularly updated as the conference progresses, so please check back frequently.</p>`
    },
    venueId: domain.id,
    reviewerName: domain.content.reviewers_name?.value,
    officialReviewName: domain.content.review_name?.value,
    reviewRatingName: domain.content.review_rating?.value,
    areaChairName: domain.content.area_chairs_name?.value,
    submissionName: domain.content.submission_name?.value,
    submissionInvitationId: domain.content.submission_id?.value,
    customMaxPapersInvitationId: domain.content.reviewers_custom_max_papers_id?.value,
    recruitmentInvitationId: domain.content.reviewers_recruitment_id?.value,
    reviewLoad: '',
    hasPaperRanking: false,
    registrationFormDomainMap: {
      '/Reviewers/-/Registration': 'aclweb.org/ACL/ARR',
      '/Reviewers/-/Max_Load_And_Unavailability_Request': 'aclweb.org/ACL/ARR',
      '/Reviewers/-/License_Agreement': 'aclweb.org/ACL/ARR',
      '/Reviewers/-/Emergency_Reviewer_Agreement': 'aclweb.org/ACL/ARR'
    },
  }
}
