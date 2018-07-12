#!/usr/bin/python
import requests
import pprint
import json
import os
import getpass
import re
import datetime
import builtins

class OpenReviewException(Exception):
    pass

class Client(object):

    def __init__(self, baseurl = None, username = None, password = None):
        """
        :arg baseurl: url to the host, example: https://openreview.net (should be replaced by 'host' name).

        :arg username: openreview username.

        :arg password: openreview password.
        """
        if baseurl==None:
            try:
                self.baseurl = os.environ['OPENREVIEW_BASEURL']
            except KeyError:
                self.baseurl = builtins.input('Environment variable OPENREVIEW_BASEURL not found. Please provide a base URL: ')
        else:
            self.baseurl = baseurl

        if username==None:
            try:
                self.username = os.environ['OPENREVIEW_USERNAME']
            except KeyError:
                self.username = builtins.input('Environment variable OPENREVIEW_USERNAME not found. Please provide a username: ')
        else:
            self.username = username

        if password==None:
            try:
                self.password = os.environ['OPENREVIEW_PASSWORD']
            except KeyError:
                self.password = builtins.input('Environment variable OPENREVIEW_PASSWORD not found. Please provide a password: ')
        else:
            self.password = password

        self.groups_url = self.baseurl + '/groups'
        self.login_url = self.baseurl + '/login'
        self.register_url = self.baseurl + '/register'
        self.invitations_url = self.baseurl + '/invitations'
        self.mail_url = self.baseurl + '/mail'
        self.notes_url = self.baseurl + '/notes'
        self.tags_url = self.baseurl + '/tags'
        self.profiles_url = self.baseurl + '/user/profile'
        self.reference_url = self.baseurl + '/references'
        self.tilde_url = self.baseurl + '/tildeusername'
        self.token = self.__login_user(self.username, self.password)
        self.headers = {'Authorization': 'Bearer ' + self.token, 'User-Agent': 'test-create-script'}
        self.signature = self.get_profile(self.username).id

    ## PRIVATE FUNCTIONS
    def __handle_response(self,response):
        try:
            response.raise_for_status()

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

    def __login_user(self,username=None, password=None):

        if username==None:
            try:
                username = os.environ["OPENREVIEW_USERNAME"]
            except KeyError:
                username = builtins.input("Please provide your OpenReview username (e.g. username@umass.edu): ")

        if password==None:
            try:
                password = os.environ["OPENREVIEW_PASSWORD"]
            except KeyError:
                password = getpass.getpass("Please provide your OpenReview password: ")

        self.user = {'id':username,'password':password}

        response = requests.post(self.login_url, json=self.user)
        response = self.__handle_response(response)

        return str(response.json()['token'])

    ## PUBLIC FUNCTIONS

    def register_user(self, email = None, first = None, last = None, middle = '', password = None):
        '''
        |  Registers a new user
        '''
        register_payload = {
            'email': email,
            'name': {   'first': first, 'last': last, 'middle': middle},
            'password': password
        }
        response = requests.post(self.register_url, json = register_payload, headers = self.headers)
        response = self.__handle_response(response)
        return str(response.json())

    def activate_user(self, token):
        '''
        |  Activates a newly registered user
        |  @token -- activation token
        '''
        response = requests.put(self.baseurl + '/activate/' + token, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()

    def get_activatable(self, token = None):
        '''
        |  Returns the activation token for a registered user
        '''
        response = requests.get(self.baseurl + '/activatable/' + token, params = {}, headers = self.headers)
        response = self.__handle_response(response)
        token = response.json()['activatable']['token']
        return token

    def get_group(self, id):
        """
        |  Returns a single Group by id if available
        """
        response = requests.get(self.groups_url, params = {'id':id}, headers = self.headers)
        response = self.__handle_response(response)
        g = response.json()['groups'][0]
        return Group.from_json(g)

    def get_invitation(self, id):
        """
        |  Returns a single invitation by id if available
        """
        response = requests.get(self.invitations_url, params = {'id': id}, headers = self.headers)
        response = self.__handle_response(response)
        i = response.json()['invitations'][0]
        return Invitation.from_json(i)

    def get_note(self, id):
        """
        |  Returns a single note by id if available
        """
        response = requests.get(self.notes_url, params = {'id':id}, headers = self.headers)
        response = self.__handle_response(response)
        n = response.json()['notes'][0]
        return Note.from_json(n)

    def get_tag(self, id):
        """
        |  Returns a single tag by id if available
        """
        response = requests.get(self.tags_url, params = {'id': id}, headers = self.headers)
        response = self.__handle_response(response)
        t = response.json()['tags'][0]
        return Tag.from_json(t)

    def get_profile(self, email_or_id):
        """
        |  Returns a single profile (a note) by id, if available
        """
        tildematch = re.compile('~.+')
        emailmatch = re.compile('.+@.+')
        if tildematch.match(email_or_id):
            att = 'id'
        else:
            att = 'email'
        response = requests.get(self.profiles_url, params = {att: email_or_id}, headers = self.headers)
        response = self.__handle_response(response)
        profile = response.json()['profile']
        return Note.from_json(profile)

    def get_profiles(self, email_or_id_list):
        """
        |  If the list is tilde_ids, returns an array of profiles
        |  If the list is emails, returns an array of dictionaries with 'email' and 'profile'
        """
        tildematch = re.compile('~.+')
        if len(email_or_id_list) > 0 and tildematch.match(email_or_id_list[0]):
            response = requests.post(self.baseurl + '/user/profiles', json={'ids': email_or_id_list}, headers = self.headers)
            response = self.__handle_response(response)
            return [Note.from_json(p) for p in response.json()['profiles']]
        else:
            response = requests.post(self.baseurl + '/user/profiles', json={'emails': email_or_id_list}, headers = self.headers)
            response = self.__handle_response(response)
            return { p['email'] : Note.from_json(p['profile'])
                            for p in response.json()['profiles'] }

    def post_profile(self, id, content):
        '''
        |  Posts the profile
        '''
        response = requests.put(
            self.profiles_url,
            json = { 'id': id, 'content': content },
            headers = self.headers)

        response = self.__handle_response(response)
        profile = response.json()
        return Note.from_json(profile)

    def update_profile(self, id, content):
        '''
        |  Updates the profile
        '''
        response = requests.post(
            self.profiles_url,
            json = {'id': id, 'content': content},
            headers = self.headers)

        response = self.__handle_response(response)
        profile = response.json()
        return Note.from_json(profile)

    def get_groups(self, id = None, regex = None, member = None, host = None, signatory = None):
        """
        |  Returns a list of Group objects based on the filters provided.
        """
        params = {}
        if id != None: params['id'] = id
        if regex != None: params['regex'] = regex
        if member != None: params['member'] = member
        if host != None: params['host'] = host
        if signatory != None: params['signatory'] = signatory

        response = requests.get(self.groups_url, params = params, headers = self.headers)
        response = self.__handle_response(response)
        groups = [Group.from_json(g) for g in response.json()['groups']]
        return groups

    def get_invitations(self, id = None, invitee = None, replytoNote = None, replyForum = None, signature = None, note = None, regex = None, tags = None):
        """
        |  Returns a list of Group objects based on the filters provided.
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

        response = requests.get(self.invitations_url, params=params, headers=self.headers)
        response = self.__handle_response(response)

        invitations = [Invitation.from_json(i) for i in response.json()['invitations']]
        return invitations

    def get_notes(self, id = None, paperhash = None, forum = None, invitation = None, replyto = None, tauthor = None, signature = None, writer = None, trash = None, number = None, limit = None, offset = None, mintcdate = None, details = None):
        """
        |  Returns a list of Note objects based on the filters provided.
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
        if limit != None:
            params['limit'] = limit
        if offset != None:
            params['offset'] = offset
        if mintcdate != None:
            params['mintcdate'] = mintcdate
        if details != None:
            params['details'] = details

        response = requests.get(self.notes_url, params = params, headers = self.headers)
        response = self.__handle_response(response)

        return [Note.from_json(n) for n in response.json()['notes']]

    def get_references(self, referent = None, invitation = None, mintcdate = None, limit = None, offset = None):
        """
        |  Returns a list of revisions for a note.
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

        response = requests.get(self.reference_url, params = params, headers = self.headers)
        response = self.__handle_response(response)

        return [Note.from_json(n) for n in response.json()['references']]

    def get_tags(self, id = None, invitation = None, forum = None, limit = None, offset = None):
        """
        |  Returns a list of Tag objects based on the filters provided.
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
        |  Posts the group. Upon success, returns the posted Group object.
        |  If the group is unsigned, signs it using the client's default signature.
        """
        if overwrite or not self.exists(group.id):
            if not group.signatures: group.signatures = [self.signature]
            if not group.writers: group.writers = [self.signature]
            response = requests.post(self.groups_url, json=group.to_json(), headers=self.headers)
            response = self.__handle_response(response)

        return Group.from_json(response.json())

    def post_invitation(self, invitation):
        """
        |  Posts the invitation. Upon success, returns the posted Invitation object.
        |  If the invitation is unsigned, signs it using the client's default signature.
        """
        if not invitation.signatures: invitation.signatures = [self.signature]
        if not invitation.writers: invitation.writers = [self.signature]
        response = requests.post(self.invitations_url, json = invitation.to_json(), headers = self.headers)
        response = self.__handle_response(response)

        return Invitation.from_json(response.json())

    def post_note(self, note):
        """
        |  Posts the note. Upon success, returns the posted Note object.
        |  If the note is unsigned, signs it using the client's default signature
        """
        if not note.signatures: note.signatures = [self.signature]
        response = requests.post(self.notes_url, json=note.to_json(), headers=self.headers)
        response = self.__handle_response(response)

        return Note.from_json(response.json())

    def post_tag(self, tag):
        """
        |  Posts the tag. Upon success, returns the posted Tag object.
        """
        response = requests.post(self.tags_url, json = tag.to_json(), headers = self.headers)
        response = self.__handle_response(response)

        return Tag.from_json(response.json())

    def delete_note(self, note):
        """
        |  Deletes the note and returns the deleted Note object with
        |  status = 'ok' in case of a successful deletion and an OpenReview exception otherwise.
        """
        response = requests.delete(self.notes_url, json = note.to_json(), headers = self.headers)
        response = self.__handle_response(response)
        return response.json()

    def send_mail(self, subject, recipients, message):
        '''
        |  Sends emails to a list of recipients
        '''
        response = requests.post(self.mail_url, json = {'groups': recipients, 'subject': subject , 'message': message}, headers = self.headers)
        response = self.__handle_response(response)

        return response.json()

    def add_members_to_group(self, group, members):
        '''
        |  Adds members to a group
        |  Members should be in a string, unicode or a list format
        '''
        def add_member(group,members):
            response = requests.put(self.groups_url + '/members', json = {'id': group, 'members': members}, headers = self.headers)
            response = self.__handle_response(response)
            return self.get_group(response.json()['id'])

        member_type = type(members)
        if member_type == str or member_type == unicode:
            return add_member(group.id, [members])
        if member_type == list:
            return add_member(group.id, members)
        raise OpenReviewException("add_members_to_group()- members '"+str(members)+"' ("+str(member_type)+") must be a str, unicode or list")

    def remove_members_from_group(self, group, members):
        '''
        |  Removes members from a group
        |  Members should be in a string, unicode or a list format
        '''
        def remove_member(group,members):
            response = requests.delete(self.groups_url + '/members', json = {'id': group, 'members': members}, headers = self.headers)
            response = self.__handle_response(response)
            return self.get_group(response.json()['id'])

        member_type = type(members)
        if member_type == str or member_type == unicode:
            return remove_member(group.id, [members])
        if member_type == list:
            return remove_member(group.id, members)

    def search_notes(self, term, content = 'all', group = 'all', source='all', limit = None, offset = None):
        '''
        |  Searches notes based on term, content, group and source as the criteria
        '''
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
        '''
        |  Returns next possible tilde user name corresponding to the specified first, middle and last name
        |  First and last names are required, while middle name is optional
        '''

        response = requests.get(self.tilde_url, params = { 'first': first, 'last': last, 'middle': middle }, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()

class Group(object):
    def __init__(self, id, readers, writers, signatories, signatures, cdate = None, ddate = None, members = None, nonreaders = None, web = None):
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

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.to_json())


    def to_json(self):
        '''
        |  Returns serialized json string for a given object
        '''
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
            'web': self.web
        }
        # if self.web !=None:
        #     body['web']=self.web
        return body

    @classmethod
    def from_json(Group,g):
        '''
        |  Returns a deserialized object from a json string

        |  @g: The json string consisting of a serialized object of type "Group"
        '''
        group = Group(g['id'],
            cdate = g.get('cdate'),
            ddate = g.get('ddate'),
            writers = g.get('writers'),
            members = g.get('members'),
            readers = g.get('readers'),
            nonreaders = g.get('nonreaders'),
            signatories = g.get('signatories'),
            signatures = g.get('signatures'))
        if 'web' in g:
            group.web = g['web']
        return group

    def add_member(self, member):
        '''
        |  Adds a member to the group
        '''
        if type(member) is Group:
            self.members.append(member.id)
        else:
            self.members.append(str(member))
        return self

    def remove_member(self, member):
        '''
        |  Removes a member from the group
        '''
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
        '''
        |  Adds a webfield to the group
        '''
        with open(web) as f:
            self.web = f.read()

    def post(self, client):
        '''
        |  Posts a group
        '''
        client.post_group(self)

class Invitation(object):
    def __init__(self,
        id,
        readers,
        writers,
        invitees,
        signatures,
        reply,
        noninvitees = None,
        nonreaders = None,
        web = None,
        process = None,
        duedate = None,
        cdate = None,
        rdate = None,
        ddate = None,
        tcdate = None,
        tmdate = None,
        multiReply = None,
        taskCompletionCount = None,
        transform = None):

        self.id = id
        self.cdate = cdate
        self.rdate = rdate
        self.ddate = ddate
        self.duedate = duedate
        self.readers = readers
        self.nonreaders = [] if nonreaders==None else nonreaders
        self.writers = writers
        self.invitees = invitees
        self.noninvitees = [] if noninvitees==None else noninvitees
        self.signatures = signatures
        self.multiReply = multiReply
        self.taskCompletionCount = taskCompletionCount
        self.reply = reply
        self.tcdate = tcdate
        self.tmdate = tmdate
        self.web = None
        if web != None:
            with open(web) as f:
                self.web = f.read()
        self.process = None
        if process != None:
            with open(process) as f:
                self.process = f.read()
        self.transform = None
        if transform != None:
            with open(transform) as f:
                self.transform = f.read()

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.to_json())

    def to_json(self):
        '''
        |  Returns serialized json string for a given object
        '''
        body = {
            'id': self.id,
            'cdate': self.cdate,
            'rdate': self.rdate,
            'ddate': self.ddate,
            'tcdate': self.tcdate,
            'tmdate': self.tmdate,
            'duedate': self.duedate,
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
            'transform': self.transform
        }

        if hasattr(self,'web'):
            body['web']=self.web
        if hasattr(self,'process'):
            body['process']=self.process
        return body

    @classmethod
    def from_json(Invitation,i):
        '''
        |  Returns a deserialized object from a json string

        |  @i: The json string consisting of a serialized object of type "Invitation"
        '''
        invitation = Invitation(i['id'],
            cdate = i.get('cdate'),
            rdate = i.get('rdate'),
            ddate = i.get('ddate'),
            tcdate = i.get('tcdate'),
            tmdate = i.get('tmdate'),
            duedate = i.get('duedate'),
            readers = i.get('readers'),
            nonreaders = i.get('nonreaders'),
            writers = i.get('writers'),
            invitees = i.get('invitees'),
            noninvitees = i.get('noninvitees'),
            signatures = i.get('signatures'),
            multiReply = i.get('multiReply'),
            taskCompletionCount = i.get('taskCompletionCount'),
            reply = i.get('reply')
            )
        if 'web' in i:
            invitation.web = i['web']
        if 'process' in i:
            invitation.process = i['process']
        if 'transform' in i:
            invitation.transform = i['transform']
        return invitation

class Note(object):
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
        forumContent=None,
        referent=None,
        replyto=None,
        nonreaders=None,
        overwriting=None,
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
        self.forumContent = forumContent
        self.referent = referent
        self.invitation = invitation
        self.replyto = replyto
        self.readers = readers
        self.nonreaders = [] if nonreaders==None else nonreaders
        self.signatures = signatures
        self.writers = writers
        self.number = number
        self.overwriting = overwriting
        if tauthor:
            self.tauthor = tauthor

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.to_json())

    def to_json(self):
        '''
        |  Returns serialized json string for a given object
        '''
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
            'forumContent': self.forumContent,
            'referent': self.referent,
            'invitation': self.invitation,
            'replyto': self.replyto,
            'readers': self.readers,
            'nonreaders': self.nonreaders,
            'signatures': self.signatures,
            'writers': self.writers,
            'number': self.number,
            'overwriting': self.overwriting
        }
        if hasattr(self, 'tauthor'):
            body['tauthor'] = self.tauthor
        return body

    @classmethod
    def from_json(Note,n):
        '''
        |  Returns a deserialized object from a json string

        |  @n: The json string consisting of a serialized object of type "Note"
        '''
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
        forumContent=n.get('forumContent'),
        referent=n.get('referent'),
        invitation=n.get('invitation'),
        replyto=n.get('replyto'),
        readers=n.get('readers'),
        nonreaders=n.get('nonreaders'),
        signatures=n.get('signatures'),
        writers=n.get('writers'),
        overwriting=n.get('overwriting'),
        tauthor=n.get('tauthor')
        )
        return note

class Tag(object):
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
        '''
        |  Returns serialized json string for a given object
        '''
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
        '''
        |  Returns a deserialized object from a json string

        |  @t: The json string consisting of a serialized object of type "Tag"
        '''
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

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.to_json())

