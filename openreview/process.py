from rendered_js import RenderedJS

'''
Contains code related to process functions.

Process functions are pieces of javascript code that are executed
when a note is posted to the process function's invitation.

'''

class ProcessFunction(RenderedJS):
  '''
  ProcessFunction:  base class representing a process function.

  - arguments -
  chainlinks
  user_constants

  - variables -
  js_blocks
  user_constants


  '''

  def __init__(self, user_constants = {}, chainlinks = []):
    super(ProcessFunction, self).__init__(user_constants = user_constants)

    # a list of ProcessChainLink objects
    self.chainlinks = chainlinks

    self.function_head_block = [
      'function () {',
      'var or3client = lib.or3client;',
    ]

    self.process_chain_block = []

    self.function_tail_block = [
      '.then(result => done())',
      '.catch(error => done(error));',
      'return true;',
      '};'
    ]


    self.js_blocks = [
      self.function_head_block,
      self.constants_block,
      self.process_chain_block,
      self.function_tail_block
    ]

    self._update()

  def _update(self):
    super(ProcessFunction, self)._update()

    self.process_chain_block[:] = []

    for c in self.chainlinks:
      self.process_chain_block.append(c.render())

  def insert_chainlink(self, chainlink):
    '''
    Todo: docstring
    '''
    assert issubclass(type(chainlink), ProcessChainLink)
    self.chainlinks.append(chainlink)
    self._update()

class ProcessChainLink(object):
  def __init__(self, js, head = False, input_var = 'result'):
    '''
    js:   a list of javascript instructions
    return_line:  a string representing the variable to return.
    head: if True, this chainlink is first in the chain
    '''

    self.head = head

    if self.head:
      return_line = js[-1]

      if 'return' in return_line:
          return_idx = return_line.index('return')
          return_line = return_line[(7 + return_idx):]


      if ';' in return_line:
          semicolon_idx = return_line.index(';')
          return_line = return_line[:semicolon_idx]

      self.js_block = js[:-1] + [return_line]

    else:
      self.chainlink_head = [
        '.then({input_var} => {{ console.log(JSON.stringify({input_var}));'.format(input_var = input_var)
      ]

      self.chainlink_tail = [
        '})'
      ]
      self.js_block = self.chainlink_head + js + self.chainlink_tail

  def render(self):
    return '\n'.join(self.js_block)

class NoteReceivedNotification(ProcessChainLink):
  def __init__(self, head = False):

    note_var = 'note' if head else 'result'

    ProcessChainLink.__init__(self, [
      'var authorMail = {',
      '  groups: note.content.authorids,',
      '  subject: \'Your submission to \'+ SHORT_PHRASE + \' has been received: \' + note.content.title,',
      '  message: \'Your submission to \'+ SHORT_PHRASE + \' has been posted.\\n\\nTitle: \' + note.content.title + \'\\n\\nAbstract: \' + note.content.abstract + \'\\n\\nTo view your submission, click here: \' + baseUrl + \'/forum?id=\' + {note}.forum'.format(note = note_var),
      '};',
      'return or3client.or3request(or3client.mailUrl, authorMail, \'POST\', token);',
      ],
      head = head)

class AllowRevision(ProcessChainLink):
  def __init__(self, head = False):
    ProcessChainLink.__init__(self, [
      'var revisionInvitation = {',
      '  id: CONFERENCE + \'/-/Paper\' + note.number + \'/Add/Revision\',',
      '  readers: [\'everyone\'],',
      '  writers: [CONFERENCE],',
      '  invitees: note.content[\'authorids\'],',
      '  signatures: [CONFERENCE],',
      '  duedate: invitation.duedate,',
      '  reply: {',
      '    referent: note.id,',
      '    forum: note.forum,',
      '    content: invitation.reply.content,',
      '    signatures: invitation.reply.signatures,',
      '    writers: invitation.reply.writers,',
      '    readers: invitation.reply.readers',
      '  }',
      '};',
      'return or3client.or3request(or3client.inviteUrl, revisionInvitation, \'POST\', token);',
      ],
      head = head)

class BlindSubmission(ProcessChainLink):
  def __init__(self, blind_name, head = False):
    ProcessChainLink.__init__(self, [
      'var blindSubmission = {',
      '  original: note.id,',
      '  invitation: DISPLAY_INVITATION,',
      '  forum: null,',
      '  parent: null,',
      '  signatures: [CONFERENCE],',
      '  writers: [CONFERENCE],',
      '  readers: [\'everyone\'],',
      '  content: {',
      '    authors: [\'Anonymous\'],',
      '    authorids: [\'Anonymous\'],',
      '  }',
      '};',
      'return or3client.or3request(or3client.notesUrl, blindSubmission, \'POST\', token);',
      ],
      head = head)

class SubmissionProcess(ProcessFunction):
  def __init__(self, mask = None):
    ProcessFunction.__init__(self)

    self.mask = mask

    self.insert_chainlink(AllowRevision(head = True))

    if self.mask:
      blind_submission_chainlink = BlindSubmission(blind_name = self.mask)
      self.insert_chainlink(blind_submission_chainlink)
      mail_chainlink = NoteReceivedNotification()
    else:
      mail_chainlink = NoteReceivedNotification()

    self.insert_chainlink(mail_chainlink)
