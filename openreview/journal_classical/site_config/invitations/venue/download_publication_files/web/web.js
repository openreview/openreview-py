(function() {
  var container = '#invitation-container';

  var htmlEscape = function(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  var contentValue = function(content, key, fallback) {
    var item = content && content[key];
    if (item && Object.prototype.hasOwnProperty.call(item, 'value')) return item.value;
    return fallback;
  };

  var jsonString = function(value) {
    return JSON.stringify(value, null, 2) + '\n';
  };

  var normalizeVolume = function(value, year) {
    if (typeof value === 'number') return value;
    var text = String(value || '').trim();
    if (/^v?\d+$/.test(text)) return Number(text.replace(/^v/, ''));
    return (year % 100) + 1;
  };

  var publicationIdFromPaperNumber = function(year, number) {
    return String(year % 100).padStart(2, '0') + '-' + String(number % 100000).padStart(5, '0');
  };

  var inferAttachmentExtension = function(filename, contentType) {
    var name = String(filename || '');
    var match = name.match(/(\.[A-Za-z0-9][A-Za-z0-9._-]*)$/);
    if (match) return match[1].toLowerCase();
    if (/zip/i.test(contentType || '')) return '.zip';
    if (/pdf/i.test(contentType || '')) return '.pdf';
    if (/gzip/i.test(contentType || '')) return '.gz';
    return '.bin';
  };

  var publicUrls = function(paperId, volume) {
    return {
      abstract: 'https://www.jmlr.org/papers/v' + volume + '/' + paperId + '.html',
      pdf: 'https://www.jmlr.org/papers/volume' + volume + '/' + paperId + '/' + paperId + '.pdf'
    };
  };

  var downloadBlob = function(blob, filename) {
    var url = URL.createObjectURL(blob);
    var pageDocument = globalThis.document;
    var link = pageDocument.createElement('a');
    link.href = url;
    link.download = filename;
    pageDocument.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(function() { URL.revokeObjectURL(url); }, 1000);
  };

  var unresolvedTemplate = function(value) {
    return typeof value === 'string' && value.indexOf('${') >= 0;
  };

  var invitationId = invitation && invitation.id || '';
  var paperNumberFromInvitationId = function() {
    var match = String(invitationId).match(/\/Paper(\d+)\/-/);
    return match ? Number(match[1]) : null;
  };

  var contentNoteNumber = contentValue(invitation.content, 'noteNumber');
  var contentNoteId = contentValue(invitation.content, 'noteId');
  var noteNumber = unresolvedTemplate(contentNoteNumber) ? paperNumberFromInvitationId() : Number(contentNoteNumber || paperNumberFromInvitationId());
  var noteId = unresolvedTemplate(contentNoteId) ? null : contentNoteId;

  var loadPublicationNote = function() {
    if (noteId) {
      return Webfield2.api.get('/notes', { id: noteId }).then(function(result) {
        var note = result.notes && result.notes[0];
        if (!note) throw new Error('Could not load paper note ' + noteId);
        return note;
      });
    }
    if (!noteNumber) {
      throw new Error('Could not infer paper number from invitation ' + invitationId);
    }
    return Webfield2.api.get('/notes', { invitation: 'JMLR/-/Submission', number: noteNumber }).then(function(result) {
      var note = result.notes && result.notes[0];
      if (!note) throw new Error('Could not load JMLR Paper' + noteNumber + ' submission.');
      noteId = note.id;
      return note;
    });
  };

  $(container).html([
      '<div class="jmlr-publication-download">',
      '<h3>Download publication files</h3>',
      '<p class="text-muted">Download final publication files for one camera-ready approved paper. This does not mark the paper as published.</p>',
      '<div id="jmlr-download-publication-links"></div>',
      '<a id="jmlr-download-publication-back" class="btn btn-default" href="' + (noteId ? '/forum?id=' + encodeURIComponent(noteId) : '#') + '">Back to paper</a>',
      '<p id="jmlr-download-publication-status" style="margin-top: 10px;"></p>',
    '</div>'
  ].join(''));

  var renderDownloadLinks = function() {
    var status = $('#jmlr-download-publication-status');
    status.removeClass('text-danger text-success').addClass('text-muted').text('Preparing download links...');
    loadPublicationNote().then(function(note) {
      $('#jmlr-download-publication-back').attr('href', '/forum?id=' + encodeURIComponent(note.id));
      var venueid = contentValue(note.content, 'venueid');
      if (venueid !== 'JMLR/Camera_Ready_Approved') {
        throw new Error('Only JMLR/Camera_Ready_Approved papers can be downloaded.');
      }
      var invitationMetadata = contentValue(invitation.content, 'publicationMetadata');
      if (unresolvedTemplate(invitationMetadata)) invitationMetadata = null;
      var metadata = invitationMetadata || contentValue(note.content, 'publication_metadata', {}) || {};
      var year = Number(metadata.year || new Date(note.pdate || note.cdate).getUTCFullYear());
      var volume = normalizeVolume(metadata.volume, year);
      var paperId = (/^\d{2}-\d{5}$/.test(String(metadata.id || ''))) ? String(metadata.id) : publicationIdFromPaperNumber(year, note.number || noteNumber);
      var top = paperId + '/';
      var pdfName = paperId + '.pdf';
      var info = $.extend(true, {}, metadata, {
        id: paperId,
        issue: metadata.issue || note.number || noteNumber,
        volume: volume,
        title: metadata.title || contentValue(note.content, 'title', ''),
        abstract: metadata.abstract || contentValue(note.content, 'abstract', ''),
        authors: metadata.authors || contentValue(note.content, 'authors', []),
        emails: metadata.emails || [],
        pages: metadata.pages || [1, null],
        year: year
      });
      var pdfUrl = '/pdf?id=' + encodeURIComponent(note.id);
      var supplementaryValue = contentValue(note.content, 'supplementary_material');
      var supplementaryUrl = null;
      var supplementaryName = null;
      var files = [{ kind: 'pdf', filename: pdfName, source: pdfUrl }];
      var omitted = [];
      if (supplementaryValue) {
        supplementaryName = paperId + '-supplementary' + inferAttachmentExtension(supplementaryValue, '');
        supplementaryUrl = '/attachment?id=' + encodeURIComponent(note.id) + '&name=supplementary_material';
        files.push({ kind: 'supplementary', filename: supplementaryName, source: supplementaryUrl });
      } else {
        omitted.push({ kind: 'supplementary', reason: 'No supplementary material is present on this paper.' });
      }
      var metadata = {
        info: info,
        manifest: {
          paper_number: note.number || noteNumber,
          forum_id: note.id,
          publication_id: paperId,
          volume: volume,
          year: year,
          public_urls: publicUrls(paperId, volume),
          files: files.concat([{ kind: 'metadata', filename: 'publication.json' }]),
          omitted: omitted
        }
      };
      var metadataText = jsonString(metadata);
      $('#jmlr-download-publication-links').html([
        '<p><a class="btn btn-primary" href="' + pdfUrl + '" target="_blank" rel="noopener noreferrer" download="' + htmlEscape(pdfName) + '">Download final PDF</a></p>',
        supplementaryUrl ? '<p><a class="btn btn-default" href="' + supplementaryUrl + '" target="_blank" rel="noopener noreferrer" download="' + htmlEscape(supplementaryName) + '">Download supplementary material</a></p>' : '',
        '<p><button id="jmlr-download-publication-json" type="button" class="btn btn-default">Download publication.json</button></p>'
      ].join(''));
      $('#jmlr-download-publication-json').on('click', function() {
        downloadBlob(new Blob([metadataText], { type: 'application/json' }), 'publication.json');
      });
      status.removeClass('text-muted text-danger').addClass('text-success').text('Publication download links are ready for ' + paperId + '.');
    }).then(null, function(error) {
      status.removeClass('text-muted text-success').addClass('text-danger').text(error.message || String(error));
    });
  };

  renderDownloadLinks();
}());
