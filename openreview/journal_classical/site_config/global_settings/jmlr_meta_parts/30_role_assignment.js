var renderRoleColumn = function(config) {
  var roleDisabled = config.disabled ? ' disabled' : '';
  var hasAvailability = !!config.availabilityRole;
  var availabilityDisabled = (config.disabled || !config.checked) ? ' disabled' : '';
  var monthOptions = getMonthOptions(24);
  var availabilityState = getAvailabilityState(config.availabilityData);
  var availabilityMonthValue = getAvailabilityMonthValue(config.availabilityData, monthOptions);
  var stateSelectStyle = ' style="display: block; width: 68px; min-width: 68px; max-width: 68px; height: 24px; padding: 1px 14px 1px 3px; font-size: 11px; line-height: 20px;"';
  var monthSelectStyle = ' style="' + (availabilityState === 'until' ? '' : 'display: none; ') + 'width: 84px; min-width: 84px; max-width: 84px; height: 24px; padding: 1px 14px 1px 3px; font-size: 11px; line-height: 20px; margin-top: 2px;"';
  return '<div class="role-column-control compact-role-control" data-role="' + _.escape(config.role) + '">' +
    '<label class="checkbox mb-1" title="' + _.escape(config.label) + '"><input type="checkbox" class="js-role-checkbox" data-role="' + _.escape(config.role) + '"' + (config.checked ? ' checked' : '') + roleDisabled + '> In</label>' +
    (hasAvailability ? '<select class="form-control input-sm js-role-availability-state" title="Assignment availability" data-availability-role="' + _.escape(config.availabilityRole) + '"' + availabilityDisabled + stateSelectStyle + '>' +
      '<option value="available"' + (availabilityState === 'available' ? ' selected' : '') + '>Avail</option>' +
      '<option value="until"' + (availabilityState === 'until' ? ' selected' : '') + '>Until</option>' +
      '<option value="indefinite"' + (availabilityState === 'indefinite' ? ' selected' : '') + '>Indef</option>' +
    '</select>' +
    '<select class="form-control input-sm js-role-availability-month" title="Next available date" data-availability-role="' + _.escape(config.availabilityRole) + '"' + availabilityDisabled + monthSelectStyle + '>' +
      monthOptions.map(function(option) {
        return '<option value="' + option.value + '"' + (Number(option.value) === availabilityMonthValue ? ' selected' : '') + '>' + _.escape(option.label) + '</option>';
      }).join('') +
    '</select>' : '') +
    (config.disabled ? '<p class="small text-muted mb-0">Group unavailable.</p>' : '') +
  '</div>';
};

var getRoleMembersFromState = function(roleName) {
  return (jmlrRoleAssignmentState && jmlrRoleAssignmentState[roleName] || []).slice();
};

var postRoleGroupMembers = function(groupId, members) {
  return Webfield2.api.post('/groups/edits', {
    invitation: VENUE_ID + '/-/Edit',
    signatures: [VENUE_ID],
    group: {
      id: groupId,
      members: members
    }
  });
};

var setRoleMembership = function(roleName, groupId, profileId, shouldInclude) {
  var members = getRoleMembersFromState(roleName);
  var hadMember = members.includes(profileId);
  if (shouldInclude && !hadMember) {
    members.push(profileId);
  }
  if (!shouldInclude && hadMember) {
    members = members.filter(function(memberId) {
      return memberId !== profileId;
    });
  }
  if (hadMember === shouldInclude) {
    return $.Deferred().resolve().promise();
  }
  return postRoleGroupMembers(groupId, members).then(function() {
    jmlrRoleAssignmentState[roleName] = members;
  });
};

var getAvailabilityLabel = function(state) {
  return state === 'available' ? 'Available' : 'Unavailable';
};

var getAvailabilityWeight = function(state, monthValue) {
  return state === 'until' ? Number(monthValue) : null;
};

var getMonthOptions = function(count) {
  var now = new Date();
  var options = [];
  for (var i = 1; i <= count; i += 1) {
    var month = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + i, 1));
    options.push({
      value: month.getTime(),
      label: month.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
    });
  }
  return options;
};

var getAvailabilityState = function(data) {
  var label = data && data.label || 'Available';
  var weight = Number(data && data.weight);
  if (label === 'Unavailable' && (!weight || weight > Date.now())) {
    return weight ? 'until' : 'indefinite';
  }
  return 'available';
};

var getAvailabilityMonthValue = function(data, monthOptions) {
  var weight = Number(data && data.weight);
  if (weight && weight > Date.now()) {
    return weight;
  }
  return monthOptions[0].value;
};

var postAvailabilityEdge = function(data, state, monthValue) {
  if (!data) {
    return $.Deferred().resolve().promise();
  }
  var label = getAvailabilityLabel(state);
  var weight = getAvailabilityWeight(state, monthValue);
  var currentWeight = data.weight === undefined || data.weight === null ? null : Number(data.weight);
  var edge = {
    invitation: data.invitationId,
    signatures: [jmlrPeopleManagementSignature],
    head: data.headId,
    tail: data.tailId,
    label: label,
    weight: weight
  };
  if (data.edgeId) {
    edge.id = data.edgeId;
  }
  if (data.label === label && currentWeight === weight) {
    return $.Deferred().resolve().promise();
  }
  return Webfield2.api.post('/edges', edge);
};

var bindRoleAssignmentControls = function() {
  var syncAvailabilityMonthVisibility = function(container) {
    container.find('.js-role-availability-state').each(function() {
      var stateSelect = $(this);
      var column = stateSelect.closest('.role-column-control');
      column.find('.js-role-availability-month').toggle(stateSelect.val() === 'until');
    });
  };
  var syncAvailabilityControls = function(source) {
    var role = source.data('availability-role');
    var row = source.closest('tr');
    var column = source.closest('.role-column-control');
    var state = column.find('.js-role-availability-state').val();
    var month = column.find('.js-role-availability-month').val();
    row.find('.js-role-availability-state[data-availability-role="' + role + '"]:enabled').val(state);
    row.find('.js-role-availability-month[data-availability-role="' + role + '"]:enabled').val(month);
    syncAvailabilityMonthVisibility(row);
  };
  var getAvailabilityChoice = function(row, availabilityRole) {
    var stateSelect = row.find('.js-role-availability-state[data-availability-role="' + availabilityRole + '"]').filter(':enabled').first();
    var monthSelect = row.find('.js-role-availability-month[data-availability-role="' + availabilityRole + '"]').filter(':enabled').first();
    return {
      state: stateSelect.length ? stateSelect.val() : 'available',
      monthValue: Number(monthSelect.val())
    };
  };
  var syncActionEditorRoleSelection = function(row, changedRole) {
    var actionEditorCheckbox = row.find('.js-role-checkbox[data-role="actionEditor"]');
    var ossActionEditorCheckbox = row.find('.js-role-checkbox[data-role="ossActionEditor"]');
    if (changedRole === 'ossActionEditor' && ossActionEditorCheckbox.prop('checked')) {
      actionEditorCheckbox.prop('checked', true);
    }
    if (changedRole === 'actionEditor' && !actionEditorCheckbox.prop('checked')) {
      ossActionEditorCheckbox.prop('checked', false);
    }
  };
  var syncRoleColumnControls = function(row) {
    row.find('.role-column-control').each(function() {
      var column = $(this);
      var checkbox = column.find('.js-role-checkbox');
      column.find('.js-role-availability-state, .js-role-availability-month').prop('disabled', !checkbox.prop('checked'));
      syncAvailabilityMonthVisibility(column);
    });
  };
  $('.js-role-checkbox').off('change').on('change', function() {
    var checkbox = $(this);
    var row = checkbox.closest('tr');
    syncActionEditorRoleSelection(row, checkbox.data('role'));
    syncRoleColumnControls(row);
  });
  $('.js-role-availability-state, .js-role-availability-month').off('change').on('change', function() {
    syncAvailabilityControls($(this));
  });
  syncAvailabilityMonthVisibility($(document));
  $('.js-update-role-assignment').off('click').on('click', function() {
    var button = $(this);
    var row = button.closest('tr');
    var control = row.find('.role-assignment-control[data-role-assignment-data]');
    var profileId = control.data('profile-id');
    var roleData = control.data('role-assignment-data');
    var actionEditorAvailabilityData = control.data('action-editor-availability-data');
    var reviewerAvailabilityData = control.data('reviewer-availability-data');
    var isActionEditor = row.find('.js-role-checkbox[data-role="actionEditor"]').prop('checked');
    var isOssActionEditor = row.find('.js-role-checkbox[data-role="ossActionEditor"]').prop('checked');
    var effectiveActionEditor = isActionEditor || isOssActionEditor;
    var isEditorInChief = row.find('.js-role-checkbox[data-role="editorInChief"]').prop('checked');
    var isProductionEditor = row.find('.js-role-checkbox[data-role="productionEditor"]').prop('checked');
    var isReviewer = row.find('.js-role-checkbox[data-role="reviewer"]').prop('checked');
    var actionEditorAvailability = getAvailabilityChoice(row, 'actionEditor');
    var reviewerAvailability = getAvailabilityChoice(row, 'reviewer');
    var requests = [
      setRoleMembership('editorsInChief', EDITORS_IN_CHIEF_ID, profileId, isEditorInChief),
      setRoleMembership('actionEditors', ACTION_EDITOR_ID, profileId, isActionEditor || isOssActionEditor),
      setRoleMembership('reviewers', REVIEWERS_ID, profileId, isReviewer)
    ];
    if (roleData && roleData.productionEditorGroupExists) {
      requests.push(setRoleMembership('productionEditors', PRODUCTION_EDITORS_ID, profileId, isProductionEditor));
    }
    if (effectiveActionEditor) {
      requests.push(postAvailabilityEdge(actionEditorAvailabilityData, actionEditorAvailability.state, actionEditorAvailability.monthValue));
    }
    if (roleData && roleData.ossActionEditorGroupExists) {
      if (OSS_ACTION_EDITORS_ENABLED) {
        requests.push(setRoleMembership('ossActionEditors', OSS_ACTION_EDITORS_ID, profileId, isOssActionEditor));
      }
    }
    if (isReviewer) {
      requests.push(postAvailabilityEdge(reviewerAvailabilityData, reviewerAvailability.state, reviewerAvailability.monthValue));
    }
    button.text('Updating...');
    row.find('button, input, select').prop('disabled', true);
    $.when.apply($, requests).then(function() {
      button.text('Updated').removeClass('btn-primary').addClass('btn-success');
      setTimeout(safeReloadPage, 800);
    }, function(error) {
      var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to update roles.';
      window.alert(message);
      button.text('Update');
      row.find('button, input, select').prop('disabled', false);
    });
  });
};

var renderAssignRolesTable = function(container, rows) {
  Webfield2.ui.renderTable(container, rows, {
    headings: ['#', 'Person', 'EIC', 'AE', 'OSS', 'PE', 'Rev', 'Update'],
    renders: [
      function(data) { return '<strong class="note-number">' + data.number + '</strong>'; },
      Handlebars.templates.committeeSummary,
      renderRoleColumn,
      renderRoleColumn,
      renderRoleColumn,
      renderRoleColumn,
      renderRoleColumn,
      function(data) {
        var roleDataJson = _.escape(JSON.stringify(data.roleAssignmentData));
        var aeAvailabilityJson = _.escape(JSON.stringify(data.actionEditorAvailabilityData));
        var reviewerAvailabilityJson = _.escape(JSON.stringify(data.reviewerAvailabilityData));
        return '<div class="role-assignment-control" data-profile-id="' + _.escape(data.roleAssignmentData.profileId) + '" data-role-assignment-data="' + roleDataJson + '" data-action-editor-availability-data="' + aeAvailabilityJson + '" data-reviewer-availability-data="' + reviewerAvailabilityJson + '">' +
          '<button type="button" class="btn btn-xs btn-primary js-update-role-assignment">Update</button>' +
        '</div>';
      }
    ],
    sortOptions: {
      Name: function(row) { return row.summary.name.toLowerCase(); },
      EIC: function(row) { return row.editorInChiefRoleData.checked ? 0 : 1; },
      Action_Editor: function(row) { return row.roleAssignmentData.isActionEditor ? 0 : 1; },
      OSS_AE: function(row) { return row.roleAssignmentData.isOssActionEditor ? 0 : 1; },
      Production_Editor: function(row) { return row.roleAssignmentData.isProductionEditor ? 0 : 1; },
      Reviewer: function(row) { return row.roleAssignmentData.isReviewer ? 0 : 1; }
    },
    searchProperties: {
      name: ['summary.name'],
      editorInChief: ['editorInChiefRoleData.checked'],
      actionEditor: ['roleAssignmentData.isActionEditor'],
      ossActionEditor: ['roleAssignmentData.isOssActionEditor'],
      productionEditor: ['roleAssignmentData.isProductionEditor'],
      reviewer: ['roleAssignmentData.isReviewer'],
      default: ['summary.name']
    },
    extraClasses: 'console-table',
    pageSize: 10,
    postRenderTable: function() {
      $(container + ' .console-table th').eq(0).css('width', '4%');
      $(container + ' .console-table td').css('vertical-align', 'top');
      $(container + ' .compact-role-control label').css({ display: 'block', margin: '0 0 3px', whiteSpace: 'nowrap' });
      $(container + ' .compact-role-control label').css({ fontSize: '11px', lineHeight: '16px', margin: '0 0 2px' });
      $(container + ' .compact-role-control input').css('margin-right', '2px');
      $(container + ' .compact-role-control select').css('font-size', '11px');
      $(container + ' .js-update-role-assignment').css('white-space', 'nowrap');
      bindRoleAssignmentControls();
    }
  });
};

var renderAssignRolesTab = function(data) {
  jmlrRoleAssignmentState = data.roleAssignmentState;
  $('#assign-roles').html(
    '<div class="people-status-controls mb-3">' +
      '<p class="text-muted">Use this page to update JMLR role membership and assignment availability.</p>' +
      '<p class="small text-muted">OSS AE is a marker on top of the Action Editor role. Selecting OSS AE also selects AE; clearing AE clears OSS AE.</p>' +
    '</div>' +
    '<div id="assign-roles-table"></div>'
  );
  renderAssignRolesTable('#assign-roles-table', data.roleAssignmentRows);
};
