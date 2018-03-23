#!/usr/bin/python
# -*- coding: utf-8 -*-
import openreview
import tools
import numpy as np
from collections import defaultdict

def get_conflicts(author_profiles, user_profile):
    author_domains = set()
    author_emails = set()
    author_relations = set()

    for author_email, profile in author_profiles.iteritems():

        author_info = get_author_info(profile, author_email)

        author_domains.update(author_info['domains'])
        author_emails.update(author_info['emails'])
        author_relations.update(author_info['relations'])

    user_info = get_profile_info(user_profile)

    conflicts = set()
    conflicts.update(author_domains.intersection(user_info['domains']))
    conflicts.update(author_relations.intersection(user_info['emails']))
    conflicts.update(author_emails.intersection(user_info['relations']))

    return list(conflicts)

def get_author_info(profile, email):
    if profile:
        return get_profile_info(profile)
    else:
        return {
            'domains': get_domains(email, subdomains = True),
            'emails': [email],
            'relations': []
        }


def get_profile_info(profile):

    domains = set()
    emails = set()
    relations = set()

    ## Emails section
    for e in profile.content['emails']:
        domains.update(get_domains(e, subdomains = True))
        emails.add(e)

    ## Institution section
    for h in profile.content.get('history', []):
        domain = h.get('institution', {}).get('domain', '')
        domains.update(get_domains(domain, subdomains = True))


    ## Relations section
    relations.update([r['email'] for r in profile.content.get('relations', [])])

    ## Filter common domains
    if 'gmail.com' in domains:
        domains.remove('gmail.com')

    return {
        'domains': domains,
        'emails': emails,
        'relations': relations
    }

def get_domains(entity, subdomains = False):

    if '@' in entity:
        full_domain = entity.split('@')[1]
    else:
        full_domain = entity

    if subdomains:
        domain_components = full_domain.split('.')
        domains = ['.'.join(domain_components[index:len(domain_components)]) for index, path in enumerate(domain_components)]
        valid_domains = [d for d in domains if '.' in d]
        return valid_domains
    else:
        return full_domain

def match(client, configuration_note, Solver):
    '''
    Given a configuration note, and a "Solver" class definition,
    returns a list of assignment openreview.Note objects.

    '''

    # unpack variables
    label = configuration_note.content['label']
    solver_config = configuration_note.content['configuration']
    weights = solver_config['weights']

    paper_invitation_id = configuration_note.content['paper_invitation']
    metadata_invitation_id = configuration_note.content['metadata_invitation']
    match_group_id = configuration_note.content['match_group']
    constraints = configuration_note.content['constraints']
    assignment_invitation_id = configuration_note.content['assignment_invitation']

    # make network calls
    papers = tools.get_all_notes(client, paper_invitation_id)
    papers_by_forum = {n.forum: n for n in papers}
    metadata_notes = [n for n in tools.get_all_notes(client, metadata_invitation_id) if n.forum in papers_by_forum]
    match_group = client.get_group(id = match_group_id)
    assignment_invitation = client.get_invitation(assignment_invitation_id)
    existing_assignment_notes = tools.get_all_notes(client, assignment_invitation_id)

    # organize data into indices
    existing_assignments = {n.forum: n.to_json() for n in existing_assignment_notes if n.content['label'] == label}
    scores_by_user_by_forum = get_weighted_scores(metadata_notes, weights, constraints, match_group)

    # TODO: allow individual constraints
    alphas = [(solver_config['minpapers'], solver_config['maxpapers'])] * len(match_group.members)
    betas = [(solver_config['minusers'], solver_config['maxusers'])] * len(metadata_notes) # why is this the length of the metadata notes?

    score_matrix, hard_constraint_dict, user_by_index, forum_by_index = encode_score_matrix(scores_by_user_by_forum)

    solution = Solver(alphas, betas, score_matrix, hard_constraint_dict).solve()

    assigned_userids = decode_score_matrix(solution, user_by_index, forum_by_index)

    new_assignment_notes = create_or_update_assignments(
        assigned_userids,
        existing_assignments,
        assignment_invitation,
        configuration_note,
        scores_by_user_by_forum
    )

    return new_assignment_notes

def get_weighted_scores(metadata_notes, weights, constraints, match_group):
    '''
    Returns a dict of dicts that contains weighted feature scores per user, per forum.

    e.g. {
        'abcXYZ': {
            '~Michael_Spector1': {
                'affinityScore': 0.85
            },
            '~Melisa_Bok1': {
                'affinityScore': 0.93
            }
        }
    }

    '''

    scores_by_user_by_forum = {}
    for m in metadata_notes:
        user_entries = [e for e in m.content['groups'][match_group.id] if e['userId'] in match_group.members]
        features_by_user = { entry['userId']: weight_scores(entry['scores'], weights) for entry in user_entries}

        # apply user-defined constraints
        if m.forum in constraints:
            constraint_by_user = { user: {'userConstraint': value} for user, value in constraints[forum].iteritems()}
            features_by_user.update(constraint_by_user)

        scores_by_user_by_forum[m.forum] = features_by_user

    return scores_by_user_by_forum

def weight_scores(scores, weights):
    '''
    multiplies feature values by weights, excepting hard constraints
    '''
    weighted_scores = {}
    for feature in weights:
        if feature in scores:
            weighted_scores[feature] = scores[feature]

            if scores[feature] != '-inf' and scores[feature] != '+inf':
                weighted_scores[feature] *= weights[feature]

    return weighted_scores

def create_assignment(forum, label, assignment_invitation):
    '''
    Creates the JSON record for an empty assignment Note.

    *important* return type is dict, not openreview.Note
    '''

    return {
        'forum': forum,
        'invitation': assignment_invitation.id,
        'readers': assignment_invitation.reply['readers']['values'],
        'writers': assignment_invitation.reply['writers']['values'],
        'signatures': assignment_invitation.reply['signatures']['values'],
        'content': {
            'label': label
        }
    }

def create_or_update_config(client, label, params):
    '''
    makes a network call to get any existing configuration notes that match the given label,
    and updates the note with the given params.

    Returns an openreview.Note object with the updated params.
    '''
    config_by_label = {n.content['label']: n.to_json() for n in client.get_notes(invitation=params['invitation'])}
    configuration_note_params = config_by_label.get(label, {})
    user_constraints = configuration_note_params.get('content', {}).get('constraints', {})
    configuration_note_params.update(params)
    configuration_note_params['content']['constraints'] = user_constraints

    return openreview.Note(**configuration_note_params)

def encode_score_matrix(scores_by_user_by_forum):
    '''
    Given a dict of dicts with scores for every user, for every forum,
    encodes the score matrix to be used by the solver.

    Also returns:
    (1) a hard constraint dict (needed by the solver),
    (2) indices needed by the decode_score_matrix() function

    '''

    forums = scores_by_user_by_forum.keys()
    num_users = None
    for forum in forums:
        num_users_in_forum = len(scores_by_user_by_forum[forum])
        if not num_users:
            num_users = num_users_in_forum
        else:
            assert num_users_in_forum == num_users, "Error: uneven number of user scores by forum"
    if num_users:
        users = scores_by_user_by_forum[forums[0]]

    index_by_user = {user: i for i, user in enumerate(users)}
    index_by_forum = {forum: i for i, forum in enumerate(forums)}

    user_by_index = {i: user for i, user in enumerate(users)}
    forum_by_index = {i: forum for i, forum in enumerate(forums)}

    score_matrix = np.zeros((len(index_by_user), len(index_by_forum)))
    hard_constraint_dict = {}

    for forum, weighted_scores_by_user in scores_by_user_by_forum.iteritems():
        paper_index = index_by_forum[forum]

        for user, user_scores in weighted_scores_by_user.iteritems():
            user_index = index_by_user.get(user, None)
            hard_constraint_value = get_hard_constraint_value(user_scores.values())

            if user_index:
                coordinates = (user_index, paper_index)
                if hard_constraint_value == -1:
                    mean = np.mean(user_scores.values())
                    if np.isnan(mean).any():
                        print forum, user, user_scores

                    score_matrix[coordinates] = mean
                else:
                    hard_constraint_dict[coordinates] = hard_constraint_value

    return score_matrix, hard_constraint_dict, user_by_index, forum_by_index

def decode_score_matrix(solution, user_by_index, forum_by_index):
    '''
    Decodes the 2D score matrix into a returned dict of user IDs keyed by forum ID.

    e.g. {
        'abcXYZ': '~Melisa_Bok1',
        '123-AZ': '~Michael_Spector1'
    }
    '''

    assignments_by_forum = defaultdict(list)
    for var_name in solution:
        var_val = var_name.split('x_')[1].split(',')

        user_index, paper_index = (int(var_val[0]), int(var_val[1]))
        user_id = user_by_index[user_index]
        forum = forum_by_index[paper_index]
        match = solution[var_name]

        if match == 1:
            assignments_by_forum[forum].append(user_id)

    return assignments_by_forum

def create_or_update_assignments(assignments, existing_assignments, assignment_invitation, configuration_note, scores_by_user_by_forum):
    '''
    Creates or updates (as applicable) the assignment notes with new assignments.

    Returns a list of openreview.Note objects.
    '''

    alternates = configuration_note.content['configuration']['alternates']
    label = configuration_note.content['label']
    new_assignment_notes = []
    for forum, userids in assignments.iteritems():
        scores_by_user = scores_by_user_by_forum[forum]
        assignment = existing_assignments.get(forum, create_assignment(forum, label, assignment_invitation))

        new_content = {
            'assignedGroups': get_assigned_groups(userids, scores_by_user),
            'alternateGroups': get_alternate_groups(userids, scores_by_user, alternates)
        }

        assignment['content'].update(new_content)

        new_assignment_notes.append(openreview.Note(**assignment))

    return new_assignment_notes

def get_assigned_groups(userids, scores_by_user):
    '''
    Returns a list of assignment group entries.

    Entries are dicts with the following fields:
        'finalScore'
        'scores'
        'userId'
    '''

    assignment_entries = []
    for user, scores in scores_by_user.iteritems():
        if user in userids:
            assignment_entries.append({
                'finalScore': np.mean([val for feature, val in scores.iteritems() if val != '+inf' and val != '-inf']),
                'scores': scores,
                'userId': user
            })

    return assignment_entries

def get_alternate_groups(assigned_userids, scores_by_user, alternates):
    '''
    Returns a list of alternate group entries.
    The list will have length == @alternates.

    Entries are dicts with the following fields:
        'finalScore'
        'scores'
        'userId'

    '''
    alternate_entries = []

    for user, scores in scores_by_user.iteritems():
        if user not in assigned_userids:
            alternate_entries.append({
                'finalScore': np.mean([val for feature, val in scores.iteritems() if val != '+inf' and val != '-inf']),
                'scores': scores,
                'userId': user
            })

    sorted_entries = sorted(alternate_entries, key=lambda x: x['finalScore'])
    top_n_entries = sorted_entries[:alternates]
    return top_n_entries

def get_hard_constraint_value(score_array):
    """
    A function to check for the presence of Hard Constraints in the score array (+Inf or -Inf) ,
    :param score_array:
    :return:
    """
    for element in score_array:
        if str(element).strip().lower() == '+inf':
            return 1
        if str(element).strip().lower() == '-inf':
            return 0
    return -1

