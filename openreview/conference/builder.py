from __future__ import absolute_import

import time
import re
from .. import openreview
from .. import tools
from . import webfield
from . import invitation


class Conference(object):

    def __init__(self, client):
        self.client = client
        self.groups = []
        self.name = ''
        self.short_name = ''
        self.header = {}
        self.invitation_builder = invitation.InvitationBuilder(client)
        self.webfield_builder = webfield.WebfieldBuilder(client)
        self.authors_name = 'Authors'
        self.reviewers_name = 'Reviewers'
        self.area_chairs_name = 'Area_Chairs'
        self.program_chairs_name = 'Program_Chairs'
        self.submission_name = 'Submission'
        self.layout = 'tabs'

    def __create_group(self, group_id, group_owner_id, members = []):

        group = tools.get_group(self.client, id = group_id)
        if group is None:
            return self.client.post_group(openreview.Group(id = group_id,
                readers = [self.id, group_owner_id, group_id],
                writers = [self.id],
                signatures = [self.id],
                signatories = [group_id],
                members = members))
        else:
            return self.client.add_members_to_group(group, members)

    def set_id(self, id):
        self.id = id

    def get_id(self):
        return self.id

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_short_name(self, name):
        self.short_name = name

    def get_short_name(self):
        return self.short_name

    def set_reviewers_name(self, name):
        self.reviewers_name = name

    def set_area_chairs_name(self, name):
        self.area_chairs_name = name

    def set_program_chairs_name(self, name):
        self.program_chairs_name = name

    def set_submission_name(self, name):
        self.submission_name = name

    def get_program_chairs_id(self):
        return self.id + '/' + self.program_chairs_name

    def get_reviewers_id(self):
        return self.id + '/' + self.reviewers_name

    def get_authors_id(self):
        return self.id + '/' + self.authors_name

    def get_area_chairs_id(self):
        return self.id + '/' + self.area_chairs_name

    def get_submission_id(self):
        return self.id + '/-/' + self.submission_name

    def set_conference_groups(self, groups):
        self.groups = groups

    def get_conference_groups(self):
        return self.groups

    def set_homepage_header(self, header):
        self.header = header

    def set_homepage_layout(self, layout):
        self.layout = layout

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

    def open_submissions(self, due_date = None, public = False, subject_areas = [], additional_fields = {}, additional_readers = [], include_keywords = True, include_TLDR = True):

        ## Author console
        authors_group = openreview.Group(id = self.id + '/Authors',
            readers = ['everyone'],
            signatories = [self.id],
            signatures = [self.id],
            writers = [self.id]
        )
        self.webfield_builder.set_author_page(self.id, authors_group, { 'title': 'Author console', 'submission_id': self.get_submission_id()})

        ## Submission invitation
        options = {
            'conference_short_name': self.short_name,
            'public': public,
            'submission_name': self.submission_name,
            'due_date': due_date,
            'subject_areas': subject_areas,
            'additional_fields': additional_fields,
            'additional_readers': additional_readers,
            'include_keywords': include_keywords,
            'include_TLDR': include_TLDR
        }
        return self.invitation_builder.set_submission_invitation(self.id, due_date, options)

    def close_submissions(self, freeze_submissions = True):

        # Get invitation
        invitation = self.client.get_invitation(id = self.get_submission_id())

        # Set duedate in the past
        now = round(time.time() * 1000)
        if invitation.duedate > now:
            invitation.duedate = now
        invitation = self.client.post_invitation(invitation)

        # If freeze submissions then remove writers
        # use a process pool to run this
        if freeze_submissions:
            if invitation.reply['writers'] != self.id:
                invitation.reply['writers'] = self.id
                invitation = self.client.post_invitation(invitation)

            notes_iterator = tools.iterget_notes(self.client, invitation = invitation.id)
            for note in notes_iterator:
                if note.writers != [self.id]:
                    note.writers = [self.id]
                    self.client.post_note(note)

        # Add venue to active venues
        active_venues_group = self.client.get_group(id = 'active_venues')
        self.client.add_members_to_group(active_venues_group, [self.get_id()])

        return invitation

    def open_comments(self, name, public, anonymous):
        ## Create comment invitations per paper
        notes_iterator = tools.iterget_notes(self.client, invitation = self.get_submission_id())
        if public:
            self.invitation_builder.set_public_comment_invitation(self.id, notes_iterator, name, anonymous)
        else:
            self.invitation_builder.set_private_comment_invitation(self, notes_iterator, name, anonymous)

    # def close_comments():
    #     ## disable comments removing the invitees? or setting an expiration date

    def set_program_chairs(self, emails):
        pcs_id = self.get_program_chairs_id()
        return self.__create_group(pcs_id, self.id, emails)

    def set_area_chairs(self, emails):
        acs_id = self.get_area_chairs_id()
        return self.__create_group(acs_id, self.id, emails)

    def set_reviewers(self, emails):
        reviewers_id = self.get_reviewers_id()
        group = self.__create_group(reviewers_id, self.id, emails)

        return self.webfield_builder.set_reviewer_page(self.id, group)

    def set_authors(self):
        notes_iterator = tools.iterget_notes(self.client, invitation = self.get_submission_id())

        for n in notes_iterator:
            group = self.__create_group('{conference_id}/Paper{number}'.format(conference_id = self.id, number = n.number), self.id)
            self.__create_group('{number_group}/{author_name}'.format(number_group = group.id, author_name = self.authors_name), self.id, n.content.get('authorids'))

    def recruit_reviewers(self, emails = [], title = None, message = None, reviewers_name = 'Reviewers', reviewer_accepted_name = None, remind = False):

        pcs_id = self.get_program_chairs_id()
        reviewers_id = self.id + '/' + reviewers_name
        reviewers_declined_id = reviewers_id + '/Declined'
        reviewers_invited_id = reviewers_id + '/Invited'
        reviewers_accepted_id = reviewers_id
        if reviewer_accepted_name:
            reviewers_accepted_id = reviewers_id + '/' + reviewer_accepted_name
        hash_seed = '1234'

        reviewers_accepted_group = self.__create_group(reviewers_accepted_id, pcs_id)
        reviewers_declined_group = self.__create_group(reviewers_declined_id, pcs_id)
        reviewers_invited_group = self.__create_group(reviewers_invited_id, pcs_id)

        options = {
            'reviewers_name': reviewers_name,
            'reviewers_accepted_id': reviewers_accepted_id,
            'reviewers_declined_id': reviewers_declined_id,
            'hash_seed': hash_seed
        }
        invitation = self.invitation_builder.set_reviewer_recruiter_invitation(self.id, options)
        invitation = self.webfield_builder.set_recruit_page(self.id, invitation, self.get_homepage_options())
        recruit_message = '''Dear {name},

        You have been nominated by the program chair committeee of ''' + self.short_name + ''' to serve as a reviewer.  As a respected researcher in the area, we hope you will accept and help us make the conference a success.

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

        if remind:
            remind_reviewers = list(set(reviewers_invited_group.members) - set(reviewers_declined_group.members) - set(reviewers_accepted_group.members))
            for reviewer in remind_reviewers:
                name =  re.sub('[0-9]+', '', reviewer.replace('~', '').replace('_', ' ')) if reviewer.startswith('~') else 'invitee'
                tools.recruit_reviewer(self.client, reviewer, name,
                    hash_seed,
                    invitation.id,
                    recruit_message,
                    'Reminder: ' + recruit_message_subj,
                    reviewers_invited_id,
                    verbose = False)

        invite_emails = list(set(emails) - set(reviewers_invited_group.members))
        for email in invite_emails:
            name =  re.sub('[0-9]+', '', email.replace('~', '').replace('_', ' ')) if email.startswith('~') else 'invitee'
            tools.recruit_reviewer(self.client, email, name,
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
        self.conference.set_name(name)

    def set_conference_short_name(self, name):
        self.conference.set_short_name(name)

    def set_conference_reviewers_name(self, name):
        self.conference.set_reviewers_name(name)

    def set_conference_area_chairs_name(self, name):
        self.conference.set_area_chairs_name(name)

    def set_conference_program_chairs_name(self, name):
        self.conference.set_program_chairs_name(name)

    def set_conference_submission_name(self, name):
        self.conference.set_submission_name(name)

    def set_homepage_header(self, header):
        self.conference.set_homepage_header(header)

    def set_homepage_layout(self, layout):
        self.conference.set_homepage_layout(layout)

    def get_result(self):

        id = self.conference.get_id()
        groups = self.__build_groups(id)
        for g in groups[:-1]:
            self.webfield_builder.set_landing_page(g)
        host = self.client.get_group(id = 'host')
        root_id = groups[0].id
        if root_id == root_id.lower():
            root_id = groups[1].id
        self.client.add_members_to_group(host, root_id)

        options = self.conference.get_homepage_options()
        options['reviewers_name'] = self.conference.reviewers_name
        options['area_chairs_name'] = self.conference.area_chairs_name
        options['reviewers_id'] = self.conference.get_reviewers_id()
        options['authors_id'] = self.conference.get_authors_id()
        options['program_chairs_id'] = self.conference.get_program_chairs_id()
        options['area_chairs_id'] = self.conference.get_area_chairs_id()
        options['submission_id'] = self.conference.get_submission_id()
        self.webfield_builder.set_home_page(group = groups[-1], layout = self.conference.layout, options = options)

        self.conference.set_conference_groups(groups)
        return self.conference
