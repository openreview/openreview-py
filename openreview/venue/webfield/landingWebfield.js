// Webfield component
var GROUP_ID = '';
var PARENT_GROUP_ID = '';
var HEADER = {};
var VENUE_LINKS = [];

return {
  component: 'GroupDirectory',
  version: 1,
  properties: {
    title: HEADER.title,
    subtitle: HEADER.description,
    parentGroupId: PARENT_GROUP_ID,
    links: VENUE_LINKS,
  }
}