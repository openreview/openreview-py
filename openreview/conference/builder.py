from __future__ import absolute_import

import time
from .. import openreview
from .. import tools
from . import webfield
from . import invitation

class ConferenceType(object):

    @classmethod
    def homepage_webfield_template(cls):
        return "noBlindConferenceWebfield.js"

    @classmethod
    def submission_reply(cls):
        return None

class SingleBlindConferenceType(ConferenceType):

    @classmethod
    def homepage_webfield_template(cls):
        return "noBlindConferenceWebfield.js"

class DoubleBlindConferenceType(ConferenceType):

    @classmethod
    def homepage_webfield_template(cls):
        return "homepage.js"

    @classmethod
    def submission_reply(cls, id):
        return {
            'forum': None,
            'replyto': None,
            'readers': {
                'values-copied': [
                    '{content.authorids}',
                    '{signatures}'
                ]
            },
            'writers': {
                'values-copied': [
                    id,
                    '{content.authorids}',
                    '{signatures}'
                ]
            },
            'signatures': {
                'values-regex': '~.*'
            },
            'content': {
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
        }

class Conference(object):

    def __init__(self, client):
        self.client = client
        self.groups = []
        self.name = None
        self.type = ConferenceType
        self.header = {}
        self.invitation_builder = invitation.InvitationBuilder(client)
        self.webfield_builder = webfield.WebfieldBuilder(client)


    def __create_group(self, group_id, group_owner_id):

        group = tools.get_group(self.client, id = group_id)
        if group is None:
            group = self.client.post_group(openreview.Group(id = group_id,
                readers = [self.id, group_owner_id],
                writers = [self.id],
                signatures = [self.id],
                signatories = [self.id],
                members = []))
        return group

    def set_id(self, id):
        self.id = id

    def get_id(self):
        return self.id

    def set_conference_name(self, name):
        self.name = name

    def get_conference_name(self):
        return self.name

    def set_type(self, type):
        self.type = type

    def get_type(self):
        return self.type

    def set_conference_groups(self, groups):
        self.groups = groups

    def get_conference_groups(self):
        return self.groups

    def set_homepage_header(self, header):
        self.header = header

    def get_homepage_options(self):
        options = {}
        if self.name:
            options['subtitle'] = self.name
        if self.header:
            options['title'] = self.header.get('title')
            options['subtitle'] = self.header.get('subtitle')
            options['location'] = self.header.get('location')
            options['date'] = self.header.get('date')
            options['website'] = self.header.get('website')
            options['instructions'] = self.header.get('instructions')
            options['deadline'] = self.header.get('deadline')
        return options

    def open_submissions(self, due_date = None, subject_areas = None):

        ## Author console
        authors_group = openreview.Group(id = self.id + '/Authors',
            readers = ['everyone'],
            signatories = [self.id],
            signatures = [self.id],
            writers = [self.id]
        )
        self.webfield_builder.set_author_page(self.id, authors_group, { 'title': 'Author console'})

        ## Submission invitation
        options = {
            'name': 'Submission',
            'due_date': due_date,
            'subject_areas': subject_areas,
            'reply': self.type.submission_reply(self.id)
        }
        return self.invitation_builder.set_submission_invitation(self.id, options)

    def close_submissions(self, freeze_submissions = True):

        # Get invitation
        invitation = self.client.get_invitation(id = self.id + '/-/Submission')
        if invitation.reply['writers'] != self.id:
            invitation.reply['writers'] = self.id

        now = round(time.time() * 1000)
        if invitation.duedate > now:
            invitation.duedate = now
        self.client.post_invitation(invitation)

        # if freeze submissions then remove writers
        # use a process pool to run this
        notes_iterator = tools.iterget_notes(self.client, invitation = invitation.id)
        for note in notes_iterator:
            if note.writers != [self.id]:
                note.writers = [self.id]
                self.client.post_note(note)

        return invitation

    def recruit_reviewers(self, emails, title = None, message = None):

        pcs_id = self.id + '/Program_Chairs'
        reviewers_id = self.id + '/Reviewers'
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'
        hash_seed = '1234'

        self.__create_group(reviewers_id, pcs_id)
        self.__create_group(reviewers_declined_id, pcs_id)
        self.__create_group(reviewers_invited_id, pcs_id)

        options = {
            'reviewers_id': reviewers_id,
            'reviewers_declined_id': reviewers_declined_id,
            'hash_seed': hash_seed
        }
        invitation = self.invitation_builder.set_reviewer_recruiter_invitation(self.id, options)
        invitation = self.webfield_builder.set_recruit_page(self.id, invitation, self.get_homepage_options())
        recruit_message = '''Dear {name},

        You have been nominated by the program chair committeee of ''' + self.id + ''' to serve as a reviewer.  As a respected researcher in the area, we hope you will accept and help us make the conference a success.

        Reviewers are also welcome to submit papers, so please also consider submitting to the conference!

        We will be using OpenReview.net and a reviewing process that we hope will be engaging and inclusive of the whole community.

        The success of the conference depends on the quality of the reviewing process and ultimately on the quality and dedication of the reviewers. We hope you will accept our invitation.

        To ACCEPT the invitation, please click on the following link:


        {accept_url}

        To DECLINE the invitation, please click on the following link:

        {decline_url}

        Please answer within 10 days.

        If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using.  Visit http://openreview.net/profile after logging in.

        If you have any questions, please contact us at info@openreview.net.

        Cheers!

        Program Chairs

        '''
        recruit_message_subj = self.id + ': Invitation to Review'

        if title:
            recruit_message_subj = title

        if message:
            recruit_message = message

        for email in emails:
            tools.recruit_reviewer(self.client, email, 'artist',
                hash_seed,
                invitation.id,
                recruit_message,
                recruit_message_subj,
                reviewers_invited_id,
                verbose = False)

        return self.client.get_group(id = reviewers_invited_id)


class ConferenceBuilder(object):

    def __init__(self, client):
        self.client = client
        self.conference = Conference(client)
        self.webfield_builder = webfield.WebfieldBuilder(client)


    def __build_groups(self, conference_id):
        path_components = conference_id.split('/')
        paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]
        groups = []

        for p in paths:
            group = tools.get_group(self.client, id = p)

            if group is None:
                group = self.client.post_group(openreview.Group(
                    id = p,
                    readers = ['everyone'],
                    nonreaders = [],
                    writers = [p],
                    signatories = [p],
                    signatures = ['~Super_User1'],
                    members = [])
                )

            groups.append(group)

        return groups


    def set_conference_id(self, id):
        self.conference.set_id(id)

    def set_conference_name(self, name):
        self.conference.set_conference_name(name)

    def set_homepage_header(self, header):
        self.conference.set_homepage_header(header)

    def set_conference_type(self, type):
        self.conference.set_type(type)

    def get_result(self):

        id = self.conference.get_id()
        groups = self.__build_groups(id)
        for g in groups[:-1]:
            self.webfield_builder.set_landing_page(g)

        self.webfield_builder.set_home_page(groups[-1], self.conference.get_type().homepage_webfield_template() , self.conference.get_homepage_options())

        self.conference.set_conference_groups(groups)
        return self.conference
