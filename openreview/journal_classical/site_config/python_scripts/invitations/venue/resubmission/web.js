// JMLR delta: Journal does not expose a paper-scoped resubmission entry link.
// Seed only the hidden previous-paper field, then hand off to Journal's native
// VenueHomepage/NoteEditor so Authors keeps its searchable profile selector.
(function () {
  var venue = 'JMLR';
  var submissionInvitationId = 'JMLR/-/Submission';
  var invitationId = invitation && invitation.id || '';
  var numberMatch = invitationId.match(/\/Paper(\d+)\/-\/Resubmission$/);
  var previousNumber = numberMatch && numberMatch[1];
  var previousForumId = invitation && invitation.edit && invitation.edit.note && invitation.edit.note.forum;
  var previousUrl = '{{SITE_URL}}/forum?id=' + encodeURIComponent(previousForumId || '');

  if (!previousNumber || !previousForumId) {
    Webfield2.ui.errorMessage('The previous JMLR paper could not be resolved from this resubmission action.');
    return;
  }
  if (!user || user.isGuest) {
    Webfield2.ui.errorMessage('Log in as an author of the previous paper to submit this resubmission.');
    return;
  }

  // Native NoteEditor can initialize its draft widgets before useUser has
  // resolved the cookie. Seed both keys it can use during that transition.
  var draftUsers = ['guest', user.id];
  if (user.profile && user.profile.id) draftUsers.push(user.profile.id);
  draftUsers.filter(function (value, index, values) {
    return value && values.indexOf(value) === index;
  }).forEach(function (draftUser) {
    var storageKey = [
      draftUser, 'null', 'null', submissionInvitationId, 'previous_JMLR_submission_url'
    ].join('|');
    globalThis.localStorage.setItem(storageKey, previousUrl);
  });
  var target = '{{SITE_URL}}/group?' + $.param({
    id: venue,
    resubmissionOf: previousNumber,
    previous_JMLR_submission_URL: previousUrl
  });
  globalThis.location.replace(target);
}());
