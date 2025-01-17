// Webfield component
const tabs = [{
  name: 'Your Consoles',
  type: 'consoles'
}]

const decisionHeadingMap = domain.content.decision_heading_map?.value

if (decisionHeadingMap) {
  for (const [venue, tabName] of Object.entries(decisionHeadingMap)) {
    tabs.push({
      name:tabName,
      query: {
        'content.venue': venue,
        'invitation': domain.content.submission_id?.value
      },
      options: {
        hideWhenEmpty: true,
        enableSearch: true
      }
    })
  }
}

if (domain.content.public_submissions.value && !decisionHeadingMap) {
  tabs.push({
    name: 'Active Submissions',
    query: {
      'content.venueid': domain.content.submission_venue_id?.value
    },
    options: {
      enableSearch: true
    }
  })
}

if (domain.content.public_withdrawn_submissions?.value) {
  tabs.push({
    name: 'Withdrawn Submissions',
    query: {
      'content.venueid': domain.content.withdrawn_venue_id?.value
    },
    options: {
      hideWhenEmpty: true
    }
  })
}

if (domain.content.public_desk_rejected_submissions?.value) {
  tabs.push({
    name: 'Desk Rejected Submissions',
    query: {
      'content.venueid': domain.content.desk_rejected_venue_id?.value
    },
    options: {
      hideWhenEmpty: true
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
    header: {
      title: domain.content.title?.value,
      subtitle: domain.content.subtitle?.value,
      website: domain.content.website?.value,
      contact: domain.content.contact?.value,
      location: domain.content.location.value,
      instructions: domain.content.instructions.value,
      date: domain.content.start_date.value,
      deadline: domain.content.date.value
    },
    submissionId: domain.content.submission_id?.value,
    parentGroupId: domain.parent,
    tabs: tabs
  }
}
