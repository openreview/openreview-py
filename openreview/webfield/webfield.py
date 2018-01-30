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

class TabbedHomepage(object):

  def __init__(self, js_constants, group_id):

    self.js_constants = js_constants

    self.constants_block =[
      'var SUBJECT_AREAS_LIST = [];',
      'var BUFFER = 1000 * 60 * 30;  // 30 minutes',
      'var PAGE_SIZE = 50;',
      'var paperDisplayOptions = {',
      '  pdfLink: true,',
      '  replyCount: true,',
      '  showContents: true',
      '};',

      'var commentDisplayOptions = {',
      '  pdfLink: false,',
      '  replyCount: true,',
      '  showContents: false,',
      '  showParent: true',
      '};',

      'var initialPageLoad = true;'
      ]

    for k, v in self.js_constants.iteritems():
      if v:
        self.constants_block.append('var {k} = \'{v}\';'.format(k=k, v=v))

    self.constants_block += [
      'var CONFERENCE_REGEX = CONFERENCE.replace(\'.\', \'\\\\.\').replace(\'/\',\'\\\\/\')',
      'var WILDCARD_INVITATION = CONFERENCE + \'/-/.*\';'
      ]

    self.instructions = self.constants_block + [
      '// Main is the entry point to the webfield code and runs everything',
      'function main() {',
      '  Webfield.ui.setup(\'#group-container\', CONFERENCE);  // required',
      '  renderConferenceHeader();',
      '  renderSubmissionButton();',
      '  renderConferenceTabs();',
      '  load().then(renderContent);',
      '}',
      '',
      '// Load makes all the API calls needed to get the data to render the page',
      '// It returns a jQuery deferred object: https://api.jquery.com/category/deferred-object/',
      'function load() {',
      '  var notesP = Webfield.api.getSubmissions(BLIND_INVITATION, {',
      '    pageSize: PAGE_SIZE',
      '  });',
      '',
      '  var submittedNotesP = Webfield.api.getSubmissions(WILDCARD_INVITATION, {',
      '    pageSize: PAGE_SIZE,',
      '    tauthor: true',
      '  });',
      '',
      '  var assignedNotePairsP = Webfield.api.getSubmissions(WILDCARD_INVITATION, {',
      '    pageSize: 100,',
      '    invitee: true,',
      '    duedate: true',
      '  });',
      '',
      '  var userGroupsP;',
      '  var authorNotesP;',
      '  if (!user || _.startsWith(user.id, \'guest_\')) {',
      '    userGroupsP = $.Deferred().resolve([]);',
      '    authorNotesP = $.Deferred().resolve([]);',
      '',
      '  } else {',
      '    userGroupsP = Webfield.get(\'/groups\', {member: user.id}).then(function(result) {',
      '      return _.filter(',
      '        _.map(result.groups, function(g) { return g.id; }),',
      '        function(id) { return _.startsWith(id, CONFERENCE); }',
      '      );',
      '    });',
      '',
      '    authorNotesP = Webfield.get(\'/notes/search\', {',
      '      term: user.profile.id,',
      '      group: CONFERENCE,',
      '      content: \'authors\',',
      '      source: \'forum\'',
      '    }).then(function(result) {',
      '      return result.notes;',
      '    });',
      '  }',
      '',
      '  var tagInvitationsP = Webfield.api.getTagInvitations(BLIND_INVITATION);',
      '',
      '  return userGroupsP',
      '  .then(function(userGroups) {',
      '',
      '    var assignedPaperNumbers = getPaperNumbersfromGroups(userGroups);',
      '    var assignedNotesP = $.Deferred().resolve([]);',
      '',
      '    if (assignedPaperNumbers.length) {',
      '        assignedNotesP = Webfield.api.getSubmissions(BLIND_INVITATION, {',
      '        pageSize: PAGE_SIZE,',
      '        number: assignedPaperNumbers.join()',
      '      });',
      '    }',
      '',
      '    return $.when(',
      '      notesP, submittedNotesP, assignedNotePairsP, assignedNotesP, userGroups,',
      '      authorNotesP, tagInvitationsP',
      '    );',
      '  });',
      '',
      '}',
      '',
      '',
      '// Render functions',
      'function renderConferenceHeader() {',
      '  Webfield.ui.venueHeader({',
      '    title: TITLE,',
      '    subtitle: SUBTITLE,',
      '    location: LOCATION,',
      '    date: DATE,',
      '    website: WEBSITE,',
      '    instructions: INSTRUCTIONS,',
      '    deadline: DEADLINE',
      '  });',
      '',
      '  Webfield.ui.spinner(\'#notes\');',
      '}',
      '',
      'function renderSubmissionButton() {',
      '  Webfield.api.getSubmissionInvitation(SUBMISSION_INVITATION, {deadlineBuffer: BUFFER})',
      '    .then(function(invitation) {',
      '      Webfield.ui.submissionButton(invitation, user, {',
      '        onNoteCreated: function() {',
      '          // Callback funtion to be run when a paper has successfully been submitted (required)',
      '          promptMessage(\'Your submission to \' + TITLE + \' is complete. The list of all current submissions is shown below.\');',
      '',
      '          load().then(renderContent).then(function() {',
      '            $(\'.tabs-container a[href="#all-submitted-papers"]\').click();',
      '          });',
      '        }',
      '      });',
      '    });',
      '}',
      '',
      'function renderConferenceTabs() {',
      '  var sections = [',
      '    {',
      '      heading: \'All Submitted Papers\',',
      '      id: \'all-submitted-papers\',',
      '    },',
      '    {',
      '      heading: \'My Tasks\',',
      '      id: \'my-tasks\',',
      '    },',
      '    {',
      '      heading: \'My Submitted Papers\',',
      '      id: \'my-submitted-papers\',',
      '    },',
      '    {',
      '      heading: \'My Assigned Papers\',',
      '      id: \'my-assigned-papers\',',
      '    },',
      '    {',
      '      heading: \'My Comments & Reviews\',',
      '      id: \'my-comments-reviews\',',
      '    },',
      '  ];',
      '',
      '  Webfield.ui.tabPanel(sections, {',
      '    container: \'#notes\',',
      '    hidden: true',
      '  });',
      '}',
      '',
      'function renderContent(notes, submittedNotes, assignedNotePairs, assignedNotes, userGroups, authorNotes, tagInvitations) {',
      '  var data, commentNotes;',
      '',
      '  // if (_.isEmpty(userGroups)) {',
      '  //   // If the user isn\'t part of the conference don\'t render tabs',
      '  //   $(\'.tabs-container\').hide();',
      '  //   return;',
      '  // }',
      '',
      '  commentNotes = [];',
      '  _.forEach(submittedNotes, function(note) {',
      '    if (!_.isNil(note.ddate)) {',
      '      return;',
      '    }',
      '    if (!_.includes([SUBMISSION_INVITATION, RECRUIT_REVIEWERS], note.invitation)) {',
      '      commentNotes.push(note);',
      '    }',
      '  });',
      '',
      '  // Filter out all tags that belong to other users (important for bid tags)',
      '  notes = _.map(notes, function(n) {',
      '    n.tags = _.filter(n.tags, function(t) {',
      '      return !_.includes(t.signatures, user.id);',
      '    });',
      '    return n;',
      '  });',
      '',
      '  var assignedPaperNumbers = getPaperNumbersfromGroups(userGroups);',
      '  if (assignedPaperNumbers.length !== assignedNotes.length) {',
      '    console.warn(\'WARNING: The number of assigned notes returned by API does not \' +',
      '      \'match the number of assigned note groups the user is a member of.\');',
      '  }',
      '',
      '  var authorPaperNumbers = getAuthorPaperNumbersfromGroups(userGroups);',
      '  if (authorPaperNumbers.length !== authorNotes.length) {',
      '    console.warn(\'WARNING: The number of submitted notes returned by API does not \' +',
      '      \'match the number of submitted note groups the user is a member of.\');',
      '  }',
      '',
      '  // My Tasks tab',
      '  if (userGroups.length) {',
      '    var tasksOptions = {',
      '      container: \'#my-tasks\',',
      '      emptyMessage: \'No outstanding tasks for \' + TITLE',
      '    }',
      '    Webfield.ui.taskList(assignedNotePairs, tagInvitations, tasksOptions)',
      '  } else {',
      '    $(\'.tabs-container a[href="#my-tasks"]\').parent().hide();',
      '  }',
      '',
      '  // All Submitted Papers tab',
      '  var submissionListOptions = _.assign({}, paperDisplayOptions, {',
      '    showTags: true,',
      '    tagInvitations: tagInvitations,',
      '    container: \'#all-submitted-papers\'',
      '  });',
      '',
      '  Webfield.ui.submissionList(notes, {',
      '    heading: null,',
      '    container: \'#all-submitted-papers\',',
      '    search: {',
      '      enabled: true,',
      '      subjectAreas: SUBJECT_AREAS_LIST,',
      '      onResults: function(searchResults) {',
      '        var blindedSearchResults = searchResults.filter(function(note) {',
      '          return note.invitation === BLIND_INVITATION;',
      '        });',
      '        Webfield.ui.searchResults(blindedSearchResults, submissionListOptions);',
      '        Webfield.disableAutoLoading();',
      '      },',
      '      onReset: function() {',
      '        Webfield.ui.searchResults(notes, submissionListOptions);',
      '        if (notes.length === PAGE_SIZE) {',
      '          Webfield.setupAutoLoading(BLIND_INVITATION, PAGE_SIZE, submissionListOptions);',
      '        }',
      '      }',
      '    },',
      '    displayOptions: submissionListOptions,',
      '    fadeIn: false',
      '  });',
      '',
      '  if (notes.length === PAGE_SIZE) {',
      '    Webfield.setupAutoLoading(BLIND_INVITATION, PAGE_SIZE, submissionListOptions);',
      '  }',
      '',
      '  // My Submitted Papers tab',
      '  if (authorNotes.length) {',
      '    Webfield.ui.searchResults(',
      '      authorNotes,',
      '      _.assign({}, paperDisplayOptions, {container: \'#my-submitted-papers\'})',
      '    );',
      '  } else {',
      '    $(\'.tabs-container a[href="#my-submitted-papers"]\').parent().hide();',
      '  }',
      '',
      '  // My Assigned Papers tab (only show if not empty)',
      '  if (assignedNotes.length) {',
      '    Webfield.ui.searchResults(',
      '      assignedNotes,',
      '      _.assign({}, paperDisplayOptions, {container: \'#my-assigned-papers\'})',
      '    );',
      '  } else {',
      '    $(\'.tabs-container a[href="#my-assigned-papers"]\').parent().hide();',
      '  }',
      '',
      '  // My Comments & Reviews tab (only show if not empty)',
      '  if (commentNotes.length) {',
      '    Webfield.ui.searchResults(',
      '      commentNotes,',
      '      _.assign({}, commentDisplayOptions, {',
      '        container: \'#my-comments-reviews\',',
      '        emptyMessage: \'No comments or reviews to display\'',
      '      })',
      '    );',
      '  } else {',
      '    $(\'.tabs-container a[href="#my-comments-reviews"]\').parent().hide();',
      '  }',
      '',
      '  $(\'#notes .spinner-container\').remove();',
      '  $(\'.tabs-container\').show();',
      '',
      '  // Show first available tab',
      '  if (initialPageLoad) {',
      '    $(\'.tabs-container ul.nav-tabs li a:visible\').eq(0).click();',
      '    initialPageLoad = false;',
      '  }',
      '}',
      '',
      '// Helper functions',
      'function getPaperNumbersfromGroups(groups) {',
      '  var re = new RegExp(\'^\' + CONFERENCE_REGEX + \'\/Paper([0-9]+)\/(AnonReviewer[0-9]+|Area_Chair)\');',
      '  return _.map(',
      '    _.filter(groups, function(gid) { return re.test(gid); }),',
      '    function(fgid) { return parseInt(fgid.match(re)[1], 10); }',
      '  );',
      '}',
      '',
      'function getAuthorPaperNumbersfromGroups(groups) {',
      '  var re = new RegExp(\'^\' + CONFERENCE_REGEX + \'\/Paper(\d+)\/Authors\');',
      '  return _.map(',
      '    _.filter(groups, function(gid) { return re.test(gid); }),',
      '    function(fgid) { return parseInt(fgid.match(re)[1], 10); }',
      '  );',
      '}',
      '',
      'function getDueDateStatus(date) {',
      '  var day = 24 * 60 * 60 * 1000;',
      '  var diff = Date.now() - date.getTime();',
      '',
      '  if (diff > 0) {',
      '    return \'expired\';',
      '  }',
      '  if (diff > -3 * day) {',
      '    return \'warning\';',
      '  }',
      '  return '';',
      '}',
      '',
      '// Go!',
      'main();',

    ]

  def render(self):
    return '\n'.join(self.instructions)
