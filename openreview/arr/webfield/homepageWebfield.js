// Webfield component
const tabs = [{
    name: 'Your Consoles',
    type: 'consoles'
  }]
  
  tabs.push({
    name: 'Anonymous Pre-prints',
    query: {
      'content.venueid': domain.content.submission_venue_id?.value
    },
    options: {
      postQuery: {
        'readers': 'everyone'
      },
      hideWhenEmpty: true,
      pageSize: 1000
    }
  })
  
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
  
