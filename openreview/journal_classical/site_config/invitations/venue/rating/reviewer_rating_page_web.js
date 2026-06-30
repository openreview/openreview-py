var JMLR_RATING_PAGE = __JMLR_RATING_PAGE_JSON__;

var escapeHtml = function(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
};

var fieldValue = function(name) {
  var selected = $('input[name="' + name + '"]:checked').val();
  if (selected !== undefined) return selected;
  return $('[name="' + name + '"]').val() || '';
};

var contentField = function(value) {
  return { value: value };
};

var checkboxValue = function(name) {
  return $('input[name="' + name + '"]').prop('checked') === true
    ? 'Select this reviewer for automatic assignment if the paper is resubmitted.'
    : '';
};

var reviewerDisplayLabel = function() {
  return JMLR_RATING_PAGE.reviewerLabel || ('Reviewer ' + JMLR_RATING_PAGE.reviewerAnonId);
};

var closeRatingPage = function() {
  var pageWindow = typeof globalThis !== 'undefined' ? globalThis : null;
  if (!pageWindow) return;

  var $status = $('#jmlr-reviewer-rating-status');
  $status.removeClass('text-muted text-danger').addClass('text-success').text('Rating submitted. Closing this rating page...');

  try {
    pageWindow.open('', '_self');
    pageWindow.close();
  } catch (error) {}

  pageWindow.setTimeout(function() {
    if (pageWindow.closed) return;
    if (JMLR_RATING_PAGE.returnUrl) {
      pageWindow.location.replace(JMLR_RATING_PAGE.returnUrl);
    } else {
      $('#invitation-container').html('<p class="alert alert-success">Rating submitted. You may close this page.</p>');
    }
  }, 250);
};

var submitRating = function() {
  var $submit = $('#jmlr-reviewer-rating-submit');
  var $status = $('#jmlr-reviewer-rating-status');
  $submit.prop('disabled', true);
  $status.removeClass('text-danger text-success').addClass('text-muted').text('Submitting...');

  var content = {
    rating: contentField(fieldValue('rating')),
    timeliness: contentField(fieldValue('timeliness')),
    resubmission_auto_assignment: contentField(checkboxValue('resubmission_auto_assignment')),
    reviewer_anon_id: contentField(JMLR_RATING_PAGE.reviewerAnonId),
    reviewer_profile_id: contentField(JMLR_RATING_PAGE.reviewerProfileId),
    reviewer_rating_context: contentField(reviewerDisplayLabel() + ' rating context')
  };
  if (JMLR_RATING_PAGE.reviewNoteId) {
    content.review_note_id = contentField(JMLR_RATING_PAGE.reviewNoteId);
  }
  var comment = fieldValue('comment').trim();
  if (comment) {
    content.comment = contentField(comment);
  }

  Webfield2.api.post('/notes/edits?awaitProcess=false', {
    invitation: JMLR_RATING_PAGE.ratingInvitationId,
    signatures: [JMLR_RATING_PAGE.actionEditorSignature],
    note: {
      forum: JMLR_RATING_PAGE.forumId,
      replyto: JMLR_RATING_PAGE.replytoId,
      signatures: [JMLR_RATING_PAGE.actionEditorSignature],
      readers: JMLR_RATING_PAGE.readers,
      nonreaders: JMLR_RATING_PAGE.nonreaders,
      writers: JMLR_RATING_PAGE.writers,
      content: content
    }
  }).then(function() {
    closeRatingPage();
  }).fail(function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to submit reviewer rating.';
    $status.removeClass('text-muted text-success').addClass('text-danger').text(message);
    $submit.prop('disabled', false);
  });
};

var ratingOptions = ['No rating', 'Exceeds expectations', 'Meets expectations', 'Falls below expectations', 'Report problem'];
var timelinessOptions = ['On time', 'Past due', 'Review not expected'];
var radioGroup = function(name, options, selected) {
  return options.map(function(option) {
    var id = 'jmlr-' + name + '-' + option.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    return '<label class="radio-inline" for="' + id + '"><input id="' + id + '" type="radio" name="' + name + '" value="' + escapeHtml(option) + '"' + (option === selected ? ' checked="checked"' : '') + '> ' + escapeHtml(option) + '</label>';
  }).join('');
};

$('#invitation-container').html([
  '<div class="jmlr-reviewer-rating-page">',
    '<h3>Rate ' + escapeHtml(reviewerDisplayLabel()) + '</h3>',
    '<div class="well" style="white-space:pre-wrap;">' + escapeHtml(JMLR_RATING_PAGE.contextText) + '</div>',
    '<div class="form-group"><label>Rating</label><div>' + radioGroup('rating', ratingOptions, JMLR_RATING_PAGE.defaultRating || 'No rating') + '</div></div>',
    '<div class="form-group"><label>Timeliness</label><div>' + radioGroup('timeliness', timelinessOptions, JMLR_RATING_PAGE.defaultTimeliness || 'On time') + '</div></div>',
    '<div class="checkbox"><label><input type="checkbox" name="resubmission_auto_assignment"' + (JMLR_RATING_PAGE.defaultResubmissionAutoAssignment ? ' checked="checked"' : '') + '> Select this reviewer for automatic assignment if the paper is resubmitted.</label></div>',
    '<div class="form-group"><label for="jmlr-reviewer-rating-comment">Comment</label><textarea id="jmlr-reviewer-rating-comment" name="comment" class="form-control" rows="5"></textarea></div>',
    '<p class="small text-muted">This rating will be signed as ' + escapeHtml(JMLR_RATING_PAGE.actionEditorSignature) + '.</p>',
    '<button id="jmlr-reviewer-rating-submit" class="btn btn-primary" type="button">Submit rating</button> ',
    '<a class="btn btn-default" href="' + escapeHtml(JMLR_RATING_PAGE.returnUrl) + '">Cancel</a>',
    '<p id="jmlr-reviewer-rating-status" style="margin-top:10px;"></p>',
  '</div>'
].join(''));

$('#jmlr-reviewer-rating-submit').on('click', submitRating);
