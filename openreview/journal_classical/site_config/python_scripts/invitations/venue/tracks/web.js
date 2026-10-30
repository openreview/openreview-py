// JMLR delta: Journal has no editor for JMLR's public managed-track registry.
(function () {
  var root = '#invitation-container';
  var GROUP = 'JMLR/Tracks';
  var INVITATION = 'JMLR/-/Manage_Tracks';
  var EIC = 'JMLR/Editors_In_Chief';
  var records = [];
  var escapeHtml = function (value) { return $('<div>').text(value == null ? '' : String(value)).html(); };
  var slug = function (value) {
    var id = String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
    if (!/^[a-z]/.test(id)) id = 'track_' + id;
    return id.slice(0, 64);
  };
  var render = function () {
    var rows = records.map(function (track, index) {
      return '<tr data-index="' + index + '"><td><code>' + escapeHtml(track.id) + '</code></td>' +
        '<td><input class="form-control track-name" value="' + escapeHtml(track.name) + '"></td>' +
        '<td><input class="form-control track-start" type="date" value="' + escapeHtml(track.beginning_date || '') + '"></td>' +
        '<td><input class="form-control track-end" type="date" value="' + escapeHtml(track.ending_date || '') + '"></td>' +
        '<td><button class="btn btn-default btn-sm track-up" ' + (index ? '' : 'disabled') + '>Up</button> ' +
        '<button class="btn btn-default btn-sm track-down" ' + (index + 1 < records.length ? '' : 'disabled') + '>Down</button></td></tr>';
    }).join('');
    $('#jmlr-track-body').html(rows || '<tr><td colspan="5">No managed tracks.</td></tr>');
  };
  var sync = function () {
    $('#jmlr-track-body tr[data-index]').each(function () {
      var row = $(this), track = records[Number(row.attr('data-index'))];
      track.name = String(row.find('.track-name').val() || '').trim();
      track.beginning_date = row.find('.track-start').val() || null;
      track.ending_date = row.find('.track-end').val() || null;
    });
  };
  $(root).html('<h2>Manage JMLR Tracks</h2>' +
    '<p>Regular is permanent. Managed tracks are publicly readable, ordered before Regular for matching, and remain in history after they close.</p>' +
    '<p>Beginning and ending dates use Anywhere on Earth (UTC−12). A blank date is unbounded.</p>' +
    '<div class="table-responsive"><table class="table"><thead><tr><th>ID</th><th>Display name</th><th>Beginning</th><th>Ending</th><th>Order</th></tr></thead><tbody id="jmlr-track-body"></tbody></table></div>' +
    '<div class="form-inline"><input id="jmlr-track-new" class="form-control" placeholder="New track name"> <button id="jmlr-track-add" class="btn btn-default">Add track</button> <button id="jmlr-track-save" class="btn btn-primary">Save</button></div><p id="jmlr-track-status"></p>');
  $(root).on('click', '.track-up,.track-down', function () {
    sync();
    var index = Number($(this).closest('tr').attr('data-index'));
    var other = $(this).hasClass('track-up') ? index - 1 : index + 1;
    var item = records[index]; records[index] = records[other]; records[other] = item; render();
  });
  $('#jmlr-track-add').on('click', function () {
    sync();
    var name = String($('#jmlr-track-new').val() || '').trim(), id = slug(name);
    if (!name || records.some(function (track) { return track.id === id; })) {
      $('#jmlr-track-status').text(name ? 'That generated track ID already exists.' : 'Enter a track name.'); return;
    }
    records.push({id: id, name: name, beginning_date: null, ending_date: null});
    $('#jmlr-track-new').val(''); render();
  });
  $('#jmlr-track-save').on('click', function () {
    sync(); $('#jmlr-track-status').text('Saving...');
    Webfield2.api.post('/groups/edits?awaitProcess=true', {
      invitation: INVITATION, signatures: [EIC], readers: [EIC], writers: [EIC],
      group: {id: GROUP, content: {tracks: {value: JSON.stringify(records)}}}
    }).then(
      function () { $('#jmlr-track-status').text('Saved. Submission choices have been refreshed.'); },
      function (error) { $('#jmlr-track-status').text(error.message || error); }
    );
  });
  Webfield2.api.get('/groups', {id: GROUP}).then(function (result) {
    records = JSON.parse(result.groups[0].content.tracks.value || '[]'); render(); Webfield2.ui.done();
  }, function (error) { $('#jmlr-track-status').text(error.message || error); Webfield2.ui.done(); });
}());
