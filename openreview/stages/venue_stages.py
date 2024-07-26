import openreview
import datetime
from enum import Enum
from . import default_content

SHORT_BUFFER_MIN = 30

class IdentityReaders(Enum):
    PROGRAM_CHAIRS = 0
    SENIOR_AREA_CHAIRS = 1
    SENIOR_AREA_CHAIRS_ASSIGNED = 2
    AREA_CHAIRS = 3
    AREA_CHAIRS_ASSIGNED = 4
    REVIEWERS = 5
    REVIEWERS_ASSIGNED = 6

    @classmethod
    def get_readers(self, conference, number, identity_readers):
        readers = [conference.id]
        if self.PROGRAM_CHAIRS in identity_readers:
            readers.append(conference.get_program_chairs_id())
        if self.SENIOR_AREA_CHAIRS in identity_readers:
            readers.append(conference.get_senior_area_chairs_id())
        if self.SENIOR_AREA_CHAIRS_ASSIGNED in identity_readers:
            readers.append(conference.get_senior_area_chairs_id(number))
        if self.AREA_CHAIRS in identity_readers:
            readers.append(conference.get_area_chairs_id())
        if self.AREA_CHAIRS_ASSIGNED in identity_readers:
            readers.append(conference.get_area_chairs_id(number))
        if self.REVIEWERS in identity_readers:
            readers.append(conference.get_reviewers_id())
        if self.REVIEWERS_ASSIGNED in identity_readers:
            readers.append(conference.get_reviewers_id(number))
        return readers

class AuthorReorder(Enum):
        ALLOW_REORDER = 0
        ALLOW_EDIT = 1
        DISALLOW_EDIT = 2

class SubmissionStage(object):

    class Readers(Enum):
        EVERYONE = 0
        SENIOR_AREA_CHAIRS = 1
        SENIOR_AREA_CHAIRS_ASSIGNED = 2
        AREA_CHAIRS = 3
        AREA_CHAIRS_ASSIGNED = 4
        REVIEWERS = 5
        REVIEWERS_ASSIGNED = 6
        EVERYONE_BUT_REJECTED = 7

    def __init__(
            self,
            name='Submission',
            start_date=None,
            due_date=None,
            second_due_date=None,
            readers=[],
            double_blind=False,
            additional_fields={},
            remove_fields=[],
            hide_fields=[],
            subject_areas=[],
            email_pcs=False,
            create_groups=False,
            # We need to assume the Official Review super invitation is already created and active
            create_review_invitation=False,
            withdraw_submission_exp_date=None,
            withdrawn_submission_public=False,
            withdrawn_submission_reveal_authors=False,
            email_pcs_on_withdraw=False,
            desk_rejected_submission_public=False,
            desk_rejected_submission_reveal_authors=False,
            email_pcs_on_desk_reject=False,
            author_names_revealed=False,
            papers_released=False,
            author_reorder_after_first_deadline=AuthorReorder.ALLOW_EDIT,
            submission_email=None,
            force_profiles=False,
            second_deadline_additional_fields={},
            second_deadline_remove_fields=[],
            commitments_venue=False
        ):

        self.start_date = start_date
        self.due_date = due_date
        self.exp_date = (due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if due_date else None
        self.second_due_date = second_due_date
        self.second_due_date_exp_date = (second_due_date + datetime.timedelta(minutes = SHORT_BUFFER_MIN)) if second_due_date else None
        self.name = name
        self.readers = readers
        self.double_blind = double_blind
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.hide_fields = hide_fields
        self.subject_areas = subject_areas
        self.email_pcs = email_pcs
        self.create_groups = create_groups
        self.create_review_invitation = create_review_invitation
        self.withdraw_submission_exp_date = withdraw_submission_exp_date
        self.withdrawn_submission_public = withdrawn_submission_public
        self.withdrawn_submission_reveal_authors = withdrawn_submission_reveal_authors
        self.email_pcs_on_withdraw = email_pcs_on_withdraw
        self.desk_rejected_submission_public = desk_rejected_submission_public
        self.desk_rejected_submission_reveal_authors = desk_rejected_submission_reveal_authors
        self.email_pcs_on_desk_reject = email_pcs_on_desk_reject
        self.author_names_revealed = author_names_revealed
        self.papers_released = papers_released
        self.public = self.Readers.EVERYONE in self.readers
        self.author_reorder_after_first_deadline = author_reorder_after_first_deadline
        self.submission_email = submission_email
        self.withdrawal_name = 'Withdrawal'
        self.desk_rejection_name = 'Desk_Rejection'
        self.force_profiles = force_profiles
        self.second_deadline_additional_fields = second_deadline_additional_fields
        self.second_deadline_remove_fields = second_deadline_remove_fields
        self.commitments_venue = commitments_venue

    def get_readers(self, conference, number, decision=None, accept_options=None):

        if self.Readers.EVERYONE in self.readers:
            return ['everyone']

        submission_readers=[conference.id]
        is_accepted = decision and openreview.tools.is_accept_decision(decision, accept_options)

        if self.Readers.EVERYONE_BUT_REJECTED in self.readers:
            hide = not decision or not is_accepted
            if hide:
                if conference.use_senior_area_chairs:
                    submission_readers.append(conference.get_senior_area_chairs_id(number=number))
                if conference.use_area_chairs:
                    submission_readers.append(conference.get_area_chairs_id(number=number))
                submission_readers.append(conference.get_reviewers_id(number=number))
                submission_readers.append(conference.get_authors_id(number=number))
                return submission_readers
            else:
                return ['everyone']

        if self.Readers.SENIOR_AREA_CHAIRS in self.readers and conference.use_senior_area_chairs:
            submission_readers.append(conference.get_senior_area_chairs_id())

        if self.Readers.SENIOR_AREA_CHAIRS_ASSIGNED in self.readers and conference.use_senior_area_chairs:
            submission_readers.append(conference.get_senior_area_chairs_id(number=number))

        if self.Readers.AREA_CHAIRS in self.readers and conference.use_area_chairs:
            submission_readers.append(conference.get_area_chairs_id())

        if self.Readers.AREA_CHAIRS_ASSIGNED in self.readers and conference.use_area_chairs:
            submission_readers.append(conference.get_area_chairs_id(number=number))

        if self.Readers.REVIEWERS in self.readers:
            submission_readers.append(conference.get_reviewers_id())

        if self.Readers.REVIEWERS_ASSIGNED in self.readers:
            submission_readers.append(conference.get_reviewers_id(number=number))

        if conference.ethics_review_stage and number in conference.ethics_review_stage.submission_numbers:
            if conference.use_ethics_chairs:
                submission_readers.append(conference.get_ethics_chairs_id())
            if conference.use_ethics_reviewers:
                submission_readers.append(conference.get_ethics_reviewers_id(number=number))

        if conference.use_publication_chairs and decision and is_accepted:
            submission_readers.append(conference.get_publication_chairs_id())

        submission_readers.append(conference.get_authors_id(number=number))
        return submission_readers

    def get_invitation_readers(self, conference, under_submission):
        # Rolling review should be release right away
        if self.create_groups:
            return {'values': ['everyone']}

        if under_submission or self.double_blind:
            has_authorids = 'authorids' in self.get_content()
            readers = {
                'values-copied': [
                    conference.get_id()
                ]
            }

            if has_authorids:
                readers['values-copied'].append('{content.authorids}')
            readers['values-copied'].append('{signatures}')

            return readers

        return {
            'values-regex': '.*'
        }

    def get_invitation_writers(self, conference):

        has_authorids = 'authorids' in self.get_content()
        writers = {
            'values-copied': [
                conference.get_id()
            ]
        }

        if has_authorids:
            writers['values-copied'].append('{content.authorids}')
        writers['values-copied'].append('{signatures}')

        return writers


    def get_submission_id(self, conference):
        return conference.get_invitation_id(self.name)

    def get_blind_submission_id(self, conference):
        name = self.name
        if self.double_blind:
            name = 'Blind_' + name
        return conference.get_invitation_id(name)

    def get_withdrawn_submission_id(self, conference):
        return conference.get_invitation_id(f'Withdrawn_{self.name}')

    def get_desk_rejected_submission_id(self, conference):
        return conference.get_invitation_id(f'Desk_Rejected_{self.name}')

    def get_content(self, api_version='1', conference=None, venue_id=None):

        if api_version == '1':
            content = default_content.submission.copy()

            if self.subject_areas:
                content['subject_areas'] = {
                    'order' : 5,
                    'description' : "Select or type subject area",
                    'values-dropdown': self.subject_areas,
                    'required': True
                }

            for field in self.remove_fields:
                del content[field]

            for order, key in enumerate(self.additional_fields, start=10):
                value = self.additional_fields[key]
                value['order'] = order
                content[key] = value

            if self.second_due_date and 'pdf' in content:
                content['pdf']['required'] = False

            if self.force_profiles:
                content['authorids'] = {
                    'description': 'Search author profile by first, middle and last name or email address. All authors must have an OpenReview profile prior to submitting a paper.',
                    'order': 3,
                    'values-regex': r'~.*',
                    'required':True
                }
                
        elif api_version == '2':
            content = default_content.submission_v2.copy()

            if self.subject_areas:
                content['subject_areas'] = {
                    'order' : 5,
                    'description' : "Select or type subject area",
                    'value': {
                        'param': {
                            'type': 'string[]',
                            'enum': self.subject_areas,
                            'input': 'select'                    
                        }
                    }
                }

            for field in self.remove_fields:
                if field == 'TL;DR':
                    field = 'TLDR'
                if field in content:
                    del content[field]
                else:
                    print('Field {} not found in content: {}'.format(field, content))

            for key, value in self.additional_fields.items():
                content[key] = value

            if self.second_due_date and 'pdf' in content:
                content['pdf']['value']['param']['optional'] = True

            if self.force_profiles:
                content['authorids'] = {
                    'order': 3,
                    'description': 'Search author profile by first, middle and last name or email address. All authors must have an OpenReview profile prior to submitting a paper.',
                    'value': {
                        'param': {
                            'type': 'profile[]',
                            'regex': r'~.*',
                        }
                    }
                }

            if self.commitments_venue and 'paper_link' not in content:
                content['paper_link'] = {
                    'value': {
                        'param': {
                            'type': 'string',
                            'regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                            'mismatchError': 'must be a valid link to an OpenReview submission: https://openreview.net/forum?id=...'
                        }
                    },
                    'description': 'Please provide the link to your ARR submission. The link should have the following format: https://openreview.net/forum?id=<PAPER_ID> where <PAPER_ID> is the paper ID of your ARR submission. Make sure to only add the paper id and not other parameters after &.',
                    'order': 8
                }


            if conference:
                submission_id = self.get_submission_id(conference)
                submission_invitation = openreview.tools.get_invitation(conference.client, submission_id)
                if submission_invitation:
                    for field, value in submission_invitation.edit['note']['content'].items():
                        if field not in content:
                            content[field] = { 'delete': True }

                if venue_id:
                    content['venue'] = {
                        'value': {
                            'param': {
                                'const': openreview.tools.pretty_id(venue_id),
                                'hidden': True
                            }
                        }
                    }
                    content['venueid'] = {
                        'value': {
                            'param': {
                                'const': venue_id,
                                'hidden': True
                            }
                        }
                    }

        return content
    
    def get_hidden_field_names(self):
        return (['authors', 'authorids'] if self.double_blind and not self.author_names_revealed else []) + self.hide_fields

    def is_under_submission(self):
        return self.due_date is None or datetime.datetime.utcnow() < self.due_date

    def get_withdrawal_readers(self, conference, number):

        if self.public and self.withdrawn_submission_public:
            return ['everyone']
        else:
            readers = [conference.get_program_chairs_id()]
            if conference.use_senior_area_chairs:
                readers.append(conference.get_senior_area_chairs_id(number))
            if conference.use_area_chairs:
                readers.append(conference.get_area_chairs_id(number))
            readers.append(conference.get_reviewers_id(number))
            readers.append(conference.get_authors_id(number))
            return readers

    def get_desk_rejection_readers(self, conference, number):

        if self.public and self.desk_rejected_submission_public:
            return ['everyone']
        else:
            readers = [conference.get_program_chairs_id()]
            if conference.use_senior_area_chairs:
                readers.append(conference.get_senior_area_chairs_id(number))
            if conference.use_area_chairs:
                readers.append(conference.get_area_chairs_id(number))
            readers.append(conference.get_reviewers_id(number))
            readers.append(conference.get_authors_id(number))
            return readers
        
    def get_submission_tracks(self):
        if self.additional_fields and 'track' in self.additional_fields:
            return self.additional_fields['track']['value']['param']['enum']

class BidStage(object):

    def __init__(self, committee_id, start_date=None, due_date=None, request_count=50, score_ids=[], instructions=False, allow_conflicts_bids=False):
        self.committee_id=committee_id
        self.start_date=start_date
        self.due_date=due_date
        self.name='Bid'
        self.request_count=request_count
        self.score_ids=score_ids
        self.instructions=instructions
        self.allow_conflicts_bids=allow_conflicts_bids
        self.default_scores_spec={
            'weight': 1,
            'default': 0,
            'translate_map' : {
                'Very High': 1.0,
                'High': 0.5,
                'Neutral': 0.0,
                'Low': -0.5,
                'Very Low': -1.0
            }
        }

    def get_invitation_readers(self, conference):
        readers = [conference.get_id()]
        if self.committee_id == conference.get_reviewers_id():
            if conference.use_senior_area_chairs:
                readers.append(conference.get_senior_area_chairs_id())
            if conference.use_area_chairs:
                readers.append(conference.get_area_chairs_id())
        if self.committee_id == conference.get_area_chairs_id():
            if conference.use_senior_area_chairs:
                readers.append(conference.get_senior_area_chairs_id())
        readers.append(self.committee_id)
        return readers

    def get_readers(self, conference):
        values_copied = [conference.get_id()]
        if self.committee_id == conference.get_reviewers_id():
            if conference.use_senior_area_chairs:
                values_copied.append(conference.get_senior_area_chairs_id())
            if conference.use_area_chairs:
                values_copied.append(conference.get_area_chairs_id())
        if self.committee_id == conference.get_area_chairs_id():
            if conference.use_senior_area_chairs:
                values_copied.append(conference.get_senior_area_chairs_id())
        values_copied.append('{signatures}')
        return values_copied

    def get_bid_options(self):
        options = ['Very High', 'High', 'Neutral', 'Low', 'Very Low']
        if self.allow_conflicts_bids:
            options.append('Conflict')
        return options

    def get_score_ids(self):
        if self.score_ids:
            return self.score_ids

        return [self.committee_id + '/-/Affinity_Score']

    def get_instructions(self):
        if self.instructions:
            return self.instructions

        sorted_tip = ''
        if self.score_ids:
            sorted_tip = '''
            <li>
                Papers are sorted based on keyword similarity with the papers
                that you provided in the Expertise Selection Interface.
            </li>'''

        return f'''<p class="dark"><strong>Instructions:</strong></p>
<ul>
    <li>
        Please indicate your <strong>level of interest</strong> in
        reviewing the submitted papers below,
        on a scale from "Very Low" interest to "Very High" interest.
    </li>
    <li>
        Please bid on as many papers as possible
        to ensure that your preferences are taken into account.
    </li>
    <li>
        Use the search field to filter papers by keyword or subject area.
    </li>
    <li>
        Ensure that you have at least <strong>{self.request_count} bids</strong>.
    </li>
</ul>
<p class="dark"><strong>A few tips:</strong></p>
<ul>
    <li>
        Papers for which you have a conflict of interest are not shown.
    </li>
    <li>
        Positive bids ("High" and "Very High") will, in most cases, increase the likelihood that you will be assigned that paper.
    </li>
    <li>
        Negative bids ("Low" and "Very Low") will, in most cases, decrease the likelihood that you will be assigned that paper.
    </li>
    {sorted_tip}
</ul>
<br>'''

class ExpertiseSelectionStage(object):

    def __init__(self, start_date = None, due_date = None, include_option = False):
        self.start_date = start_date
        self.due_date = due_date
        self.name = 'Expertise_Selection'
        self.include_option = include_option

class SubmissionRevisionStage():

    def __init__(self, name='Revision', start_date=None, due_date=None, additional_fields={}, remove_fields=[], only_accepted=False, multiReply=None, allow_author_reorder=False, allow_license_edition=False):
        self.name = name
        self.start_date = start_date
        self.due_date = due_date
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.only_accepted = only_accepted
        self.multiReply=multiReply
        self.allow_author_reorder=allow_author_reorder
        self.allow_license_edition=allow_license_edition

    def get_content(self, api_version='2', conference=None):
        
        content = conference.submission_stage.get_content(api_version, conference).copy()

        for field in self.remove_fields:
            if field in content:
                del content[field]
            else:
                print('Field {} not found in content: {}'.format(field, content))

        for key, value in self.additional_fields.items():
            content[key] = value

        if self.allow_author_reorder == AuthorReorder.ALLOW_REORDER:
            content['authors'] = {
                'value': {
                    'param': {
                        'type': 'string[]',
                        'const': ['${{6/id}/content/authors/value}'],
                        'hidden': True,
                    }
                },
                'order': 3
            }
            content['authorids'] = {
                'value': ['${{4/id}/content/authorids/value}'],
                'order':4
            }
        elif self.allow_author_reorder == AuthorReorder.DISALLOW_EDIT:
            if 'authors' in content:
                del content['authors']
            if 'authorids' in content:
                del content['authorids']

        if conference:
            invitation_id = conference.get_invitation_id(self.name)
            invitation = openreview.tools.get_invitation(conference.client, invitation_id)
            if invitation:
                for field, value in invitation.edit.get('invitation', {}).get('edit', {}).get('note', {}).get('content', {}).items() if invitation.edit else {}:
                    if field not in content:
                        content[field] = { 'delete': True }

        
        return content        

class ReviewStage(object):

    class Readers(Enum):
        REVIEWERS = 0
        REVIEWERS_ASSIGNED = 1
        REVIEWERS_SUBMITTED = 2
        REVIEWER_SIGNATURE = 3

    def __init__(self,
        start_date = None,
        due_date = None,
        exp_date = None,
        name = None,
        allow_de_anonymization = False,
        public = False,
        release_to_authors = False,
        release_to_reviewers = Readers.REVIEWER_SIGNATURE,
        email_pcs = False,
        additional_fields = {},
        remove_fields = [],
        rating_field_name = 'rating',
        confidence_field_name = 'confidence',
        source_submissions_query = {},
        child_invitations_name = 'Official_Review'
    ):

        self.start_date = start_date
        self.due_date = due_date
        self.exp_date = exp_date
        self.name = 'Official_Review'
        if name:
            self.name = name
        self.allow_de_anonymization = allow_de_anonymization
        self.public = public
        self.release_to_authors = release_to_authors
        self.release_to_reviewers = release_to_reviewers
        self.email_pcs = email_pcs
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.rating_field_name = rating_field_name
        self.confidence_field_name = confidence_field_name
        self.source_submissions_query = source_submissions_query
        self.child_invitations_name = child_invitations_name
        self.process_path = 'process/review_process.py'
        self.preprocess_path = None

    def _get_reviewer_readers(self, conference, number, review_signature=None):
        if self.release_to_reviewers is ReviewStage.Readers.REVIEWERS:
            return conference.get_reviewers_id()
        if self.release_to_reviewers is ReviewStage.Readers.REVIEWERS_ASSIGNED:
            return conference.get_reviewers_id(number = number)
        if self.release_to_reviewers is ReviewStage.Readers.REVIEWERS_SUBMITTED:
            return conference.get_reviewers_id(number = number) + '/Submitted'
        if self.release_to_reviewers is ReviewStage.Readers.REVIEWER_SIGNATURE:
            if review_signature:
                return review_signature
            return '{signatures}'
        raise openreview.OpenReviewException('Unrecognized readers option')

    def get_readers(self, conference, number, review_signature=None):

        if self.public:
            return ['everyone']

        readers = [ conference.get_program_chairs_id()]

        if conference.use_senior_area_chairs:
            readers.append(conference.get_senior_area_chairs_id(number = number))

        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(number = number))

        readers.append(self._get_reviewer_readers(conference, number, review_signature))

        ## Workaround to make the reviews visible to the author of the review when reviewers submitted is selected
        if self.release_to_reviewers is ReviewStage.Readers.REVIEWERS_SUBMITTED and review_signature:
            readers.append(review_signature)

        if conference.ethics_review_stage and number in conference.ethics_review_stage.submission_numbers:
            if conference.use_ethics_chairs:
                readers.append(conference.get_ethics_chairs_id())
            if conference.use_ethics_reviewers:
                readers.append(conference.get_ethics_reviewers_id(number=number))

        if self.release_to_authors:
            readers.append(conference.get_authors_id(number = number))

        return readers

    def get_nonreaders(self, conference, number):

        if self.public:
            return []

        if self.release_to_authors:
            return []

        return [conference.get_authors_id(number = number)]

    def get_signatures(self, conference, number):
        if self.allow_de_anonymization:
            return ['~.*']

        return [conference.get_anon_reviewer_id(number=number, anon_id='.*')]
    
    def get_content(self, api_version='2', conference=None):

        content = default_content.review_v2.copy()

        for field in self.remove_fields:
            if field in content:
                del content[field]
            else:
                print('Field {} not found in content: {}'.format(field, content))

        for key, value in self.additional_fields.items():
            content[key] = value

        if conference:
            invitation_id = conference.get_invitation_id(self.name)
            invitation = openreview.tools.get_invitation(conference.client, invitation_id)
            if invitation:
                for field, value in invitation.edit.get('invitation', {}).get('edit', {}).get('note', {}).get('content', {}).items() if invitation.edit else {}:
                    if field not in content:
                        content[field] = { 'delete': True }

        return content
class EthicsReviewStage(object):

    class Readers(Enum):
        ALL_COMMITTEE = 0
        ALL_ASSIGNED_COMMITTEE = 1
        ASSIGNED_ETHICS_REVIEWERS = 2
        ETHICS_REVIEWERS_SUBMITTED = 3
        ETHICS_REVIEWER_SIGNATURE = 4

    def __init__(self,
        start_date = None,
        due_date = None,
        exp_date = None,
        name = None,
        release_to_public = False,
        release_to_authors = False,
        release_to_reviewers = Readers.ETHICS_REVIEWER_SIGNATURE,
        additional_fields = {},
        remove_fields = [],
        submission_numbers = [],
        enable_comments = False,
        release_to_chairs = False,
        compute_affinity_scores = None
    ):

        self.start_date = start_date
        self.due_date = due_date
        self.exp_date = exp_date
        self.name = name if name else 'Ethics_Review'
        self.release_to_public = release_to_public
        self.release_to_authors = release_to_authors
        self.release_to_reviewers = release_to_reviewers
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.submission_numbers = submission_numbers
        self.enable_comments = enable_comments
        self.process_path = 'process/ethics_review_process.py'
        self.flag_process_path = 'process/ethics_flag_process.py'
        self.preprocess_path = None
        self.release_to_chairs = release_to_chairs
        self.compute_affinity_scores = compute_affinity_scores     

    def get_readers(self, conference, number, ethics_review_signature=None):

        if self.release_to_public:
            return ['everyone']

        readers = [ conference.get_program_chairs_id()]

        if self.release_to_reviewers == self.Readers.ALL_COMMITTEE:
            if conference.use_senior_area_chairs:
                readers.append(conference.get_senior_area_chairs_id())

            if conference.use_area_chairs:
                readers.append(conference.get_area_chairs_id())

            readers.append(conference.get_reviewers_id())

            if conference.use_ethics_chairs:
                readers.append(conference.get_ethics_chairs_id())

            readers.append(conference.get_ethics_reviewers_id())

        if self.release_to_reviewers == self.Readers.ALL_ASSIGNED_COMMITTEE:
            if conference.use_senior_area_chairs:
                readers.append(conference.get_senior_area_chairs_id(number=number))

            if conference.use_area_chairs:
                readers.append(conference.get_area_chairs_id(number=number))

            readers.append(conference.get_reviewers_id(number=number))

            if conference.use_ethics_chairs:
                readers.append(conference.get_ethics_chairs_id())

            readers.append(conference.get_ethics_reviewers_id(number=number))

        if self.release_to_reviewers == self.Readers.ASSIGNED_ETHICS_REVIEWERS:

            if conference.use_ethics_chairs:
                readers.append(conference.get_ethics_chairs_id())

            readers.append(conference.get_ethics_reviewers_id(number=number))

        if self.release_to_reviewers == self.Readers.ETHICS_REVIEWERS_SUBMITTED:

            if conference.use_ethics_chairs:
                readers.append(conference.get_ethics_chairs_id())

            readers.append(conference.get_ethics_reviewers_id(number=number) + '/Submitted')
            if ethics_review_signature:
                readers.append(ethics_review_signature)

        if self.release_to_reviewers == self.Readers.ETHICS_REVIEWER_SIGNATURE:

            if conference.use_ethics_chairs:
                readers.append(conference.get_ethics_chairs_id())

            if ethics_review_signature:
                readers.append(ethics_review_signature)
            else:
                readers.append('{signatures}')

        if self.release_to_authors:
            readers.append(conference.get_authors_id(number = number))

        return readers

    def get_nonreaders(self, conference, number):

        if self.release_to_public:
            return []

        if self.release_to_authors:
            return []

        return [conference.get_authors_id(number = number)]

    def get_signatures(self, conference, number):
        return [conference.get_anon_reviewer_id(number=number, anon_id='.*', name=conference.ethics_reviewers_name), conference.get_program_chairs_id()]

    def get_content(self, api_version='2', conference=None):

        content = default_content.ethics_review_v2.copy()

        for field in self.remove_fields:
            if field in content:
                del content[field]
            else:
                print('Field {} not found in content: {}'.format(field, content))
        
        for key, value in self.additional_fields.items():
            content[key] = value

        if conference:
            invitation_id = conference.get_invitation_id(self.name)
            invitation = openreview.tools.get_invitation(conference.client, invitation_id)
            if invitation:
                for field, value in invitation.edit.get('invitation', {}).get('edit', {}).get('note', {}).get('content', {}).items() if invitation.edit else {}:
                    if field not in content:
                        content[field] = { 'delete': True }

        return content

class ReviewRebuttalStage(object):

    class Readers(Enum):
        EVERYONE = 0
        SENIOR_AREA_CHAIRS = 1
        SENIOR_AREA_CHAIRS_ASSIGNED = 2
        AREA_CHAIRS = 3
        AREA_CHAIRS_ASSIGNED = 4
        REVIEWERS = 5
        REVIEWERS_ASSIGNED = 6
        REVIEWERS_SUBMITTED = 7

    def __init__(self, start_date = None, due_date = None, name = 'Rebuttal', email_pcs = False, additional_fields = {}, single_rebuttal = False, unlimited_rebuttals = False, readers = []):
        self.start_date = start_date
        self.due_date = due_date
        self.name = name
        self.email_pcs = email_pcs
        self.additional_fields = additional_fields
        self.remove_fields = []
        self.single_rebuttal = single_rebuttal
        self.unlimited_rebuttals = unlimited_rebuttals
        self.readers = readers

    def get_invitation_readers(self, conference, number):

        if self.Readers.EVERYONE in self.readers:
            return ['everyone']
        
        invitation_readers=[conference.get_program_chairs_id()]

        if self.Readers.SENIOR_AREA_CHAIRS in self.readers and conference.use_senior_area_chairs:
            invitation_readers.append(conference.get_senior_area_chairs_id())

        if self.Readers.SENIOR_AREA_CHAIRS_ASSIGNED in self.readers and conference.use_senior_area_chairs:
            invitation_readers.append(conference.get_senior_area_chairs_id(number=number))

        if self.Readers.AREA_CHAIRS in self.readers and conference.use_area_chairs:
            invitation_readers.append(conference.get_area_chairs_id())

        if self.Readers.AREA_CHAIRS_ASSIGNED in self.readers and conference.use_area_chairs:
            invitation_readers.append(conference.get_area_chairs_id(number=number))

        if self.Readers.REVIEWERS in self.readers:
            invitation_readers.append(conference.get_reviewers_id())

        if self.Readers.REVIEWERS_ASSIGNED in self.readers:
            invitation_readers.append(conference.get_reviewers_id(number=number))

        if self.Readers.REVIEWERS_SUBMITTED in self.readers:
            invitation_readers.append(conference.get_reviewers_id(number=number) + '/Submitted')

        if conference.ethics_review_stage and number in conference.ethics_review_stage.submission_numbers:
            if conference.use_ethics_chairs:
                invitation_readers.append(conference.get_ethics_chairs_id())
            if conference.use_ethics_reviewers:
                invitation_readers.append(conference.get_ethics_reviewers_id(number=number))

        invitation_readers.append(conference.get_authors_id(number=number))
        return invitation_readers        

    def get_content(self, api_version='2', conference=None):
        
        content = default_content.rebuttal_v2.copy()

        for field in self.remove_fields:
            if field in content:
                del content[field]
            else:
                print('Field {} not found in content: {}'.format(field, content))

        for key, value in self.additional_fields.items():
            content[key] = value

        if conference:
            invitation_id = conference.get_invitation_id(self.name)
            invitation = openreview.tools.get_invitation(conference.client, invitation_id)
            if invitation:
                for field, value in invitation.edit.get('invitation', {}).get('edit', {}).get('note', {}).get('content', {}).items() if invitation.edit else {}:
                    if field not in content:
                        content[field] = { 'delete': True }

        return content

class ReviewRevisionStage(object):

    def __init__(self, start_date = None, due_date = None, name = 'Review_Revision', additional_fields = {}, remove_fields = []):
        self.start_date = start_date
        self.due_date = due_date
        self.name = name
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields

class ReviewRatingStage(object):

    class Readers(Enum):
        REVIEWERS = 0
        REVIEWERS_ASSIGNED = 1
        REVIEWERS_SUBMITTED = 2
        REVIEWER_SIGNATURE = 3
        NO_REVIEWERS = 4

    def __init__(self, start_date = None, due_date = None, name = 'Review_Rating', additional_fields = {}, remove_fields = [], public = False, release_to_reviewers = Readers.NO_REVIEWERS):
        self.start_date = start_date
        self.due_date = due_date
        self.name = name
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.public = public
        self.release_to_reviewers = release_to_reviewers

    def _get_reviewer_readers(self, conference, number, review_signature):
        if self.release_to_reviewers is ReviewRatingStage.Readers.REVIEWERS:
            return conference.get_reviewers_id()
        if self.release_to_reviewers is ReviewRatingStage.Readers.REVIEWERS_ASSIGNED:
            return conference.get_reviewers_id(number = number)
        if self.release_to_reviewers is ReviewRatingStage.Readers.REVIEWERS_SUBMITTED:
            return conference.get_reviewers_id(number = number) + '/Submitted'
        if self.release_to_reviewers is ReviewRatingStage.Readers.REVIEWER_SIGNATURE:
            return review_signature
        raise openreview.OpenReviewException('Unrecognized readers option')

    def get_readers(self, conference, number, review_signature):

        if self.public:
            return ['everyone']

        readers = [ conference.get_program_chairs_id()]

        if conference.use_area_chairs:
            readers.append('{signatures}')

        if self.release_to_reviewers is not ReviewRatingStage.Readers.NO_REVIEWERS:
            readers.append(self._get_reviewer_readers(conference, number, review_signature))

        return readers

class CommentStage(object):

    class Readers(Enum):
        EVERYONE = 0
        SENIOR_AREA_CHAIRS_ASSIGNED = 1
        AREA_CHAIRS_ASSIGNED = 2
        REVIEWERS_ASSIGNED = 3
        REVIEWERS_SUBMITTED = 4
        AUTHORS = 5

    def __init__(self,
        official_comment_name=None,
        start_date=None,
        end_date=None,
        allow_public_comments=False,
        anonymous=False,
        reader_selection=False,
        email_pcs=False,
        email_sacs = False,
        only_accepted=False,
        check_mandatory_readers=False,
        readers=[],
        invitees=[],
        enable_chat=False):

        self.official_comment_name = official_comment_name if official_comment_name else 'Official_Comment'
        self.public_name = 'Public_Comment'
        self.start_date = start_date
        self.end_date = end_date
        self.allow_public_comments = allow_public_comments
        self.anonymous = anonymous
        self.reader_selection = reader_selection
        self.email_pcs = email_pcs
        self.email_sacs = email_sacs
        self.only_accepted=only_accepted
        self.check_mandatory_readers=check_mandatory_readers
        self.readers = readers
        self.invitees = invitees
        self.enable_chat = enable_chat

    def get_readers(self, conference, number, api_version='1'):

        if api_version == '2' and self.reader_selection:

            readers  = []
            is_everyone_included = self.allow_public_comments or self.Readers.EVERYONE in self.readers

            if is_everyone_included:
                readers.append({ 'value': 'everyone', 'optional': True })

            readers.append({ 'value': conference.get_program_chairs_id(), 'optional': False })

            if conference.use_senior_area_chairs and self.Readers.SENIOR_AREA_CHAIRS_ASSIGNED in self.readers:
                readers.append({ 'value': conference.get_senior_area_chairs_id(number), 'optional': False })

            if conference.use_area_chairs and self.Readers.AREA_CHAIRS_ASSIGNED in self.readers:
                readers.append({ 'value': conference.get_area_chairs_id(number), 'optional': True })

            if self.Readers.REVIEWERS_ASSIGNED in self.readers:
                readers.append({ 'value': conference.get_reviewers_id(number), 'optional': True })

            if self.Readers.REVIEWERS_SUBMITTED in self.readers:
                readers.append({ 'value': conference.get_reviewers_id(number) + '/Submitted', 'optional': True })

            if self.Readers.REVIEWERS_ASSIGNED in self.readers or self.Readers.REVIEWERS_SUBMITTED in self.readers:
                readers.append({ 'prefix': conference.get_anon_reviewer_id(number=number, anon_id='.*'), 'optional': True })

            if self.Readers.AUTHORS in self.readers:
                readers.append({ 'value': conference.get_authors_id(number), 'optional': True })                

            return readers

        readers = [conference.get_program_chairs_id()]

        if self.allow_public_comments or self.Readers.EVERYONE in self.readers:
            readers.append('everyone')

        if self.reader_selection:
            readers.append(conference.get_anon_reviewer_id(number=number, anon_id='.*'))

        if conference.use_senior_area_chairs and self.Readers.SENIOR_AREA_CHAIRS_ASSIGNED in self.readers:
            readers.append(conference.get_senior_area_chairs_id(number))

        if conference.use_area_chairs and self.Readers.AREA_CHAIRS_ASSIGNED in self.readers:
            readers.append(conference.get_area_chairs_id(number))

        if self.Readers.REVIEWERS_ASSIGNED in self.readers:
            readers.append(conference.get_reviewers_id(number))

        if self.Readers.REVIEWERS_SUBMITTED in self.readers:
            readers.append(conference.get_reviewers_id(number) + '/Submitted')

        if self.Readers.AUTHORS in self.readers:
            readers.append(conference.get_authors_id(number))

        return readers

    def get_signatures(self, conference, number):

        committee = [conference.get_program_chairs_id()]

        if conference.use_senior_area_chairs and self.Readers.SENIOR_AREA_CHAIRS_ASSIGNED in self.invitees:
            committee.append(conference.get_senior_area_chairs_id(number))

        if conference.use_area_chairs and self.Readers.AREA_CHAIRS_ASSIGNED in self.invitees:
            committee.append(conference.get_anon_area_chair_id(number=number, anon_id='.*'))

        if conference.use_secondary_area_chairs and self.Readers.AREA_CHAIRS_ASSIGNED in self.invitees:
            committee.append(conference.get_anon_secondary_area_chair_id(number=number, anon_id='.*'))

        if self.Readers.REVIEWERS_ASSIGNED in self.invitees or self.Readers.REVIEWERS_SUBMITTED in self.invitees:
            committee.append(conference.get_anon_reviewer_id(number=number, anon_id='.*'))

        if self.Readers.AUTHORS in self.invitees:
            committee.append(conference.get_authors_id(number))

        return committee

    def get_invitees(self, conference, number):
        invitees = [conference.get_id(), conference.support_user]

        if conference.use_senior_area_chairs and self.Readers.SENIOR_AREA_CHAIRS_ASSIGNED in self.invitees:
            invitees.append(conference.get_senior_area_chairs_id(number))

        if conference.use_area_chairs and self.Readers.AREA_CHAIRS_ASSIGNED in self.invitees:
            invitees.append(conference.get_area_chairs_id(number))

        if self.Readers.REVIEWERS_ASSIGNED in self.invitees:
            invitees.append(conference.get_reviewers_id(number))

        if self.Readers.REVIEWERS_SUBMITTED in self.invitees:
            invitees.append(conference.get_reviewers_id(number) + '/Submitted')

        if self.Readers.AUTHORS in self.invitees:
            invitees.append(conference.get_authors_id(number))

        return invitees

    def get_chat_invitees(self, conference, number):
        invitees = [conference.get_id(), conference.support_user]

        if conference.use_senior_area_chairs and self.Readers.SENIOR_AREA_CHAIRS_ASSIGNED in self.invitees:
            invitees.append(conference.get_senior_area_chairs_id(number))

        if conference.use_area_chairs and self.Readers.AREA_CHAIRS_ASSIGNED in self.invitees:
            invitees.append(conference.get_area_chairs_id(number))

        if self.Readers.REVIEWERS_ASSIGNED in self.invitees:
            invitees.append(conference.get_reviewers_id(number))

        if self.Readers.REVIEWERS_SUBMITTED in self.invitees:
            invitees.append(conference.get_reviewers_id(number) + '/Submitted')

        return invitees
    
    def get_chat_signatures(self, conference, number):

        committee = [conference.get_program_chairs_id()]

        if conference.use_senior_area_chairs and self.Readers.SENIOR_AREA_CHAIRS_ASSIGNED in self.invitees:
            committee.append(conference.get_senior_area_chairs_id(number))

        if conference.use_area_chairs and self.Readers.AREA_CHAIRS_ASSIGNED in self.invitees:
            committee.append(conference.get_anon_area_chair_id(number=number, anon_id='.*'))

        if conference.use_secondary_area_chairs and self.Readers.AREA_CHAIRS_ASSIGNED in self.invitees:
            committee.append(conference.get_anon_secondary_area_chair_id(number=number, anon_id='.*'))

        if self.Readers.REVIEWERS_ASSIGNED in self.invitees or self.Readers.REVIEWERS_SUBMITTED in self.invitees:
            committee.append(conference.get_anon_reviewer_id(number=number, anon_id='.*'))

        return committee    

    def get_chat_readers(self, conference, number, api_version='1'):

        readers = [conference.get_program_chairs_id()]

        if conference.use_senior_area_chairs and self.Readers.SENIOR_AREA_CHAIRS_ASSIGNED in self.readers:
            readers.append(conference.get_senior_area_chairs_id(number))

        if conference.use_area_chairs and self.Readers.AREA_CHAIRS_ASSIGNED in self.readers:
            readers.append(conference.get_area_chairs_id(number))

        if self.Readers.REVIEWERS_ASSIGNED in self.readers:
            readers.append(conference.get_reviewers_id(number))

        if self.Readers.REVIEWERS_SUBMITTED in self.readers:
            readers.append(conference.get_reviewers_id(number) + '/Submitted')               

        return readers

    def get_mandatory_readers(self, conference, number):
        readers = [conference.get_program_chairs_id()]
        if conference.use_senior_area_chairs:
            readers.append(conference.get_senior_area_chairs_id(number))
        return readers


class MetaReviewStage(object):

    class Readers(Enum):
        REVIEWERS = 0
        REVIEWERS_ASSIGNED = 1
        REVIEWERS_SUBMITTED = 2
        NO_REVIEWERS = 3

    def __init__(self, name='Meta_Review', start_date = None, due_date = None, exp_date = None, public = False, release_to_authors = False, release_to_reviewers = Readers.NO_REVIEWERS, additional_fields = {}, remove_fields=[], process = None, recommendation_field_name = 'recommendation', source_submissions_query = {}, child_invitations_name = 'Meta_Review', content=None):

        self.start_date = start_date
        self.due_date = due_date
        self.exp_date = exp_date
        self.name = name
        self.public = public
        self.release_to_authors = release_to_authors
        self.release_to_reviewers = release_to_reviewers
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields
        self.process = None
        self.recommendation_field_name = recommendation_field_name
        self.process_path = 'process/metareview_process.py'
        self.preprocess_path = None        
        self.source_submissions_query = source_submissions_query
        self.child_invitations_name = child_invitations_name
        self.content = content

    def _get_reviewer_readers(self, conference, number):
        if self.release_to_reviewers is MetaReviewStage.Readers.REVIEWERS:
            return conference.get_reviewers_id()
        if self.release_to_reviewers is MetaReviewStage.Readers.REVIEWERS_ASSIGNED:
            return conference.get_reviewers_id(number = number)
        if self.release_to_reviewers is MetaReviewStage.Readers.REVIEWERS_SUBMITTED:
            return conference.get_reviewers_id(number = number) + '/Submitted'
        raise openreview.OpenReviewException('Unrecognized readers option')

    def get_readers(self, conference, number):

        if self.public:
            return ['everyone']

        readers = []

        if conference.use_senior_area_chairs:
            readers.append(conference.get_senior_area_chairs_id(number = number))

        if conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(number = number))

        if self.release_to_authors:
            readers.append(conference.get_authors_id(number = number))

        if self.release_to_reviewers is not MetaReviewStage.Readers.NO_REVIEWERS:
            readers.append(self._get_reviewer_readers(conference, number))
        readers.append(conference.get_program_chairs_id())

        return readers
    
    def get_writers(self, conference, number):

        writers = [conference.id]

        if conference.use_senior_area_chairs:
            writers.append(conference.get_senior_area_chairs_id(number = number))

        writers.append('${3/signatures}')

        return writers

    def get_nonreaders(self, conference, number):

        if self.public:
            return []

        if self.release_to_authors:
            return []

        return [conference.get_authors_id(number = number)]

    def get_signatures(self, conference, number):

        committee = [conference.get_program_chairs_id()]

        if conference.use_area_chairs:
            committee.append(conference.get_anon_area_chair_id(number=number, anon_id='.*'))

        return committee

    def get_content(self, api_version='2', conference=None):

        if self.content:
            return self.content
        
        content = default_content.meta_review_v2.copy()

        for field in self.remove_fields:
            if field in content:
                del content[field]
            else:
                print('Field {} not found in content: {}'.format(field, content))

        for key, value in self.additional_fields.items():
            content[key] = value

        if conference:
            invitation_id = conference.get_invitation_id(self.name)
            invitation = openreview.tools.get_invitation(conference.client, invitation_id)
            if invitation:
                for field, value in invitation.edit.get('invitation', {}).get('edit', {}).get('note', {}).get('content', {}).items() if invitation.edit else {}:
                    if field not in content:
                        content[field] = { 'delete': True }

        return content

class MetaReviewRevisionStage(object):

    def __init__(self, start_date = None, due_date = None, name = 'Meta_Review_Revision', additional_fields = {}, remove_fields = []):
        self.start_date = start_date
        self.due_date = due_date
        self.name = name
        self.additional_fields = additional_fields
        self.remove_fields = remove_fields

class DecisionStage(object):

    def __init__(self, name = 'Decision', options = None, accept_options = None, start_date = None, due_date = None, public = False, release_to_authors = False, release_to_reviewers = False, release_to_area_chairs = False, email_authors = False, additional_fields = {}, decisions_file=None, content=None):
        if not options:
            options = ['Accept (Oral)', 'Accept (Poster)', 'Reject']
        self.options = options
        self.accept_options = accept_options
        self.start_date = start_date
        self.due_date = due_date
        self.name = name
        self.public = public
        self.release_to_authors = release_to_authors
        self.release_to_reviewers = release_to_reviewers
        self.release_to_area_chairs = release_to_area_chairs
        self.email_authors = email_authors
        self.additional_fields = additional_fields
        self.decisions_file = decisions_file
        self.decision_field_name = 'decision'
        self.remove_fields = []
        self.content = content

    def get_readers(self, conference, number):

        if self.public:
            return ['everyone']

        readers = [ conference.get_program_chairs_id()]
        if self.release_to_area_chairs and conference.use_senior_area_chairs:
            readers.append(conference.get_senior_area_chairs_id(number = number))

        if self.release_to_area_chairs and conference.use_area_chairs:
            readers.append(conference.get_area_chairs_id(number = number))

        if self.release_to_reviewers:
            readers.append(conference.get_reviewers_id(number = number))

        if self.release_to_authors:
            readers.append(conference.get_authors_id(number = number))

        return readers

    def get_nonreaders(self, conference, number):

        if self.public:
            return []

        if self.release_to_authors:
            return []

        return [conference.get_authors_id(number = number)]
    
    def get_content(self, api_version='2', conference=None):

        if self.content:
            if 'decision' in self.content:
                self.content['decision']['value']['param']['enum'] = self.options
            return self.content
        
        content = default_content.decision_v2.copy()

        for field in self.remove_fields:
            if field in content:
                del content[field]
            else:
                print('Field {} not found in content: {}'.format(field, content))

        for key, value in self.additional_fields.items():
            content[key] = value

        if conference:
            invitation_id = conference.get_invitation_id(self.name)
            invitation = openreview.tools.get_invitation(conference.client, invitation_id)
            if invitation:
                for field, value in invitation.edit.get('invitation', {}).get('edit', {}).get('note', {}).get('content', {}).items() if invitation.edit else {}:
                    if field not in content:
                        content[field] = { 'delete': True }

        
        if 'decision' in content:
            content['decision']['value']['param']['enum'] = self.options
        return content    

class RegistrationStage(object):

    def __init__(self, committee_id, name='Registration', start_date=None, due_date=None, expdate=None, additional_fields={}, instructions=None, title=None, remove_fields=[]):
        self.committee_id = committee_id
        self.name = name
        self.start_date = start_date
        self.due_date = due_date
        self.expdate = expdate
        self.additional_fields = additional_fields
        self.instructions = instructions
        self.title = title
        self.remove_fields = remove_fields

    def get_content(self, api_version='2', conference=None):
        
        content = {
            'profile_confirmed': {
                'description': 'In order to avoid conflicts of interest in reviewing, we ask that all reviewers take a moment to update their OpenReview profiles (link in instructions above) with their latest information regarding email addresses, work history and professional relationships. Please confirm that your OpenReview profile is up-to-date by selecting "Yes".\n\n',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': ['Yes'],
                        'input': 'checkbox'
                    }
                },
                'order': 1
            },
            'expertise_confirmed': {
                'description': 'We will be using OpenReview\'s Expertise System as a factor in calculating paper-reviewer affinity scores. Please take a moment to ensure that your latest papers are visible at the Expertise Selection (link in instructions above). Please confirm finishing this step by selecting "Yes".\n\n',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': ['Yes'],
                        'input': 'checkbox'
                    }
                },
                'order': 2
            }
        }

        for field in self.remove_fields:
            if field in content:
                del content[field]
            else:
                print('Field {} not found in content: {}'.format(field, content))

        for key, value in self.additional_fields.items():
            content[key] = value

        if conference:
            invitation_id = conference.get_invitation_id(self.name)
            invitation = openreview.tools.get_invitation(conference.client, invitation_id)
            if invitation:
                for field, value in invitation.edit.get('invitation', {}).get('edit', {}).get('note', {}).get('content', {}).items() if invitation.edit else {}:
                    if field not in content:
                        content[field] = { 'delete': True }

        return content
class CustomStage(object):
    """
    param reply_to: submission, reviews, metareviews, forum
    type reply_to: string
    """

    class Participants(Enum):
        EVERYONE = 0
        SENIOR_AREA_CHAIRS = 1
        SENIOR_AREA_CHAIRS_ASSIGNED = 2
        AREA_CHAIRS = 3
        AREA_CHAIRS_ASSIGNED = 4
        SECONDARY_AREA_CHAIRS = 5
        REVIEWERS = 6
        REVIEWERS_ASSIGNED = 7
        REVIEWERS_SUBMITTED = 8
        AUTHORS = 9
        ETHICS_CHAIRS = 10
        ETHICS_REVIEWERS_ASSIGNED = 11
        SIGNATURES = 12
        PROGRAM_CHAIRS = 13

    class Source(Enum):
        ALL_SUBMISSIONS = 0
        ACCEPTED_SUBMISSIONS = 1
        PUBLIC_SUBMISSIONS = 2
        FLAGGED_SUBMISSIONS = 3

    class ReplyTo(Enum):
        FORUM = 0
        WITHFORUM = 1
        REVIEWS = 2
        METAREVIEWS = 3

    class ReplyType(Enum):
        REPLY = 0
        REVISION = 1

    def __init__(self, name, reply_to, source, reply_type=ReplyType.REPLY, start_date=None, due_date=None, exp_date=None, invitees=[], readers=[], content={}, multi_reply = False, email_pcs = False, email_sacs = False, notify_readers=False, email_template=None, allow_de_anonymization=False):
        self.name = name
        self.reply_to = reply_to
        self.source = source
        self.reply_type = reply_type
        self.start_date = start_date
        self.due_date = due_date
        self.exp_date = exp_date
        self.invitees = invitees
        self.readers = readers
        self.content = content
        self.multi_reply = multi_reply
        self.email_pcs = email_pcs
        self.email_sacs = email_sacs
        self.notify_readers = notify_readers
        self.email_template = email_template
        self.allow_de_anonymization = allow_de_anonymization

    def get_invitees(self, conference, number):
        invitees = [conference.id]

        if conference.use_senior_area_chairs and self.Participants.SENIOR_AREA_CHAIRS_ASSIGNED in self.invitees:
            invitees.append(conference.get_senior_area_chairs_id(number))

        if conference.use_area_chairs and self.Participants.AREA_CHAIRS_ASSIGNED in self.invitees:
            invitees.append(conference.get_area_chairs_id(number))

        if conference.use_secondary_area_chairs and self.Participants.SECONDARY_AREA_CHAIRS in self.invitees:
            invitees.append(conference.get_secondary_area_chairs_id(number))

        if self.Participants.REVIEWERS_ASSIGNED in self.invitees:
            invitees.append(conference.get_reviewers_id(number))

        if self.Participants.REVIEWERS_SUBMITTED in self.invitees:
            invitees.append(conference.get_reviewers_id(number) + '/Submitted')

        if self.Participants.AUTHORS in self.invitees:
            invitees.append(conference.get_authors_id(number))

        if conference.use_ethics_chairs and self.Participants.ETHICS_CHAIRS in self.invitees:
            invitees.append(conference.get_ethics_chairs_id())

        if conference.use_ethics_reviewers and self.Participants.ETHICS_REVIEWERS_ASSIGNED in self.invitees:
            invitees.append(conference.get_ethics_reviewers_id(number))

        return invitees
    
    def get_noninvitees(self, conference, number):
        noninvitees = []

        if conference.use_area_chairs and self.Participants.AREA_CHAIRS_ASSIGNED in self.invitees and conference.use_secondary_area_chairs and self.Participants.SECONDARY_AREA_CHAIRS not in self.invitees:
            noninvitees.append(conference.get_secondary_area_chairs_id(number))

        return noninvitees

    def get_readers(self, conference, number):
        readers = [conference.get_program_chairs_id()]

        if self.Participants.EVERYONE in self.readers:
            return ['everyone']

        if conference.use_senior_area_chairs and self.Participants.SENIOR_AREA_CHAIRS_ASSIGNED in self.readers:
            readers.append(conference.get_senior_area_chairs_id(number))

        if conference.use_area_chairs and self.Participants.AREA_CHAIRS_ASSIGNED in self.readers:
            readers.append(conference.get_area_chairs_id(number))

        if self.Participants.REVIEWERS_ASSIGNED in self.readers:
            readers.append(conference.get_reviewers_id(number))

        if self.Participants.REVIEWERS_SUBMITTED in self.readers:
            readers.append(conference.get_reviewers_id(number) + '/Submitted')

        if self.Participants.AUTHORS in self.readers:
            readers.append(conference.get_authors_id(number))

        if conference.use_ethics_chairs and self.Participants.ETHICS_CHAIRS in self.readers:
            readers.append(conference.get_ethics_chairs_id())

        if conference.use_ethics_reviewers and self.Participants.ETHICS_REVIEWERS_ASSIGNED in self.readers:
            readers.append(conference.get_ethics_reviewers_id(number))

        if self.allow_de_anonymization or self.Participants.SIGNATURES in self.readers:
            readers.append('${3/signatures}')

        return readers
    
    def get_nonreaders(self, conference, number):
        nonreaders = []

        if conference.use_area_chairs and self.Participants.AREA_CHAIRS_ASSIGNED in self.readers and conference.use_secondary_area_chairs and self.Participants.SECONDARY_AREA_CHAIRS not in self.readers:
            nonreaders.append(conference.get_secondary_area_chairs_id(number))

        return nonreaders

    def get_signatures(self, conference, number):
        if self.allow_de_anonymization:
            return ['~.*', conference.get_program_chairs_id()]

        committee = []

        if conference.use_senior_area_chairs and self.Participants.SENIOR_AREA_CHAIRS_ASSIGNED in self.invitees:
                committee.append(conference.get_senior_area_chairs_id(number))

        if conference.use_area_chairs and self.Participants.AREA_CHAIRS_ASSIGNED in self.invitees:
                committee.append(conference.get_anon_area_chair_id(number=number, anon_id='.*'))

        if self.Participants.REVIEWERS_ASSIGNED in self.invitees or self.Participants.REVIEWERS_SUBMITTED in self.invitees:
            committee.append(conference.get_anon_reviewer_id(number=number, anon_id='.*'))

        if self.Participants.AUTHORS in self.invitees:
            committee.append(conference.get_authors_id(number))

        if conference.use_ethics_chairs and self.Participants.ETHICS_CHAIRS in self.invitees:
            committee.append(conference.get_ethics_chairs_id())

        if conference.use_ethics_reviewers and self.Participants.ETHICS_REVIEWERS_ASSIGNED in self.invitees:
            committee.append(conference.get_anon_reviewer_id(number=number, anon_id='.*', name=conference.ethics_reviewers_name))

        if self.Participants.PROGRAM_CHAIRS in self.invitees:
            committee.append(conference.get_program_chairs_id())

        if not committee:
            return [conference.get_program_chairs_id()]

        return committee

    def get_source_submissions(self):

        if self.source == self.Source.ACCEPTED_SUBMISSIONS:
            source = 'accepted_submissions'
        elif self.source == self.Source.PUBLIC_SUBMISSIONS:
            source = 'public_submissions'
        elif self.source == self.Source.ALL_SUBMISSIONS:
            source = 'all_submissions'
        elif self.source == self.Source.FLAGGED_SUBMISSIONS:
            source = 'flagged_for_ethics_review'
        
        return source

    def get_reply_to(self):

        if self.reply_to == self.ReplyTo.FORUM:
            reply_to = 'forum'
        elif self.reply_to == self.ReplyTo.WITHFORUM:
            reply_to = 'withForum'
        elif self.reply_to == self.ReplyTo.REVIEWS:
            reply_to = 'reviews'
        elif self.reply_to == self.ReplyTo.METAREVIEWS:
            reply_to = 'metareviews'

        return reply_to

    def get_reply_type(self):

        if self.reply_type == self.ReplyType.REPLY:
            reply_type = 'reply'
        elif self.reply_type == self.ReplyType.REVISION:
            reply_type = 'revision'

        return reply_type

    def get_content(self, api_version='2', conference=None):
        
        content = self.content.copy()

        if conference:
            invitation_id = conference.get_invitation_id(self.name)
            invitation = openreview.tools.get_invitation(conference.client, invitation_id)
            if invitation:
                for field, value in invitation.edit.get('invitation', {}).get('edit', {}).get('note', {}).get('content', {}).items() if invitation.edit else {}:
                    if field not in content:
                        content[field] = { 'delete': True }

        
        return content