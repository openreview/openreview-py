// Webfield component
const tabs = [{
    name: 'Venue Configuration Requests',
    query: {
      'invitation': 'openreview.net/-/Venue_Configuration_Request'
    },
    options: {
      enableSearch: true
    }
  }]
  

return {
    component: 'VenueHomepage',
    version: 1,
    properties: {
      header: {
        title: 'OpenReview Venue Configuration Requests',
        subtitle: '',
        website: 'https://openreview.net',
        contact: 'info@openreview.net',
        //location: domain.content.location.value,
        instructions: `
**Instructions:** This page displays all venue configuration requests. Click on a request to view more details and to make a decision.        
`,
        //date: domain.content.start_date.value,
        //deadline: domain.content.date.value
      },
      submissionId: 'openreview.net/-/Venue_Configuration_Request',
      //parentGroupId: domain.parent,
      tabs: tabs
    }
  }
  