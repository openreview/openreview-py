var venueSubmissionSignedInProfile = null;

var getSignedInSubmissionAuthorListLine = function(profile) {
  profile = profile || (user && user.profile);
  if (!profile || !profile.id || !user || _.startsWith(user.id, 'guest_')) {
    return null;
  }

  return profile.id;
};

var ensureVenueSubmissionApi2ApiUrl = function() {
  var api2Url = typeof OR_API_V2_URL !== 'undefined' && OR_API_V2_URL ? OR_API_V2_URL : null;
  if (!api2Url) {
    return;
  }

  OR_API_URL = api2Url;
  if (typeof globalThis !== 'undefined' && globalThis) {
    globalThis.OR_API_URL = api2Url;
    if (globalThis.window) {
      globalThis.window.OR_API_URL = api2Url;
    }
  }
  if (typeof window !== 'undefined' && window) {
    window.OR_API_URL = api2Url;
  }
};

var ensureVenueSubmissionFileChunkUpload = function() {
  ensureVenueSubmissionApi2ApiUrl();

  if (typeof Webfield2 === 'undefined') {
    return;
  }

  if (Webfield2.jmlrApi2FileChunkUploadPatched &&
      typeof Webfield2.sendFileChunk === 'function' &&
      Webfield2.sendFileChunk.jmlrApi2FileChunkUploadPatched &&
      typeof Webfield2.jmlrVenueSubmissionSendFileChunk === 'function') {
    return;
  }

  Webfield2.sendFileChunk = function(formData, progressElement) {
    var apiUrl = typeof OR_API_URL !== 'undefined' && OR_API_URL ? OR_API_URL : '';
    if (!apiUrl && typeof location !== 'undefined' && location.origin) {
      apiUrl = location.origin.replace('://', '://api2.');
    }
    if (!apiUrl) {
      return $.Deferred().reject(new Error('Unable to determine the OpenReview API URL for file upload.')).promise();
    }
    var progress = progressElement && progressElement.find ? progressElement : (progressElement ? $(progressElement) : $());
    return $.ajax({
      url: apiUrl + '/attachment/chunk',
      type: 'put',
      contentType: false,
      processData: false,
      data: formData,
      xhrFields: {
        withCredentials: true
      },
      success: function(response) {
        if (response && !response.url && progress.length) {
          var values = Object.values(response);
          if (values.length) {
            var percent = ((100 * values.filter(function(value) { return value === 'completed'; }).length) / values.length).toFixed(0) + '%';
            progress.find('.progress-bar').css('width', percent).text(percent);
          }
        }
      }
    });
  };
  Webfield2.sendFileChunk.jmlrApi2FileChunkUploadPatched = true;
  Webfield2.jmlrVenueSubmissionSendFileChunk = Webfield2.sendFileChunk;
  Webfield2.jmlrApi2FileChunkUploadPatched = true;
};

var ensureVenueSubmissionEditSignaturePost = function() {
  if (typeof Webfield2 === 'undefined' || !Webfield2.post || Webfield2.jmlrVenueSubmissionSignaturePostPatched) {
    return;
  }

  var originalPost = Webfield2.post;
  Webfield2.post = function(url, payload, options) {
    var profileId = user && user.profile && user.profile.id;
    if (url === '/notes/edits' &&
        payload &&
        payload.invitation === SUBMISSION_ID) {
      url = '/notes/edits?awaitProcess=true';
      if ((!payload.signatures || !payload.signatures.length) &&
          profileId &&
          _.startsWith(profileId, '~')) {
        payload.signatures = [profileId];
      }
    }
    return originalPost.call(this, url, payload, options);
  };
  Webfield2.jmlrVenueSubmissionSignaturePostPatched = true;
};

var ensureVenueSubmissionEditorAlignment = function(editor) {
  if (!$('#jmlr-submission-editor-alignment').length) {
    $('head').append(
      '<style id="jmlr-submission-editor-alignment">' +
      '#new-submission .note_editor, #new-submission .note_editor * { text-align: left !important; }' +
      '</style>'
    );
  }
  if (editor && editor.length) {
    editor.css('text-align', 'left');
  }
};

var markVenueSubmissionEditor = function(editor) {
  if (!editor || !editor.length) {
    return;
  }
  editor.attr({
    'data-invitation-id': SUBMISSION_ID,
    'data-jmlr-editor': 'submission'
  });
  editor.closest('#new-submission').attr('data-invitation-id', SUBMISSION_ID);
};

var relabelVenueSubmissionMainPaperPdf = function(editor) {
  if (!editor || !editor.length) {
    return;
  }
  var pdfInput = editor.find('input[name="pdf"], input.note_pdf').first();
  var heading = pdfInput.closest('.row').find('.small_heading').first();
  if (!heading.length) {
    return;
  }
  var requiredMarker = heading.find('.required_field').first().prop('outerHTML') || '';
  heading.html(requiredMarker + 'Main Paper PDF');
};

var getVenueSubmissionRouteArg = function(name) {
  if (args && args[name] !== undefined) {
    return args[name];
  }
  var pageLocation =
    (typeof globalThis !== 'undefined' && globalThis.location) ||
    (typeof location !== 'undefined' && location);
  if (!pageLocation || !pageLocation.search) {
    return null;
  }
  try {
    return new URLSearchParams(pageLocation.search).get(name);
  } catch (error) {
    return null;
  }
};

var getVenueSubmissionPreviousNumber = function() {
  return getVenueSubmissionRouteArg('previous_JMLR_submission_number') ||
    getVenueSubmissionRouteArg('previous_jmlr_submission_number') ||
    getVenueSubmissionRouteArg('resubmissionOf');
};

var getVenueSubmissionPreviousUrl = function() {
  return getVenueSubmissionRouteArg('previous_JMLR_submission_URL') ||
    getVenueSubmissionRouteArg('previous_jmlr_submission_url');
};

var isVenueResubmissionRoute = function() {
  var previousNumber = String(getVenueSubmissionPreviousNumber() || '').trim();
  return Boolean(previousNumber && previousNumber.toUpperCase() !== 'N/A');
};

var hideVenueSubmissionField = function(editor, fieldName) {
  var field = editor.find('[name="' + fieldName + '"]').first();
  if (!field.length) {
    return;
  }
  var row = field.closest('.row');
  if (row.length) {
    row.hide();
  } else {
    field.closest('.form-group').hide();
  }
};

var venueResubmissionPaperLabel = function() {
  var previousNumber = String(getVenueSubmissionPreviousNumber() || '').trim();
  return previousNumber ? 'JMLR Paper ' + previousNumber : 'the prior JMLR paper';
};

var renderVenueResubmissionEditorContext = function(editor) {
  if (!editor || !editor.length || !isVenueResubmissionRoute()) {
    return;
  }
  var paperLabel = venueResubmissionPaperLabel();
  if (!editor.find('.jmlr-resubmission-editor-context').length) {
    editor.prepend(
      '<div class="jmlr-resubmission-editor-context alert alert-info" style="margin-bottom: 16px;">' +
      '<strong>Resubmission for ' + _.escape(paperLabel) + '.</strong> ' +
      'This form creates a linked JMLR resubmission. Author List and Open Source Software are copied from the prior paper and locked.' +
      '</div>'
    );
  }
};

var relabelVenueResubmissionSubmit = function(editor) {
  if (!editor || !editor.length || !isVenueResubmissionRoute()) {
    return;
  }
  var submitControl = editor.find('button[type="submit"], input[type="submit"]').last();
  if (!submitControl.length) {
    submitControl = editor.find('button.btn-primary, input.btn-primary').last();
  }
  if (!submitControl.length) {
    return;
  }
  if (submitControl.is('input')) {
    submitControl.val('Submit Resubmission');
  } else {
    submitControl.text('Submit Resubmission');
  }
};

var venueSubmissionControlledFileLabel = function(fieldName) {
  if (fieldName === 'pdf') {
    return 'Main Paper PDF';
  }
  if (fieldName === 'supplementary_material') {
    return 'Supplementary Material';
  }
  if (fieldName === 'response_to_reviewers') {
    return 'Response to Reviewers';
  }
  return fieldName;
};

var venueSubmissionControlledFileDescription = function(fieldName) {
  if (fieldName === 'pdf') {
    return 'Required. Use the file chooser below to upload the main paper PDF. The file must end with .pdf.';
  }
  if (fieldName === 'supplementary_material') {
    return 'Optional. All supplementary material must be self-contained and zipped into a single file. The maximum file size is 10MB.';
  }
  if (fieldName === 'response_to_reviewers') {
    return 'Required for resubmissions. Upload a PDF response to the previous reviewers.';
  }
  return '';
};

var venueSubmissionControlledFileExtensions = function(fieldName) {
  return fieldName === 'supplementary_material' ? '.zip,.pdf' : '.pdf';
};

var venueSubmissionControlledFileKey = function(fieldName) {
  return 'jmlr-upload-' + fieldName;
};

var venueSubmissionControlledClientUploadId = function(fieldName) {
  var fieldPart = String(fieldName || 'file').replace(/[^a-z0-9]/gi, '').toLowerCase().slice(0, 3) || 'fil';
  var timePart = Date.now().toString(36);
  var randomPart = Math.random().toString(36).slice(2, 8);
  return ('j' + fieldPart + timePart + randomPart).slice(0, 25);
};

var venueSubmissionControlledFileValue = function(editor, fieldName) {
  return editor.data(venueSubmissionControlledFileKey(fieldName) + '-url') || '';
};

var venueSubmissionFileSelected = function(editor, fieldName) {
  var selector = 'input[name="' + fieldName + '"][type="file"], input.note_' + fieldName + '[type="file"], input.jmlr-controlled-file[data-field-name="' + fieldName + '"]';
  var fileInput = editor.find(selector).first();
  var files = fileInput.length ? fileInput.prop('files') : null;
  return Boolean(files && files.length);
};

var venueSubmissionControlledUploadResponseUrl = function(response) {
  if (!response) {
    return '';
  }
  if (typeof response === 'string') {
    return response;
  }
  if (response.url) {
    return response.url;
  }
  var values = Object.values(response);
  var url = values.find(function(value) {
    return typeof value === 'string' && (
      value.indexOf('/attachment') === 0 ||
      value.indexOf('/pdf') === 0 ||
      /^https?:\/\//.test(value)
    );
  });
  return url || '';
};

var venueSubmissionControlledUploadErrorMessage = function(error) {
  if (!error) {
    return '';
  }
  var message = error.responseJSON && error.responseJSON.message ||
    error.responseText ||
    error.statusText ||
    error.message ||
    String(error);
  return message ? String(message).slice(0, 240) : '';
};

var uploadVenueSubmissionAttachment = function(formData) {
  ensureVenueSubmissionApi2ApiUrl();
  var apiUrl = typeof OR_API_URL !== 'undefined' && OR_API_URL ? OR_API_URL : '';
  if (!apiUrl && typeof location !== 'undefined' && location.origin) {
    apiUrl = location.origin.replace('://', '://api2.');
  }
  if (!apiUrl) {
    return $.Deferred().reject(new Error('Unable to determine the OpenReview API URL for file upload.')).promise();
  }
  return $.ajax({
    url: apiUrl + '/attachment',
    type: 'put',
    contentType: false,
    processData: false,
    data: formData,
    xhrFields: {
      withCredentials: true
    }
  });
};

var setVenueSubmissionControlledUploadFailed = function(editor, fieldName, status, message) {
  editor.removeData(venueSubmissionControlledFileKey(fieldName) + '-uploading');
  editor.data(venueSubmissionControlledFileKey(fieldName) + '-error', message || '');
  status.text('Upload failed' + (message ? ': ' + message : '') + '. Choose the file again before submitting.');
};

var uploadVenueSubmissionControlledFile = function(editor, fieldName, fileInput) {
  var files = fileInput && fileInput.length ? fileInput.prop('files') : null;
  var status = editor.find('.jmlr-controlled-file-status[data-field-name="' + fieldName + '"]').first();
  if (!files || !files.length) {
    editor.removeData(venueSubmissionControlledFileKey(fieldName) + '-url');
    editor.removeData(venueSubmissionControlledFileKey(fieldName) + '-uploading');
    status.text('');
    return;
  }

  ensureVenueSubmissionFileChunkUpload();
  var formData = new FormData();
  formData.append('invitationId', SUBMISSION_ID);
  formData.append('name', fieldName);
  formData.append('file', files[0]);
  editor.data(venueSubmissionControlledFileKey(fieldName) + '-uploading', true);
  editor.removeData(venueSubmissionControlledFileKey(fieldName) + '-url');
  status.html(
    '<span>Uploading...</span>' +
    '<div class="progress" style="margin: 4px 0 0; max-width: 260px;">' +
      '<div class="progress-bar" role="progressbar" style="width: 0%;">0%</div>' +
    '</div>'
  );
  return uploadVenueSubmissionAttachment(formData).then(function(response) {
    var url = venueSubmissionControlledUploadResponseUrl(response);
    editor.data(venueSubmissionControlledFileKey(fieldName) + '-url', url);
    editor.removeData(venueSubmissionControlledFileKey(fieldName) + '-uploading');
    status.text(url ? 'Uploaded.' : 'Upload did not return a file URL.');
    return url;
  }, function(error) {
    var message = venueSubmissionControlledUploadErrorMessage(error);
    setVenueSubmissionControlledUploadFailed(editor, fieldName, status, message);
    return $.Deferred().reject(error).promise();
  });
};

if (typeof globalThis !== 'undefined' && globalThis) {
  globalThis.uploadVenueSubmissionControlledFile = uploadVenueSubmissionControlledFile;
}

var renderVenueSubmissionControlledFile = function(editor, fieldName, required) {
  if (!editor || !editor.length || editor.find('.jmlr-controlled-file-row[data-field-name="' + fieldName + '"]').length) {
    return;
  }
  var row = $(
    '<div class="row jmlr-controlled-file-row" data-field-name="' + fieldName + '">' +
      '<div class="small_heading">' + (required ? '<span class="required_field">*</span>' : '') + _.escape(venueSubmissionControlledFileLabel(fieldName)) + '</div>' +
      '<div class="hint">' + _.escape(venueSubmissionControlledFileDescription(fieldName)) + '</div>' +
      '<input type="file" class="form-control jmlr-controlled-file" data-field-name="' + fieldName + '" accept="' + venueSubmissionControlledFileExtensions(fieldName) + '">' +
      '<div class="hint jmlr-controlled-file-status" data-field-name="' + fieldName + '" style="margin-top: 4px;"></div>' +
    '</div>'
  );
  var anchor = editor.find('textarea[name="cover_letter"]').closest('.row');
  if (fieldName === 'supplementary_material') {
    anchor = editor.find('.jmlr-controlled-file-row[data-field-name="pdf"]').first();
  } else if (fieldName === 'response_to_reviewers') {
    anchor = editor.find('.jmlr-controlled-file-row[data-field-name="supplementary_material"]').first();
  }
  if (anchor && anchor.length) {
    anchor.after(row);
  } else {
    editor.append(row);
  }
  row.find('input[type="file"]').on('change', function() {
    uploadVenueSubmissionControlledFile(editor, fieldName, $(this));
  });
};

var renderVenueSubmissionControlledFiles = function(editor) {
  renderVenueSubmissionControlledFile(editor, 'pdf', true);
  renderVenueSubmissionControlledFile(editor, 'supplementary_material', false);
  if (isVenueResubmissionRoute()) {
    renderVenueSubmissionControlledFile(editor, 'response_to_reviewers', true);
  }
};

var renderVenueSubmissionControlledOss = function(editor) {
  if (!OSS_ACTION_EDITORS_ENABLED || !editor || !editor.length || editor.find('.jmlr-controlled-oss-row').length) {
    return;
  }
  var row = $(
    '<div class="row jmlr-controlled-oss-row">' +
      '<div class="small_heading">Open Source Software</div>' +
      '<div class="hint">Open Source Software (OSS) track submission. Check this box if this submission is for the JMLR Open Source Software (OSS) track.</div>' +
      '<label class="checkbox-inline"><input type="checkbox" name="open_source_software" class="jmlr-controlled-oss" value="Yes"> Yes</label>' +
    '</div>'
  );
  var anchor = editor.find('.jmlr-controlled-file-row[data-field-name="supplementary_material"]').first();
  if (anchor.length) {
    anchor.after(row);
  } else {
    editor.append(row);
  }
};

var venueSubmissionContentValue = function(editor, fieldName) {
  return String(editor.find('input[name="' + fieldName + '"], textarea[name="' + fieldName + '"]').first().val() || '').trim();
};

var asNoteContent = function(values) {
  var content = {};
  Object.keys(values).forEach(function(fieldName) {
    var value = values[fieldName];
    if (value !== undefined && value !== null && value !== '') {
      content[fieldName] = { value: value };
    }
  });
  return content;
};

var buildVenueSubmissionPayload = function(editor) {
  var profileId = user && user.profile && user.profile.id;
  var paperAuthorsSignature = VENUE_ID + '/Paper${2/number}/Authors';
  var authorList = editor.data('jmlr-resubmission-author-list') || venueSubmissionContentValue(editor, 'author_list');
  var parsedAuthorList = parseVenueSubmissionAuthorList(authorList);
  if (parsedAuthorList.error) {
    return { errors: [parsedAuthorList.error] };
  }
  var submittingAuthorError = validateVenueSubmissionSubmittingAuthor(parsedAuthorList.authorids);
  if (submittingAuthorError) {
    return { errors: [submittingAuthorError] };
  }
  if (editor.data(venueSubmissionControlledFileKey('pdf') + '-uploading')) {
    return { errors: ['Main Paper PDF is still uploading. Wait for the upload to finish before submitting.'] };
  }
  var pdfUrl = venueSubmissionControlledFileValue(editor, 'pdf');
  if (!pdfUrl) {
    return { errors: ['Main Paper PDF is required. Use the file chooser below Main Paper PDF to upload the main paper PDF before submitting.'] };
  }
  var previousNumber = String(getVenueSubmissionPreviousNumber() || '').trim() || 'N/A';
  if (previousNumber && previousNumber.toUpperCase() !== 'N/A' && !/^\d+$/.test(previousNumber)) {
    return { errors: ['Previous JMLR Submission Number must be a number, or N/A for a new submission.'] };
  }
  var values = {
    title: venueSubmissionContentValue(editor, 'title'),
    abstract: venueSubmissionContentValue(editor, 'abstract'),
    author_list: parsedAuthorList.authorList,
    authors: parsedAuthorList.authors,
    authorids: parsedAuthorList.authorids,
    pdf: pdfUrl,
    previous_JMLR_submission_number: previousNumber,
    venue: 'Submitted to JMLR',
    venueid: VENUE_ID + '/Submitted'
  };
  var conflicts = venueSubmissionContentValue(editor, 'conflict_of_interests');
  if (conflicts) values.conflict_of_interests = conflicts;
  var coverLetter = venueSubmissionContentValue(editor, 'cover_letter');
  if (coverLetter) values.cover_letter = coverLetter;
  var supplementaryUrl = venueSubmissionControlledFileValue(editor, 'supplementary_material');
  if (supplementaryUrl) values.supplementary_material = supplementaryUrl;
  if (OSS_ACTION_EDITORS_ENABLED && (editor.find('input.jmlr-controlled-oss[name="open_source_software"]').first().prop('checked') || editor.data('jmlr-resubmission-oss') === 'true')) {
    values.open_source_software = true;
  }
  if (previousNumber.toUpperCase() !== 'N/A') {
    var previousUrl = String(getVenueSubmissionPreviousUrl() || '').trim();
    if (previousUrl) values.previous_JMLR_submission_URL = previousUrl;
    var previousList = editor.data('jmlr-resubmission-previous-list');
    if (previousList) values.previous_JMLR_submissions = previousList;
    if (editor.data(venueSubmissionControlledFileKey('response_to_reviewers') + '-uploading')) {
      return { errors: ['Response to Reviewers PDF is still uploading. Wait for the upload to finish before submitting.'] };
    }
    var responseUrl = venueSubmissionControlledFileValue(editor, 'response_to_reviewers');
    if (!responseUrl) {
      return { errors: ['Response to Reviewers PDF is required for resubmissions. Use the file chooser below Response to Reviewers to upload a PDF before submitting.'] };
    }
    values.response_to_reviewers = responseUrl;
  }
  return {
    payload: {
      invitation: SUBMISSION_ID,
      signatures: [profileId],
      note: {
        signatures: [paperAuthorsSignature],
        content: asNoteContent(values)
      }
    }
  };
};

var installVenueSubmissionControlledSubmit = function(editor) {
  if (!editor || !editor.length || editor.data('jmlr-controlled-submit-installed')) {
    return;
  }
  editor.data('jmlr-controlled-submit-installed', true);
  editor.find('button, input[type="submit"]').filter(function() {
    return $(this).text().trim() === 'Submit' || $(this).val() === 'Submit';
  }).hide();
  editor.find('button, input[type="button"]').filter(function() {
    return $(this).text().trim() === 'Cancel' || $(this).val() === 'Cancel';
  }).hide();
  var submitButton = $('<button type="button" class="btn btn-sm btn-primary jmlr-controlled-submit">Submit</button>');
  var status = $('<div class="jmlr-controlled-submit-status hint" style="margin-top: 8px;"></div>');
  editor.append(submitButton).append(status);
  submitButton.on('click', function() {
    if (submitButton.prop('disabled')) return;
    var built = buildVenueSubmissionPayload(editor);
    if (built.errors && built.errors.length) {
      status.text(built.errors.join(' '));
      return;
    }
    submitButton.prop('disabled', true);
    status.text('Submitting...');
    Webfield2.api.post('/notes/edits?awaitProcess=true', built.payload).then(function() {
      var venueUrl = '/group?id=' + VENUE_ID + '&submissionPending=1';
      if (typeof globalThis !== 'undefined' && globalThis.location) {
        globalThis.location.href = venueUrl;
      } else if (typeof location !== 'undefined') {
        location.href = venueUrl;
      }
    }, function(error) {
      submitButton.prop('disabled', false);
      var message = error && (error.message || error.responseText) ? (error.message || error.responseText) : 'Submission failed.';
      status.text(message);
    });
  });
};

var parseVenueSubmissionForumId = function(url) {
  if (!url) {
    return null;
  }
  try {
    var parser = document.createElement('a');
    parser.href = String(url);
    var query = parser.search || '';
    var match = query.match(/[?&]id=([^&]+)/);
    return match ? decodeURIComponent(match[1]) : null;
  } catch (error) {
    if (String(url).indexOf('forum?id=') >= 0) {
      var parts = String(url).split('forum?id=');
      return parts[1] ? parts[1].split('&')[0] : null;
    }
  }
  return null;
};

var noteContentValue = function(note, fieldName) {
  var field = note && note.content && note.content[fieldName];
  return field && field.value !== undefined ? field.value : field;
};

var setVenueSubmissionFieldValue = function(editor, fieldName, value) {
  var field = editor.find('input[name="' + fieldName + '"], textarea[name="' + fieldName + '"]').first();
  if (!field.length) {
    return;
  }
  field.val(value).trigger('input').trigger('change');
};

var setVenueSubmissionOssValue = function(editor, isOss) {
  if (!OSS_ACTION_EDITORS_ENABLED) {
    return;
  }
  var ossInputs = editor.find('input[name="open_source_software"]');
  if (!ossInputs.length) {
    return;
  }
  ossInputs.each(function() {
    var input = $(this);
    if (input.attr('type') === 'checkbox') {
      input.prop('checked', Boolean(isOss)).trigger('change');
    } else {
      input.val(isOss ? 'Yes' : '').trigger('input').trigger('change');
    }
    input.prop('disabled', true);
  });
  if (!editor.find('.jmlr-resubmission-oss-locked').length) {
    var paperLabel = venueResubmissionPaperLabel();
    ossInputs.first().closest('.row, .form-group').append(
      '<p class="jmlr-resubmission-oss-locked text-muted" style="margin: 4px 0 0;">Open Source Software was copied from ' + _.escape(paperLabel) + ' and is locked for this resubmission.</p>'
    );
  }
};

var venueSubmissionPreviousListMarkdown = function(previousNote) {
  if (!previousNote || !previousNote.id) {
    return '';
  }
  var rows = [];
  var siteUrl = '{{SITE_URL}}';
  var previousNumber = previousNote.number || noteContentValue(previousNote, 'submission_number') || getVenueSubmissionPreviousNumber();
  rows.push('- [Paper ' + previousNumber + '](' + siteUrl + '/forum?id=' + previousNote.id + ')');
  var previousList = String(noteContentValue(previousNote, 'previous_JMLR_submissions') || '').trim();
  if (previousList) {
    previousList.split(/\r?\n/).forEach(function(line) {
      var cleanLine = String(line || '').trim();
      if (cleanLine && rows.indexOf(cleanLine) < 0) {
        rows.push(cleanLine);
      }
    });
  }
  return rows.join('\n');
};

var lockVenueResubmissionAuthors = function(editor, authorList) {
  setVenueSubmissionFieldValue(editor, 'author_list', authorList);
  var authorInput = editor.find('textarea[name="author_list"], input[name="author_list"]').first();
  authorInput.prop('readonly', true).addClass('disabled');
  if (!editor.find('.jmlr-resubmission-author-locked').length) {
    var paperLabel = venueResubmissionPaperLabel();
    authorInput.after(
      '<p class="jmlr-resubmission-author-locked text-muted" style="margin: 4px 0 8px;">Author List was copied from ' + _.escape(paperLabel) + ' and is locked for this resubmission.</p>'
    );
  }
};

var applyVenueResubmissionPreviousNote = function(editor, previousNote) {
  if (!previousNote || !previousNote.content) {
    return;
  }
  var previousAuthorIds = noteContentValue(previousNote, 'authorids') || [];
  var previousAuthorList = Array.isArray(previousAuthorIds) && previousAuthorIds.length
    ? previousAuthorIds.join(', ')
    : String(noteContentValue(previousNote, 'author_list') || '').trim();
  var previousOss = noteContentValue(previousNote, 'open_source_software');
  var isOss = previousOss === true || previousOss === 'true' || previousOss === 'Yes';
  if (previousAuthorList) {
    editor.data('jmlr-resubmission-author-list', previousAuthorList);
    lockVenueResubmissionAuthors(editor, previousAuthorList);
  }
  var previousSubmissionsList = venueSubmissionPreviousListMarkdown(previousNote);
  if (previousSubmissionsList) {
    editor.data('jmlr-resubmission-previous-list', previousSubmissionsList);
    setVenueSubmissionFieldValue(editor, 'previous_JMLR_submissions', previousSubmissionsList);
  }
  editor.data('jmlr-resubmission-oss', isOss ? 'true' : 'false');
  setVenueSubmissionOssValue(editor, isOss);
};

var loadVenueResubmissionPreviousNote = function(editor) {
  if (!isVenueResubmissionRoute() || !Webfield2 || !Webfield2.api) {
    return;
  }
  var previousUrl = getVenueSubmissionPreviousUrl();
  var previousForumId = parseVenueSubmissionForumId(previousUrl);
  var request = previousForumId
    ? Webfield2.api.get('/notes', { id: previousForumId })
    : Webfield2.api.get('/notes', { invitation: SUBMISSION_ID, number: Number(getVenueSubmissionPreviousNumber()) });
  request
    .then(function(result) {
      var previousNote = result && result.notes && result.notes[0];
      applyVenueResubmissionPreviousNote(editor, previousNote);
    })
    .fail(function() {
      Webfield2.ui.errorMessage('Could not load the previous submission to prefill resubmission authors.');
    });
};

var prefillVenueSubmissionModeFields = function(editor) {
  if (!editor || !editor.length) {
    return;
  }
  var previousNumber = String(getVenueSubmissionPreviousNumber() || '').trim();
  setVenueSubmissionFieldValue(editor, 'previous_JMLR_submission_number', previousNumber || 'N/A');
  hideVenueSubmissionField(editor, 'previous_JMLR_submission_number');
  if (!isVenueResubmissionRoute()) {
    hideVenueSubmissionField(editor, 'response_to_reviewers');
  }
  var previousUrl = getVenueSubmissionPreviousUrl();
  if (previousUrl) {
    setVenueSubmissionFieldValue(editor, 'previous_JMLR_submission_URL', String(previousUrl).trim());
  }
  if (isVenueResubmissionRoute()) {
    renderVenueResubmissionEditorContext(editor);
    relabelVenueResubmissionSubmit(editor);
    loadVenueResubmissionPreviousNote(editor);
  }
};

var updateVenueSubmissionAuthorListGuidance = function(container, profile) {
  var authorListLine = getSignedInSubmissionAuthorListLine(profile);
  if (!container || !container.length) {
    return;
  }

  container.find('.submission-author-list-helper').remove();
  if (!authorListLine) {
    return;
  }

  var authorListInput = container.find('textarea[name="author_list"], input[name="author_list"]').first();
  if (!authorListInput.length) {
    return;
  }

  var profileHint = container.find('.jmlr-author-list-profile-id-hint');
  if (!profileHint.length) {
    profileHint = $('<p class="jmlr-author-list-profile-id-hint text-muted" style="margin: 4px 0 8px;"></p>');
    authorListInput.before(profileHint);
  }
  profileHint.text('For example, your OpenReview profile ID is ' + authorListLine + '.');
};

var parseVenueSubmissionAuthorList = function(authorList) {
  if (String(authorList || '').match(/[\r\n]/)) {
    return {
      error: 'Author List must use comma-separated OpenReview profile IDs only. Line breaks are not allowed.'
    };
  }
  var authorids = [];
  (authorList || '').split(',').forEach(function(part) {
    var authorid = part.trim();
    if (authorid) {
      authorids.push(authorid);
    }
  });

  if (!authorids.length) {
    return {
      error: 'Author List is required. Enter every author by OpenReview profile ID, in paper order, for example: ~First_Author1, ~Second_Author1.'
    };
  }

  var seen = {};
  for (var i = 0; i < authorids.length; i += 1) {
    var authorid = authorids[i];
    var entryNumber = i + 1;
    if (!/^~[A-Za-z0-9_]+[0-9]*$/.test(authorid)) {
      return {
        error: 'Author List entry ' + entryNumber + ' must be a valid OpenReview profile ID like ~First_Author1. Email addresses and names are not allowed: ' + authorid + '.'
      };
    }
    if (seen[authorid]) {
      return { error: 'Author List contains a duplicate OpenReview profile ID: ' + authorid + '.' };
    }
    seen[authorid] = true;
  }

  return {
    authors: authorids,
    authorids: authorids,
    authorList: authorids.join(', ')
  };
};

var validateVenueSubmissionSubmittingAuthor = function(authorids) {
  var profileId = user && user.profile && user.profile.id;
  if (!profileId || !_.startsWith(profileId, '~')) {
    return 'You must be signed in with an OpenReview profile to submit.';
  }
  if (authorids.indexOf(profileId) < 0) {
    return 'The submitting author must be included in Author List using their OpenReview profile ID: ' + profileId + '.';
  }
  return null;
};

var normalizeVenueSubmissionInvitationForEditor = function(submissionInvitation) {
  var invitationForEditor = $.extend(true, {}, submissionInvitation);
  var content = invitationForEditor.edit &&
    invitationForEditor.edit.note &&
    invitationForEditor.edit.note.content;

  if (content) {
    [
      'authors',
      'authorids',
      'pdf',
      'supplementary_material',
      'response_to_reviewers',
      'open_source_software',
      'previous_JMLR_submission_number',
      'venue',
      'venueid',
      'previous_JMLR_submission_URL',
      'previous_JMLR_submissions',
      'author_change_summary',
      'camera_ready_revision_action',
      'download_publication_files_action',
      'previous_author_names',
      'current_author_names'
    ].forEach(function(fieldName) {
      delete content[fieldName];
    });
  }

  return invitationForEditor;
};

var renderVenueSubmissionEditor = function(options) {
  options = options || {};
  ensureVenueSubmissionFileChunkUpload();
  ensureVenueSubmissionEditSignaturePost();

  var buttonContainer = $('#new-submission');
  if (!buttonContainer.length) {
    return $.Deferred().resolve().promise();
  }

  if (user && user.profile && user.profile.id && !_.startsWith(user.id, 'guest_')) {
    venueSubmissionSignedInProfile = user.profile;
    Webfield2.api.get('/profiles', { id: user.profile.id })
      .then(function(result) {
        var profile = result && result.profiles && result.profiles[0];
        if (profile) {
          venueSubmissionSignedInProfile = profile;
          updateVenueSubmissionAuthorListGuidance($('.note_editor', '#new-submission'), venueSubmissionSignedInProfile);
        }
      });
  }

  return Webfield2.get('/invitations', { id: SUBMISSION_ID })
    .then(function(result) {
      var submissionInvitation = result.invitations && result.invitations[0];
      if (!submissionInvitation) {
        return $.Deferred().reject('Submission invitation not found').promise();
      }

      var invitationForEditor = normalizeVenueSubmissionInvitationForEditor(submissionInvitation);
      buttonContainer.hide().append(view.mkInvitationButton(invitationForEditor, function() {
        if (!user || _.startsWith(user.id, 'guest_')) {
          promptLogin(user);
          return;
        }

        if ($('.note_editor', buttonContainer).length) {
          $('.note_editor', buttonContainer).slideUp('normal', function() {
            $(this).remove();
          });
          return;
        }

        var profileId = user && user.profile && user.profile.id;
        var editorInvitation = $.extend(true, {}, invitationForEditor);
        if (profileId && _.startsWith(profileId, '~') && editorInvitation.edit) {
          editorInvitation.edit.signatures = [profileId];
        }

        view2.mkNewNoteEditor(editorInvitation, null, null, user, {
          onCompleted: function(editor) {
            if (editor) {
              editor.hide();
              ensureVenueSubmissionEditorAlignment(editor);
              markVenueSubmissionEditor(editor);
              updateVenueSubmissionAuthorListGuidance(editor, venueSubmissionSignedInProfile || (user && user.profile));
              relabelVenueSubmissionMainPaperPdf(editor);
              renderVenueSubmissionControlledFiles(editor);
              renderVenueSubmissionControlledOss(editor);
              prefillVenueSubmissionModeFields(editor);
              installVenueSubmissionControlledSubmit(editor);
              buttonContainer.append(editor);
              editor.slideDown();
            }
          },
          onValidate: function(invitationObj, formData) {
            var editor = $('.note_editor', buttonContainer);
            var profileId = user && user.profile && user.profile.id;
            var lockedResubmissionAuthorList = editor.data('jmlr-resubmission-author-list');
            if (lockedResubmissionAuthorList) {
              formData.author_list = lockedResubmissionAuthorList;
            }
            var parsedAuthorList = parseVenueSubmissionAuthorList(formData.author_list);
            if (parsedAuthorList.error) {
              return [parsedAuthorList.error];
            }
            var submittingAuthorError = validateVenueSubmissionSubmittingAuthor(parsedAuthorList.authorids);
            if (submittingAuthorError) {
              return [submittingAuthorError];
            }
            formData.author_list = parsedAuthorList.authorList;
            formData.authors = parsedAuthorList.authors;
            formData.authorids = parsedAuthorList.authorids;
            formData.venue = 'Submitted to JMLR';
            formData.venueid = VENUE_ID + '/Submitted';
            if (venueSubmissionControlledFileValue(editor, 'pdf')) {
              formData.pdf = venueSubmissionControlledFileValue(editor, 'pdf');
            }
            if (venueSubmissionControlledFileValue(editor, 'supplementary_material')) {
              formData.supplementary_material = venueSubmissionControlledFileValue(editor, 'supplementary_material');
            }
            if (venueSubmissionControlledFileValue(editor, 'response_to_reviewers')) {
              formData.response_to_reviewers = venueSubmissionControlledFileValue(editor, 'response_to_reviewers');
            }
            if (profileId && _.startsWith(profileId, '~')) {
              formData.signatures = [profileId];
              formData.editSignatureInputValues = [profileId];
            }
            var lockedResubmissionOss = editor.data('jmlr-resubmission-oss');
            if (!OSS_ACTION_EDITORS_ENABLED) {
              delete formData.open_source_software;
            } else if (lockedResubmissionOss === 'true') {
              formData.open_source_software = true;
            } else if (lockedResubmissionOss === 'false') {
              delete formData.open_source_software;
            } else if (editor.find('input.jmlr-controlled-oss[name="open_source_software"]').first().prop('checked')) {
              formData.open_source_software = true;
            } else {
              delete formData.open_source_software;
            }
            if (editor.data(venueSubmissionControlledFileKey('pdf') + '-uploading')) {
              return ['Main Paper PDF is still uploading. Wait for the upload to finish before submitting.'];
            }
            if (!formData.pdf) {
              return ['Main Paper PDF is required. Use the file chooser below Main Paper PDF to upload the main paper PDF before submitting.'];
            }
            var previousNumber = String(getVenueSubmissionPreviousNumber() || formData.previous_JMLR_submission_number || '').trim();
            if (!previousNumber) {
              formData.previous_JMLR_submission_number = 'N/A';
              previousNumber = 'N/A';
            }
            if (previousNumber && previousNumber.toUpperCase() !== 'N/A') {
              if (!/^\d+$/.test(previousNumber)) {
                return ['Previous JMLR Submission Number must be a number, or N/A for a new submission.'];
              }
              formData.previous_JMLR_submission_number = previousNumber;
              var previousList = editor.data('jmlr-resubmission-previous-list');
              if (previousList) {
                formData.previous_JMLR_submissions = previousList;
              }
              if (editor.data(venueSubmissionControlledFileKey('response_to_reviewers') + '-uploading')) {
                return ['Response to Reviewers PDF is still uploading. Wait for the upload to finish before submitting.'];
              }
              if (!formData.response_to_reviewers) {
                return ['Response to Reviewers PDF is required for resubmissions. Use the file chooser below Response to Reviewers to upload a PDF before submitting.'];
              }
            } else {
              delete formData.response_to_reviewers;
            }
            delete formData.author_change_confirmed;
            delete formData.author_change_approval_status;
            delete formData.author_change_summary;
            delete formData.previous_author_names;
            delete formData.current_author_names;
            return [];
          },
          onNoteCreated: function() {
            var venueUrl = '/group?id=' + VENUE_ID + '&submissionPending=1';
            if (typeof globalThis !== 'undefined' && globalThis.location) {
              globalThis.location.href = venueUrl;
            } else if (typeof location !== 'undefined') {
              location.href = venueUrl;
            }
          }
        });
      }, { largeLabel: true }));

      var pageHash = '';
      var pageSearch = '';
      var pageLocation =
        (typeof globalThis !== 'undefined' && globalThis.location) ||
        (typeof location !== 'undefined' && location);
      if (pageLocation) {
        pageHash = pageLocation.hash || '';
        pageSearch = pageLocation.search || '';
      }
      if ((args && args.newSubmission) ||
          pageHash.indexOf('new-submission') >= 0 ||
          /[?&]newSubmission=1(?:&|$)/.test(pageSearch)) {
        $('#jmlr-new-submission-entry > a.list-group-item').hide();
        setTimeout(function() {
          buttonContainer.find('button').filter(function() {
            return $(this).text().trim() === 'JMLR Submission';
          }).first().trigger('click');
        }, 0);
      }

      if (options.onlyWhenRoute && !isVenueSubmissionRoute()) {
        return buttonContainer.hide().promise();
      }
      return buttonContainer.fadeIn().promise();
    })
    .fail(function(error) {
      Webfield2.ui.errorMessage(error);
    });
};
