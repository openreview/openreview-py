from collections import defaultdict
from ..rendered_js import RenderedJS
import functions

class Webfield(RenderedJS):
  def __init__(self, user_constants = {}, loaded_vars = {}, subject_areas = []):
    super(Webfield, self).__init__(user_constants = user_constants)

    self.subject_areas = set(subject_areas)

    self.webfield_head_block = [
      'var paperDisplayOptions = {',
      '  pdfLink: true,',
      '  replyCount: true,',
      '  showContents: true',
      '};',
      'var BUFFER = 1000 * 60 * 30;  // 30 minutes',
      'var PAGE_SIZE = 50;'
    ]

    # a dict of javascript functions, keyed on function names
    # main_functions get called in main()
    self.main_functions = []
    # helper functions are just defined
    self.helper_functions = []
    self.function_definitions_block = []

    # load() makes the api calls to the server.
    self.loaded_vars = loaded_vars
    self.load_block = []

    # render() is called when all the data is finished being loaded from the server
    # It should also be called when the page needs to be refreshed, for example after a user
    # submits a new paper.
    self.render_commands = []
    self.render_block = []

    self.main_commands = []
    self.main_head = [
      '// Main is the entry point to the webfield code and runs everything',
      'function main() {',
      '  Webfield.ui.setup(\'#group-container\', CONFERENCE);  // required'
    ]

    self.main_tail = [
      '  load().then(render)',
      '  .then(function() {',
      '    Webfield.setupAutoLoading(DISPLAY_INVITATION, PAGE_SIZE, paperDisplayOptions);',
      '  });',
      '}',
      '// Go!',
      'main();'
    ]

    self.js_blocks = [
      self.webfield_head_block,
      self.constants_block,
      self.function_definitions_block,
      self.load_block,
      self.render_block,
      self.main_head,
      self.main_commands,
      self.main_tail
    ]

    self._update()

  def _update(self):
    super(Webfield, self)._update()

    sorted_subject_areas = ',\n'.join(['\'' + area + '\'' for area in sorted(list(self.subject_areas))])

    subj_string = '\n'.join([
      'var SUBJECT_AREAS = [',
      sorted_subject_areas,
      '];'
    ])

    self.constants_block.append(subj_string)

    load_args = self._update_load_block()

    self._update_render_block(load_args)

    self._update_main_block()

  def _update_load_block(self):
    load_vars_block = ['  var {0} = {1};\n'.format(varname, js) for varname, js in self.loaded_vars.iteritems()]
    load_args = sorted([varname for varname in self.loaded_vars.keys()])
    self.load_block[:] = [
      'function load(){'
    ] + load_vars_block + [
      'return $.when({load_args})'.format(load_args = ','.join(load_args)),
      '}'
    ]
    return load_args

  def _update_render_block(self, load_args):
    self.render_block[:] = [
      'function render({load_args}){{'.format(load_args = ','.join(load_args)),
    ] + self.render_commands + [
      '}'
    ]

  def _update_main_block(self):
    self.function_definitions_block[:] = []
    self.main_commands[:] = []

    for webfield_function in self.helper_functions:
      self.function_definitions_block.append(webfield_function.render())

    for webfield_function in self.main_functions:
      self.function_definitions_block.append(webfield_function.render())
      self.main_commands.append('  {function}();'.format(function=webfield_function.name))


  def add_subject_areas(self, subject_areas):
    self.subject_areas.update(subject_areas)

  def remove_subject_areas(self, subject_areas):
    # TODO
    pass

  def add_function(self, webfield_function, helper = False):
    assert issubclass(type(webfield_function), functions.WebfieldFunction)
    if not helper:
      self.main_functions.append(webfield_function)
    else:
      self.helper_functions.append(webfield_function)

  def add_loaded_var(self, varname, js):
    # TODO: add some more checks here, make sure that there aren't repeated variables
    self.loaded_vars[varname] = js

  def add_render_commands(self, render_commands):
    if type(render_commands) == list:
      self.render_commands += render_commands
    if type(render_commands) == str:
      self.render_commands.append(render_commands)

class BasicHomepage(Webfield):
  '''
  Represents a basic homepage webfield for a conference/venue.

  '''
  def __init__(self, user_constants = {}, subject_areas = []):
    super(BasicHomepage, self).__init__(user_constants = user_constants, subject_areas = subject_areas)

    self.add_function(functions.RenderConferenceHeader())

    ## alternatively, you could do:
    '''
    self.add_function(functions.WebfieldFunction('renderConferenceHeader', [
      'Webfield.ui.venueHeader({',
      '  title: TITLE,',
      '  subtitle: SUBTITLE,',
      '  location: LOCATION,',
      '  date: DATE,',
      '  website: WEBSITE,',
      '  deadline: DEADLINE,',
      '  instructions: INSTRUCTIONS',
      '});',
      'Webfield.ui.spinner(\'#notes\');'
      ]))
    '''

    self.add_loaded_var('invitation',
      'Webfield.api.getSubmissionInvitation(ENTRY_INVITATION, {deadlineBuffer: BUFFER})')

    self.add_loaded_var('notes',
      'Webfield.api.getSubmissions(DISPLAY_INVITATION, {pageSize: PAGE_SIZE})'
      )

    self.add_render_commands([
      '// Display submission button and form (if invitation is readable)',
      '$(\'#invitation\').empty();',
      'if (invitation) {',
      '  Webfield.ui.submissionButton(invitation, user, {',
      '    onNoteCreated: function() {',
      '      // Callback funtion to be run when a paper has successfully been submitted (required)',
      '      load().then(render).then(function() {',
      '        Webfield.setupAutoLoading(DISPLAY_INVITATION, PAGE_SIZE, paperDisplayOptions);',
      '      });',
      '    }',
      '  });',
      '}',
      '// Display the list of all submitted papers',
      '$(\'#notes\').empty();',
      'Webfield.ui.submissionList(notes, {',
      '  heading: \'Submitted Papers\',',
      '  displayOptions: paperDisplayOptions,',
      '  search: {',
      '    enabled: true,',
      '    subjectAreas: SUBJECT_AREAS,',
      '    onResults: function(searchResults) {',
      '      Webfield.ui.searchResults(searchResults, paperDisplayOptions);',
      '      Webfield.disableAutoLoading();',
      '    },',
      '    onReset: function() {',
      '      Webfield.ui.searchResults(notes, paperDisplayOptions);',
      '      Webfield.setupAutoLoading(DISPLAY_INVITATION, PAGE_SIZE, paperDisplayOptions);',
      '    }',
      '  }',
      '});',
      ])
