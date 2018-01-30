'''
Process function templates.

Process functions are pieces of javascript code that are executed
when a note is posted to the process function's invitation.

'''

class MaskSubmissionProcess(object):
  def __init__(self, js_constants, mask):
    self.js_constants = js_constants
    self.constants_block = []

    for k, v in self.js_constants.iteritems():
      if v:
        self.constants_block.append('var {k} = \'{v}\';'.format(k=k, v=v))

    reply_reader_values = [v for k,v in mask.reply['readers'].iteritems() if 'value' in k]
    assert len(reply_reader_values) == 1, 'Too many values in reply readers: ' + reply_reader_values

    reply_reader_strings = ['\'{}\''.format(v) for v in reply_reader_values[0]]

    reply_readers = '[' + ',\n'.join(reply_reader_strings) + ']'

    self.instructions = [
      'function () {',
      '  var or3client = lib.or3client;'] + self.constants_block + [
      '  var revisionInvitation = {',
      '    id: CONFERENCE + \'/-/Paper\' + note.number + \'/Add_Revision\',',
      '    readers: [\'everyone\'],',
      '    writers: [CONFERENCE],',
      '    invitees: note.content[\'authorids\'],',
      '    signatures: [CONFERENCE],',
      '    duedate: invitation.duedate,',
      '    reply: {',
      '      referent: note.id,',
      '      forum: note.forum,',
      '      content: invitation.reply.content,',
      '      signatures: invitation.reply.signatures,',
      '      writers: invitation.reply.writers,',
      '      readers: invitation.reply.readers',
      '    }',
      '  };',

      '  or3client.or3request(or3client.inviteUrl, revisionInvitation, \'POST\', token)',
      '  .then(result => { console.log(JSON.stringify(result));',
      '    var blindSubmission = {',
      '      original: note.id,',
      '      invitation: \'{mask_id}\','.format(mask_id = mask.id),
      '      forum: null,',
      '      parent: null,',
      '      signatures: [CONFERENCE],',
      '      writers: [CONFERENCE],',
      '      readers: {reply_readers},'.format(reply_readers = reply_readers),
      '      content: {',
      '        authors: [\'Anonymous\'],',
      '        authorids: [CONFERENCE + \'/Paper\' + note.number + \'/Authors\'],',
      '      }',
      '    };',
      '    return or3client.or3request(or3client.notesUrl, blindSubmission, \'POST\', token);',
      '  })',
      '  .then(result => { console.log(JSON.stringify(result));',
      '    var authorMail = {',
      '      groups: note.content.authorids,',
      '      subject: \'Your submission to \'+ TITLE + \' has been received: \' + note.content.title,',
      '      message: \'Your submission to \'+ TITLE + \' has been posted.\\n\\nTitle: \' + note.content.title + \'\\n\\nAbstract: \' + note.content.abstract + \'\\n\\nTo view your submission, click here: \' + baseUrl + \'/forum?id=\' + result.forum',
      '    };',
      '    return or3client.or3request(or3client.mailUrl, authorMail, \'POST\', token);',
      '  })',
      '  .then(result => done())',
      '  .catch(error => done(error));',
      '  return true;',
      '};'
    ]

  def render(self):
    return '\n'.join(self.instructions)

