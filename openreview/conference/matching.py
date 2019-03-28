from __future__ import division
import openreview
import csv
from collections import defaultdict

class Matching(object):

    def __init__(self, conference):
        self.conference = conference

    def clear(self, client, invitation):
        note_list = list(openreview.tools.iterget_notes(client, invitation = invitation))
        for note in note_list:
            client.delete_note(note)

    def _jaccard_similarity(self, list1, list2):
        set1 = set(list1)
        set2 = set(list2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)

    def _append_manual_conflicts(self, profile, manual_user_conflicts):
        for conflict_domain in manual_user_conflicts:
            manual_entry = {
                'end': None,
                'start': None,
                'position': 'Manual Entry',
                'institution': {
                    'name': 'Manual Entry',
                    'domain': conflict_domain
                }
            }
            profile.content['history'].append(manual_entry)
        return profile


    def _build_entries(self, author_profiles, reviewer_profiles, paper_bid_jsons, paper_recommendation_jsons, scores_by_reviewer, manual_conflicts_by_id):
        entries = []
        bid_count = 0
        for profile in reviewer_profiles:
            bid_score_map = {
                'Very High': 1.0,
                'High': 0.5,
                'Neutral': 0.0,
                'Low': -0.5,
                'Very Low': -1.0
            }
            try:
                reviewer_bids = sorted([t for t in paper_bid_jsons if profile.id in t['signatures']], key=lambda t: t.get('tmdate',0), reverse=True)
            except TypeError as e:
                raise e
            reviewer_scores = scores_by_reviewer.get(profile.id, {})

            # find conflicts between the reviewer's profile and the paper's authors' profiles
            user_entry = {
                'userid': profile.id,
                'scores': reviewer_scores
            }

            # Bid can contain a 'Conflict of Interest' selection, so install in the entry if bid is set to that
            if reviewer_bids:
                tag = reviewer_bids[0]['tag']
                if tag == 'Conflict of Interest':
                    print('Conflict of Interest for', profile.id)
                    user_entry['conflicts'] = ['self-declared COI']
                else:
                    bid_score = bid_score_map.get(tag, 0.0)
                    bid_count += 1
                    if bid_score != 0.0:
                        user_entry['scores']['bid'] = bid_score

            reviewer_recommendations = [ t['tag'] for t in sorted(paper_recommendation_jsons, key=lambda x: x['cdate'])]
            if reviewer_recommendations:
                ## Set value between High(0.5) and Very High(1)
                count = len(reviewer_recommendations)
                if profile.id in reviewer_recommendations:
                    index = reviewer_recommendations.index(profile.id)
                    score = 0.5 + (0.5 * ((count - index) / count))
                    user_entry['scores']['recommendation'] = score

            manual_user_conflicts = manual_conflicts_by_id.get(profile.id, [])
            if manual_user_conflicts:
                profile = self._append_manual_conflicts(profile, manual_user_conflicts)
            conflicts = openreview.tools.get_conflicts(author_profiles, profile)

            if conflicts:
                user_entry['conflicts'] = conflicts + user_entry.get('conflicts', [])

            entries.append(user_entry)

        ## Assert amount of bids and tags
        difference = list(set([tag['signatures'][0] for tag in paper_bid_jsons]) - set([profile.id for profile in reviewer_profiles]))
        assert len(difference) == 0, 'There is a difference in forum: ' + paper_bid_jsons[0]['forum'] + ' for tags with no profile found: ' + ','.join(difference)
        assert bid_count == len(paper_bid_jsons), 'Incorrect number(score_count: '+ str(bid_count) + ' tag_count:' + str(len(paper_bid_jsons)) +') of bid scores in the metadata for paper: ' + paper_bid_jsons[0]['forum']
        return entries

    def _get_profiles(self, client, ids_or_emails):
        ids = []
        emails = []
        for member in ids_or_emails:
            if '~' in member:
                ids.append(member)
            else:
                emails.append(member)

        profiles = client.search_profiles(ids = ids)

        profile_by_email = client.search_profiles(emails = emails)
        for email in emails:
            profiles.append(profile_by_email.get(email, openreview.Profile(id = email,
            content = {
                'emails': [email],
                'preferredEmail': email
            })))

        return profiles

    def post_metadata_note(self,
        client,
        note,
        reviewer_profiles,
        metadata_inv,
        paper_scores,
        manual_conflicts_by_id,
        bid_invitation,
        recommendation_invitation):

        authorids = note.content['authorids']
        if note.details.get('original'):
            authorids = note.details['original']['content']['authorids']
        paper_bid_jsons = list(filter(lambda t: t['invitation'] == bid_invitation, note.details['tags']))
        paper_recommendation_jsons = list(filter(lambda t: t['invitation'] == recommendation_invitation, note.details['tags']))
        paper_author_profiles = self._get_profiles(client, authorids)
        entries = self._build_entries(paper_author_profiles, reviewer_profiles, paper_bid_jsons, paper_recommendation_jsons, paper_scores, manual_conflicts_by_id)

        new_metadata_note = openreview.Note(**{
            'forum': note.id,
            'invitation': metadata_inv.id,
            'readers': metadata_inv.reply['readers']['values'],
            'writers': metadata_inv.reply['writers']['values'],
            'signatures': metadata_inv.reply['signatures']['values'],
            'content': {
                'title': 'Paper Metadata',
                'entries': entries
            }
        })

        return client.post_note(new_metadata_note)

    def get_assignments(self, config_note, submissions, assignment_notes):
        assignments = []

        paper_by_forum = { n.forum: n for n in submissions }

        added_constraints = config_note.content.get('constraints', {})

        for assignment in assignment_notes:
            assigned_groups = assignment.content['assignedGroups']
            paper_constraints = added_constraints.get(assignment.forum, {})
            paper_assigned = []
            for assignment_entry in assigned_groups:
                score = assignment_entry.get('finalScore', 0)
                user_id = assignment_entry['userId']
                paper_assigned.append(user_id)

                paper = paper_by_forum.get(assignment.forum)

                if paper and paper_constraints.get(user_id) != '-inf':
                    current_row = [paper.number, paper.forum, user_id, score]
                    assignments.append(current_row)

            for user, constraint in paper_constraints.items():
                print('user, constraint', user, constraint)
                if user not in paper_assigned and constraint == '+inf':
                    current_row = [paper.number, paper.forum, user, constraint]
                    assignments.append(current_row)


        return sorted(assignments, key=lambda x: x[0])

    def setup(self, affinity_score_file = None, tpms_score_file = None):

        conference = self.conference
        client = conference.client
        CONFERENCE_ID = conference.get_id()
        PROGRAM_CHAIRS_ID = conference.get_program_chairs_id()
        SUBMISSION_ID = conference.get_blind_submission_id()
        METADATA_INV_ID = CONFERENCE_ID + '/-/Paper_Metadata'
        REVIEWERS_ID = conference.get_reviewers_id()
        AREA_CHAIRS_ID = conference.get_area_chairs_id()
        ASSIGNMENT_INV_ID = self.conference.get_paper_assignment_id()
        scores = ['bid']
        if affinity_score_file:
            scores.append('affinity')
        if tpms_score_file:
            scores.append('tpms')
        if conference.subject_areas:
            scores.append('subjectArea')
        try:
            client.get_invitation(conference.get_recommendation_id())
            scores.append('recommendation')
        except openreview.OpenReviewException:
            print('Recommendation invitation not found')

        metadata_inv = openreview.Invitation.from_json({
            'id': METADATA_INV_ID,
            'readers': [
                CONFERENCE_ID,
                PROGRAM_CHAIRS_ID
            ],
            'writers': [CONFERENCE_ID],
            'signatures': [CONFERENCE_ID],
            'reply': {
                'forum': None,
                'replyto': None,
                'invitation': SUBMISSION_ID,
                'readers': {
                    'values': [
                        CONFERENCE_ID,
                    ]
                },
                'writers': {
                    'values': [CONFERENCE_ID]
                },
                'signatures': {
                    'values': [CONFERENCE_ID]},
                'content': {}
            }
        })


        assignment_inv = openreview.Invitation.from_json({
            'id': ASSIGNMENT_INV_ID,
            'readers': [CONFERENCE_ID],
            'writers': [CONFERENCE_ID],
            'signatures': [CONFERENCE_ID],
            'reply': {
                'forum': None,
                'replyto': None,
                'invitation': SUBMISSION_ID,
                'readers': {'values': [CONFERENCE_ID, PROGRAM_CHAIRS_ID]},
                'writers': {'values': [CONFERENCE_ID]},
                'signatures': {'values': [CONFERENCE_ID]},
                'content': {}
            }
        })


        CONFIG_INV_ID = CONFERENCE_ID + '/-/Assignment_Configuration'

        config_inv = openreview.Invitation.from_json({
            'id': CONFIG_INV_ID,
            'readers': [CONFERENCE_ID, PROGRAM_CHAIRS_ID],
            'writers': [CONFERENCE_ID],
            'signatures': [PROGRAM_CHAIRS_ID],
            'reply': {
                'forum': None,
                'replyto': None,
                'invitation': None,
                'readers': {'values': [CONFERENCE_ID, PROGRAM_CHAIRS_ID]},
                'writers': {'values': [CONFERENCE_ID, PROGRAM_CHAIRS_ID]},
                'signatures': {'values': [PROGRAM_CHAIRS_ID]},
                'content': {
                    'title': {
                        'value-regex': '.{1,250}',
                        'required': True,
                        'description': 'Title of the configuration.',
                        'order': 1
                    },
                    'max_users': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Max number of reviewers that can review a paper',
                        'order': 2
                    },
                    'min_users': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Min number of reviewers required to review a paper',
                        'order': 3
                    },
                    'max_papers': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Max number of reviews a person has to do',
                        'order': 4
                    },
                    'min_papers': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Min number of reviews a person should do',
                        'order': 5
                    },
                    'alternates': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Number of alternate reviewers for a paper',
                        'order': 6
                    },
                    'config_invitation': {
                        'value': CONFERENCE_ID,
                        'required': True,
                        'description': 'Invitation to get the configuration note',
                        'order': 7
                    },
                    'paper_invitation': {
                        'value': SUBMISSION_ID,
                        'required': True,
                        'description': 'Invitation to get the configuration note',
                        'order': 8
                    },
                    'metadata_invitation': {
                        'value': METADATA_INV_ID,
                        'required': True,
                        'description': 'Invitation to get the configuration note',
                        'order': 9
                    },
                    'assignment_invitation': {
                        'value': ASSIGNMENT_INV_ID,
                        'required': True,
                        'description': 'Invitation to get the configuration note',
                        'order': 10
                    },
                    'match_group': {
                        'value-radio': [AREA_CHAIRS_ID, REVIEWERS_ID],
                        'required': True,
                        'description': 'Invitation to get the configuration note',
                        'order': 11
                    },
                    'scores_names': {
                        'values-dropdown': scores,
                        'required': True,
                        'description': 'List of scores names',
                        'order': 12
                    },
                    'scores_weights': {
                        'values-regex': '\\d*\\.?\\d*', # decimal number allowed
                        'required': True,
                        'description': 'Comma separated values of scores weights, should follow the same order than scores_names',
                        'order': 13
                    },
                    'constraints': {
                        'value-dict': {}, # Add some json validation schema
                        'required': False,
                        'description': 'Manually entered user/papers constraints',
                        'order': 14
                    },
                    'custom_loads': {
                        'value-dict': {},
                        'required': False,
                        'description': 'Manually entered custom user maximun loads',
                        'order': 15
                    },
                    'status': {
                        'value-dropdown': ['Initialized', 'Running', 'Error', 'No Solution', 'Complete', 'Deployed']
                    }
                }
            }

        })


        print('clearing previous metadata, assignments, and configs...')
        self.clear(client, METADATA_INV_ID)
        self.clear(client, ASSIGNMENT_INV_ID)
        self.clear(client, CONFIG_INV_ID)

        reviewers_group = client.get_group(REVIEWERS_ID)
        # The reviewers are all emails so convert to tilde ids
        reviewers_group = openreview.tools.replace_members_with_ids(client,reviewers_group)
        if not all(['~' in member for member in reviewers_group.members]):
            print('WARNING: not all reviewers have been converted to profile IDs. Members without profiles will not have metadata created.')


        if conference.use_area_chairs:
            areachairs_group = client.get_group(AREA_CHAIRS_ID)
            # The areachairs are all emails so convert to tilde ids
            areachairs_group = openreview.tools.replace_members_with_ids(client,areachairs_group)
            if not all(['~' in member for member in areachairs_group.members]):
                print('WARNING: not all area chairs have been converted to profile IDs. Members without profiles will not have metadata created.')

            user_profiles = self._get_profiles(client, reviewers_group.members + areachairs_group.members)
        else:
            user_profiles = self._get_profiles(client, reviewers_group.members)

        # create metadata
        metadata_inv = client.post_invitation(metadata_inv)
        config_inv = client.post_invitation(config_inv)
        assignment_inv = client.post_invitation(assignment_inv)

        # Get the submissions.
        submissions = list(openreview.tools.iterget_notes(
            client, invitation = conference.get_blind_submission_id(), details='original,tags'))

        submissions_per_number = { note.number: note for note in submissions }
        profiles_by_email = {}
        for profile in user_profiles:
            for email in profile.content['emails']:
                profiles_by_email[email] = profile

        scores_by_reviewer_by_paper = {note.forum: defaultdict(dict) for note in submissions}

        if affinity_score_file:
            with open(affinity_score_file) as f:
                for row in csv.reader(f):
                    paper_note_id = row[0]
                    profile_id = row[1]
                    score = row[2]
                    if paper_note_id in scores_by_reviewer_by_paper:
                        scores_by_reviewer_by_paper[paper_note_id][profile_id].update({'affinity': float(score)})

        if tpms_score_file:
            with open(tpms_score_file) as f:
                for row in csv.reader(f):
                    paper_note_id = submissions_per_number[int(row[0])].id
                    profile_id = profiles_by_email.get(row[1], { id: row[1] }).id
                    score = row[2]
                    if paper_note_id in scores_by_reviewer_by_paper:
                        scores_by_reviewer_by_paper[paper_note_id][profile_id].update({'tpms': float(score)})

        if conference.subject_areas:
            user_subject_areas = list(openreview.tools.iterget_notes(client, invitation = conference.get_registration_id()))
            for note in submissions:
                note_subject_areas = note.content['subject_areas']
                paper_note_id = note.id
                for subject_area_note in user_subject_areas:
                    profile_id = subject_area_note.signatures[0]
                    subject_areas = subject_area_note.content['subject_areas']
                    score = self._jaccard_similarity(note_subject_areas, subject_areas)
                    if paper_note_id in scores_by_reviewer_by_paper:
                        scores_by_reviewer_by_paper[paper_note_id][profile_id].update({'subjectArea': float(score)})

        metadata_notes = []
        for note in submissions:
            scores_by_reviewer = scores_by_reviewer_by_paper[note.id]
            metadata_notes.append(self.post_metadata_note(client,
                note,
                user_profiles,
                metadata_inv,
                scores_by_reviewer,
                {},
                conference.get_bid_id(),
                conference.get_recommendation_id(note.number))
            )

        return metadata_notes


    def get_assignment_notes (self):
        return self.conference.client.get_notes(invitation = self.conference.get_paper_assignment_id())

    def deploy(self, assingment_title):

        # Get the configuration note to check the group to assign
        client = self.conference.client
        notes = client.get_notes(invitation = self.conference.get_id() + '/-/Assignment_Configuration', content = { 'title': assingment_title })

        if notes:
            configuration_note = notes[0]
            match_group = configuration_note.content['match_group']
            is_area_chair = self.conference.get_area_chairs_id() == match_group
            submissions = openreview.tools.iterget_notes(client, invitation = self.conference.get_blind_submission_id())
            assignment_notes = openreview.tools.iterget_notes(client, invitation = self.conference.get_id() + '/-/Paper_Assignment', content = { 'title': assingment_title })


            assignments = self.get_assignments(configuration_note, submissions, assignment_notes)

            for a in assignments:
                paper_number = a[0]
                user = a[2]

                if is_area_chair:
                    parent_label = 'Area_Chairs'
                    individual_label = 'Area_Chair'
                    individual_group_params = {}
                    parent_group_params = {}
                else:
                    parent_label = 'Reviewers'
                    individual_label = 'AnonReviewer'
                    individual_group_params = {
                        'readers': [
                            self.conference.get_id(),
                            self.conference.get_program_chairs_id(),
                            self.conference.get_id() + 'Paper{0}/Area_Chairs'.format(paper_number)
                        ],
                    }
                    parent_group_params = {
                       'readers': [
                            self.conference.get_id(),
                            self.conference.get_program_chairs_id(),
                            self.conference.get_id() + 'Paper{0}/Area_Chairs'.format(paper_number)
                        ]
                    }

                new_assigned_group = openreview.tools.add_assignment(
                    client, paper_number, self.conference.get_id(), user,
                    parent_label = parent_label,
                    individual_label = individual_label,
                    individual_group_params = individual_group_params,
                    parent_group_params = parent_group_params)
                print(new_assigned_group)


        else:
            raise openreview.OpenReviewException('Configuration not found for ' + assingment_title)





