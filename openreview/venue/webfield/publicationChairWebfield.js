// Webfield component
const venue_id = domain.id

const tabs = [{
    name: 'Accepted Submissions',
    query: {
        'content.venueid': venue_id
    }
  }]

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