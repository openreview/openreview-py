// Webfield component
const tabs = []
tabs.push({
  name: 'Accepted Papers',
  query: {
    'content.venueid': domain.id,
    details: 'replyCount,presentation',
    sort: 'pdate:desc'    
  }
})

return {
  component: 'VenueHomepage',
  version: 1,
  properties: {
    header: {
      title: domain.content.title.value,
      subtitle: `TODO: event certification ${utils.prettyId(args.event)}`
    },
    parentGroupId: domain.parent,
    apiVersion: 2,
    tabs: tabs
  }
}

