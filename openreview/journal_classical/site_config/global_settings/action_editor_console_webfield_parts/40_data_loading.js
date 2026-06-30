var main = function() {
  hideOpenReviewGroupModeBanner();

  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Pending Tasks', 'Active Papers', 'Assigned Papers'],
    referrer: args && args.referrer
  });
  JMLRPermissionHelpers.renderVenueHomepageStrip({ container: '#group-container', venueId: VENUE_ID, $: $ });

  loadData()
    .then(formatData)
    .then(renderData)
    .then(Webfield2.ui.done)
    .fail(Webfield2.ui.errorMessage);
};


var loadData = function() {
  return resolveConsoleRoleProfileId(ACTION_EDITOR_ID, /AE|Action_Editor|ActionEditor/i)
    .then(function(consoleProfileId) {
      var customQuotaInvitationPromise = Webfield2.api.get('/invitations', {
        id: ACTION_EDITOR_ID + '/-/' + CUSTOM_MAX_PAPERS_NAME,
        type: 'edges'
      }).then(function(result) {
        return result.invitations && result.invitations[0];
      });
      var availabilityInvitationPromise = Webfield2.api.get('/invitations', {
        id: ACTION_EDITOR_ID + '/-/' + AVAILABILITY_NAME,
        type: 'edges'
      }).then(function(result) {
        return result.invitations && result.invitations[0];
      });
      var availabilityEdgePromise = consoleProfileId ? Webfield2.api.getAll('/edges', {
        invitation: ACTION_EDITOR_ID + '/-/' + AVAILABILITY_NAME,
        tail: consoleProfileId
      }).then(function(edges) {
        return edges && edges[0];
      }) : $.Deferred().resolve(null).promise();

      if (!consoleProfileId) {
        return $.when(
          $.Deferred().resolve({}).promise(),
          $.Deferred().resolve([]).promise(),
          $.Deferred().resolve([]).promise(),
          $.Deferred().resolve({}).promise(),
          customQuotaInvitationPromise,
          availabilityInvitationPromise,
          availabilityEdgePromise,
          consoleProfileId
        );
      }

      return $.when(
        Webfield2.api.getAll('/edges', {
          tail: consoleProfileId,
          domain: VENUE_ID
        }),
        Webfield2.api.getAll('/groups', {
          prefix: VENUE_ID + '/' + SUBMISSION_GROUP_NAME,
          member: consoleProfileId,
          select: 'id,members',
          domain: VENUE_ID
        }).then(function(groups) {
          return groups || [];
        })
      ).then(function(assignmentEdges, assignedAnonGroups) {
      var assignedNumbers = uniqueValues(activeActionEditorAssignmentPaperNumbers(assignmentEdges).concat(actionEditorPaperNumbersFromAnonGroups(assignedAnonGroups)));

      if (!assignedNumbers.length) {
        return $.when(
          $.Deferred().resolve({}).promise(),
          $.Deferred().resolve([]).promise(),
          $.Deferred().resolve([]).promise(),
          $.Deferred().resolve({}).promise(),
          customQuotaInvitationPromise,
          availabilityInvitationPromise,
          availabilityEdgePromise,
          consoleProfileId
        );
      }

      // Create an array of API calls for each assigned group
      var invitationApiCalls = assignedNumbers.map(function(groupNumber) {
        return Webfield2.api.get('/invitations', { 
          select: 'id,cdate,duedate,expdate',
          prefix: VENUE_ID + '/' + SUBMISSION_GROUP_NAME + groupNumber + '/' // or whatever prefix you need
        });
      });

      // Execute all invitation API calls
      var invitationPromises = $.when.apply($, invitationApiCalls);      
      
      return $.when(
        Webfield2.api.getGroupsByNumber(VENUE_ID, REVIEWERS_NAME, { withProfiles: true }),
        $.Deferred().resolve([]).promise(),
        Webfield2.api.getAllSubmissions(SUBMISSION_ID, { numbers: assignedNumbers, domain: VENUE_ID, limit: CONSOLE_FETCH_LIMIT }),
        invitationPromises.then(function() {
          var results = Array.prototype.slice.call(arguments);
          // If only one result, jQuery doesn't wrap it in an array, so we need to handle that
          var allResults = invitationApiCalls.length === 1 ? [results[0]] : results;
          
          // Flatten all invitations into a single array
          var allInvitations = [];
          allResults.forEach(function(result) {
            if (result && result.invitations && Array.isArray(result.invitations)) {
              allInvitations = allInvitations.concat(result.invitations);
            }
          });
          return _.keyBy(allInvitations, 'id');
        }),
        customQuotaInvitationPromise,
        availabilityInvitationPromise,
        availabilityEdgePromise,
        consoleProfileId
      );
    });
    });
};
