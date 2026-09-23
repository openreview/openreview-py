// webfield_template
/* globals $, Webfield2: false */
var PREPARE_AE_BATCH_ID = '';
var EIC_ID = '';
var VENUE_ID = '';

(function () {
  var root = '#invitation-container';
  var confirmation = 'Desk triage is complete; prepare currently unassigned papers';
  $(root).html('<h2>Prepare Action Editor Batch</h2>' +
    '<p>Prepare all currently unassigned submitted papers for native matching. Coordinate with other Editors-in-Chief and inspect any pending batch before submitting. Preparation does not run Matcher or Deploy.</p>' +
    '<div class="form-group"><label for="ae-batch-label">Batch label</label>' +
    '<input id="ae-batch-label" class="form-control" maxlength="80" autocomplete="off"></div>' +
    '<div class="checkbox"><label><input id="ae-batch-confirm" type="checkbox"> ' + confirmation + '</label></div>' +
    '<button id="ae-batch-submit" class="btn btn-primary">Prepare batch</button>' +
    '<p id="ae-batch-status" role="status" aria-live="polite"></p>');
  $('#ae-batch-submit').on('click', function () {
    var label = String($('#ae-batch-label').val() || '').trim();
    var button = $(this);
    if (!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(label)) {
      $('#ae-batch-status').text('Enter a unique batch label using letters, numbers, underscores or hyphens.');
      return;
    }
    if (!$('#ae-batch-confirm').prop('checked')) {
      $('#ae-batch-status').text('Confirm desk triage before preparing the batch.');
      return;
    }
    button.prop('disabled', true);
    $('#ae-batch-status').text('Preparing batch...');
    Webfield2.api.post('/notes/edits', {
      invitation: PREPARE_AE_BATCH_ID,
      signatures: [EIC_ID], readers: [EIC_ID], writers: [VENUE_ID],
      note: {signatures: [EIC_ID], readers: [EIC_ID], writers: [VENUE_ID],
        content: {batch_label: {value: label}, confirmation: {value: confirmation},
          status: {value: 'Pending'}}}
    }).then(function (edit) {
      var id = edit && edit.note && edit.note.id;
      $('#ae-batch-status').html(id
        ? 'Request submitted. <a href="/forum?id=' + encodeURIComponent(id) + '">Inspect batch request</a> before running Matcher.'
        : 'Request submitted; inspect the batch request before running Matcher.');
    }, function (error) {
      $('#ae-batch-status').text((error.message || String(error)) +
        ' The request outcome may be uncertain. Inspect batch requests and refresh before any retry.');
    });
  });
  Webfield2.ui.done();
}());
