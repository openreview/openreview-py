#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import inspect

import json
import os

import openreview
import re
import datetime
import csv
from pylatexenc.latexencode import utf8tolatex, unicode_to_latex, UnicodeToLatexConversionRule, UnicodeToLatexEncoder, RULE_REGEX
from Crypto.Hash import HMAC, SHA256
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import tld
import urllib.parse as urlparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

def decision_to_venue(venue_id, decision_option, accept_options=None):
    """
    Returns the venue for a submission based on its decision

    :param venue_id: venue's short name (i.e., ICLR 2022)
    :type venue_id: string
    :param decision_option: paper decision (i.e., Accept, Reject)
    :type decision_option: string
    :param accept_options: accept decisions (i.e., [ Accept (Best Paper), Invite to Archive ])
    :type accept_options: list
    """
    venue = venue_id
    if is_accept_decision(decision_option, accept_options):
        decision = decision_option.replace('Accept', '') if 'Accept' in decision_option else decision_option
        decision = re.sub(r'[()\W]+', '', decision)
        if decision: 
            venue += ' ' + decision.strip()
    else:
        venue = f'Submitted to {venue}'
    return venue

def is_accept_decision(decision, accept_options=None):
    """
    Checks if decision is an accept decision

    :param decision: paper decision (i.e., Accept, Reject)
    :type decision: string
    :param accept_options: accept decisions (i.e., [ Accept (Best Paper), Invite to Archive ])
    :type accept_options: list
    """
    if (accept_options and decision in accept_options) or (not accept_options and 'Accept' in decision):
        return True
    return False

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

def format_params(params):
    if isinstance(params, dict):
        formatted_params = {}
        for key, value in params.items():
            formatted_params[key] = format_params(value)
        return formatted_params

    if isinstance(params, list):
        formatted_params = []
        for value in params:
            formatted_params.append(format_params(value))
        return formatted_params

    if isinstance(params, bool):
        return json.dumps(params)

    return params

def concurrent_requests(request_func, params, desc='Gathering Responses'):
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
    max_workers = cpu_count() - 1
    futures = []
    gathering_responses = tqdm(total=len(params), desc=desc)
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


def get_profiles(client, ids_or_emails, with_publications=False, with_relations=False, with_preferred_emails=None, as_dict=False):
    '''
    Helper function that repeatedly queries for profiles, given IDs and emails.
    Useful for getting more Profiles than the server will return by default (1000)

    :param with_preferred_emails: invitation id to get the edges where the preferred emails are stored
    :type with_preferred_emails: str
    '''
    ids = []
    emails = []
    for member in ids_or_emails:
        if '~' in member:
            ids.append(member)
        else:
            emails.append(member)

    profile_by_id = {}
    profile_by_id_or_email = {}

    def process_profile(profile, email=None):
        profile_by_id[profile.id] = profile
        for name in profile.content.get("names", []):
            if name.get("username"):
                profile_by_id_or_email[name.get("username")] = profile
        if email:
            profile_by_id_or_email[email] = profile        

    batch_size = 1000
    ## Get profiles by id and add them to the profiles list
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_profiles = client.search_profiles(ids=batch_ids)
        for profile in batch_profiles:
            process_profile(profile)

    ## Get profiles by email and add them to the profiles list
    for j in range(0, len(emails), batch_size):
        batch_emails = emails[j:j+batch_size]
        batch_profile_by_email = client.search_profiles(confirmedEmails=batch_emails)
        for email, profile in batch_profile_by_email.items():
            process_profile(profile, email)            

    for email in emails:
        if email not in profile_by_id_or_email:
            profile = openreview.Profile(
                id=email,
                content={
                    'emails': [email],
                    'preferredEmail': email,
                    'emailsConfirmed': [email],
                    'names': []
                })
            profile_by_id[profile.id] = profile
            profile_by_id_or_email[email] = profile
 

    ## Get publications for all the profiles
    profiles = list(profile_by_id.values())
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

        notes_v1 = concurrent_requests(lambda profile : client_v1.get_all_notes(content={'authorids': profile.id}), profiles, desc='Loading API v1 publications')
        for idx, publications in enumerate(notes_v1):
            profiles[idx].content['publications'] = publications

        notes_v2 = concurrent_requests(lambda profile : client_v2.get_all_notes(content={'authorids': profile.id}), profiles, desc='Loading API v2 publications')
        for idx, publications in enumerate(notes_v2):
            if profiles[idx].content.get('publications'):
                profiles[idx].content['publications'] = profiles[idx].content['publications'] +  publications
            else:
                profiles[idx].content['publications'] = publications

    if with_relations:

        relation_profile_ids = set()
        for profile in profiles:
            relation_usernames = [relation.get('username') for relation in profile.content.get('relations', []) if relation.get('username')]
            relation_emails = [relation.get('email') for relation in profile.content.get('relations', []) if relation.get('email')]
            relation_profile_ids.update(relation_usernames)
            relation_profile_ids.update(relation_emails)

        relation_profiles_by_id = get_profiles(client, list(relation_profile_ids), as_dict=True)

        for profile in profiles:
            for relation in profile.content.get('relations', []):
                relation_profile = relation_profiles_by_id.get(relation.get('username')) or relation_profiles_by_id.get(relation.get('email'))
                if relation_profile:
                    relation['profile_id'] = relation_profile.id

    if with_preferred_emails is not None:

        preferred_email_by_id = { g['id']['head']: g['values'][0]['tail'] for g in client.get_grouped_edges(invitation=with_preferred_emails, groupby='head', select='tail')}

        for profile in profiles:
            preferred_email = preferred_email_by_id.get(profile.id)
            if preferred_email:
                profile.content['preferredEmail'] = preferred_email
    
    if as_dict:
        profiles_as_dict = {}
        for id in ids:
            profiles_as_dict[id] = profile_by_id_or_email.get(id)

        for email in emails:
            profiles_as_dict[email] = profile_by_id_or_email.get(email)

        return profiles_as_dict

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

def get_note(client, id):
    """
    Get a single Note by id if available

    :param client: User that will retrieve the note
    :type client: Client
    :param id: id of the note
    :type id: str

    :return: Note that matches the passed id
    :rtype: Note
    """
    note = None
    try:
        note = client.get_note(id = id)
    except openreview.OpenReviewException as e:
        # throw an error if it is something other than "not found"
        error =  e.args[0]
        if error.get('name') == 'NotFoundError' or error.get('message').startswith('Note Not Found'):
            return None
        else:
            raise e
    return note

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

def create_profile(client, email, fullname, url='http://no_url', allow_duplicates=False):

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
    :param url: Homepage url
    :type url: str, optional
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

        username_response = client.get_tildeusername(fullname)

        # the username in each response will end with 1
        # if profiles don't exist for those names
        username_unclaimed = username_response['username'].endswith('1')

        if username_unclaimed:
            profile_exists = False
        else:
            profile_exists = True

        tilde_id = username_response['username']
        if (not profile_exists) or allow_duplicates:

            tilde_group = openreview.Group(id=tilde_id, signatures=[client.profile.id], signatories=[tilde_id], readers=[tilde_id], writers=[client.profile.id], members=[email])
            email_group = openreview.Group(id=email, signatures=[client.profile.id], signatories=[email], readers=[email], writers=[client.profile.id], members=[tilde_id])
            profile_content = {
                'emails': [email],
                'preferredEmail': email,
                'names': [
                    {
                        'fullname': fullname,
                        'username': tilde_id
                    }
                ],
                'homepage': url
            }
            client.post_group(tilde_group)
            client.post_group(email_group)

            profile = client.post_profile(openreview.Profile(id=tilde_id, content=profile_content, signatures=[tilde_id]))

            return profile

        else:
            raise openreview.OpenReviewException(
                'Failed to create new profile {tilde_id}: There is already a profile with the name: \"{fullname}\"'.format(
                    fullname=fullname, tilde_id=tilde_id))
    else:
        raise openreview.OpenReviewException('There is already a profile with this email address: {}'.format(email))

def create_authorid_profiles(client, note, print=print):
    # for all submissions get authorids, if in form of email address, try to find associated profile
    # if profile doesn't exist, create one
    created_profiles = []

    if 'authorids' in note.content and 'authors' in note.content:
        author_names = [a.replace('*', '') for a in note.content['authors']]
        author_emails = [e for e in note.content['authorids']]
        if len(author_names) == len(author_emails):
            # iterate through authorids and authors at the same time
            for (author_id, author_name) in zip(author_emails, author_names):
                author_id = author_id.strip()
                author_name = author_name.strip()

                if '@' in author_id:
                    try:
                        profile = create_profile(client=client, email=author_id, fullname=author_name)
                        created_profiles.append(profile)
                        print('{}: profile created with id {}'.format(note.id, profile.id))
                    except openreview.OpenReviewException as e:
                        print('Error while creating profile for note id {note_id}, author {author_id}, '.format(note_id=note.id, author_id=author_id), e)
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
        return primary_preferred_name['fullname'].split(' ')[-1]    

    return primary_preferred_name['fullname']

def generate_bibtex(note, venue_fullname, year, url_forum=None, paper_status='under review', anonymous=True, names_reversed=False, baseurl='https://openreview.net', editor=None):
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
    :param paper_status: Used to indicate the status of a paper: ["accepted", "rejected" or "under review"]
    :type paper_status: string, optional
    :param anonymous: Used to indicate whether or not the paper's authors should be revealed
    :type anonymous: bool, optional
    :param names_reversed: If true, it indicates that the last name is written before the first name
    :type names_reversed: bool, optional
    :param baseurl: Base url where the bibtex is from. Default https://openreview.net
    :type baseurl: str, optional

    :return: Note bibtex
    :rtype: str
    """

    note_title = note.content['title'] if isinstance(note.content['title'], str) else note.content['title']['value']

    first_word = re.sub('[^a-zA-Z]', '', note_title.split(' ')[0].lower())

    forum = note.forum if not url_forum else url_forum

    if anonymous:
        first_author_last_name = 'anonymous'
        authors = 'Anonymous'
    else:
        note_author_list = note.content['authors'] if isinstance(note.content['authors'], list) else note.content['authors']['value']
        first_author_last_name = note_author_list[0].split(' ')[-1].lower()
        if names_reversed:
            # last, first
            author_list = []
            for name in note_author_list:
                last = name.split(' ')[-1]
                rest = (' ').join(name.split(' ')[:-1])
                author_list.append(last+', '+rest)
            authors = ' and '.join(author_list)
        else:
            authors = ' and '.join(note_author_list)

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
    bibtex_title = u.unicode_to_latex(note_title)

    if paper_status == 'under review':

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
        return '\n'.join(under_review_bibtex)
    
    if paper_status == 'accepted':

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
        return '\n'.join(accepted_bibtex)

    if paper_status == 'rejected':

        rejected_bibtex = [
            '@misc{',
            utf8tolatex(first_author_last_name + year + first_word + ','),
            'title={' + bibtex_title + '},',
            'author={' + utf8tolatex(authors) + '},',
            'year={' + year + '},',
            'url={'+baseurl+'/forum?id=' + forum + '}',
            '}'
        ]
        return '\n'.join(rejected_bibtex)

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
    domain_components = [c for c in domain.split('.') if c and not c.isspace()]
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
    updated_members = []
    without_profile_ids = []

    member_profiles = get_profiles(client, group.members, as_dict=True)

    for member in group.members:
        profile = member_profiles.get(member)
        if profile is not None:
            updated_members.append(profile.id)
        elif member.startswith('~'):
            without_profile_ids.append(member)
        else:
            updated_members.append(member)

    if without_profile_ids:
        raise openreview.OpenReviewException(f"Profile Not Found for {without_profile_ids}")
    group.members = updated_members

    if getattr(client, 'post_group', None):
        return client.post_group(group)

    if getattr(client, 'post_group_edit', None):
        client.post_group_edit(
            invitation = group.domain + '/-/Edit',
            readers = [group.domain],
            writers = [group.domain],
            signatures = [group.domain],
            group = openreview.api.Group(
                id = group.id, 
                members = list(set(group.members))
            )
        )
        return client.get_group(group.id)

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

    if (params.get('limit') or float('inf')) <= client.limit:
        docs = get_function(**params)
        return docs
    else:
        get_count_params = params.copy()
        if get_count_params.get('offset') is not None:
            get_count_params.pop('offset')
        get_count_params['with_count'] = True
        get_count_params['limit'] = 1
        _, count = get_function(**get_count_params)

    params['with_count'] = False

    limit = params.get('limit')
    if (limit or client.limit) > client.limit:
        params.pop('limit')
    docs = get_function(**params)

    offset = params.get('offset') or 0

    if (count - offset) <= client.limit:
        return docs

    start = offset + client.limit

    if limit is None:
        end = count
    else:
        end = min(offset + limit, count)

    offset_list = list(range(start, end, client.limit))

    futures = []
    gathering_responses = tqdm(total=len(offset_list), desc='Gathering Responses')

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for count, offset in enumerate(offset_list):
            params['offset'] = offset
            if (count + 1) == len(offset_list) and (end - offset) > 0:
                params['limit'] = end - offset
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

class efficient_iterget:
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
    def __init__(self, get_function, desc='Gathering Responses', **params):
        self.obj_index = 0

        self.params = params
        self.params.update({
            'with_count': True,
            'sort': params.get('sort') or 'id',
            'limit': params.get('limit') or 1000
        })

        self.get_function = get_function
        self.current_batch, total = self.get_function(**self.params)

        self.gathering_responses = tqdm(total=total, desc=desc) if total > self.params['limit'] else None

    def update_batch(self):
        after = self.current_batch[-1].id
        self.params['after'] = after
        self.params['with_count'] = False
        next_batch = self.get_function(**self.params)
        if next_batch:
            self.current_batch = next_batch
        else:
            self.current_batch = []

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.current_batch) == 0:
            if self.gathering_responses:
                self.gathering_responses.close()
            raise StopIteration
        else:
            next_obj = self.current_batch[self.obj_index]
            if (self.obj_index + 1) == len(self.current_batch):
                self.update_batch()
                self.obj_index = 0
            else:
                if self.gathering_responses:
                    self.gathering_responses.update(1)
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
                   limit = None, 
                   trash = None):
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
    if trash == True:
        params['trash']=True
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

    return efficient_iterget(client.get_notes, desc='Getting Notes', **params)

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

def iterget_invitations(client, id=None, ids=None, invitee=None, regex=None, tags=None, minduedate=None, duedate=None, pastdue=None, replytoNote=None, replyForum=None, signature=None, note=None, replyto=None, details=None, expired=None, super=None, sort=None):
    """
    Returns an iterator over invitations, filtered by the provided parameters, ignoring API limit.

    :param client: Client used to get the Invitations
    :type client: Client
    :param id: an Invitation ID. If provided, returns invitations whose "id" value is this Invitation ID.
    :type id: str, optional
    :param ids: Comma separated Invitation IDs. If provided, returns invitations whose "id" value is any of the passed Invitation IDs.
    :type ids: str, optional
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
    if ids is not None:
        params['ids'] = ids
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
    if expired is not None:
        params['expired'] = expired
    if sort is not None:
        params['sort'] = sort


    return efficient_iterget(client.get_invitations, desc='Getting Invitations', **params)

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

    return efficient_iterget(client.get_groups, desc='Getting Groups', **params)

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
    replyTo=None,
    invitation=None,
    signature=None):
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
    url = '{baseurl}/invitation?id={recruitment_inv}&user={user}&key={hashkey}'.format(
        baseurl = baseurl if baseurl else client.baseurl,
        recruitment_inv = recruit_reviewers_id,
        user = urlparse.quote(user),
        hashkey = hashkey
    )

    # format the message defined above
    personalized_message = recruit_message.replace("{{fullname}}", first) if first else recruit_message
    personalized_message = personalized_message.replace("{{accept_url}}", url + "&response=Yes")
    personalized_message = personalized_message.replace("{{decline_url}}", url + "&response=No")
    personalized_message = personalized_message.replace("{{invitation_url}}", url)
    personalized_message = personalized_message.replace("{{contact_info}}", contact_info)

    personalized_message.format()

    try:
        client.add_members_to_group(reviewers_invited_id, [user])
    except openreview.OpenReviewException as e:
        raise e

    # send the email through openreview
    if invitation is not None:
        response = client.post_message(recruit_message_subj, [user], personalized_message, parentGroup=reviewers_invited_id, replyTo=replyTo, invitation=invitation, signature=signature)
    else:
        response = client.post_message(recruit_message_subj, [user], personalized_message, parentGroup=reviewers_invited_id, replyTo=replyTo)

    if verbose:
        print("Sent to the following: ", response)
        print(personalized_message)

def recruit_user(client, user,
    hash_seed,
    recruitment_message_subject,
    recruitment_message_content,
    recruitment_invitation_id,
    comittee_invited_id,
    contact_email,
    message_invitation,
    message_signature,
    name=None):

    hashkey = HMAC.new(hash_seed.encode('utf-8'), msg=user.encode('utf-8'), digestmod=SHA256).hexdigest()

    url = f'https://openreview.net/invitation?id={recruitment_invitation_id}&user={urlparse.quote(user)}&key={hashkey}'

    personalized_message = recruitment_message_content.replace("{{fullname}}", name) if name else recruitment_message_content
    personalized_message = personalized_message.replace("{{invitation_url}}", url)
    personalized_message = personalized_message.replace("{{contact_info}}", contact_email)

    personalized_message.format()

    client.post_message(recruitment_message_subject, [user], personalized_message, parentGroup=comittee_invited_id, replyTo=contact_email, invitation=message_invitation, signature=message_signature)


def get_all_venues(client):
    """
    Returns a list of all the venues

    :param client: Client used to get all the venues
    :type client: Client

    :return: List of all the venues represented by a their corresponding Group id
    :rtype: list[str]
    """
    return client.get_group("host").members

def info_function_builder(policy_function):
    def inner(profile, n_years=None, submission_venueid=None):
        common_domains = ['gmail.com', 'qq.com', '126.com', '163.com',
                    'outlook.com', 'hotmail.com', 'yahoo.com', 'foxmail.com', 'aol.com', 'msn.com', 'ymail.com', 'googlemail.com', 'live.com']
        argspec = inspect.getfullargspec(policy_function)
        if 'submission_venueid' in argspec.args:
            result = policy_function(profile, n_years, submission_venueid)
        else:
            result = policy_function(profile, n_years)
        domains = set()
        subdomains_dict = {}
        for domain in result['domains']:
            if domain not in subdomains_dict:
                subdomains = openreview.tools.subdomains(domain)
                subdomains_dict[domain] = subdomains
            domains.update(subdomains_dict[domain])

        # Filter common domains
        for common_domain in common_domains:
            domains.discard(common_domain)

        result['domains'] = list(domains)
        return result
    return inner

def get_conflicts(author_profiles, user_profile, policy='default', n_years=None):
    """
    Finds conflicts between the passed user Profile and the author Profiles passed as arguments

    :param author_profiles: List of Profiles for which an association is to be found
    :type author_profiles: list[Profile]
    :param user_profile: Profile for which the conflicts will be found
    :type user_profile: Profile
    :param policy: Policy can be either a function or a string. If it is a function, it will be called with the user Profile and the author Profile as arguments. If it is a string, it will be used to find the corresponding function in the default policy dictionary. If no policy is passed, the default policy will be used.
    :type policy: str or function, optional
    :param n_years: Number of years to be considered for conflict detection.
    :type n_years: int, optional

    :return: List containing all the conflicts between the user Profile and the author Profiles
    :rtype: list[str]
    """

    author_ids = set()
    author_domains = set()
    author_emails = set()
    author_relations = set()
    author_publications = set()

    if callable(policy):
        info_function = info_function_builder(policy)
    elif policy == 'NeurIPS':
        info_function = info_function_builder(get_neurips_profile_info)
    else:
        info_function = info_function_builder(get_profile_info)

    for profile in author_profiles:
        author_info = info_function(profile, n_years)
        author_ids.add(author_info['id'])
        author_domains.update(author_info['domains'])
        author_emails.update(author_info['emails'])
        author_relations.update(author_info['relations'])
        author_publications.update(author_info['publications'])

    user_info = info_function(user_profile, n_years)

    conflicts = set()
    conflicts.update(author_ids.intersection(set([user_info['id']])))
    conflicts.update(author_domains.intersection(user_info['domains']))
    conflicts.update(author_relations.intersection([user_info['id']]))
    conflicts.update(author_ids.intersection(user_info['relations']))
    conflicts.update(author_emails.intersection(user_info['emails']))
    conflicts.update(author_publications.intersection(user_info['publications']))

    return list(conflicts)

def get_profile_info(profile, n_years=None):
    """
    Gets all the domains, emails, relations associated with a Profile

    :param profile: Profile from which all the relations will be obtained
    :type profile: Profile
    :param n_years: Number of years to consider when getting the profile information
    :type n_years: int, optional

    :return: Dictionary with the domains, emails, and relations associated with the passed Profile
    :rtype: dict
    """
    domains = set()
    emails = set()
    relations = set()
    publications = set()

    if n_years:
        cut_off_date = datetime.datetime.now()
        cut_off_date = cut_off_date - datetime.timedelta(days=365 * n_years)
        cut_off_year = cut_off_date.year
    else:
        cut_off_year = -1

    ## Emails section
    for email in profile.content['emails']:
        # split email
        if '@' in email:
            domain = email.split('@')[1]
            domains.add(domain)
        else:
            print('Profile with invalid email:', profile.id, email)

    ## Institution section
    for history in profile.content.get('history', []):
        try:
            end = int(history.get('end', 0) or 0)
        except:
            end = 0
        if not end or (int(end) > cut_off_year):
            domain = history.get('institution', {}).get('domain', '')
            domains.add(domain)

    ## Relations section
    relations = filter_relations_by_year(profile.content.get('relations', []), cut_off_year)

    ## Publications section: get publications within last n years, default is all publications from previous years
    publications = filter_publications_by_year(profile.content.get('publications', []), cut_off_year)

    return {
        'id': profile.id,
        'domains': domains,
        'emails': emails,
        'relations': relations,
        'publications': publications
    }

def get_neurips_profile_info(profile, n_years=None):
    """
    Gets all the domains, emails, relations associated with a Profile

    :param profile: Profile from which all the relations will be obtained
    :type profile: Profile
    :param n_years: Number of years to consider when getting the profile information
    :type n_years: int, optional

    :return: Dictionary with the domains, emails, and relations associated with the passed Profile
    :rtype: dict
    """
    domains = set()
    emails=set()
    relations = set()
    publications = set()

    if n_years:
        cut_off_date = datetime.datetime.now()
        cut_off_date = cut_off_date - datetime.timedelta(days=365 * n_years)
        cut_off_year = cut_off_date.year
    else:
        cut_off_year = -1

    ## Institution section, get history within the last n years, excluding internships
    for h in profile.content.get('history', []):
        position = h.get('position')
        if not position or (isinstance(position, str) and 'intern' not in position.lower()):
            try:
                end = int(h.get('end', 0) or 0)
            except:
                end = 0
            if not end or (int(end) > cut_off_year):
                domain = h.get('institution', {}).get('domain', '')
                domains.add(domain)

    ## Relations section, get coauthor/coworker relations within the last n years + all the other relations
    relations = filter_relations_by_year(profile.content.get('relations', []), cut_off_year, ['Coauthor','Coworker'])

    ## if institution section is empty, add email domains
    if not domains:
        for email in profile.content['emails']:
            if '@' in email:
                domain = email.split('@')[1]
                domains.add(domain)
            else:
                print('Profile with invalid email:', profile.id, email)

    ## Publications section: get publications within last n years
    publications = filter_publications_by_year(profile.content.get('publications', []), cut_off_year)

    return {
        'id': profile.id,
        'domains': domains,
        'emails': emails,
        'relations': relations,
        'publications': publications
    }

def get_current_submissions_profile_info(profile, n_years=None, submission_venueid=None):
    """
    Gets only submissions submitted to the current venue

    :param profile: Profile from which all publications will be obtained
    :type profile: Profile
    :param submission_venue_id: venue_id of submissions we want to obtain
    :type submission_venue_id: str

    :return: Dictionary with the current publications associated with the passed Profile
    :rtype: dict
    """
    domains = set()
    relations = set()
    publications = set()

    if n_years is not None:
        cut_off_date = datetime.datetime.now()
        cut_off_date = cut_off_date - datetime.timedelta(days=365 * n_years)
        cut_off_year = cut_off_date.year
    else:
        cut_off_year = -1

    ## Institution section, get history within the last n years, excluding internships
    for h in profile.content.get('history', []):
        position = h.get('position')
        if not position or (isinstance(position, str) and 'intern' not in position.lower()):
            try:
                end = int(h.get('end', 0) or 0)
            except:
                end = 0
            if not end or (int(end) > cut_off_year):
                domain = h.get('institution', {}).get('domain', '')
                domains.add(domain)

    ## Relations section, get coauthor/coworker relations within the last n years + all the other relations
    relations = filter_relations_by_year(profile.content.get('relations', []), cut_off_year, ['Coauthor','Coworker'])

    ## Get publications
    for publication in profile.content.get('publications', []):
        if isinstance(publication.content.get('venueid'), dict) and publication.content['venueid']['value'] == submission_venueid:
            publications.add(publication.id)

    return {
        'id': profile.id,
        'domains': domains,
        'emails': set(),
        'relations': relations,
        'publications': publications
    }

def filter_publications_by_year(publications, cut_off_year):
    
    def extract_year(publication_id, timestamp):
        try:
            return int(datetime.datetime.fromtimestamp(timestamp/1000).year)
        except:
            print('Error extracting the date for publication: ', publication_id)       
            return None
    
    ## Publications section: get publications within last n years
    ## 1. try to get the year from the publication date
    ## 2. if not available, try to get the year from the content year field
    ## 3. if not available, try to get the year from the creation date
    filtered_publications = set()
    current_year = datetime.datetime.now().year
    for publication in publications:
        year = None
        if publication.pdate:
            year = extract_year(publication.id, publication.pdate)

        if not year and 'year' in publication.content:
            unformatted_year = None
            if isinstance(publication.content['year'], dict) and 'value' in publication.content['year']:
                unformatted_year = publication.content['year']['value']
            elif isinstance(publication.content['year'], str):
                unformatted_year = publication.content['year']

            try:
                converted_year = int(unformatted_year)
                if converted_year <= current_year:
                    year = converted_year
            except Exception as e:
                year = None
        if not year:
            year = extract_year(publication.id, publication.cdate if publication.cdate else publication.tcdate)

        if year and year > cut_off_year:
            filtered_publications.add(publication.id)

    return filtered_publications    

def filter_relations_by_year(relations, cut_off_year, only_relations=None):

    filtered_relations = set()
    for r in relations:
        relation_id = r.get('profile_id', r.get('username', r.get('email')))
        if relation_id:
            end = None
            try:
                end = int(r.get('end'))
            except:
                end = None            
            if only_relations is None or r.get('relation', '') in only_relations:
                if end is None or end > cut_off_year:
                    filtered_relations.add(relation_id)
            else:
                filtered_relations.add(relation_id)

    return filtered_relations

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
    invitaiton_id = original_note.invitation

    updated_references = []

    if references:
        pdf_url = client.put_attachment(file_path, invitaiton_id, 'pdf')

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

def get_own_reviews(client):
    baseurl_v1, baseurl_v2 = get_base_urls(client)
    client_v1 = openreview.Client(baseurl=baseurl_v1, token=client.token)
    client_v2 = openreview.api.OpenReviewClient(baseurl=baseurl_v2, token=client.token)

    # Get all the reviews from v1
    notes_v1 = client_v1.get_all_notes(tauthor=True)

    submissions_and_official_reviews = []

    # Filter Official Reviews
    for note in notes_v1:
        # Make sure that the Official Review is public
        if 'Official_Review' not in note.invitation or 'everyone' not in note.readers:
            continue
        submission_id = note.forum
        # Make sure that the submission is public
        submission = client_v1.get_note(submission_id)
        if 'everyone' not in submission.readers:
            continue
        # Add both submission and note
        submissions_and_official_reviews.append((submission, note, 1))

    # Get all the reviews from v2
    profile_id = 'Guest' if not getattr(client, 'profile') else getattr(getattr(client, 'profile'), 'id')
    if profile_id == 'Guest':
        notes_v2 = []
    else:
        notes_v2 = client_v2.get_all_notes(signature=profile_id, transitive_members=True)

    # TMLR was created before the invitation names were added to the
    # group content, so we need to hardcode it
    domain_to_reviewer_invitation_suffix = {
        'TMLR': '/-/Review'
    }

    # Filter Official Reviews
    for note in notes_v2:
        # Get review invitation name from domain group content
        if domain_to_reviewer_invitation_suffix.get(note.domain) is None:
            domain = note.domain
            group = client_v2.get_group(domain)
            reviewer_invitation_suffix = getattr(group, 'content', {}).get('review_name', {}).get('value', None)
            if reviewer_invitation_suffix is None:
                continue
            domain_to_reviewer_invitation_suffix[domain] = '/-/' + reviewer_invitation_suffix
        
        reviewer_invitation_suffix = domain_to_reviewer_invitation_suffix[note.domain]

        # Make sure that the Official Review is public
        official_review = None
        for invitation in note.invitations:
            if reviewer_invitation_suffix in invitation:
                official_review = note
        if official_review is None or 'everyone' not in note.readers:
            continue
        submission_id = official_review.forum
        # Make sure that the submission is public
        submission = client_v2.get_note(submission_id)
        if 'everyone' not in submission.readers:
            continue
        # Add both submission and note
        submissions_and_official_reviews.append((submission, official_review, 2))

    links = []
    for submission, official_review, version in submissions_and_official_reviews:
        submission_link = f'https://openreview.net/forum?id={submission.id}'
        review_link = f'https://openreview.net/forum?id={submission.id}&noteId={official_review.id}'
        submission_title = ''
        if version == 1:
            submission_title = submission.content.get('title', '')
        else:
            submission_title = submission.content.get('title', {}).get('value', '')
        links.append({
            'submission_title': submission_title,
            'submission_link': submission_link,
            'review_link': review_link
        })
    
    return links

def get_base_urls(client):

    baseurl_v1 = 'http://localhost:3000'
    baseurl_v2 = 'http://localhost:3001'

    if 'https://devapi' in client.baseurl:
        baseurl_v1 = 'https://devapi.openreview.net'
        baseurl_v2 = 'https://devapi2.openreview.net'
    if 'https://api' in client.baseurl:
        baseurl_v1 = 'https://api.openreview.net'
        baseurl_v2 = 'https://api2.openreview.net'

    return [baseurl_v1, baseurl_v2] 
