'''
class ProcessChainLink


'''

class ProcessChainLink(object):
  def __init__(self, js, head=False):
    self.head = head
    if not self.head:
      self.value = '\n'.join([
        '.then(result => {',
        '  console.log(JSON.stringify(result));',
        '  {}'.format(js),
        '})'
        ])
    else:
      self.value = js

class MailChainLink(ProcessChainLink):
  def __init__(self, short_phrase, use_result = False, head = False):
    ProcessChainLink.__init__(self, '\n'.join([
      '',
      '// start MailChainLink',
      'var notificationNote = note;' if not use_result else 'var notificationNote = result;',
      'var authorMail = {{',
      '  groups: note.content.authorids,',
      '  subject: \'Your submission to {short_phrase} has been received: \' + note.content.title,',
      '  message: \'Your submission to {short_phrase} has been posted.\\n\\nTitle: \' + note.content.title + \'\\n\\nAbstract: \' + note.content.abstract + \'\\n\\nTo view your submission, click here: \' + baseUrl + \'/forum?id=\' + notificationNote.forum',
      '}};',
      'return or3client.or3request(or3client.mailUrl, authorMail, \'POST\', token)',
      '// end MailChainLink',
      ''
      ]).format(short_phrase = short_phrase),
      head = head)

class RevisionChainLink(ProcessChainLink):
  def __init__(self, conference_id, head = False):
    ProcessChainLink.__init__(self, '\n'.join([
      '',
      '// start RevisionChainLink',
      'var revisionInvitation = {{',
      '  id: \'{conference_id}\' + \'/-/Paper\'+note.number+\'/Add/Revision\','
      '  readers: [\'everyone\'],',
      '  writers: [\'{conference_id}\'],',
      '  invitees: note.content[\'authorids\'],',
      '  signatures: [\'{conference_id}\'],',
      '  duedate: invitation.duedate,',
      '  reply: {{',
      '    referent: note.id,',
      '    forum: note.forum,',
      '    content: invitation.reply.content,',
      '    signatures: invitation.reply.signatures,',
      '    writers: invitation.reply.writers,',
      '    readers: invitation.reply.readers',
      '  }}',
      '}};',
      'return or3client.or3request(or3client.inviteUrl, revisionInvitation, \'POST\', token)',
      '// end RevisionChainLink',
      ''
      ]).format(conference_id = conference_id),
      head = head)

class BlindSubmissionChainLink(ProcessChainLink):
  def __init__(self, conference_id, blind_name, head = False):
    ProcessChainLink.__init__(self, '\n'.join([
      '',
      '// start BlindSubmissionChainLink',
      'var blindSubmission = {{',
      '  original: note.id,',
      '  invitation: \'{conference_id}/-/{blind_name}\',',
      '  forum: null,',
      '  parent: null,',
      '  signatures: [\'{conference_id}\'],',
      '  writers: [\'{conference_id}\'],',
      '  readers: [\'everyone\'],',
      '  content: {{',
      '    authors: [\'Anonymous\'],',
      '    authorids: [\'Anonymous\'],',
      '  }}',
      '}}',
      'return or3client.or3request(or3client.notesUrl, blindSubmission, \'POST\', token)',
      '// end BlindSubmissionChainLink',
      ''
      ]).format(blind_name = blind_name, conference_id = conference_id),
      head = head)

class ProcessFunction(object):
  def __init__(self):
    self.process_head = '\n'.join([
      '',
      '// start ProcessHead',
      'function () {',
      '  var or3client = lib.or3client;',
      '// end ProcessHead',
      ''
      ])

    self.process_chain = []
    self.process_tail = '\n'.join([
      '',
      '// start ProcessTail',
      '  .then(result => done())',
      '  .catch(error => done(error));',
      '  return true;',
      '};',
      '// start ProcessTail',
      ''
      ])

    self.value = None

  def update_value(self):
    self.value = self.process_head + '\n'.join(self.process_chain) + self.process_tail

  def insert_chainlink(self, chainlink):
    assert issubclass(type(chainlink), ProcessChainLink)
    self.process_chain.append(chainlink.value)
    self.update_value()

class SubmissionProcess(ProcessFunction):
  def __init__(self, short_phrase, conference_id, blind_name = None):
    ProcessFunction.__init__(self)

    revision_chainlink = RevisionChainLink(conference_id, head = True)
    self.insert_chainlink(revision_chainlink)

    if blind_name != None:
      blind_submission_chainlink = BlindSubmissionChainLink(conference_id, blind_name)
      self.insert_chainlink(blind_submission_chainlink)
      mail_chainlink = MailChainLink(short_phrase, use_result = True)
    else:
      mail_chainlink = MailChainLink(short_phrase)

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
