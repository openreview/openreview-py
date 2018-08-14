#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import openreview
import re
import datetime
import time
from Crypto.Hash import HMAC, SHA256

super_user_id = 'OpenReview.net'

def get_profile(client, value):
    profile = None
    try:
        profile = client.get_profile(value)
    except openreview.OpenReviewException as e:
        # throw an error if it is something other than "not found"
        if e[0][0] != 'Profile not found':
            print("OpenReviewException: {0}".format(e))
            return e
    return profile

def create_profile(client, email, first, last, middle = None, allow_duplicates = False):

    '''
    Given email, first name, last name, and middle name (optional), creates and returns
    a user profile.

    If a profile with the same name exists, and allow_duplicates is False, an exception is raised.

    If a profile with the same name exists and allow_duplicates is True, a profile is created with
    the next largest number (e.g. if ~Michael_Spector1 exists, ~Michael_Spector2 will be created)
    '''

    profile = get_profile(client, email)

    if not profile:
        response = client.get_tildeusername(first, last, middle)
        tilde_id = response['username'].encode('utf-8')

        if tilde_id.endswith(last + '1') or allow_duplicates:

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
            profile = client.post_profile(openreview.Profile(id=tilde_id, content=profile_content))

            return profile

        else:
            raise openreview.OpenReviewException('There is already a profile with this first: {0}, middle: {1}, last name: {2}'.format(first, middle, last))
    else:
        return profile

def get_preferred_name(client, group_id):
    '''
    Returns a string representing the user's preferred name, if available,
    or the first listed name if not available.

    Accepts emails or tilde ids.
    '''

    profile = client.get_profile(group_id)
    names = profile.content['names']
    preferred_names = [n for n in names if n.get('preferred', False)]
    if preferred_names:
        primary_preferred_name = preferred_names[0]
    else:
        primary_preferred_name = names[0]

    name_parts = []
    if primary_preferred_name.get('first'):
        name_parts.append(primary_preferred_name['first'])
    if primary_preferred_name.get('middle'):
        name_parts.append(primary_preferred_name['middle'])
    if primary_preferred_name.get('last'):
        name_parts.append(primary_preferred_name['last'])

    return ' '.join(name_parts)

def build_groups(conference_group_id, default_params=None):
    '''
    Given a group ID, returns a list of empty groups that correspond to the given group's subpaths

    (e.g. Test.com, Test.com/TestConference, Test.com/TestConference/2018)

    >>> [group.id for group in build_groups('ICML.cc/2019/Conference')]
    [u'ICML.cc', u'ICML.cc/2019', u'ICML.cc/2019/Conference']
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

def post_group_parents(client, group, overwrite_parents=False):
    '''
    Helper function for posting groups created by build_groups function.

    Recommended that this function be deprecated.
    '''
    groups = build_groups(group.id)

    posted_groups = []
    for g in groups:
        if g.id == group.id:
            posted_groups.append(client.post_group(group))
        else:
            if not client.exists(g.id) or overwrite_parents:
                posted_groups.append(client.post_group(g))
            else:
                posted_groups.append(g)

    return posted_groups

def get_bibtex(note, venue_fullname, year, url_forum=None, accepted=False, anonymous=True):
    '''
    Generates a bibtex field for a given Note.

    The "accepted" argument is used to indicate whether or not the paper was ultimately accepted.
    (OpenReview generates bibtex fields for rejected papers)

    The "anonymous" argument is used to indicate whether or not the paper's authors should be
    revealed.

    Warning: this function is a work-in-progress.
    '''

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

def subdomains(domain):
    '''
    Given an email address, returns a list with the domains and subdomains.

    >>> subdomains('johnsmith@iesl.cs.umass.edu')
    [u'iesl.cs.umass.edu', u'cs.umass.edu', u'umass.edu']
    '''

    if '@' in domain:
        full_domain = domain.split('@')[1]
    else:
        full_domain = domain
    domain_components = full_domain.split('.')
    domains = ['.'.join(domain_components[index:len(domain_components)]) for index, path in enumerate(domain_components)]
    valid_domains = [d for d in domains if '.' in d]
    return valid_domains

def profile_conflicts(profile):
    '''
    Given a profile, returns a tuple containing two sets: domain_conflicts and
    relation_conflicts.

    domain_conflicts is a set of domains/subdomains that may have a conflict of
    interest with the given profile.

    relation_conflicts is a set of group IDs (email addresses or profiles) that
    may have a conflict of interest with the given profile.

    .. todo:: Update this function after the migration to non-Note Profile objects.
    '''
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
    '''
    Helper function for profile_conflicts function. Given a reviewer ID or email
    address, requests the server for that reviewer's profile, and checks it for
    conflicts using profile_conflicts.

    '''
    try:
        profile = client.get_profile(reviewer_to_add)
        user_domain_conflicts, user_relation_conflicts = profile_conflicts(profile)
        user_relation_conflicts.update([reviewer_to_add])
    except openreview.OpenReviewException as e:
        user_domain_conflicts, user_relation_conflicts = (set(), set())

    return user_domain_conflicts, user_relation_conflicts

def get_paper_conflicts(client, paper):
    '''
    Given a Note object representing a submitted paper, returns a tuple containing
    two sets: domain_conflicts and relation_conflicts.

    domain_conflicts is a set of domains/subdomains that may have a conflict of
    interest with the given paper.

    relation_conflicts is a set of group IDs (email addresses or profiles) that
    may have a conflict of interest with the given paper.

    Automatically ignores domain conflicts with "gmail.com".

    .. todo:: Update this function after the migration to non-Note Profile objects.

    '''
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
    '''
    Returns the paperhash of a paper, given the title and first author.

    >>> get_paperhash('David Soergel', 'Open Scholarship and Peer Review: a Time for Experimentation')
    u'soergel|open_scholarship_and_peer_review_a_time_for_experimentation'

    '''

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
    '''
    Given a Group object, iterates through the Group's members and, for any member
    represented by an email address, attempts to find a profile associated with
    that email address. If a profile is found, replaces the email with the profile ID.

    Returns None.
    '''
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

def iterget(get_function, **kwargs):
    '''
    Iterator over a given get function from the client.
    '''
    done = False
    offset = 0
    params = {
        'limit': 1000 if 'limit' not in kwargs else kwargs['limit']
    }

    while not done:
        params['offset'] = offset

        params.update(kwargs)
        batch = get_function(**params)
        offset += params['limit']
        for obj in batch:
            yield obj

        if len(batch) < params['limit']:
            done = True

def get_all_tags(client, invitation, limit=1000):
    '''
    Given an invitation, returns all Tags that respond to it, ignoring API limit.
    '''
    return list(iterget(client.get_tags, invitation=invitation, limit=limit))

def get_all_notes(client, invitation, limit=1000):
    '''
    Given an invitation, returns all Notes that respond to it, ignoring API limit.
    '''
    return list(iterget(client.get_notes, invitation=invitation, limit=limit))

def next_individual_suffix(unassigned_individual_groups, individual_groups, individual_label):
    '''
    |  "individual groups" are groups with a single member;
    |  e.g. conference.org/Paper1/AnonReviewer1

    :arg unassigned_individual_groups: a list of individual groups with no members
    :arg individual_groups: the full list of individual groups, empty or not
    :arg individual_label: the "label" of the group: e.g. "AnonReviewer"

    :return: an individual group's suffix (e.g. AnonReviewer1)\n
        The suffix will be the next available empty group,\n
        or will be the suffix of the largest indexed group +1
    '''

    if len(unassigned_individual_groups) > 0:
        anonreviewer_group = unassigned_individual_groups[0]
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


def get_reviewer_groups(client, paper_number, conference, group_params, parent_label, individual_label):

    '''
    This is only intended to be used as a local helper function

    :arg paper_number: the number of the paper to assign
    :arg conference: the ID of the conference being assigned
    :arg group_params: optional parameter that overrides the default
    '''

    # get the parent group if it already exists, and create it if it doesn't.
    try:
        parent_group = client.get_group('{}/Paper{}/{}'.format(conference, paper_number, parent_label))
    except openreview.OpenReviewException as e:
        if 'Group Not Found' in e[0][0]:

            # Set the default values for the parent and individual groups
            group_params_default = {
                'readers': [conference, '{}/Program_Chairs'.format(conference)],
                'writers': [conference],
                'signatures': [conference],
                'signatories': []
            }
            group_params_default.update(group_params)
            group_params = group_params_default

            parent_group = client.post_group(openreview.Group(
                id = '{}/Paper{}/{}'.format(conference, paper_number, parent_label),
                nonreaders = ['{}/Paper{}/Authors'.format(conference, paper_number)],
                **group_params
            ))
        else:
            raise e

    '''
    get the existing individual groups, while making sure that the parent group isn't included.
    This can happen if the parent group and the individual groups are named similarly.

    For example, if:
        parent_group_label = "Area_Chairs"
        individual_group_label = "Area_Chairs"

        Then the call for individual groups by wildcard will pick up all the
        individual groups AND the parent group.
    '''

    individual_groups = client.get_groups(id = '{}/Paper{}/{}.*'.format(conference, paper_number, individual_label))
    individual_groups = [g for g in individual_groups if g.id != parent_group.id]
    unassigned_individual_groups = sorted([ a for a in individual_groups if a.members == [] ], key=lambda x: x.id)
    return [parent_group, individual_groups, unassigned_individual_groups]



def add_assignment(client, paper_number, conference, reviewer,
                    parent_group_params = {},
                    individual_group_params = {},
                    parent_label = 'Reviewers',
                    individual_label = 'AnonReviewer'):

    '''
    |  Assigns a reviewer to a paper.
    |  Also adds the given user to the parent and individual groups defined by the paper number, conference, and labels
    |  "individual groups" are groups with a single member;
    |      e.g. conference.org/Paper1/AnonReviewer1
    |  "parent group" is the group that contains the individual groups;
    |      e.g. conference.org/Paper1/Reviewers

    :arg paper_number: the number of the paper to assign
    :arg conference: the ID of the conference being assigned
    :arg reviewer: may be an email address or a tilde ID;
    :arg parent_group_params: optional parameter that overrides the default
    :arg individual_group_params: optional parameter that overrides the default
    '''

    result = get_reviewer_groups(client, paper_number, conference, parent_group_params, parent_label, individual_label)
    parent_group = result[0]
    individual_groups = result[1]
    unassigned_individual_groups = result[2]

    '''
    Adds the given user to the parent group, and to the next empty individual group.
    Prints the results to the console.
    '''
    profile = get_profile(client, reviewer)
    user = profile.id if profile else reviewer

    if user not in parent_group.members:
        client.add_members_to_group(parent_group, user)
        print("{:40s} --> {}".format(user.encode('utf-8'), parent_group.id))

    assigned_individual_groups = [a for a in individual_groups if user in a.members]
    if not assigned_individual_groups:
        # assign reviewer to group
        suffix = next_individual_suffix(unassigned_individual_groups, individual_groups, individual_label)
        anonreviewer_id = '{}/Paper{}/{}'.format(conference, paper_number, suffix)
        paper_authors = '{}/Paper{}/Authors'.format(conference, paper_number)

        # Set the default values for the individual groups
        individual_group_params_default = {
            'readers': [conference, '{}/Program_Chairs'.format(conference)],
            'writers': [conference],
            'signatures': [conference],
            'signatories': []
        }
        individual_group_params_default.update(individual_group_params)
        individual_group_params = individual_group_params_default

        individual_group = openreview.Group(
            id = anonreviewer_id,
            **individual_group_params)

        individual_group.readers.append(anonreviewer_id)
        individual_group.nonreaders.append(paper_authors)
        individual_group.signatories.append(anonreviewer_id)
        individual_group.members.append(user)

        print("{:40s} --> {}".format(user.encode('utf-8'), individual_group.id))
        return client.post_group(individual_group)
    else:
        # user already assigned to individual group(s)
        for g in assigned_individual_groups:
            print("{:40s} === {}".format(user.encode('utf-8'), g.id))
        return assigned_individual_groups[0]


def remove_assignment(client, paper_number, conference, reviewer,
    parent_group_params = {},
    parent_label = 'Reviewers',
    individual_label = 'AnonReviewer'):

    '''
    |  Un-assigns a reviewer from a paper.
    |  Removes the given user from the parent group, and any assigned individual groups.

    |  "individual groups" are groups with a single member;
    |      e.g. conference.org/Paper1/AnonReviewer1
    |  "parent group" is the group that contains the individual groups;
    |      e.g. conference.org/Paper1/Reviewers

    :arg paper_number: the number of the paper to assign
    :arg conference: the ID of the conference being assigned
    :arg reviewer: same as @reviewer_to_add, but removes the user
    :arg parent_group_params: optional parameter that overrides the default
    :arg individual_group_params: optional parameter that overrides the default
    '''

    result = get_reviewer_groups(client, paper_number, conference, parent_group_params, parent_label, individual_label)
    parent_group = result[0]
    individual_groups = result[1]

    profile = get_profile(client, reviewer)
    user = profile.id if profile else reviewer

    '''
    Removes the given user from the parent group,
        and any assigned individual groups.
    '''

    user_groups = [g.id for g in client.get_groups(member=user)]

    for user_entity in user_groups:
        if user_entity in parent_group.members:
            client.remove_members_from_group(parent_group, user_entity)
            print("{:40s} xxx {}".format(user_entity, parent_group.id))

        assigned_individual_groups = [a for a in individual_groups if user_entity in a.members]
        for individual_group in assigned_individual_groups:
            print("{:40s} xxx {}".format(user_entity, individual_group.id))
            client.remove_members_from_group(individual_group, user_entity)


def assign(client, paper_number, conference,
    parent_group_params = {},
    individual_group_params = {},
    reviewer_to_add = None,
    reviewer_to_remove = None,
    parent_label = 'Reviewers',
    individual_label = 'AnonReviewer'):

    '''
    Either assigns or unassigns a reviewer to a paper.
    TODO: Is this function really necessary?

    "individual groups" are groups with a single member;
    e.g. conference.org/Paper1/AnonReviewer1
    "parent group" is the group that contains the individual groups;
    e.g. conference.org/Paper1/Reviewers

    :arg paper_number: the number of the paper to assign
    :arg conference: the ID of the conference being assigned
    :arg parent_group_params: optional parameter that overrides the default
    :arg individual_group_params: optional parameter that overrides the default
    :arg reviewer_to_add: may be an email address or a tilde ID; adds the given user to the parent and individual groups defined by the paper number, conference, and labels
    :arg reviewer_to_remove: same as @reviewer_to_add, but removes the user

    It's important to remove any users first, so that we can do direct replacement of one user with another.

    For example: passing in a reviewer to remove AND a reviewer to add should replace the first user with the second.
    '''
    if reviewer_to_remove:
        remove_assignment(client, paper_number, conference, reviewer_to_remove,
                          parent_group_params, parent_label, individual_label)
    if reviewer_to_add:
        add_assignment(client, paper_number, conference, reviewer_to_add,
                        parent_group_params,
                        individual_group_params,
                        parent_label,
                        individual_label)


def timestamp_GMT(year, month, day, hour=0, minute=0, second=0):
    '''
    Given year, month, day, and (optionally) hour, minute, second in GMT time zone:
    returns the number of milliseconds between this day and Epoch Time (Jan 1, 1970).

    >>> timestamp_GMT(1990, 12, 20, hour=12, minute=30, second=24)
    661696224000

    '''
    return int((datetime.datetime(year, month, day, hour, minute, second) - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

def recruit_reviewer(client, email, first,
    hash_seed,
    recruit_reviewers_id,
    recruit_message,
    recruit_message_subj,
    reviewers_invited_id,
    verbose=True):
    '''
    Recruit a reviewer. Sends an email to the reviewer with a link to accept or
    reject the recruitment invitation.

    :arg hash_seed: a random number for seeding the hash.
    :arg recruit_message: a formattable string containing the following string variables: (name, accept_url, decline_url)
    :arg recruit_message_subj: subject line for the recruitment email
    :arg reviewers_invited_id: group ID for the "Reviewers Invited" group, often used to keep track of which reviewers have already been emailed.
    '''


    hashkey = HMAC.new(hash_seed, msg=email.encode('utf-8'), digestmod=SHA256).hexdigest()

    # build the URL to send in the message
    url = '{baseurl}/invitation?id={recruitment_inv}&email={email}&key={hashkey}&response='.format(
        baseurl = client.baseurl,
        recruitment_inv = recruit_reviewers_id,
        email = email,
        hashkey = hashkey
    )

    # format the message defined above
    personalized_message = recruit_message.format(
        name = first,
        accept_url = url + "Yes",
        decline_url = url + "No"
    )

    # send the email through openreview
    response = client.send_mail(recruit_message_subj, [email], personalized_message)

    if 'groups' in response and response['groups']:
        reviewers_invited = client.get_group(reviewers_invited_id)
        client.add_members_to_group(reviewers_invited, response['groups'])

    if verbose:
        print("Sent to the following: ", response)
        print(personalized_message)

def post_submission_groups(client, conference_id, submission_invite, chairs):
    '''
    Create paper group, authors group, reviewers group, review non-readers group
    for all notes returned by the submission_invite.
    '''
    submissions = client.get_notes(invitation=submission_invite)
    for paper in submissions:
        paper_num = str(paper.number)
        print("Adding groups for Paper" + paper_num)

        ## Paper Group
        paperGroup = conference_id + '/Paper' + paper_num
        client.post_group(openreview.Group(
            id=paperGroup,
            signatures=[conference_id],
            writers=[conference_id],
            members=[],
            readers=['everyone'],
            signatories=[]))

        ## Author group
        authorGroup = paperGroup + '/Authors'
        client.post_group(openreview.Group(
            id=authorGroup,
            signatures=[conference_id],
            writers=[conference_id],
            members=paper.content['authorids'],
            readers=[conference_id, chairs, authorGroup],
            signatories=[]))

        ## Reviewer group - people that can see the review invitation
        reviewerGroup = paperGroup + '/Reviewers'
        client.post_group(openreview.Group(
            id=reviewerGroup,
            signatures=[conference_id],
            writers=[conference_id],
            members=[],
            readers=[conference_id, chairs],
            signatories=[]))

        ## NonReviewers - people that aren't allowed to see the reviews.
        # Used to prevent reviewers from seeing other reviews of that paper
        # until their review is complete.
        nonReviewerGroup = reviewerGroup + '/NonReaders'
        client.post_group(openreview.Group(
            id=nonReviewerGroup,
            signatures=[conference_id],
            writers=[conference_id],
            members=[],
            readers=[conference_id, chairs],
            signatories=[]))

def get_submission_invitations(client, open_only=False):
    '''
    Returns a list of invitation ids visible to the client according to the value of parameter "open_only".

    :arg client: Object of :class:`~openreview.Client` class
    :arg open_only: Default value is False. This is a boolean param with value True implying that the results would be invitations having a future due date.

    Example Usage:

    >>> get_submission_invitations(c,True)
    [u'machineintelligence.cc/MIC/2018/Conference/-/Submission', u'machineintelligence.cc/MIC/2018/Abstract/-/Submission', u'ISMIR.net/2018/WoRMS/-/Submission', u'OpenReview.net/Anonymous_Preprint/-/Submission']
    '''

    #Calculate the epoch for current timestamp
    now = int(time.time()*1000)
    duedate = now if open_only==True else None
    invitations = client.get_invitations(regex='.*/-/.*[sS]ubmission.*',minduedate=duedate)

    # For each group in the list, append the invitation id to a list
    invitation_ids = [inv.id for inv in invitations]

    return invitation_ids

def get_all_venues(client):
    '''
    Returns a list of all the venues

    :arg client: Object of :class:`~openreview.Client` class
    '''
    return client.get_group("host").members
