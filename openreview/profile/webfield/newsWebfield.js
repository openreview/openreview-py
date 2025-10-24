// Webfield component
const tabs = [{
  name: 'All Articles',
  query: {
    invitation: `${entity.id}/-/Article`,
    details: 'presentation',
    sort: 'cdate:desc'    
  },
  options: {
    paperDisplayOptions: {
      usePaperHashUrl: true
    }
  }
}]


return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: {
      title: 'OpenReview News',
      subtitle: 'OpenReview Announcements and Updates',
      website: 'https://openreview.net',
      instructions: `
**OpenReview News** is a place to learn about the OpenReview community, new platform features, upcoming events, future plans, new perspectives on peer review, and open science.

**Contributing to the News:**  If you have news or updates that you would like to share with the OpenReview community, please contact the OpenReview support team using the feedback form, available on the "Contact" page linked at the bottom of this page.
`  
    },
    submissionId: `${entity.id}/-/Article`,
    submissionConfirmationMessage: 'Your news article has been uploaded.',
    parentGroupId: entity.parent,
    tabs: tabs
  }
}



