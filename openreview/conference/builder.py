from __future__ import absolute_import

from .. import openreview
from .. import tools
from . import webfield
from . import invitation

class Conference(object):

    def __init__(self, client):
        self.client = client
        self.groups = []
        self.name = None
        self.header = {}
        self.invitation_builder = invitation.InvitationBuilder(client)
        self.webfield_builder = webfield.WebfieldBuilder(client)

    def set_id(self, id):
        self.id = id

    def get_id(self):
        return self.id

    def set_conference_name(self, name):
        self.name = name

    def get_conference_name(self):
        return self.name

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

    def open_submissions(self, mode = 'blind', due_date = None, subject_areas = []):
        options = {
            'due_date': due_date
        }
        return self.invitation_builder.set_submission_invitation(self.id, options)

    def recruit_reviewers(self, emails):

        pcs_id = self.id + '/Program_Chairs'
        reviewers_id = self.id + '/Reviewers'
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'
        hash_seed = '1234'

        self.client.post_group(openreview.Group(id = reviewers_id,
            readers = [self.id, pcs_id],
            writers = [self.id],
            signatures = [self.id],
            signatories = [self.id],
            members = []))

        self.client.post_group(openreview.Group(id = reviewers_declined_id,
            readers = [self.id, pcs_id],
            writers = [self.id],
            signatures = [self.id],
            signatories = [self.id],
            members = []))

        self.client.post_group(openreview.Group(id = reviewers_invited_id,
            readers = [self.id, pcs_id],
            writers = [self.id],
            signatures = [self.id],
            signatories = [self.id],
            members = []))


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
        self.webfieldBuilder = webfield.WebfieldBuilder(client)


    def __build_groups(self, conference_id):
        path_components = conference_id.split('/')
        paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]
        groups = []

        for p in paths:
            group = tools.get_group(self.client, id = p)

            if group is None:
                print('post group')
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

        #update web pages
        for g in groups[:-1]:
            self.webfieldBuilder.set_landing_page(g)

        self.webfieldBuilder.set_home_page(groups[-1], self.conference.get_homepage_options())

        return groups


    def set_conference_id(self, id):
        self.conference.set_id(id)

    def set_conference_name(self, name):
        self.conference.set_conference_name(name)

    def set_homepage_header(self, header):
        self.conference.set_homepage_header(header)

    def get_result(self):

        id = self.conference.get_id()
        groups = self.__build_groups(id)
        self.conference.set_conference_groups(groups)
        return self.conference
