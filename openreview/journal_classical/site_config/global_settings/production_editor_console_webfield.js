// JMLR-only worklist for manual publication on jmlr.org. Journal owns the
// OpenReview acceptance/publication lifecycle but has no jmlr.org worklist;
// this page deliberately does not expose or mutate Journal lifecycle state.
(function () {
  var venue = 'JMLR';
  var submissionInvitation = venue + '/-/Submission';
  var statusInvitation = venue + '/-/Publication_Status';
  var eicId = venue + '/Editors_In_Chief';
  var peId = venue + '/Production_Editors';

  var value = function (field, fallback) {
    return field && Object.prototype.hasOwnProperty.call(field, 'value') ? field.value : (field == null ? fallback : field);
  };
  var escapeHtml = function (text) { return $('<div>').text(text == null ? '' : String(text)).html(); };
  var profileId = function () { return user && user.profile && user.profile.id || user && user.id || ''; };
  var inGroup = function (group) { return group && (group.members || []).indexOf(profileId()) >= 0; };
  var accepted = function (note) { return value(note.content && note.content.venueid, '') === venue; };
  var statusFor = function (note) { return value(note && note.content && note.content.status, 'Ready'); };
  var failureMessage = function (error, fallback) {
    if (typeof error === 'string' && error) return error;
    if (error && error.responseJSON && error.responseJSON.message) return error.responseJSON.message;
    if (error && error.responseText) {
      try {
        var parsed = JSON.parse(error.responseText);
        if (parsed && parsed.message) return parsed.message;
      } catch (ignored) {}
    }
    return fallback;
  };
  var getAllStatuses = function (offset, notes) {
    return Webfield2.api.get('/notes', { invitation: statusInvitation, domain: venue, limit: 1000, offset: offset || 0 })
      .then(function (result) {
        var batch = result.notes || [];
        var all = (notes || []).concat(batch);
        return batch.length === 1000 ? getAllStatuses(all.length, all) : { notes: all };
      });
  };

  var setup = function () {
    Webfield2.ui.setup('#group-container', venue, {
      title: 'JMLR Production Editor Worklist',
      instructions: 'Publish accepted papers on jmlr.org, enter the JMLR publication URL, then mark the work complete.',
      tabs: ['Pending'],
      referrer: typeof args !== 'undefined' && args ? args.referrer : undefined,
      fullWidth: true
    });
  };

  var row = function (paper, statusNote) {
    var status = statusFor(statusNote);
    var number = paper.number;
    var prefix = 'pe-' + number;
    var pageUrl = value(statusNote && statusNote.content && statusNote.content.jmlr_publication_url, '');
    var bundleId = venue + '/Paper' + number + '/-/Download_Publication_Files';
    return '<tr data-paper-id="' + escapeHtml(paper.id) + '" data-status-id="' + escapeHtml(statusNote && statusNote.id || '') + '" data-final-pdf="' + escapeHtml(value(statusNote && statusNote.content && statusNote.content.pdf, '')) + '" data-supplementary-material="' + escapeHtml(value(statusNote && statusNote.content && statusNote.content.supplementary_material, '')) + '">' +
      '<td><strong>#' + number + '</strong><br><span class="label label-' + (status === 'Published' ? 'success' : 'info') + '">' + escapeHtml(status) + '</span></td>' +
      '<td><strong>' + escapeHtml(value(paper.content && paper.content.title, 'Untitled')) + '</strong><br>' +
      '<a href="/forum?id=' + encodeURIComponent(paper.id) + '">Public OpenReview paper</a> · ' +
      '<a href="/invitation?id=' + encodeURIComponent(bundleId) + '">Private publication bundle</a></td>' +
      '<td><label class="sr-only" for="' + prefix + '-page">JMLR publication URL</label><input class="form-control js-page-url" id="' + prefix + '-page" type="url" placeholder="https://www.jmlr.org/papers/v27/..." value="' + escapeHtml(pageUrl) + '"></td>' +
      '<td><button class="btn btn-primary btn-xs js-save" data-next="Published">Mark published</button><div class="js-result small" style="margin-top:4px"></div></td></tr>';
  };

  var table = function (rows, emptyText) {
    if (!rows.length) return '<div class="container"><p class="text-muted">' + escapeHtml(emptyText) + '</p></div>';
    return '<div class="container-fluid"><div class="table-responsive"><table class="table table-striped console-table"><thead><tr><th style="width:9%">Paper</th><th style="width:36%">Accepted record and files</th><th style="width:35%">JMLR URL</th><th>Completion</th></tr></thead><tbody>' + rows.join('') + '</tbody></table></div></div>';
  };

  var save = function (button, signature) {
    var tr = button.closest('tr');
    var result = tr.find('.js-result');
    var next = button.attr('data-next');
    var paperId = tr.attr('data-paper-id');
    var publicationUrl = tr.find('.js-page-url').val().trim();
    if (!publicationUrl) {
      result.addClass('text-danger').text('The JMLR publication URL is required before marking publication complete.');
      return;
    }
    if (!/^https:\/\/(www\.)?jmlr\.org\/papers\/v[0-9]+\/[^/?#]+\.html$/.test(publicationUrl)) {
      result.addClass('text-danger').text('The JMLR publication URL must use https://www.jmlr.org/papers/v<volume>/<paper>.html.');
      return;
    }
    var note = {
      forum: paperId, replyto: paperId, signatures: [signature], readers: [eicId, peId], writers: [eicId, peId],
      content: {
        status: { value: next },
        jmlr_publication_url: { value: publicationUrl },
        pdf: { value: tr.attr('data-final-pdf') || '' },
        supplementary_material: { value: tr.attr('data-supplementary-material') || '' }
      }
    };
    if (tr.attr('data-status-id')) note.id = tr.attr('data-status-id');
    button.prop('disabled', true);
    result.removeClass('text-danger text-success').text('Saving…');
    Webfield2.api.post('/notes/edits?awaitProcess=true', { invitation: statusInvitation, signatures: [signature], note: note })
      .then(function () {
        tr.remove();
        var remaining = $('#pending tbody tr').length;
        $('#pe-pending-count').text(remaining);
        if (!remaining) $('#pending').html(table([], 'No publication work is pending.'));
      })
      .fail(function (error) {
        button.prop('disabled', false);
        result.addClass('text-danger').text(failureMessage(error, 'Could not save publication status.'));
      });
  };

  setup();
  if (!user || user.isGuest) {
    Webfield2.ui.errorMessage('You must be logged in to access this page.');
    Webfield2.ui.done();
    return;
  }

  $.when(
    Webfield2.api.getAllSubmissions(submissionInvitation, { domain: venue }),
    getAllStatuses(),
    Webfield2.api.getGroup(peId),
    Webfield2.api.getGroup(eicId)
  ).then(function (submissions, statusResult, peGroup, eicGroup) {
    if (!inGroup(peGroup) && !inGroup(eicGroup)) {
      Webfield2.ui.errorMessage('You must be a Production Editor or Editor-in-Chief to access this worklist.');
      Webfield2.ui.done();
      return;
    }
    var signature = inGroup(peGroup) ? peId : eicId;
    var byForum = (statusResult.notes || []).reduce(function (map, note) { map[note.forum] = note; return map; }, {});
    var papers = (submissions || []).filter(accepted).sort(function (a, b) { return b.number - a.number; });
    var pending = papers.filter(function (paper) {
      return byForum[paper.id] && statusFor(byForum[paper.id]) !== 'Published';
    });
    $('#pending').html('<div class="container"><p><strong id="pe-pending-count">' + pending.length + '</strong> publication item' + (pending.length === 1 ? '' : 's') + ' remaining.</p></div>' + table(pending.map(function (paper) { return row(paper, byForum[paper.id]); }), 'No publication work is pending.'));
    $('.js-save').on('click', function () { save($(this), signature); });
    Webfield2.ui.done();
  }).fail(function () {
    Webfield2.ui.errorMessage('The publication worklist could not be loaded. Please reload the page.');
    Webfield2.ui.done();
  });
})();
