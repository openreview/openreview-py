// Webfield component
return {
  component: 'AuthorConsole',
  version: 1,
  properties: {
    header: {
      title: domain.content.title?.value,
      subtitle: domain.content.subtitle?.value,
      website: domain.content.website?.value,
      contact: domain.content.contact?.value,
      instructions: `<p class="dark">This page provides information and status updates for your submissions to ${domain.content.subtitle?.value}. It will be regularly updated as the cycle progresses, so please check back frequently.</p>
<p class="dark">For more information about the ACL Rolling Review process, please visit <a href="https://aclrollingreview.org" target="_blank" rel="nofollow">https://aclrollingreview.org</a>.</p>`
    },
    apiVersion: 2,
    venueId: domain.id,
    submissionId: domain.content.submission_id?.value,
    authorSubmissionField: 'content.authorids',
    officialReviewName: domain.content.review_name?.value,
    decisionName: domain.content.decision_name?.value,
    reviewRatingName: domain.content.review_rating?.value,
    reviewConfidenceName: domain.content.review_confidence?.value,
    authorName: domain.content.authors_name?.value,
    submissionName: domain.content.submission_name?.value,
    wildcardInvitation: domain.id + '.*'
  }
}
