#!/usr/bin/python
# -*- coding: utf-8 -*-
import openreview
import re

super_user_id = 'OpenReview.net'

def get_profile(client, value):
    profile = None
    try:
        profile = client.get_profile(value)
    except openreview.OpenReviewException as e:
        # throw an error if it is something other than "not found"
        if e[0][0] != 'Profile not found':
            print "OpenReviewException: {0}".format(e)
            return e
    return profile

def create_profile(client, email, first, last, middle = None):

    profile = get_profile(client, email)

    if not profile:
        response = client.get_tildeusername(first, last, middle)
        tilde_id = response['username'].encode('utf-8')

        if tilde_id.endswith(last + '1'):

            tilde_group = openreview.Group(id = tilde_id, signatures = [super_user_id], signatories = [tilde_id], readers = [tilde_id], writers = [super_user_id], members = [email])
            email_group = openreview.Group(id = email, signatures = [super_user_id], signatories = [email], readers = [email], writers = [super_user_id], members = [tilde_id])
            profile_content = {
                'emails': [email],
                'preferred_email': email,
                'names': [
                    {
                        'first': first,
                        'middle': middle,
                        'last': last,
                        'username': tilde_id
                    }
                ]
            }
            client.post_group(tilde_group)
            client.post_group(email_group)
            profile = client.post_profile(tilde_id, profile_content)

            return profile

        else:
            raise openreview.OpenReviewException('There is already a profile with this first: {0}, middle: {1}, last name: {2}'.format(first, middle, last))
    else:
        raise openreview.OpenReviewException('There is already a profile with this email: {0}'.format(email))

def build_groups(conference_group_id, default_params=None):
    '''

    Given a group ID, returns a list of empty groups that correspond to the given group's subpaths
    (e.g. Test.com, Test.com/TestConference, Test.com/TestConference/2018)

    '''

    path_components = conference_group_id.split('/')
    paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]

    if not default_params:
        default_params = {
            'readers': ['everyone'],
            'writers': [],
            'signatures': [],
            'signatories': [],
            'members': []
        }

    groups = {p: openreview.Group(p, **default_params) for p in paths}
    groups[conference_group_id].writers = groups[conference_group_id].signatories = [conference_group_id]

    return sorted(groups.values(), key=lambda x: len(x.id))

def get_bibtex(note, venue_fullname, year, url_forum=None, accepted=False, anonymous=True):

    def capitalize_title(title):
        capitalization_regex = re.compile('[A-Z]{2,}')
        words = re.split('(\W)', title)
        for idx, word in enumerate(words):
            m = capitalization_regex.search(word)
            if m:
                new_word = '{' + word[m.start():m.end()] + '}'
                words[idx] = words[idx].replace(word[m.start():m.end()], new_word)
        return ''.join(words)


    first_word = re.sub('[^a-zA-Z]', '', note.content['title'].split(' ')[0].lower())

    forum = note.forum if not url_forum else url_forum

    if anonymous:
        first_author_last_name = 'anonymous'
        authors = 'Anonymous'
    else:
        first_author_last_name = note.content['authors'][0].split(' ')[1].lower()
        authors = ' and '.join(note.content['authors'])

    bibtex_title = capitalize_title(note.content['title'])

    rejected_bibtex = [
        '@misc{',
        first_author_last_name + year + first_word + ',',
        'title={' + bibtex_title + '},',
        'author={' + authors + '},',
        'year={' + year + '},',
        'url={https://openreview.net/forum?id=' + forum + '},',
        '}'
    ]

    accepted_bibtex = [
        '@inproceedings{',
        first_author_last_name + '2018' + first_word + ',',
        'title={' + bibtex_title + '},',
        'author={' + authors + '},',
        'booktitle={' + venue_fullname + '},',
        'year={' + year + '},',
        'url={https://openreview.net/forum?id=' + forum + '},',
        '}'
    ]

    if accepted:
        bibtex = accepted_bibtex
    else:
        bibtex = rejected_bibtex

    return '\n'.join(bibtex)

def subdomains(email):
    '''
    Given an email address, get the domains and subdomains.

    e.g. johnsmith@iesl.cs.umass.edu --> [umass.edu, cs.umass.edu, iesl.cs.umass.edu]
    '''

    full_domain = email.split('@')[1]
    domain_components = full_domain.split('.')
    domains = ['.'.join(domain_components[index:len(domain_components)]) for index, path in enumerate(domain_components)]
    valid_domains = [d for d in domains if '.' in d]
    return valid_domains

def profile_conflicts(profile):
    domain_conflicts = set()
    relation_conflicts = set()

    profile_domains = []
    for e in profile.content['emails']:
        profile_domains += subdomains(e)

    domain_conflicts.update(profile_domains)

    institution_domains = [h['institution']['domain'] for h in profile.content['history']]
    domain_conflicts.update(institution_domains)

    if 'relations' in profile.content:
        relation_conflicts.update([r['email'] for r in profile.content['relations']])

    if 'gmail.com' in domain_conflicts:
        domain_conflicts.remove('gmail.com')

    return (domain_conflicts, relation_conflicts)

def get_profile_conflicts(client, reviewer_to_add):
    try:
        profile = client.get_profile(reviewer_to_add)
        user_domain_conflicts, user_relation_conflicts = profile_conflicts(profile)
        user_relation_conflicts.update([reviewer_to_add])
    except openreview.OpenReviewException as e:
        user_domain_conflicts, user_relation_conflicts = (set(), set())

    return user_domain_conflicts, user_relation_conflicts

def get_paper_conflicts(client, paper):
    authorids = paper.content['authorids']
    domain_conflicts = set()
    relation_conflicts = set()
    for e in authorids:
        author_domain_conflicts, author_relation_conflicts = get_profile_conflicts(client, e)

        domain_conflicts.update(author_domain_conflicts)
        relation_conflicts.update(author_relation_conflicts)

        if '@' in e:
            domain_conflicts.update(subdomains(e))

    relation_conflicts = set([e for e in authorids if '@' in e])

    # remove the domain "gmail.com"
    if 'gmail.com' in domain_conflicts:
        domain_conflicts.remove('gmail.com')

    return (domain_conflicts, relation_conflicts)

def get_paperhash(first_author, title):
    title = title.strip()
    strip_punctuation = '[^A-zÀ-ÿ\d\s]'.decode('utf-8')
    title = re.sub(strip_punctuation, '', title)
    first_author = re.sub(strip_punctuation, '', first_author)
    first_author = first_author.split(' ').pop()
    title = re.sub(strip_punctuation, '', title)
    title = re.sub('\r|\n', '', title)
    title = re.sub('\s+', '_', title)
    first_author = re.sub(strip_punctuation, '', first_author)
    return (first_author + '|' + title).lower()

def replace_members_with_ids(client, group):
    ids = []
    emails = []
    for member in group.members:
        if '~' not in member:
            try:
                profile = client.get_profile(member.lower())
                ids.append(profile.id)
            except openreview.OpenReviewException as e:
                if ['Profile not found'] in e:
                    emails.append(member)
                else:
                    raise e
        else:
            ids.append(member)

    group.members = ids + emails
    client.post_group(group)

def get_all_notes(client, invitation, limit=1000):
    done = False
    notes = []
    offset = 0
    while not done:
        batch = client.get_notes(invitation=invitation, limit=limit, offset=offset)
        notes += batch
        offset += limit
        if len(batch) < limit:
            done = True
    return notes

def next_individual_suffix(empty_individual_groups, individual_groups, individual_label):
    if len(empty_individual_groups) > 0:
        anonreviewer_group = empty_individual_groups[0]
        empty_individual_groups.remove(anonreviewer_group)
        anonreviewer_suffix = anonreviewer_group.id.split('/')[-1]
        return anonreviewer_suffix
    elif len(individual_groups) > 0:
        anonreviewer_group_ids = [g.id for g in individual_groups]

        # reverse=True lets us get the AnonReviewer group with the highest index
        highest_anonreviewer_id = sorted(anonreviewer_group_ids, reverse=True)[0]

        # find the number of the highest anonreviewer group
        highest_anonreviewer_index = highest_anonreviewer_id[-1]
        return '{}{}'.format(individual_label, int(highest_anonreviewer_index)+1)
    else:
        return '{}1'.format(individual_label)

def assign(client, paper_number, conference,
    reviewer_group_params = {},
    anonreviewer_group_params = {},
    reviewer_to_add = None,
    reviewer_to_remove = None,
    check_conflicts_invitation = None,
    parent_label = 'Reviewers',
    individual_label = None):

    group_params_default = {
        'readers': [conference, '{}/Program_Chairs'.format(conference)],
        'writers': [conference],
        'signatures': [conference],
        'signatories': []
    }
    reviewer_group_params_default = {k:v for k,v in group_params_default.iteritems()}
    reviewer_group_params_default.update(reviewer_group_params)
    reviewer_group_params = reviewer_group_params_default

    anonreviewer_group_params_default = {k:v for k,v in group_params_default.iteritems()}
    anonreviewer_group_params_default.update(anonreviewer_group_params)
    anonreviewer_group_params = anonreviewer_group_params_default

    # ensure that two groups are created or already exist:
    # one "parent" group, containing all "reviewers" for the paper,
    # and one "individual" group, containing just a single user

    try:
        parent_group = client.get_group('{}/Paper{}/{}'.format(conference, paper_number, parent_label))
    except openreview.OpenReviewException as e:
        if e[0][0]['type'] == 'Not Found':
            parent_group = client.post_group(openreview.Group(
                id = '{}/Paper{}/{}'.format(conference, paper_number, parent_label),
                nonreaders = ['{}/Paper{}/Authors'.format(conference, paper_number)],
                **reviewer_group_params
            ))
        else:
            raise e

    individual_groups = client.get_groups(id = '{}/Paper{}/{}.*'.format(conference, paper_number, individual_label))
    individual_groups = [g for g in individual_groups if g.id != parent_group.id]

    empty_individual_groups = sorted([ a for a in individual_groups if a.members == [] ], key=lambda x: x.id)

    if reviewer_to_remove:
        client.remove_members_from_group(parent_group, reviewer_to_remove)
        assigned_individual_groups = [a for a in individual_groups if reviewer_to_remove in a.members]
        for individual_group in assigned_individual_groups:
            print "removing {0} from {1}".format(reviewer_to_remove, individual_group.id)
            client.remove_members_from_group(individual_group, reviewer_to_remove)
            empty_individual_groups.append(individual_group)
            empty_individual_groups = sorted(empty_individual_groups, key=lambda x: x.id)

    if reviewer_to_add:
        user_continue = True
        assigned_individual_groups = [a for a in individual_groups if reviewer_to_add in a.members]

        if check_conflicts_invitation:
            paper = client.get_notes(invitation=check_conflicts_invitation, number=paper_number)[0]

            user_domain_conflicts, user_relation_conflicts = get_profile_conflicts(client, reviewer_to_add)
            paper_domain_conflicts, paper_relation_conflicts = get_paper_conflicts(client, paper)

            domain_conflicts = paper_domain_conflicts.intersection(user_domain_conflicts)
            relation_conflicts = paper_relation_conflicts.intersection(user_relation_conflicts)

            if domain_conflicts:
                print "{:40s} XXX User has COI with the following domain: {}".format(reviewer_to_add, domain_conflicts)
            if relation_conflicts:
                print "{:40s} XXX User has COI with the following relation: {}".format(reviewer_to_add, relation_conflicts)

            if domain_conflicts or relation_conflicts:
                user_continue = raw_input('continue with assignment? y/[n]: ').lower() == 'y'

        if not user_continue:
            print "aborting assignment."
            return False

        if user_continue:
            if reviewer_to_add not in parent_group.members:
                client.add_members_to_group(parent_group, reviewer_to_add)
                print "{:40s} --> {}".format(reviewer_to_add, parent_group.id)
            else:
                print "{:40s} === {}".format(reviewer_to_add, parent_group.id)

            if not assigned_individual_groups:
                suffix = next_individual_suffix(empty_individual_groups, individual_groups, individual_label)
                anonreviewer_id = '{}/Paper{}/{}'.format(conference, paper_number, suffix)
                paper_authors = '{}/Paper{}/Authors'.format(conference, paper_number)
                individual_group = openreview.Group(
                    id = anonreviewer_id,
                    **anonreviewer_group_params)

                individual_group.readers.append(anonreviewer_id)
                individual_group.nonreaders.append(paper_authors)
                individual_group.signatories.append(anonreviewer_id)
                individual_group.members.append(reviewer_to_add)

                print "{:40s} --> {}".format(reviewer_to_add, individual_group.id)

                client.post_group(individual_group)
            else:
                for g in assigned_individual_groups:
                    print "{:40s} === {}".format(reviewer_to_add, g.id)

            return True

