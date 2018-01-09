'''

Base class for rendered javascript code.

Webfield and Process classes extend RenderedJS

'''

class RenderedJS(object):

  def __init__(self, user_constants = {}):
    self.user_constants = user_constants
    self.js_blocks = []

    self.constants_block = []

  def _update(self):
    self.constants_block[:] = []

    for k, v in self.user_constants.iteritems():
      if v:
        self.constants_block.append('var {k} = \'{v}\';'.format(k=k, v=v))

  def render(self):
    self._update()
    rendered_js = '\n'.join(['\n'.join(instruction_list) for instruction_list in self.js_blocks])
    return rendered_js

  def update_variables(self, variables):
    '''
    variables:  a dict of variable names and values.
    '''
    self.user_constants.update(variables)

  def remove_variables(self, variable_names):
    '''
    variable_names: a list of variable names.
    '''
    for k in variable_names:
      self.user_constants.pop(k)
