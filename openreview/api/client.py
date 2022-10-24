#!/usr/bin/python
from __future__ import absolute_import, division, print_function, unicode_literals
from datetime import date
from deprecated.sphinx import deprecated
import sys
if sys.version_info[0] < 3:
    string_types = [str, unicode]
else:
    string_types = [str]

from .. import tools
import requests
import pprint
import os
import re
import time
import jwt
import traceback
from openreview import Profile
from openreview import OpenReviewException
from .. import tools

class OpenReviewClient(object):
    """
    :param baseurl: URL to the host, example: https://api.openreview.net (should be replaced by 'host' name). If none is provided, it defaults to the environment variable `OPENREVIEW_BASEURL`
    :type baseurl: str, optional
    :param username: OpenReview username. If none is provided, it defaults to the environment variable `OPENREVIEW_USERNAME`
    :type username: str, optional
    :param password: OpenReview password. If none is provided, it defaults to the environment variable `OPENREVIEW_PASSWORD`
    :type password: str, optional
    :param token: Session token. This token can be provided instead of the username and password if the user had already logged in
    :type token: str, optional
    :param expiresIn: Time in seconds before the token expires. If none is set the value will be set automatically to one hour. The max value that it can be set to is 1 week.
    :type expiresIn: number, optional
    """
    def __init__(self, baseurl = None, username = None, password = None, token= None, tokenExpiresIn=None):

        self.baseurl = baseurl
        if not self.baseurl:
           self.baseurl = os.environ.get('OPENREVIEW_BASEURL', 'http://localhost:3001')
        self.groups_url = self.baseurl + '/groups'
        self.login_url = self.baseurl + '/login'
        self.register_url = self.baseurl + '/register'
        self.invitations_url = self.baseurl + '/invitations'
        self.mail_url = self.baseurl + '/mail'
        self.notes_url = self.baseurl + '/notes'
        self.tags_url = self.baseurl + '/tags'
        self.edges_url = self.baseurl + '/edges'
        self.bulk_edges_url = self.baseurl + '/edges/bulk'
        self.profiles_url = self.baseurl + '/profiles'
        self.profiles_search_url = self.baseurl + '/profiles/search'
        self.profiles_merge_url = self.baseurl + '/profiles/merge'
        self.reference_url = self.baseurl + '/references'
        self.tilde_url = self.baseurl + '/tildeusername'
        self.pdf_url = self.baseurl + '/pdf'
        self.pdf_revisions_url = self.baseurl + '/references/pdf'
        self.messages_url = self.baseurl + '/messages'
        self.messages_direct_url = self.baseurl + '/messages/direct'
        self.process_logs_url = self.baseurl + '/logs/process'
        self.jobs_status = self.baseurl + '/jobs/status'
        self.venues_url = self.baseurl + '/venues'
        self.note_edits_url = self.baseurl + '/notes/edits'
        self.invitation_edits_url = self.baseurl + '/invitations/edits'
        self.user_agent = 'OpenReviewPy/v' + str(sys.version_info[0])

        self.limit = 1000
        self.token = token.replace('Bearer ', '') if token else None
        self.profile = None
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json'
        }

        if self.token:
            self.headers['Authorization'] = 'Bearer ' + self.token
            self.user = jwt.decode(self.token, "secret", algorithms=["HS256"], issuer="openreview", options={"verify_signature": False})
            try:
                self.profile = self.get_profile()
            except:
                self.profile = None
        else:
            if not username:
                username = os.environ.get('OPENREVIEW_USERNAME')

            if not password:
                password = os.environ.get('OPENREVIEW_PASSWORD')

            if username or password:
                self.login_user(username, password, expiresIn=tokenExpiresIn)



    ## PRIVATE FUNCTIONS

    def __handle_token(self, response):
        self.token = str(response['token'])
        self.profile = Profile( id = response['user']['profile']['id'] )
        self.headers['Authorization'] ='Bearer ' + self.token
        self.user = jwt.decode(self.token, "secret", algorithms=["HS256"], issuer="openreview", options={"verify_signature": False})
        return response

    def __handle_response(self,response):
        try:
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if 'application/json' in response.headers.get('Content-Type'):
                error = response.json()
            elif response.text:
                error = {
                    'name': 'Error',
                    'message': response.text
                }
            else:
                error = {
                    'name': 'Error',
                    'message': response.reason
                }
            raise OpenReviewException(error)

    ## PUBLIC FUNCTIONS
    def impersonate(self, group_id):
        response = requests.post(self.baseurl + '/impersonate', json={ 'groupId': group_id }, headers=self.headers)
        response = self.__handle_response(response)
        json_response = response.json()
        self.__handle_token(json_response)
        return json_response

    def login_user(self,username=None, password=None, expiresIn=None):
        """
        Logs in a registered user

        :param username: OpenReview username
        :type username: str, optional
        :param password: OpenReview password
        :type password: str, optional

        :return: Dictionary containing user information and the authentication token
        :rtype: dict
        """
        user = { 'id': username, 'password': password, 'expiresIn': expiresIn }
        response = requests.post(self.login_url, headers=self.headers, json=user)
        response = self.__handle_response(response)
        json_response = response.json()
        self.__handle_token(json_response)
        return json_response

    def register_user(self, email = None, first = None, last = None, middle = '', password = None):
        """
        Registers a new user

        :param email: email that will be used as id to log in after the user is registered
        :type email: str, optional
        :param first: First name of the user
        :type first: str, optional
        :param last: Last name of the user
        :type last: str, optional
        :param middle: Middle name of the user
        :type middle: str, optional
        :param password: Password used to log into OpenReview
        :type password: str, optional

        :return: Dictionary containing the new user information including his id, username, email(s), readers, writers, etc.
        :rtype: dict
        """
        register_payload = {
            'email': email,
            'name': {   'first': first, 'last': last, 'middle': middle},
            'password': password
        }
        response = requests.post(self.register_url, json = register_payload, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()

    def activate_user(self, token, content):
        """
        Activates a newly registered user

        :param token: Activation token. If running in localhost, use email as token
        :type token: str
        :param content: Content of the profile to activate
        :type content: dict

        :return: Dictionary containing user information and the authentication token
        :rtype: dict

        Example:

        >>> res = client.activate_user('new@user.com', {
            'names': [
                    {
                        'first': 'New',
                        'last': 'User',
                        'username': '~New_User1'
                    }
                ],
            'emails': ['new@user.com'],
            'preferredEmail': 'new@user.com'
            })
        """
        response = requests.put(self.baseurl + '/activate/' + token, json = { 'content': content }, headers = self.headers)
        response = self.__handle_response(response)
        json_response = response.json()
        self.__handle_token(json_response)

        return json_response

    def get_activatable(self, token = None):
        response = requests.get(self.baseurl + '/activatable/' + token, params = {}, headers = self.headers)
        response = self.__handle_response(response)
        self.__handle_token(response.json()['activatable'])
        return self.token

    def get_group(self, id):
        """
        Get a single Group by id if available

        :param id: id of the group
        :type id: str

        :return: Dictionary with the group information
        :rtype: Group

        Example:

        >>> group = client.get_group('your-email@domain.com')
        """
        response = requests.get(self.groups_url, params = {'id':id}, headers = self.headers)
        response = self.__handle_response(response)
        g = response.json()['groups'][0]
        return Group.from_json(g)

    def get_invitation(self, id):
        """
        Get a single invitation by id if available

        :param id: id of the invitation
        :type id: str

        :return: Invitation matching the passed id
        :rtype: Invitation
        """
        response = requests.get(self.invitations_url, params = {'id': id}, headers = self.headers)
        response = self.__handle_response(response)
        i = response.json()['invitations'][0]
        return Invitation.from_json(i)

    def get_note(self, id, details=None):
        """
        Get a single Note by id if available

        :param id: id of the note
        :type id: str

        :return: Note matching the passed id
        :rtype: Note
        """
        response = requests.get(self.notes_url, params = {'id':id, 'details': details}, headers = self.headers)
        response = self.__handle_response(response)
        n = response.json()['notes'][0]
        return Note.from_json(n)

    def get_tag(self, id):
        """
        Get a single Tag by id if available

        :param id: id of the Tag
        :type id: str

        :return: Tag with the Tag information
        :rtype: Tag
        """
        response = requests.get(self.tags_url, params = {'id': id}, headers = self.headers)
        response = self.__handle_response(response)
        t = response.json()['tags'][0]
        return Tag.from_json(t)

    def get_edge(self, id, trash=False):
        """
        Get a single Edge by id if available

        :param id: id of the Edge
        :type id: str

        return: Edge object with its information
        :rtype: Edge
        """
        response = requests.get(self.edges_url, params = {'id': id, 'trash': 'true' if trash == True else 'false'}, headers=self.headers)
        response = self.__handle_response(response)
        edges = response.json()['edges']
        if edges:
            return Edge.from_json(edges[0])
        else:
            raise OpenReviewException('Edge not found')

    def get_profile(self, email_or_id = None):
        """
        Get a single Profile by id, if available

        :param email_or_id: e-mail or id of the profile
        :type email_or_id: str, optional

        :return: Profile object with its information
        :rtype: Profile
        """
        params = {}
        if email_or_id:
            tildematch = re.compile('~.+')
            if tildematch.match(email_or_id):
                att = 'id'
            else:
                att = 'email'
            params[att] = email_or_id
        response = requests.get(self.profiles_url, params=tools.format_params(params), headers = self.headers)
        response = self.__handle_response(response)
        profiles = response.json()['profiles']
        if profiles:
            return Profile.from_json(profiles[0])
        else:
            raise OpenReviewException(['Profile Not Found'])

    def search_profiles(self, confirmedEmails = None, emails = None, ids = None, term = None, first = None, middle = None, last = None):
        """
        Gets a list of profiles using either their ids or corresponding emails

        :param confirmedEmails: List of confirmed emails registered in OpenReview
        :type confirmedEmails: list, optional
        :param emails: List of emails registered in OpenReview
        :type emails: list, optional
        :param ids: List of OpenReview username ids
        :type ids: list, optional
        :param term: Substring in the username or e-mail to be searched
        :type term: str, optional
        :param first: First name of user
        :type first: str, optional
        :param middle: Middle name of user
        :type middle: str, optional
        :param last: Last name of user
        :type last: str, optional

        :return: List of profiles, if emails is present then a dictionary of { email: profiles } is returned. If confirmedEmails is present then a dictionary of { email: profile } is returned
        :rtype: list[Profile]
        """

        def batches(items, batch_size=1000):
            batch = []
            for item in items:
                if len(batch) == batch_size:
                    yield batch
                    batch = []

                batch.append(item)

            if batch:
                yield batch

        if term:
            response = requests.get(self.profiles_search_url, params = { 'term': term }, headers = self.headers)
            response = self.__handle_response(response)
            return [Profile.from_json(p) for p in response.json()['profiles']]

        if emails:
            full_response = []
            for email_batch in batches(emails):
                response = requests.post(self.profiles_search_url, json = {'emails': email_batch}, headers = self.headers)
                response = self.__handle_response(response)
                full_response.extend(response.json()['profiles'])

            profiles_by_email = {}
            for p in full_response:
                if p['email'] not in profiles_by_email:
                    profiles_by_email[p['email']] = []
                profiles_by_email[p['email']].append(Profile.from_json(p))
            return profiles_by_email

        if confirmedEmails:
            full_response = []
            for email_batch in batches(confirmedEmails):
                response = requests.post(self.profiles_search_url, json = {'emails': email_batch}, headers = self.headers)
                response = self.__handle_response(response)
                full_response.extend(response.json()['profiles'])

            profiles_by_email = {}
            for p in full_response:
                profile = Profile.from_json(p)
                if p['email'] in profile.content['emailsConfirmed']:
                    profiles_by_email[p['email']] = profile
            return profiles_by_email



        if ids:
            full_response = []
            for id_batch in batches(ids):
                response = requests.post(self.profiles_search_url, json = {'ids': id_batch}, headers = self.headers)
                response = self.__handle_response(response)
                full_response.extend(response.json()['profiles'])

            return [Profile.from_json(p) for p in full_response]

        if first or middle or last:
            response = requests.get(self.profiles_url, params = {'first': first, 'middle': middle, 'last': last}, headers = self.headers)
            response = self.__handle_response(response)
            return [Profile.from_json(p) for p in response.json()['profiles']]


        return []

    def get_pdf(self, id, is_reference=False):
        """
        Gets the binary content of a pdf using the provided note/reference id
        If the pdf is not found then this returns an error message with "status":404.

        Use the note id when trying to get the latest pdf version and reference id
        when trying to get a previous version of the pdf

        :param id: Note id or Reference id of the pdf
        :type id: str
        :param is_reference: Indicates that the passed id is a reference id instead of a note id
        :type is_reference: bool, optional

        :return: The binary content of a pdf
        :rtype: bytes

        Example:

        >>> f = get_pdf(id='Place Note-ID here')
        >>> with open('output.pdf','wb') as op: op.write(f)

        """
        params = {}
        params['id'] = id

        headers = self.headers.copy()
        headers['content-type'] = 'application/pdf'

        url = self.pdf_revisions_url if is_reference else self.pdf_url

        response = requests.get(url, params=tools.format_params(params), headers = headers)
        response = self.__handle_response(response)
        return response.content

    def get_attachment(self, id, field_name):
        """
        Gets the binary content of a attachment using the provided note id
        If the pdf is not found then this returns an error message with "status":404.

        :param id: Note id or Reference id of the pdf
        :type id: str
        :param field_name: name of the field associated with the attachment file
        :type field_name: str

        :return: The binary content of a pdf
        :rtype: bytes

        Example:

        >>> f = get_attachment(id='Place Note-ID here', field_name='pdf')
        >>> with open('output.pdf','wb') as op: op.write(f)

        """
        response = requests.get(self.baseurl + '/attachment', params = { 'id': id, 'name': field_name }, headers = self.headers)
        response = self.__handle_response(response)
        return response.content

    def get_venues(self, id=None, ids=None, invitations=None):
        """
        Gets list of Note objects based on the filters provided. The Notes that will be returned match all the criteria passed in the parameters.

        :param id: a Venue ID. If provided, returns Notes whose ID matches the given ID.
        :type id: str, optional
        :param ids: A list of Venue IDs. If provided, returns Notes containing these IDs.
        :type ids: list, optional
        :param invitations: A list of Invitation IDs. If provided, returns Venues whose "invitation" field is this Invitation ID.
        :type invitations: list, optional

        :return: List of Venues
        :rtype: list[dict]
        """
        params = {}
        if id is not None:
            params['id'] = id
        if ids is not None:
            params['ids'] = ','.join(ids)
        if invitations is not None:
            params['invitations'] = ','.join(invitations)

        response = requests.get(self.venues_url, params=tools.format_params(params), headers=self.headers)
        response = self.__handle_response(response)

        return response.json()['venues']

    def put_attachment(self, file_path, invitation, name):
        """
        Uploads a file to the openreview server

        :param file: Path to the file
        :type file: str
        :param invitation: Invitation of the note that required the attachment
        :type file: str
        :param file: name of the note field to save the attachment url
        :type file: str

        :return: A relative URL for the uploaded file
        :rtype: str
        """

        headers = self.headers.copy()

        with open(file_path, 'rb') as f:
            response = requests.put(self.baseurl + '/attachment', files=(
                ('invitationId', (None, invitation)),
                ('name', (None, name)),
                ('file', (file_path, f))
            ), headers = headers)

        response = self.__handle_response(response)
        return response.json()['url']

    def post_profile(self, profile):
        """
        Updates a Profile

        :param profile: Profile object
        :type profile: Profile

        :return: The new updated Profile
        :rtype: Profile
        """
        response = requests.post(
            self.profiles_url,
            json = profile.to_json(),
            headers = self.headers)

        response = self.__handle_response(response)
        return Profile.from_json(response.json())

    def merge_profiles(self, profileTo, profileFrom):
        """
        Merges two Profiles

        :param profileTo: Profile object to merge to
        :type profileTo: Profile
        :param profileFrom: Profile object to merge from (this profile will be deleted)
        :type: profileFrom: Profile

        :return: The new updated Profile
        :rtype: Profile
        """
        response = requests.post(
            self.profiles_merge_url,
            json = {
                'to': profileTo,
                'from': profileFrom
            },
            headers = self.headers)

        response = self.__handle_response(response)
        return Profile.from_json(response.json())


    def get_groups(self, id = None, prefix = None, member = None, signatory = None, web = None, limit = None, offset = None, with_count=False):
        """
        Gets list of Group objects based on the filters provided. The Groups that will be returned match all the criteria passed in the parameters.

        :param id: id of the Group
        :type id: str, optional
        :param prefix: Prefix that matches several Group ids
        :type prefix: str, optional
        :param member: Groups that contain this member
        :type member: str, optional
        :param signatory: Groups that contain this signatory
        :type signatory: str, optional
        :param web: Groups that contain a web field value
        :type web: bool, optional
        :param limit: Maximum amount of Groups that this method will return. The limit parameter can range between 0 and 1000 inclusive. If a bigger number is provided, only 1000 Groups will be returned
        :type limit: int, optional
        :param offset: Indicates the position to start retrieving Groups. For example, if there are 10 Groups and you want to obtain the last 3, then the offset would need to be 7.
        :type offset: int, optional

        :return: List of Groups
        :rtype: list[Group]
        """
        params = {}
        if id is not None: params['id'] = id
        if prefix is not None: params['prefix'] = prefix
        if member is not None: params['member'] = member
        if signatory is not None: params['signatory'] = signatory
        if web: params['web'] = web
        params['limit'] = limit
        params['offset'] = offset

        response = requests.get(self.groups_url, params=tools.format_params(params), headers = self.headers)
        response = self.__handle_response(response)
        groups = [Group.from_json(g) for g in response.json()['groups']]

        if with_count and params.get('offset') is None:
            return groups, response.json()['count']

        return groups

    def get_all_groups(self, id = None, prefix = None, member = None, signatory = None, web = None, limit = None, offset = None, with_count=False):
        """
        Gets list of Group objects based on the filters provided. The Groups that will be returned match all the criteria passed in the parameters.

        :param id: id of the Group
        :type id: str, optional
        :param prefix: Prefix that matches several Group ids
        :type prefix: str, optional
        :param member: Groups that contain this member
        :type member: str, optional
        :param signatory: Groups that contain this signatory
        :type signatory: str, optional
        :param web: Groups that contain a web field value
        :type web: bool, optional
        :param limit: Maximum amount of Groups that this method will return. The limit parameter can range between 0 and 1000 inclusive. If a bigger number is provided, only 1000 Groups will be returned
        :type limit: int, optional
        :param offset: Indicates the position to start retrieving Groups. For example, if there are 10 Groups and you want to obtain the last 3, then the offset would need to be 7.
        :type offset: int, optional

        :return: List of Groups
        :rtype: list[Group]
        """
        params = {
            'id': id,
            'prefix': prefix,
            'member': member,
            'signatory': signatory,
            'web': web,
            'limit': limit,
            'offset': offset,
            'with_count': with_count
        }

        return tools.concurrent_get(self, self.get_groups, **params)

    def get_invitations(self,
        id = None,
        ids = None,
        invitee = None,
        replytoNote = None,
        replyForum = None,
        signature = None,
        note = None,
        prefix = None,
        tags = None,
        limit = None,
        offset = None,
        minduedate = None,
        duedate = None,
        pastdue = None,
        replyto = None,
        details = None,
        expired = None,
        type = None,
        with_count=False,
        invitation = None
    ):
        """
        Gets list of Invitation objects based on the filters provided. The Invitations that will be returned match all the criteria passed in the parameters.

        :param id: id of the Invitation
        :type id: str, optional
        :param ids: Comma separated Invitation IDs. If provided, returns invitations whose "id" value is any of the passed Invitation IDs.
        :type ids: str, optional
        :param invitee: Invitations that contain this invitee
        :type invitee: str, optional
        :param replytoNote: Invitations that contain this replytoNote
        :type replytoNote: str, optional
        :param replyForum: Invitations that contain this replyForum
        :type replyForum: str, optional
        :param signature: Invitations that contain this signature
        :type signature: optional
        :param note: Invitations that contain this note
        :type note: str, optional
        :param prefix: Invitation ids that match this prefix
        :type prefix: str, optional
        :param tags: Invitations that contain these tags
        :type tags: Tag, optional
        :param int limit: Maximum amount of Invitations that this method will return. The limit parameter can range between 0 and 1000 inclusive. If a bigger number is provided, only 1000 Invitations will be returned
        :type limit: int, optional
        :param int offset: Indicates the position to start retrieving Invitations. For example, if there are 10 Invitations and you want to obtain the last 3, then the offset would need to be 7.
        :type offset: int, optional
        :param minduedate: Invitations that have at least this value as due date
        :type minduedate: int, optional
        :param duedate: Invitations that contain this due date
        :type duedate: int, optional
        :param pastdue: Invitaions that are past due
        :type pastdue: bool, optional
        :param replyto: Invitations that contain this replyto
        :type replyto: optional
        :param details: TODO: What is a valid value for this field?
        :type details: dict, optional
        :param expired: If true, retrieves the Invitations that have expired, otherwise, the ones that have not expired
        :type expired: bool, optional

        :return: List of Invitations
        :rtype: list[Invitation]
        """
        params = {}
        if id is not None:
            params['id'] = id
        if ids is not None:
            params['ids'] = ids
        if invitee is not None:
            params['invitee'] = invitee
        if replytoNote is not None:
            params['replytoNote'] = replytoNote
        if replyForum is not None:
            params['replyForum'] = replyForum
        if signature is not None:
            params['signature'] = signature
        if note is not None:
            params['note']=note
        if prefix:
            params['prefix'] = prefix
        if tags:
            params['tags'] = tags
        if minduedate:
            params['minduedate'] = minduedate
        params['replyto'] = replyto
        params['duedate'] = duedate
        params['pastdue'] = pastdue
        params['details'] = details
        params['limit'] = limit
        params['offset'] = offset
        params['expired'] = expired
        params['type'] = type
        params['invitation'] = invitation

        response = requests.get(self.invitations_url, params=tools.format_params(params), headers=self.headers)
        response = self.__handle_response(response)

        invitations = [Invitation.from_json(i) for i in response.json()['invitations']]

        if with_count and params.get('offset') is None:
            return invitations, response.json()['count']

        return invitations

    def get_all_invitations(self,
        id = None,
        ids = None,
        invitee = None,
        replytoNote = None,
        replyForum = None,
        signature = None,
        note = None,
        prefix = None,
        tags = None,
        limit = None,
        offset = None,
        minduedate = None,
        duedate = None,
        pastdue = None,
        replyto = None,
        details = None,
        expired = None,
        type = None,
        with_count=False,
        invitation = None
    ):
        """
        Gets list of Invitation objects based on the filters provided. The Invitations that will be returned match all the criteria passed in the parameters.

        :param id: id of the Invitation
        :type id: str, optional
        :param ids: Comma separated Invitation IDs. If provided, returns invitations whose "id" value is any of the passed Invitation IDs.
        :type ids: str, optional
        :param invitee: Invitations that contain this invitee
        :type invitee: str, optional
        :param replytoNote: Invitations that contain this replytoNote
        :type replytoNote: str, optional
        :param replyForum: Invitations that contain this replyForum
        :type replyForum: str, optional
        :param signature: Invitations that contain this signature
        :type signature: optional
        :param note: Invitations that contain this note
        :type note: str, optional
        :param prefix: Invitation ids that match this prefix
        :type prefix: str, optional
        :param tags: Invitations that contain these tags
        :type tags: Tag, optional
        :param int limit: Maximum amount of Invitations that this method will return. The limit parameter can range between 0 and 1000 inclusive. If a bigger number is provided, only 1000 Invitations will be returned
        :type limit: int, optional
        :param int offset: Indicates the position to start retrieving Invitations. For example, if there are 10 Invitations and you want to obtain the last 3, then the offset would need to be 7.
        :type offset: int, optional
        :param minduedate: Invitations that have at least this value as due date
        :type minduedate: int, optional
        :param duedate: Invitations that contain this due date
        :type duedate: int, optional
        :param pastdue: Invitaions that are past due
        :type pastdue: bool, optional
        :param replyto: Invitations that contain this replyto
        :type replyto: optional
        :param details: TODO: What is a valid value for this field?
        :type details: dict, optional
        :param expired: If true, retrieves the Invitations that have expired, otherwise, the ones that have not expired
        :type expired: bool, optional

        :return: List of Invitations
        :rtype: list[Invitation]
        """
        params = {
            'id': id,
            'ids': ids,
            'invitee': invitee,
            'replytoNote': replytoNote,
            'replyForum': replyForum,
            'signature': signature,
            'note': note,
            'prefix': prefix,
            'tags': tags,
            'limit': limit,
            'offset': offset,
            'minduedate': minduedate,
            'duedate': duedate,
            'pastdue': pastdue,
            'replyto': replyto,
            'details': details,
            'expired': expired,
            'type': type,
            'with_count': with_count,
            'invitation': invitation
        }

        return tools.concurrent_get(self, self.get_invitations, **params)

    def get_invitation_edit(self, id):
        """
        Get a single edit by id if available

        :param id: id of the edit
        :type id: str

        :return: edit matching the passed id
        :rtype: Note
        """
        response = requests.get(self.invitation_edits_url, params = {'id':id}, headers = self.headers)
        response = self.__handle_response(response)
        n = response.json()['edits'][0]
        return Edit.from_json(n)

    def get_invitation_edits(self, invitation_id = None, invitation = None, with_count=False, sort=None):
        """
        Gets a list of edits for a note. The edits that will be returned match all the criteria passed in the parameters.

        :return: List of edits
        :rtype: list[Edit]
        """
        params = {}
        if invitation_id:
            params['invitation.id'] = invitation_id
        if invitation:
            params['invitation'] = invitation
        if sort:
            params['sort'] = sort

        response = requests.get(self.invitation_edits_url, params=tools.format_params(params), headers = self.headers)
        response = self.__handle_response(response)

        edits = [Edit.from_json(n) for n in response.json()['edits']]

        if with_count and params.get('offset') is None:
            return edits, response.json()['count']

        return edits        

    def get_notes(self, id = None,
            paperhash = None,
            forum = None,
            original = None,
            invitation = None,
            replyto = None,
            tauthor = None,
            signature = None,
            writer = None,
            trash = None,
            number = None,
            content = None,
            limit = None,
            offset = None,
            mintcdate = None,
            details = None,
            sort = None,
            with_count=False
            ):
        """
        Gets list of Note objects based on the filters provided. The Notes that will be returned match all the criteria passed in the parameters.

        :param id: a Note ID. If provided, returns Notes whose ID matches the given ID.
        :type id: str, optional
        :param paperhash: A "paperhash" for a note. If provided, returns Notes whose paperhash matches this argument.
            (A paperhash is a human-interpretable string built from the Note's title and list of authors to uniquely
            identify the Note)
        :type paperhash: str, optional
        :param forum: A Note ID. If provided, returns Notes whose forum matches the given ID.
        :type forum: str, optional
        :param original: A Note ID. If provided, returns Notes whose original matches the given ID.
        :type original: str, optional
        :param invitation: An Invitation ID. If provided, returns Notes whose "invitation" field is this Invitation ID.
        :type invitation: str, optional
        :param replyto: A Note ID. If provided, returns Notes whose replyto field matches the given ID.
        :type replyto: str, optional
        :param tauthor: A Group ID. If provided, returns Notes whose tauthor field ("true author") matches the given ID, or is a transitive member of the Group represented by the given ID.
        :type tauthor: str, optional
        :param signature: A Group ID. If provided, returns Notes whose signatures field contains the given Group ID.
        :type signature: str, optional
        :param writer: A Group ID. If provided, returns Notes whose writers field contains the given Group ID.
        :type writer: str, optional
        :param trash: If True, includes Notes that have been deleted (i.e. the ddate field is less than the
            current date)
        :type trash: bool, optional
        :param number: If present, includes Notes whose number field equals the given integer.
        :type number: int, optional
        :param content: If present, includes Notes whose each key is present in the content field and it is equals the given value.
        :type content: dict, optional
        :param limit: Maximum amount of Notes that this method will return. The limit parameter can range between 0 and 1000 inclusive. If a bigger number is provided, only 1000 Notes will be returned
        :type limit: int, optional
        :param offset: Indicates the position to start retrieving Notes. For example, if there are 10 Notes and you want to obtain the last 3, then the offset would need to be 7.
        :type offset: int, optional
        :param mintcdate: Represents an Epoch time timestamp, in milliseconds. If provided, returns Notes
            whose "true creation date" (tcdate) is at least equal to the value of mintcdate.
        :type mintcdate: int, optional
        :param details: TODO: What is a valid value for this field?
        :type details: optional
        :param sort: Sorts the output by field depending on the string passed. Possible values: number, cdate, ddate, tcdate, tmdate, replyCount (Invitation id needed in the invitation field).
        :type sort: str, optional

        :return: List of Notes
        :rtype: list[Note]
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
        if content is not None:
            for k in content:
                params['content.' + k] = content[k]
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        if mintcdate is not None:
            params['mintcdate'] = mintcdate
        if details is not None:
            params['details'] = details
        params['sort'] = sort
        params['original'] = original

        response = requests.get(self.notes_url, params=tools.format_params(params), headers = self.headers)
        response = self.__handle_response(response)

        notes = [Note.from_json(n) for n in response.json()['notes']]

        if with_count and params.get('offset') is None:
            return notes, response.json()['count']

        return notes

    def get_all_notes(self, id = None,
            paperhash = None,
            forum = None,
            original = None,
            invitation = None,
            replyto = None,
            tauthor = None,
            signature = None,
            writer = None,
            trash = None,
            number = None,
            content = None,
            limit = None,
            offset = None,
            mintcdate = None,
            details = None,
            sort = None,
            with_count=False
            ):
        """
        Gets list of Note objects based on the filters provided. The Notes that will be returned match all the criteria passed in the parameters.

        :param id: a Note ID. If provided, returns Notes whose ID matches the given ID.
        :type id: str, optional
        :param paperhash: A "paperhash" for a note. If provided, returns Notes whose paperhash matches this argument.
            (A paperhash is a human-interpretable string built from the Note's title and list of authors to uniquely
            identify the Note)
        :type paperhash: str, optional
        :param forum: A Note ID. If provided, returns Notes whose forum matches the given ID.
        :type forum: str, optional
        :param original: A Note ID. If provided, returns Notes whose original matches the given ID.
        :type original: str, optional
        :param invitation: An Invitation ID. If provided, returns Notes whose "invitation" field is this Invitation ID.
        :type invitation: str, optional
        :param replyto: A Note ID. If provided, returns Notes whose replyto field matches the given ID.
        :type replyto: str, optional
        :param tauthor: A Group ID. If provided, returns Notes whose tauthor field ("true author") matches the given ID, or is a transitive member of the Group represented by the given ID.
        :type tauthor: str, optional
        :param signature: A Group ID. If provided, returns Notes whose signatures field contains the given Group ID.
        :type signature: str, optional
        :param writer: A Group ID. If provided, returns Notes whose writers field contains the given Group ID.
        :type writer: str, optional
        :param trash: If True, includes Notes that have been deleted (i.e. the ddate field is less than the
            current date)
        :type trash: bool, optional
        :param number: If present, includes Notes whose number field equals the given integer.
        :type number: int, optional
        :param content: If present, includes Notes whose each key is present in the content field and it is equals the given value.
        :type content: dict, optional
        :param limit: Maximum amount of Notes that this method will return. The limit parameter can range between 0 and 1000 inclusive. If a bigger number is provided, only 1000 Notes will be returned
        :type limit: int, optional
        :param offset: Indicates the position to start retrieving Notes. For example, if there are 10 Notes and you want to obtain the last 3, then the offset would need to be 7.
        :type offset: int, optional
        :param mintcdate: Represents an Epoch time timestamp, in milliseconds. If provided, returns Notes
            whose "true creation date" (tcdate) is at least equal to the value of mintcdate.
        :type mintcdate: int, optional
        :param details: TODO: What is a valid value for this field?
        :type details: optional
        :param sort: Sorts the output by field depending on the string passed. Possible values: number, cdate, ddate, tcdate, tmdate, replyCount (Invitation id needed in the invitation field).
        :type sort: str, optional

        :return: List of Notes
        :rtype: list[Note]
        """

        params = {
            'id': id,
            'paperhash': paperhash,
            'forum': forum,
            'original': original,
            'invitation': invitation,
            'replyto': replyto,
            'tauthor': tauthor,
            'signature': signature,
            'writer': writer,
            'trash': trash,
            'number': number,
            'content': content,
            'limit': limit,
            'offset': offset,
            'mintcdate': mintcdate,
            'details': details,
            'sort': sort,
            'with_count': with_count
        }

        return tools.concurrent_get(self, self.get_notes, **params)

    def get_note_edit(self, id):
        """
        Get a single edit by id if available

        :param id: id of the edit
        :type id: str

        :return: edit matching the passed id
        :rtype: Note
        """
        response = requests.get(self.note_edits_url, params = {'id':id}, headers = self.headers)
        response = self.__handle_response(response)
        n = response.json()['edits'][0]
        return Edit.from_json(n)

    def get_note_edits(self, note_id = None, invitation = None, with_count=False, sort=None):
        """
        Gets a list of edits for a note. The edits that will be returned match all the criteria passed in the parameters.

        :return: List of edits
        :rtype: list[Edit]
        """
        params = {}
        if note_id:
            params['note.id'] = note_id
        if invitation:
            params['invitation'] = invitation
        if sort:
            params['sort'] = sort

        response = requests.get(self.note_edits_url, params=tools.format_params(params), headers = self.headers)
        response = self.__handle_response(response)

        edits = [Edit.from_json(n) for n in response.json()['edits']]

        if with_count and params.get('offset') is None:
            return edits, response.json()['count']

        return edits

    def get_tags(self, id = None, invitation = None, forum = None, signature = None, tag = None, limit = None, offset = None, with_count=False):
        """
        Gets a list of Tag objects based on the filters provided. The Tags that will be returned match all the criteria passed in the parameters.

        :param id: A Tag ID. If provided, returns Tags whose ID matches the given ID.
        :type id: str, optional
        :param forum: A Note ID. If provided, returns Tags whose forum matches the given ID.
        :type forum: str, optional
        :param invitation: An Invitation ID. If provided, returns Tags whose "invitation" field is this Invitation ID.
        :type invitation: str, optional

        :return: List of tags
        :rtype: list[Tag]
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
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset

        response = requests.get(self.tags_url, params=tools.format_params(params), headers = self.headers)
        response = self.__handle_response(response)

        tags = [Tag.from_json(t) for t in response.json()['tags']]
        if with_count and params.get('offset') is None:
            return tags, response.json()['count']

        return tags

    def get_all_tags(self, id = None, invitation = None, forum = None, signature = None, tag = None, limit = None, offset = None, with_count=False):
        """
        Gets a list of Tag objects based on the filters provided. The Tags that will be returned match all the criteria passed in the parameters.

        :param id: A Tag ID. If provided, returns Tags whose ID matches the given ID.
        :type id: str, optional
        :param forum: A Note ID. If provided, returns Tags whose forum matches the given ID.
        :type forum: str, optional
        :param invitation: An Invitation ID. If provided, returns Tags whose "invitation" field is this Invitation ID.
        :type invitation: str, optional

        :return: List of tags
        :rtype: list[Tag]
        """
        params = {
            'id': id,
            'invitation': invitation,
            'forum': forum,
            'signature': signature,
            'tag': tag,
            'limit': limit,
            'offset': offset,
            'with_count': with_count
        }

        return tools.concurrent_get(self, self.get_tags, **params)

    def get_edges(self, id = None, invitation = None, head = None, tail = None, label = None, limit = None, offset = None, with_count=False, trash=None):
        """
        Returns a list of Edge objects based on the filters provided.

        :arg id: a Edge ID. If provided, returns Edge whose ID matches the given ID.
        :arg invitation: an Invitation ID. If provided, returns Edges whose "invitation" field is this Invitation ID.
        :arg head: Profile ID of the Profile that is connected to the Note ID in tail
        :arg tail: Note ID of the Note that is connected to the Profile ID in head
        :arg label: Label ID of the match
        """
        params = {}

        params['id'] = id
        params['invitation'] = invitation
        params['head'] = head
        params['tail'] = tail
        params['label'] = label
        params['limit'] = limit
        params['offset'] = offset
        params['trash'] = trash

        response = requests.get(self.edges_url, params=tools.format_params(params), headers = self.headers)
        response = self.__handle_response(response)

        edges = [Edge.from_json(e) for e in response.json()['edges']]

        if with_count and params.get('offset') is None:
            return edges, response.json()['count']

        return edges

    def get_all_edges(self, id = None, invitation = None, head = None, tail = None, label = None, limit = None, offset = None, with_count=False, trash=None):
        """
        Returns a list of Edge objects based on the filters provided.

        :arg id: a Edge ID. If provided, returns Edge whose ID matches the given ID.
        :arg invitation: an Invitation ID. If provided, returns Edges whose "invitation" field is this Invitation ID.
        :arg head: Profile ID of the Profile that is connected to the Note ID in tail
        :arg tail: Note ID of the Note that is connected to the Profile ID in head
        :arg label: Label ID of the match
        """
        params = {
            'id': id,
            'invitation': invitation,
            'head': head,
            'tail': tail,
            'label': label,
            'limit': limit,
            'offset': offset,
            'with_count': with_count,
            'trash': trash
        }

        return tools.concurrent_get(self, self.get_edges, **params)

    def get_edges_count(self, id = None, invitation = None, head = None, tail = None, label = None):
        """
        Returns a list of Edge objects based on the filters provided.

        :arg id: a Edge ID. If provided, returns Edge whose ID matches the given ID.
        :arg invitation: an Invitation ID. If provided, returns Edges whose "invitation" field is this Invitation ID.
        :arg head: Profile ID of the Profile that is connected to the Note ID in tail
        :arg tail: Note ID of the Note that is connected to the Profile ID in head
        :arg label: Label ID of the match
        """
        params = {}

        params['id'] = id
        params['invitation'] = invitation
        params['head'] = head
        params['tail'] = tail
        params['label'] = label
        params['limit'] = 1
        params['offset'] = 0

        response = requests.get(self.edges_url, params=tools.format_params(params), headers = self.headers)
        response = self.__handle_response(response)

        return response.json()['count']

    def get_grouped_edges(self, invitation=None, head=None, tail=None, label=None, groupby='head', select='tail', limit=None, offset=None):
        '''
        Returns a list of JSON objects where each one represents a group of edges.  For example calling this
        method with default arguments will give back a list of groups where each group is of the form:
        {id: {head: paper-1} values: [ {tail: user-1}, {tail: user-2} ]}
        Note: The limit applies to the number of groups returned.  It does not apply to the number of edges within the groups.

        :param invitation:
        :param groupby:
        :param select:
        :param limit:
        :param offset:
        :return:
        '''
        params = {}
        params['id'] = None
        params['invitation'] = invitation
        params['head'] = head
        params['tail'] = tail
        params['label'] = label
        params['groupBy'] = groupby
        params['select'] = select
        params['limit'] = limit
        params['offset'] = offset
        response = requests.get(self.edges_url, params=tools.format_params(params), headers = self.headers)
        response = self.__handle_response(response)
        json = response.json()
        return json['groupedEdges'] # a list of JSON objects holding information about an edge


    def post_group(self, group, overwrite = True):
        """
        Posts the group. If the group is unsigned, signs it using the client's default signature.

        :param group: Group to be posted
        :type group: Group
        :param overwrite: Determines whether to overwrite an existing group or not
        :type overwrite: bool, optional

        :return: The posted Group
        :rtype: Group
        """
        if overwrite or not self.exists(group.id):
            if not group.signatures: group.signatures = [self.profile.id]
            if not group.writers: group.writers = [self.profile.id]
            response = requests.post(self.groups_url, json=group.to_json(), headers=self.headers)
            response = self.__handle_response(response)

        return Group.from_json(response.json())

    def post_invitation(self, invitation):
        """
        Posts the invitation. If the invitation is unsigned, signs it using the client's default signature.

        :param invitation: Invitation to be posted
        :type invitation: Invitation

        :return: The posted Invitation
        :rtype: Invitation
        """
        response = requests.post(self.invitations_url, json = invitation.to_json(), headers = self.headers)
        response = self.__handle_response(response)

        return Invitation.from_json(response.json())

    def post_note(self, note):
        """
        Posts the note. If the note is unsigned, signs it using the client's default signature.

        :param note: Note to be posted
        :type note: Note

        :return: The posted Note
        :rtype: Note
        """
        if not note.signatures: note.signatures = [self.profile.id]
        response = requests.post(self.notes_url, json=note.to_json(), headers=self.headers)
        response = self.__handle_response(response)

        return Note.from_json(response.json())

    def post_tag(self, tag):
        """
        Posts the tag. If the tag is unsigned, signs it using the client's default signature.

        :param tag: Tag to be posted
        :type tag: Tag

        :return Tag: The posted Tag
        """
        response = requests.post(self.tags_url, json = tag.to_json(), headers = self.headers)
        response = self.__handle_response(response)

        return Tag.from_json(response.json())

    def post_edge(self, edge):
        """
        Posts the edge. Upon success, returns the posted Edge object.
        """
        response = requests.post(self.edges_url, json = edge.to_json(), headers = self.headers)
        response = self.__handle_response(response)

        return Edge.from_json(response.json())

    def post_edges (self, edges):
        '''
        Posts the list of Edges.   Returns a list Edge objects updated with their ids.
        '''
        send_json = [edge.to_json() for edge in edges]
        response = requests.post(self.bulk_edges_url, json = send_json, headers = self.headers)
        response = self.__handle_response(response)
        received_json_array = response.json()
        edge_objects = [Edge.from_json(edge) for edge in received_json_array]
        return edge_objects

    def post_venue(self, venue):
        """
        Posts the venue. Upon success, returns the posted Venue object.
        """

        response = requests.post(self.venues_url, json=venue, headers=self.headers)
        response = self.__handle_response(response)

        return response.json()

    def delete_edges(self, invitation, label=None, head=None, tail=None, wait_to_finish=False, soft_delete=False):
        """
        Deletes edges by a combination of invitation id and one or more of the optional filters.

        :param invitation: an invitation ID
        :type invitation: str
        :param label: a matching label ID
        :type label: str, optional
        :param head: id of the edge head (head type defined by the edge invitation)
        :type head: str, optional
        :param tail: id of the edge tail (tail type defined by the edge invitation)
        :type tail: str, optional
        :param wait_to_finish: True if execution should pause until deletion of edges is finished
        :type wait_to_finish: bool, optional

        :return: a {status = 'ok'} in case of a successful deletion and an OpenReview exception otherwise
        :rtype: dict
        """
        delete_query = {'invitation': invitation}
        if label:
            delete_query['label'] = label
        if head:
            delete_query['head'] = head
        if tail:
            delete_query['tail'] = tail

        delete_query['waitToFinish'] = wait_to_finish
        delete_query['softDelete'] = soft_delete

        response = requests.delete(self.edges_url, json = delete_query, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()

    def delete_note(self, note_id):
        """
        Deletes the note

        :param note_id: ID of Note to be deleted
        :type note_id: str

        :return: a {status = 'ok'} in case of a successful deletion and an OpenReview exception otherwise
        :rtype: dict
        """
        response = requests.delete(self.notes_url, json = {'id': note_id}, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()

    def delete_profile_reference(self, reference_id):
        '''
        Deletes the Profile Reference specified by `reference_id`.

        :param reference_id: ID of the Profile Reference to be deleted.
        :type reference_id: str

        :return: a {status = 'ok'} in case of a successful deletion and an OpenReview exception otherwise
        :rtype: dict
        '''

        response = requests.delete(self.profiles_url + '/reference', json = {'id': reference_id}, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()

    def delete_group(self, group_id):
        """
        Deletes the group

        :param group_id: ID of Group to be deleted
        :type group_id: str

        :return: a {status = 'ok'} in case of a successful deletion and an OpenReview exception otherwise
        :rtype: dict
        """
        response = requests.delete(self.groups_url, json = {'id': group_id}, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()


    def post_message(self, subject, recipients, message, ignoreRecipients=None, sender=None, replyTo=None, parentGroup=None):
        """
        Posts a message to the recipients and consequently sends them emails

        :param subject: Subject of the e-mail
        :type subject: str
        :param recipients: Recipients of the e-mail. Valid inputs would be tilde username or emails registered in OpenReview
        :type recipients: list[str]
        :param message: Message in the e-mail
        :type message: str
        :param ignoreRecipients: List of groups ids to be ignored from the recipient list
        :type subject: list[str]
        :param sender: Specify the from address and name of the email, the dictionary should have two keys: 'name' and 'email'
        :type sender: dict
        :param replyTo: e-mail address used when recipients reply to this message
        :type replyTo: str
        :param parentGroup: parent group recipients of e-mail belong to
        :type parentGroup: str

        :return: Contains the message that was sent to each Group
        :rtype: dict
        """
        response = requests.post(self.messages_url, json = {
            'groups': recipients,
            'subject': subject ,
            'message': message,
            'ignoreGroups': ignoreRecipients,
            'from': sender,
            'replyTo': replyTo,
            'parentGroup': parentGroup
            }, headers = self.headers)
        response = self.__handle_response(response)

        return response.json()

    def post_direct_message(self, subject, recipients, message, sender=None):
        """
        Posts a message to the recipients and consequently sends them emails

        :param subject: Subject of the e-mail
        :type subject: str
        :param recipients: Recipients of the e-mail. Valid inputs would be tilde username or emails registered in OpenReview
        :type recipients: list[str]
        :param message: Message in the e-mail
        :type message: str

        :return: Contains the message that was sent to each Group
        :rtype: dict
        """
        response = requests.post(self.messages_direct_url, json = {
            'groups': recipients,
            'subject': subject ,
            'message': message,
            'from': sender
            }, headers = self.headers)
        response = self.__handle_response(response)

        return response.json()

    def add_members_to_group(self, group, members):
        """
        Adds members to a group

        :param group: Group (or Group's id) to which the members will be added
        :type group: Group or str
        :param members: Members that will be added to the group. Members should be in a string, unicode or a list format
        :type members: str, list, unicode

        :return: Group with the members added
        :rtype: Group
        """
        def add_member(group, members):
            group_id = group if type(group) in string_types else group.id
            if members:
                response = requests.put(self.groups_url + '/members', json = {'id': group_id, 'members': members}, headers = self.headers)
                response = self.__handle_response(response)
                return Group.from_json(response.json())
            return group

        member_type = type(members)
        if member_type in string_types:
            return add_member(group, [members])
        if member_type == list:
            return add_member(group, members)
        raise OpenReviewException("add_members_to_group()- members '"+str(members)+"' ("+str(member_type)+") must be a str, unicode or list, but got " + repr(member_type) + " instead")

    def remove_members_from_group(self, group, members):
        """
        Removes members from a group

        :param group: Group (or Group's id) from which the members will be removed
        :type group: Group or str
        :param members: Members that will be removed. Members should be in a string, unicode or a list format
        :type members: str, list, unicode

        :return: Group without the members that were removed
        :type: Group
        """
        def remove_member(group, members):
            group_id = group if type(group) in string_types else group.id
            response = requests.delete(self.groups_url + '/members', json = {'id': group_id, 'members': members}, headers = self.headers)
            response = self.__handle_response(response)
            return Group.from_json(response.json())

        member_type = type(members)
        if member_type in string_types:
            return remove_member(group, [members])
        if member_type == list:
            return remove_member(group, members)

    def search_notes(self, term, content = 'all', group = 'all', source='all', limit = None, offset = None):
        """
        Searches notes based on term, content, group and source as the criteria. Unlike :meth:`~openreview.Client.get_notes`, this method uses Elasticsearch to retrieve the Notes

        :param term: Term used to look for the Notes
        :type term: str
        :param content: Specifies whether to look in all the content, authors, or keywords. Valid inputs: 'all', 'authors', 'keywords'
        :type content: str, optional
        :param group: Specifies under which Group to look. E.g. 'all', 'ICLR', 'UAI', etc.
        :type group: str, optional
        :param source: Whether to look in papers, replies or all
        :type source: str, optional
        :param limit: Maximum amount of Notes that this method will return. The limit parameter can range between 0 and 1000 inclusive. If a bigger number is provided, only 1000 Notes will be returned
        :type limit: int, optional
        :param offset: Indicates the position to start retrieving Notes. For example, if there are 10 Notes and you want to obtain the last 3, then the offset would need to be 7.
        :type offset: int, optional

        :return: List of notes
        :rtype: list[Note]
        """
        params = {
            'term': term,
            'content': content,
            'group': group,
            'source': source
        }

        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset

        response = requests.get(self.notes_url + '/search', params=tools.format_params(params), headers = self.headers)
        response = self.__handle_response(response)
        return [Note.from_json(n) for n in response.json()['notes']]

    def get_notes_by_ids(self, ids):
        response = requests.post(self.notes_url + '/search', json = { 'ids': ids }, headers = self.headers)
        response = self.__handle_response(response)
        return [Note.from_json(n) for n in response.json()['notes']]

    def get_tildeusername(self, first, last, middle = None):
        """
        Gets next possible tilde user name corresponding to the specified first, middle and last name

        :param first: First name of the user
        :type first: str
        :param last: Last name of the user
        :type last: str
        :param middle: Middle name of the user
        :type middle: str, optional

        :return: next possible tilde user name corresponding to the specified first, middle and last name
        :rtype: dict
        """

        response = requests.get(self.tilde_url, params = { 'first': first, 'last': last, 'middle': middle }, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()

    def get_messages(self, to = None, subject = None, status = None, offset = None, limit = None):
        """
        **Only for Super User**. Retrieves all the messages sent to a list of usernames or emails and/or a particular e-mail subject

        :param to: Tilde user names or emails
        :type to: list[str], optional
        :param subject: Subject of the e-mail
        :type subject: str, optional
        :param status: Commad separated list of status values corresponding to the message: delivered, bounce, droppped, etc
        :type status: str, optional

        :return: Messages that match the passed parameters
        :rtype: dict
        """

        response = requests.get(self.messages_url, params = { 'to': to, 'subject': subject, 'status': status, 'offset': offset, 'limit': limit }, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()['messages']

    def get_process_logs(self, id = None, invitation = None, status = None):
        """
        **Only for Super User**. Retrieves the logs of the process function executed by an Invitation

        :param id: Note id
        :type id: str, optional
        :param invitation: Invitation id that executed the process function that produced the logs
        :type invitation: str, optional

        :return: Logs of the process
        :rtype: dict
        """

        response = requests.get(self.process_logs_url, params = { 'id': id, 'invitation': invitation, 'status': status }, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()['logs']

    def post_invitation_edit(self, invitations, readers=None, writers=None, signatures=None, invitation=None, content=None, replacement=None):
        """
        """
        edit_json = {}
        
        if invitations is not None:
            edit_json['invitations'] = invitations

        if readers is not None:
            edit_json['readers'] = readers

        if writers is not None:
            edit_json['writers'] = writers

        if signatures is not None:
            edit_json['signatures'] = signatures                        

        if content is not None:
            edit_json['content'] = content

        if content is not None:
            edit_json['content'] = content

        if replacement is not None:
            edit_json['replacement'] = replacement

        if invitation is not None:
            edit_json['invitation'] = invitation.to_json()

        response = requests.post(self.invitation_edits_url, json = edit_json, headers = self.headers)
        response = self.__handle_response(response)

        return response.json()

    def post_note_edit(self, invitation, signatures, note=None, readers=None, writers=None):
        """
        """
        edit_json = {
            'invitation': invitation,
            'signatures': signatures,
            'note': note.to_json() if note else {}
        }

        if readers is not None:
            edit_json['readers'] = readers

        if writers is not None:
            edit_json['writers'] = writers

        response = requests.post(self.note_edits_url, json = edit_json, headers = self.headers)
        response = self.__handle_response(response)

        return response.json()

    def post_edit(self, edit):
        """
        """

        edit_json = edit.to_json()

        if 'note' in edit_json:
            response = requests.post(self.note_edits_url, json = edit_json, headers = self.headers)
        elif 'invitation' in edit_json:
            response = requests.post(self.invitation_edits_url, json = edit_json, headers = self.headers)

        response = self.__handle_response(response)

        return response.json()

    def get_jobs_status(self):
        """
        **Only for Super User**. Retrieves the jobs status of the queue

        :return: Jobs status
        :rtype: dict
        """

        response = requests.get(self.jobs_status, headers=self.headers)
        response = self.__handle_response(response)
        return response.json()

    def request_expertise(self, name, group_id, paper_invitation, alternate_match_group = None, exclusion_inv=None, model=None, baseurl=None):

        # Build entityA from group_id
        entityA = {
            'type': 'Group',
            'memberOf': group_id
        }
        if exclusion_inv:
            expertise = {'exclusion': { 'invitation': exclusion_inv }}
            entityA['expertise'] = expertise

        # Build entityB from alternate_match_group or paper_invitation
        if alternate_match_group:
            entityB = {
                'type': 'Group',
                'memberOf': alternate_match_group
            }
        else:
            entityB = {
                'type': 'Note',
                'invitation': paper_invitation
            }

        expertise_request = {
            'name': name,
            'entityA': entityA,
            'entityB': entityB,
            'model': {
                'name': model
            }
        }

        base_url = baseurl if baseurl else self.baseurl
        response = requests.post(base_url + '/expertise', json = expertise_request, headers = self.headers)
        response = self.__handle_response(response)

        return response.json()

    def request_single_paper_expertise(self, name, group_id, paper_id, model=None, baseurl=None):

        # Build entityA from group_id
        entityA = {
            'type': 'Group',
            'memberOf': group_id
        }

        # Build entityB from paper_id
        entityB = {
            'type': 'Note',
            'id': paper_id
        }

        expertise_request = {
            'name': name,
            'entityA': entityA,
            'entityB': entityB,
            'model': {
                'name': model
            }
        }

        base_url = baseurl if baseurl else self.baseurl
        if base_url.startswith('http://localhost'):
            return {}
        print('compute expertise', {'name': name, 'match_group': group_id , 'paper_id': paper_id, 'model': model})
        response = requests.post(base_url + '/expertise', json = expertise_request, headers = self.headers)
        print('response json', response.json())
        response = self.__handle_response(response)

        return response.json()

    def get_expertise_status(self, job_id, baseurl=None):

        print('get expertise status', baseurl, job_id)
        base_url = baseurl if baseurl else self.baseurl
        if base_url.startswith('http://localhost'):
            print('get expertise status localhost, return Completed')
            return { 'status': 'Completed' }
        response = requests.get(base_url + '/expertise/status', params = {'jobId': job_id}, headers = self.headers)
        response = self.__handle_response(response)

        response_json = response.json()
        print('get expertise status', response_json)
        return response_json

    def get_expertise_results(self, job_id, baseurl=None, wait_for_complete=False):

        print('get expertise results', baseurl, job_id)
        base_url = baseurl if baseurl else self.baseurl
        call_max = 500

        if base_url.startswith('http://localhost'):
            print('return expertise results localhost, return []')
            return { 'results': [] }

        if wait_for_complete:
            call_count = 0
            status_response = self.get_expertise_status(job_id, baseurl=base_url)
            status = status_response.get('status')
            while status not in ['Completed', 'Error'] and call_count < call_max:
                time.sleep(60)
                status_response = self.get_expertise_status(job_id)
                status = status_response.get('status')
                call_count += 1

            if 'Completed' == status:
                return self.get_expertise_results(job_id, baseurl=base_url)
            if 'Error' == status:
                raise OpenReviewException('There was an error computing scores, description: ' + status_response.get('description'))
            if call_count == call_max:
                raise OpenReviewException('Time out computing scores, description: ' + status_response.get('description'))
            raise OpenReviewException('Unknown error, description: ' + status_response.get('description'))
        else:
            response = requests.get(base_url + '/expertise/results', params = {'jobId': job_id}, headers = self.headers)
            response = self.__handle_response(response)
            print('return expertise results', baseurl, job_id)
            return response.json()


class Edit(object):
    """
    :param id: Edit id
    :type id: str
    :param readers: List of readers in the Edit, each reader is a Group id
    :type readers: list[str], optional
    :param writers: List of writers in the Edit, each writer is a Group id
    :type writers: list[str], optional
    :param signatures: List of signatures in the Edit, each signature is a Group id
    :type signatures: list[str], optional
    :param note: Template of the Note that will be created
    :type note: dict, optional
    :param invitation: Template of the Invitation that will be created
    :type invitation: dict, optional
    :param nonreaders: List of nonreaders in the Edit, each nonreader is a Group id
    :type nonreaders: list[str], optional
    :param cdate: Creation date
    :type cdate: int, optional
    :param ddate: Deletion date
    :type ddate: int, optional
    :param tcdate: True creation date
    :type tcdate: int, optional
    :param tmdate: Modification date
    :type tmdate: int, optional
    """
    def __init__(self,
        id = None,
        invitations = None,
        readers = None,
        writers = None,
        signatures = None,
        note = None,
        invitation = None,
        nonreaders = None,
        cdate = None,
        ddate = None,
        tauthor = None):

        self.id = id
        self.invitations = invitations
        self.cdate = cdate
        self.ddate = ddate
        self.readers = readers
        self.nonreaders = nonreaders
        self.writers = writers
        self.signatures = signatures
        self.note = note
        self.invitation = invitation
        self.tauthor = tauthor

    def __repr__(self):
        content = ','.join([("%s = %r" % (attr, value)) for attr, value in vars(self).items()])
        return 'Edit(' + content + ')'

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(vars(self))

    def to_json(self):
        """
        Converts Edit instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary.

        :return: Dictionary containing all the parameters of a Edit instance
        :rtype: dict
        """
        body = {}

        if (self.id):
            body['id'] = self.id
        if self.invitations:
            body['invitations'] = self.invitations
        if (self.readers):
            body['readers'] = self.readers
        if (self.nonreaders):
            body['nonreaders'] = self.nonreaders
        if (self.writers):
            body['writers'] = self.writers
        if (self.signatures):
            body['signatures'] = self.signatures
        if (self.note):
            body['note'] = self.note.to_json()
        if isinstance(self.invitation, Invitation):
            body['invitation'] = self.invitation.to_json()
        if isinstance(self.invitation, str):
            body['invitation'] = self.invitation
        if (self.ddate):
            body['ddate'] = self.ddate

        return body

    @classmethod
    def from_json(Edit,e):
        """
        Creates an Edit object from a dictionary that contains keys values equivalent to the name of the instance variables of the Edit class

        :param i: Dictionary containing key-value pairs, where the keys values are equivalent to the name of the instance variables in the Edit class
        :type i: dict

        :return: Edit whose instance variables contain the values from the dictionary
        :rtype: Edit
        """
        edit = Edit(e.get('id'),
            invitations = e.get('invitations'),
            cdate = e.get('cdate'),
            ddate = e.get('ddate'),
            readers = e.get('readers'),
            nonreaders = e.get('nonreaders'),
            writers = e.get('writers'),
            signatures = e.get('signatures'),
            note = Note.from_json(e['note']) if 'note' in e else None,
            invitation = e.get('invitation'),
            tauthor = e.get('tauthor')
            )

        if isinstance(edit.invitation, dict):
            edit.invitation = Invitation.from_json(edit.invitation)
        
        return edit

class Note(object):
    """
    TODO: write docs
    """
    def __init__(self,
        invitations=None,
        readers=None,
        writers=None,
        signatures=None,
        content=None,
        id=None,
        number=None,
        cdate=None,
        mdate=None,
        tcdate=None,
        tmdate=None,
        ddate=None,
        forum=None,
        replyto=None,
        nonreaders=None,
        domain=None,
        details = None):

        self.id = id
        self.number = number
        self.cdate = cdate
        self.mdate = mdate
        self.tcdate = tcdate
        self.tmdate = tmdate
        self.ddate = ddate
        self.content = content
        self.forum = forum
        self.replyto = replyto
        self.readers = readers
        self.nonreaders = nonreaders
        self.signatures = signatures
        self.writers = writers
        self.number = number
        self.details = details
        self.invitations = invitations
        self.domain = domain

    def __repr__(self):
        content = ','.join([("%s = %r" % (attr, value)) for attr, value in vars(self).items()])
        return 'Note(' + content + ')'

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(vars(self))

    def to_json(self):
        """
        Converts Note instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary.

        :return: Dictionary containing all the parameters of a Note instance
        :rtype: dict
        """
        body = {
        }
        if self.id:
            body['id'] = self.id
        if self.forum:
            body['forum'] = self.forum
        if self.replyto:
            body['replyto'] = self.replyto
        if self.content:
            body['content'] = self.content
        if self.invitations:
            body['invitations'] = self.invitations
        if self.cdate:
            body['cdate'] = self.cdate
        if self.mdate:
            body['mdate'] = self.mdate
        if self.ddate:
            body['ddate'] = self.ddate
        if self.nonreaders is not None:
            body['nonreaders'] = self.nonreaders
        if self.signatures:
            body['signatures'] = self.signatures
        if self.writers:
            body['writers'] = self.writers
        if self.readers:
            body['readers'] = self.readers
        return body

    @classmethod
    def from_json(Note,n):
        """
        Creates a Note object from a dictionary that contains keys values equivalent to the name of the instance variables of the Note class

        :param n: Dictionary containing key-value pairs, where the keys values are equivalent to the name of the instance variables in the Note class
        :type n: dict

        :return: Note whose instance variables contain the values from the dictionary
        :rtype: Note
        """
        note = Note(
        id = n.get('id'),
        number = n.get('number'),
        cdate = n.get('cdate'),
        mdate = n.get('mdate'),
        tcdate = n.get('tcdate'),
        tmdate =n.get('tmdate'),
        ddate=n.get('ddate'),
        content=n.get('content'),
        forum=n.get('forum'),
        invitations=n.get('invitations'),
        replyto=n.get('replyto'),
        readers=n.get('readers'),
        nonreaders=n.get('nonreaders'),
        signatures=n.get('signatures'),
        writers=n.get('writers'),
        details=n.get('details'),
        domain=n.get('domain')
        )
        return note

class Invitation(object):
    """
    """
    def __init__(self,
        id = None,
        invitations = None,
        domain = None,
        readers = None,
        writers = None,
        invitees = None,
        signatures = None,
        edit = None,
        edge = None,
        type = 'Note',
        noninvitees = None,
        nonreaders = None,
        web = None,
        process = None,
        preprocess = None,
        date_processes = None,
        duedate = None,
        expdate = None,
        cdate = None,
        ddate = None,
        tcdate = None,
        tmdate = None,
        minReplies = None,
        maxReplies = None,
        bulk = None,
        content = None,
        reply_forum_views = [],
        details = None):

        self.id = id
        self.invitations = invitations
        self.domain = domain
        self.cdate = cdate
        self.ddate = ddate
        self.duedate = duedate
        self.expdate = expdate
        self.readers = readers
        self.nonreaders = nonreaders
        self.writers = writers
        self.invitees = invitees
        self.noninvitees = noninvitees
        self.signatures = signatures
        self.minReplies = minReplies
        self.maxReplies = maxReplies
        self.edit = edit
        self.edge = edge
        self.type = type
        self.tcdate = tcdate
        self.tmdate = tmdate
        self.bulk = bulk
        self.details = details
        self.reply_forum_views = reply_forum_views
        self.web = web
        self.process = process
        self.preprocess = preprocess
        self.date_processes = date_processes
        self.content = content

    def __repr__(self):
        content = ','.join([("%s = %r" % (attr, value)) for attr, value in vars(self).items()])
        return 'Invitation(' + content + ')'

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(vars(self))

    def pretty_id(self):
        tokens = self.id.split('/')[-2:]
        filtered_tokens = []

        for token in tokens:
            token = token.replace('_', ' ').strip()
            if token.startswith('~'):
                token = tools.pretty_id(token)
            if token != '-':
                filtered_tokens.append(token)

        return (' ').join(filtered_tokens)

    def to_json(self):
        """
        Converts Invitation instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary.

        :return: Dictionary containing all the parameters of a Invitation instance
        :rtype: dict
        """
        body = {
            'id': self.id
        }

        if self.invitations:
            body['invitations'] = self.invitations
        
        if self.domain:
            body['domain'] = self.domain

        if self.cdate:
            body['cdate'] = self.cdate

        if self.ddate:
            body['ddate'] = self.ddate

        if self.duedate:
            body['duedate'] = self.duedate

        if self.expdate:
            body['expdate'] = self.expdate

        if self.readers:
            body['readers'] = self.readers

        if self.nonreaders:
            body['nonreaders'] = self.nonreaders

        if self.writers:
            body['writers'] = self.writers

        if self.invitees:
            body['invitees'] = self.invitees

        if self.noninvitees:
            body['noninvitees'] = self.noninvitees

        if self.signatures:
            body['signatures'] = self.signatures

        if self.reply_forum_views:
            body['reply_forum_views'] = self.reply_forum_views

        if self.content:
            body['content'] = self.content

        if  self.minReplies:
            body['minReplies']=self.minReplies
        if  self.maxReplies:
            body['maxReplies']=self.maxReplies
        if self.web:
            body['web']=self.web
        if  self.process:
            body['process']=self.process
        if  self.preprocess:
            body['preprocess']=self.preprocess
        if  self.date_processes:
            body['dateprocesses']=self.date_processes
        if self.edit is not None:
            if self.type == 'Note':
                body['edit']=self.edit
            if self.type == 'Edge':
                body['edge']=self.edit
        if self.edge:
            body['edge']=self.edge
        if self.bulk is not None:
            body['bulk']=self.bulk
        return body

    @classmethod
    def from_json(Invitation,i):
        """
        Creates an Invitation object from a dictionary that contains keys values equivalent to the name of the instance variables of the Invitation class

        :param i: Dictionary containing key-value pairs, where the keys values are equivalent to the name of the instance variables in the Invitation class
        :type i: dict

        :return: Invitation whose instance variables contain the values from the dictionary
        :rtype: Invitation
        """
        invitation = Invitation(i['id'],
            invitations = i.get('invitations'),
            domain = i.get('domain'),
            cdate = i.get('cdate'),
            ddate = i.get('ddate'),
            tcdate = i.get('tcdate'),
            tmdate = i.get('tmdate'),
            duedate = i.get('duedate'),
            expdate = i.get('expdate'),
            readers = i.get('readers'),
            nonreaders = i.get('nonreaders'),
            writers = i.get('writers'),
            invitees = i.get('invitees'),
            noninvitees = i.get('noninvitees'),
            signatures = i.get('signatures'),
            minReplies = i.get('minReplies'),
            edit = i.get('edit'),
            maxReplies = i.get('maxReplies'),
            details = i.get('details'),
            reply_forum_views = i.get('replyForumViews'),
            bulk = i.get('bulk')
            )
        if 'content' in i:
            invitation.content = i['content']
        if 'web' in i:
            invitation.web = i['web']
        if 'process' in i:
            invitation.process = i['process']
        if 'transform' in i:
            invitation.transform = i['transform']
        if 'preprocess' in i:
            invitation.preprocess = i['preprocess']
        if 'dateprocesses' in i:
            invitation.date_processes = i['dateprocesses']
        if 'edge' in i:
            invitation.edit = i['edge']
            invitation.type = 'Edge'
        return invitation

class Edge(object):
    def __init__(self, head, tail, invitation, readers=None, writers=None, signatures=None, id=None, weight=None, label=None, cdate=None, ddate=None, nonreaders=None, tcdate=None, tmdate=None, tddate=None, tauthor=None):
        self.id = id
        self.invitation = invitation
        self.head = head
        self.tail = tail
        self.weight = weight
        self.label = label
        self.cdate = cdate
        self.ddate = ddate
        self.readers = readers
        self.nonreaders = nonreaders
        self.writers = writers
        self.signatures = signatures
        self.tcdate = tcdate
        self.tmdate = tmdate
        self.tddate = tddate
        self.tauthor = tauthor

    def to_json(self):
        '''
        Returns serialized json string for a given object
        '''
        body = {
            'invitation': self.invitation,
            'head': self.head,
            'tail': self.tail,
        }
        if self.id:
            body['id'] = self.id
        if self.ddate:
            body['ddate'] = self.ddate
        if self.readers is not None:
            body['readers'] = self.readers
        if self.writers is not None:
            body['writers'] = self.writers
        if self.nonreaders is not None:
            body['nonreaders'] = self.nonreaders
        if self.signatures is not None:
            body['signatures'] = self.signatures
        if self.weight is not None:
            body['weight'] = self.weight
        if self.label is not None:
            body['label'] = self.label

        return body

    @classmethod
    def from_json(Edge, e):
        '''
        Returns a deserialized object from a json string

        :arg t: The json string consisting of a serialized object of type "Edge"
        '''
        edge = Edge(
            id = e.get('id'),
            cdate = e.get('cdate'),
            tcdate = e.get('tcdate'),
            tmdate = e.get('tmdate'),
            ddate = e.get('ddate'),
            tddate = e.get('tddate'),
            invitation = e.get('invitation'),
            readers = e.get('readers'),
            nonreaders = e.get('nonreaders'),
            writers = e.get('writers'),
            signatures = e.get('signatures'),
            head = e.get('head'),
            tail = e.get('tail'),
            weight = e.get('weight'),
            label = e.get('label'),
            tauthor=e.get('tauthor')
        )
        return edge

    def __repr__(self):
        content = ','.join([("%s = %r" % (attr, value)) for attr, value in vars(self).items()])
        return 'Edge(' + content + ')'

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(vars(self))

class Group(object):
    """
    When a user is created, it is automatically assigned to certain groups that give him different privileges. A username is also a group, therefore, groups can be members of other groups.

    :param id: id of the Group
    :type id: str
    :param readers: List of readers in the Group, each reader is a Group id
    :type readers: list[str]
    :param writers: List of writers in the Group, each writer is a Group id
    :type writers: list[str]
    :param signatories: List of signatories in the Group, each writer is a Group id
    :type signatories: list[str]
    :param signatures: List of signatures in the Group, each signature is a Group id
    :type signatures: list[str]
    :param cdate: Creation date of the Group
    :type cdate: int, optional
    :param ddate: Deletion date of the Group
    :type ddate: int, optional
    :param tcdate: true creation date of the Group
    :type tcdate: int, optional
    :param tmdate: true modification date of the Group
    :type tmdate: int, optional
    :param members: List of members in the Group, each member is a Group id
    :type members: list[str], optional
    :param nonreaders: List of nonreaders in the Group, each nonreader is a Group id
    :type nonreaders: list[str], optional
    :param web: Path to a file that contains the webfield
    :type web: optional
    :param web_string: String containing the webfield for this Group
    :type web_string: str, optional
    :param details:
    :type details: optional
    """
    def __init__(self, id, readers, writers, signatories, signatures, invitation=None, cdate = None, ddate = None, tcdate=None, tmdate=None, members = None, nonreaders = None, impersonators=None, web = None, web_string=None, anonids= None, deanonymizers=None, host=None, details = None):
        # post attributes
        self.id=id
        self.invitation=invitation
        self.cdate = cdate
        self.ddate = ddate
        self.tcdate = tcdate
        self.tmdate = tmdate
        self.writers = writers
        self.members = [] if members is None else members
        self.readers = readers
        self.nonreaders = [] if nonreaders is None else nonreaders
        self.signatures = signatures
        self.signatories = signatories
        self.anonids = anonids
        self.web=None
        self.impersonators = impersonators
        self.host = host
        if web is not None:
            with open(web) as f:
                self.web = f.read()

        if web_string:
            self.web = web_string

        self.anonids = anonids
        self.deanonymizers = deanonymizers
        self.details = details

    def __repr__(self):
        content = ','.join([("%s = %r" % (attr, value)) for attr, value in vars(self).items()])
        return 'Group(' + content + ')'

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(vars(self))


    def to_json(self):
        """
        Converts Group instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary.

        :return: Dictionary containing all the parameters of a Group instance
        :rtype: dict
        """
        body = {
            'id': self.id,
            'invitation': self.invitation,
            'cdate': self.cdate,
            'ddate': self.ddate,
            'signatures': self.signatures,
            'writers': self.writers,
            'members': self.members,
            'readers': self.readers,
            'nonreaders': self.nonreaders,
            'signatories': self.signatories,
            'impersonators': self.impersonators,
            'anonids': self.anonids,
            'deanonymizers': self.deanonymizers,
            'web': self.web,
            'host': self.host,
            'details': self.details
        }

        return body

    @classmethod
    def from_json(Group,g):
        """
        Creates a Group object from a dictionary that contains keys values equivalent to the name of the instance variables of the Group class

        :param g: Dictionary containing key-value pairs, where the keys values are equivalent to the name of the instance variables in the Group class
        :type g: dict

        :return: Group whose instance variables contain the values from the dictionary
        :rtype: Group
        """
        group = Group(g['id'],
            invitation=g.get('invitation'),
            cdate = g.get('cdate'),
            ddate = g.get('ddate'),
            tcdate = g.get('tcdate'),
            tmdate = g.get('tmdate'),
            writers = g.get('writers'),
            members = g.get('members'),
            readers = g.get('readers'),
            nonreaders = g.get('nonreaders'),
            signatories = g.get('signatories'),
            signatures = g.get('signatures'),
            anonids=g.get('anonids'),
            deanonymizers=g.get('deanonymizers'),
            impersonators=g.get('impersonators'),
            host=g.get('host'),
            details = g.get('details'))
        if 'web' in g:
            group.web = g['web']
        return group

    def add_member(self, member):
        """
        Adds a member to the group. This is done only on the object not in OpenReview. Another method like :meth:`~openreview.Group.post` is needed for the change to show in OpenReview

        :param member: Member to add to the group
        :type member: str

        :return: Group with the new member added
        :rtype: Group
        """
        if type(member) is Group:
            self.members.append(member.id)
        else:
            self.members.append(str(member))
        return self

    def remove_member(self, member):
        """
        Removes a member from the group. This is done only on the object not in OpenReview. Another method like :meth:`~openreview.Group.post` is needed for the change to show in OpenReview

        :param member: Member to remove from the group
        :type member: str

        :return: Group after the member was removed
        :rtype: Group
        """
        if type(member) is Group:
            try:
                self.members.remove(member.id)
            except(ValueError):
                pass
        else:
            try:
                self.members.remove(str(member))
            except(ValueError):
                pass
        return self

    def add_webfield(self, web):
        """
        Adds a webfield to the group

        :param web: Path to the file that contains the webfield
        :type web: str
        """
        with open(web) as f:
            self.web = f.read()

    def post(self, client):
        """
        Posts a group to OpenReview

        :param client: Client that will post the Group
        :type client: Client
        """
        client.post_group(self)


