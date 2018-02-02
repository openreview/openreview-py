'''
Process function templates.

Process functions are pieces of javascript code that are executed
when a note is posted to the process function's invitation.

'''

class MaskSubmissionProcess(object):
  def __init__(self, file, js_constants, mask):
    self.js_constants = js_constants
    self.constants_block = []

    with open(file) as f:
      self.process_template = f.read()

    for k, v in self.js_constants.iteritems():
      if v:
        self.process_template = self.process_template.replace('//<{k}>'.format(k=k),'var {k} = \'{v}\';'.format(k=k, v=v))

  def render(self):
    return self.process_template

