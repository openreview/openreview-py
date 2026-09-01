// Webfield component
// JMLR compatibility layer: Journal owns the standard venue homepage; this
// small override adds only linked-resubmission context and JMLR navigation.
let instructions = `
Journal of Machine Learning Research (JMLR) uses the standard OpenReview
Journal submission and role-console workflow. Use New Submission for a new
manuscript. A permitted Regular resubmission must be started from the previous
paper's Start Resubmission action so the prior paper is linked automatically.

For journal information, visit [jmlr.org](https://www.jmlr.org/).
`

let title = domain.content.title.value
const resubmissionNumber = String(args?.resubmissionOf || '').trim()
const resubmissionUrl = String(args?.previous_JMLR_submission_URL || '').trim()
const isResubmissionRoute = /^\d+$/.test(resubmissionNumber) &&
  /^https:\/\/(?:dev\.)?openreview\.net\/forum\?id=[^&]+/.test(resubmissionUrl)
if (isResubmissionRoute) {
  title = `Resubmission for JMLR Paper ${resubmissionNumber}`
  instructions = `<div id="jmlr-resubmission-inherited-context" class="panel panel-default" style="padding:12px;margin-bottom:12px">
  <p>This native Journal submission form creates a new paper and forum; it is not an independent new submission.</p>
  <p><strong>Previous JMLR submission:</strong> <a href="${resubmissionUrl}">JMLR Paper ${resubmissionNumber}</a></p>
  <p><strong>Track:</strong> Regular (inherited). Keep Regular selected below; a different selection is rejected.</p>
  <p>Use the searchable Authors control to add each author by OpenReview profile.</p>
</div>`
}
const submissionInvitationId = domain.content.submission_id.value
const underReviewId = domain.content.under_review_venue_id.value
const decisionPendingId = domain.content.decision_pending_venue_id.value
const certifications = (domain.content.certifications?.value || []).concat(domain.content.eic_certifications?.value || [])
if (domain.content.expert_reviewer_certification?.value) {
  certifications.push(domain.content.expert_reviewer_certification.value)
}

const tabs = [{ name: 'Your Consoles', type: 'consoles' }]

if (domain.content.event_certifications?.value) {
  tabs.push({
    name: 'Event Certifications',
    links: domain.content.event_certifications.value.map(certification => ({
      name: utils.prettyId(certification),
      url: `/group?id=${domain.id}/Event_Certifications&event=${certification}`
    }))
  })
}

tabs.push({
  name: 'Accepted Papers',
  query: {
    'content.venueid': domain.id,
    details: 'replyCount,presentation',
    sort: 'pdate:desc'
  }
})

tabs.push({
  name: 'Under Review Submissions',
  query: {
    invitation: submissionInvitationId,
    'content.venueid': [underReviewId, decisionPendingId].join(','),
    details: 'replyCount,presentation',
    sort: 'mdate:desc'
  }
})

tabs.push({
  name: 'All Submissions',
  query: {
    invitation: submissionInvitationId,
    details: 'replyCount,presentation',
    sort: 'mdate:desc'
  }
})

certifications.forEach(certification => {
  tabs.push({
    name: certification,
    query: {
      invitation: submissionInvitationId,
      'content.venueid': domain.id,
      'content.certifications': certification,
      details: 'replyCount,presentation',
      sort: 'pdate:desc'
    }
  })
})

return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: { title, instructions },
    submissionId: submissionInvitationId,
    parentGroupId: domain.parent,
    tabs
  }
}
