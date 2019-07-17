#!/usr/bin/python
from __future__ import absolute_import, division, print_function, unicode_literals
from deprecated.sphinx import deprecated
import sys
if sys.version_info[0] < 3:
    string_types = [str, unicode]
else:
    string_types = [str]

import requests
import pprint
import json
import os
import getpass
import re
import datetime



class OpenReviewException(Exception):
    pass

class Client(object):
    """
    :param baseurl: URL to the host, example: https://openreview.net (should be replaced by 'host' name). If none is provided, it defaults to the environment variable `OPENREVIEW_BASEURL`
    :type baseurl: str, optional
    :param username: OpenReview username. If none is provided, it defaults to the environment variable `OPENREVIEW_USERNAME`
    :type username: str, optional. If none is provided, it defaults to the environment variable `OPENREVIEW_PASSWORD`
    :param password: OpenReview password
    :type password: str, optional
    :param token: Session token. This token can be provided instead of the username and password if the user had already logged in
    :type token: str, optional
    """
    def __init__(self, baseurl = None, username = None, password = None, token= None):
        self.baseurl = baseurl
        if not self.baseurl:
            self.baseurl = os.environ.get('OPENREVIEW_BASEURL', 'http://localhost:3000')

        if not username:
            username = os.environ.get('OPENREVIEW_USERNAME')

        if not password:
            password = os.environ.get('OPENREVIEW_PASSWORD')

        self.token = token
        self.profile = None
        self.groups_url = self.baseurl + '/groups'
        self.login_url = self.baseurl + '/login'
        self.register_url = self.baseurl + '/register'
        self.invitations_url = self.baseurl + '/invitations'
        self.mail_url = self.baseurl + '/mail'
        self.notes_url = self.baseurl + '/notes'
        self.tags_url = self.baseurl + '/tags'
        self.profiles_url = self.baseurl + '/profiles'
        self.profiles_search_url = self.baseurl + '/profiles/search'
        self.reference_url = self.baseurl + '/references'
        self.tilde_url = self.baseurl + '/tildeusername'
        self.pdf_url = self.baseurl + '/pdf'
        self.messages_url = self.baseurl + '/messages'
        self.process_logs_url = self.baseurl + '/logs/process'

        self.headers = {
            'User-Agent': 'test-create-script',
            'Authorization': self.token
        }

        if username and password:
            self.login_user(username, password)

        if token:
            try:
                self.profile = self.get_profile()
            except:
                self.profile = None


    ## PRIVATE FUNCTIONS

    def __handle_token(self, response):
        self.token = str(response['token'])
        self.profile = Profile( id = response['user']['profile']['id'] )
        self.headers['Authorization'] ='Bearer ' + self.token
        return response

    def __handle_response(self,response):
        try:
            response.raise_for_status()

            if("application/json" in response.headers['content-type']):
                if 'errors' in response.json():
                    raise OpenReviewException(response.json()['errors'])
                if 'error' in response.json():
                    raise OpenReviewException(response.json()['error'])

            return response
        except requests.exceptions.HTTPError as e:
            if 'errors' in response.json():
                raise OpenReviewException(response.json()['errors'])
            else:
                raise OpenReviewException(response.json())

    ## PUBLIC FUNCTIONS

    def login_user(self,username=None, password=None):
        """
        Logs in a registered user

        :param username: OpenReview username
        :type username: str, optional
        :param password: OpenReview password
        :type password: str, optional

        :return: Dictionary containing user information and the authentication token
        :rtype: dict
        """
        user = { 'id': username, 'password': password }
        header = { 'User-Agent': 'test-create-script' }
        response = requests.post(self.login_url, headers=header, json=user)
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

    def get_note(self, id):
        """
        Get a single Note by id if available

        :param id: id of the note
        :type id: str

        :return: Note matching the passed id
        :rtype: Note
        """
        response = requests.get(self.notes_url, params = {'id':id}, headers = self.headers)
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
        response = requests.get(self.profiles_url, params = params, headers = self.headers)
        response = self.__handle_response(response)
        profiles = response.json()['profiles']
        if profiles:
            return Profile.from_json(profiles[0])
        else:
            raise OpenReviewException(['Profile not found'])

    @deprecated(version='0.9.20', reason="Use search_profiles instead")
    def get_profiles(self, email_or_id_list = None, id = None, email = None, first = None, middle = None, last = None):
        """
        Gets a list of profiles

        :param email_or_id_list: List of ids or emails
        :type email_or_id_list: list, optional
        :param id: OpenReview username id
        :type id: str, optional
        :param email: e-mail registered in OpenReview
        :type email: str, optional
        :param first: First name of the user
        :type first: str, optional
        :param middle: Middle name of the user
        :type middle: str, optional
        :param last: Last name of the user
        :type last: str, optional

        :return: List of profiles
        :rtype: list[Profile]
        """

        ## Deprecated, don't use it
        if email_or_id_list is not None:
            pure_tilde_ids = all(['~' in i for i in email_or_id_list])
            pure_emails = all(['@' in i for i in email_or_id_list])

            def get_ids_response(id_list):
                response = requests.post(self.baseurl + '/user/profiles', json={'ids': id_list}, headers = self.headers)
                response = self.__handle_response(response)
                return [Profile.from_json(p) for p in response.json()['profiles']]

            def get_emails_response(email_list):
                response = requests.post(self.baseurl + '/user/profiles', json={'emails': email_list}, headers = self.headers)
                response = self.__handle_response(response)
                return { p['email'] : Profile.from_json(p['profile'])
                    for p in response.json()['profiles'] }

            if pure_tilde_ids:
                get_response = get_ids_response
                update_result = lambda result, response: result.extend(response)
                result = []
            elif pure_emails:
                get_response = get_emails_response
                update_result = lambda result, response: result.update(response)
                result = {}
            else:
                raise OpenReviewException('the input argument cannot contain a combination of email addresses and profile IDs.')

            done = False
            offset = 0
            limit = 1000
            while not done:
                current_batch = email_or_id_list[offset:offset+limit]
                offset += limit
                response = get_response(current_batch)
                update_result(result, response)
                if len(current_batch) < limit:
                    done = True

            return result

        response = requests.get(self.profiles_url, params = { 'id': id, 'email': email, 'first': first, 'middle': middle, 'last': last }, headers = self.headers)
        response = self.__handle_response(response)
        return [Profile.from_json(p) for p in response.json()['profiles']]

    def search_profiles(self, emails = None, ids = None, term = None, first = None, middle = None, last = None):
        """
        Gets a list of profiles using either their ids or corresponding emails

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

        :return: List of profiles
        :rtype: list[Profile]
        """

        if term:
            response = requests.get(self.profiles_search_url, params = { 'term': term }, headers = self.headers)
            response = self.__handle_response(response)
            return [Profile.from_json(p) for p in response.json()['profiles']]

        if emails:
            response = requests.post(self.profiles_search_url, json = {'emails': emails}, headers = self.headers)
            response = self.__handle_response(response)
            return { p['email'] : Profile.from_json(p)
                for p in response.json()['profiles'] }

        if ids:
            response = requests.post(self.profiles_search_url, json = {'ids': ids}, headers = self.headers)
            response = self.__handle_response(response)
            return [Profile.from_json(p) for p in response.json()['profiles']]

        if first or middle or last:
            response = requests.get(self.profiles_url, params = {'first': first, 'middle': middle, 'last': last}, headers = self.headers)
            response = self.__handle_response(response)
            return [Profile.from_json(p) for p in response.json()['profiles']]


        return []

    def get_pdf(self, id):
        """
        Gets the binary content of a pdf using the provided note id
        If the pdf is not found then this returns an error message with "status":404

        :param id: Note id of the pdf
        :type id: str

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

        response = requests.get(self.pdf_url, params = params, headers = headers)
        response = self.__handle_response(response)
        return response.content

    def put_pdf(self, fname):
        """
        Uploads a pdf to the openreview server

        :param fname: Path to the pdf
        :type fname: str

        :return: A relative URL for the uploaded pdf
        :rtype: str
        """
        params = {}
        params['id'] = id

        headers = self.headers.copy()
        headers['content-type'] = 'application/pdf'

        with open(fname, 'rb') as f:
            response = requests.put(self.pdf_url, files={'data': f}, headers = headers)

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

    def get_groups(self, id = None, regex = None, member = None, signatory = None, limit = None, offset = None):
        """
        Gets list of Group objects based on the filters provided. The Groups that will be returned match all the criteria passed in the parameters.

        :param id: id of the Group
        :type id: str, optional
        :param regex: Regex that matches several Group ids
        :type regex: str, optional
        :param member: Groups that contain this member
        :type member: str, optional
        :param signatory: Groups that contain this signatory
        :type signatory: str, optional
        :param limit: Maximum amount of Groups that this method will return. The limit parameter can range between 0 and 1000 inclusive. If a bigger number is provided, only 1000 Groups will be returned
        :type limit: int, optional
        :param offset: Indicates the position to start retrieving Groups. For example, if there are 10 Groups and you want to obtain the last 3, then the offset would need to be 7.
        :type offset: int, optional

        :return: List of Groups
        :rtype: list[Group]
        """
        params = {}
        if id != None: params['id'] = id
        if regex != None: params['regex'] = regex
        if member != None: params['member'] = member
        if signatory != None: params['signatory'] = signatory
        params['limit'] = limit
        params['offset'] = offset

        response = requests.get(self.groups_url, params = params, headers = self.headers)
        response = self.__handle_response(response)
        groups = [Group.from_json(g) for g in response.json()['groups']]
        return groups

    def get_invitations(self, id = None, invitee = None, replytoNote = None, replyForum = None, signature = None, note = None, regex = None, tags = None, limit = None, offset = None, minduedate = None, duedate = None, pastdue = None, replyto = None, details = None, expired = None):
        """
        Gets list of Invitation objects based on the filters provided. The Invitations that will be returned match all the criteria passed in the parameters.

        :param id: id of the Invitation
        :type id: str, optional
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
        :param regex: Invitation ids that match this regex
        :type regex: str, optional
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
        if id!=None:
            params['id'] = id
        if invitee!=None:
            params['invitee'] = invitee
        if replytoNote!=None:
            params['replytoNote'] = replytoNote
        if replyForum!=None:
            params['replyForum'] = replyForum
        if signature!=None:
            params['signature'] = signature
        if note!=None:
            params['note']=note
        if regex:
            params['regex'] = regex
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

        response = requests.get(self.invitations_url, params=params, headers=self.headers)
        response = self.__handle_response(response)

        invitations = [Invitation.from_json(i) for i in response.json()['invitations']]
        return invitations

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
            sort = None):
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
        if id != None:
            params['id'] = id
        if paperhash != None:
            params['paperhash'] = paperhash
        if forum != None:
            params['forum'] = forum
        if invitation != None:
            params['invitation'] = invitation
        if replyto != None:
            params['replyto'] = replyto
        if tauthor != None:
            params['tauthor'] = tauthor
        if signature != None:
            params['signature'] = signature
        if writer != None:
            params['writer'] = writer
        if trash == True:
            params['trash']=True
        if number != None:
            params['number'] = number
        if content != None:
            for k in content:
                params['content.' + k] = content[k]
        if limit != None:
            params['limit'] = limit
        if offset != None:
            params['offset'] = offset
        if mintcdate != None:
            params['mintcdate'] = mintcdate
        if details != None:
            params['details'] = details
        params['sort'] = sort
        params['original'] = original

        response = requests.get(self.notes_url, params = params, headers = self.headers)
        response = self.__handle_response(response)

        return [Note.from_json(n) for n in response.json()['notes']]

    def get_references(self, referent = None, invitation = None, mintcdate = None, limit = None, offset = None, original = False):
        """
        Gets a list of revisions for a note. The revisions that will be returned match all the criteria passed in the parameters.

        :param referent: A Note ID. If provided, returns references whose "referent" value is this Note ID.
        :type referent: str, optional
        :param invitation: An Invitation ID. If provided, returns references whose "invitation" field is this Invitation ID.
        :type invitation: str, optional
        :param mintcdate: Represents an Epoch time timestamp, in milliseconds. If provided, returns references
            whose "true creation date" (tcdate) is at least equal to the value of mintcdate.
        :type mintcdate: int, optional
        :param bool original: If True then get_references will additionally return the references to the original note.
        :type offset: int, optional
        :type original: bool, optional

        :return: List of revisions
        :rtype: list[Note]
        """
        params = {}
        if referent != None:
            params['referent'] = referent
        if invitation != None:
            params['invitation'] = invitation
        if mintcdate != None:
            params['mintcdate'] = mintcdate
        if limit != None:
            params['limit'] = limit
        if offset != None:
            params['offset'] = offset
        if original == True:
            params['original'] = "true"

        response = requests.get(self.reference_url, params = params, headers = self.headers)
        response = self.__handle_response(response)

        return [Note.from_json(n) for n in response.json()['references']]

    def get_tags(self, id = None, invitation = None, forum = None, limit = None, offset = None):
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

        if id != None:
            params['id'] = id
        if forum != None:
            params['forum'] = forum
        if invitation != None:
            params['invitation'] = invitation
        if limit != None:
            params['limit'] = limit
        if offset != None:
            params['offset'] = offset

        response = requests.get(self.tags_url, params = params, headers = self.headers)
        response = self.__handle_response(response)

        return [Tag.from_json(t) for t in response.json()['tags']]

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

    def send_mail(self, subject, recipients, message):
        """
        Posts a message to the recipients and consequently sends them emails as well

        :param subject: Subject of the e-mail
        :type subject: str
        :param recipients: Recipients of the e-mail. Valid inputs would be tilde username or emails registered in OpenReview
        :type recipients: list[str]
        :param message: Message in the e-mail
        :type message: str

        :return: Contains the message that was sent to each Group
        :rtype: dict
        """
        response = requests.post(self.mail_url, json = {'groups': recipients, 'subject': subject , 'message': message}, headers = self.headers)
        response = self.__handle_response(response)

        return response.json()

    def add_members_to_group(self, group, members):
        """
        Adds members to a group

        :param group: Group to which the members will be added
        :type group: Group
        :param members: Members that will be added to the group. Members should be in a string, unicode or a list format
        :type members: str, list, unicode

        :return: Group with the members added
        :rtype: Group
        """
        def add_member(group, members):
            if members:
                response = requests.put(self.groups_url + '/members', json = {'id': group.id, 'members': members}, headers = self.headers)
                response = self.__handle_response(response)
                return Group.from_json(response.json())
            else:
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

        :param group: Group from which the members will be removed
        :type group: Group
        :param members: Members that will be removed. Members should be in a string, unicode or a list format
        :type members: str, list, unicode

        :return: Group without the members that were removed
        :type: Group
        """
        def remove_member(group,members):
            response = requests.delete(self.groups_url + '/members', json = {'id': group, 'members': members}, headers = self.headers)
            response = self.__handle_response(response)
            return Group.from_json(response.json())

        member_type = type(members)
        if member_type in string_types:
            return remove_member(group.id, [members])
        if member_type == list:
            return remove_member(group.id, members)

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

        if limit != None:
            params['limit'] = limit
        if offset != None:
            params['offset'] = offset

        response = requests.get(self.notes_url + '/search', params = params, headers = self.headers)
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

    def get_messages(self, to = None, subject = None):
        """
        **Only for Super User**. Retrieves all the messages sent to a list of usernames or emails and/or a particular e-mail subject

        :param to: Tilde user names or emails
        :type to: list[str], optional
        :param subject: Subject of the e-mail
        :type subject: str, optional

        :return: Messages that match the passed parameters
        :rtype: dict
        """

        response = requests.get(self.messages_url, params = { 'to': to, 'subject': subject }, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()['messages']

    def get_process_logs(self, id = None, invitation = None):
        """
        **Only for Super User**. Retrieves the logs of the process function executed by an Invitation

        :param id: Note id
        :type id: str, optional
        :param invitation: Invitation id that executed the process function that produced the logs
        :type invitation: str, optional

        :return: Logs of the process
        :rtype: dict
        """

        response = requests.get(self.process_logs_url, params = { 'id': id, 'invitation': invitation }, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()['logs']


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
    :param members: List of members in the Group, each member is a Group id
    :type members: list[str], optional
    :param nonreaders: List of nonreaders in the Group, each nonreader is a Group id
    :type nonreaders: list[str], optional
    :param web: Path to a file that contains the webfield
    :type web: optional
    :param details:
    :type details: optional
    """
    def __init__(self, id, readers, writers, signatories, signatures, cdate = None, ddate = None, members = None, nonreaders = None, web = None, details = None):
        # post attributes
        self.id=id
        self.cdate = cdate
        self.ddate = ddate
        self.writers = writers
        self.members = [] if members==None else members
        self.readers = readers
        self.nonreaders = [] if nonreaders==None else nonreaders
        self.signatures = signatures
        self.signatories = signatories
        self.web=None
        if web != None:
            with open(web) as f:
                self.web = f.read()
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
            'cdate': self.cdate,
            'ddate': self.ddate,
            'signatures': self.signatures,
            'writers': self.writers,
            'members': self.members,
            'readers': self.readers,
            'nonreaders': self.nonreaders,
            'signatories': self.signatories,
            'web': self.web,
            'details': self.details
        }
        # if self.web !=None:
        #     body['web']=self.web
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
            cdate = g.get('cdate'),
            ddate = g.get('ddate'),
            writers = g.get('writers'),
            members = g.get('members'),
            readers = g.get('readers'),
            nonreaders = g.get('nonreaders'),
            signatories = g.get('signatories'),
            signatures = g.get('signatures'),
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

class Invitation(object):
    """
    :param id: Invitation id
    :type id: str
    :param readers: List of readers in the Invitation, each reader is a Group id
    :type readers: list[str], optional
    :param writers: List of writers in the Invitation, each writer is a Group id
    :type writers: list[str], optional
    :param invitees: List of invitees in the Invitation, each invitee is a Group id
    :type invitees: list[str], optional
    :param signatures: List of signatures in the Invitation, each signature is a Group id
    :type signatures: list[str], optional
    :param reply: Template of the Note that will be created
    :type reply: dict, optional
    :param super: Parent Invitation id
    :type super: str, optional
    :param noninvitees: List of noninvitees in the Invitation, each noninvitee is a Group id
    :type noninvitees: list[str], optional
    :param nonreaders: List of nonreaders in the Invitation, each nonreader is a Group id
    :type nonreaders: list[str], optional
    :param web: Path to a file containing a webfield
    :type web: str, optional
    :param process: Path to a file containing the process function
    :type process: str, optional
    :param process_string: String containin the process function
    :type process_string: str, optional
    :param duedate: Due date
    :type duedate: int, optional
    :param expdate: Expiration date
    :type expdate: int, optional
    :param cdate: Creation date
    :type cdate: int, optional
    :param rdate: This field is never used
    :type rdate: int, optional
    :param ddate: Deletion date
    :type ddate: int, optional
    :param tcdate: True creation date
    :type tcdate: int, optional
    :param tmdate: Modification date
    :type tmdate: int, optional
    :param multiReply: If true, allows for multiple Notes created from this Invitation (e.g. comments in a forum), otherwise, only one Note may be created (e.g. paper submission)
    :type multiReply: bool, optional
    :param taskCompletionCount: Keeps count of the number of times the Invitation has been used
    :type taskCompletionCount: int, optional
    :param transform: Path to a file that contains the transform function
    :type transform: str, optional
    :param details:
    :type details: dict, optional
    """
    def __init__(self,
        id,
        readers = None,
        writers = None,
        invitees = None,
        signatures = None,
        reply = None,
        super = None,
        noninvitees = None,
        nonreaders = None,
        web = None,
        process = None,
        process_string = None,
        duedate = None,
        expdate = None,
        cdate = None,
        rdate = None,
        ddate = None,
        tcdate = None,
        tmdate = None,
        multiReply = None,
        taskCompletionCount = None,
        transform = None,
        details = None):

        self.id = id
        self.super = super
        self.cdate = cdate
        self.rdate = rdate
        self.ddate = ddate
        self.duedate = duedate
        self.expdate = expdate
        self.readers = readers
        self.nonreaders = nonreaders
        self.writers = writers
        self.invitees = invitees
        self.noninvitees = noninvitees
        self.signatures = signatures
        self.multiReply = multiReply
        self.taskCompletionCount = taskCompletionCount
        self.reply = reply
        self.tcdate = tcdate
        self.tmdate = tmdate
        self.details = details
        self.web = None
        self.process = None
        if web != None:
            with open(web) as f:
                self.web = f.read()
        if process != None:
            with open(process) as f:
                self.process = f.read()
        self.transform = None
        if transform != None:
            with open(transform) as f:
                self.transform = f.read()
        if process_string:
            self.process = process_string

    def __repr__(self):
        content = ','.join([("%s = %r" % (attr, value)) for attr, value in vars(self).items()])
        return 'Invitation(' + content + ')'

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(vars(self))

    def to_json(self):
        """
        Converts Invitation instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary.

        :return: Dictionary containing all the parameters of a Invitation instance
        :rtype: dict
        """
        body = {
            'id': self.id,
            'super': self.super,
            'cdate': self.cdate,
            'rdate': self.rdate,
            'ddate': self.ddate,
            'tcdate': self.tcdate,
            'tmdate': self.tmdate,
            'duedate': self.duedate,
            'expdate': self.expdate,
            'readers': self.readers,
            'nonreaders': self.nonreaders,
            'writers': self.writers,
            'invitees': self.invitees,
            'noninvitees': self.noninvitees,
            'signatures': self.signatures,
            'multiReply': self.multiReply,
            'taskCompletionCount': self.taskCompletionCount,
            'reply': self.reply,
            'process': self.process,
            'web': self.web,
            'transform': self.transform,
            'details': self.details
        }

        if hasattr(self,'web'):
            body['web']=self.web
        if hasattr(self,'process'):
            body['process']=self.process
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
            super = i.get('super'),
            cdate = i.get('cdate'),
            rdate = i.get('rdate'),
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
            multiReply = i.get('multiReply'),
            taskCompletionCount = i.get('taskCompletionCount'),
            reply = i.get('reply'),
            details = i.get('details')
            )
        if 'web' in i:
            invitation.web = i['web']
        if 'process' in i:
            invitation.process = i['process']
        if 'transform' in i:
            invitation.transform = i['transform']
        return invitation

class Note(object):
    """
    :param invitation: Invitation id
    :type invitation: str
    :param readers: List of readers in the Invitation, each reader is a Group id
    :type readers: list[str]
    :param writers: List of writers in the Invitation, each writer is a Group id
    :type writers: list[str]
    :param signatures: List of signatures in the Invitation, each signature is a Group id
    :type signatures: list[str]
    :param content: Content of the Note
    :type content: dict
    :param id: Note id
    :type id: str, optional
    :param original: If this Note is a blind copy of a Note, then this contains the id of that Note
    :type original: str, optional
    :param number: Note number. E.g. when the Note is a paper submission, this value is the paper number
    :type number: int, optional
    :param cdate: Creation date
    :type cdate: int, optional
    :param tcdate: True creation date
    :type tcdate: int, optional
    :param tmdate: Modification date
    :type tmdate: int, optional
    :param ddate: Deletion date
    :type ddate: int, optional
    :param forum: Forum id
    :type forum: str, optional
    :param referent: If this Note is used as a ref, this field points to the Profile
    :type referent: str, optional
    :param replyto: A Note ID. If provided, returns Notes whose replyto field matches the given ID
    :type replyto: str, optional
    :param nonreaders: List of nonreaders in the Invitation, each nonreader is a Group id
    :type nonreaders: list[str], optional
    :param details:
    :type details: dict, optional
    :param tauthor: True author
    :type tauthor: str, optional
    """
    def __init__(self,
        invitation,
        readers,
        writers,
        signatures,
        content,
        id=None,
        original=None,
        number=None,
        cdate=None,
        tcdate=None,
        tmdate=None,
        ddate=None,
        forum=None,
        referent=None,
        replyto=None,
        nonreaders=None,
        details = None,
        tauthor=None):

        self.id = id
        self.original = original
        self.number = number
        self.cdate = cdate
        self.tcdate = tcdate
        self.tmdate = tmdate
        self.ddate = ddate
        self.content = content
        self.forum = forum
        self.referent = referent
        self.invitation = invitation
        self.replyto = replyto
        self.readers = readers
        self.nonreaders = [] if nonreaders==None else nonreaders
        self.signatures = signatures
        self.writers = writers
        self.number = number
        self.details = details
        if tauthor:
            self.tauthor = tauthor

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
            'id': self.id,
            'original': self.original,
            'cdate': self.cdate,
            'tcdate': self.tcdate,
            'tmdate': self.tmdate,
            'ddate': self.ddate,
            'number': self.number,
            'content': self.content,
            'forum': self.forum,
            'referent': self.referent,
            'invitation': self.invitation,
            'replyto': self.replyto,
            'readers': self.readers,
            'nonreaders': self.nonreaders,
            'signatures': self.signatures,
            'writers': self.writers,
            'number': self.number,
            'details': self.details
        }
        if hasattr(self, 'tauthor'):
            body['tauthor'] = self.tauthor
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
        original = n.get('original'),
        number = n.get('number'),
        cdate = n.get('cdate'),
        tcdate = n.get('tcdate'),
        tmdate =n.get('tmdate'),
        ddate=n.get('ddate'),
        content=n.get('content'),
        forum=n.get('forum'),
        referent=n.get('referent'),
        invitation=n.get('invitation'),
        replyto=n.get('replyto'),
        readers=n.get('readers'),
        nonreaders=n.get('nonreaders'),
        signatures=n.get('signatures'),
        writers=n.get('writers'),
        details=n.get('details'),
        tauthor=n.get('tauthor')
        )
        return note

class Tag(object):
    """
    :param tag: Content of the tag
    :type tag: str
    :param invitation: Invitation id
    :type invitation: str
    :param readers: List of readers in the Invitation, each reader is a Group id
    :type readers: list[str]
    :param signatures: List of signatures in the Invitation, each signature is a Group id
    :type signatures: list[str]
    :param id: Tag id
    :type id: str, optional
    :param cdate: Creation date
    :type cdate: int, optional
    :param tcdate: True creation date
    :type tcdate: int, optional
    :param ddate: Deletion date
    :type ddate: int, optional
    :param forum: Forum id
    :type forum: str, optional
    :param replyto: Note id
    :type replyto: list[str], optional
    :param nonreaders: List of nonreaders in the Invitation, each nonreader is a Group id
    :type nonreaders: list[str], optional
    """
    def __init__(self, tag, invitation, readers, signatures, id=None, cdate=None, tcdate=None, ddate=None, forum=None, replyto=None, nonreaders=None):
        self.id = id
        self.cdate = cdate
        self.tcdate = tcdate
        self.ddate = ddate
        self.tag = tag
        self.forum = forum
        self.invitation = invitation
        self.replyto = replyto
        self.readers = readers
        self.nonreaders = [] if nonreaders==None else nonreaders
        self.signatures = signatures

    def to_json(self):
        """
        Converts Tag instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary.

        :return: Dictionary containing all the parameters of a Tag instance
        :rtype: dict
        """
        return {
            'id': self.id,
            'cdate': self.cdate,
            'tcdate': self.tcdate,
            'ddate': self.ddate,
            'tag': self.tag,
            'forum': self.forum,
            'invitation': self.invitation,
            'replyto': self.replyto,
            'readers': self.readers,
            'nonreaders': self.nonreaders,
            'signatures': self.signatures
        }

    @classmethod
    def from_json(Tag, t):
        """
        Creates a Tag object from a dictionary that contains keys values equivalent to the name of the instance variables of the Tag class

        :param n: Dictionary containing key-value pairs, where the keys values are equivalent to the name of the instance variables in the Tag class
        :type n: dict

        :return: Tag whose instance variables contain the values from the dictionary
        :rtype: Tag
        """
        tag = Tag(
            id = t.get('id'),
            cdate = t.get('cdate'),
            tcdate = t.get('tcdate'),
            ddate = t.get('ddate'),
            tag = t.get('tag'),
            forum = t.get('forum'),
            invitation = t.get('invitation'),
            replyto = t.get('replyto'),
            readers = t.get('readers'),
            nonreaders = t.get('nonreaders'),
            signatures = t.get('signatures'),
        )
        return tag

    def __repr__(self):
        content = ','.join([("%s = %r" % (attr, value)) for attr, value in vars(self).items()])
        return 'Tag(' + content + ')'

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(vars(self))


class Profile(object):
    """
    :param id: Profile id
    :type id: str, optional
    :param tcdate: True creation date
    :type tcdate: int, optional
    :param tmdate: Modification date
    :type tmdate: int, optional
    :param referent: If this is a ref, it contains the Profile id that it points to
    :type referent: str, optional
    :param packaging: Contains previous versions of this Profile
    :type packaging: dict, optional
    :param invitation: Invitation id
    :type invitation: str, optional
    :param readers: List of readers in the Invitation, each reader is a Group id
    :type readers: str, optional
    :param nonreaders: List of nonreaders in the Invitation, each nonreader is a Group id
    :type nonreaders: str, optional
    :param signatures: List of signatures in the Invitation, each signature is a Group id
    :type signatures: str, optional
    :param writers: List of writers in the Invitation, each writer is a Group id
    :type writers: str, optional
    :param content: Dictionary containing the information of the Profile
    :type content: dict, optional
    :param metaContent: Contains information of the entities that have changed the Profile
    :type metaContent: dict, optional
    :param active: If true, the Profile is active in OpenReview
    :type active: bool, optional
    :param password: If true, the Profile has a password, otherwise, it was automatically created and the person that it belongs to has not set a password yet
    :type password: bool, optional
    :param tauthor: True author
    :type tauthor: str, optional
    """
    def __init__(self, id=None, active=None, password=None, number=None, tcdate=None, tmdate=None, referent=None, packaging=None, invitation=None, readers=None, nonreaders=None, signatures=None, writers=None, content=None, metaContent=None, tauthor=None):
        self.id = id
        self.number = number
        self.tcdate = tcdate
        self.tmdate = tmdate
        self.referent = referent
        self.packaging = packaging
        self.invitation = invitation
        self.readers = readers
        self.nonreaders = nonreaders
        self.signatures = signatures
        self.writers = writers
        self.content = content
        self.metaContent = metaContent
        self.active = active
        self.password = password
        if tauthor:
            self.tauthor = tauthor

    def __repr__(self):
        content = ','.join([("%s = %r" % (attr, value)) for attr, value in vars(self).items()])
        return 'Profile(' + content + ')'

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(vars(self))

    def to_json(self):
        """
        Converts Profile instance to a dictionary. The instance variable names are the keys and their values the values of the dictinary.

        :return: Dictionary containing all the parameters of a Profile instance
        :rtype: dict
        """
        body = {
            'id': self.id,
            'number': self.number,
            'tcdate': self.tcdate,
            'tmdate': self.tmdate,
            'referent': self.referent,
            'packaging': self.packaging,
            'invitation': self.invitation,
            'readers': self.readers,
            'nonreaders': self.nonreaders,
            'signatures': self.signatures,
            'writers': self.writers,
            'content': self.content,
            'metaContent': self.metaContent,
            'active': self.active,
            'password': self.password
        }
        if hasattr(self, 'tauthor'):
            body['tauthor'] = self.tauthor
        return body

    @classmethod
    def from_json(Profile,n):
        """
        Creates a Profile object from a dictionary that contains keys values equivalent to the name of the instance variables of the Profile class

        :param i: Dictionary containing key-value pairs, where the keys values are equivalent to the name of the instance variables in the Profile class
        :type i: dict

        :return: Profile whose instance variables contain the values from the dictionary
        :rtype: Profile
        """
        profile = Profile(
        id = n.get('id'),
        active = n.get('active'),
        password = n.get('password'),
        number = n.get('number'),
        tcdate = n.get('tcdate'),
        tmdate=n.get('tmdate'),
        referent=n.get('referent'),
        packaging=n.get('packaging'),
        invitation=n.get('invitation'),
        readers=n.get('readers'),
        nonreaders=n.get('nonreaders'),
        signatures=n.get('signatures'),
        writers=n.get('writers'),
        content=n.get('content'),
        metaContent=n.get('metaContent'),
        tauthor=n.get('tauthor')
        )
        return profile

