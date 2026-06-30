var getNextMonthStartOption = function() {
  var now = new Date();
  var timestamp = Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1);
  return {
    value: timestamp,
    label: new Date(timestamp).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
  };
};

var getAvailabilityState = function(edge) {
  if (!edge || edge.label !== 'Unavailable') return 'available';
  if (edge.weight && Number(edge.weight) > Date.now()) return 'until';
  return 'available';
};

var getAvailabilityStatusText = function(edge) {
  var state = getAvailabilityState(edge);
  if (state === 'until') return 'Current setting: unavailable until ' + formatDate(Number(edge.weight)) + '.';
  return 'Current setting: available for new assignments.';
};

var renderAvailabilityForm = function(container, config) {
  var edge = config.edge || null;
  var state = getAvailabilityState(edge);
  var nextMonth = getNextMonthStartOption();
  var currentStatus = getAvailabilityStatusText(edge);

  $(container).append(
    '<details class="assignment-availability-form panel panel-default" style="max-width: 720px; margin: 12px 0;">' +
      '<summary class="panel-heading" style="cursor: pointer;">' +
        '<strong>Assignment Availability</strong>' +
        '<span class="small text-muted js-availability-current" style="margin-left: 8px;">' + _.escape(currentStatus) + '</span>' +
      '</summary>' +
      '<div class="panel-body">' +
        '<p class="text-muted">Use this to pause new JMLR action-editor assignments. You will still keep any papers already assigned to you.</p>' +
        '<div class="form-inline">' +
          '<label for="ae-availability-state" style="margin-right: 6px;">Status:</label>' +
          '<select id="ae-availability-state" class="form-control js-availability-state" style="margin-right: 8px;">' +
            '<option value="available"' + (state === 'available' ? ' selected' : '') + '>Available</option>' +
            '<option value="until"' + (state === 'until' ? ' selected' : '') + '>Unavailable until ' + _.escape(nextMonth.label) + '</option>' +
          '</select>' +
          '<button type="button" class="btn btn-primary js-save-availability">Save</button>' +
        '</div>' +
        '<p class="small text-muted js-availability-month-help" style="margin-top: 8px;">Unavailable pauses resume at the beginning of next month, ' + _.escape(nextMonth.label) + '.</p>' +
        '<p class="small text-muted">For longer absences or to stop receiving assignments indefinitely, contact the Editors-in-Chief.</p>' +
        '<p class="js-availability-status" style="margin-top: 8px;"></p>' +
      '</div>' +
    '</details>'
  );

  var form = $(container).find('.assignment-availability-form').last();

  form.find('.js-save-availability').on('click', function() {
    var button = $(this);
    var status = form.find('.js-availability-status');
    var selectedState = form.find('.js-availability-state').val();
    var edgePayload = {
      invitation: config.invitationId,
      signatures: [config.signatureId || config.tailId],
      readers: uniqueValues(['JMLR/Editors_In_Chief', config.tailId]),
      writers: uniqueValues(['JMLR/Editors_In_Chief', config.tailId]),
      head: config.headId,
      tail: config.tailId,
      label: selectedState === 'available' ? 'Available' : 'Unavailable'
    };
    if (config.edgeId) edgePayload.id = config.edgeId;
    if (selectedState === 'until') edgePayload.weight = nextMonth.value;
    button.prop('disabled', true).text('Saving...');
    status.removeClass('text-danger text-success').text('');
    Webfield2.api.post('/edges', edgePayload).then(function(postedEdge) {
      config.edgeId = postedEdge.id;
      config.edge = postedEdge;
      form.find('.js-availability-current').text(getAvailabilityStatusText(postedEdge));
      status.addClass('text-success').text('Assignment availability saved.');
    }, function(error) {
      var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to save assignment availability.';
      status.addClass('text-danger').text(message);
    }).always(function() {
      button.prop('disabled', false).text('Save');
    });
  });
};

var renderActionEditorConsoleControlsIntro = function(container) {
  $(container).append(
    '<div class="ae-console-controls-intro" style="max-width: 720px; margin: 12px 0;">' +
      '<p><strong>Max Active Papers:</strong> ' + _.escape(ACTION_EDITORS_MAX_PAPERS) + '</p>' +
      '<p class="small text-muted">Maximum number of active JMLR papers assigned to you as action editor at one time. Once this limit is reached, new papers will not be assigned, but valid resubmissions may still return to you for continuity.</p>' +
      '<p class="small text-muted"><strong>New-paper cooldown:</strong> After a new action-editor assignment, ordinary new papers are paused for ' + _.escape(ACTION_EDITOR_NEW_ASSIGNMENT_COOLDOWN_DAYS) + ' days. Valid resubmissions may bypass this cooldown for continuity.</p>' +
    '</div>'
  );
};

var renderExpertiseSelectionLink = function(container) {
  $(container).append(
    '<div class="expertise-selection-link panel panel-default" style="max-width: 720px; margin: 12px 0;">' +
      '<div class="panel-body">' +
        '<p style="margin-bottom: 6px;"><strong>Expertise Selection:</strong></p>' +
        '<a href="/invitation?id=' + ACTION_EDITORS_EXPERTISE_SELECTION_ID + '&referrer=' + referrerUrl + '">Select your expertise</a>' +
      '</div>' +
    '</div>'
  );
};

var renderResubmissionPolicy = function(container) {
  $(container).append(
    '<div class="ae-resubmission-policy" style="max-width: 720px; margin: 12px 0;">' +
      '<p><strong>Resubmissions:</strong> A valid previous JMLR submission returns to the previous action editor through checked assignment logic. This continuity can bypass normal new-paper max-load and cooldown checks, but ordinary new papers still respect AE availability and max active paper limits.</p>' +
    '</div>'
  );
};
