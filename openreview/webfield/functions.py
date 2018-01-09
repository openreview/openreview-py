from ..rendered_js import RenderedJS

class WebfieldFunction(RenderedJS):
  def __init__(self, name, args = [], function_block = []):
    super(WebfieldFunction, self).__init__()

    self.name = name
    self.args = args

    # double brackets are needed here because the RenderedJS
    # base class expects a list of code blocks. This is a
    # list consisting of a single code block (itself a list)
    self.function_block = function_block
    self.js_blocks = [self.function_block]

  def render(self):
    rendered_js = super(WebfieldFunction, self).render()
    return 'function {name}('.format(name=self.name) + ', '.join(self.args) + '){{{js}}}'.format(js=rendered_js)

class RenderConferenceHeader(WebfieldFunction):
  def __init__(self):
    super(RenderConferenceHeader, self).__init__(
      name = 'RenderConferenceHeader',
      function_block = [
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
        ]
      )

class RenderSubmissionButton(WebfieldFunction):
  def __init__(self):
    super(RenderSubmissionButton, self).__init__(
      name = 'RenderSubmissionButton',
      function_block = [
        'Webfield.api.getSubmissionInvitation(ENTRY_INVITATION, {deadlineBuffer: BUFFER})',
        '  .then(function(invitation) {',
        '    Webfield.ui.submissionButton(invitation, user, {',
        '      onNoteCreated: function() {',
        '        // Callback funtion to be run when a paper has successfully been submitted (required)',
        '        promptMessage(\'Submission successful.\');',
        '        load().then(render);',
        '      }',
        '    });',
        '  });'
        ]
      )

class WebfieldLoad(WebfieldFunction):
  def __init__(self, args = [], ):
    super(WebfieldLoad, self).__init__(
      name = 'load',
      args = args,
      function_block = function
      )
