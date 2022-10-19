import csv
import json
from json import tool
import os
import time
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

    def __init__(self, client, venue_id):

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
        self.submission_stage = None
        self.review_stage = None
        self.ethics_review_stage = None
        self.bid_stages = []
        self.meta_review_stage = None
        self.comment_stage = None
        self.decision_stage = None
        self.submission_revision_stage = False
        self.use_area_chairs = False
        self.use_senior_area_chairs = False
        self.use_ethics_chairs = False
        self.use_recruitment_template = True
        self.support_user = 'OpenReview.net/Support'
        self.invitation_builder = InvitationBuilder(self)
        self.group_builder = GroupBuilder(self)
        self.recruitment = Recruitment(self)
        self.reviewer_identity_readers = []
        self.area_chair_identity_readers = []
        self.senior_area_chair_identity_readers = []        

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

    def get_recruitment_id(self, committee_id):
        return self.get_invitation_id('Recruitment', prefix=committee_id)

    def get_bid_id(self, committee_id):
        return self.get_invitation_id('Bid', prefix=committee_id)

    def get_paper_assignment_id(self, committee_id, deployed=False, invite=False):
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
        reviewers_id = self.get_committee_id('Reviewer_.*' if anon else self.reviewers_name, number)
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
        return self.get_committee_id('Area_Chair_.*' if anon else self.area_chairs_name, number)

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

    def get_homepage_options(self):
        options = {}
        options['title'] = self.name
        options['subtitle'] = self.short_name
        options['website'] = self.website
        options['contact'] = self.contact
        return options

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

    def get_submissions(self, venueid=None, sort=None, details=None):
        return self.client.get_all_notes(content={ 'venueid': venueid if venueid else f'{self.get_submission_venue_id()}'}, sort=sort, details=details)

    def setup(self, program_chair_ids=[]):
    
        venue_id = self.venue_id

        groups = self.group_builder.build_groups(venue_id)
        for i, g in enumerate(groups[:-1]):
            self.group_builder.set_landing_page(g, groups[i-1] if i > 0 else None)

        venue_group = groups[-1]
        print(venue_group)
        self.group_builder.set_home_page(venue_group, groups[-2] if len(groups) > 1 else None)

        ## pc group
        #to-do add pc group webfield
        pc_group_id = self.get_program_chairs_id()
        pc_group = openreview.tools.get_group(self.client, pc_group_id)
        if not pc_group:
            pc_group=self.client.post_group(Group(id=pc_group_id,
                            readers=['everyone'],
                            writers=[venue_id, pc_group_id],
                            signatures=[venue_id],
                            signatories=[pc_group_id, venue_id],
                            members=program_chair_ids
                            ))
        # with open(os.path.join(os.path.dirname(__file__), 'webfield/editorsInChiefWebfield.js')) as f:
        #     content = f.read()
        #     content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
        #     content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{journal.short_name}";')
        #     content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + journal.get_author_submission_id() + "';")
        #     content = content.replace("var EDITORS_IN_CHIEF_NAME = '';", "var EDITORS_IN_CHIEF_NAME = '" + journal.editors_in_chief_name + "';")
        #     content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + journal.reviewers_name + "';")
        #     content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + journal.action_editors_name + "';")
        #     if journal.get_request_form():
        #         content = content.replace("var JOURNAL_REQUEST_ID = '';", "var JOURNAL_REQUEST_ID = '" + journal.get_request_form().id + "';")

        #     editor_in_chief_group.web = content
        #     self.client.post_group(editor_in_chief_group)

        ## Add pcs to have all the permissions
        self.client.add_members_to_group(venue_group, pc_group_id)

        ## authors group
        authors_id = self.get_authors_id()
        authors_group = openreview.tools.get_group(self.client, authors_id)
        if not authors_group:
            authors_group = Group(id=authors_id,
                            readers=[venue_id, authors_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[])

        with open(os.path.join(os.path.dirname(__file__), 'webfield/authorsWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            ##content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.submission_stage.get_submission_id(self) + "';")
            authors_group.web = content
            self.client.post_group(authors_group)

        authors_accepted_id = self.get_authors_accepted_id()
        authors_accepted_group = openreview.tools.get_group(self.client, authors_accepted_id)
        if not authors_accepted_group:
            authors_accepted_group = self.client.post_group(Group(id=authors_accepted_id,
                            readers=[venue_id, authors_accepted_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]))

        self.invitation_builder.set_meta_invitation()

        self.group_builder.create_reviewers_group()
        if self.use_area_chairs:
            self.group_builder.create_area_chairs_group()
        self.client.add_members_to_group('venues', venue_id)
        self.client.add_members_to_group('host', venue_id)

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
        allow_overlap_official_committee = False):

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
        self.group_builder.set_submission_variables()

    def create_review_stage(self):
        invitation = self.invitation_builder.set_review_invitation()
        self.invitation_builder.create_paper_invitations(invitation.id, self.get_submissions())
        self.group_builder.set_review_variables()

    def create_meta_review_stage(self):
        invitation = self.invitation_builder.set_meta_review_invitation()
        self.invitation_builder.create_paper_invitations(invitation.id, self.get_submissions())
        self.group_builder.set_meta_review_variables()

    def setup_post_submission_stage(self, force=False, hide_fields=[]):
        venue_id = self.venue_id
        submissions = self.get_submissions()
        
        self.group_builder.create_paper_committee_groups(submissions)
        
        def update_submission_readers(submission):
            return self.client.post_note_edit(invitation=self.get_meta_invitation_id(),
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(id=submission.id,
                        readers = self.submission_stage.get_readers(self, submission.number)
                    )
                )            
        ## Release the submissions to specified readers
        openreview.tools.concurrent_requests(update_submission_readers, submissions, desc='update_submission_readers')
             
        ## Create revision invitation if there is a second deadline?
        ## Create withdraw and desk reject invitations
        self.invitation_builder.create_paper_invitations(self.get_withdrawal_id(), submissions)
        self.invitation_builder.create_paper_invitations(self.get_desk_rejection_id(), submissions)

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
                print(_decision)
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

            content = {
                'venueid': {
                    'value': tools.pretty_id(venue_id)
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
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(id=submission.id,
                        readers = submission_readers,
                        content = content
                    )
                )

    def send_decision_notifications(self, decision_options, messages):
        paper_notes = self.get_submissions(venueid=tools.pretty_id(self.venue_id), details='directReplies')

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
        
    def setup_committee_matching(self, committee_id=None, compute_affinity_scores=False, compute_conflicts=False, alternate_matching_group=None):
        if committee_id is None:
            committee_id=self.get_reviewers_id()
        if self.use_senior_area_chairs and committee_id == self.get_senior_area_chairs_id() and not alternate_matching_group:
            alternate_matching_group = self.get_area_chairs_id()
        venue_matching = matching.Matching(self, self.client.get_group(committee_id), alternate_matching_group)

        return venue_matching.setup(compute_affinity_scores, compute_conflicts)

    def set_assignments(self, assignment_title, committee_id, enable_reviewer_reassignment=False, overwrite=False):

        match_group = self.client.get_group(committee_id)
        conference_matching = matching.Matching(self, match_group)
        return conference_matching.deploy(assignment_title, overwrite, enable_reviewer_reassignment)