#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os

from deprecated.sphinx import deprecated
import sys
import openreview
import re
import datetime
import time
from pylatexenc.latexencode import utf8tolatex, unicode_to_latex, UnicodeToLatexConversionRule, UnicodeToLatexEncoder, RULE_REGEX
from Crypto.Hash import HMAC, SHA256
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import tld
import urllib.parse as urlparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor


def run_once(f):
    """
    Decorator to run a function only once and return its output for any subsequent call to the function without running
    it again
    """
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            wrapper.to_return = f(*args, **kwargs)
        return wrapper.to_return
    wrapper.has_run = False
    return wrapper


def concurrent_requests(request_func, params, max_workers=min(6, cpu_count() - 1)):
    """
    Returns a list of results given for each request_func param execution. It shows a progress bar to know the progress of the task.

    :param request_func: a function to execute for each value of the list.
    :type request_func: function
    :param params: a list of values to be executed by request_func.
    :type params: list
    :param max_workers: number of workers to use in the multiprocessing tool, default value is 6.
    :type max_workers: int

    :return: A list of results given for each func value execution
    :rtype: list
    """
    futures = []
    gathering_responses = tqdm(total=len(params), desc='Gathering Responses')
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for param in params:
            futures.append(executor.submit(request_func, param))

        for future in futures:
            gathering_responses.update(1)
            results.append(future.result())

        gathering_responses.close()

        return results

def get_profile(client, value, with_publications=False):
    """
    Get a single profile (a note) by id, if available

    :param client: User that will retrieve the profile
    :type client: Client
    :param value: e-mail or id of the profile
    :type value: str

    :return: Profile with that matches the value passed as parameter
    :rtype: Profile
    """
    profile = None
    try:
        profile = client.get_profile(value)
        if with_publications:
            baseurl_v1 = 'http://localhost:3000'
            baseurl_v2 = 'http://localhost:3001'

            if 'https://devapi' in client.baseurl:
                baseurl_v1 = 'https://devapi.openreview.net'
                baseurl_v2 = 'https://devapi2.openreview.net'
            if 'https://api' in client.baseurl:
                baseurl_v1 = 'https://api.openreview.net'
                baseurl_v2 = 'https://api2.openreview.net'

            client_v1 = openreview.Client(baseurl=baseurl_v1, token=client.token)
            #client_v2 = openreview.api.OpenReviewClient(baseurl=baseurl_v2, token=client.token)
            notes_v1 = list(iterget_notes(client_v1, content={'authorids': profile.id}))
            #notes_v2 = list(iterget_notes(client_v2, content={'authorids': profile.id}))
            profile.content['publications'] = notes_v1 #+ notes_v2
    except openreview.OpenReviewException as e:
        # throw an error if it is something other than "not found"
        if 'Profile Not Found' not in e.args[0]:
            raise e
    return profile

def get_profiles(client, ids_or_emails, with_publications=False):
    '''
    Helper function that repeatedly queries for profiles, given IDs and emails.
    Useful for getting more Profiles than the server will return by default (1000)
    '''
    ids = []
    emails = []
    for member in ids_or_emails:
        if '~' in member:
            ids.append(member)
        else:
            emails.append(member)

    profiles = []
    profile_by_email = {}

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_profiles = client.search_profiles(ids=batch_ids)
        profiles.extend(batch_profiles)

    for j in range(0, len(emails), batch_size):
        batch_emails = emails[j:j+batch_size]
        batch_profile_by_email = client.search_profiles(confirmedEmails=batch_emails)
        profile_by_email.update(batch_profile_by_email)

    for email in emails:
        profiles.append(profile_by_email.get(email, openreview.Profile(
            id=email,
            content={
                'emails': [email],
                'preferredEmail': email,
                'emailsConfirmed': [email],
                'names': []
            })))

    if with_publications:
        baseurl_v1 = 'http://localhost:3000'
        baseurl_v2 = 'http://localhost:3001'

        if 'https://devapi' in client.baseurl:
            baseurl_v1 = 'https://devapi.openreview.net'
            baseurl_v2 = 'https://devapi2.openreview.net'
        if 'https://api' in client.baseurl:
            baseurl_v1 = 'https://api.openreview.net'
            baseurl_v2 = 'https://api2.openreview.net'

        client_v1 = openreview.Client(baseurl=baseurl_v1, token=client.token)
        client_v2 = openreview.api.OpenReviewClient(baseurl=baseurl_v2, token=client.token)

        notes_v1 = concurrent_requests(lambda profile : client_v1.get_all_notes(content={'authorids': profile.id}), profiles)
        for idx, publications in enumerate(notes_v1):
            profiles[idx].content['publications'] = publications

        notes_v2 = concurrent_requests(lambda profile : client_v2.get_all_notes(content={'authorids': profile.id}), profiles)
        for idx, publications in enumerate(notes_v2):
            if profiles[idx].content.get('publications'):
                profiles[idx].content['publications'] = profiles[idx].content['publications'] +  publications
            else:
                profiles[idx].content['publications'] = publications

    return profiles

def get_group(client, id):
    """
    Get a single Group by id if available

    :param client: User that will retrieve the group
    :type client: Client
    :param id: id of the group
    :type id: str

    :return: Group that matches the passed id
    :rtype: Group
    """
    group = None
    try:
        group = client.get_group(id = id)
    except openreview.OpenReviewException as e:
        # throw an error if it is something other than "not found"
        error =  e.args[0]
        if error.get('name') == 'NotFoundError' or error.get('message').startswith('Group Not Found'):
            return None
        else:
            raise e
    return group

def get_invitation(client, id):
    """
    Get a single Invitation by id if available

    :param client: User that will retrieve the invitation
    :type client: Client
    :param id: id of the invitation
    :type id: str

    :return: Invitation that matches the passed id or None if it does not exist or it is expired
    :rtype: Invitation
    """
    invitation = None
    try:
        invitation = client.get_invitation(id = id)
    except openreview.OpenReviewException as e:
        print('Can not retrieve invitation', e)
    return invitation

def create_profile(client, email, first, last, middle=None, allow_duplicates=False):

    """
    Given email, first name, last name, and middle name (optional), creates a new profile.

    :param client: User that will create the Profile
    :type client: Client
    :param email: Preferred e-mail in the Profile
    :type email: str
    :param first: First name of the user
    :type first: str
    :param last: Last name of the user
    :type last: str
    :param middle: Middle name of the user
    :type middle: str, optional
    :param allow_duplicates: If a profile with the same name exists, and allow_duplicates is False, an exception is raised. If a profile with the same name exists and allow_duplicates is True, a profile is created with the next largest number (e.g. if ~Michael_Spector1 exists, ~Michael_Spector2 will be created)
    :type allow_duplicates: bool, optional

    :return: The created Profile
    :rtype: Profile
    """

    profile = get_profile(client, email)

    if not profile:

        # validate the name with just first and last names,
        # and also with first, middle, and last.
        # this is so that we catch more potential collisions;
        # let the caller decide what to do with false positives.

        username_response_FL_only = client.get_tildeusername(
            first,
            last,
            None
        )

        username_response_full = client.get_tildeusername(
            first,
            last,
            middle
        )

        # the username in each response will end with 1
        # if profiles don't exist for those names
        username_FL_unclaimed = username_response_FL_only['username'].endswith('1')
        username_full_unclaimed = username_response_full['username'].endswith('1')

        if all([username_FL_unclaimed, username_full_unclaimed]):
            profile_exists = False
        else:
            profile_exists = True

        tilde_id = username_response_full['username']
        if (not profile_exists) or allow_duplicates:

            tilde_group = openreview.Group(id=tilde_id, signatures=[client.profile.id], signatories=[tilde_id], readers=[tilde_id], writers=[client.profile.id], members=[email])
            email_group = openreview.Group(id=email, signatures=[client.profile.id], signatories=[email], readers=[email], writers=[client.profile.id], members=[tilde_id])
            profile_content = {
                'emails': [email],
                'preferredEmail': email,
                'names': [
                    {
                        'first': first,
                        'middle': middle,
                        'last': last,
                        'username': tilde_id
                    }
                ],
                'homepage': 'http://no_url'
            }
            client.post_group(tilde_group)
            client.post_group(email_group)

            profile = client.post_profile(openreview.Profile(id=tilde_id, content=profile_content, signatures=[tilde_id]))

            return profile

        else:
            raise openreview.OpenReviewException(
                'Failed to create new profile {tilde_id}: There is already a profile with the name: \"{first} {middle} {last}\"'.format(
                    first=first, middle=middle, last=last, tilde_id=tilde_id))
    else:
        raise openreview.OpenReviewException('There is already a profile with this email address: {}'.format(email))

def create_authorid_profiles(client, note, print=print):
    # for all submissions get authorids, if in form of email address, try to find associated profile
    # if profile doesn't exist, create one
    created_profiles = []

    def clean_name(name):
        '''
        Replaces invalid characters with equivalent valid ones.
        '''
        return name.replace('’', "'")

    def get_names(author_name):
        '''
        Splits a string into first and last (and middle, if applicable) names.
        '''
        names = author_name.split(' ')
        if len(names) > 1:
            first = names[0]
            last = names[-1]
            middle = ' '.join(names[1:-1])
            return [clean_name(n) for n in [first, last, middle]]
        else:
            return []

    if 'authorids' in note.content and 'authors' in note.content:
        author_names = [a.replace('*', '') for a in note.content['authors']]
        author_emails = [e for e in note.content['authorids']]
        if len(author_names) == len(author_emails):
            # iterate through authorids and authors at the same time
            for (author_id, author_name) in zip(author_emails, author_names):
                author_id = author_id.strip()
                author_name = author_name.strip()

                if '@' in author_id:
                    names = get_names(author_name)
                    if names:
                        try:
                            profile = create_profile(client=client, email=author_id, first=names[0], last=names[1], middle=names[2])
                            created_profiles.append(profile)
                            print('{}: profile created with id {}'.format(note.id, profile.id))
                        except openreview.OpenReviewException as e:
                            print('Error while creating profile for note id {note_id}, author {author_id}, '.format(note_id=note.id, author_id=author_id), e)
                    else:
                        print('{}: invalid author name {}'.format(note.id, author_name))
        else:
            print('{}: length mismatch. authors ({}), authorids ({})'.format(
                note.id,
                len(author_names),
                len(author_emails)
                ))

    return created_profiles

def get_preferred_name(profile, last_name_only=False):
    """
    Accepts openreview.Profile object

    :param profile: Profile from which the preferred name will be retrieved
    :type profile: Profile

    :return: User's preferred name, if available, or the first listed name if not available.
    :rtype: str
    """

    names = profile.content['names']
    preferred_names = [n for n in names if n.get('preferred', False)]
    if preferred_names:
        primary_preferred_name = preferred_names[0]
    else:
        primary_preferred_name = names[0]

    if last_name_only:
        return primary_preferred_name['last']

    name_parts = []
    if primary_preferred_name.get('first'):
        name_parts.append(primary_preferred_name['first'])
    if primary_preferred_name.get('middle'):
        name_parts.append(primary_preferred_name['middle'])
    if primary_preferred_name.get('last'):
        name_parts.append(primary_preferred_name['last'])

    return ' '.join(name_parts)

def build_groups(conference_group_id, default_params=None):
    """
    Given a group ID, returns a list of empty groups that correspond to the given group's subpaths

    (e.g. Test.com, Test.com/TestConference, Test.com/TestConference/2018)

    :param conference_group_id: Conference Group id (e.g. Test.com/TestConference/2018)
    :type conference_group_id: str
    :param default_params: Dictionary that contains the values of the instance variables of each of the Groups
    :type default_params: dict, optional

    :return: List of the created Groups sorted from general to particular
    :rtype: list[Group]

    Example:

    >>> [group.id for group in build_groups('ICML.cc/2019/Conference')]
    [u'ICML.cc', u'ICML.cc/2019', u'ICML.cc/2019/Conference']
    """

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

@deprecated(version='0.9.20')
def post_group_parents(client, group, overwrite_parents=False):
    """
    This function calls :func:`tools.build_groups` using the id of the group parameter. Each group generated from group.id is posted by calling :meth:`openreview.Client.post_group`

    :param client: User that will post the Groups
    :type client: Client
    :param group: Group from which the id will be extracted to create empty Groups
    :type group: Group
    :param overwrite_parents:
    :type overwrite_parents: bool, optional

    :return: List of posted Groups
    :rtype: list[Group]
    """
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

def get_bibtex(note, venue_fullname, year, url_forum=None, accepted=False, anonymous=True, names_reversed = False, baseurl='https://openreview.net', editor=None):
    """
    Generates a bibtex field for a given Note.

    :param note: Note from which the bibtex is generated
    :type note: Note
    :param venue_fullname: Full name of the venue to be placed in the book title field
    :type venue_fullname: str
    :param year: Note year
    :type year: str
    :param url_forum: Forum id, if none is provided, it is obtained from the note parameter: note.forum
    :type url_forum: str, optional
    :param accepted: Used to indicate whether or not the paper was ultimately accepted
    :type accepted: bool, optional
    :param anonymous: Used to indicate whether or not the paper's authors should be revealed
    :type anonymous: bool, optional
    :param names_reversed: If true, it indicates that the last name is written before the first name
    :type names_reversed: bool, optional
    :param baseurl: Base url where the bibtex is from. Default https://openreview.net
    :type baseurl: str, optional

    :return: Note bibtex
    :rtype: str
    """

    first_word = re.sub('[^a-zA-Z]', '', note.content['title'].split(' ')[0].lower())

    forum = note.forum if not url_forum else url_forum

    if anonymous:
        first_author_last_name = 'anonymous'
        authors = 'Anonymous'
    else:
        first_author_last_name = note.content['authors'][0].split(' ')[-1].lower()
        if names_reversed:
            # last, first
            author_list = []
            for name in note.content['authors']:
                last = name.split(' ')[-1]
                rest = (' ').join(name.split(' ')[:-1])
                author_list.append(last+', '+rest)
            authors = ' and '.join(author_list)
        else:
            authors = ' and '.join(note.content['authors'])

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
    bibtex_title = u.unicode_to_latex(note.content['title'])

    under_review_bibtex = [
        '@inproceedings{',
        utf8tolatex(first_author_last_name + year + first_word + ','),
        'title={' + bibtex_title + '},',
        'author={' + utf8tolatex(authors) + '},',
        'booktitle={Submitted to ' + utf8tolatex(venue_fullname) + '},',
        'year={' + year + '},',
        'url={'+baseurl+'/forum?id=' + forum + '},',
        'note={under review}',
        '}'
    ]

    rejected_bibtex = [
        '@misc{',
        utf8tolatex(first_author_last_name + year + first_word + ','),
        'title={' + bibtex_title + '},',
        'author={' + utf8tolatex(authors) + '},',
        'year={' + year + '},',
        'url={'+baseurl+'/forum?id=' + forum + '}',
        '}'
    ]

    accepted_bibtex = [
        '@inproceedings{',
        utf8tolatex(first_author_last_name + year + first_word + ','),
        'title={' + bibtex_title + '},',
        'author={' + utf8tolatex(authors) + '},',
        'booktitle={' + utf8tolatex(venue_fullname) + '},'
    ]
    if editor:
        accepted_bibtex.append('editor={' + utf8tolatex(editor) + '},')

    accepted_bibtex = accepted_bibtex + [
        'year={' + year + '},',
        'url={'+baseurl+'/forum?id=' + forum + '}',
        '}'
    ]

    bibtex = rejected_bibtex
    if accepted:
        bibtex = accepted_bibtex
    else:
        if anonymous:
            # We assume the paper is under review
            bibtex = under_review_bibtex

    return '\n'.join(bibtex)


@run_once
def load_duplicate_domains():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, 'duplicate_domains.json')) as f:
        duplicate_domains = json.load(f)

    f.close()
    return duplicate_domains


def subdomains(domain):
    """
    Given an email address, returns a list with the domains and subdomains.

    :param domain: e-mail address or domain of the e-mail address
    :type domain: str

    :return: List of domains and subdomains
    :rtype: list[str]

    Example:

    >>> subdomains('johnsmith@iesl.cs.umass.edu')
    [u'iesl.cs.umass.edu', u'cs.umass.edu', u'umass.edu']
    """

    duplicate_domains: dict = load_duplicate_domains()
    if '@' in domain:
        full_domain = domain.split('@')[1]
    else:
        full_domain = domain
    domain_components = [c for c in full_domain.split('.') if c and not c.isspace()]
    domains = ['.'.join(domain_components[index:len(domain_components)]) for index, path in enumerate(domain_components)]
    valid_domains = set()
    for d in domains:
        if not tld.is_tld(d):
            valid_domains.add(duplicate_domains.get(d, d))

    return sorted(valid_domains)

def get_paperhash(first_author, title):
    """
    Returns the paperhash of a paper, given the title and first author.

    :param first_author: First author that appears on the paper
    :type first_author: str
    :param title: Title of the paper
    :type title: str

    :return: paperhash, see example
    :rtype: str

    Example:

    >>> get_paperhash('David Soergel', 'Open Scholarship and Peer Review: a Time for Experimentation')
    u'soergel|open_scholarship_and_peer_review_a_time_for_experimentation'

    """

    title = title.strip()
    strip_punctuation = '[^A-zÀ-ÿ\d\s]'
    title = re.sub(strip_punctuation, '', title)
    first_author = re.sub(strip_punctuation, '', first_author)
    first_author = first_author.split(' ').pop()
    title = re.sub(strip_punctuation, '', title)
    title = re.sub('\r|\n', '', title)
    title = re.sub('\s+', '_', title)
    first_author = re.sub(strip_punctuation, '', first_author)
    return (first_author + '|' + title).lower()

def replace_members_with_ids(client, group):
    """
    Given a Group object, iterates through the Group's members and, for any member represented by an email address, attempts to find a profile associated with that email address. If a profile is found, replaces the email with the profile id.

    :param client: Client used to get the Profiles and to post the new Group
    :type client: Client
    :param group: Group for which the profiles will be updated
    :type group: Group

    :return: Group with the emails replaced by Profile ids
    :rtype: Group
    """
    ids = []
    emails = []

    def classify_members(member):
        if '@' in member:
            try:
                profile = client.get_profile(member.lower())
                return 'ids', profile.id
            except openreview.OpenReviewException as e:
                if 'Profile Not Found' in e.args[0]:
                    return 'emails', member.lower()
                else:
                    raise e
        elif '~' in member:
            profile = client.get_profile(member)
            return 'ids', profile.id
        else:
            _group = client.get_group(member)
            return 'ids', _group.id

    results = concurrent_requests(classify_members, group.members)

    for key, member in results:
        if key == 'ids':
            ids.append(member)
        elif key == 'emails':
            emails.append(member)

    group.members = ids + emails

    return client.post_group(group)

def concurrent_get(client, get_function, **params):
    """
    Given a function that takes a single parameter, returns a list of results.

    :param client: Client used to make requests
    :param get_function: Function that takes a that performs the request
    :type get_function: function
    :param params: Parameters to pass to the get_function
    :type params: dict

    :return: List of results
    :rtype: list
    """
    max_workers = min(cpu_count() - 1, 6)

    params.update({
        'offset': params.get('offset') or 0,
        'limit': min(params.get('limit') or client.limit, client.limit),
        'with_count': True
    })

    docs, count = get_function(**params)
    if count <= params['limit']:
        return docs

    params['with_count'] = False

    offset_list = list(range(params['limit'], count, params['limit']))

    futures = []
    gathering_responses = tqdm(total=len(offset_list), desc='Gathering Responses')

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for offset in offset_list:
            params['offset'] = offset
            futures.append(executor.submit(get_function, **params))

        for future in futures:
            gathering_responses.update(1)
            docs.extend(future.result())

        gathering_responses.close()

        return docs

class iterget:
    """
    This class can create an iterator from a getter method that returns a list. Below all the iterators that can be created from a getter method:

    :meth:`openreview.Client.get_tags` --> :func:`tools.iterget_tags`

    :meth:`openreview.Client.get_notes` --> :func:`tools.iterget_notes`

    :meth:`openreview.Client.get_references` --> :func:`tools.iterget_references`

    :meth:`openreview.Client.get_invitations` --> :func:`tools.iterget_invitations`

    :meth:`openreview.Client.get_groups` --> :func:`tools.iterget_groups`

    :param get_function: Any of the aforementioned methods
    :type get_function: function
    :param params: Dictionary containing parameters for the corresponding method. Refer to the passed method documentation for details
    :type params: dict
    """
    def __init__(self, get_function, **params):
        self.offset = 0

        self.last_batch = False
        self.batch_finished = False
        self.obj_index = 0

        self.params = params
        self.params.update({
            'offset': self.offset,
            'limit': params.get('limit') or 1000
        })

        self.get_function = get_function
        self.current_batch = self.get_function(**self.params)

    def update_batch(self):
        self.offset += self.params['limit']
        self.params['offset'] = self.offset
        next_batch = self.get_function(**self.params)
        if next_batch:
            self.current_batch = next_batch
        else:
            self.current_batch = []

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.current_batch) == 0:
            raise StopIteration
        else:
            next_obj = self.current_batch[self.obj_index]
            if (self.obj_index + 1) == len(self.current_batch):
                self.update_batch()
                self.obj_index = 0
            else:
                self.obj_index += 1
            return next_obj

    next = __next__


def iterget_messages(client, to = None, subject = None, status = None):
    """
    Returns an iterator over Messages ignoring API limit.

    Example:

    >>> iterget_messages(client, to='melisa@mail.com')

    :return: Iterator over Messages filtered by the provided parameters
    :rtype: iterget
    """
    params = {
        'to': to,
        'subject': subject,
        'status': status
    }

    return iterget(client.get_messages, **params)

def iterget_tags(client, id = None, invitation = None, forum = None, signature = None, tag = None):
    """
    Returns an iterator over Tags ignoring API limit.

    Example:

    >>> iterget_tags(client, invitation='MyConference.org/-/Bid_Tags')

    :param client: Client used to get the Tags
    :type client: Client
    :param id: a Tag ID. If provided, returns Tags whose ID matches the given ID.
    :type id: str, optional
    :param forum: a Note ID. If provided, returns Tags whose forum matches the given ID.
    :type forum: str, optional
    :param invitation: an Invitation ID. If provided, returns Tags whose "invitation" field is this Invitation ID.
    :type invitation: str, optional

    :return: Iterator over Tags filtered by the provided parameters
    :rtype: iterget
    """
    params = {}

    if id is not None:
        params['id'] = id
    if forum is not None:
        params['forum'] = forum
    if invitation is not None:
        params['invitation'] = invitation
    if signature is not None:
        params['signature'] = signature
    if tag is not None:
        params['tag'] = tag

    return iterget(client.get_tags, **params)

def iterget_edges (client,
                   invitation = None,
                   head = None,
                   tail = None,
                   label = None,
                   limit = None):
    params = {}
    if invitation is not None:
        params['invitation'] = invitation
    if head is not None:
        params['head'] = head
    if tail is not None:
        params['tail'] = tail
    if label is not None:
        params['label'] = label
    if limit is not None:
        params['limit'] = limit
    return iterget(client.get_edges, **params)

def iterget_grouped_edges(
        client,
        invitation=None,
        groupby='head',
        select='id,tail,label,weight',
        logger=None
    ):
    '''Helper function for retrieving and parsing all edges in bulk'''

    ## Backend has pagination temporally disabled, it returns all the groups now so we need to do one iteration.
    grouped_edges_iterator = client.get_grouped_edges(invitation=invitation, groupby=groupby, select=select)

    for group in grouped_edges_iterator:
        group_edges = []

        for group_values in group['values']:
            edge_params = {
                'readers': [],
                'writers': [],
                'signatures': [],
                'invitation': invitation
            }
            edge_params.update(group_values)
            edge_params.update(group['id'])
            group_edges.append(openreview.Edge(**edge_params))

        yield group_edges


def iterget_notes(client,
    id = None,
    paperhash = None,
    forum = None,
    invitation = None,
    replyto = None,
    tauthor = None,
    signature = None,
    writer = None,
    trash = None,
    number = None,
    mintcdate = None,
    content = None,
    details = None,
    sort = None):
    """
    Returns an iterator over Notes filtered by the provided parameters ignoring API limit.

    :param client: Client used to get the Notes
    :type client: Client
    :param id: a Note ID. If provided, returns Notes whose ID matches the given ID.
    :type id: str, optional
    :param paperhash: a "paperhash" for a note. If provided, returns Notes whose paperhash matches this argument. (A paperhash is a human-interpretable string built from the Note's title and list of authors to uniquely identify the Note)
    :type paperhash: str, optional
    :param forum: a Note ID. If provided, returns Notes whose forum matches the given ID.
    :type forum: str, optional
    :param invitation: an Invitation ID. If provided, returns Notes whose "invitation" field is this Invitation ID.
    :type invitation: str, optional
    :param replyto: a Note ID. If provided, returns Notes whose replyto field matches the given ID.
    :type replyto: str, optional
    :param tauthor: a Group ID. If provided, returns Notes whose tauthor field ("true author") matches the given ID, or is a transitive member of the Group represented by the given ID.
    :type tauthor: str, optional
    :param signature: a Group ID. If provided, returns Notes whose signatures field contains the given Group ID.
    :type signature: str, optional
    :param writer: a Group ID. If provided, returns Notes whose writers field contains the given Group ID.
    :type writer: str, optional
    :param trash: If True, includes Notes that have been deleted (i.e. the ddate field is less than the current date)
    :type trash: bool, optional
    :param number: If present, includes Notes whose number field equals the given integer.
    :type number: int, optional
    :param mintcdate: Represents an Epoch time timestamp in milliseconds. If provided, returns Notes whose "true creation date" (tcdate) is at least equal to the value of mintcdate.
    :type mintcdate: int, optional
    :param content: If present, includes Notes whose each key is present in the content field and it is equals the given value.
    :type content: dict, optional
    :param details: TODO: What is a valid value for this field?
    :type details: str, optional

    :return: Iterator over Notes filtered by the provided parameters
    :rtype: iterget
    """
    params = {}
    if id is not None:
        params['id'] = id
    if paperhash is not None:
        params['paperhash'] = paperhash
    if forum is not None:
        params['forum'] = forum
    if invitation is not None:
        params['invitation'] = invitation
    if replyto is not None:
        params['replyto'] = replyto
    if tauthor is not None:
        params['tauthor'] = tauthor
    if signature is not None:
        params['signature'] = signature
    if writer is not None:
        params['writer'] = writer
    if trash == True:
        params['trash']=True
    if number is not None:
        params['number'] = number
    if mintcdate is not None:
        params['mintcdate'] = mintcdate
    if content is not None:
        params['content'] = content
    if details is not None:
        params['details'] = details
    params['sort'] = sort

    return iterget(client.get_notes, **params)

def iterget_references(client, referent = None, invitation = None, mintcdate = None):
    """
    Returns an iterator over references filtered by the provided parameters ignoring API limit.

    :param client: Client used to get the references
    :type client: Client
    :param referent: a Note ID. If provided, returns references whose "referent" value is this Note ID.
    :type referent: str, optional
    :param invitation: an Invitation ID. If provided, returns references whose "invitation" field is this Invitation ID.
    :type invitation: str, optional
    :param mintcdate: Represents an Epoch time timestamp in milliseconds. If provided, returns references whose "true creation date" (tcdate) is at least equal to the value of mintcdate.
    :type mintcdate: int, optional

    :return: Iterator over references filtered by the provided parameters
    :rtype: iterget
    """

    params = {}
    if referent is not None:
        params['referent'] = referent
    if invitation is not None:
        params['invitation'] = invitation
    if mintcdate is not None:
        params['mintcdate'] = mintcdate

    return iterget(client.get_references, **params)

def iterget_invitations(client, id=None, invitee=None, regex=None, tags=None, minduedate=None, duedate=None, pastdue=None, replytoNote=None, replyForum=None, signature=None, note=None, replyto=None, details=None, expired=None, super=None):
    """
    Returns an iterator over invitations, filtered by the provided parameters, ignoring API limit.

    :param client: Client used to get the Invitations
    :type client: Client
    :param id: an Invitation ID. If provided, returns invitations whose "id" value is this Invitation ID.
    :type id: str, optional
    :param invitee: Essentially, invitees field in an Invitation object contains Group Ids being invited using the invitation. If provided, returns invitations whose "invitee" field contains the given string.
    :type invitee: str, optional
    :param regex: a regular expression string to match Invitation IDs. If provided, returns invitations whose "id" value matches the given regex.
    :type regex: str, optional
    :param tags: If provided, returns Invitations whose Tags field contains the given Tag IDs.
    :type tags: list[str], optional
    :param minduedate: Represents an Epoch time timestamp in milliseconds. If provided, returns Invitations whose duedate is at least equal to the value of minduedate.
    :type minduedate: int, optional
    :param duedate: Represents an Epoch time timestamp in milliseconds. If provided, returns Invitations whose duedate field matches the given duedate.
    :type duedate: int, optional
    :param pastdue:
    :type pastdue: bool, optional
    :param replytoNote: a Note ID. If provided, returns Invitations whose replytoNote field contains the given Note ID.
    :type replytoNote: str, optional
    :param replyForum: a forum ID. If provided, returns Invitations whose forum field contains the given forum ID.
    :type replyForum: str, optional
    :param signature: a Group ID. If provided, returns Invitations whose signature field contains the given Group ID.
    :type signature: str, optional
    :param note: a Note ID. If provided, returns Invitations whose note field contains the given Note ID.
    :type note: str, optional
    :param replyto: a Note ID. If provided, returns Invitations whose replyto field matches the given Note ID.
    :type replyto: str, optional
    :param details:
    :type details: str, optional
    :param expired: get also expired invitions, by default returns 'active' invitations.
    :type expired: bool, optional

    :return: Iterator over Invitations filtered by the provided parameters
    :rtype: iterget
    """

    params = {}
    if id is not None:
        params['id'] = id
    if invitee is not None:
        params['invitee'] = invitee
    if regex is not None:
        params['regex'] = regex
    if tags is not None:
        params['tags'] = tags
    if minduedate is not None:
        params['minduedate'] = minduedate
    if duedate is not None:
        params['duedate'] = duedate
    if pastdue is not None:
        params['pastdue'] = pastdue
    if details is not None:
        params['details'] = details
    if replytoNote is not None:
        params['replytoNote'] = replytoNote
    if replyForum is not None:
        params['replyForum'] = replyForum
    if signature is not None:
        params['signature'] = signature
    if note is not None:
        params['note'] = note
    if replyto is not None:
        params['replyto'] = replyto
    if super is not None:
        params['super'] = super
    params['expired'] = expired

    return iterget(client.get_invitations, **params)

def iterget_groups(client, id = None, regex = None, member = None, host = None, signatory = None, web = None):
    """
    Returns an iterator over groups filtered by the provided parameters ignoring API limit.

    :param client: Client used to get the Groups
    :type client: Client
    :param id: a Note ID. If provided, returns groups whose "id" value is this Group ID.
    :type id: str, optional
    :param regex: a regular expression string to match Group IDs. If provided, returns groups whose "id" value matches the given regex.
    :type regex: str, optional
    :param member: Essentially, members field contains Group Ids that are members of this Group object. If provided, returns groups whose "members" field contains the given string.
    :type member: str, optional
    :param host:
    :type host: str, optional
    :param signatory: a Group ID. If provided, returns Groups whose signatory field contains the given Group ID.
    :type signatory: str, optional
    :param web: Groups that contain a web field value
    :type web: bool, optional

    :return: Iterator over Groups filtered by the provided parameters
    :rtype: iterget
    """

    params = {}
    if id is not None:
        params['id'] = id
    if regex is not None:
        params['regex'] = regex
    if member is not None:
        params['member'] = member
    if host is not None:
        params['host'] = host
    if signatory is not None:
        params['signatory'] = signatory
    if web is not None:
        params['web'] = web

    return iterget(client.get_groups, **params)

def next_individual_suffix(unassigned_individual_groups, individual_groups, individual_label):
    """
    Gets an individual group's suffix (e.g. AnonReviewer1). The suffix will be the next available empty group or will be the suffix of the largest indexed group +1

    :param unassigned_individual_groups: a list of individual groups with no members
    :type unassigned_individual_groups: list[Group]
    :param individual_groups: the full list of individual groups (groups with a single member: e.g. conference.org/Paper1/AnonReviewer1), empty or not
    :type individual_groups: list[Group]
    :param individual_label: the "label" of the group: e.g. "AnonReviewer"
    :type individual_label: str

    :return: An individual group's suffix (e.g. AnonReviewer1)
    :rtype: str
    """

    if len(unassigned_individual_groups) > 0:
        anonreviewer_group = unassigned_individual_groups[0]
        anonreviewer_suffix = anonreviewer_group.id.split('/')[-1]
        return anonreviewer_suffix
    elif len(individual_groups) > 0:
        anonreviewer_group_ids = [int(g.id.split(individual_label)[1]) for g in individual_groups]

        # reverse=True lets us get the AnonReviewer group with the highest index
        highest_anonreviewer_id = sorted(anonreviewer_group_ids, reverse=True)[0]

        return '{}{}'.format(individual_label, highest_anonreviewer_id+1)
    else:
        return '{}1'.format(individual_label)

def get_reviewer_groups(client, paper_number, conference, group_params, parent_label, individual_label):

    """
    This is only intended to be used as a local helper function for :func:`tools.add_assignment`

    :param client: Client used to get the Groups
    :type client: Client
    :param paper_number: the number of the paper to assign
    :type paper_number: int
    :param conference: the ID of the conference being assigned
    :type conference: str
    :param group_params: optional parameter that overrides the default
    :type group_params: dict
    :param parent_label: String assgined to identify the parent Group
    :type parent_label: str
    :param individual_label: String assigned to identify a individual Group
    :type individual_label: str

    :return: List containing the parent Group, list of individual groups, and list of unassigned individual groups
    :rtype: list[Group, list[Group], list[Group]]
    """

    # get the parent group if it already exists, and create it if it doesn't.
    try:
        parent_group = client.get_group('{}/Paper{}/{}'.format(conference, paper_number, parent_label))
    except openreview.OpenReviewException as e:
        if 'Group Not Found' in e.args[0].get('message'):
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

    """
    get the existing individual groups, while making sure that the parent group isn't included.
    This can happen if the parent group and the individual groups are named similarly.

    For example, if:
        parent_group_label = "Area_Chairs"
        individual_group_label = "Area_Chairs"

        Then the call for individual groups by wildcard will pick up all the
        individual groups AND the parent group.
    """

    individual_groups = client.get_groups(regex = '{}/Paper{}/{}[0-9]+$'.format(conference, paper_number, individual_label))
    individual_groups = [g for g in individual_groups if g.id != parent_group.id]
    unassigned_individual_groups = sorted([ a for a in individual_groups if a.members == [] ], key=lambda x: x.id)
    return [parent_group, individual_groups, unassigned_individual_groups]

def add_assignment(client, paper_number, conference, reviewer,
    parent_group_params = {},
    individual_group_params = {},
    parent_label = 'Reviewers',
    individual_label = 'AnonReviewer',
    use_profile = True):

    """
    Assigns a reviewer to a paper.
    Also adds the given user to the parent and individual groups defined by the paper number, conference, and labels
    "individual groups" are groups with a single member;
    e.g. conference.org/Paper1/AnonReviewer1
    "parent group" is the group that contains the individual groups;
    e.g. conference.org/Paper1/Reviewers

    :param client: Client used to add the assignment
    :type client: Client
    :param paper_number: the number of the paper to assign
    :type paper_number: int
    :param conference: the ID of the conference being assigned
    :type conference: str
    :param reviewer: may be an email address or a tilde ID that wants to be assigned to the paper
    :type reviewer: str
    :param parent_group_params: optional parameter that overrides the default
    :type parent_group_params: dict, optional
    :param individual_group_params: optional parameter that overrides the default
    :type individual_group_params: dict, optional
    :param parent_label: String used to identify the parent Group
    :type parent_label: str, optional
    :param individual_label: String assigned to identify an individual Group
    :type individual_label: str, optional
    :param use_profile: If true, retrieves the profile of the reviewer, otherwise, uses the passed reviewer
    :type use_profile: bool, optional

    :return: Tuple containing the passed reviewer in the zeroth position and a list of Group ids in the first position
    :rtype: tuple(str, list(str))
    """
    result = get_reviewer_groups(client, paper_number, conference, parent_group_params, parent_label, individual_label)
    parent_group = result[0]
    individual_groups = result[1]
    unassigned_individual_groups = result[2]

    """
    Adds the given user to the parent group, and to the next empty individual group.
    Prints the results to the console.
    """
    if use_profile:
        profile = get_profile(client, reviewer)
        user = profile.id if profile else reviewer
    else:
        user = reviewer

    affected_groups = set()
    client.add_members_to_group(parent_group, user)
    affected_groups.add(parent_group.id)

    assigned_individual_groups = [a for a in individual_groups if user in a.members]
    if not assigned_individual_groups:
        # assign reviewer to group
        suffix = next_individual_suffix(unassigned_individual_groups, individual_groups, individual_label)
        anonreviewer_id = '{}/Paper{}/{}'.format(conference, paper_number, suffix)
        paper_authors = '{}/Paper{}/Authors'.format(conference, paper_number)

        # Set the default values for the individual groups
        default_readers = [conference, '{}/Program_Chairs'.format(conference)]
        default_writers = [conference]
        default_signatures = [conference]
        default_nonreaders = []
        default_members = []
        default_signatories = []

        readers = individual_group_params.get('readers', default_readers)[:]
        readers.append(anonreviewer_id)

        nonreaders = individual_group_params.get('nonreaders', default_nonreaders)[:]
        nonreaders.append(paper_authors)

        writers = individual_group_params.get('writers', default_writers)[:]

        members = individual_group_params.get('members', default_members)[:]
        members.append(user)

        signatories = individual_group_params.get('signatories', default_signatories)[:]
        signatories.append(anonreviewer_id)

        signatures = individual_group_params.get('signatures', default_signatures)[:]

        individual_group = openreview.Group(
            id = anonreviewer_id,
            readers = readers,
            nonreaders = nonreaders,
            writers = writers,
            members = members,
            signatories = signatories,
            signatures = signatures)

        client.post_group(individual_group)
        affected_groups.add(individual_group.id)
    else:
        # user already assigned to individual group(s)
        for g in assigned_individual_groups:
            affected_groups.add(g.id)

    return (user,list(affected_groups))

def remove_assignment(client, paper_number, conference, reviewer,
    parent_group_params = {},
    parent_label = 'Reviewers',
    individual_label = 'AnonReviewer'):

    """
    |  Un-assigns a reviewer from a paper.
    |  Removes the given user from the parent group, and any assigned individual groups.

    |  "individual groups" are groups with a single member;
    |      e.g. conference.org/Paper1/AnonReviewer1
    |  "parent group" is the group that contains the individual groups;
    |      e.g. conference.org/Paper1/Reviewers

    :param client: Client used to remove the assignment
    :type client: Client
    :param paper_number: the number of the paper to assign
    :type paper_number: int
    :param conference: the ID of the conference being assigned
    :type conference: str
    :param reviewer: same as @reviewer_to_add, but removes the user
    :type reviewer: str
    :param parent_group_params: optional parameter that overrides the default
    :type parent_group_params: dict, optional
    :param parent_label: String used to identify the parent Group
    :type parent_label: str, optional
    :param individual_label: String assigned to identify an individual Group
    :type individual_label: str, optional
    :param use_profile: If true, retrieves the profile of the reviewer, otherwise, uses the passed reviewer
    :type use_profile: bool, optional

    :return: Tuple containing the passed reviewer in the zeroth position and a list of Group ids in the first position
    :rtype: tuple(str, list(str))
    """

    result = get_reviewer_groups(client, paper_number, conference, parent_group_params, parent_label, individual_label)
    parent_group = result[0]
    individual_groups = result[1]

    profile = get_profile(client, reviewer)
    user = profile.id if profile else reviewer

    """
    Removes the given user from the parent group,
        and any assigned individual groups.
    """

    #TODO: Need to refactor this function's code

    user_groups = [g.id for g in client.get_groups(member=user)]
    user_groups.append(user)
    if ('@' in reviewer) and (reviewer not in user_groups):
        user_groups.append(reviewer)

    affected_groups = set()

    for user_entity in user_groups:
        if user_entity in parent_group.members:
            client.remove_members_from_group(parent_group, user_entity)
        affected_groups.add(parent_group.id)

        assigned_individual_groups = [a for a in individual_groups if user_entity in a.members]
        for individual_group in assigned_individual_groups:
            affected_groups.add(individual_group.id)
            client.remove_members_from_group(individual_group, user_entity)
    return (user, list(affected_groups))

@deprecated(version='0.9.5')
def assign(client, paper_number, conference,
    parent_group_params = {},
    individual_group_params = {},
    reviewer_to_add = None,
    reviewer_to_remove = None,
    parent_label = 'Reviewers',
    individual_label = 'AnonReviewer',
    use_profile = True):

    """

    Either assigns or unassigns a reviewer to a paper.
    TODO: Is this function really necessary?

    "individual groups" are groups with a single member;
    e.g. conference.org/Paper1/AnonReviewer1
    "parent group" is the group that contains the individual groups;
    e.g. conference.org/Paper1/Reviewers

    :param client: Client used to assign or unassign a reviewer to a paper
    :type client: Client
    :param paper_number: the number of the paper to assign
    :type paper_number: int
    :param conference: the ID of the conference being assigned
    :type conference: str
    :param parent_group_params: optional parameter that overrides the default
    :type parent_group_params: dict, optional
    :param individual_group_params: optional parameter that overrides the default
    :type individual_group_params: dict, optional
    :param reviewer_to_add: may be an email address or a tilde ID; adds the given user to the parent and individual groups defined by the paper number, conference, and labels
    :type reviewer_to_add: str, optional
    :param reviewer_to_remove: same as @reviewer_to_add, but removes the user
    :type reviewer_to_remove: str, optional
    :param parent_label: String used to identify the parent Group
    :type parent_label: str, optional
    :param individual_label: String assigned to identify an individual Group
    :type individual_label: str, optional
    :param use_profile: If true, retrieves the profile of the reviewer, otherwise, uses the passed reviewer
    :type use_profile: bool, optional

    :return: Tuple containing the passed reviewer in the zeroth position and a list of Group ids in the first position
    :rtype: tuple(str, list(str))

    It's important to remove any users first, so that we can do direct replacement of one user with another.

    For example: passing in a reviewer to remove AND a reviewer to add should replace the first user with the second.
    """
    changed_groups = []
    user = ""

    if reviewer_to_remove:
        user, changed_groups = remove_assignment(client, paper_number, conference, reviewer_to_remove,
                          parent_group_params, parent_label, individual_label)

    if reviewer_to_add:
        user, changed_groups = add_assignment(client, paper_number, conference, reviewer_to_add,
                        parent_group_params,
                        individual_group_params,
                        parent_label,
                        individual_label,
                        use_profile = use_profile)

    return (user, changed_groups)

def timestamp_GMT(year, month, day, hour=0, minute=0, second=0):
    """
    Given year, month, day, and (optionally) hour, minute, second in GMT time zone:
    returns the number of milliseconds between this date and Epoch Time (Jan 1, 1970).

    :param year: year >= 1970
    :type year: int
    :param month: value from 1 to 12
    :type month: int
    :param day: value from 1 to 28, 29, 30, or 31; depending on the month value.
    :type day: int
    :param hour: value from 0 to 23
    :type hour: int, optional
    :param minute: value from 0 to 59
    :type minute: int, optional
    :param second: value from 0 to 59
    :type second: int, optional

    :return: Number of milliseconds between the passed date and Epoch Time (Jan 1, 1970)
    :rtype: int

    >>> timestamp_GMT(1990, 12, 20, hour=12, minute=30, second=24)
    661696224000

    """
    return datetime_millis(datetime.datetime(year, month, day, hour, minute, second))

def datetime_millis(dt):
    """
    Converts a datetime to milliseconds.

    :param dt: A date that want to be converted to milliseconds
    :type dt: datetime

    :return: The time from Jan 1, 1970 to the passed date in milliseconds
    :rtype: int
    """
    if isinstance(dt, datetime.datetime):
        epoch = datetime.datetime.utcfromtimestamp(0)
        return int((dt - epoch).total_seconds() * 1000)

    return dt

def recruit_reviewer(client, user, first,
    hash_seed,
    recruit_reviewers_id,
    recruit_message,
    recruit_message_subj,
    reviewers_invited_id,
    contact_info='info@openreview.net',
    verbose=True,
    replyTo=None):
    """
    Recruit a reviewer. Sends an email to the reviewer with a link to accept or
    reject the recruitment invitation.

    :param client: Client used to send the e-mail
    :type client: Client
    :param user: User to whom the e-mail will be sent
    :type user: str
    :param first: First name of the person to whom e-mail will be sent
    :type first: str
    :param hash_seed: a random number for seeding the hash.
    :type hash_seed: int
    :param recruit_message: a formattable string containing the following string variables: (name, accept_url, decline_url)
    :type recruit_message: str
    :param recruit_message_subj: subject line for the recruitment email
    :type recruit_message_subj: str
    :param reviewers_invited_id: group ID for the "Reviewers Invited" group, often used to keep track of which reviewers have already been emailed. str
    :type reviewers_invited_id: str
    :param contact_info: The information used to contact support for questions
    :type contact_info: str
    :param verbose: Shows response of :meth:`openreview.Client.post_message` and shows the body of the message sent
    :type verbose: bool, optional
    :param baseurl: Use this baseUrl instead of client.baseurl to create recruitment links
    :type baseurl: str, optional
    """

    # the HMAC.new() function only accepts bytestrings, not unicode.
    # In Python 3, all strings are treated as unicode by default, so we must call encode on
    # these unicode strings to convert them to bytestrings. This behavior is the same in
    # Python 2, because we imported unicode_literals from __future__.
    hashkey = HMAC.new(hash_seed.encode('utf-8'), msg=user.encode('utf-8'), digestmod=SHA256).hexdigest()
    baseurl = 'https://openreview.net' #Always pointing to the live site so we don't send more invitations with localhost

    # build the URL to send in the message
    url = '{baseurl}/invitation?id={recruitment_inv}&user={user}&key={hashkey}&response='.format(
        baseurl = baseurl if baseurl else client.baseurl,
        recruitment_inv = recruit_reviewers_id,
        user = urlparse.quote(user),
        hashkey = hashkey
    )

    # format the message defined above
    personalized_message = recruit_message.format(
        name = first,
        accept_url = url + "Yes",
        decline_url = url + "No",
        contact_info = contact_info
    )

    client.add_members_to_group(reviewers_invited_id, [user])

    # send the email through openreview
    response = client.post_message(recruit_message_subj, [user], personalized_message, parentGroup=reviewers_invited_id, replyTo=replyTo)

    if verbose:
        print("Sent to the following: ", response)
        print(personalized_message)

def post_submission_groups(client, conference_id, submission_invite, chairs):
    """
    Create paper group, authors group, reviewers group, review non-readers group
    for all notes returned by the submission_invite.

    :param client: client that will post the Groups
    :type client: Client
    :param conference_id: Conference which the Groups belong to
    :type conference_id: str
    :param submission_invite: Invitation id to get all the Notes that are paper submissions
    :type submission_invite: str
    :param chairs: Chairs of the conference
    :type chairs: str
    """
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
    """
    Returns a list of invitation ids visible to the client according to the value of parameter "open_only".

    :param client: Client used to get the Invitations
    :type client: Client
    :param open_only: If True, the results will be invitations having a future due date.
    :type open_only: bool, optional

    :return: List of Invitation ids
    :rtype: list[str]

    Example Usage:

    >>> get_submission_invitations(c,True)
    [u'machineintelligence.cc/MIC/2018/Conference/-/Submission', u'machineintelligence.cc/MIC/2018/Abstract/-/Submission', u'ISMIR.net/2018/WoRMS/-/Submission', u'OpenReview.net/Anonymous_Preprint/-/Submission']
    """

    #Calculate the epoch for current timestamp
    now = int(time.time()*1000)
    duedate = now if open_only==True else None
    invitations = client.get_invitations(regex='.*/-/.*[sS]ubmission.*',minduedate=duedate)

    # For each group in the list, append the invitation id to a list
    invitation_ids = [inv.id for inv in invitations]

    return invitation_ids

def get_all_venues(client):
    """
    Returns a list of all the venues

    :param client: Client used to get all the venues
    :type client: Client

    :return: List of all the venues represented by a their corresponding Group id
    :rtype: list[str]
    """
    return client.get_group("host").members

def _fill_str(template_str, paper):
    """
    Fills a "template string" with the corresponding values from an openreview.Note object.
    """
    paper_params = paper.to_json()
    pattern = '|'.join(['<{}>'.format(field) for field, value in paper_params.items()])
    matches = re.findall(pattern, template_str)
    for match in matches:
        discovered_field = re.sub('<|>', '', match)
        template_str = template_str.replace(match, str(paper_params[discovered_field]))
    return template_str

def _fill_str_or_list(template_str_or_list, paper):
    """
    Fills a "template string", or a list of template strings, with the corresponding values
    from an openreview.Note object.
    """
    if type(template_str_or_list) == list:
        return [_fill_str(v, paper) for v in template_str_or_list]
    elif type(template_str_or_list) == str:
        return _fill_str(template_str_or_list, paper)
    elif any([type(template_str_or_list) == t for t in [int, float, type(None), bool]]):
        return template_str_or_list
    else:
        raise ValueError('first argument must be list or string: ', template_str_or_list)

def fill_template(template, paper):
    """
    Fills an openreview "template" with the corresponding values from an :class:`~openreview.Note` object.
    Templates are dicts that match the schema of any OpenReview object class .

    Example:

    >>> group_template = {
        'id': 'Conf.org/2019/Paper<number>',
        'members': ['Conf.org/2019/Paper<number>/Reviewers']
    }

    :param template: a dict that matches the schema of an OpenReview :class:`~openreview.Group` or :class:`~openreview.Invitation` with any number of wildcards in the form of "<attr>" where "attr" is an attribute in the :class:`~openreview.Note` class.
    :type template: dict
    :param paper: an instance of :class:`~openreview.Note` class, to fill the template values.
    :type paper: Note

    :return: The openreview "template" with the corresponding values from the paper passed as parameter
    :rtype: dict
    """
    new_template = {}
    for field, value in template.items():
        if type(value) != dict:
            new_template[field] = _fill_str_or_list(value, paper)
        else:
            # recursion
            new_template[field] = fill_template(value, paper)

    return new_template

def get_conflicts(author_profiles, user_profile, policy='default', n_years=5):
    """
    Finds conflicts between the passed user Profile and the author Profiles passed as arguments

    :param author_profiles: List of Profiles for which an association is to be found
    :type author_profiles: list[Profile]
    :param user_profile: Profile for which the conflicts will be found
    :type user_profile: Profile

    :return: List containing all the conflicts between the user Profile and the author Profiles
    :rtype: list[str]
    """
    author_domains = set()
    author_emails = set()
    author_relations = set()
    author_publications = set()
    info_function = get_neurips_profile_info if policy == 'neurips' else get_profile_info

    for profile in author_profiles:
        author_info = info_function(profile, n_years)
        author_domains.update(author_info['domains'])
        author_emails.update(author_info['emails'])
        author_relations.update(author_info['relations'])
        author_publications.update(author_info['publications'])

    user_info = info_function(user_profile, n_years)

    conflicts = set()
    conflicts.update(author_domains.intersection(user_info['domains']))
    conflicts.update(author_relations.intersection(user_info['emails']))
    conflicts.update(author_emails.intersection(user_info['relations']))
    conflicts.update(author_emails.intersection(user_info['emails']))
    conflicts.update(author_publications.intersection(user_info['publications']))

    return list(conflicts)

def get_profile_info(profile, n_years=3):
    """
    Gets all the domains, emails, relations associated with a Profile

    :param profile: Profile from which all the relations will be obtained
    :type profile: Profile

    :return: Dictionary with the domains, emails, and relations associated with the passed Profile
    :rtype: dict
    """
    domains = set()
    emails = set()
    relations = set()
    publications = set()
    common_domains = ['gmail.com', 'qq.com', '126.com', '163.com',
                      'outlook.com', 'hotmail.com', 'yahoo.com', 'foxmail.com', 'aol.com', 'msn.com', 'ymail.com', 'googlemail.com', 'live.com']

    ## Emails section
    for email in profile.content['emails']:
        if email.startswith("****@"):
            raise openreview.OpenReviewException("You do not have the required permissions as some emails are obfuscated. Please login with the correct account or contact support.")
        domains.update(openreview.tools.subdomains(email))
        emails.add(email)

    ## Institution section
    for h in profile.content.get('history', []):
        domain = h.get('institution', {}).get('domain', '')
        domains.update(openreview.tools.subdomains(domain))

    ## Relations section
    relations.update([r['email'] for r in profile.content.get('relations', [])])

    ## TODO:: Parameterize the number of years for publications to consider from
    ## Publications section: get publications within last n years, default is all publications from previous years
    for pub in profile.content.get('publications', []):
        publications.add(pub.id)

    ## Filter common domains
    for common_domain in common_domains:
        if common_domain in domains:
            domains.remove(common_domain)

    return {
        'id': profile.id,
        'domains': domains,
        'emails': emails,
        'relations': relations,
        'publications': publications
    }

def get_neurips_profile_info(profile, n_years=3):

    domains = set()
    emails=set()
    relations = set()
    publications = set()
    common_domains = ['gmail.com', 'qq.com', '126.com', '163.com',
                      'outlook.com', 'hotmail.com', 'yahoo.com', 'foxmail.com', 'aol.com', 'msn.com', 'ymail.com', 'googlemail.com', 'live.com']
    curr_year = datetime.datetime.now().year
    cut_off_year = curr_year - n_years - 1

    ## Institution section, get history within the last n years
    for h in profile.content.get('history', []):
        if h.get('end') is None or int(h.get('end')) > cut_off_year:
            domain = h.get('institution', {}).get('domain', '')
            domains.update(openreview.tools.subdomains(domain))

    ## Relations section, get coauthor/coworker relations within the last n years + all the other relations
    for r in profile.content.get('relations', []):
        if r.get('relation', '') in ['Coauthor','Coworker']:
            if r.get('end') is None or int(r.get('end')) > cut_off_year:
                relations.add(r['email'])
        else:
            relations.add(r['email'])

    ## Emails section
    for email in profile.content['emails']:
        if email.startswith("****@"):
            raise openreview.OpenReviewException("You do not have the required permissions as some emails are obfuscated. Please login with the correct account or contact support.")
        emails.add(email)

    ## if institution section is empty, add email domains
    if not domains:
        for email in profile.content['emails']:
            domains.update(openreview.tools.subdomains(email))

    ## Publications section: get publications within last n years
    for pub in profile.content.get('publications', []):
        year = None
        if 'year' in pub.content and isinstance(pub.content['year'], str):
            try:
                converted_year = int(pub.content['year'])
                if converted_year <= curr_year:
                    year = converted_year
            except Exception as e:
                year = None
        if not year:
            timtestamp = pub.cdate if pub.cdate else pub.tcdate
            year = int(datetime.datetime.fromtimestamp(timtestamp/1000).year)
        if year > cut_off_year:
            publications.add(pub.id)

    ## Filter common domains
    for common_domain in common_domains:
        if common_domain in domains:
            domains.remove(common_domain)

    return {
        'id': profile.id,
        'domains': domains,
        'emails': emails,
        'relations': relations,
        'publications': publications
    }



def post_bulk_edges (client, edges, batch_size = 50000):
    num_edges = len(edges)
    result = []
    for i in tqdm(range(0, num_edges, batch_size), total=(num_edges // batch_size + 1)):
        end = min(i + batch_size, num_edges)
        batch = client.post_edges(edges[i:end])
        result += batch
    return result

def overwrite_pdf(client, note_id, file_path):
    """
    Overwrite all the references of a note with the new pdf file.
    If the note has an original note then update original references
    """
    note = client.get_note(id=note_id)
    original_note = note

    if note.original:
        original_note = client.get_note(id=note.original)

    references = client.get_references(referent=original_note.id)

    updated_references = []

    if references:
        pdf_url = client.put_pdf(file_path)

        for reference in references:
            if 'pdf' in reference.content:
                reference.content['pdf'] = pdf_url
                updated_references.append(client.post_note(reference))

    return updated_references

def pretty_id(group_id):

    if not group_id:
        return ''

    if group_id.startswith('~') and len(group_id):
        return re.sub('[0-9]+', '', group_id.replace('~', '').replace('_', ' '))

    if group_id in ['everyone', '(anonymous)', '(guest)', '~']:
        return group_id

    tokens = group_id.split('/')

    transformed_tokens = []

    for token in tokens:
        transformed_token=re.sub('\..+', '', token).replace('-', '').replace('_', ' ')
        letters_only=re.sub('\d|\W', '', transformed_token)

        if letters_only != transformed_token.lower():
            transformed_tokens.append(transformed_token)


    return ' '.join(transformed_tokens)

def export_committee(client, committee_id, file_name):
    members=client.get_group(committee_id).members
    profiles=get_profiles(client, members)
    with open(file_name, 'w') as outfile:
        csvwriter = csv.writer(outfile, delimiter=',')
        for profile in tqdm(profiles):
            s = csvwriter.writerow([profile.get_preferred_email(), profile.get_preferred_name(pretty=True)])
