from collections import defaultdict

class Homepage(object):
  '''
  Represents a webfield for a conference/venue homepage.

  '''
  def __init__(self, constants = {}):
    self.js_blocks = []

    self.subject_areas = set()

    self.default_constants = [
      'var paperDisplayOptions = {',
      '  pdfLink: true,',
      '  replyCount: true,',
      '  showContents: true',
      '};',
      'var BUFFER = 1000 * 60 * 30;  // 30 minutes',
      'var PAGE_SIZE = 50;'
    ]

    self.user_constants = {
      'CONFERENCE': None,
      'ENTRY_INVITATION': None,
      'DISPLAY_INVITATION': None,
      'TITLE': None,
      'SUBTITLE': None,
      'LOCATION': None,
      'DATE': None,
      'WEBSITE': None,
      'DEADLINE': None,
      'INSTRUCTIONS': None
    }

    if constants:
      for k, v in constants.iteritems():
        self.user_constants[k] = v

    self.constants_block = []
    self.js_blocks.append(self.constants_block)

    self.main_block = [
      '// Main is the entry point to the webfield code and runs everything',
      'function main() {',
      '  Webfield.ui.setup(\'#group-container\', CONFERENCE);  // required',
      '  renderConferenceHeader();',
      '  load().then(render).then(function() {',
      '    Webfield.setupAutoLoading(DISPLAY_INVITATION, PAGE_SIZE, paperDisplayOptions);',
      '  });',
      '}'
      ]

    self.js_blocks.append(self.main_block)

    self.header_block = [
      '// RenderConferenceHeader renders the static info at the top of the page. Since that content',
      '// never changes, put it in its own function',
      'function renderConferenceHeader() {',
      '  Webfield.ui.venueHeader({',
      '    title: TITLE,',
      '    subtitle: SUBTITLE,',
      '    location: LOCATION,',
      '    date: DATE,',
      '    website: WEBSITE,',
      '    deadline: DEADLINE,',
      '    instructions: INSTRUCTIONS',
      '  });',
      '  Webfield.ui.spinner(\'#notes\');'
      '}'
      ]

    self.js_blocks.append(self.header_block)

    self.load_block = [
      '// Load makes all the API calls needed to get the data to render the page',
      '// It returns a jQuery deferred object: https://api.jquery.com/category/deferred-object/',
      'function load() {',
      '  var invitationP = Webfield.api.getSubmissionInvitation(ENTRY_INVITATION, {deadlineBuffer: BUFFER});',
      '  var notesP = Webfield.api.getSubmissions(DISPLAY_INVITATION, {pageSize: PAGE_SIZE});',
      '  return $.when(invitationP, notesP);',
      '}'
      ]

    self.js_blocks.append(self.load_block)

    self.render_block = [
      '// Render is called when all the data is finished being loaded from the server',
      '// It should also be called when the page needs to be refreshed, for example after a user',
      '// submits a new paper.',
      ''
      'function render(invitation, notes) {',
      '  // Display submission button and form (if invitation is readable)',
      '  $(\'#invitation\').empty();',
      '  if (invitation) {',
      '    Webfield.ui.submissionButton(invitation, user, {',
      '      onNoteCreated: function() {',
      '        // Callback funtion to be run when a paper has successfully been submitted (required)',
      '        load().then(render).then(function() {',
      '          Webfield.setupAutoLoading(DISPLAY_INVITATION, PAGE_SIZE, paperDisplayOptions);',
      '        });',
      '      }',
      '    });',
      '  }',
      '',
      '  // Display the list of all submitted papers',
      '  $(\'#notes\').empty();',
      '  Webfield.ui.submissionList(notes, {',
      '    heading: \'Submitted Papers\',',
      '    displayOptions: paperDisplayOptions,',
      '    search: {',
      '      enabled: true,',
      '      subjectAreas: SUBJECT_AREAS,',
      '      onResults: function(searchResults) {',
      '        Webfield.ui.searchResults(searchResults, paperDisplayOptions);',
      '        Webfield.disableAutoLoading();',
      '      },',
      '      onReset: function() {',
      '        Webfield.ui.searchResults(notes, paperDisplayOptions);',
      '        Webfield.setupAutoLoading(DISPLAY_INVITATION, PAGE_SIZE, paperDisplayOptions);',
      '      }',
      '    }',
      '  });',
      '}',
      ''
      '// Go!',
      'main();'
      ]

    self.js_blocks.append(self.render_block)

  def update_constants(self):
    self.constants_block[:] = []

    for c in self.default_constants:
      self.constants_block.append(c)

    for k, v in self.user_constants.iteritems():
      if v:
        self.constants_block.append('var {k} = \'{v}\';'.format(k=k, v=v))

    sorted_subject_areas = '\n'.join(sorted(list(self.subject_areas)))

    subj_string = '\n'.join([
      'var SUBJECT_AREAS = [',
      sorted_subject_areas,
      '];'
    ])

    self.constants_block.append(subj_string)

  def render(self):
    self.update_constants()
    rendered_js = '\n'.join(['\n'.join(instruction_list) for instruction_list in self.js_blocks])
    return rendered_js

  def add_subject_areas(self, subject_areas):
    self.subject_areas.update(subject_areas)

  def remove_subject_areas(self, subject_areas):
    # TODO
    pass



recruitment_web = """
// Constants
var CONFERENCE_ID = '{0}';

// Main is the entry point to the webfield code and runs everything
function main() {{
  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required
  render();
}}

function render() {{
  var accepted = args.response === 'Yes';
  var message = accepted ?
    'Thank you for accepting the invitation!' :
    'You have declined the invitation.';

  var $response = $('#notes');
  $response.empty().append('<div class="panel"><div class="row"><strong>' + message + '</strong></div></div>');

  if (accepted) {{
    // Display response text
    $response.append([
      '<div class="panel">',
        '<div class="row">',
          '<p>If you do not already have an OpenReview account, please sign up <a href="/signup">here</a>.</p>',
          '<p>If you have an existing OpenReview account, please ensure that the email address that received this invitation is linked to your <a href="/profile?mode=edit">profile page</a> and has been confirmed.</p>',
        '</div>',
      '</div>'
    ].join('\n'));
  }}
}}

// Go!
main();

"""
