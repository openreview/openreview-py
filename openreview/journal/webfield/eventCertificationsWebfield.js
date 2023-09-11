// Webfield component
const tabs = []
tabs.push({
  name: 'Accepted Papers',
  query: {
    'content.venueid': domain.id,
    details: 'replyCount,presentation',
    sort: 'pdate:desc'    
  },
  postQuery: {
    'content.event_certification': args.event
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

