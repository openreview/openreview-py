from .. import openreview
from . import group
from .invitation import InvitationBuilder
from .recruitment import Recruitment
from .assignment import Assignment

import re
import csv
import datetime
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
        self.decision_pending_venue_id = f'{venue_id}/Decision_Pending'
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
    
    def get_message_sender(self):
        return {
            'fromName': self.short_name,
            'fromEmail': f'{self.short_name.replace(" ", "").lower()}-notifications@openreview.net'
        }    

    def get_editors_in_chief_id(self):
        return f'{self.venue_id}/{self.editors_in_chief_name}'

    def get_publication_chairs_id(self):
        return f'{self.venue_id}/Publication_Chairs'
    
    def get_action_editors_archived_id(self):
        return f'{self.get_action_editors_id()}/Archived'    

    def get_action_editors_id(self, number=None, anon=False):
        return self.__get_group_id('Action_Editor_' if anon else self.action_editors_name, number)

    def get_reviewers_id(self, number=None, anon=False):
        return self.__get_group_id('Reviewer_' if anon else self.reviewers_name, number)

    def get_reviewers_archived_id(self):
        return f'{self.get_reviewers_id()}/Archived' 
    
    def get_reviewers_reported_id(self):
        return self.get_reviewers_id() + '/Reported'
    
    def get_reviewers_volunteers_id(self):
        return f'{self.get_reviewers_id()}/Volunteers'     
    
    def get_expert_reviewers_id(self):
        return self.__get_group_id('Expert_Reviewers')
    
    def get_expert_reviewers_member_id(self):
        return self.__get_invitation_id(name='Member', prefix=self.get_expert_reviewers_id())

    def get_archived_reviewers_member_id(self):
        return self.__get_invitation_id(name='Member', prefix=self.get_reviewers_archived_id())        

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
    
    def get_event_certification_id(self):
        return self.__get_invitation_id(name='Event_Certification')

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
    
    def get_ae_expertise_selection_id(self):
        return self.__get_invitation_id(name='Expertise_Selection', prefix=self.get_action_editors_id())

    def get_decision_approval_id(self, number=None):
        return self.__get_invitation_id(name='Decision_Approval', number=number)

    def get_review_id(self, number=None):
        return self.__get_invitation_id(name='Review', number=number)

    def get_review_rating_id(self, signature=None):
        return self.__get_invitation_id(name='Rating', prefix=signature)
    
    def get_review_rating_enabling_id(self, number=None):
        return self.__get_invitation_id(name='Review_Rating_Enabling', number=number)

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
    
    def get_reviewer_invite_assignment_id(self):
        return self.__get_invitation_id(name='Invite_Assignment', prefix=self.get_reviewers_id())

    def get_reviewer_assignment_recruitment_id(self):
        return self.__get_invitation_id(name='Assignment_Recruitment', prefix=self.get_reviewers_id())        

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
    
    def get_reviewer_expertise_selection_id(self):
        return self.__get_invitation_id(name='Expertise_Selection', prefix=self.get_reviewers_id())
    
    def get_reviewers_message_id(self, number=None):
        return self.__get_invitation_id(name='Message', number=number)

    def get_expertise_selection_id(self, committee_id):
        return self.__get_invitation_id(name='Expertise_Selection', prefix=committee_id)

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
    
    def get_preferred_emails_invitation_id(self):
        return self.__get_invitation_id(name='Preferred_Emails')

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

    def get_expertise_model(self):
        return self.settings.get('expertise_model', 'specter+mfr')
    
    def get_ae_recommendation_period_length(self):
        return self.settings.get('ae_recommendation_period', 1)
    
    def get_under_review_approval_period_length(self):
        return self.settings.get('under_review_approval_period', 1)
    
    def get_reviewer_assignment_period_length(self):
        return self.settings.get('reviewer_assignment_period', 1)
    
    def get_camera_ready_period_length(self):
        return self.settings.get('camera_ready_period', 4)
    
    def get_camera_ready_verification_period_length(self):
        return self.settings.get('camera_ready_verification_period', 1)
    
    def get_recommendation_period_length(self):
        return self.settings.get('recommendation_period', 2)
    
    def get_decision_period_length(self):
        return self.settings.get('decision_period', 1)
    
    def get_discussion_period_length(self):
        return self.settings.get('discussion_period', 2)

    def get_review_period_length(self, note=None):
        review_period = self.settings.get('review_period', 2)
        if note and 'submission_length' in note.content:
            if 'Regular submission' in note.content['submission_length']['value']:
                return review_period ## weeks
            if 'Long submission' in note.content['submission_length']['value']:
                return 2 * review_period ## weeks
        return review_period ## weeks
    
    def get_expert_reviewer_certification(self):
        return "Expert Certification"

    def is_active_submission(self, submission):
        venue_id = submission.content.get('venueid', {}).get('value')
        return venue_id in [self.submitted_venue_id, self.under_review_venue_id, self.assigning_AE_venue_id, self.assigned_AE_venue_id]
    
    def setup(self, support_role, editors=[], assignment_delay=5):
        self.invitation_builder.set_meta_invitation()
        self.group_builder.set_groups(support_role, editors)
        self.invitation_builder.set_invitations(assignment_delay)
        self.group_builder.set_group_variable(self.get_action_editors_id(), 'REVIEWER_REPORT_ID', self.get_reviewer_report_form())
        self.group_builder.set_group_variable(self.get_action_editors_id() + '/Archived', 'REVIEWER_REPORT_ID', self.get_reviewer_report_form())
        self.group_builder.set_group_variable(self.get_editors_in_chief_id(), 'REVIEWER_REPORT_ID', self.get_reviewer_report_form())
        self.group_builder.set_group_variable(self.get_editors_in_chief_id(), 'REVIEWER_ACKOWNLEDGEMENT_RESPONSIBILITY_ID', self.get_acknowledgement_responsibility_form())

    def setup_ae_matching(self, label):
        self.assignment.setup_ae_matching(label)

    ## Same interface like Conference and Venue class
    def set_assignments(self, assignment_title, committee_id=None, overwrite=True, enable_reviewer_reassignment=True):
        self.assignment.set_ae_assignments(assignment_title)
    
    def unset_assignments(self, assignment_title, committee_id=None):
        self.assignment.unset_ae_assignments(assignment_title)

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
        self.invitation_builder.set_note_comment_invitation(note, public=False)
        self.invitation_builder.set_note_reviewer_message_invitation(note)
        self.assignment.request_expertise(note, self.get_action_editors_id())
        self.assignment.request_expertise(note, self.get_reviewers_id())
        print('Finished setup author submission data.')
        

    def setup_under_review_submission(self, note):
        self.invitation_builder.set_note_review_invitation(note, self.get_due_date(weeks = self.get_review_period_length(note)))
        self.invitation_builder.set_note_solicit_review_invitation(note)
        self.invitation_builder.set_note_comment_invitation(note)
        self.invitation_builder.release_submission_history(note)
        self.invitation_builder.expire_invitation(self.get_review_approval_id(note.number))

    def is_submission_public(self):
        return self.settings.get('submission_public', True)

    def get_issn(self):
        return self.settings.get('issn', None)
    
    def get_submission_license(self):
        return self.settings.get('submission_license', 'CC BY-SA 4.0')
    
    def get_expertise_model(self):
        return self.settings.get('expertise_model', 'specter+mfr')

    def are_authors_anonymous(self):
        return self.settings.get('author_anonymity', True)
    
    def release_submission_after_acceptance(self):
        return self.settings.get('release_submission_after_acceptance', True)
    
    def should_eic_submission_notification(self):
        return self.settings.get('eic_submission_notification', False)
    
    def should_skip_ac_recommendation(self):
        return self.settings.get('skip_ac_recommendation', False)
    
    def should_skip_reviewer_responsibility_acknowledgement(self):
        return self.settings.get('skip_reviewer_responsibility_acknowledgement', False) 

    def should_skip_reviewer_assignment_acknowledgement(self):
        return self.settings.get('skip_reviewer_assignment_acknowledgement', False)        

    def should_skip_camera_ready_revision(self):
        return self.settings.get('skip_camera_ready_revision', False)

    def get_certifications(self):
        return self.settings.get('certifications', []) 

    def get_eic_certifications(self):
        return self.settings.get('eic_certifications', []) 

    def get_event_certifications(self):
        return self.settings.get('event_certifications', [])                

    def get_submission_length(self):
        return self.settings.get('submission_length', [])
    
    def get_website_url(self, key):
        return self.settings.get('website_urls', {}).get(key)
    
    def get_editors_in_chief_email(self):
        return self.settings.get('editors_email', self.contact_info)

    def should_show_conflict_details(self):
        return self.settings.get('show_conflict_details', False)

    def has_publication_chairs(self):
        return self.settings.get('has_publication_chairs', False)
    
    def has_archived_action_editors(self):
        return self.settings.get('archived_action_editors', False)

    def has_archived_reviewers(self):
        return self.settings.get('archived_reviewers', False)

    def has_expert_reviewers(self):
        return self.settings.get('expert_reviewers', False) 

    def has_external_reviewers(self):
        return self.settings.get('external_reviewers', True)            

    def get_number_of_reviewers(self):
        return self.settings.get('number_of_reviewers', 3)

    def get_reviewers_max_papers(self):
        return self.settings.get('reviewers_max_papers', 6)

    def get_ae_max_papers(self):
        return self.settings.get('action_editors_max_papers', 12)

    def get_submission_additional_fields(self):
        return self.settings.get('submission_additional_fields', {})
    
    def get_review_additional_fields(self):
        return self.settings.get('review_additional_fields', {})
    
    def get_official_recommendation_additional_fields(self):
        return self.settings.get('official_recommendation_additional_fields', {}) 

    def get_decision_additional_fields(self):
        return self.settings.get('decision_additional_fields', {})        

    def should_release_authors(self):
        return self.is_submission_public() and self.are_authors_anonymous()

    def get_author_submission_readers(self, number):
        if self.are_authors_anonymous():
            return [ self.venue_id, self.get_action_editors_id(number), self.get_authors_id(number)]
    
    def get_under_review_submission_readers(self, number):
        if self.is_submission_public():
            return ['everyone']
        return [self.venue_id, self.get_action_editors_id(), self.get_reviewers_id(number), self.get_authors_id(number)]

    def get_release_review_readers(self, number):
        if self.is_submission_public():
            return ['everyone']
        return [self.get_editors_in_chief_id(), self.get_action_editors_id(), self.get_reviewers_id(number), self.get_authors_id(number)]        
    
    def get_release_decision_readers(self, number):
        if self.is_submission_public():
            return ['everyone']
        return [self.get_editors_in_chief_id(), self.get_action_editors_id(), self.get_reviewers_id(number), self.get_authors_id(number)]        

    def get_release_authors_readers(self, number):
        if self.is_submission_public() or self.release_submission_after_acceptance():
            return ['everyone']
        return [self.get_editors_in_chief_id(), self.get_action_editors_id(), self.get_authors_id(number)]          

    def get_official_comment_readers(self, number):
        readers = []
        if self.is_submission_public():
            readers.append('everyone')

        readers.append(self.get_editors_in_chief_id())

        if not self.is_submission_public():
            readers.append(self.get_action_editors_id())
            
        return readers + [self.get_action_editors_id(number), 
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
        year = datetime.datetime.utcnow().year

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

            year = datetime.datetime.fromtimestamp(note.pdate/1000).year if note.pdate else year
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
                    signature_members = signature_members  + self.client.get_group(signature['id']).members
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

        if note.id == forum.id:
            action = 'posted' if edit.tcdate == edit.tmdate else 'edited'
        else:
            action = 'posted' if note.tcdate == note.tmdate else 'edited'

        readers = note.readers
        nonreaders = [edit.tauthor]
        if note.nonreaders:
            nonreaders += note.nonreaders
        formatted_invitation = edit.invitation.split('/-/')[1].replace('_', ' ')
        lower_formatted_invitation = formatted_invitation.lower()
        before_invitation = 'An' if lower_formatted_invitation[0] in vowels else 'A'
        is_public = 'everyone' in readers

        subject = f'''[{self.short_name}] {formatted_invitation} {action} on submission {forum.number}: {forum.content['title']['value']}'''

        formatted_content = f'''
Submission: {forum.content['title']['value']}
'''
        for field in content_fields:
            formatted_field = field[0].upper() + field.replace('_', ' ')[1:]
            formatted_content = formatted_content + f'{formatted_field}: {note.content.get(field, {}).get("value", "")}' + '\n'

        content = f'''{formatted_content}
To view the {lower_formatted_invitation}, click here: https://openreview.net/forum?id={note.forum}&noteId={note.id}'''

        ## Notify author of the note
        if action == 'posted' and self.get_editors_in_chief_id() not in note.signatures:
            message = f'''Hi {{{{fullname}}}},

Your {lower_formatted_invitation} on a submission has been {action}
{content}
'''
            self.client.post_message(invitation=self.get_meta_invitation_id(), recipients=[edit.tauthor], subject=subject, message=message, replyTo=self.contact_info, signature=self.venue_id, sender=self.get_message_sender())

        ## Notify authors
        if is_public or self.get_authors_id(number=forum.number) in readers:
            message = f'''Hi {{{{fullname}}}},

{before_invitation} {lower_formatted_invitation} has been {action} on your submission.
{content}
'''
            self.client.post_message(invitation=self.get_meta_invitation_id(), recipients=[self.get_authors_id(number=forum.number)], subject=subject, message=message, ignoreRecipients=nonreaders, replyTo=self.contact_info, signature=self.venue_id, sender=self.get_message_sender())

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
            self.client.post_message(invitation=self.get_meta_invitation_id(), recipients=reviewer_recipients, subject=subject, message=message, ignoreRecipients=nonreaders, replyTo=self.contact_info, signature=self.venue_id, sender=self.get_message_sender())


        ## Notify action editors
        if is_public or self.get_action_editors_id(number=forum.number) in readers or self.get_action_editors_id() in readers:
            message = f'''Hi {{{{fullname}}}},

{before_invitation} {lower_formatted_invitation} has been {action} on a submission for which you are an Action Editor.
{content}
'''
            self.client.post_message(invitation=self.get_meta_invitation_id(), recipients=[self.get_action_editors_id(number=forum.number)], subject=subject, message=message, ignoreRecipients=nonreaders, replyTo=self.contact_info, signature=self.venue_id, sender=self.get_message_sender())


        if self.get_editors_in_chief_id() in readers and len(readers) == 2 and 'comment' in lower_formatted_invitation:
            message = f'''Hi {{{{fullname}}}},

{before_invitation} {lower_formatted_invitation} has been {action} on a submission for which you are serving as Editor-In-Chief.
{content}
'''
            self.client.post_message(invitation=self.get_meta_invitation_id(), recipients=[self.get_editors_in_chief_id()], subject=subject, message=message, ignoreRecipients=nonreaders, replyTo=self.contact_info, signature=self.venue_id, sender=self.get_message_sender())

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
                                'deletable': True,
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
                        cdate=ae_assignment_edge.cdate,
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
                        cdate=reviewer_assignment_edge.cdate,
                        head=reviewer_assignment_edge.head,
                        tail=reviewer_assignment_edge.tail,
                        weight=reviewer_assignment_edge.weight,
                        label=reviewer_assignment_edge.label,
                        signatures=[self.venue_id]
                    )
                    self.client.post_edge(archived_edge)
                    ## avoid process function execution
                    self.client.delete_edges(invitation=reviewer_assignment_edge.invitation, head=reviewer_assignment_edge.head, tail=reviewer_assignment_edge.tail, soft_delete=True, wait_to_finish=True)

    @classmethod
    def update_affinity_scores(Journal, client, support_group_id='OpenReview.net/Support'):

        journal_requests = client.get_all_notes(invitation=f'{support_group_id}/-/Journal_Request')

        for journal_request in tqdm(journal_requests):

            journal = openreview.journal.JournalRequest.get_journal(client, journal_request.id, setup=False)
            print('Check venue', journal.venue_id)

            author_group = client.get_group(journal.get_authors_id())

            ## Get all the submissions that don't have a decision affinity scores
            submissions = journal.client.get_all_notes(invitation=journal.get_author_submission_id())
            active_submissions = [s for s in submissions if s.content['venueid']['value'] in [journal.submitted_venue_id, journal.assigning_AE_venue_id, journal.assigned_AE_venue_id]]

            ## For each submission check the status of the expertise task
            for submission in tqdm(active_submissions):
                ae_score_count = journal.client.get_edges_count(invitation=journal.get_ae_affinity_score_id(), head=submission.id)
                if ae_score_count == 0:
                    print('Submission with no AE scores', submission.id, submission.number)
                    result = journal.client.get_expertise_status(paper_id=submission.id, group_id=journal.get_action_editors_id())
                    job_status = result['results'][0] if (result and result['results']) else None
                    if job_status and job_status['status'] == 'Completed':
                        print('Job Completed')
                        journal.assignment.setup_ae_assignment(submission, job_status['jobId'])
                        if not journal.should_skip_ac_recommendation():
                            print('Setup AE recommendation')
                            invitation = openreview.tools.get_invitation(client, journal.get_ae_recommendation_id(number=submission.number))
                            if invitation is None:
                                journal.invitation_builder.set_ae_recommendation_invitation(submission, journal.get_due_date(weeks = journal.get_ae_recommendation_period_length()))
                                ## send email to authors
                                print('Send email to authors')
                                message=author_group.content['ae_recommendation_email_template_script']['value'].format(
                                    venue_id=journal.venue_id,
                                    short_name=journal.short_name,
                                    submission_id=submission.id,
                                    submission_number=submission.number,
                                    submission_title=submission.content['title']['value'],
                                    website=journal.website,
                                    contact_info=journal.contact_info,
                                    invitation_url=f'https://openreview.net/invitation?id={journal.get_ae_recommendation_id(number=submission.number)}'
                                )                                
                                journal.client.post_message(
                                    invitation=journal.get_meta_invitation_id(),
                                    recipients=submission.signatures,
                                    subject=f'[{journal.short_name}] Suggest candidate Action Editor for your new {journal.short_name} submission',
                                    message=message,
                                    replyTo=journal.contact_info,
                                    signature=journal.venue_id,
                                    sender=journal.get_message_sender()
                                )


                reviewers_score_count = journal.client.get_edges_count(invitation=journal.get_reviewer_affinity_score_id(), head=submission.id)
                if reviewers_score_count == 0:
                    print('Submission with no reviewers scores', submission.id, submission.number)
                    result = journal.client.get_expertise_status(paper_id=submission.id, group_id=journal.get_reviewers_id())
                    job_status = result['results'][0] if (result and result['results']) else None
                    if job_status and job_status['status'] == 'Completed':
                        print('Job Completed')
                        journal.assignment.setup_reviewer_assignment(submission, job_status['jobId'])

    def run_reviewer_stats(self, end_cdate, output_file, start_cdate=None):

        invitations_by_id = { i.id: i for i in self.client.get_all_invitations(prefix=self.venue_id, expired=True)}
        submission_by_id = { n.id: n for n in self.client.get_all_notes(invitation=self.get_author_submission_id(), details='replies')}
        archived_assignments_by_reviewers = { e['id']['tail']: e['values']for e in self.client.get_grouped_edges(invitation=self.get_reviewer_assignment_id(archived=True), groupby='tail')}
        assignments_by_reviewers = { e['id']['tail']: e['values']for e in self.client.get_grouped_edges(invitation=self.get_reviewer_assignment_id(), groupby='tail')}
        availability_by_reviewer = { e['id']['tail']: e['values'][0] for e in self.client.get_grouped_edges(invitation=self.get_reviewer_availability_id(), groupby='tail')}

        report_by_reviewer = {}
        reports = self.client.get_all_notes(invitation=self.get_reviewer_report_id())
        for report in reports:
            reviewer_id = report.content['reviewer_id']['value']
            if reviewer_id not in report_by_reviewer:
                report_by_reviewer[reviewer_id] = []
            
            report_by_reviewer[reviewer_id].append(report.content['report_reason']['value'])

        rating_map = {
            "Exceeds expectations": 3,
            "Meets expectations": 2,
            "Falls below expectations": 1
        }

        def get_responsibility_invitation(profile):
            for name in profile.content['names']:
                if 'username' in name:
                    ack_invitation = invitations_by_id.get(self.get_reviewer_responsibility_id(name["username"]))
                    if ack_invitation:
                        return ack_invitation
                    
            for email in profile.content['emailsConfirmed']:
                ack_invitation = invitations_by_id.get(self.get_reviewer_responsibility_id(email))
                if ack_invitation:
                    return ack_invitation
                
            print('no responsibility invitation for', profile.id)

        def get_ack_invitation(submission_number, profile):
            for name in profile.content['names']:
                if 'username' in name:
                    ack_invitation = invitations_by_id.get(self.get_reviewer_assignment_acknowledgement_id(submission_number, name["username"]))
                    if ack_invitation:
                        return ack_invitation
                    
            for email in profile.content['emailsConfirmed']:
                ack_invitation = invitations_by_id.get(self.get_reviewer_assignment_acknowledgement_id(submission_number, email))
                if ack_invitation:
                    return ack_invitation
                
            print('no ack invitation for', submission_number, profile.id)

        def get_reviewer_stats(reviewer, assignment):
            
            submission = submission_by_id[assignment['head']]
            if start_cdate and submission.cdate < start_cdate:
                return None
            if submission.cdate > end_cdate:
                return None

            ack_invitation = get_ack_invitation(submission.number, reviewer)
            
            anon_group = [g for g in self.client.get_groups(prefix=self.get_reviewers_id(number=submission.number, anon=True), member=reviewer.id)][0]
            acks = [r for r in submission.details['replies'] if r['invitations'][0] == ack_invitation.id]
            reviews = [r for r in submission.details['replies'] if '/-/Review' in r['invitations'][0] and anon_group.id in r['signatures']]
            recommendations = [r for r in submission.details['replies'] if '/-/Official_Recommendation' in r['invitations'][0] and anon_group.id in r['signatures']]
            comments = [r for r in submission.details['replies'] if '/-/Official_Comment' in r['invitations'][0] and anon_group.id in r['signatures']]
            ratings = [r for r in submission.details['replies'] if r['invitations'][0] == f'{anon_group.id}/-/Rating']
            
            assignment_cdate = datetime.datetime.fromtimestamp(assignment['cdate']/1000)

            ack_duedate = datetime.datetime.fromtimestamp(ack_invitation.duedate/1000)
            
            ack_days = None
            ack_deadline = None
            if acks:
                ack = acks[0]
                ack_tcdate = datetime.datetime.fromtimestamp(ack['tcdate']/1000)
                
                ack_days = (ack_tcdate - assignment_cdate).days
                ack_deadline = (ack_tcdate - ack_duedate).days
                
            review_days = None
            review_deadline = None
            review_length = 0
            review_complete = 0

            review_invitation = invitations_by_id[self.get_review_id(number=submission.number)]
            review_duedate = datetime.datetime.fromtimestamp(review_invitation.duedate/1000)

            if reviews:
                review = reviews[0]
                review_tcdate = datetime.datetime.fromtimestamp(review['tcdate']/1000)

                review_days = (review_tcdate - assignment_cdate).days
                review_deadline = (review_tcdate - review_duedate).days
                review_length = len(review['content'].get('summary_of_contributions', {}).get('value', '')) + len(review['content'].get('strengths_and_weaknesses', {}).get('value', '')) + len(review['content'].get('requested_changes', {}).get('value', '')) + len(review['content'].get('broader_impact_concerns', {}).get('value', ''))

                review_complete += 1

            recommendation_invitation = invitations_by_id.get(self.get_reviewer_recommendation_id(number=submission.number))
            recommendation_days = None
            recommendation_deadline = None
            if recommendation_invitation:
                recommendation_duedate = datetime.datetime.fromtimestamp(recommendation_invitation.duedate/1000)
                recommendation_cdate = datetime.datetime.fromtimestamp(recommendation_invitation.cdate/1000)

                if recommendations:
                    recommendation = recommendations[0]
                    recommendation_tcdate = datetime.datetime.fromtimestamp(recommendation['tcdate']/1000)

                    recommendation_days = (recommendation_tcdate - recommendation_cdate).days
                    recommendation_deadline = (recommendation_tcdate - recommendation_duedate).days

            comment_count = 0
            comment_length = 0
            for comment in comments:
                comment_count += 1
                comment_length += len(comment['content']['comment']['value'])
                
            review_rating = None
            if ratings:
                review_rating = rating_map[ratings[0]['content']['rating']['value']]

            return {
                'assigment_ack_days': ack_days,
                'assignment_ack_deadline': ack_deadline,
                'review_days': review_days,
                'review_deadline': review_deadline,
                'review_length': review_length,
                'review_complete': review_complete,
                'comment_count': comment_count,
                'comment_length': comment_length,
                'recommendation_days': recommendation_days,
                'recommendation_deadline': recommendation_deadline,
                'review_rating': review_rating
            }       


        rows = []
        reviewers = openreview.tools.get_profiles(self.client, self.client.get_group(self.get_reviewers_id()).members)
        for reviewer in reviewers:
            availability = None
            availability_cdate = None
            assignment_responsability_days = None ## time of first assignment - time of responsability posted
            assignment_responsability_deadline = None ## time of responsability posted - time of responsability deadline
            assigment_ack_days = [] ## time of assignment - time of ack posted
            assignment_ack_deadline = [] ## time of ack posted - ack deadline
            review_days = [] ## time of review posted - time of assignment
            review_deadline = [] ## time of review posted - time review deadline
            review_count = 0 ## sum of assignments
            review_complete = 0 ## sum of review posted
            review_length = [] ## sum of all the field lengths
            comment_length = [] ## sum of all the field lengths
            comment_count = [] ## sum of comment count
            recommendation_days = [] ## time of recommendation.cdate - time of recommendation posted
            recommendation_deadline = [] ## time of recommendation posted - time recommendation deadline
            review_rating = [] ## review rating number for each review
            review_rating_average = 0 ## avg review_rating
            reports = report_by_reviewer.get(reviewer.id, []) ## note id of review reports

            availability_edge = availability_by_reviewer.get(reviewer.id, None)
            if availability_edge:
                availability = availability_edge['label']
                availability_cdate = datetime.datetime.fromtimestamp(availability_edge['cdate']/1000)    
            
            responsibility_invitation = get_responsibility_invitation(reviewer)
            if responsibility_invitation:
                responsibility_duedate = datetime.datetime.fromtimestamp(responsibility_invitation.duedate/1000)
                responsibility_cdate = datetime.datetime.fromtimestamp(responsibility_invitation.cdate/1000)
                response = self.client.get_notes(invitation=responsibility_invitation.id)
                if response:
                    responsibility_note = response[0]
                    responsibility_tcdate = datetime.datetime.fromtimestamp(responsibility_note.tcdate/1000)
                
                assignment_responsability_days = (responsibility_tcdate - responsibility_cdate).days
                assignment_responsability_deadline = (responsibility_tcdate - responsibility_duedate).days

            
            archived_assignments = archived_assignments_by_reviewers.get(reviewer.id, [])
            
            for assignment in archived_assignments:
                stats = get_reviewer_stats(reviewer, assignment)
                if stats:
                    assigment_ack_days.append(stats['assigment_ack_days'])
                    assignment_ack_deadline.append(stats['assignment_ack_deadline'])
                    review_days.append(stats['review_days'])
                    review_deadline.append(stats['review_deadline'])
                    review_length.append(stats['review_length'])
                    review_complete += stats['review_complete']
                    comment_count.append(stats['comment_count'])
                    comment_length.append(stats['comment_length'])
                    recommendation_days.append(stats['recommendation_days'])
                    recommendation_deadline.append(stats['recommendation_deadline'])
                    if stats['review_rating']:
                        review_rating.append(stats['review_rating'])
                    review_count += 1
                                         
            assignments = assignments_by_reviewers.get(reviewer.id, [])
            
            for assignment in assignments:
                stats = get_reviewer_stats(reviewer, assignment)
                if stats:
                    assigment_ack_days.append(stats['assigment_ack_days'])
                    assignment_ack_deadline.append(stats['assignment_ack_deadline'])
                    review_days.append(stats['review_days'])
                    review_deadline.append(stats['review_deadline'])
                    review_length.append(stats['review_length'])
                    review_complete += stats['review_complete']
                    comment_count.append(stats['comment_count'])
                    comment_length.append(stats['comment_length'])
                    recommendation_days.append(stats['recommendation_days'])
                    recommendation_deadline.append(stats['recommendation_deadline'])
                    if stats['review_rating']:
                        review_rating.append(stats['review_rating'])
                    review_count += 1

            review_rating_average = sum(review_rating) / len(review_rating) if review_rating else 0

            rows.append([
                reviewer.id,
                availability,
                availability_cdate,
                assignment_responsability_days,
                assignment_responsability_deadline,
                assigment_ack_days,
                assignment_ack_deadline,
                review_count,
                review_complete,
                review_length,
                review_days,
                review_deadline,
                recommendation_days,
                recommendation_deadline,
                comment_count,
                comment_length,
                review_rating,
                review_rating_average,
                reports

            ])

            with open(output_file, 'w') as file_handle:
                writer = csv.writer(file_handle)
                writer.writerow([
                    'Reviewer ID',
                    'Availability',
                    'Availability date',
                    'Responsibility days',
                    'Responsibility deadline',
                    'ACK days',
                    'ACK deadline',
                    'Review count',
                    'Review complete',
                    'Review length',
                    'Review days',
                    'Review deadline',
                    'Recommendation days',
                    'Recommendation deadline',
                    'Comment count',
                    'Comment length',
                    'Review rating',
                    'Review rating average',
                    'Reviewer reports'
                ])
                for row in rows:
                    writer.writerow(row)                                


    def run_action_editors_stats(self, end_cdate, output_file, start_cdate=None):

        invitations_by_id = { i.id: i for i in self.client.get_all_invitations(prefix=self.venue_id, expired=True)}
        submission_by_id = { n.id: n for n in self.client.get_all_notes(invitation=self.get_author_submission_id(), details='replies')}
        archived_assignments_by_action_editors = { e['id']['tail']: e['values']for e in self.client.get_grouped_edges(invitation=self.get_ae_assignment_id(archived=True), groupby='tail')}
        assignments_by_action_editors = { e['id']['tail']: e['values']for e in self.client.get_grouped_edges(invitation=self.get_ae_assignment_id(), groupby='tail')}
        availability_by_action_editors = { e['id']['tail']: e['values'][0] for e in self.client.get_grouped_edges(invitation=self.get_ae_availability_id(), groupby='tail')}
        custom_quota_by_action_editors = { e['id']['tail']: e['values'][0]['weight'] for e in self.client.get_grouped_edges(invitation=self.get_ae_custom_max_papers_id(), groupby='tail')}
        recruitment_notes = self.client.get_all_notes(forum=self.request_form_id)
        recruitment_note_by_signature = {}

        for note in recruitment_notes:
            if note.signatures[0] not in recruitment_note_by_signature:
                recruitment_note_by_signature[note.signatures[0]] = []
            recruitment_note_by_signature[note.signatures[0]].append(note)
        
        def get_recruited_reviewers(profile):
            invited_reviewer_emails = []
            for name in profile.content['names']:
                if 'username' in name:
                    ae_recruitment_notes = recruitment_note_by_signature.get(name["username"], [])
                    for note in ae_recruitment_notes:
                        if 'invitee_email' in note.content:
                            invited_reviewer_emails.append(note.content['invitee_email']['value'])
            return invited_reviewer_emails

        def get_action_editor_stats(action_editor, assignment):

            submission = submission_by_id[assignment['head']]
            if start_cdate and submission.cdate < start_cdate:
                return None            
            if submission.cdate > end_cdate:
                return None

            anon_group = [g for g in self.client.get_groups(prefix=self.get_action_editors_id(number=submission.number), member=action_editor.id)][0]
            review_approvals = [r for r in submission.details['replies'] if self.get_review_approval_id(number=submission.number) in r['invitations']]
            comments = [r for r in submission.details['replies'] if self.get_official_comment_id(number=submission.number) in r['invitations'] and anon_group.id in r['signatures']]
            decisions = [r for r in submission.details['replies'] if self.get_ae_decision_id(number=submission.number) in r['invitations']]
            
            assignment_cdate = datetime.datetime.fromtimestamp(assignment['cdate']/1000)

            review_approval_days = None
            review_approval_deadline = None
            review_approval_invitation = invitations_by_id[self.get_review_approval_id(number=submission.number)]
            review_approval_duedate = datetime.datetime.fromtimestamp(review_approval_invitation.duedate/1000)

            if review_approvals:
                review_approval = review_approvals[0]
                review_approval_tcdate = datetime.datetime.fromtimestamp(review_approval['tcdate']/1000)
                
                review_approval_days = (review_approval_tcdate - assignment_cdate).days
                review_approval_deadline = (review_approval_tcdate - review_approval_duedate).days
                
            decision_days = None
            decision_deadline = None
            decision_length = 0
            accept_count = 0 
            accept_revision_count = 0 
            reject_count = 0            

            decision_invitation = invitations_by_id.get(self.get_ae_decision_id(number=submission.number))
            if decision_invitation:
                decision_duedate = datetime.datetime.fromtimestamp(decision_invitation.duedate/1000)
                decision_cdate = datetime.datetime.fromtimestamp(decision_invitation.cdate/1000)

                if decisions:
                    decision = decisions[0]
                    decision_tcdate = datetime.datetime.fromtimestamp(decision['tcdate']/1000)

                    decision_days = (decision_tcdate - decision_cdate).days
                    decision_deadline = (decision_tcdate - decision_duedate).days
                    decision_length = len(decision['content'].get('claims_and_evidence', {}).get('value', '')) + len(decision['content'].get('audience', {}).get('value', '')) + len(decision['content'].get('comment', {}).get('value', ''))
                    accept_count = 1 if decision['content']['recommendation']['value'] == 'Accept as is' else 0
                    accept_revision_count = 1 if decision['content']['recommendation']['value'] == 'Accept with minor revision' else 0
                    reject_count = 1 if decision['content']['recommendation']['value'] == 'Reject' else 0
            
            comment_count = 0
            comment_length = 0
            for comment in comments:
                comment_count += 1
                comment_length += len(comment['content']['comment']['value'])
                
            return {
                'review_approval_days': review_approval_days,
                'review_approval_deadline': review_approval_deadline,
                'decision_days': decision_days,
                'decision_deadline': decision_deadline,
                'decision_length': decision_length,
                'accept_count': accept_count,
                'accept_revision_count': accept_revision_count,
                'reject_count': reject_count,
                'comment_count': comment_count,
                'comment_length': comment_length,
            }       


        rows = []
        action_editors = openreview.tools.get_profiles(self.client, self.client.get_group(self.get_action_editors_id()).members)
        for action_editor in action_editors:
            availability = None
            availability_cdate = None
            review_approval_days = [] 
            review_approval_deadline = [] 
            decision_days = [] 
            decision_deadline = [] 
            decision_length = []
            paper_count = 0 
            accept_count = 0 
            accept_revision_count = 0 
            reject_count = 0 
            comment_length = [] 
            comment_count = [] 
            recruited_reviewers = get_recruited_reviewers(action_editor) 
            last_time_assignment = 0
            current_custom_max_quota = custom_quota_by_action_editors.get(action_editor.id, self.get_ae_max_papers())

            availability_edge = availability_by_action_editors.get(action_editor.id, None)
            if availability_edge:
                availability = availability_edge['label']
                availability_cdate = datetime.datetime.fromtimestamp(availability_edge['cdate']/1000)    
            
            archived_assignments = archived_assignments_by_action_editors.get(action_editor.id, [])
            
            for assignment in archived_assignments:
                stats = get_action_editor_stats(action_editor, assignment)
                if stats:
                    review_approval_days.append(stats['review_approval_days'])
                    review_approval_deadline.append(stats['review_approval_deadline'])
                    decision_days.append(stats['decision_days'])
                    decision_deadline.append(stats['decision_deadline'])
                    decision_length.append(stats['decision_length'])
                    comment_count.append(stats['comment_count'])
                    comment_length.append(stats['comment_length'])
                    paper_count += 1
                    accept_count += stats['accept_count']
                    accept_revision_count += stats['accept_revision_count']
                    reject_count += stats['reject_count']

                    if assignment['cdate'] > last_time_assignment:
                        last_time_assignment = assignment['cdate']

                                         
            assignments = assignments_by_action_editors.get(action_editor.id, [])
            
            for assignment in assignments:
                stats = get_action_editor_stats(action_editor, assignment)
                if stats:
                    review_approval_days.append(stats['review_approval_days'])
                    review_approval_deadline.append(stats['review_approval_deadline'])
                    decision_days.append(stats['decision_days'])
                    decision_deadline.append(stats['decision_deadline'])
                    decision_length.append(stats['decision_length'])
                    comment_count.append(stats['comment_count'])
                    comment_length.append(stats['comment_length'])
                    paper_count += 1
                    accept_count += stats['accept_count']
                    accept_revision_count += stats['accept_revision_count']
                    reject_count += stats['reject_count']

                    if assignment['cdate'] > last_time_assignment:
                        last_time_assignment = assignment['cdate']                    

            rows.append([
                action_editor.id,
                availability,
                availability_cdate,
                review_approval_days,
                review_approval_deadline,
                decision_days,
                decision_deadline,
                decision_length,
                paper_count,
                accept_count,
                accept_revision_count,
                reject_count,
                comment_length,
                comment_count,
                recruited_reviewers,
                datetime.datetime.fromtimestamp(last_time_assignment/1000) if last_time_assignment else None,
                current_custom_max_quota
            ])

            with open(output_file, 'w') as file_handle:
                writer = csv.writer(file_handle)
                writer.writerow([
                    'Action Editor ID',
                    'Availability',
                    'Availability date',
                    'Review approval days',
                    'Review approval deadline',
                    'Decision days',
                    'Decision deadline',
                    'Decision length',
                    'Paper count',
                    'Accept count',
                    'Accept revision count',
                    'Reject count',
                    'Comment length',
                    'Comment count',
                    'Recruited reviewers count',
                    'Last time assignment',
                    'Current custom max quota'
                ])
                for row in rows:
                    writer.writerow(row)     


    def run_reviewer_unavailability_stats(self):

        unavailable_reviewers = self.client.get_all_edges(invitation=self.get_reviewer_availability_id(), label='Unavailable', head=self.get_reviewers_id())

        reviewers = self.client.get_group(self.get_reviewers_id()).members

        for edge in unavailable_reviewers:
            if edge.tail in reviewers:
                profile = self.client.get_profile(edge.tail)
                tmdate = datetime.datetime.fromtimestamp(edge.tmdate/1000)
                
                messages = self.client.get_messages(subject=f'[{self.short_name}] Consider updating your availability for {self.short_name}', to=profile.get_preferred_email())
                
                if not messages:
                    continue

                unavailable_since_month = tmdate.month
                unavailable_since_year = tmdate.year
                last_message_date = datetime.datetime.fromtimestamp(messages[0]['cdate']/1000)
                
                if last_message_date.month == datetime.datetime.now().month:
                    previous_message_month = last_message_date.month
                    previous_message_year = last_message_date.year
                
                    for message in messages[1:]:
                        message_sent = datetime.datetime.fromtimestamp(message['cdate']/1000)
                        message_month = message_sent.month
                        message_year = message_sent.year
                
                        if previous_message_year == message_year:
                            if (previous_message_month == message_month or previous_message_month == message_month + 1):
                                unavailable_since_month = message_month
                                unavailable_since_year = message_year
                            else:
                                break
                        else:
                            if previous_message_month == 1 and message_month == 12:
                                unavailable_since_month = message_month
                                unavailable_since_year = message_year
                            else:
                                break 
                                
                        previous_message_month = message_month
                        previous_message_year = message_year
                            
                print(f'{[edge.tail, unavailable_since_month, unavailable_since_year]},')
                
    
    def set_impersonators(self, impersonators):
        self.group_builder.set_impersonators(impersonators)

    @classmethod
    def check_new_profiles(Journal, client, support_group_id = 'OpenReview.net/Support'):

        def mark_as_conflict(journal, edge, submission, user_profile):
            edge.label='Conflict Detected'
            edge.tail=user_profile.id
            edge.readers=None
            edge.writers=None
            edge.cdate = None            
            client.post_edge(edge)

            ## Send email to reviewer
            subject=f"[{journal.short_name}] Conflict detected for paper {submission.number}: {submission.content['title']['value']}"
            message =f'''Hi {{{{fullname}}}},
You have accepted the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.

A conflict was detected between you and the submission authors and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

OpenReview Team'''
            response = client.post_message(subject, [edge.tail], message, replyTo=journal.contact_info, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, sender=journal.get_message_sender())

            ## Send email to inviter
            subject=f"[{journal.short_name}] Conflict detected between reviewer {user_profile.get_preferred_name(pretty=True)} and paper {submission.number}: {submission.content['title']['value']}"
            message =f'''Hi {{{{fullname}}}},
A conflict was detected between {user_profile.get_preferred_name(pretty=True)} and the paper {submission.number} and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, edge.signatures, message, replyTo=journal.contact_info, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, sender=journal.get_message_sender())            
        
        def mark_as_accepted(journal, edge, submission, user_profile):

            edge.label='Accepted'
            edge.tail=user_profile.id
            edge.readers=None
            edge.writers=None
            edge.cdate = None
            client.post_edge(edge)

            short_phrase = journal.short_name
            reviewer_name = 'Reviewer' ## add this to the invitation?

            assignment_edges = client.get_edges(invitation=journal.get_reviewer_assignment_id(), head=submission.id, tail=edge.tail)

            if not assignment_edges:
                print('post assignment edge')
                client.post_edge(openreview.api.Edge(
                    invitation=journal.get_reviewer_assignment_id(),
                    head=edge.head,
                    tail=edge.tail,
                    signatures=[journal.venue_id],
                    weight=1
                ))

                instructions=f'Please go to the Tasks page and check your {short_phrase} pending tasks: https://openreview.net/tasks'

                print('send confirmation email')
                ## Send email to reviewer
                subject=f'[{short_phrase}] {reviewer_name} Assignment confirmed for paper {submission.number}: {submission.content["title"]["value"]}'
                message =f'''Hi {{{{fullname}}}},
Thank you for accepting the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.

{instructions}

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team'''

                ## - Send email
                response = client.post_message(subject, [edge.tail], message, replyTo=journal.contact_info, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, sender=journal.get_message_sender())

                ## Send email to inviter
                subject=f'[{short_phrase}] {reviewer_name} {user_profile.get_preferred_name(pretty=True)} signed up and is assigned to paper {submission.number}: {submission.content["title"]["value"]}'
                message =f'''Hi {{{{fullname}}}},
The {reviewer_name} {user_profile.get_preferred_name(pretty=True)} that you invited to review paper {submission.number} has accepted the invitation, signed up and is now assigned to the paper {submission.number}.

OpenReview Team'''

                ## - Send email
                response = client.post_message(subject, edge.signatures, message, replyTo=journal.contact_info, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, sender=journal.get_message_sender())            
        
        journal_requests = client.get_all_notes(invitation=f'{support_group_id}/-/Journal_Request')

        for journal_request in tqdm(journal_requests):

            journal = openreview.journal.JournalRequest.get_journal(client, journal_request.id, setup=False)
            print('Check venue', journal.venue_id)

            invite_assignment_invitation_id = journal.get_reviewer_invite_assignment_id()
            grouped_edges = client.get_grouped_edges(invitation=invite_assignment_invitation_id, label='Pending Sign Up', groupby='tail')
            print('Pending sign up edges found', len(grouped_edges))

            for grouped_edge in grouped_edges:

                tail = grouped_edge['id']['tail']
                profiles=openreview.tools.get_profiles(client, [tail], with_publications=True, with_relations=True)

                if profiles and profiles[0].active:

                    user_profile=profiles[0]
                    print('Profile found for', tail, user_profile.id)

                    edges = grouped_edge['values']

                    for edge in edges:

                        edge = openreview.api.Edge.from_json(edge)
                        submission=client.get_note(id=edge.head)

                        if submission.content['venueid']['value'] == journal.under_review_venue_id:

                            ## Check if there is already an accepted edge for that profile id
                            accepted_edges = client.get_edges(invitation=invite_assignment_invitation_id, label='Accepted', head=submission.id, tail=user_profile.id)

                            if not accepted_edges:
                                ## Check if the user was invited again with a profile id
                                invitation_edges = client.get_edges(invitation=invite_assignment_invitation_id, label='Invitation Sent', head=submission.id, tail=user_profile.id)
                                if invitation_edges:
                                    invitation_edge = invitation_edges[0]
                                    print(f'User invited twice, remove double invitation edge {invitation_edge.id}')
                                    invitation_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
                                    client.post_edge(invitation_edge)

                                ## Check conflicts
                                author_profiles = openreview.tools.get_profiles(client, submission.content['authorids']['value'], with_publications=True, with_relations=True)
                                conflicts=openreview.tools.get_conflicts(author_profiles, user_profile, policy='NeurIPS', n_years=3)

                                if conflicts:
                                    print(f'Conflicts detected for {edge.head} and {user_profile.id}', conflicts)
                                    mark_as_conflict(journal, edge, submission, user_profile)
                                else:
                                    print(f'Mark accepted for {edge.head} and {user_profile.id}')
                                    mark_as_accepted(journal, edge, submission, user_profile)
                                                                                                                                                
                            else:
                                print("user already accepted with another invitation edge", submission.id, user_profile.id)                                

                        else:
                            print(f'submission {submission.id} is not active: {submission.content["venueid"]["value"]}')

                else:
                    print(f'no profile active for {tail}')                                             
        
        return True        
            