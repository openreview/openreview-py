// ------------------------------------
// Advanced venue homepage template
//
// This webfield displays the conference header (#header),
// important instructions for this phase of the conference,
// and a tabbed interface for viewing various types of notes.
// ------------------------------------

// Constants
var CONFERENCE_ID = 'OpenReview.net/Archive';
var DIRECT_UPLOAD_ID = CONFERENCE_ID + '/-/Direct_Upload';
var IMPORTED_RECORD_ID = CONFERENCE_ID + '/-/Imported_Record'

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showContents: true
};

var HEADER = {
  title: 'OpenReview Archive',
  subtitle: 'Publication Upload Portal for Paper-Reviewer Matching',
  location: 'Global',
  date: 'Ongoing',
  website: 'https://openreview.net',
  instructions: '<strong>General Information</strong><br>\
    <ul>\
    <li>The OpenReview paper-reviewer matching system uses the text from your authored publications to match you with relevant papers.</li>\
    <li>Your reviewing expertise for every submission is inferred from keywords extracted from text of your publications, and is represented by an affinity score. </li> \
    <li>For any given submission, your affinity score is based on the single publication that is most similar to the submission. </li>\
    <li>While more publications are always better, breadth across your areas of expertise is the most important factor.</li>\
    </ul>\
    <strong>Updating your Expertise</strong><br>\
    <ul>\
    <li>Listed below are your authored papers that we currently have on record. </li> \
    <li>If the papers listed do not adequately represent your reviewing expertise, please upload a few papers that are representative of your work by clicking the "OpenReview Archive Direct Upload" button below.</li>\
    <li><strong>Do not upload papers that you are not willing to share publicly.</strong> If you decide to upload an unpublished paper, it will be treated as a public preprint. </li>\
    <li>In the "pdf" field, please provide either a URL to a pdf file, <strong>or</strong> upload the PDF from your hard drive.</li>\
    <li>Please make sure that the original author order is preserved.</li>\
    <li>OpenReview will attempt to fill in missing fields from the contents of the PDF.</li>\
    </ul>\
    <strong>Imported Papers</strong><br>\
    <ul>\
    <li>Some of the papers listed below have been automatically imported from records in other public repositories (e.g. SemanticScholar, arXiv, etc.).</li>\
    <li>Imported Papers are visible only to you and the other inferred authors of the paper until they have been claimed.</li>\
    <li>You can claim (or disavow, in the case of an incorrect authorship attribution) one of these records with the "Authorship Claim" option below each imported record.</li>\
    <li>Please allow a couple days for incorrect authorships to be removed from your list; they will not be incorporated into your affinity scores. </li>\
    </ul>\
    <p><strong>Questions?</strong><br> \
    Please contact the OpenReview support team at \
    <a href="mailto:info@openreview.net">info@openreview.net</a> with any questions or concerns about the OpenReview platform. \</br> \
    </p>',
}

var BUFFER = 1000 * 60 * 30;  // 30 minutes
var PAGE_SIZE = 50;

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showContents: true,
  showDetails: true
};
var commentDisplayOptions = {
  pdfLink: false,
  replyCount: true,
  showContents: false,
  showParent: true
};

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  renderConferenceHeader();
  renderSubmissionButton(DIRECT_UPLOAD_ID);
  renderConferenceTabs();

  load().then(renderContent).then(function() {
    $('.tabs-container a[href="#imported-papers"]').click();
  });
}

// Load makes all the API calls needed to get the data to render the page
// It returns a jQuery deferred object: https://api.jquery.com/category/deferred-object/
function load() {

  var authorNotesP;
  var directUploadsP;
  if (!user || _.startsWith(user.id, 'guest_')) {
    authorNotesP = $.Deferred().resolve([]);
    directUploadsP = $.Deferred().resolve([]);
  } else {
    authorNotesP = Webfield.get('/notes', {
      'content.authorids': user.profile.id,
      details: 'forumContent,writable,tags'
    }).then(function(result) {
      return result.notes;
    });

    directUploadsP = Webfield.get('/notes', {
      invitation: DIRECT_UPLOAD_ID,
      details: 'writable',
      tauthor: true,
    }).then(function(result) {
      return result.notes;
    });

  var tagInvitationsP = Webfield.getAll('/invitations', {id: 'OpenReview.net/Archive/-/Authorship_Claim', tags: true}).then(function(invitations) {
    return invitations.filter(function(invitation) {
      return invitation.invitees.length;
    });
  });

  }
  return $.when(authorNotesP, directUploadsP, tagInvitationsP);
}


// Render functions
function renderConferenceHeader() {
  Webfield.ui.venueHeader(HEADER);

  Webfield.ui.spinner('#notes');
}

function renderSubmissionButton(INVITATION_ID) {
  Webfield.api.getSubmissionInvitation(INVITATION_ID, {deadlineBuffer: BUFFER})
    .then(function(invitation) {
      Webfield.ui.submissionButton(invitation, user, {
        onNoteCreated: function() {
          // Callback funtion to be run when a paper has successfully been submitted (required)
          promptMessage('Your submission is complete.');

          load().then(renderContent).then(function() {
            $('.tabs-container a[href="#user-uploaded-papers"]').click();
          });
        }
      });
    });
}

function renderConferenceTabs() {
  var sections = [
    {
      heading: 'Imported Papers',
      id: 'imported-papers'
    },
    {
      heading: 'Confirmed Papers',
      id: 'confirmed-papers',
    }
  ];

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });
}

function renderContent(authorNotes, directUploadNotes, tagInvitations) {

  var allNotes = _.unionBy(authorNotes, directUploadNotes, function(note){return note.id;});

  var isConfirmedImport = function(note){
    return note.details.tags && note.details.tags.length > 0 && _.includes(note.details.tags[0].tag, 'Yes');
  }

  var importedPapers = _.filter(allNotes, function(note){
    return note.invitation === IMPORTED_RECORD_ID && !isConfirmedImport(note);});

  var confirmedPapers = _.filter(allNotes, function(note){
    return note.invitation != IMPORTED_RECORD_ID || isConfirmedImport(note);});

  // importedPapers tab
  var importedPapersOptions = _.assign({}, paperDisplayOptions, {
    showTags: true,
    tagInvitations: tagInvitations,
    container: '#imported-papers'
  });

  if (importedPapers.length) {
    Webfield.ui.submissionList(importedPapers, {
      heading: null,
      container: '#imported-papers',
      displayOptions: importedPapersOptions,
      fadeIn: false
    });

    $('.tabs-container a[href="#imported-papers"]').parent().show();
  } else {
    $('.tabs-container a[href="#imported-papers"]').parent().hide();
  }

  // All Submitted Papers tab
  var confirmedPapersOptions = _.assign({}, paperDisplayOptions, {
    showTags: false,
    container: '#confirmed-papers'
  });

  $(confirmedPapersOptions.container).empty();

  if (confirmedPapers.length){
    Webfield.ui.submissionList(confirmedPapers, {
      heading: null,
      container: '#confirmed-papers',
      displayOptions: confirmedPapersOptions,
      fadeIn: false
    });

  } else {
    $('.tabs-container a[href="#confirmed-papers"]').parent().hide();
  }

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();