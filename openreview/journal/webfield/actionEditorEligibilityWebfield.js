// VENUE_PLACEHOLDER delta: Journal has no combined base-membership and track-eligibility page.
(function () {
  var root = '#invitation-container', VENUE = 'VENUE_PLACEHOLDER', EIC = 'VENUE_PLACEHOLDER/Editors_In_Chief', BASE = 'VENUE_PLACEHOLDER/Action_Editors';
  var ADD = 'VENUE_PLACEHOLDER/-/Add_Action_Editor', REMOVE = 'VENUE_PLACEHOLDER/-/Manage_Action_Editors';
  var REGULAR = 'VENUE_PLACEHOLDER/Action_Editors/-/Regular_Ineligible';
  var MANAGED = 'VENUE_PLACEHOLDER/Action_Editors/-/Track_Eligible';
  var state = {members: [], regular: {}, managed: {}, profiles: {}, tracks: [], selected: ''};
  var escapeHtml = function (v) { return $('<div>').text(v == null ? '' : String(v)).html(); };
  var api = function (method, path, body) { return method === 'POST' ? Webfield2.api.post(path, body || {}) : Webfield2.api.get(path, body || {}); };
  var activeByTail = function (edges) { var out = {}; (edges || []).forEach(function (edge) { if (!edge.ddate) (out[edge.tail] = out[edge.tail] || []).push(edge); }); return out; };
  var managedByLabel = function (edges) {
    var out = {}; (edges || []).forEach(function (edge) { if (!edge.ddate) { out[edge.label] = out[edge.label] || {}; (out[edge.label][edge.tail] = out[edge.label][edge.tail] || []).push(edge); } }); return out;
  };
  var name = function (id) { var p = state.profiles[id], names = p && p.content && p.content.names || []; return names.length ? names[0].fullname : id; };
  var emails = function (id) { var c = state.profiles[id] && state.profiles[id].content || {}; return [c.preferredEmail].concat(c.emails || []).filter(Boolean).join(' '); };
  var eligible = function (id, track) { return track === 'Regular' ? !state.regular[id] : !!(state.managed[track] || {})[id]; };
  var selectedName = function () { var found = state.tracks.filter(function (t) { return t.id === state.selected; })[0]; return found ? found.name : state.selected; };
  var render = function () {
    var query = String($('#journal-ae-search').val() || '').toLowerCase(), filter = $('#journal-ae-filter').val();
    var extra = state.selected ? '<th>' + escapeHtml(selectedName()) + '</th>' : '';
    $('#journal-ae-head').html('<tr><th>Action Editor</th><th>Regular</th>' + extra + '<th>Action</th></tr>');
    var rows = state.members.filter(function (id) {
      var matches = !query || (id + ' ' + name(id) + ' ' + emails(id)).toLowerCase().indexOf(query) >= 0;
      if (filter === 'regular_eligible') matches = matches && eligible(id, 'Regular');
      if (filter === 'regular_ineligible') matches = matches && !eligible(id, 'Regular');
      if (filter === 'selected_eligible') matches = matches && state.selected && eligible(id, state.selected);
      if (filter === 'selected_ineligible') matches = matches && state.selected && !eligible(id, state.selected);
      return matches;
    }).map(function (id) {
      var extraCell = state.selected ? '<td><input type="checkbox" data-track="' + escapeHtml(state.selected) + '" ' + (eligible(id, state.selected) ? 'checked' : '') + '></td>' : '';
      return '<tr data-id="' + escapeHtml(id) + '"><td><strong>' + escapeHtml(name(id)) + '</strong><br><a href="/profile?id=' + encodeURIComponent(id) + '">' + escapeHtml(id) + '</a></td>' +
        '<td><input type="checkbox" data-track="Regular" ' + (eligible(id, 'Regular') ? 'checked' : '') + '></td>' + extraCell +
        '<td><button class="btn btn-primary btn-sm journal-save">Save</button> <button class="btn btn-danger btn-sm journal-remove">Remove</button></td></tr>';
    }).join('');
    $('#journal-ae-body').html(rows || '<tr><td colspan="4">No matching Action Editors.</td></tr>');
  };
  var editEligibility = function (id, track, checked) {
    var existing = (track === 'Regular' ? state.regular[id] : (state.managed[track] || {})[id]) || [];
    var shouldExist = track === 'Regular' ? !checked : checked;
    if (!!existing.length === shouldExist) return Promise.resolve();
    var body = {invitation: track === 'Regular' ? REGULAR : MANAGED, signatures: [EIC], writers: [EIC],
      readers: shouldExist ? [VENUE, EIC] : [EIC, id], head: BASE, tail: id,
      label: track === 'Regular' ? 'Regular Ineligible' : track};
    if (existing.length) return Promise.all(existing.map(function (edge) {
      return api('POST', '/edges', $.extend({}, body, {id: edge.id, ddate: Date.now()}));
    }));
    return api('POST', '/edges', body);
  };
  var load = function () {
    $('#journal-ae-status').text('Loading...');
    return Promise.all([
      api('GET', '/groups', {id: BASE}), api('GET', '/groups', {id: 'VENUE_PLACEHOLDER/Tracks'}),
      Webfield2.api.getAll('/edges', {invitation: REGULAR, head: BASE}), Webfield2.api.getAll('/edges', {invitation: MANAGED, head: BASE})
    ]).then(function (r) {
      state.members = (r[0].groups[0].members || []).filter(function (id) { return /^~/.test(id); });
      var trackValue = r[1].groups[0].content.tracks.value || [];
      state.tracks = (typeof trackValue === 'string' ? JSON.parse(trackValue) : trackValue)
        .filter(function (track) { return track.id !== 'Regular'; });
      state.regular = activeByTail(r[2]); state.managed = managedByLabel(r[3]);
      return Promise.all(state.members.map(function (id) { return api('GET', '/profiles', {id: id}).then(function (p) { state.profiles[id] = p.profiles[0]; }); }));
    }).then(function () {
      $('#journal-extra-track').html('<option value="">No additional track</option>' + state.tracks.map(function (track) { return '<option value="' + escapeHtml(track.id) + '">' + escapeHtml(track.name) + '</option>'; }).join('')).val(state.selected);
      $('#journal-ae-status').text(''); render();
    });
  };
  var loadUntilEligibility = function (id, expected, attempts) {
    return load().then(function () {
      var settled = Object.keys(expected).every(function (track) {
        return eligible(id, track) === expected[track];
      });
      if (settled) return;
      if (attempts <= 1) return Promise.reject(new Error('Saved eligibility is not visible yet. Retry Save.'));
      return new Promise(function (resolve) { setTimeout(resolve, 500); })
        .then(function () { return loadUntilEligibility(id, expected, attempts - 1); });
    });
  };
  $(root).html('<h2>Manage Action Editors</h2><p>Regular is always shown. Select one managed track to inspect or edit beside it. Availability remains in Journal’s private assignment control.</p>' +
    '<p><a href="/invitation?id=VENUE_PLACEHOLDER%2F-%2FManage_Tracks">Manage Tracks</a></p>' +
    '<div class="form-inline"><input id="journal-ae-search" class="form-control" placeholder="Search name, email, or profile ID"> ' +
    '<select id="journal-extra-track" class="form-control"><option value="">No additional track</option></select> ' +
    '<select id="journal-ae-filter" class="form-control"><option value="">All eligibility</option><option value="regular_eligible">Regular eligible</option><option value="regular_ineligible">Regular ineligible</option><option value="selected_eligible">Selected track eligible</option><option value="selected_ineligible">Selected track ineligible</option></select> ' +
    '<input id="journal-ae-add" class="form-control" placeholder="~Profile_ID"><button id="journal-ae-add-button" class="btn btn-default">Add AE</button></div>' +
    '<p id="journal-ae-status"></p><table class="table"><thead id="journal-ae-head"></thead><tbody id="journal-ae-body"></tbody></table>');
  $(root).on('input change', '#journal-ae-search,#journal-ae-filter', render);
  $('#journal-extra-track').on('change', function () { state.selected = $(this).val(); render(); });
  $(root).on('click', '.journal-save', function () {
    var row = $(this).closest('tr'), id = row.attr('data-id'), tracks = ['Regular'].concat(state.selected ? [state.selected] : []), button = $(this).prop('disabled', true);
    var expected = {}; tracks.forEach(function (track) { expected[track] = row.find('[data-track="' + track + '"]').prop('checked'); });
    Promise.all(tracks.map(function (track) { return editEligibility(id, track, row.find('[data-track="' + track + '"]').prop('checked')); }))
      .then(function () { return loadUntilEligibility(id, expected, 10); })
      .catch(function (e) { $('#journal-ae-status').text(e.message || e); })
      .then(function () { button.prop('disabled', false); });
  });
  $(root).on('click', '.journal-remove', function () {
    var id = $(this).closest('tr').attr('data-id');
    api('POST', '/groups/edits?awaitProcess=true', {invitation: REMOVE, signatures: [EIC], readers: [EIC], writers: [EIC], group: {id: BASE, members: {remove: [id]}}})
      .then(load, function (e) { $('#journal-ae-status').text(e.message || e); });
  });
  $('#journal-ae-add-button').on('click', function () {
    var id = String($('#journal-ae-add').val() || '').trim();
    api('POST', '/groups/edits?awaitProcess=true', {invitation: ADD, signatures: [EIC], readers: [EIC], writers: [EIC], group: {id: BASE, members: {add: [id]}}})
      .then(load, function (e) { $('#journal-ae-status').text(e.message || e); });
  });
  load().then(function () { Webfield2.ui.done(); }, function (e) { $('#journal-ae-status').text(e.message || e); Webfield2.ui.done(); });
}());
