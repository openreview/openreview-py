import csv
import json
from json import tool
import datetime
from io import StringIO
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import openreview
from openreview import tools
from .invitation import InvitationBuilder
from .group import GroupBuilder
from openreview.api import Group
from openreview.api import Note
from .recruitment import Recruitment
from . import matching

class Venue(object):

    def __init__(self, client, venue_id, support_user):

        self.client = client
        self.request_form_id = None
        self.venue_id = venue_id
        self.name = 'TBD'
        self.short_name = 'TBD'
        self.website = None
        self.contact = None
        self.id = venue_id # get compatibility with conference
        self.program_chairs_name = 'Program_Chairs'
        self.reviewers_name = 'Reviewers'
        self.reviewer_roles = ['Reviewers']
        self.area_chair_roles = ['Area_Chairs']
        self.senior_area_chair_roles = ['Senior_Area_Chairs']        
        self.area_chairs_name = 'Area_Chairs'
        self.senior_area_chairs_name = 'Senior_Area_Chairs'
        self.ethics_chairs_name = 'Ethics_Chairs'
        self.ethics_reviewers_name = 'Ethics_Reviewers'
        self.authors_name = 'Authors'
        self.use_ethics_chairs = False
        self.use_ethics_reviewers = False 
        self.expertise_selection_stage = None       
        self.submission_stage = None
        self.review_stage = None
        self.ethics_review_stage = None
        self.bid_stages = []
        self.meta_review_stage = None
        self.comment_stage = None
        self.decision_stage = None
        self.submission_revision_stage = None
        self.registration_stages = []
        self.use_area_chairs = False
        self.use_senior_area_chairs = False
        self.use_ethics_chairs = False
        self.use_secondary_area_chairs = False
        self.use_recruitment_template = True
        self.support_user = support_user
        self.invitation_builder = InvitationBuilder(self)
        self.group_builder = GroupBuilder(self)
        self.recruitment = Recruitment(self)
        self.reviewer_identity_readers = []
        self.area_chair_identity_readers = []
        self.senior_area_chair_identity_readers = []
        self.enable_reviewers_reassignment = False
        self.reviewers_proposed_assignment_title = None
        self.conflict_policy = 'default'

    def get_id(self):
        return self.venue_id

    def get_short_name(self):
        return self.short_name

    def get_committee_name(self, committee_id, pretty=False):
        name = committee_id.split('/')[-1]

        if pretty:
            name = name.replace('_', ' ')
            if name.endswith('s'):
                return name[:-1]
        return name

    def get_committee_names(self):
        committee=[self.reviewers_name]

        if self.use_area_chairs:
            committee.append(self.area_chairs_name)

        if self.use_senior_area_chairs:
            committee.append(self.senior_area_chairs_name)

        return committee

    def get_roles(self):
        roles = self.reviewer_roles
        if self.use_area_chairs:
            roles = self.reviewer_roles + [self.area_chairs_name]
        if self.use_senior_area_chairs:
            roles = roles + [self.senior_area_chairs_name]
        return roles

    def get_meta_invitation_id(self):
        return f'{self.venue_id}/-/Edit'

    def get_submission_id(self):
        return self.submission_stage.get_submission_id(self)

    def get_pc_submission_revision_id(self):
        return self.get_invitation_id('PC_Revision')

    def get_recruitment_id(self, committee_id):
        return self.get_invitation_id('Recruitment', prefix=committee_id)

    def get_expertise_selection_id(self, committee_id):
        return self.get_invitation_id(self.expertise_selection_stage.name if self.expertise_selection_stage else 'Expertise_Selection', prefix=committee_id)    

    def get_bid_id(self, committee_id):
        return self.get_invitation_id('Bid', prefix=committee_id)

    def get_assignment_id(self, committee_id, deployed=False, invite=False):
        if deployed:
            return self.get_invitation_id('Assignment', prefix=committee_id)
        if invite:
            return self.get_invitation_id('Invite_Assignment', prefix=committee_id)
        return self.get_invitation_id('Proposed_Assignment', prefix=committee_id)

    def get_affinity_score_id(self, committee_id):
        return self.get_invitation_id('Affinity_Score', prefix=committee_id)

    def get_conflict_score_id(self, committee_id):
        return self.get_invitation_id('Conflict', prefix=committee_id)

    def get_custom_max_papers_id(self, committee_id):
        return self.get_invitation_id('Custom_Max_Papers', prefix=committee_id)

    def get_recommendation_id(self, committee_id=None):
        if not committee_id:
            committee_id = self.get_reviewers_id()
        return self.get_invitation_id('Recommendation', prefix=committee_id)

    def get_paper_group_prefix(self, number=None):
        prefix = f'{self.venue_id}/{self.submission_stage.name}'
        if number:
            prefix = f'{prefix}{number}'
        return prefix
    
    def get_invitation_id(self, name, number = None, prefix = None):
        invitation_id = self.id
        if prefix:
            invitation_id = prefix
        if number:
            invitation_id = f'{self.get_paper_group_prefix(number)}/-/'
        else:
            invitation_id = invitation_id + '/-/'

        invitation_id =  invitation_id + name
        return invitation_id

    def get_committee(self, number = None, submitted_reviewers = False, with_authors = False):
        committee = [self.id]

        if with_authors:
            committee.append(self.get_authors_id(number))

        if submitted_reviewers:
            committee.append(self.get_reviewers_id(number, submitted=True))
        else:
            committee.append(self.get_reviewers_id(number))

        if self.use_area_chairs:
            committee.append(self.get_area_chairs_id(number))

        if self.use_senior_area_chairs:
            committee.append(self.get_senior_area_chairs_id(number))

        committee.append(self.get_program_chairs_id())

        return committee

    def get_committee_id(self, name, number=None):
        committee_id = self.id + '/'
        if number:
            committee_id = f'{self.get_paper_group_prefix(number)}/{name}'
        else:
            committee_id = committee_id + name
        return committee_id

    def get_committee_id_invited(self, committee_name):
        return self.get_committee_id(committee_name) + '/Invited'

    def get_committee_id_declined(self, committee_name):
        return self.get_committee_id(committee_name) + '/Declined'

    ## Compatibility with Conference, refactor conference references to use get_reviewers_id
    def get_anon_reviewer_id(self, number, anon_id):
        return self.get_reviewers_id(number, True)

    def get_reviewers_name(self, pretty=True):
        if pretty:
            name=self.reviewers_name.replace('_', ' ')
            return name[:-1] if name.endswith('s') else name
        return self.reviewers_name

    def get_ethics_reviewers_name(self, pretty=True):
        if pretty:
            name=self.ethics_reviewers_name.replace('_', ' ')
            return name[:-1] if name.endswith('s') else name
        return self.ethics_reviewers_name

    def get_area_chairs_name(self, pretty=True):
        if pretty:
            name=self.area_chairs_name.replace('_', ' ')
            return name[:-1] if name.endswith('s') else name
        return self.area_chairs_name
    
    def get_reviewers_id(self, number = None, anon=False, submitted=False):
        rev_name = self.reviewers_name[:-1] if self.reviewers_name.endswith('s') else self.reviewers_name
        reviewers_id = self.get_committee_id(f'{rev_name}_.*' if anon else self.reviewers_name, number)
        if submitted:
            return reviewers_id + '/Submitted'
        return reviewers_id

    def get_authors_id(self, number = None):
        return self.get_committee_id(self.authors_name, number)

    def get_authors_accepted_id(self, number = None):
        return self.get_committee_id(self.authors_name) + '/Accepted'

    def get_program_chairs_id(self):
        return self.get_committee_id(self.program_chairs_name)

    def get_area_chairs_id(self, number = None, anon=False):
        ac_name = self.area_chairs_name[:-1] if self.area_chairs_name.endswith('s') else self.area_chairs_name
        return self.get_committee_id(f'{ac_name}_.*' if anon else self.area_chairs_name, number)

    ## Compatibility with Conference, refactor conference references to use get_area_chairs_id
    def get_anon_area_chair_id(self, number, anon_id):
        return self.get_area_chairs_id(number, True)

    def get_senior_area_chairs_id(self, number = None):
        return self.get_committee_id(self.senior_area_chairs_name, number)

    def get_ethics_chairs_id(self, number = None):
        return self.get_committee_id(self.ethics_chairs_name, number)

    def get_ethics_reviewers_id(self, number = None, anon=False):
        return self.get_committee_id('Ethics_Reviewer_.*' if anon else self.ethics_reviewers_name, number)

    def get_withdrawal_id(self, number = None):
        return self.get_invitation_id(self.submission_stage.withdrawal_name, number)

    def get_withdrawn_id(self):
        return self.get_invitation_id(f'Withdrawn_{self.submission_stage.name}')

    def get_desk_rejection_id(self, number = None):
        return self.get_invitation_id(self.submission_stage.desk_rejection_name, number)

    def get_desk_rejected_id(self):
        return self.get_invitation_id(f'Desk_Rejected_{self.submission_stage.name}')

    def get_participants(self, number=None, with_program_chairs=False, with_authors=False):
        committee = []
        if with_program_chairs:
            committee.append(self.get_program_chairs_id())
        if self.use_senior_area_chairs:
            committee.append(self.get_senior_area_chairs_id(number))
        if self.use_area_chairs:
            committee.append(self.get_area_chairs_id(number))
        committee.append(self.get_reviewers_id(number))
        if with_authors:
            committee.append(self.get_authors_id(number))
        return committee

    def get_submission_venue_id(self, submission_invitation_name=None):
        if submission_invitation_name:
            return f'{self.venue_id}/{submission_invitation_name}'
        if self.submission_stage:
            return f'{self.venue_id}/{self.submission_stage.name}'
        return f'{self.venue_id}/Submission'

    def get_withdrawn_submission_venue_id(self, submission_invitation_name=None):
        if submission_invitation_name:
            return f'{self.venue_id}/Withdrawn_{submission_invitation_name}'
        if self.submission_stage:
            return f'{self.venue_id}/Withdrawn_{self.submission_stage.name}'
        return f'{self.venue_id}/Withdrawn_Submission' 

    def get_desk_rejected_submission_venue_id(self, submission_invitation_name=None):
        if submission_invitation_name:
            return f'{self.venue_id}/Desk_Rejected_{submission_invitation_name}'
        if self.submission_stage:
            return f'{self.venue_id}/Desk_Rejected_{self.submission_stage.name}'
        return f'{self.venue_id}/Desk_Rejected_Submission'                

    def get_rejected_submission_venue_id(self, submission_invitation_name=None):
        if submission_invitation_name:
            return f'{self.venue_id}/Rejected_{submission_invitation_name}'
        if self.submission_stage:
            return f'{self.venue_id}/Rejected_{self.submission_stage.name}'
        return f'{self.venue_id}/Rejected_Submission' 

    def get_submissions(self, venueid=None, accepted=False, sort=None, details=None):
        if accepted:
            accepted_notes = self.client.get_all_notes(content={ 'venueid': self.venue_id}, sort=sort)
            if len(accepted_notes) == 0:
                accepted_notes = []
                notes = self.client.get_all_notes(content={ 'venueid': f'{self.get_submission_venue_id()}'}, sort=sort, details='directReplies')
                for note in notes:
                    for reply in note.details['directReplies']:
                        if f'{self.venue_id}/{self.submission_stage.name}{note.number}/-/{self.decision_stage.name}' in reply['invitations']:
                            if 'Accept' in reply['content']['decision']['value']:
                                accepted_notes.append(note)
            return accepted_notes
        else:
            notes = self.client.get_all_notes(content={ 'venueid': venueid if venueid else f'{self.get_submission_venue_id()}'}, sort=sort, details=details)
            if len(notes) == 0:
                notes = self.client.get_all_notes(content={ 'venueid': self.venue_id}, sort=sort, details=details)
                rejected = self.client.get_all_notes(content={ 'venueid': f'{self.venue_id}/Rejected'}, sort=sort, details=details)
                if rejected:
                    notes.extend(rejected)
            return notes

    #use to expire revision invitations from request form
    def expire_invitation(self, invitation_id):

        invitation_name = invitation_id.split('/-/')[-1]

        notes = self.get_submissions()
        for note in notes:
            invitation = f'{self.venue_id}/{self.submission_stage.name}{note.number}/-/{invitation_name}'
            self.invitation_builder.expire_invitation(invitation)

    def setup(self, program_chair_ids=[]):
    
        self.invitation_builder.set_meta_invitation()

        self.group_builder.create_venue_group()

        self.group_builder.create_program_chairs_group(program_chair_ids)

        self.group_builder.create_authors_group()

        self.group_builder.create_reviewers_group()
        
        if self.use_area_chairs:
            self.group_builder.create_area_chairs_group()

        if self.use_senior_area_chairs:
            self.group_builder.create_senior_area_chairs_group()            

    def recruit_reviewers(self,
        title,
        message,
        invitees = [],
        reviewers_name = 'Reviewers',
        remind = False,
        invitee_names = [],
        retry_declined = False,
        contact_info = '',
        reduced_load_on_decline = None,
        default_load= 0,
        allow_overlap_official_committee = False,
        accept_recruitment_template=None):

        return self.recruitment.invite_committee(title,
            message,
            invitees,
            reviewers_name,
            remind,
            invitee_names,
            retry_declined,
            contact_info,
            reduced_load_on_decline,
            # default_load, ##can this be removed? We never get it from the request form
            allow_overlap_official_committee)

    def create_submission_stage(self):
        self.invitation_builder.set_submission_invitation()
        self.invitation_builder.set_withdrawal_invitation()
        self.invitation_builder.set_desk_rejection_invitation()
        if self.expertise_selection_stage:
            self.invitation_builder.set_expertise_selection_invitations()

    def create_review_stage(self):
        invitation = self.invitation_builder.set_review_invitation()
        self.invitation_builder.create_paper_invitations(invitation.id, self.get_submissions())

    def create_meta_review_stage(self):
        invitation = self.invitation_builder.set_meta_review_invitation()
        self.invitation_builder.create_paper_invitations(invitation.id, self.get_submissions())

    def create_registration_stages(self):
        self.invitation_builder.set_registration_invitations()
    
    def setup_post_submission_stage(self, force=False, hide_fields=[]):
        venue_id = self.venue_id
        submissions = self.get_submissions()
        hide_author_fields = ['authors', 'authorids'] if self.submission_stage.double_blind else []
        final_hide_fields = hide_author_fields + hide_fields
        
        self.group_builder.create_paper_committee_groups(submissions)
        
        def update_submission_readers(submission):

            if submission.content['venueid']['value'] == self.get_submission_venue_id():

                note_content = {}
                for field, value in submission.content.items():
                    if field in final_hide_fields and 'readers' not in value:
                        note_content[field] = {
                            'readers': [venue_id, self.get_authors_id(submission.number)]
                        }
                                           
                    if field not in final_hide_fields and 'readers' in value:
                        note_content[field] = {
                            'readers': { 'delete': True }
                        }                        

                new_readers = self.submission_stage.get_readers(self, submission.number)
                note_readers = new_readers if submission.readers != new_readers else None
               
                note_writers = [venue_id, self.get_authors_id(submission.number)] if submission.writers != [venue_id, self.get_authors_id(submission.number)] else None
                note_signatures = [self.get_authors_id(submission.number)]

                note_odate = openreview.tools.datetime_millis(datetime.datetime.utcnow()) if (submission.odate is None and note_readers and 'everyone' in note_readers) else None

                if note_readers or note_writers or note_content or note_odate:
                    return self.client.post_note_edit(invitation=self.get_meta_invitation_id(),
                        readers=[venue_id, self.get_authors_id(submission.number)],
                        writers=[venue_id],
                        signatures=[venue_id],
                        note=openreview.api.Note(id=submission.id,
                                odate = note_odate,
                                readers = note_readers,
                                writers = note_writers,
                                signatures = note_signatures,
                                content = note_content 
                            )
                        )
                else:
                    return submission
        ## Release the submissions to specified readers if venueid is still submission
        openreview.tools.concurrent_requests(update_submission_readers, submissions, desc='update_submission_readers')

        ## Open PC Revision
        self.invitation_builder.set_pc_submission_revision_invitation()
             
        ## Create revision invitation if there is a second deadline?
        ## Create withdraw and desk reject invitations
        self.invitation_builder.create_paper_invitations(self.get_withdrawal_id(), submissions)
        self.invitation_builder.create_paper_invitations(self.get_desk_rejection_id(), submissions)

        self.group_builder.add_to_active_venues()

    def create_bid_stages(self):
        self.invitation_builder.set_bid_invitations()

    def create_comment_stage(self):
        comment_invitation = self.invitation_builder.set_official_comment_invitation()
        self.invitation_builder.create_paper_invitations(comment_invitation.id, self.get_submissions())
        if self.comment_stage.allow_public_comments:
            public_notes = [note for note in self.get_submissions() if 'everyone' in note.readers]
            comment_invitation = self.invitation_builder.set_public_comment_invitation()
            self.invitation_builder.create_paper_invitations(comment_invitation.id, public_notes)

    def create_decision_stage(self):
        invitation = self.invitation_builder.set_decision_invitation()
        self.invitation_builder.create_paper_invitations(invitation.id, self.get_submissions())

        decision_file = self.decision_stage.decisions_file
        if decision_file:

            baseurl = 'http://localhost:3000'
            if 'https://devapi' in self.client.baseurl:
                baseurl = 'https://devapi.openreview.net'
            if 'https://api' in self.client.baseurl:
                baseurl = 'https://api.openreview.net'
            api1_client = openreview.Client(baseurl=baseurl, token=self.client.token)

            if '/attachment' in decision_file:
                decisions = api1_client.get_attachment(id=self.request_form_id, field_name='decisions_file')

            else:
                with open(decision_file, 'rb') as file_handle:
                    decisions = file_handle.read()

            self.post_decisions(decisions, api1_client)

    def post_decisions(self, decisions_file, api1_client):

        decisions_data = list(csv.reader(StringIO(decisions_file.decode()), delimiter=","))

        paper_notes = {n.number: n for n in self.get_submissions(details='directReplies')}

        def post_decision(paper_decision):
            if len(paper_decision) < 2:
                raise openreview.OpenReviewException(
                    "Not enough values provided in the decision file. Expected values are: paper_number, decision, comment")
            if len(paper_decision) > 3:
                raise openreview.OpenReviewException(
                    "Too many values provided in the decision file. Expected values are: paper_number, decision, comment"
                )
            if len(paper_decision) == 3:
                paper_number, decision, comment = paper_decision
            else:
                paper_number, decision = paper_decision
                comment = ''

            paper_number = int(paper_number)

            print(f"Posting Decision {decision} for Paper {paper_number}")
            paper_note = paper_notes.get(paper_number, None)
            if not paper_note:
                raise openreview.OpenReviewException(
                    f"Paper {paper_number} not found. Please check the submitted paper numbers."
                )

            paper_decision_note = None
            if paper_note.details:
                for reply in paper_note.details['directReplies']:
                    if f'{self.venue_id}/{self.submission_stage.name}{paper_note.number}/-/{self.decision_stage.name}' in reply['invitations']:
                        paper_decision_note = reply
                        break

            content = {
                'title': {'value': 'Paper Decision'},
                'decision': {'value': decision.strip()},
                'comment': {'value': comment},
            }
            if paper_decision_note:
                self.client.post_note_edit(invitation = self.get_invitation_id(self.decision_stage.name, paper_number),
                    signatures = [self.get_program_chairs_id()],
                    note = Note(
                        id = paper_decision_note['id'],
                        content = content
                    )
                )
            else:
                self.client.post_note_edit(invitation = self.get_invitation_id(self.decision_stage.name, paper_number),
                    signatures = [self.get_program_chairs_id()],
                    note = Note(
                        content = content
                    )
                )

            print(f"Decision posted for Paper {paper_number}")

        futures = []
        futures_param_mapping = {}
        gathering_responses = tqdm(total=len(decisions_data), desc='Gathering Responses')
        results = []
        errors = {}

        with ThreadPoolExecutor(max_workers=min(6, cpu_count() - 1)) as executor:
            for _decision in decisions_data:
                _future = executor.submit(post_decision, _decision)
                futures.append(_future)
                futures_param_mapping[_future] = str(_decision)

            for future in futures:
                gathering_responses.update(1)
                try:
                    results.append(future.result())
                except Exception as e:
                    errors[futures_param_mapping[future]] = e.args[0] if isinstance(e, openreview.OpenReviewException) else repr(e)

            gathering_responses.close()

        error_status = ''
        if errors:
            error_status = f'''
Total Errors: {len(errors)}
```python
{json.dumps({key: errors[key] for key in list(errors.keys())[:10]}, indent=2)}
```
'''
        if self.request_form_id:
            forum_note = api1_client.get_note(self.request_form_id)
            status_note = openreview.Note(
                invitation=self.support_user + '/-/Request' + str(forum_note.number) + '/Decision_Upload_Status',
                forum=self.request_form_id,
                replyto=self.request_form_id,
                readers=[self.get_program_chairs_id(), self.support_user],
                writers=[],
                signatures=[self.support_user],
                content={
                    'title': 'Decision Upload Status',
                    'decision_posted': f'''{len(results)} Papers''',
                    'error': error_status
                }
            )

            api1_client.post_note(status_note)

    def post_decision_stage(self, reveal_all_authors=False, reveal_authors_accepted=False, decision_heading_map=None, submission_readers=None):

        venue_id = self.venue_id
        submissions = self.get_submissions(sort='number:asc', details='directReplies')

        def is_release_authors(is_note_accepted):
            return reveal_all_authors or (reveal_authors_accepted and is_note_accepted)

        def decision_to_venueid(decision):
            if 'Accept' in decision:
                return venue_id
            else:
                return f'{venue_id}/Rejected'

        if submission_readers:
            self.submission_stage.readers = submission_readers

        for submission in submissions:
            decision_note = None
            if submission.details:
                for reply in submission.details['directReplies']:
                    if f'{self.venue_id}/{self.submission_stage.name}{submission.number}/-/{self.decision_stage.name}' in reply['invitations']:
                        decision_note = reply
                        break
            note_accepted = decision_note and 'Accept' in decision_note['content']['decision']['value']
            submission_readers = self.submission_stage.get_readers(self, submission.number, decision_note['content']['decision']['value'] if decision_note else None)

            venue = self.short_name
            decision_option = decision_note['content']['decision']['value'] if decision_note else ''
            venue = tools.decision_to_venue(venue, decision_option)
            venueid = decision_to_venueid(decision_option)

            content = {
                'venueid': {
                    'value': venueid
                },
                'venue': {
                    'value': venue
                }
            }

            if is_release_authors(note_accepted):
                content['authorids'] = {
                    'readers': { 'delete': True }
                }
                content['authors'] = {
                    'readers': { 'delete': True }
                }

            self.client.post_note_edit(invitation=self.get_meta_invitation_id(),
                readers=[venue_id, self.get_authors_id(submission.number)],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(id=submission.id,
                        readers = submission_readers,
                        content = content,
                        odate = openreview.tools.datetime_millis(datetime.datetime.utcnow()) if (submission.odate is None and 'everyone' in submission_readers) else None,
                        pdate = openreview.tools.datetime_millis(datetime.datetime.utcnow()) if (submission.pdate is None and note_accepted) else None
                    )
                )

    def send_decision_notifications(self, decision_options, messages):
        paper_notes = self.get_submissions(venueid=self.venue_id, details='directReplies')

        def send_notification(note):
            decision_note = None
            for reply in note.details['directReplies']:
                if f'{self.venue_id}/{self.submission_stage.name}{note.number}/-/{self.decision_stage.name}' in reply['invitations']:
                    decision_note = reply
                    break
            subject = "[{SHORT_NAME}] Decision notification for your submission {submission_number}: {submission_title}".format(
                SHORT_NAME=self.short_name,
                submission_number=note.number,
                submission_title=note.content['title']['value']
            )
            if decision_note and not self.client.get_messages(subject=subject):
                message = messages[decision_note['content']['decision']['value']]
                final_message = message.replace("{{submission_title}}", note.content['title']['value'])
                final_message = final_message.replace("{{forum_url}}", f'https://openreview.net/forum?id={note.id}')
                self.client.post_message(subject, recipients=note.content['authorids']['value'], message=final_message)

        tools.concurrent_requests(send_notification, paper_notes)

    def create_submission_revision_stage(self):
        invitation = tools.get_invitation(self.client, self.get_submission_id())
        if invitation:
            notes = self.get_submissions(accepted=self.submission_revision_stage.only_accepted)
            if self.submission_revision_stage.only_accepted:
                all_notes = self.get_submissions()
                accepted_note_ids = [note.id for note in notes]
                non_accepted_notes = [note for note in all_notes if note.id not in accepted_note_ids]
                expire_invitation_ids = [self.get_invitation_id(self.submission_revision_stage.name, note.number) for note in non_accepted_notes]
                tools.concurrent_requests(self.invitation_builder.expire_invitation, expire_invitation_ids)
            revision_invitation = self.invitation_builder.set_submission_revision_invitation(invitation.edit['note']['content'])
            self.invitation_builder.create_paper_invitations(revision_invitation.id, notes)

    def setup_committee_matching(self, committee_id=None, compute_affinity_scores=False, compute_conflicts=False, alternate_matching_group=None):
        if committee_id is None:
            committee_id=self.get_reviewers_id()
        if self.use_senior_area_chairs and committee_id == self.get_senior_area_chairs_id() and not alternate_matching_group:
            alternate_matching_group = self.get_area_chairs_id()
        venue_matching = matching.Matching(self, self.client.get_group(committee_id), alternate_matching_group)

        return venue_matching.setup(compute_affinity_scores, self.conflict_policy if compute_conflicts else False)

    def set_assignments(self, assignment_title, committee_id, enable_reviewer_reassignment=False, overwrite=False):

        match_group = self.client.get_group(committee_id)
        conference_matching = matching.Matching(self, match_group)
        return conference_matching.deploy(assignment_title, overwrite, enable_reviewer_reassignment)

    def setup_assignment_recruitment(self, committee_id, hash_seed, due_date, assignment_title=None, invitation_labels={}, email_template=None):

        match_group = self.client.get_group(committee_id)
        conference_matching = matching.Matching(self, match_group)
        return conference_matching.setup_invite_assignment(hash_seed, assignment_title, due_date, invitation_labels=invitation_labels, email_template=email_template)


    @classmethod
    def check_new_profiles(Venue, client):

        def mark_as_conflict(venue_group, edge, submission, user_profile):
            edge.label='Conflict Detected'
            edge.tail=user_profile.id
            edge.readers=None
            edge.writers=None            
            client.post_edge(edge)

            ## Send email to reviewer
            subject=f"[{venue_group.content['subtitle']['value']}] Conflict detected for paper {submission.number}"
            message =f'''Hi {{{{fullname}}}},
You have accepted the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.

A conflict was detected between you and the submission authors and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

OpenReview Team'''
            response = client.post_message(subject, [edge.tail], message)

            ## Send email to inviter
            subject=f"[{venue_group.content['subtitle']['value']}] Conflict detected between reviewer {user_profile.get_preferred_name(pretty=True)} and paper {submission.number}"
            message =f'''Hi {{{{fullname}}}},
A conflict was detected between {user_profile.get_preferred_name(pretty=True)}({user_profile.get_preferred_email()}) and the paper {submission.number} and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, edge.signatures, message)            
        
        def mark_as_accepted(venue_group, edge, submission, user_profile, invite_assignment_invitation):

            edge.label='Accepted'
            edge.tail=user_profile.id
            edge.readers=None
            edge.writers=None
            client.post_edge(edge)

            short_phrase = venue_group.content['subtitle']['value']
            assigment_label = invite_assignment_invitation.content.get('assignment_label', {}).get('value')
            assignment_invitation_id = invite_assignment_invitation.content.get('assignment_invitation_id', {}).get('value')
            committee_invited_id = invite_assignment_invitation.content.get('committee_invited_id', {}).get('value')
            paper_reviewer_invited_id = invite_assignment_invitation.content.get('paper_reviewer_invited_id', {}).get('value')
            reviewers_id = invite_assignment_invitation.content.get('match_group', {}).get('value')
            reviewer_name = 'Reviewer' ## add this to the invitation?

            assignment_edges = client.get_edges(invitation=assignment_invitation_id, head=submission.id, tail=edge.tail, label=assigment_label)

            if not assignment_edges:
                print('post assignment edge')
                client.post_edge(openreview.api.Edge(
                    invitation=assignment_invitation_id,
                    head=edge.head,
                    tail=edge.tail,
                    label=assigment_label,
                    signatures=[venue_group.id],
                    weight=1
                ))

                if committee_invited_id:
                    client.add_members_to_group(committee_invited_id.replace('/Invited', ''), edge.tail)
                if paper_reviewer_invited_id:
                    external_paper_committee_id=paper_reviewer_invited_id.replace('/Invited', '').replace('{number}', str(submission.number))
                    client.add_members_to_group(external_paper_committee_id, edge.tail)

                if assigment_label:
                    instructions=f'The {short_phrase} program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.'
                else:
                    instructions=f'Please go to the {short_phrase} Reviewers Console and check your pending tasks: https://openreview.net/group?id={reviewers_id}'

                print('send confirmation email')
                ## Send email to reviewer
                subject=f'[{short_phrase}] {reviewer_name} Assignment confirmed for paper {submission.number}'
                message =f'''Hi {{{{fullname}}}},
Thank you for accepting the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.

{instructions}

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team'''

                ## - Send email
                response = client.post_message(subject, [edge.tail], message)

                ## Send email to inviter
                subject=f'[{short_phrase}] {reviewer_name} {user_profile.get_preferred_name(pretty=True)} signed up and is assigned to paper {submission.number}'
                message =f'''Hi {{{{fullname}}}},
The {reviewer_name} {user_profile.get_preferred_name(pretty=True)}({user_profile.get_preferred_email()}) that you invited to review paper {submission.number} has accepted the invitation, signed up and is now assigned to the paper {submission.number}.

OpenReview Team'''

                ## - Send email
                response = client.post_message(subject, edge.signatures, message)            
        
        active_venues = client.get_group('active_venues').members

        for venue_id in active_venues:

            venue_group = client.get_group(venue_id)
            
            if hasattr(venue_group, 'domain') and venue_group.content:
                
                print(f'Check active venue {venue_group.id}')
                invite_assignment_invitation_id = venue_group.content.get('reviewers_invite_assignment_id', {}).get('value')

                if invite_assignment_invitation_id:
                    
                    ## check if it is expired?
                    invite_assignment_invitation = openreview.tools.get_invitation(client, invite_assignment_invitation_id)

                    if invite_assignment_invitation:
                        grouped_edges = client.get_grouped_edges(invitation=invite_assignment_invitation.id, label='Pending Sign Up', groupby='tail')
                        print('Pending sign up edges found', len(grouped_edges))

                        for grouped_edge in grouped_edges:

                            tail = grouped_edge['id']['tail']
                            profiles=openreview.tools.get_profiles(client, [tail], with_publications=True)

                            if profiles and profiles[0].active:

                                user_profile=profiles[0]
                                print('Profile found for', tail, user_profile.id)

                                edges = grouped_edge['values']

                                for edge in edges:

                                    edge = openreview.api.Edge.from_json(edge)
                                    submission=client.get_note(id=edge.head)

                                    if submission.content['venueid']['value'] == venue_group.content.get('submission_venue_id', {}).get('value'):

                                        ## Check if there is already an accepted edge for that profile id
                                        accepted_edges = client.get_edges(invitation=invite_assignment_invitation.id, label='Accepted', head=submission.id, tail=user_profile.id)

                                        if not accepted_edges:
                                            ## Check if the user was invited again with a profile id
                                            invitation_edges = client.get_edges(invitation=invite_assignment_invitation.id, label='Invitation Sent', head=submission.id, tail=user_profile.id)
                                            if invitation_edges:
                                                print(f'User invited twice, remove double invitation edge {invitation_edge.id}')
                                                invitation_edge = invitation_edges[0]
                                                invitation_edge.ddate = openreview.tools.datetime_millis(datetime.datetime.utcnow())
                                                client.post_edge(invitation_edge)

                                            ## Check conflicts
                                            author_profiles = openreview.tools.get_profiles(client, submission.content['authorids']['value'], with_publications=True)
                                            conflicts=openreview.tools.get_conflicts(author_profiles, user_profile, policy=venue_group.content.get('conflict_policy', {}).get('value'))

                                            if conflicts:
                                                print(f'Conflicts detected for {edge.head} and {user_profile.id}', conflicts)
                                                mark_as_conflict(venue_group, edge, submission, user_profile)
                                            else:
                                                print(f'Mark accepted for {edge.head} and {user_profile.id}')
                                                mark_as_accepted(venue_group, edge, submission, user_profile, invite_assignment_invitation)
                                                                                                                                                            
                                        else:
                                            print("user already accepted with another invitation edge", submission.id, user_profile.id)                                

                                    else:
                                        print(f'submission {submission.id} is not active: {submission.content["venueid"]["value"]}')

                            else:
                                print(f'no profile active for {tail}')                                             
        
        return True
