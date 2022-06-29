// Webfield component
var VENUE_ID = '';
var SUBMISSION_ID = '';

return {
  component: 'AuthorConsole',
  version: 1,
  properties: {
    header: {
      "title": "Author Console",
      "instructions": ""
    },
    isV2Group: true,
    venueId: `${VENUE_ID}`,
    submissionId: `${SUBMISSION_ID}`,
  }
}