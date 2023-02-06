from itertools import groupby
from .. import openreview
from .. import tools
from . import group
from .invitation import InvitationBuilder
from .recruitment import Recruitment
from .assignment import Assignment
from openreview.api import Edge
from openreview.api import Group

import re
import json
import datetime
import random
import secrets
from tqdm import tqdm
from pylatexenc.latexencode import utf8tolatex, UnicodeToLatexConversionRule, UnicodeToLatexEncoder, RULE_REGEX

class Journal(object):

    def __init__(self, client, venue_id, secret_key, contact_info, full_name, short_name, website='jmlr.org/tmlr', submission_name='Submission', settings={}):

        self.client = client
        self.venue_id = venue_id
        self.secret_key = secret_key
        self.contact_info = contact_info
        self.short_name = short_name
        self.full_name = full_name
        self.website = website
        self.submission_name = submission_name
        self.settings = settings
        self.request_form_id = None
        self.editors_in_chief_name = 'Editors_In_Chief'
        self.action_editors_name = 'Action_Editors'
        self.reviewers_name = 'Reviewers'
        self.solicit_reviewers_name = 'Solicit_Reviewers'
        self.authors_name = 'Authors'
        self.submission_group_name = 'Paper'
        self.submitted_venue_id = f'{venue_id}/Submitted'
        self.under_review_venue_id = f'{venue_id}/Under_Review'
        self.rejected_venue_id = f'{venue_id}/Rejected'
        self.desk_rejected_venue_id = f'{venue_id}/Desk_Rejected'
        self.withdrawn_venue_id = f'{venue_id}/Withdrawn_Submission'
        self.retracted_venue_id = f'{venue_id}/Retracted_Acceptance'
        self.assigning_AE_venue_id = f'{venue_id}/Assigning_AE'
        self.assigned_AE_venue_id = f'{venue_id}/Assigned_AE'
        self.accepted_venue_id = venue_id
        self.invitation_builder = InvitationBuilder(self)
        self.group_builder = group.GroupBuilder(self)
        self.header = {
            "title": self.full_name,
            "short": self.short_name,
            "subtitle": "To be defined",
            "location": "Everywhere",
            "date": "Ongoing",
            "website": "https://openreview.net",
            "instructions": '',
            "deadline": "",
            "contact": self.contact_info
        }
        self.assignment = Assignment(self)
        self.recruitment = Recruitment(self)
        self.unavailable_reminder_period = 4 # weeks
        self.ae_custom_max_papers = 12

    def __get_group_id(self, name, number=None):
        if number:
            return f'{self.venue_id}/{self.submission_group_name}{number}/{name}'
        return f'{self.venue_id}/{name}'

    def __get_invitation_id(self, name, prefix=None, number=None):
        group_id = self.venue_id
        if prefix:
            group_id = prefix
        if number:
            return f'{group_id}/{self.submission_group_name}{number}/-/{name}'
        return f'{group_id}/-/{name}'

    def get_editors_in_chief_id(self):
        return f'{self.venue_id}/{self.editors_in_chief_name}'

    def get_publication_chairs_id(self):
        return f'{self.venue_id}/Publication_Chairs'

    def get_action_editors_id(self, number=None):
        return self.__get_group_id(self.action_editors_name, number)

    def get_reviewers_id(self, number=None, anon=False):
        return self.__get_group_id('Reviewer_' if anon else self.reviewers_name, number)

    def get_reviewers_reported_id(self):
        return self.get_reviewers_id() + '/Reported'

    def get_solicit_reviewers_id(self, number=None, declined=False):
        group_id = self.__get_group_id(self.solicit_reviewers_name, number)
        if declined:
            group_id = group_id + '/Declined'
        return group_id

    def get_authors_id(self, number=None):
        return self.__get_group_id(self.authors_name, number)

    def get_meta_invitation_id(self):
        return self.__get_invitation_id(name='Edit')

    def get_form_id(self):
        return self.__get_invitation_id(name='Form')

    def get_review_approval_id(self, number=None):
        return self.__get_invitation_id(name='Review_Approval', number=number)

    def get_withdrawal_id(self, number=None):
        return self.__get_invitation_id(name='Withdrawal', number=number)

    def get_desk_rejection_id(self, number=None):
        return self.__get_invitation_id(name='Desk_Rejection', number=number)

    def get_desk_rejection_approval_id(self, number=None):
        return self.__get_invitation_id(name='Desk_Rejection_Approval', number=number)        

    def get_retraction_id(self, number=None):
        return self.__get_invitation_id(name='Retraction', number=number)

    def get_retraction_approval_id(self, number=None):
        return self.__get_invitation_id(name='Retraction_Approval', number=number)

    def get_retraction_release_id(self, number=None):
        return self.__get_invitation_id(name='Retraction_Release', number=number)

    def get_retracted_id(self):
        return self.__get_invitation_id(name='Retracted')

    def get_under_review_id(self):
        return self.__get_invitation_id(name='Under_Review')

    def get_desk_rejected_id(self):
        return self.__get_invitation_id(name='Desk_Rejected')

    def get_withdrawn_id(self):
        return self.__get_invitation_id(name='Withdrawn')

    def get_author_submission_id(self):
        return self.__get_invitation_id(name=self.submission_name if self.submission_name else 'Submission')

    def get_release_review_id(self, number=None):
        return self.__get_invitation_id(name='Review_Release', number=number)

    def get_release_comment_id(self, number=None):
        return self.__get_invitation_id(name='Comment_Release', number=number)

    def get_release_decision_id(self, number=None):
        return self.__get_invitation_id(name='Decision_Release', number=number)

    def get_authors_release_id(self, number=None):
        return self.__get_invitation_id(name='Authors_Release', number=number)

    def get_authors_deanonymization_id(self, number=None):
        return self.__get_invitation_id(name='Authors_De-Anonymization', number=number)

    def get_ae_decision_id(self, number=None):
        return self.__get_invitation_id(name='Decision', number=number)

    def get_ae_recruitment_id(self):
        return self.__get_invitation_id(name='Recruitment', prefix=self.get_action_editors_id())

    def get_ae_conflict_id(self):
        return self.__get_invitation_id(name='Conflict', prefix=self.get_action_editors_id())

    def get_ae_affinity_score_id(self):
        return self.__get_invitation_id(name='Affinity_Score', prefix=self.get_action_editors_id())

    def get_ae_aggregate_score_id(self):
        return self.__get_invitation_id(name='Aggregate_Score', prefix=self.get_action_editors_id())

    def get_ae_resubmission_score_id(self):
        return self.__get_invitation_id(name='Resubmission_Score', prefix=self.get_action_editors_id())

    def get_ae_assignment_configuration_id(self):
        return self.__get_invitation_id(name='Assignment_Configuration', prefix=self.get_action_editors_id())

    def get_ae_assignment_id(self, proposed=False, archived=False):
        name = 'Assignment'
        if archived:
            name = 'Archived_Assignment'
        if proposed:
            name = 'Proposed_Assignment'
        return self.__get_invitation_id(name=name, prefix=self.get_action_editors_id())    

    def get_ae_recommendation_id(self, number=None):
        return self.__get_invitation_id(name='Recommendation', prefix=self.get_action_editors_id(number=number))

    def get_ae_custom_max_papers_id(self, number=None):
        return self.__get_invitation_id(name='Custom_Max_Papers', prefix=self.get_action_editors_id(number=number))

    def get_ae_local_custom_max_papers_id(self, number=None):
        return self.__get_invitation_id(name='Local_Custom_Max_Papers', prefix=self.get_action_editors_id(number=number))

    def get_ae_availability_id(self):
        return self.__get_invitation_id(name='Assignment_Availability', prefix=self.get_action_editors_id())

    def get_decision_approval_id(self, number=None):
        return self.__get_invitation_id(name='Decision_Approval', number=number)

    def get_review_id(self, number=None):
        return self.__get_invitation_id(name='Review', number=number)

    def get_review_rating_id(self, signature=None):
        return self.__get_invitation_id(name='Rating', prefix=signature)

    def get_accepted_id(self):
        return self.__get_invitation_id(name='Accepted')

    def get_rejected_id(self):
        return self.__get_invitation_id(name='Rejected')

    def get_reviewer_recommendation_id(self, number=None):
        return self.__get_invitation_id(name='Official_Recommendation', number=number)

    def get_reviewer_recruitment_id(self):
        return self.__get_invitation_id(name='Recruitment', prefix=self.get_reviewers_id())

    def get_reviewer_responsibility_id(self, signature=None):
        if signature:
            return self.__get_invitation_id(name=f'{signature}/Responsibility/Acknowledgement', prefix=self.get_reviewers_id())
        return self.__get_invitation_id(name='Responsibility_Acknowledgement', prefix=self.get_reviewers_id())

    def get_reviewer_report_id(self):
        return self.__get_invitation_id(name='Reviewer_Report', prefix=self.get_reviewers_id())

    def get_reviewer_conflict_id(self):
        return self.__get_invitation_id(name='Conflict', prefix=self.get_reviewers_id())

    def get_reviewer_affinity_score_id(self):
        return self.__get_invitation_id(name='Affinity_Score', prefix=self.get_reviewers_id())

    def get_reviewer_assignment_id(self, number=None, archived=False):
        name = 'Assignment'
        if archived:
            name = 'Archived_Assignment'
        return self.__get_invitation_id(name=name, prefix=self.get_reviewers_id(number))

    def get_reviewer_assignment_acknowledgement_id(self, number=None, reviewer_id=None):
        if reviewer_id:
           return self.__get_invitation_id(name=f'{reviewer_id}/Assignment/Acknowledgement', prefix=self.get_reviewers_id(number))
        return self.__get_invitation_id(name='Assignment_Acknowledgement', prefix=self.get_reviewers_id(number))

    def get_reviewer_custom_max_papers_id(self):
        return self.__get_invitation_id(name='Custom_Max_Papers', prefix=self.get_reviewers_id())

    def get_reviewer_availability_id(self):
        return self.__get_invitation_id(name='Assignment_Availability', prefix=self.get_reviewers_id())

    def get_reviewer_pending_review_id(self):
        return self.__get_invitation_id(name='Pending_Reviews', prefix=self.get_reviewers_id())

    def get_camera_ready_revision_id(self, number=None):
        return self.__get_invitation_id(name='Camera_Ready_Revision', number=number)

    def get_camera_ready_verification_id(self, number=None):
        return self.__get_invitation_id(name='Camera_Ready_Verification', number=number)

    def get_eic_revision_id(self, number=None):
        return self.__get_invitation_id(name='EIC_Revision', number=number)
    
    def get_revision_id(self, number=None):
        return self.__get_invitation_id(name='Revision', number=number)

    def get_solicit_review_id(self, number=None):
        return self.__get_invitation_id(name='Volunteer_to_Review', number=number)

    def get_solicit_review_approval_id(self, number=None, signature=None):
        if signature:
            return self.__get_invitation_id(name=f'{signature}_Volunteer_to_Review_Approval', number=number)

        return self.__get_invitation_id(name='Volunteer_to_Review_Approval', number=number)


    def get_public_comment_id(self, number=None):
        return self.__get_invitation_id(name='Public_Comment', number=number)

    def get_official_comment_id(self, number=None):
        return self.__get_invitation_id(name='Official_Comment', number=number)

    def get_moderation_id(self, number=None):
        return self.__get_invitation_id(name='Moderation', number=number)

    def get_reviewer_report_form(self):
        forum_note = self.client.get_notes(invitation=self.get_form_id(), content={ 'title': 'Reviewer Report'})
        if forum_note:
            return forum_note[0].id

    def get_acknowledgement_responsibility_form(self):
        forum_notes = self.client.get_notes(invitation=self.get_form_id(), content={ 'title': 'Acknowledgement of reviewer responsibility'})
        if len(forum_notes) > 0:
            return forum_notes[0].id                  

    def get_support_group(self):
        if self.request_form_id:
            forum_note = self.client.get_note(self.request_form_id)
            return forum_note.invitations[0].split('/-/')[0]

    def get_review_period_length(self, note):
        if 'submission_length' in note.content:
            if 'Regular submission' in note.content['submission_length']['value']:
                return 2 ## weeks
            if 'Long submission' in note.content['submission_length']['value']:
                return 4 ## weeks
        return 2 ## weeks

    def is_active_submission(self, submission):
        venue_id = submission.content.get('venueid', {}).get('value')
        return venue_id in [self.submitted_venue_id, self.under_review_venue_id, self.assigning_AE_venue_id, self.assigned_AE_venue_id]
    
    def setup(self, support_role, editors=[], assignment_delay=5):
        self.invitation_builder.set_meta_invitation()
        self.group_builder.set_groups(support_role, editors)
        self.invitation_builder.set_invitations(assignment_delay)
        self.group_builder.set_group_variable(self.get_action_editors_id(), 'REVIEWER_REPORT_ID', self.get_reviewer_report_form())
        self.group_builder.set_group_variable(self.get_editors_in_chief_id(), 'REVIEWER_REPORT_ID', self.get_reviewer_report_form())
        self.group_builder.set_group_variable(self.get_editors_in_chief_id(), 'REVIEWER_ACKOWNLEDGEMENT_RESPONSIBILITY_ID', self.get_acknowledgement_responsibility_form())

    def setup_ae_matching(self, label):
        self.assignment.setup_ae_matching(label)

    ## Same interface like Conference and Venue class
    def set_assignments(self, assignment_title, committee_id=None, overwrite=True, enable_reviewer_reassignment=True):
        self.assignment.set_ae_assignments(assignment_title)
    
    def get_action_editors(self):
        return self.client.get_group(self.get_action_editors_id()).members

    def get_reviewers(self):
        return self.client.get_group(self.get_reviewers_id()).members

    def get_authors(self, number):
        return self.client.get_group(self.get_authors_id(number=number)).members

    def setup_ae_assignment(self, note):
        return self.assignment.setup_ae_assignment(note)

    def setup_reviewer_assignment(self, note):
        return self.assignment.setup_reviewer_assignment(note)

    def invite_action_editors(self, message, subject, invitees, invitee_names=None):
        return self.recruitment.invite_action_editors(message, subject, invitees, invitee_names)

    def invite_reviewers(self, message, subject, invitees, invitee_names=None, replyTo=None, reinvite=False):
        return self.recruitment.invite_reviewers(message, subject, invitees, invitee_names, replyTo, reinvite)

    def setup_author_submission(self, note):
        print('Setup author submission data...')
        self.group_builder.setup_submission_groups(note)
        self.invitation_builder.set_note_revision_invitation(note)
        self.invitation_builder.set_note_withdrawal_invitation(note)
        self.invitation_builder.set_note_desk_rejection_invitation(note)
        self.setup_ae_assignment(note)
        self.invitation_builder.set_ae_recommendation_invitation(note, self.get_due_date(weeks = 1))
        self.setup_reviewer_assignment(note)
        print('Finished setup author submission data.')
        

    def setup_under_review_submission(self, note):
        self.invitation_builder.set_note_review_invitation(note, self.get_due_date(weeks = self.get_review_period_length(note)))
        self.invitation_builder.set_note_solicit_review_invitation(note)
        self.invitation_builder.set_note_comment_invitation(note)
        self.invitation_builder.release_submission_history(note)
        self.invitation_builder.expire_invitation(self.get_review_approval_id(note.number))

    def assign_reviewer(self, note, reviewer, solicit):
        self.assignment.assign_reviewer(note, reviewer, solicit)

    def is_submission_public(self):
        return self.settings.get('submission_public', True)

    def get_issn(self):
        return self.settings.get('issn', None)

    def are_authors_anonymous(self):
        return self.settings.get('author_anonymity', True)

    def get_certifications(self):
        return self.settings.get('certifications', [])        

    def should_show_conflict_details(self):
        return self.settings.get('show_conflict_details', False)

    def has_publication_chairs(self):
        return self.settings.get('has_publication_chairs', False)     

    def should_release_authors(self):
        return self.is_submission_public() and self.are_authors_anonymous()

    def get_author_submission_readers(self, number):
        if self.are_authors_anonymous():
            return [ self.venue_id, self.get_action_editors_id(number), self.get_authors_id(number)]
    
    def get_under_review_submission_readers(self, number):
        if self.is_submission_public():
            return ['everyone']
        return [self.venue_id, self.get_action_editors_id(number), self.get_reviewers_id(number), self.get_authors_id(number)]

    def get_release_review_readers(self, number):
        if self.is_submission_public():
            return ['everyone']
        return [self.get_editors_in_chief_id(), self.get_action_editors_id(number), self.get_reviewers_id(number), self.get_authors_id(number)]        
    
    def get_release_decision_readers(self, number):
        if self.is_submission_public():
            return ['everyone']
        return [self.get_editors_in_chief_id(), self.get_action_editors_id(number), self.get_reviewers_id(number), self.get_authors_id(number)]        

    def get_release_authors_readers(self, number):
        if self.is_submission_public():
            return ['everyone']
        return [self.get_editors_in_chief_id(), self.get_action_editors_id(number), self.get_authors_id(number)]        

    def get_official_comment_readers(self, number):
        readers = []
        if self.is_submission_public():
            readers.append('everyone')

        return readers + [
            self.get_editors_in_chief_id(), 
            self.get_action_editors_id(number), 
            self.get_reviewers_id(number), 
            self.get_reviewers_id(number, anon=True) + '.*', 
            self.get_authors_id(number)
        ]        

    def get_due_date(self, days=0, weeks=0):
        due_date = datetime.datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999) + datetime.timedelta(days=days, weeks = weeks)
        return due_date

    def get_bibtex(self, note, new_venue_id, anonymous=False, certifications=None):

        u = UnicodeToLatexEncoder(
            conversion_rules=[
                UnicodeToLatexConversionRule(
                    rule_type=RULE_REGEX,
                    rule=[
                        (re.compile(r'[A-Z]{2,}'), r'{\g<0>}')
                    ]),
                'defaults'
            ]
        )

        first_word = re.sub('[^a-zA-Z]', '', note.content['title']['value'].split(' ')[0].lower())
        bibtex_title = u.unicode_to_latex(note.content['title']['value'])
        year = datetime.datetime.fromtimestamp(note.cdate/1000).year

        if new_venue_id == self.under_review_venue_id:

            first_author_last_name = 'anonymous'
            authors = 'Anonymous'

            bibtex = [
                '@article{',
                utf8tolatex(first_author_last_name + str(year) + first_word + ','),
                'title={' + bibtex_title + '},',
                'author={' + utf8tolatex(authors) + '},',
                'journal={Submitted to ' + self.full_name + '},',
                'year={' + str(year) + '},',
                'url={https://openreview.net/forum?id=' + note.forum + '},',
                'note={Under review}',
                '}'
            ]
            return '\n'.join(bibtex)

        if new_venue_id == self.withdrawn_venue_id:

            if anonymous:
                first_author_last_name = 'anonymous'
                authors = 'Anonymous'
            else:
                first_author_profile = self.client.get_profile(note.content['authorids']['value'][0])
                first_author_last_name = openreview.tools.get_preferred_name(first_author_profile, last_name_only=True).lower()
                authors = ' and '.join(note.content['authors']['value'])

            bibtex = [
                '@article{',
                utf8tolatex(first_author_last_name + str(year) + first_word + ','),
                'title={' + bibtex_title + '},',
                'author={' + utf8tolatex(authors) + '},',
                'journal={Submitted to ' + self.full_name + '},',
                'year={' + str(year) + '},',
                'url={https://openreview.net/forum?id=' + note.forum + '},',
                'note={Withdrawn}',
                '}'
            ]
            return '\n'.join(bibtex)


        if new_venue_id == self.rejected_venue_id:

            if anonymous:
                first_author_last_name = 'anonymous'
                authors = 'Anonymous'
            else:
                first_author_profile = self.client.get_profile(note.content['authorids']['value'][0])
                first_author_last_name = openreview.tools.get_preferred_name(first_author_profile, last_name_only=True).lower()
                authors = ' and '.join(note.content['authors']['value'])

            bibtex = [
                '@article{',
                utf8tolatex(first_author_last_name + str(year) + first_word + ','),
                'title={' + bibtex_title + '},',
                'author={' + utf8tolatex(authors) + '},',
                'journal={Submitted to ' + self.full_name + '},',
                'year={' + str(year) + '},',
                'url={https://openreview.net/forum?id=' + note.forum + '},',
                'note={Rejected}',
                '}'
            ]
            return '\n'.join(bibtex)

        if new_venue_id == self.accepted_venue_id:

            first_author_last_name = 'anonymous'
            authors = 'Anonymous'
            if 'everyone' in self.get_release_authors_readers(note.number):
                first_author_profile = self.client.get_profile(note.content['authorids']['value'][0])
                first_author_last_name = openreview.tools.get_preferred_name(first_author_profile, last_name_only=True).lower()
                authors = ' and '.join(note.content['authors']['value'])

            issn = self.get_issn()

            bibtex = [
                '@article{',
                utf8tolatex(first_author_last_name + str(year) + first_word + ','),
                'title={' + bibtex_title + '},',
                'author={' + utf8tolatex(authors) + '},',
                'journal={' + self.full_name + '},',
            ]
            if issn:
                bibtex.append('issn={' + issn + '},')
            
            bibtex = bibtex + [
                'year={' + str(year) + '},',
                'url={https://openreview.net/forum?id=' + note.forum + '},',
                'note={' + ', '.join(certifications) + '}',
                '}'
            ]
            return '\n'.join(bibtex)

        if new_venue_id == self.retracted_venue_id:

            if anonymous:
                first_author_last_name = 'anonymous'
                authors = 'Anonymous'
            else:
                first_author_profile = self.client.get_profile(note.content['authorids']['value'][0])
                first_author_last_name = openreview.tools.get_preferred_name(first_author_profile, last_name_only=True).lower()
                authors = ' and '.join(note.content['authors']['value'])

            bibtex = [
                '@article{',
                utf8tolatex(first_author_last_name + str(year) + first_word + ','),
                'title={' + bibtex_title + '},',
                'author={' + utf8tolatex(authors) + '},',
                'journal={Submitted to ' + self.full_name + '},',
                'year={' + str(year) + '},',
                'url={https://openreview.net/forum?id=' + note.forum + '},',
                'note={Retracted after acceptance}',
                '}'
            ]
            return '\n'.join(bibtex)

    def get_late_invitees(self, invitation_id):

        invitation = self.client.get_invitation(invitation_id)

        invitee_members = []
        for invitee in invitation.invitees:
            if invitee not in [self.venue_id, self.get_editors_in_chief_id()]:
                if invitee.startswith('~'):
                    profile = self.client.get_profile(invitee)
                    invitee_members.append(profile.id)
                elif '@' in invitee:
                    profile = openreview.tools.get_profile(self.client, invitee)
                    invitee_members.append(profile.id if profile else invitee)
                else:
                    invitee_members = invitee_members + self.client.get_group(invitee).members

        ## Check replies and get signatures
        replies = self.client.get_notes(invitation=invitation.id, details='signatures')

        signature_members = []
        for reply in replies:
            for signature in reply.details['signatures']:
                if signature['id'].startswith('~'):
                    profile = self.client.get_profile(signature)
                    signature_members.append(profile.id)
                else:
                    signature_members = signature_members + signature['members']
            for signature in reply.signatures:
                if signature.startswith('~'):
                    profile = self.client.get_profile(signature)
                    signature_members.append(profile.id)

        print('invitee_members', invitee_members)
        print('signature_members', signature_members)
        return list(set(invitee_members) - set(signature_members))

    def notify_readers(self, edit, content_fields=[]):

        vowels = ['a', 'e', 'i', 'o', 'u']
        note = self.client.get_note(edit.note.id)
        forum = self.client.get_note(note.forum)

        if note.ddate:
            return

        action = 'posted' if note.tcdate == note.tmdate else 'edited'

        readers = note.readers
        nonreaders = [edit.tauthor]
        if note.nonreaders:
            nonreaders += note.nonreaders
        formatted_invitation = edit.invitation.split('/-/')[1].replace('_', ' ')
        lower_formatted_invitation = formatted_invitation.lower()
        before_invitation = 'An' if lower_formatted_invitation[0] in vowels else 'A'
        is_public = 'everyone' in readers

        subject = f'''[{self.short_name}] {formatted_invitation} {action} on submission {forum.content['title']['value']}'''

        formatted_content = f'''
Submission: {forum.content['title']['value']}
'''
        for field in content_fields:
            formatted_field = field[0].upper() + field.replace('_', ' ')[1:]
            formatted_content = formatted_content + f'{formatted_field}: {note.content.get(field, {}).get("value", "")}' + '\n'

        content = f'''{formatted_content}
To view the {lower_formatted_invitation}, click here: https://openreview.net/forum?id={note.forum}&noteId={note.id}
'''

        ## Notify author of the note
        if action == 'posted' and self.get_editors_in_chief_id() not in note.signatures:
            message = f'''Hi {{{{fullname}}}},

Your {lower_formatted_invitation} on a submission has been {action}
{content}
'''
            self.client.post_message(recipients=[edit.tauthor], subject=subject, message=message, replyTo=self.contact_info)

        ## Notify authors
        if is_public or self.get_authors_id(number=forum.number) in readers:
            message = f'''Hi {{{{fullname}}}},

{before_invitation} {lower_formatted_invitation} has been {action} on your submission.
{content}
'''
            self.client.post_message(recipients=[self.get_authors_id(number=forum.number)], subject=subject, message=message, ignoreRecipients=nonreaders, replyTo=self.contact_info)

        ## Notify reviewers
        reviewer_recipients = []
        if is_public or self.get_reviewers_id(number=forum.number) in readers:
            reviewer_recipients = [self.get_reviewers_id(number=forum.number)]
        else:
            anon_reviewer_id = self.get_reviewers_id(number=forum.number, anon=True)
            for reader in readers:
                if reader.startswith(anon_reviewer_id):
                    reviewer_recipients.append(reader)
        if reviewer_recipients:
            message = f'''Hi {{{{fullname}}}},

{before_invitation} {lower_formatted_invitation} has been {action} on a submission for which you are a reviewer.
{content}
'''
            self.client.post_message(recipients=reviewer_recipients, subject=subject, message=message, ignoreRecipients=nonreaders, replyTo=self.contact_info)


        ## Notify action editors
        if is_public or self.get_action_editors_id(number=forum.number) in readers:
            message = f'''Hi {{{{fullname}}}},

{before_invitation} {lower_formatted_invitation} has been {action} on a submission for which you are an Action Editor.
{content}
'''
            self.client.post_message(recipients=[self.get_action_editors_id(number=forum.number)], subject=subject, message=message, ignoreRecipients=nonreaders, replyTo=self.contact_info)


        if self.get_editors_in_chief_id() in readers and len(readers) == 2 and 'comment' in lower_formatted_invitation:
            message = f'''Hi {{{{fullname}}}},

{before_invitation} {lower_formatted_invitation} has been {action} on a submission for which you are serving as Editor-In-Chief.
{content}
'''
            self.client.post_message(recipients=[self.get_editors_in_chief_id()], subject=subject, message=message, ignoreRecipients=nonreaders, replyTo=self.contact_info)

    def setup_note_invitations(self):

        note_invitations = self.client.get_all_invitations(prefix=f'{self.venue_id}/{self.submission_group_name}')
        submissions_by_number = { s.number: s for s in self.client.get_all_notes(invitation=self.get_author_submission_id())}

        def find_number(tokens):
            for token in tokens:
                if token.startswith(self.submission_group_name):
                    return int(token.replace(self.submission_group_name, ''))

        for invitation in note_invitations:

            tokens = invitation.id.split('/')
            name = tokens[-1]
            note_number = find_number(tokens)
            submission = submissions_by_number.get(note_number)
            replyto = None
            if 'note' in invitation.edit and 'replyto' in invitation.edit['note']:
                replyto = invitation.edit['note']['replyto']['const'] if 'const' in invitation.edit['note']['replyto'] else invitation.edit['note']['replyto']

            if name and submission:

                super_invitation_name = self.__get_invitation_id(name=name)
                if invitation.id.endswith('/Assignment/Acknowledgement'):
                    reviewer_id = tokens[-3]
                    review_invitation = self.client.get_invitation(self.get_review_id(number=note_number))
                    self.invitation_builder.set_note_reviewer_assignment_acknowledgement_invitation(submission, reviewer_id, duedate=datetime.datetime.fromtimestamp(int(invitation.duedate/1000)), review_duedate=datetime.datetime.fromtimestamp(int(review_invitation.duedate/1000)).strftime("%b %d, %Y"))

                elif invitation.id.endswith('/-/Solicit_Review'):
                    self.update_solicit_review(note_number, invitation)

                elif invitation.id == self.get_review_approval_id(number=note_number):
                    self.invitation_builder.set_note_review_approval_invitation(submission, duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))
                
                elif invitation.id == self.get_desk_rejection_approval_id(number=note_number):
                    self.invitation_builder.set_note_desk_rejection_approval_invitation(submission, openreview.api.Note(id=replyto), duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))
                
                elif invitation.id == self.get_withdrawal_id(number=note_number):
                    self.invitation_builder.set_note_withdrawal_invitation(submission)
                
                elif invitation.id == self.get_desk_rejection_id(number=note_number):
                    self.invitation_builder.set_note_desk_rejection_invitation(submission)
                
                elif invitation.id == self.get_retraction_id(number=note_number):
                    self.invitation_builder.set_note_retraction_invitation(submission)
                
                elif invitation.id == self.get_retraction_release_id(number=note_number):
                    self.invitation_builder.set_note_retraction_release_invitation(submission)
                
                elif invitation.id == self.get_retraction_approval_id(number=note_number):
                    self.invitation_builder.set_note_retraction_approval_invitation(submission, openreview.api.Note(id=replyto))
                
                elif invitation.id == self.get_review_id(number=note_number):
                    reviews = self.client.get_notes(invitation=invitation.id, limit=1)
                    is_public = reviews and 'everyone' in reviews[0].readers
                    self.invitation_builder.set_note_review_invitation(submission, duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))
                    if is_public:
                        invitation = self.invitation_builder.post_invitation_edit(invitation=openreview.api.Invitation(id=invitation.id,
                                signatures=[self.get_editors_in_chief_id()],
                                edit={
                                    'note': {
                                        'readers': [ 'everyone' ]
                                    }
                                }
                        ))                    
                
                elif invitation.id == self.get_release_review_id(number=note_number):
                    self.invitation_builder.set_note_release_review_invitation(submission)

                elif invitation.id == self.get_reviewer_recommendation_id(number=note_number):
                    self.invitation_builder.set_note_official_recommendation_invitation(submission, cdate = datetime.datetime.fromtimestamp(int(invitation.cdate/1000)), duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))

                elif invitation.id == self.get_solicit_review_id(number=note_number):
                    self.invitation_builder.set_note_solicit_review_invitation(submission)

                elif super_invitation_name == self.get_solicit_review_approval_id(number=note_number):
                    replyto_note = self.client.get_note(replyto)
                    self.invitation_builder.set_note_solicit_review_approval_invitation(submission, replyto_note, duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))

                elif invitation.id == self.get_revision_id(number=note_number):
                    self.invitation_builder.set_note_revision_invitation(submission)

                elif invitation.id == self.get_public_comment_id(number=note_number):
                    self.invitation_builder.set_note_comment_invitation(submission)

                elif invitation.id == self.get_official_comment_id(number=note_number):
                    a=1

                elif invitation.id == self.get_moderation_id(number=note_number):
                    a=1

                elif invitation.id == self.get_release_comment_id(number=note_number):
                    self.invitation_builder.set_note_release_comment_invitation(submission)

                elif invitation.id == self.get_ae_decision_id(number=note_number):
                    self.invitation_builder.set_note_decision_invitation(submission, duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))

                elif invitation.id == self.get_release_decision_id(number=note_number):
                    self.invitation_builder.set_note_decision_release_invitation(submission)

                elif invitation.id == self.get_decision_approval_id(number=note_number):
                    self.invitation_builder.set_note_decision_approval_invitation(submission, openreview.api.Note(id=replyto), duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))

                elif super_invitation_name == self.get_review_rating_id():
                    self.invitation_builder.set_note_review_rating_invitation(submission, duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))

                elif invitation.id == self.get_camera_ready_revision_id(number=note_number):
                    self.invitation_builder.set_note_camera_ready_revision_invitation(submission, duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))

                elif invitation.id == self.get_camera_ready_verification_id(number=note_number):
                    self.invitation_builder.set_note_camera_ready_verification_invitation(submission, duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))

                elif invitation.id == self.get_authors_deanonymization_id(number=note_number):
                    self.invitation_builder.set_note_authors_deanonymization_invitation(submission)

                elif invitation.id == self.get_reviewer_assignment_id(number=note_number):
                    self.invitation_builder.set_reviewer_assignment_invitation(submission, duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))                    

                elif invitation.id == self.get_ae_recommendation_id(number=note_number):
                    self.invitation_builder.set_ae_recommendation_invitation(submission, duedate = datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))                    
                else:
                    print(f'Builder not found for {invitation.id}')

            else:
                print(f'Name or invitation not found: {name}, {submission}')

    def setup_responsibility_acknowledgement_invitations(self):

        reviewer_invitations = self.client.get_all_invitations(invitation=self.get_reviewer_responsibility_id())

        for invitation in reviewer_invitations:
            tokens = invitation.id.split('/')
            self.invitation_builder.set_single_reviewer_responsibility_invitation(tokens[-3], duedate=datetime.datetime.fromtimestamp(int(invitation.duedate/1000)))
    
    def update_solicit_review(self, note_number, invitation):

        if 'const' not in invitation.edit['note']['forum']:
            return 
        
        updated_edit = {
            "signatures": {
                'param': {
                    "regex": "~.*",
                }
            },
            "readers": [
                "TMLR/Editors_In_Chief",
                f"TMLR/Paper{note_number}/Action_Editors",
                "${2/signatures}"
            ],
            "nonreaders": [
                f"TMLR/Paper{note_number}/Authors"
            ],
            "writers": [
                "TMLR",
                f"TMLR/Paper{note_number}/Action_Editors",
                "${2/signatures}"
            ],  
            "note": {
                "id": {
                    'param': {
                        "withInvitation": invitation.id,
                        "optional": True
                    }
                },
                "forum": invitation.edit['note']['forum']['const'],
                "replyto": invitation.edit['note']['replyto']['const'],
                "ddate": {
                    'param': {
                        "range": [
                        0,
                        9999999999999
                        ],
                        "optional": True,
                        "deletable": True
                    }
                },
                "signatures": ['${3/signatures}'],
                "readers": [
                    "TMLR",
                    f"TMLR/Paper{note_number}/Action_Editors",
                    "${3/signatures}"
                ],
                "nonreaders": [
                    f"TMLR/Paper{note_number}/Authors"
                ],
                "writers": [
                    "TMLR",
                    f"TMLR/Paper{note_number}/Action_Editors",
                    "${3/signatures}"
                ],
                "content": {
                    "solicit": {
                        "order": 1,
                        "value": {
                            'param': {
                                "type": "string",
                                "enum": [
                                "I solicit to review this paper."
                                ],
                                "input": "radio"
                            }
                        }
                    },
                    "comment": {
                        "order": 2,
                        "description": "Explain to the Action Editor for this submission why you believe you are qualified to be a reviewer for this work.",
                        "value": {
                            'param': {
                                "type": "string",
                                "maxLength": 200000,
                                "input": "textarea",
                                "optional": True,
                                "markdown": True
                            }

                        }
                    }
                }
            }
        }
        invitation.edit = updated_edit
        invitation.domain = None
        invitation.invitations = None
        self.invitation_builder.post_invitation_edit(invitation, replacement=True)


    def archive_assignments(self):

        submissions = self.client.get_all_notes(invitation=self.get_author_submission_id())

        ae_assignments = { e['id']['head']: e['values'] for e in self.client.get_grouped_edges(invitation=self.get_ae_assignment_id(), groupby='head')}
        reviewer_assignments = { e['id']['head']: e['values'] for e in self.client.get_grouped_edges(invitation=self.get_reviewer_assignment_id(), groupby='head')}

        ## Archive papers done
        for submission in tqdm(submissions):
            venueid = submission.content['venueid']['value']
            if venueid in [self.accepted_venue_id, self.rejected_venue_id, self.desk_rejected_venue_id, self.withdrawn_venue_id, self.retracted_venue_id]:
                submission_ae_assignments = ae_assignments.get(submission.id, [])
                for ae_assignment in submission_ae_assignments:
                    ae_assignment_edge = openreview.api.Edge.from_json(ae_assignment)
                    archived_edge = openreview.api.Edge(
                        invitation=self.get_ae_assignment_id(archived=True),
                        head=ae_assignment_edge.head,
                        tail=ae_assignment_edge.tail,
                        weight=ae_assignment_edge.weight,
                        label=ae_assignment_edge.label
                    )
                    self.client.post_edge(archived_edge)
                    ## avoid process function execution
                    self.client.delete_edges(invitation=ae_assignment_edge.invitation, head=ae_assignment_edge.head, tail=ae_assignment_edge.tail, soft_delete=True, wait_to_finish=True)

                    
                submission_reviewer_assignments = reviewer_assignments.get(submission.id, [])
                for reviewer_assignment in submission_reviewer_assignments:
                    reviewer_assignment_edge = openreview.api.Edge.from_json(reviewer_assignment)
                    archived_edge = openreview.api.Edge(
                        invitation=self.get_reviewer_assignment_id(archived=True),
                        head=reviewer_assignment_edge.head,
                        tail=reviewer_assignment_edge.tail,
                        weight=reviewer_assignment_edge.weight,
                        label=reviewer_assignment_edge.label,
                        signatures=[self.venue_id]
                    )
                    self.client.post_edge(archived_edge)
                    ## avoid process function execution
                    self.client.delete_edges(invitation=reviewer_assignment_edge.invitation, head=reviewer_assignment_edge.head, tail=reviewer_assignment_edge.tail, soft_delete=True, wait_to_finish=True)
                    