'''
Standard webfield templates.

'''

class Webfield(object):
  def __init__(self, file, js_constants, group_id, subject_areas = None):
    self.js_constants = js_constants
    self.constants_block = []

    with open(file) as f:
      self.webfield_template = f.read()

    for k, v in self.js_constants.iteritems():
      if v:
        self.webfield_template = self.webfield_template.replace('//<{k}>'.format(k=k),'var {k} = \'{v}\';'.format(k=k, v=v))

    if subject_areas:
      subject_areas_string = '[' + '\n'.join('\'{area}\','.format(area=area) for area in subject_areas) + '];'
      self.webfield_template = self.webfield_template.replace('//<SUBJECT_AREAS>', 'var SUBJECT_AREAS = ' + subject_areas_string)

  def render(self):
    return self.webfield_template
