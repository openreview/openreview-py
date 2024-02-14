// Webfield component
const instructions = ''

const title = domain.content.title.value
const submissionInvitationId = domain.content.submission_id.value
const underReviewId = domain.content.under_review_venue_id.value
const decisionPendingId = domain.content.decision_pending_venue_id.value
const certifications = (domain.content.certifications?.value || []).concat(domain.content.eic_certifications?.value || [])
if (domain.content.expert_reviewer_certification?.value) {
  certifications.push(domain.content.expert_reviewer_certification?.value)
}

const tabs = [{
  name: 'Your Consoles',
  type: 'consoles'
}]

if (domain.content.event_certifications?.value) {
  tabs.push({
    name: 'Event Certifications',
    links: domain.content.event_certifications?.value.map(certification => {
      return { name: utils.prettyId(certification), url: `/group?id=${domain.id}/Event_Certifications&event=${certification}` }
    })
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

if (domain.content.videos_url?.value) {
  tabs.push({
    name: 'Accepted Papers with Video',
    links: [
      { name: `${domain.id} Infinite Conference`, url: domain.content.videos_url.value }
    ]
  })
}

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

certifications.forEach(function(certification, index) {
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
    header: {
      title: title,
      instructions: instructions,
    },
    submissionId: submissionInvitationId,
    parentGroupId: domain.parent,
    tabs: tabs
  }
}

