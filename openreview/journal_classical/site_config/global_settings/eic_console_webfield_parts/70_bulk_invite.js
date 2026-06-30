var getBulkInviteConfig = function(role) {
  return $.extend({}, BULK_INVITE_TEMPLATES[role] || BULK_INVITE_TEMPLATES.reviewer, jmlrBulkInviteTemplates[role] || {});
};

var setBulkInviteStatus = function(message, isError) {
  $('#bulk-invite-status')
    .removeClass('text-danger text-success text-muted')
    .addClass(isError ? 'text-danger' : (message ? 'text-success' : 'text-muted'))
    .text(message || '');
};

var addBulkInviteRow = function(values) {
  values = values || {};
  var rowCount = $('#bulk-invite-recipient-rows .bulk-invite-recipient-row').length + 1;
  $('#bulk-invite-recipient-rows').append(
    '<div class="bulk-invite-recipient-row row" style="margin-bottom: 8px;">' +
      '<div class="col-sm-4">' +
        '<label class="sr-only" for="bulk-invite-openreviewid-' + rowCount + '">OpenReview ID</label>' +
        '<input id="bulk-invite-openreviewid-' + rowCount + '" class="form-control bulk-invite-openreviewid" type="text" placeholder="~OpenReview_ID" value="' + _.escape(values.openreviewid || '') + '">' +
      '</div>' +
      '<div class="col-sm-4">' +
        '<label class="sr-only" for="bulk-invite-email-' + rowCount + '">Email</label>' +
        '<input id="bulk-invite-email-' + rowCount + '" class="form-control bulk-invite-email" type="email" placeholder="email@example.edu" value="' + _.escape(values.email || '') + '">' +
      '</div>' +
      '<div class="col-sm-3">' +
        '<label class="sr-only" for="bulk-invite-name-' + rowCount + '">Name</label>' +
        '<input id="bulk-invite-name-' + rowCount + '" class="form-control bulk-invite-name" type="text" placeholder="Full Name" value="' + _.escape(values.name || '') + '">' +
      '</div>' +
      '<div class="col-sm-1">' +
        '<button type="button" class="btn btn-default js-remove-bulk-invite-row" aria-label="Remove invitee row">&times;</button>' +
      '</div>' +
    '</div>'
  );
};

var collectBulkInviteRows = function() {
  var rows = [];
  var errors = [];
  var ignored = 0;
  var seenRecipients = {};
  $('#bulk-invite-recipient-rows .bulk-invite-recipient-row').each(function(index) {
    var row = $(this);
    var openreviewid = (row.find('.bulk-invite-openreviewid').val() || '').trim();
    var email = (row.find('.bulk-invite-email').val() || '').trim();
    var name = (row.find('.bulk-invite-name').val() || '').trim();
    var rowNumber = index + 1;

    if (!openreviewid && !email && !name) {
      return;
    }
    if (openreviewid) {
      if (!_.startsWith(openreviewid, '~')) {
        errors.push('Row ' + rowNumber + ': OpenReview ID must start with ~.');
      }
      if (seenRecipients['id:' + openreviewid.toLowerCase()]) {
        ignored += 1;
        return;
      }
      seenRecipients['id:' + openreviewid.toLowerCase()] = true;
      rows.push({
        openreviewid: openreviewid,
        email: '',
        name: ''
      });
      return;
    }
    if (!isBulkInviteValidEmail(email)) {
      ignored += 1;
      return;
    }
    if (seenRecipients['email:' + email.toLowerCase()]) {
      ignored += 1;
      return;
    }
    seenRecipients['email:' + email.toLowerCase()] = true;
    rows.push({
      openreviewid: '',
      email: email,
      name: name
    });
  });
  return {
    rows: rows,
    errors: errors,
    ignored: ignored
  };
};

var isBulkInviteValidEmail = function(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email || '').trim());
};

var parseBulkInviteCsvLine = function(line) {
  var values = [];
  var current = '';
  var inQuotes = false;
  for (var index = 0; index < line.length; index += 1) {
    var character = line.charAt(index);
    var nextCharacter = line.charAt(index + 1);
    if (character === '"' && inQuotes && nextCharacter === '"') {
      current += '"';
      index += 1;
    } else if (character === '"') {
      inQuotes = !inQuotes;
    } else if (character === ',' && !inQuotes) {
      values.push(current.trim());
      current = '';
    } else {
      current += character;
    }
  }
  values.push(current.trim());
  return values;
};

var parseBulkInviteCsv = function(csvText) {
  var lines = String(csvText || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
  var headerLine = lines.shift();
  var rows = [];
  var ignored = 0;
  var seenRecipients = {};
  var errors = [];

  if (!headerLine) {
    return { rows: [], ignored: 0, errors: ['CSV file is empty.'] };
  }
  var headers = parseBulkInviteCsvLine(headerLine).map(function(header) {
    return header.trim().toLowerCase();
  });
  if (headers.join(',') !== 'openreviewid,email,name') {
    return { rows: [], ignored: lines.length, errors: ['CSV header must be exactly openreviewid,email,name.'] };
  }

  lines.forEach(function(line) {
    if (!line.trim()) {
      return;
    }
    var values = parseBulkInviteCsvLine(line);
    if (values.length !== 3) {
      ignored += 1;
      return;
    }
    var openreviewid = (values[0] || '').trim();
    var email = (values[1] || '').trim();
    var name = (values[2] || '').trim();
    var key;

    if (openreviewid) {
      if (!_.startsWith(openreviewid, '~')) {
        ignored += 1;
        return;
      }
      key = 'id:' + openreviewid.toLowerCase();
      if (seenRecipients[key]) {
        ignored += 1;
        return;
      }
      seenRecipients[key] = true;
      rows.push({ openreviewid: openreviewid, email: '', name: '' });
      return;
    }

    if (!isBulkInviteValidEmail(email)) {
      ignored += 1;
      return;
    }
    key = 'email:' + email.toLowerCase();
    if (seenRecipients[key]) {
      ignored += 1;
      return;
    }
    seenRecipients[key] = true;
    rows.push({ openreviewid: '', email: email, name: name });
  });

  return { rows: rows, ignored: ignored, errors: errors };
};

var setBulkInviteRows = function(rows) {
  $('#bulk-invite-recipient-rows').empty();
  rows.forEach(function(row) {
    addBulkInviteRow(row);
  });
  if (!rows.length) {
    addBulkInviteRow();
  }
};

var updateBulkInvitePreview = function(message) {
  var recipientData = collectBulkInviteRows();
  var preview = message || ('Preview: ' + recipientData.rows.length + ' accepted, ' + recipientData.ignored + ' ignored.');
  $('#bulk-invite-preview')
    .removeClass('text-danger text-success text-muted')
    .addClass(recipientData.errors.length ? 'text-danger' : 'text-muted')
    .text(recipientData.errors.length ? recipientData.errors.join(' ') : preview);
};

var handleBulkInviteCsvUpload = function(event) {
  var file = event.target.files && event.target.files[0];
  if (!file) {
    updateBulkInvitePreview();
    return;
  }
  if (!/\.csv$/i.test(file.name || '')) {
    $('#bulk-invite-preview').removeClass('text-muted text-success').addClass('text-danger').text('Upload a UTF-8 .csv file.');
    return;
  }
  var reader = new FileReader();
  reader.onload = function(loadEvent) {
    var parsed = parseBulkInviteCsv(loadEvent.target.result || '');
    if (parsed.errors.length) {
      $('#bulk-invite-preview').removeClass('text-muted text-success').addClass('text-danger').text(parsed.errors.join(' '));
      return;
    }
    setBulkInviteRows(parsed.rows);
    $('#bulk-invite-preview')
      .removeClass('text-danger text-muted')
      .addClass('text-success')
      .text('CSV preview: ' + parsed.rows.length + ' accepted, ' + parsed.ignored + ' ignored.');
  };
  reader.onerror = function() {
    $('#bulk-invite-preview').removeClass('text-muted text-success').addClass('text-danger').text('Could not read CSV file.');
  };
  reader.readAsText(file);
};

var bulkInviteRowsToInviteeDetails = function(rows) {
  return rows.map(function(row) {
    if (row.openreviewid) {
      return row.openreviewid;
    }
    return row.name ? row.email + ', ' + row.name : row.email;
  }).join('\n');
};

var bulkInviteTargetForRole = function(role) {
  if (role === 'actionEditor') {
    return {
      roleName: 'Action Editor',
      acceptedGroupId: ACTION_EDITOR_ID,
      inviteEdgeId: ACTION_EDITOR_ID + '/-/Recruitment_Invite',
      responseInvitationId: ACTION_EDITOR_ID + '/-/Recruitment'
    };
  }
  return {
    roleName: 'Reviewer',
    acceptedGroupId: REVIEWERS_ID,
    inviteEdgeId: REVIEWERS_ID + '/-/Recruitment_Invite',
    responseInvitationId: REVIEWERS_ID + '/-/Recruitment'
  };
};

var bulkInviteRecipientIdentity = function(row) {
  return row.openreviewid || row.email;
};

var bulkInviteRecipientName = function(row) {
  return row.name || row.openreviewid || row.email || 'invitee';
};

var hmacSha256Hex = function(secret, value) {
  if (typeof crypto === 'undefined' || !crypto.subtle || typeof TextEncoder === 'undefined') {
    return Promise.reject(new Error('This browser does not support the crypto API required to create recruitment links.'));
  }
  var encoder = new TextEncoder();
  return crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  ).then(function(key) {
    return crypto.subtle.sign('HMAC', key, encoder.encode(value));
  }).then(function(signature) {
    return Array.prototype.map.call(new Uint8Array(signature), function(byte) {
      return byte.toString(16).padStart(2, '0');
    }).join('');
  });
};

var bulkInviteResponseUrl = function(target, identity, edgeId, response) {
  return hmacSha256Hex(BULK_INVITE_HASH_SEED, edgeId + ':' + identity).then(function(key) {
    return location.origin + '/invitation?id=' + target.responseInvitationId +
      '&edge_id=' + encodeURIComponent(edgeId) +
      '&user=' + encodeURIComponent(identity) +
      '&key=' + encodeURIComponent(key) +
      '&response=' + encodeURIComponent(response);
  });
};

var renderBulkInviteMessage = function(template, target, row, acceptUrl, declineUrl) {
  return template
    .replace(/\{\{\s*fullname\s*\}\}/g, bulkInviteRecipientName(row))
    .replace(/\{\{\s*role\s*\}\}/g, target.roleName)
    .replace(/\{\{\s*accept_url\s*\}\}/g, acceptUrl)
    .replace(/\{\{\s*decline_url\s*\}\}/g, declineUrl);
};

var postBulkInviteMessage = function(subject, message, recipient, target) {
  return Webfield2.api.post('/messages', {
    groups: [recipient],
    subject: subject,
    message: message,
    invitation: VENUE_ID + '/-/Edit',
    signature: VENUE_ID
  });
};

var asBulkInvitePromise = function(result) {
  if (result && typeof result.done === 'function') {
    return new Promise(function(resolve, reject) {
      result.done(resolve);
      result.fail(reject);
    });
  }
  return Promise.resolve(result);
};

var bulkRecruitmentInviteExpirationDate = function() {
  return Date.now() + Number(BULK_RECRUITMENT_NO_RESPONSE_EXPIRATION_DAYS || 21) * 24 * 60 * 60 * 1000;
};

var postBulkRecruitmentInviteEdge = function(row, target) {
  var identity = bulkInviteRecipientIdentity(row);
  return Webfield2.api.post('/edges', {
    invitation: target.inviteEdgeId,
    signatures: [EDITORS_IN_CHIEF_ID],
    head: target.acceptedGroupId,
    tail: identity,
    label: 'Invitation Sent',
    weight: 1,
    ddate: bulkRecruitmentInviteExpirationDate(),
    readers: [EDITORS_IN_CHIEF_ID, identity],
    writers: [EDITORS_IN_CHIEF_ID]
  });
};

var expireBulkRecruitmentInviteEdge = function(edge) {
  if (!edge || !edge.id) {
    return Promise.resolve();
  }
  edge.label = 'Expired';
  edge.ddate = Date.now();
  edge.cdate = null;
  return asBulkInvitePromise(Webfield2.api.post('/edges', edge)).catch(function() {});
};

var updateBulkInviteTemplate = function() {
  var role = $('#bulk-invite-role').val();
  var config = getBulkInviteConfig(role);
  $('#bulk-invite-subject').val(config.subject);
  $('#bulk-invite-content').val(config.content);
  $('#bulk-invite-invitation').text(config.invitationId);
  $('#bulk-invite-role-note').text(config.note || '');
};

var submitBulkInvite = function() {
  var role = $('#bulk-invite-role').val();
  var config = getBulkInviteConfig(role);
  var recipientData = collectBulkInviteRows();
  var subject = ($('#bulk-invite-subject').val() || '').trim();
  var content = ($('#bulk-invite-content').val() || '').trim();
  var signature = user && user.profile && user.profile.id || user && user.id;

  if (!signature) {
    setBulkInviteStatus('Could not determine your OpenReview profile signature.', true);
    return;
  }
  if (recipientData.errors.length) {
    setBulkInviteStatus(recipientData.errors.join(' '), true);
    return;
  }
  if (!recipientData.rows.length) {
    setBulkInviteStatus('Enter at least one invitee before sending.', true);
    return;
  }
  if (!subject || !content) {
    setBulkInviteStatus('Email subject and content are required.', true);
    return;
  }
  if (content.indexOf('{{accept_url}}') < 0 || content.indexOf('{{decline_url}}') < 0) {
    setBulkInviteStatus('Email content must include {{accept_url}} and {{decline_url}}.', true);
    return;
  }

  var count = recipientData.rows.length;
  if (typeof confirm === 'function' && !confirm('Send ' + config.label + ' recruitment email to ' + count + ' invitee(s)?')) {
    return;
  }

  var submitButton = $('#bulk-invite-submit');
  submitButton.prop('disabled', true).text('Sending...');
  setBulkInviteStatus('Sending recruitment emails...', false);

  var target = bulkInviteTargetForRole(role);
  Promise.all(recipientData.rows.map(function(row) {
    var identity = bulkInviteRecipientIdentity(row);
    var postedEdge;
    return asBulkInvitePromise(postBulkRecruitmentInviteEdge(row, target)).then(function(edgeResponse) {
      postedEdge = edgeResponse && (edgeResponse.edge || edgeResponse);
      if (!postedEdge || !postedEdge.id) {
        throw new Error('OpenReview did not return a recruitment invite edge id.');
      }
      return Promise.all([
        bulkInviteResponseUrl(target, identity, postedEdge.id, 'Yes'),
        bulkInviteResponseUrl(target, identity, postedEdge.id, 'No')
      ]);
    }).then(function(urls) {
      var message = renderBulkInviteMessage(content, target, row, urls[0], urls[1]);
      return asBulkInvitePromise(postBulkInviteMessage(subject, message, identity, target));
    }).catch(function(error) {
      return expireBulkRecruitmentInviteEdge(postedEdge).then(function() {
        throw error;
      });
    });
  })).then(function() {
    setBulkInviteStatus('Recruitment messages created for ' + count + ' invitee(s).', false);
    submitButton.text('Sent');
    setTimeout(function() {
      submitButton.prop('disabled', false).text('Send Bulk Invite');
    }, 1200);
  }).catch(function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to send recruitment emails.';
    setBulkInviteStatus(message, true);
    submitButton.prop('disabled', false).text('Send Bulk Invite');
  });
};

var renderBulkInviteTab = function(venueStatusData) {
  jmlrBulkInviteTemplates = venueStatusData.bulkInviteTemplates || {};
  $('#bulk-invite').html(
    '<div class="container" style="max-width: 980px;">' +
      '<h3>Bulk Invite</h3>' +
      '<p class="dark">Send recruitment invitations for reviewers or action editors. Add one invitee per row. Use <code>openreviewid</code> when available; otherwise enter <code>email</code> and optional <code>name</code>.</p>' +
      '<div class="form-group">' +
        '<label for="bulk-invite-role">Role</label>' +
        '<select id="bulk-invite-role" class="form-control" style="max-width: 360px;">' +
          '<option value="reviewer">Reviewers</option>' +
          '<option value="actionEditor">Action Editors</option>' +
        '</select>' +
        '<p id="bulk-invite-role-note" class="small text-muted mt-1"></p>' +
      '</div>' +
      '<div class="form-group">' +
        '<label>Invitees</label>' +
        '<div class="row small text-muted" style="margin-bottom: 4px;">' +
          '<div class="col-sm-4">openreviewid</div>' +
          '<div class="col-sm-4">email</div>' +
          '<div class="col-sm-3">name</div>' +
          '<div class="col-sm-1"></div>' +
        '</div>' +
        '<div id="bulk-invite-recipient-rows"></div>' +
        '<button id="bulk-invite-add-row" type="button" class="btn btn-default btn-sm" style="margin-top: 4px;">Add Invitee</button>' +
        '<p class="small text-muted" style="margin-top: 6px;">If <code>openreviewid</code> is present, it is used for recipient identity and email/name are ignored. If <code>openreviewid</code> is empty, email is required.</p>' +
      '</div>' +
      '<div class="form-group">' +
        '<label for="bulk-invite-csv">Upload CSV invitees</label>' +
        '<input id="bulk-invite-csv" class="form-control" type="file" accept=".csv,text/csv">' +
        '<p class="small text-muted">CSV files must use the header <code>openreviewid,email,name</code>. Blank, duplicate, and malformed rows are ignored in the preview.</p>' +
        '<p id="bulk-invite-preview" class="small text-muted">Preview: 0 accepted, 0 ignored.</p>' +
      '</div>' +
      '<div class="form-group">' +
        '<label for="bulk-invite-subject">Email subject</label>' +
        '<input id="bulk-invite-subject" class="form-control" type="text">' +
      '</div>' +
      '<div class="form-group">' +
        '<label for="bulk-invite-content">Email content</label>' +
        '<textarea id="bulk-invite-content" class="form-control" rows="18"></textarea>' +
        '<p class="small text-muted">Keep {{accept_url}} and {{decline_url}} in the message. OpenReview replaces those tokens when sending.</p>' +
      '</div>' +
      '<p class="small text-muted">Recruitment response invitation: <code id="bulk-invite-invitation"></code></p>' +
      '<p>' +
        '<button id="bulk-invite-submit" type="button" class="btn btn-primary">Send Bulk Invite</button> ' +
        '<a class="btn btn-default" href="/forum?id=' + JOURNAL_REQUEST_ID + '&referrer=' + referrerUrl + '">Open Journal Request Forum</a>' +
      '</p>' +
      '<p id="bulk-invite-status" class="text-muted"></p>' +
    '</div>'
  );
  addBulkInviteRow();
  addBulkInviteRow();
  addBulkInviteRow();
  updateBulkInviteTemplate();
  $('#bulk-invite-role').off('change').on('change', updateBulkInviteTemplate);
  $('#bulk-invite-add-row').off('click').on('click', function() {
    addBulkInviteRow();
    updateBulkInvitePreview();
  });
  $('#bulk-invite').off('click', '.js-remove-bulk-invite-row').on('click', '.js-remove-bulk-invite-row', function() {
    $(this).closest('.bulk-invite-recipient-row').remove();
    if (!$('#bulk-invite-recipient-rows .bulk-invite-recipient-row').length) {
      addBulkInviteRow();
    }
    updateBulkInvitePreview();
  });
  $('#bulk-invite').off('input', '.bulk-invite-openreviewid,.bulk-invite-email,.bulk-invite-name').on('input', '.bulk-invite-openreviewid,.bulk-invite-email,.bulk-invite-name', function() {
    updateBulkInvitePreview();
  });
  $('#bulk-invite-csv').off('change').on('change', handleBulkInviteCsvUpload);
  $('#bulk-invite-submit').off('click').on('click', submitBulkInvite);
  updateBulkInvitePreview();
};
