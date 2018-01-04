class ProcessFunction(object):
  '''
  Represents a process function for an invitation.

  '''
  def __init__(self, constants = {}):

    self.js_blocks = []

    self.default_constants = [
      'var or3client = lib.or3client;',
    ]

    self.user_constants = {
      'CONFERENCE': None,
      'ENTRY_INVITATION': None,
      'DISPLAY_INVITATION': None,
      'SHORT_PHRASE': None
    }

    if constants:
      for k, v in constants.iteritems():
        self.user_constants[k] = v

    self.function_head_block = [
      'function () {'
    ]
    self.js_blocks.append(self.function_head_block)

    self.constants_block = []
    self.js_blocks.append(self.constants_block)

    self.chainlinks = [] #list of chainlinks
    self.process_chain_block = [] # list of instructions, built from the process chain
    self.js_blocks.append(self.process_chain_block)
    self.function_tail_block = [
      '.then(result => done())',
      '.catch(error => done(error));',
      'return true;',
      '};'
    ]
    self.js_blocks.append(self.function_tail_block)

  def update_constants(self):
    self.constants_block[:] = []

    for c in self.default_constants:
      self.constants_block.append(c)

    for k, v in self.user_constants.iteritems():
      if v:
        self.constants_block.append('var {k} = \'{v}\';'.format(k=k, v=v))

  def update_process_chain(self):
    self.process_chain_block[:] = []

    for c in self.chainlinks:
      self.process_chain_block.append(c.render())

  def render(self):
    self.update_constants()
    self.update_process_chain()
    rendered_js = '\n'.join(['\n'.join(instruction_list) for instruction_list in self.js_blocks])
    return rendered_js

  def insert_chainlink(self, chainlink):
    assert issubclass(type(chainlink), ProcessChainLink)
    self.chainlinks.append(chainlink)
    self.update_process_chain()

class ProcessChainLink(object):
  def __init__(self, js, input_var = 'result', return_line = None, head = False):
    '''
    js:   a list of javascript instructions
    head: if True, this chainlink is first in the chain
    '''

    self.head = head
    if not self.head:

      self.chainlink_head = [
        '.then({result} => {{ console.log(JSON.stringify({result}));'.format(result = input_var)
      ]

      self.chainlink_tail = [
        'return {instructions};'.format(instructions = return_line),
        '})'
      ]
      self.js_block = self.chainlink_head + js + self.chainlink_tail
    else:
      if return_line[-1] == ';':
        return_line = return_line[:-1]
      self.js_block = js + [return_line]

  def render(self):
    return '\n'.join(self.js_block)

class MailChainLink(ProcessChainLink):
  def __init__(self, head = False):
    note_var = 'note' if head else 'result'
    ProcessChainLink.__init__(self, [
      'var authorMail = {',
      '  groups: note.content.authorids,',
      '  subject: \'Your submission to \'+ SHORT_PHRASE + \' has been received: \' + note.content.title,',
      '  message: \'Your submission to \'+ SHORT_PHRASE + \' has been posted.\\n\\nTitle: \' + note.content.title + \'\\n\\nAbstract: \' + note.content.abstract + \'\\n\\nTo view your submission, click here: \' + baseUrl + \'/forum?id=\' + {note}.forum'.format(note = note_var),
      '};'
      ],
      return_line = 'or3client.or3request(or3client.mailUrl, authorMail, \'POST\', token)',
      head = head)

class RevisionChainLink(ProcessChainLink):
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
      '};'
      ],
      return_line = 'or3client.or3request(or3client.inviteUrl, revisionInvitation, \'POST\', token)',
      head = head)

class BlindSubmissionChainLink(ProcessChainLink):
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
      '};'
      ],
      return_line = 'or3client.or3request(or3client.notesUrl, blindSubmission, \'POST\', token)',
      head = head)

class SubmissionProcess(ProcessFunction):
  def __init__(self, mask = None):
    ProcessFunction.__init__(self)

    self.mask = mask

    revision_chainlink = RevisionChainLink(head = True)
    self.insert_chainlink(revision_chainlink)

    if self.mask:
      blind_submission_chainlink = BlindSubmissionChainLink(blind_name = self.mask)
      self.insert_chainlink(blind_submission_chainlink)
      mail_chainlink = MailChainLink()
    else:
      mail_chainlink = MailChainLink()

    self.insert_chainlink(mail_chainlink)







# TODO: Add bibtex to the open submission process
open_submission_process = """
function() {{
  // email authors, create revision, withdraw and comment invites
  // create blind submission and author group
  var or3client = lib.or3client;

  var CONF = {CONF};
  var PROGRAM_CHAIRS = CONF + '/Program_Chairs';
  var AREA_CHAIRS = CONF + '/Area_Chairs';
  var REVIEWERS = CONF + '/Reviewers';
  var AUTHORS = CONF + '/Authors';
  var REVIEWERS_PLUS = REVIEWERS + '_and_Higher';
  var AREA_CHAIRS_PLUS = AREA_CHAIRS + '_and_Higher';

  var addRevisionInvitation = {{
    id: CONF + '/-/Paper' + note.number + '/Add_Revision',
    signatures: [CONF],
    writers: [CONF],
    invitees: note.content.authorids.concat(note.signatures),
    noninvitees: [],
    readers: ['everyone'],
    reply: {{
      forum: note.id,
      referent: note.id,
      signatures: invitation.reply.signatures,
      writers: invitation.reply.writers,
      readers: invitation.reply.readers,
      content: invitation.reply.content
    }}
  }}


  or3client.or3request(or3client.inviteUrl, addRevisionInvitation, 'POST', token)
  .then(result => {{
    //Send an email to the author of the submitted note, confirming its receipt
    var mail = {{
        "groups": note.content.authorids,
        "subject": "Confirmation of your submission to {SHORT_PHRASE}: \"" + note.content.title + "\".",
        "message": `Your submission to {SHORT_PHRASE} has been posted.\n\nTitle: `+note.content.title+`\n\nAbstract: `+note.content.abstract+`\n\nTo view the note, click here: `+baseUrl+`/forum?id=` + note.forum
    }};

    var paperGroup = {{
      id: CONF + '/Paper' + note.number,
      signatures: [CONF],
      writers: [CONF],
      members: [],
      readers: [CONF],
      signatories: []
    }};
    return or3client.or3request(or3client.grpUrl, paperGroup, 'POST', token)
    .then(savedPaperGroup => {{

      var reviewerGroupId = savedPaperGroup.id + '/Reviewers';
      var areachairGroupId = savedPaperGroup.id + '/Area_Chair';

      var authorGroupId = savedPaperGroup.id + '/Authors';
      var authorGroup = {{
        id: authorGroupId,
        signatures: [CONF],
        writers: [CONF],
        members: note.content.authorids.concat(note.signatures),
        readers: [CONF, PROGRAM_CHAIRS, authorGroupId],
        signatories: [authorGroupId]
      }};

      var withdrawPaperInvitation = {{
        id: CONF + '/-/Paper' + note.number + '/Withdraw_Paper',
        signatures: [CONF],
        writers: [CONF],
        invitees: [authorGroupId],
        noninvitees: [],
        readers: ['everyone'],
        process: withdrawProcess,
        reply: {{
          forum: note.id,
          referent: note.id,
          signatures: invitation.reply.signatures,
          writers: invitation.reply.writers,
          readers: invitation.reply.readers,
          content: {{
            withdrawal: {{
              description: 'Confirm your withdrawal. The blind record of your paper will be deleted. Your identity will NOT be revealed. This cannot be undone.',
              order: 1,
              'value-radio': ['Confirmed'],
              required: true
            }}
          }}
        }}
      }}

      var publicCommentInvitation = {{
        id: CONF + '/-/Paper' + note.number + '/Public_Comment',
        signatures: [CONF],
        writers: [CONF],
        invitees: ['~'],
        noninvitees: [authorGroupId, reviewerGroupId, areachairGroupId],
        readers: ['everyone'],
        reply: {{
          forum: note.id,
          replyto: null,
          readers: {{
            description: 'The users who will be allowed to read the above content.',
            'value-dropdown': ['everyone', REVIEWERS_PLUS, AREA_CHAIRS_PLUS, PROGRAM_CHAIRS]
          }},
          signatures: {{
            description: 'How your identity will be displayed with the above content.',
            'values-regex': '~.*|\\\\(anonymous\\\\)'
          }},
          writers: {{
            'values-regex': '~.*|\\\\(anonymous\\\\)'
          }},
          content:{{
            title: {{
              order: 0,
              'value-regex': '.{{1,500}}',
              description: 'Brief summary of your comment.',
              required: true
            }},
            comment: {{
              order: 1,
              'value-regex': '[\\\\S\\\\s]{{1,5000}}',
              description: 'Your comment or reply.',
              required: true
            }}
          }}
        }}
      }}

      var officialCommentInvitation = {{
        id: CONF + '/-/Paper' + note.number + '/Official_Comment',
        signatures: [CONF],
        writers: [CONF],
        invitees: [reviewerGroupId, authorGroupId, areachairGroupId, PROGRAM_CHAIRS],
        readers: ['everyone'],
        reply: {{
          forum: note.id,
          replyto: null,
          readers: {{
            description: 'The users who will be allowed to read the above content.',
            'value-dropdown': ['everyone', REVIEWERS_PLUS, AREA_CHAIRS_PLUS, PROGRAM_CHAIRS]
          }},
          signatures: {{
            description: 'How your identity will be displayed with the above content.',
            'values-regex': [reviewerGroupId, authorGroupId, areachairGroupId, PROGRAM_CHAIRS].join('|')
          }},
          writers: {{
            'values-regex': [reviewerGroupId, authorGroupId, areachairGroupId, PROGRAM_CHAIRS].join('|')
          }},
          content:{{
            title: {{
              order: 0,
              'value-regex': '.{{1,500}}',
              description: 'Brief summary of your comment.',
              required: true
            }},
            comment: {{
              order: 1,
              'value-regex': '[\\\\S\\\\s]{{1,5000}}',
              description: 'Your comment or reply.',
              required: true
            }}
          }}
        }}
      }}

      var batchPromises = Promise.all([
        or3client.or3request(or3client.grpUrl, authorGroup, 'POST', token),
        or3client.or3request(or3client.inviteUrl, withdrawPaperInvitation, 'POST', token),
        or3client.or3request(or3client.inviteUrl, publicCommentInvitation, 'POST', token),
        or3client.or3request(or3client.inviteUrl, officialCommentInvitation, 'POST', token),
        or3client.or3request(or3client.mailUrl, mail, 'POST', token)
      ]);

      return batchPromises
    }});
  }})
  .then(result => done())
  .catch(error => done(error));

  return true;
}}
"""



recruitment_process = """
function() {{
  var or3client = lib.or3client;
  var hashKey = or3client.createHash(note.content.email, "2810398440804348173");
  if(hashKey == note.content.key) {{
    if (note.content.response == 'Yes') {{
      console.log("Invitation replied Yes")
      //if a user is in the declined group, remove them from that group and add them to the reviewers group
      or3client.removeGroupMember('{0}/Declined', note.content.email, token) //MODIFIED_BY_YCN: SPC->PC
      or3client.addGroupMember('{0}', note.content.email, token) //MODIFIED_BY_YCN: SPC->PC
      .then(result => done())
      .catch(error => done(error));
    }} else if (note.content.response == 'No'){{
      console.log("Invitation replied No")
      //if a user is in the reviewers group, remove them from that group and add them to the reviewers-declined group
      or3client.removeGroupMember('{0}', note.content.email, token) //MODIFIED_BY_YCN: SPC->PC
      or3client.addGroupMember('{0}/Declined', note.content.email, token) //MODIFIED_BY_YCN: SPC->PC
      .then(result => done())
      .catch(error => done(error));
    }} else {{
      done('Invalid response', note.content.response);
    }}
    return true;
  }} else {{
    done('Invalid key', note.content.key);
    return false;
  }}
}}
"""
