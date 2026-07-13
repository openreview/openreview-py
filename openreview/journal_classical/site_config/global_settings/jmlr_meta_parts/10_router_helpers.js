var currentUserIds = function() {
  if (!user || user.isGuest) {
    return [];
  }

  var ids = [];
  if (user.id) {
    ids.push(user.id);
  }
  if (user.profile) {
    ['id', 'preferredId'].forEach(function(field) {
      if (user.profile[field]) {
        ids.push(user.profile[field]);
      }
    });
    (user.profile.usernames || []).forEach(function(username) {
      ids.push(username);
    });
    (user.profile.emails || []).forEach(function(email) {
      ids.push(email);
    });
    (user.profile.confirmedEmails || []).forEach(function(email) {
      ids.push(email);
    });
    if (user.profile.preferredEmail) {
      ids.push(user.profile.preferredEmail);
    }
  }
  return _.uniq(ids.filter(Boolean));
};

var isOssActionEditorProfile = function(profileId, ossActionEditorIds) {
  if (!profileId) return false;
  if (!ossActionEditorIds) return false;
  if (ossActionEditorIds instanceof Set) return ossActionEditorIds.has(profileId);
  return (ossActionEditorIds || []).indexOf(profileId) >= 0;
};

var safeReloadPage = function() {
  var pageLocation =
    (typeof globalThis !== 'undefined' && globalThis.location) ||
    (typeof document !== 'undefined' && document.location) ||
    (typeof location !== 'undefined' && location);
  if (pageLocation && typeof pageLocation.reload === 'function') {
    pageLocation.reload();
  } else if (pageLocation && pageLocation.href) {
    pageLocation.href = pageLocation.href;
  }
};

var userHasRole = function(group, ids) {
  if (!group || !group.members) {
    return false;
  }
  return (group.members || []).some(function(member) {
    return ids.includes(member);
  });
};

var userHasAuthoredSubmissions = function(ids) {
  if (!ids || !ids.length) return $.Deferred().resolve(false).promise();
  return $.when.apply($, ids.map(function(id) {
    return Webfield2.api.get('/notes', {
      invitation: SUBMISSION_ID,
      domain: VENUE_ID,
      limit: 1,
      'content.authorids': id
    }).then(function(result) {
      return Boolean(result && result.notes && result.notes.length);
    }, function() {
      return false;
    });
  })).then(function() {
    return Array.prototype.slice.call(arguments).some(Boolean);
  });
};

var consoleVisibleForUser = function(consoleConfig, ids) {
  return Webfield2.api.getGroup(consoleConfig.groupId, { select: 'id,members' })
    .then(function(group) {
      if (userHasRole(group, ids)) return consoleConfig;
      if (consoleConfig.groupId !== VENUE_ID + '/Authors') return null;
      return userHasAuthoredSubmissions(ids).then(function(hasAuthoredSubmissions) {
        return hasAuthoredSubmissions ? consoleConfig : null;
      });
    }, function() {
      if (consoleConfig.groupId !== VENUE_ID + '/Authors') return null;
      return userHasAuthoredSubmissions(ids).then(function(hasAuthoredSubmissions) {
        return hasAuthoredSubmissions ? consoleConfig : null;
      });
    });
};

var hideVenueGroupChrome = function() {
  var hideAction = function() {
    $('a, button').filter(function() {
      var text = $(this).text().replace(/\s+/g, ' ').trim();
      var href = $(this).attr('href') || '';
      return text === 'Edit Group' ||
        (href.indexOf('/group/edit') >= 0 && href.indexOf('id=' + encodeURIComponent(VENUE_ID)) >= 0);
    }).each(function() {
      $(this).hide();
    });

    $('body *').filter(function() {
      var text = $(this).text().replace(/\s+/g, ' ').trim();
      return text.indexOf('Currently showing group in View mode') >= 0 && text.length < 160;
    }).each(function() {
      $(this).hide();
    });
  };
  hideAction();
  var attempts = 0;
  var interval = globalThis.setInterval(function() {
    attempts += 1;
    hideAction();
    if (attempts >= 40) globalThis.clearInterval(interval);
  }, 250);
};

var isVenueSubmissionRoute = function() {
  var pageHash = '';
  var pageSearch = '';
  var pageLocation =
    (typeof globalThis !== 'undefined' && globalThis.location) ||
    (typeof location !== 'undefined' && location);
  if (pageLocation) {
    pageHash = pageLocation.hash || '';
    pageSearch = pageLocation.search || '';
  }
  return Boolean(
    (args && args.newSubmission) ||
    pageHash.indexOf('new-submission') >= 0 ||
    /[?&]newSubmission=1(?:&|$)/.test(pageSearch)
  );
};

var renderConsoles = function(consoles) {
  if (!consoles.length) {
    $('#your-consoles').html(
      '<p class="text-muted">No JMLR role consoles are available for this account.</p>'
    );
    return;
  }

  $('#your-consoles').html(
    '<div class="list-group" style="max-width: 760px;">' +
      consoles.map(function(consoleConfig) {
        return '<a class="list-group-item" href="/group?id=' + encodeURIComponent(consoleConfig.groupId) + '">' +
          '<h4 class="list-group-item-heading">' + _.escape(consoleConfig.label) + '</h4>' +
          '<p class="list-group-item-text">' + _.escape(consoleConfig.description) + '</p>' +
        '</a>';
      }).join('') +
    '</div>'
  );
};

var renderVenueSubmissionRouteButton = function() {
  if (isVenueSubmissionRoute()) return;
  var submissionUrl = '/group?id=' + encodeURIComponent(VENUE_ID) + '#new-submission';
  var actionRow = ensureVenueActionRow();
  actionRow.find('#jmlr-submission-route').remove();
  actionRow.append(
    '<a id="jmlr-submission-route" class="btn btn-primary btn-sm" style="margin-left: 8px;" href="' + submissionUrl + '" onclick="window.location.href = \'' + submissionUrl + '\'; return false;">' +
      'JMLR Submission' +
    '</a>'
  );
};

var ensureVenueActionRow = function() {
  var wrapper = $('#jmlr-venue-actions');
  if (!wrapper.length) {
    wrapper = $(
      '<div id="jmlr-venue-actions" style="margin: 0.5rem 0 1rem;">' +
        '<div id="jmlr-venue-actions-row" class="text-right">' +
          '<span class="text-muted" style="font-weight: 600;">Add:</span>' +
        '</div>' +
        '<div id="jmlr-venue-actions-editor" style="margin-top: 0.75rem;"></div>' +
      '</div>'
    );
    var consoles = $('#your-consoles');
    if (consoles.length) {
      wrapper.insertAfter(consoles);
    } else {
      $('#group-container').append(wrapper);
    }
  }
  return wrapper.find('#jmlr-venue-actions-row');
};

var polishReviewerVolunteerEditor = function(editor) {
  if (!editor || !editor.length) return;
  editor.addClass('jmlr-reviewer-volunteer-editor');
  editor.find('input[name="title"]').closest('.row, .form-group').hide();
  editor.find('.small_heading, label').filter(function() {
    var headingText = $(this).text().replace(/\*/g, '').replace(/\s+/g, ' ').trim();
    return headingText === 'Readers' || headingText === 'Signatures';
  }).each(function() {
    $(this).parent().hide();
    $(this).closest('div').hide();
    $(this).closest('.row, .form-group').hide();
  });
  editor.find('.row, .form-group').filter(function() {
    var headingText = $(this).find('.small_heading, label').first().text().replace(/\*/g, '').replace(/\s+/g, ' ').trim();
    return headingText === 'Readers' || headingText === 'Signatures';
  }).hide();
  editor.find('*').filter(function() {
    var directText = $(this).clone().children().remove().end().text().replace(/\s+/g, ' ').trim();
    return directText === 'Edit History';
  }).each(function() {
    $(this).parent().hide();
  });
};

var renderReviewerVolunteerRouteButton = function() {
  if (isVenueSubmissionRoute() || !user || user.isGuest) return $.Deferred().resolve().promise();
  var profileId = user && user.profile && user.profile.id;
  if (!profileId || !_.startsWith(profileId, '~')) return $.Deferred().resolve().promise();
  return Webfield2.api.getGroup(REVIEWERS_ID, { select: 'id,members' }).then(function(group) {
    var members = group && group.members || [];
    if (members.indexOf(profileId) >= 0) {
      return;
    }
    var invitationId = VENUE_ID + '/-/Reviewer_Volunteer';
    return Webfield2.get('/invitations', { id: invitationId }).then(function(result) {
      var invitation = result.invitations && result.invitations[0];
      if (!invitation) return;
      var actionRow = ensureVenueActionRow();
      var editorContainer = $('#jmlr-venue-actions-editor');
      var invitationForEditor = $.extend(true, {}, invitation);
      if (invitationForEditor.edit) {
        invitationForEditor.edit.signatures = [profileId];
      }
      actionRow.find('#jmlr-reviewer-volunteer-route').remove();
      var button = $(
        '<button id="jmlr-reviewer-volunteer-route" type="button" class="btn btn-default btn-sm" style="margin-left: 8px;">' +
          'Willing to review for JMLR' +
        '</button>'
      );
      button.on('click', function() {
        if ($('.note_editor', editorContainer).length) {
          $('.note_editor', editorContainer).slideUp('normal', function() {
            $(this).remove();
          });
          return;
        }
        view2.mkNewNoteEditor(invitationForEditor, null, null, user, {
          onCompleted: function(editor) {
            if (!editor) return;
            editor.hide();
            editorContainer.empty().append(editor);
            polishReviewerVolunteerEditor(editor);
            editor.slideDown();
            setTimeout(function() {
              polishReviewerVolunteerEditor(editor);
            }, 250);
          },
          onValidate: function(invitationObj, formData) {
            if (formData.confirmation !== 'Yes, I am willing to review for JMLR' &&
                (!_.isArray(formData.confirmation) || formData.confirmation.indexOf('Yes, I am willing to review for JMLR') < 0)) {
              return ['Please confirm that you are willing to review for JMLR.'];
            }
            formData.confirmation = 'Yes, I am willing to review for JMLR';
            formData.signatures = [profileId];
            formData.editSignatureInputValues = [profileId];
            return [];
          },
          onNoteCreated: function() {
            button.remove();
            editorContainer.html(
              '<div class="alert alert-success text-left" role="alert" style="margin-top: 0.5rem;">' +
                '<strong>Thank you.</strong> You have been added to the JMLR reviewer pool. You can adjust your reviewing load from the Reviewer Console.' +
              '</div>'
            );
          }
        });
      });
      actionRow.append(button);
    });
  }, function() {
    return;
  });
};

var memberId = function(member) {
  return typeof member === 'string' ? member : member.id;
};

var getGroupSafe = function(groupId, options) {
  return Webfield2.api.getGroup(groupId, options).then(function(group) {
    if (!group) {
      return { id: groupId, members: [], exists: false };
    }
    group.exists = true;
    return group;
  }, function() {
    return { id: groupId, members: [], exists: false };
  });
};

var getEdgesByTailMap = function(invitationId, headId) {
  return Webfield2.api.getAll('/edges', { invitation: invitationId, head: headId, domain: VENUE_ID })
    .then(function(edges) {
      return (edges || []).reduce(function(byTail, edge) {
        byTail[edge.tail] = edge;
        return byTail;
      }, {});
    }, function() {
      return {};
    });
};

var getGroupContentValue = function(group, key) {
  return group && group.content && group.content[key] && group.content[key].value;
};

var userCanManagePeople = function(eicGroup) {
  var ids = currentUserIds();
  return userHasRole(eicGroup || { members: [] }, ids);
};
