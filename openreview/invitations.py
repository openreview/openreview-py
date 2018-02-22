'''
Invitation templates and tools.

Most classes extend
'''

import openreview

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

        default_content_params = {
            'title': {
                'description': 'Title of paper.',
                'order': 1,
                'value-regex': '.{1,250}',
                'required':True
            },
            'authors': {
                'description': 'Comma separated list of author names. Please provide real names; identities will be anonymized.',
                'order': 2,
                'values-regex': "[^;,\\n]+(,[^,\\n]+)*",
                'required':True
            },
            'authorids': {
                'description': 'Comma separated list of author email addresses, lowercased, in the same order as above. For authors with existing OpenReview accounts, please make sure that the provided email address(es) match those listed in the author\'s profile. Please provide real emails; identities will be anonymized.',
                'order': 3,
                'values-regex': "([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})",
                'required':True
            },
            'keywords': {
                'description': 'Comma separated list of keywords.',
                'order': 6,
                'values-regex': "(^$)|[^;,\\n]+(,[^,\\n]+)*"
            },
            'TL;DR': {
                'description': '\"Too Long; Didn\'t Read\": a short sentence describing your paper',
                'order': 7,
                'value-regex': '[^\\n]{0,250}',
                'required':False
            },
            'abstract': {
                'description': 'Abstract of paper.',
                'order': 8,
                'value-regex': '[\\S\\s]{1,5000}',
                'required':True
            },
            'pdf': {
                'description': 'Upload a PDF file that ends with .pdf',
                'order': 9,
                'value-regex': 'upload',
                'required':True
            }
        }

        self.content_params = {}
        self.content_params.update(default_content_params)
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

        default_content_params = {
            'tag': {
                'description': 'Bid description',
                'order': 1,
                'value-radio': ['I want to review',
                    'I can review',
                    'I can probably review but am not an expert',
                    'I cannot review',
                    'No bid'],
                'required':True
            }
        }

        self.content_params = {}
        self.content_params.update(default_content_params)
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
