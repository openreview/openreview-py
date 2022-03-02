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

    def __init__(self, client, venue_id, secret_key, contact_info, full_name, short_name, website='jmlr.org/tmlr', submission_name='Author_Submission'):

        self.client = client
        self.venue_id = venue_id
        self.secret_key = secret_key
        self.contact_info = contact_info
        self.short_name = short_name
        self.full_name = full_name
        self.website = website
        self.submission_name = submission_name
        self.editors_in_chief_name = 'Editors_In_Chief'
        self.action_editors_name = 'Action_Editors'
        self.reviewers_name = 'Reviewers'
        self.solicit_reviewers_name = 'Solicit_Reviewers'
        self.authors_name = 'Authors'
        self.submission_group_name = 'Paper'
        self.submitted_venue_id = f'{venue_id}/Submitted'
        self.under_review_venue_id = f'{venue_id}/Under_Review'
        self.rejected_venue_id = f'{venue_id}/Rejection'
        self.desk_rejected_venue_id = f'{venue_id}/Desk_Rejection'
        self.withdrawn_venue_id = f'{venue_id}/Withdrawn_Submission'
        self.retracted_venue_id = f'{venue_id}/Retracted_Acceptance'
        self.accepted_venue_id = venue_id
        self.invitation_builder = InvitationBuilder(self)
        self.group_builder = group.GroupBuilder(client)
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

    def get_action_editors_id(self, number=None):
        return self.__get_group_id(self.action_editors_name, number)

    def get_reviewers_id(self, number=None, anon=False):
        return self.__get_group_id('Reviewer_' if anon else self.reviewers_name, number)

    def get_solicit_reviewers_id(self, number=None):
        return self.__get_group_id(self.solicit_reviewers_name, number)

    def get_authors_id(self, number=None):
        return self.__get_group_id(self.authors_name, number)

    def get_meta_invitation_id(self):
        return self.__get_invitation_id(name='Edit')

    def get_review_approval_id(self, number=None):
        return self.__get_invitation_id(name='Review_Approval', number=number)

    def get_withdrawal_id(self, number=None):
        return self.__get_invitation_id(name='Withdrawal', number=number)

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

    def get_desk_rejection_id(self):
        return self.__get_invitation_id(name='Desk_Rejection')

    def get_withdrawn_id(self):
        return self.__get_invitation_id(name='Withdrawn')

    def get_author_submission_id(self):
        return self.__get_invitation_id(name=self.submission_name)

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

    def get_ae_assignment_id(self):
        return self.__get_invitation_id(name='Assignment', prefix=self.get_action_editors_id())

    def get_ae_recommendation_id(self, number=None):
        return self.__get_invitation_id(name='Recommendation', prefix=self.get_action_editors_id(number=number))

    def get_ae_custom_max_papers_id(self, number=None):
        return self.__get_invitation_id(name='Custom_Max_Papers', prefix=self.get_action_editors_id(number=number))

    def get_decision_approval_id(self, number=None):
        return self.__get_invitation_id(name='Decision_Approval', number=number)

    def get_review_id(self, number=None):
        return self.__get_invitation_id(name='Review', number=number)

    def get_review_rating_id(self, signature):
        return self.__get_invitation_id(name='Rating', prefix=signature)

    def get_acceptance_id(self):
        return self.__get_invitation_id(name='Acceptance')

    def get_rejection_id(self):
        return self.__get_invitation_id(name='Rejection')

    def get_reviewer_recommendation_id(self, number=None):
        return self.__get_invitation_id(name='Official_Recommendation', number=number)

    def get_reviewer_recruitment_id(self):
        return self.__get_invitation_id(name='Recruitment', prefix=self.get_reviewers_id())

    def get_reviewer_conflict_id(self):
        return self.__get_invitation_id(name='Conflict', prefix=self.get_reviewers_id())

    def get_reviewer_affinity_score_id(self):
        return self.__get_invitation_id(name='Affinity_Score', prefix=self.get_reviewers_id())

    def get_reviewer_assignment_id(self, number=None):
        return self.__get_invitation_id(name='Assignment', prefix=self.get_reviewers_id(number))

    def get_reviewer_custom_max_papers_id(self):
        return self.__get_invitation_id(name='Custom_Max_Papers', prefix=self.get_reviewers_id())

    def get_reviewer_pending_review_id(self):
        return self.__get_invitation_id(name='Pending_Reviews', prefix=self.get_reviewers_id())

    def get_camera_ready_revision_id(self, number=None):
        return self.__get_invitation_id(name='Camera_Ready_Revision', number=number)

    def get_camera_ready_verification_id(self, number=None):
        return self.__get_invitation_id(name='Camera_Ready_Verification', number=number)

    def get_revision_id(self, number=None):
        return self.__get_invitation_id(name='Revision', number=number)

    def get_solicit_review_id(self, number=None):
        return self.__get_invitation_id(name='Solicit_Review', number=number)

    def get_solicit_review_approval_id(self, number=None, signature=None):
        if signature:
            return self.__get_invitation_id(name=f'{signature}_Solicit_Review_Approval', number=number)

        return self.__get_invitation_id(name='Solicit_Review_Approval', number=number)


    def get_public_comment_id(self, number):
        return self.__get_invitation_id(name='Public_Comment', number=number)

    def get_official_comment_id(self, number):
        return self.__get_invitation_id(name='Official_Comment', number=number)

    def get_moderation_id(self, number):
        return self.__get_invitation_id(name='Moderation', number=number)

    def get_submission_editable_id(self, number):
        return self.__get_invitation_id(name='Submission_Editable', number=number)

    def setup(self, support_role, editors=[]):
        self.group_builder.set_groups(self, support_role, editors)
        self.invitation_builder.set_invitations()

    def set_action_editors(self, editors, custom_papers):
        venue_id=self.venue_id
        aes=self.get_action_editors_id()
        self.client.add_members_to_group(aes, editors)
        for index,ae in enumerate(editors):
            edge = Edge(invitation = f'{aes}/-/Custom_Max_Papers',
                readers = [venue_id, ae],
                writers = [venue_id, ae],
                signatures = [venue_id],
                head = aes,
                tail = ae,
                weight=custom_papers[index]
            )
            self.client.post_edge(edge)

    def set_reviewers(self, reviewers):
        self.client.add_members_to_group(self.get_reviewers_id(), reviewers)

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

    def invite_reviewers(self, message, subject, invitees, invitee_names=None, replyTo=None):
        return self.recruitment.invite_reviewers(message, subject, invitees, invitee_names, replyTo)

    def setup_author_submission(self, note):
        self.group_builder.setup_submission_groups(self, note)
        self.invitation_builder.set_revision_submission(note)
        self.invitation_builder.set_note_review_approval_invitation(note, openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(weeks = 1)))
        self.invitation_builder.set_note_withdrawal_invitation(note)
        self.setup_ae_assignment(note)
        self.invitation_builder.set_ae_recommendation_invitation(note, openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(weeks = 1)))


    def setup_under_review_submission(self, note):
        self.invitation_builder.set_review_invitation(note, openreview.tools.datetime_millis(datetime.datetime.utcnow() + datetime.timedelta(weeks = 2)))
        self.invitation_builder.set_note_solicit_review_invitation(note)
        self.invitation_builder.set_comment_invitation(note)
        self.setup_reviewer_assignment(note)

    def assign_reviewer(self, note, reviewer, solicit):
        self.assignment.assign_reviewer(note, reviewer, solicit)

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

        if new_venue_id == self.under_review_venue_id:

            first_author_last_name = 'anonymous'
            authors = 'Anonymous'
            year = datetime.datetime.fromtimestamp(note.cdate/1000).year

            bibtex = [
                '@article{',
                utf8tolatex(first_author_last_name + first_word + ','),
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
            year = datetime.datetime.fromtimestamp(note.cdate/1000).year

            bibtex = [
                '@article{',
                utf8tolatex(first_author_last_name + first_word + ','),
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
            year = datetime.datetime.fromtimestamp(note.mdate/1000).year

            bibtex = [
                '@article{',
                utf8tolatex(first_author_last_name + first_word + ','),
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

            first_author_profile = self.client.get_profile(note.content['authorids']['value'][0])
            first_author_last_name = openreview.tools.get_preferred_name(first_author_profile, last_name_only=True).lower()
            authors = ' and '.join(note.content['authors']['value'])
            year = datetime.datetime.fromtimestamp(note.mdate/1000).year

            bibtex = [
                '@article{',
                utf8tolatex(first_author_last_name + first_word + ','),
                'title={' + bibtex_title + '},',
                'author={' + utf8tolatex(authors) + '},',
                'journal={' + self.full_name + '},',
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
            year = datetime.datetime.fromtimestamp(note.mdate/1000).year

            bibtex = [
                '@article{',
                utf8tolatex(first_author_last_name + first_word + ','),
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
        invitee_groups = [ self.client.get_group(i) for i in invitation.invitees if i not in [self.venue_id, self.get_editors_in_chief_id()] ]
        invitee_members = [member for group in invitee_groups for member in group.members]

        replies = self.client.get_notes(invitation=invitation.id, details='signatures')
        signature_members = [member for reply in replies for signature in reply.details['signatures'] for member in signature['members']]

        return list(set(invitee_members) - set(signature_members))

    def notify_readers(self, edit, content_fields=[]):

        vowels = ['a', 'e', 'i', 'o', 'u']
        note = self.client.get_note(edit.note.id)
        forum = self.client.get_note(note.forum)

        if note.ddate:
            return

        action = 'posted' if note.tcdate == note.tmdate else 'edited'

        readers = note.readers
        nonreaders = note.nonreaders + [edit.tauthor]
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
        if action == 'posted':
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
