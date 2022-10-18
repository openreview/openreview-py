// Webfield component
const SUBMISSION_ID = ''
const PARENT_GROUP = ''
const SUBMISSION_VENUE_ID = ''
const WITHDRAWN_VENUE_ID = ''
const DESK_REJECTED_VENUE_ID = ''

const HEADER = {}

const tabs = [{
  name: 'Your Consoles',
  type: 'consoles'
}]

if (SUBMISSION_VENUE_ID) {
  tabs.push({
    name: 'Active Submissions',
    query: {
      'content.venueid': SUBMISSION_VENUE_ID
    },
    options: {
      enableSearch: true
    }
  })
}

if (WITHDRAWN_VENUE_ID) {
  tabs.push({
    name: 'Withdrawn Submissions',
    query: {
      'content.venueid': WITHDRAWN_VENUE_ID
    }
  })
}

if (DESK_REJECTED_VENUE_ID) {
  tabs.push({
    name: 'Desk Rejected Submissions',
    query: {
      'content.venueid': DESK_REJECTED_VENUE_ID
    }
  })
}

tabs.push({
  name: 'Recent Activity',
  type: 'activity'
})
  
return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: HEADER,
    parentGroupId: PARENT_GROUP,
    apiVersion: 2,
    tabs: tabs
  }
}