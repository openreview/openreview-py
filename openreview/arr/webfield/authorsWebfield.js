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
      instructions: `<p class="dark">⚠️ Due to technical limitations of OpenReview, the 'Author Tasks' tab lists only the tasks for this specific account, and only in the author role. <b>See <a href="https://aclrollingreview.org/authors#submission-forms" target="_blank">here</a> for actions expected at submission time from contributors and other authors.</b></p><br>`
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
