// webfield_template
/* globals $, Webfield2: false */

var TRACKS_ID = '';
var MANAGE_TRACKS_ID = '';
var EIC_ID = '';
var VENUE_ID = '';

(function () {
  var root = '#invitation-container';
  var tracks = [];
  var escapeHtml = function (value) {
    return $('<div>').text(value == null ? '' : String(value)).html();
  };
  var slug = function (value) {
    var id = String(value || '').replace(/[^A-Za-z0-9_-]+/g, '_').replace(/^_+|_+$/g, '');
    if (!/^[A-Za-z]/.test(id)) id = 'Track_' + id;
    return id.slice(0, 64);
  };
  var sync = function () {
    $('#journal-track-body tr[data-index]').each(function () {
      var row = $(this);
      var track = tracks[Number(row.attr('data-index'))];
      track.name = String(row.find('.track-name').val() || '').trim();
      track.open = row.find('.track-open').prop('checked');
      track.default = row.find('.track-default').prop('checked');
      track.eligibility_mode = row.find('.track-mode').val();
    });
  };
  var render = function () {
    var rows = tracks.map(function (track, index) {
      return '<tr data-index="' + index + '"><td><code>' + escapeHtml(track.id) + '</code></td>' +
        '<td><input class="form-control track-name" value="' + escapeHtml(track.name) + '"></td>' +
        '<td><input class="track-open" type="checkbox" ' + (track.open ? 'checked' : '') + '></td>' +
        '<td><input class="track-default" name="track-default" type="radio" ' + (track.default ? 'checked' : '') + '></td>' +
        '<td><select class="form-control track-mode"><option value="include" ' + (track.eligibility_mode === 'include' ? 'selected' : '') + '>Listed AEs are included</option>' +
        '<option value="exclude" ' + (track.eligibility_mode === 'exclude' ? 'selected' : '') + '>Listed AEs are excluded</option></select></td>' +
        '<td><button class="btn btn-default btn-sm track-up" ' + (index ? '' : 'disabled') + '>Up</button> ' +
        '<button class="btn btn-default btn-sm track-down" ' + (index + 1 < tracks.length ? '' : 'disabled') + '>Down</button> ' +
        '<button class="btn btn-danger btn-sm track-remove">Remove</button></td></tr>';
    }).join('');
    $('#journal-track-body').html(rows);
  };

  $(root).html('<h2>Manage Tracks</h2><p>Open tracks appear on new submissions. Track IDs remain stable; rename with the display name. Tracks used by papers must be closed rather than removed.</p>' +
    '<div class="table-responsive"><table class="table"><thead><tr><th>ID</th><th>Display name</th><th>Open</th><th>Default</th><th>AE eligibility</th><th>Order</th></tr></thead><tbody id="journal-track-body"></tbody></table></div>' +
    '<div class="form-inline"><input id="journal-track-new" class="form-control" placeholder="New track name"> <button id="journal-track-add" class="btn btn-default">Add track</button> <button id="journal-track-save" class="btn btn-primary">Save</button></div><p id="journal-track-status"></p>');
  $(root).on('click', '.track-up,.track-down', function () {
    sync();
    var index = Number($(this).closest('tr').attr('data-index'));
    var other = $(this).hasClass('track-up') ? index - 1 : index + 1;
    var item = tracks[index]; tracks[index] = tracks[other]; tracks[other] = item; render();
  });
  $(root).on('click', '.track-remove', function () {
    sync(); tracks.splice(Number($(this).closest('tr').attr('data-index')), 1); render();
  });
  $('#journal-track-add').on('click', function () {
    sync();
    var name = String($('#journal-track-new').val() || '').trim();
    var id = slug(name);
    if (!name || tracks.some(function (track) { return track.id === id; })) {
      $('#journal-track-status').text(name ? 'That generated track ID already exists.' : 'Enter a track name.'); return;
    }
    tracks.push({id: id, name: name, open: true, default: false, eligibility_mode: 'include'});
    $('#journal-track-new').val(''); render();
  });
  $('#journal-track-save').on('click', function () {
    sync(); $('#journal-track-status').text('Saving...');
    Webfield2.api.post('/groups/edits?awaitProcess=true', {
      invitation: MANAGE_TRACKS_ID,
      signatures: [EIC_ID], readers: ['everyone'], writers: [VENUE_ID],
      group: {id: TRACKS_ID, content: {tracks: {value: tracks}}}
    }).then(function () {
      $('#journal-track-status').text('Saved.');
    }, function (error) {
      $('#journal-track-status').text(error.message || error);
    });
  });
  Webfield2.api.get('/groups', {id: TRACKS_ID}).then(function (result) {
    tracks = result.groups[0].content.tracks.value || []; render(); Webfield2.ui.done();
  }, function (error) {
    $('#journal-track-status').text(error.message || error); Webfield2.ui.done();
  });
}());
