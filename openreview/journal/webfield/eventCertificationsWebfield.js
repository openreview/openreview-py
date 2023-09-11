// Webfield component
const tabs = []
tabs.push({
  name: 'Accepted Papers',
  query: {
    'content.venueid': domain.id,
    details: 'replyCount,presentation',
    sort: 'pdate:desc'    
  },
  options: {
    postQuery: {
      'content.event_certifications': args.event
    }
  }
})

return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: {
      title: domain.content.title.value,
      subtitle: `Event certification ${utils.prettyId(args.event)}`
    },
    parentGroupId: entity.parent,
    apiVersion: 2,
    tabs: tabs
  }
}

