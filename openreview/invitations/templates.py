'''
Invitation templates and tools.

Most classes extend
'''

import openreview
import content
import re
import copy

class Submission(openreview.Invitation):
    def __init__(self, name, conference_id, duedate = 0,
        process = None, inv_params = {}, reply_params = {}, content_params = {}, mask = {}):

        self.name = name
        self.conference_id = conference_id

        default_inv_params = {
            'id': '/'.join([self.conference_id, '-', self.name]),
            'readers': ['everyone'],
            'writers': [self.conference_id],
            'invitees': ['~'],
            'signatures': [self.conference_id],
            'duedate': duedate,
            'process': process
        }

        default_reply_params = {
            'forum': None,
            'replyto': None,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values': ['everyone']
            },
            'signatures': {
                'description': 'Your authorized identity to be associated with the above content.',
                'values-regex': '~.*'
            },
            'writers': {
                'values': [self.conference_id]
            }
        }

        self.content_params = {}
        self.content_params.update(content.submission)
        self.content_params.update(content_params)

        if mask:
            self.content_params = mask

        self.reply_params = {}
        self.reply_params.update(default_reply_params)
        self.reply_params.update(reply_params)
        self.reply_params['content'] = self.content_params

        self.inv_params = {}
        self.inv_params.update(default_inv_params)
        self.inv_params.update(inv_params)
        self.inv_params['reply'] = self.reply_params

        super(Submission, self).__init__(**self.inv_params)

    def add_process(self, process):
        self.process = process.render()

class AddBid(openreview.Invitation):
    def __init__(self, name, conference_id, duedate = 0,
        completion_count = 50, inv_params = {}, reply_params = {},
        content_params = {}, mask = {}):

        default_inv_params = {
            'id': conference_id + '/-/Add_Bid',
            'readers': [conference_id, conference_id + '/Reviewers'],
            'writers': [conference_id],
            'invitees': [conference_id + '/Reviewers'],
            'signatures': [conference_id],
            'duedate': duedate, # 17:00:00 EST on May 1, 2018
            'taskCompletionCount': 50,
            'multiReply': False,
        }

        default_reply_params = {
            'forum': None,
            'replyto': None,
            'invitation': conference_id + '/-/Blind_Submission',
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values-copied': [conference_id, '{signatures}']
            },
            'signatures': {
                'description': 'How your identity will be displayed with the above content.',
                'values-regex': '~.*'
            }
        }

        self.content_params = {}
        self.content_params.update(content.bid)
        self.content_params.update(content_params)

        self.reply_params = {}
        self.reply_params.update(default_reply_params)
        self.reply_params.update(reply_params)
        self.reply_params['content'] = self.content_params

        self.inv_params = {}
        self.inv_params.update(default_inv_params)
        self.inv_params.update(inv_params)
        self.inv_params['reply'] = self.reply_params

        super(AddBid, self).__init__(**self.inv_params)

class Comment(openreview.Invitation):
    def __init__(self, name, conference_id, duedate = 0,
        process = None, invitation = None, inv_params = {}, reply_params = {}, content_params = {}):

        self.name = name
        self.conference_id = conference_id

        default_inv_params = {
            'id': '/'.join([self.conference_id, '-', self.name]),
            'readers': ['everyone'],
            'writers': [self.conference_id],
            'invitees': ['~'],
            'signatures': [self.conference_id],
            'duedate': duedate,
            'process': process
        }

        default_reply_params = {
            'forum': None,
            'replyto': None,
            'invitation': invitation,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values': ['everyone']
            },
            'signatures': {
                'description': 'Your authorized identity to be associated with the above content.',
                'values-regex': '~.*'
            },
            'writers': {
                'values': [self.conference_id]
            }
        }

        self.content_params = {}
        self.content_params.update(content.comment)
        self.content_params.update(content_params)

        self.reply_params = {}
        self.reply_params.update(default_reply_params)
        self.reply_params.update(reply_params)
        self.reply_params['content'] = self.content_params

        self.inv_params = {}
        self.inv_params.update(default_inv_params)
        self.inv_params.update(inv_params)
        self.inv_params['reply'] = self.reply_params

        super(Comment, self).__init__(**self.inv_params)

    def add_process(self, process):
        self.process = process.render()

def fill_template(template_string, paper_params):
    pattern = '|'.join(['<{}>'.format(field) for field, value in paper_params.iteritems()])
    matches = re.findall(pattern, template_string)
    for match in matches:
        discovered_field = re.sub('<|>', '', match)
        template_string = template_string.replace(match, str(paper_params[discovered_field]))
        print "    new value: ", template_string
    return template_string

def generate_invitation(invitation_template, paper):
    params = copy.deepcopy(invitation_template)
    reply = params.pop('reply')
    paper_params = paper.to_json()

    def fill_list_or_str(value, paper_params=paper_params):
        if type(value) == list:
            return [fill_template(v, paper_params) for v in value]
        elif any([type(value) == t for t in [unicode, str]]):
            return fill_template(value, paper_params)
        elif any([type(value) == t for t in [int, float, type(None)]]):
            return value
        else:
            raise ValueError('first argument must be list or string: ', value)

    for field_map in [reply, params]:
        for field in field_map:
            print "field: ", field
            if field == 'content' or field == 'process' or field == 'webfield':
                pass
            elif type(field_map[field]) == dict:
                for subfield in field_map[field]:
                    if subfield != 'description':
                        field_map[field][subfield] = fill_list_or_str(field_map[field][subfield])
            else:
                field_map[field] = fill_list_or_str(field_map[field])

    return openreview.Invitation(**dict(params, **{'reply': reply}))
