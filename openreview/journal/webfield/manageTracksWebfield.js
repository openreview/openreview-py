// webfield_template
/* globals $, Webfield2: false */

var TRACKS_ID = '';
var MANAGE_TRACKS_ID = '';
var EIC_ID = '';
var VENUE_ID = '';

(function () {
  var root = '#invitation-container';
  var tracks = [];
  var openOnly = false;
  var escapeHtml = function (value) {
    return $('<div>').text(value == null ? '' : String(value)).html().replace(/"/g, '&quot;');
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
    });
    if (tracks.length) tracks[0].open = true;
  };
  var render = function () {
    var rows = tracks.map(function (track, index) {
      if (openOnly && !track.open) return '';
      return '<tr data-index="' + index + '"><td><code>' + escapeHtml(track.id) + '</code></td>' +
        '<td><input class="form-control track-name" value="' + escapeHtml(track.name) + '"></td>' +
        '<td><input class="track-open" type="checkbox" ' + (track.open ? 'checked' : '') +
        (index === 0 ? ' disabled title="The base track is always open"' : '') + '></td>' +
        '<td><button class="btn btn-danger btn-sm track-remove" ' +
        (index === 0 ? 'disabled title="The base track cannot be removed"' : '') +
        '>Remove</button></td></tr>';
    }).join('');
    $('#journal-track-body').html(rows);
  };

  $(root).html('<h2>Manage Tracks</h2><p>The first configured track is the base and remains open. Editors-in-Chief coordinate serial changes. Tracks used by papers must be closed rather than removed.</p>' +
    '<p><label><input id="journal-track-open-only" type="checkbox"> Open only</label></p>' +
    '<div class="table-responsive"><table class="table"><thead><tr><th>ID</th><th>Display name</th><th>Open</th><th>Actions</th></tr></thead><tbody id="journal-track-body"></tbody></table></div>' +
    '<div class="form-inline"><input id="journal-track-new" class="form-control" placeholder="New track name"> <button id="journal-track-add" class="btn btn-default">Add track</button> <button id="journal-track-save" class="btn btn-primary">Save</button></div><p id="journal-track-status"></p>');
  $('#journal-track-open-only').on('change', function () {
    sync(); openOnly = $(this).prop('checked'); render();
  });
  $(root).on('click', '.track-remove', function () {
    sync();
    var index = Number($(this).closest('tr').attr('data-index'));
    if (index === 0) return;
    tracks.splice(index, 1); render();
  });
  $('#journal-track-add').on('click', function () {
    sync();
    var name = String($('#journal-track-new').val() || '').trim();
    var id = slug(name);
    if (!name || tracks.some(function (track) { return track.id === id; })) {
      $('#journal-track-status').text(name ? 'That generated track ID already exists.' : 'Enter a track name.'); return;
    }
    tracks.push({id: id, name: name, open: true});
    $('#journal-track-new').val(''); render();
  });
  var loadTracks = function (done) {
    Webfield2.api.get('/groups', {id: TRACKS_ID}).then(function (result) {
      var value = result.groups[0].content.tracks.value || [];
      tracks = typeof value === 'string' ? JSON.parse(value) : value;
      render();
      if (done) done(true);
    }, function (error) {
      $('#journal-track-status').text(error.message || error);
      if (done) done(false);
    });
  };
  $('#journal-track-save').on('click', function () {
    sync(); $('#journal-track-status').text('Saving...');
    Webfield2.api.post('/groups/edits?awaitProcess=true', {
      invitation: MANAGE_TRACKS_ID,
      signatures: [EIC_ID], readers: ['everyone'], writers: [VENUE_ID],
      group: {id: TRACKS_ID, content: {tracks: {value: tracks}}}
    }).then(function () {
      loadTracks(function (loaded) {
        if (loaded) $('#journal-track-status').text('Saved.');
      });
    }, function (error) {
      $('#journal-track-status').text(error.message || error);
    });
  });
  loadTracks(function () { Webfield2.ui.done(); });
}());
