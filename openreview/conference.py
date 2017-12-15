import openreview
import builtins
from collections import namedtuple

'''
conference = openreview.Conference('auai.org/UAI/2018')

conference.add_group('Program_Chairs', members = ['~Yin_Cheng_Ng'])
conference.add_group('Senior_Program_Committee', parent = 'Program_Chairs')
conference.add_group('Program_Committee', parent = 'Senior_Program_Committee')

conference.set_recruitment('SPC_Invitation', target_group = 'Senior_Program_Committee')
conference.set_recruitment('PC_Invitation', target_group = 'Program_Committee')

'''

ConferenceGroup = namedtuple('Group', ['group', 'parent'])

recruitment_process = """
    function() {
      var or3client = lib.or3client;
      var hashKey = or3client.createHash(note.content.email, "2810398440804348173");
      if(hashKey == note.content.key) {
        if (note.content.response == 'Yes') {
          console.log("Invitation replied Yes")
          //if a user is in the declined group, remove them from that group and add them to the reviewers group
          or3client.removeGroupMember('{0}/Declined', note.content.email, token) //MODIFIED_BY_YCN: SPC->PC
          or3client.addGroupMember('{0}', note.content.email, token) //MODIFIED_BY_YCN: SPC->PC
          .then(result => done())
          .catch(error => done(error));
        } else if (note.content.response == 'No'){
          console.log("Invitation replied No")
          //if a user is in the reviewers group, remove them from that group and add them to the reviewers-declined group
          or3client.removeGroupMember('{0}', note.content.email, token) //MODIFIED_BY_YCN: SPC->PC
          or3client.addGroupMember('{0}/Declined', note.content.email, token) //MODIFIED_BY_YCN: SPC->PC
          .then(result => done())
          .catch(error => done(error));
        } else {
          done('Invalid response', note.content.response);
        }
        return true;
      } else {
        done('Invalid key', note.content.key);
        return false;
      }
    }
    """

recruitment_web = """
// Constants
var CONFERENCE_ID = '{0}';

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required
  render();
}

function render() {
  var accepted = args.response === 'Yes';
  var message = accepted ?
    'Thank you for accepting the invitation!' :
    'You have declined the invitation.';

  var $response = $('#notes');
  $response.empty().append('<div class="panel"><div class="row"><strong>' + message + '</strong></div></div>');

  if (accepted) {
    // Display response text
    $response.append([
      '<div class="panel">',
        '<div class="row">',
          '<p>If you do not already have an OpenReview account, please sign up <a href="/signup">here</a>.</p>',
          '<p>If you have an existing OpenReview account, please ensure that the email address that received this invitation is linked to your <a href="/profile?mode=edit">profile page</a> and has been confirmed.</p>',
        '</div>',
      '</div>'
    ].join('\n'));
  }
}

// Go!
main();

"""


def get_recruitment_process(target_group):
    return recruitment_process.format(target_group)

print get_recruitment_process('test')

def get_recruitment_webfield(conference_id):
    return recruitment_web.format(conference_id)

class Conference(object):
    def __init__(self, id):
        self.id = id
        self.conference_groups = {}
        self.invitations = {}

    def add_group(self, group_id, parent = None, params = None):
        full_id = self.id + '/' + group_id
        default_params = {
            'id': full_id,
            'readers': [full_id],
            'writers': [full_id],
            'signatures': [self.id],
            'signatories': [full_id],
            'members': []
        }
        params = default_params if not params else params

        def append_parent_group(params, parent_id):
            try:
                parent_group = self.conference_groups[parent_id]
            except KeyError:
                raise(KeyError('Error: parent not found {0}'.format(parent_id)))

            params['readers'] += [parent_group.group.id]

            if parent_group.parent:
                append_parent_group(params, parent_group.parent)

        if parent:
            append_parent_group(params, parent)

        conference_group = ConferenceGroup(group=openreview.Group(**params), parent=parent)
        self.conference_groups[group_id] = conference_group

    def setup_recruitment(self, invitation_id, target_group):
        default_params = {
            'id': self.id + '/-/' + invitation_id,
            'readers': ['~'],
            'writers': [self.id],
            'signatures': [self.id],
        }
        default_params['reply'] = {
            'content': {
                'email': {
                    'description': 'email address',
                    'order': 1,
                    'value-regex': '.*@.*'
                },
                'key': {
                    'description': 'Email key hash',
                    'order': 2,
                    'value-regex': '.{0,100}'
                },
                'response': {
                    'description': 'Invitation response',
                    'order': 3,
                    'value-radio': ['Yes', 'No']
                }
            },
            'readers': {
                'values': ['~Super_User1']
            },
            'signatures': {
                'values-regex': '\\(anonymous\\)'
            },
            'writers': {
                'values-regex': '\\(anonymous\\)'
            }
        }

        default_params['process'] = get_recruitment_process(target_group)
        default_params['web'] = get_recruitment_web(self.id)

        params = default_params if not params else params

        recruitment_invitation = openreview.Invitation(**params)

        self.invitations[invitation_id] = recruitment_invitation
