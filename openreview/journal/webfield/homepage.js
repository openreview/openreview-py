// Webfield component
// Constants
const submissionInvitationId = ''
const underReviewId = ''
const decisionPendingId = ''
const certifications = []
const header = {}

const tabs = [{
  name: 'Your Consoles',
  type: 'consoles'
}]

tabs.push({
  name: 'Accepted Papers',
  query: {
    'content.venueid': domain.id,
    details: 'replyCount,presentation',
    sort: 'pdate:desc'    
  },
  options: {
    hideWhenEmpty: true
  }
})

tabs.push({
  name: 'Accepted Papers with Video',
  query: {
    invitation: submissionInvitationId,
    'content.venueid': domain.id,
    details: 'replyCount,presentation',
    sort: 'pdate:desc'    
  },
  options: {
    hideWhenEmpty: true
  }
})

tabs.push({
  name: 'Under Review Submissions',
  query: {
    invitation: submissionInvitationId,
    'content.venueid': [underReviewId, decisionPendingId].join(','),
    details: 'replyCount,presentation',
    sort: 'mdate:desc'    
  },
  options: {
    hideWhenEmpty: true
  }
})

tabs.push({
  name: 'All Submissions',
  query: {
    invitation: submissionInvitationId,
    details: 'replyCount,presentation',
    sort: 'mdate:desc'    
  },
  options: {
    hideWhenEmpty: true
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
    },
    options: {
      hideWhenEmpty: true
    }
  })
})

return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: {
      title: header.title,
      instructions: header.instructions,
    },
    submissionId: submissionInvitationId,
    parentGroupId: domain.parent,
    apiVersion: 2,
    tabs: tabs
  }
}

