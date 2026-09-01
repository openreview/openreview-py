// JMLR delta: Journal publishes the record but does not produce the manual jmlr.org handoff.
(function () {
  var root = '#invitation-container';
  var value = function (key, fallback) {
    return invitation.content && invitation.content[key] ? invitation.content[key].value : fallback;
  };
  var forum = value('forumId', '');
  var metadata = value('publicationMetadata', {});
  var apiUrl = '{{API_URL}}';
  var statusInvitation = 'JMLR/-/Publication_Status';
  var noteValue = function (note, key, fallback) {
    var field = note && note.content && note.content[key];
    return field && Object.prototype.hasOwnProperty.call(field, 'value') ? field.value : (field == null ? fallback : field);
  };
  var safeDownloadPath = function (path, prefix) {
    return typeof path === 'string' && path.indexOf(prefix) === 0 ? path : '';
  };
  var render = function (statusNote) {
    var pdf = safeDownloadPath(noteValue(statusNote, 'pdf', ''), '/pdf/');
    var supplementary = safeDownloadPath(noteValue(statusNote, 'supplementary_material', ''), '/attachment/');
    if (!pdf) {
      $(root).html('<div class="alert alert-danger">The final PDF is not available on the accepted record.</div>');
      return;
    }
    var pdfUrl = apiUrl + '/pdf?' + $.param({id: statusNote.id});
    var supplementaryUrl = apiUrl + '/attachment?' + $.param({id: statusNote.id, name: 'supplementary_material'});
    var fetchFile = function (url) {
      return fetch(url, {credentials: 'include'}).then(function (response) {
        if (!response.ok) throw new Error('download_failed');
        return response.blob();
      });
    };
    Promise.all([fetchFile(pdfUrl), supplementary ? fetchFile(supplementaryUrl) : Promise.resolve(null)])
      .then(function (files) {
        var pdfObjectUrl = URL.createObjectURL(files[0]);
        var supplementaryObjectUrl = files[1] ? URL.createObjectURL(files[1]) : '';
        var metadataUrl = URL.createObjectURL(new Blob([JSON.stringify(metadata, null, 2) + '\n'], {type: 'application/json'}));
        var paperId = String(metadata.id || forum).replace(/[^A-Za-z0-9._-]/g, '_');
        $(root).html('<h2>JMLR publication files</h2><p>This private PE/EIC surface does not change publication state.</p>' +
          '<p><a class="btn btn-primary" href="' + pdfObjectUrl + '" download="' + paperId + '.pdf">Download final PDF</a></p>' +
          (supplementary ? '<p><a class="btn btn-default" href="' + supplementaryObjectUrl + '" download="' + paperId + '-supplement">Download supplement</a></p>' : '') +
          '<p><a id="jmlr-publication-json" class="btn btn-default" href="' + metadataUrl + '" download="publication.json">Download publication.json</a></p>' +
          '<p><a href="/forum?id=' + encodeURIComponent(forum) + '">Open public OpenReview record</a></p>');
        $(window).one('unload', function () {
          URL.revokeObjectURL(pdfObjectUrl); URL.revokeObjectURL(metadataUrl);
          if (supplementaryObjectUrl) URL.revokeObjectURL(supplementaryObjectUrl);
        });
      }).catch(function () {
        $(root).html('<div class="alert alert-danger">The private publication files could not be downloaded.</div>');
      });
  };
  Webfield2.api.get('/notes', {invitation: statusInvitation, forum: forum}).then(function (result) {
    var notes = result.notes || [];
    if (notes.length !== 1) {
      $(root).html('<div class="alert alert-danger">The private publication files record is unavailable.</div>');
      return;
    }
    render(notes[0]);
  }).fail(function () {
    $(root).html('<div class="alert alert-danger">The private publication files record is unavailable.</div>');
  });
}());
