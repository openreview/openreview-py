#!/usr/bin/python
import requests

import json
import os
import getpass
import ConfigParser
import re
from Crypto.Hash import HMAC, SHA256

class OpenReviewException(Exception):
    pass

class Client(object):

    def __init__(self, baseurl = None, process_dir = '../process/', webfield_dir = '../webfield/', username = None, password = None):
        """CONSTRUCTOR DOCSTRING"""
        if baseurl==None:
            try:
                self.baseurl = os.environ['OPENREVIEW_BASEURL']
            except KeyError:
                self.baseurl = raw_input('OPENREVIEW_BASEURL not found. Please provide a base URL: ')
                #self.baseurl = 'http://localhost:3000'
        else:
            self.baseurl = baseurl

        if username==None:
            try:
                self.username = os.environ['OPENREVIEW_USERNAME']
            except KeyError:
                self.username = raw_input('OPENREVIEW_USERNAME not found. Please provide a username: ')
                #raise OpenReviewException('No username found. Please provide username or set environment variable OPENREVIEW_USERNAME.')
        else:
            self.username = username

        if password==None:
            try:
                self.password = os.environ['OPENREVIEW_PASSWORD']
            except KeyError:
                self.password = raw_input('OPENREVIEW_PASSWORD not found. Please provide a password: ')
                #raise OpenReviewException('No password found. Please provide password or set environment variable OPENREVIEW_PASSWORD.')
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
            for k,v in response.json().iteritems():
                raise OpenReviewException(str(v))

    def __login_user(self,username=None, password=None):

        if username==None:
            try:
                username = os.environ["OPENREVIEW_USERNAME"]
            except KeyError:
                username = raw_input("Please provide your OpenReview username (e.g. username@umass.edu): ")

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

    def get_hash(self, data, secret):
        """Gets the hash of a piece of data given a secret value

        Keyword arguments:
        data -- the data to be encrypted
        secret -- the secret value used to encrypt the data
        """
        _hash = HMAC.new(secret, msg=data, digestmod=SHA256).hexdigest()
        return _hash

    def create_dummy(self, email = None, first = None, last = None, password = None, secure_activation = True):
        self.register_user(email = email,first = first, last = last, password = password)

        if secure_activation:
            token = '%s' % raw_input('enter the activation token: ')
        else:
            token = self.get_activatable(token = email)

        user = self.activate_user(token = token)
        return user

    def register_user(self, email = None, first = None, last = None, middle = '', password = None):
        register_payload = {
            'email': email,
            'name': {   'first': first, 'last': last, 'middle': middle},
            'password': password
        }
        response = requests.post(self.register_url, json = register_payload, headers = self.headers)
        response = self.__handle_response(response)
        return str(response.json())

    def activate_user(self, token):
        response = requests.put(self.baseurl + '/activate/' + token, headers = self.headers)
        response = self.__handle_response(response)
        return response.json()

    def get_activatable(self, token = None):
        response = requests.get(self.baseurl + '/activatable/' + token, params = {}, headers = self.headers)
        response = __handle_response(response)
        token = response.json()['activatable']['token']
        return token

    def get_group(self, id):
        """Returns a single Group by id if available"""
        response = requests.get(self.groups_url, params = {'id':id}, headers = self.headers)
        response = self.__handle_response(response)
        g = response.json()['groups'][0]
        return Group.from_json(g)

    def get_invitation(self, id):
        """Returns a single invitation by id if available"""
        response = requests.get(self.invitations_url, params = {'id': id}, headers = self.headers)
        response = self.__handle_response(response)
        i = response.json()['invitations'][0]
        return Invitation.from_json(i)

    def get_note(self, id):
        """Returns a single note by id if available"""
        response = requests.get(self.notes_url, params = {'id':id}, headers = self.headers)
        response = self.__handle_response(response)
        n = response.json()['notes'][0]
        return Note.from_json(n)

    def get_tag(self, id):
        """Returns a single tag by id if available"""
        response = requests.get(self.tags_url, params = {'id': id}, headers = self.headers)
        response = self.__handle_response(response)
        t = response.json()['tags'][0]
        return Tag.from_json(t)

    def get_profile(self, email_or_id):
        """Returns a single profile (a note) by id, if available"""
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

    def get_groups(self, prefix = None, regex = None, member = None, host = None, signatory = None):
        """Returns a list of Group objects based on the filters provided."""
        params = {}
        if prefix != None: params['regex'] = prefix+'.*'
        if regex != None: params['regex'] = regex
        if member != None: params['member'] = member
        if host != None: params['host'] = host
        if signatory != None: params['signatory'] = signatory

        response = requests.get(self.groups_url, params = params, headers = self.headers)
        response = self.__handle_response(response)
        groups = [Group.from_json(g) for g in response.json()['groups']]
        groups.sort(key = lambda x: x.id)
        return groups


    def get_invitations(self, id = None, invitee = None, replytoNote = None, replyForum = None, signature = None, note = None, regex = None, tags = None):
        """Returns a list of Group objects based on the filters provided."""
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
        invitations.sort(key = lambda x: x.id)
        return invitations



    def get_notes(self, id = None, forum = None, invitation = None, replyto = None, tauthor = None, signature = None, writer = None, includeTrash = None, number = None):
        """Returns a list of Note objects based on the filters provided."""
        params = {}
        if id != None:
            params['id'] = id
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
        if includeTrash == True:
            params['trash']=True
        if number != None:
            params['number'] = number

        response = requests.get(self.notes_url, params = params, headers = self.headers)
        response = self.__handle_response(response)

        return [Note.from_json(n) for n in response.json()['notes']]


    def get_tags(self, id = None, invitation = None, forum = None):
        """Returns a list of Tag objects based on the filters provided."""
        params = {}

        if id != None:
            params['id'] = id
        if forum != None:
            params['forum'] = forum
        if invitation != None:
            params['invitation'] = invitation

        response = requests.get(self.tags_url, params = params, headers = self.headers)
        response = self.__handle_response(response)

        return [Tag.from_json(t) for t in response.json()['tags']]

    def exists(self, groupid):
        try:
            self.get_group(groupid)
        except OpenReviewException:
            return False
        return True


    def post_group(self, group, overwrite = True):
        """
        Posts the group. Upon success, returns the posted Group object.
        If the group is unsigned, signs it using the client's default signature.
        """
        if overwrite or not self.exists(group.id):
            if not group.signatures: group.signatures = [self.signature]
            if not group.writers: group.writers = [self.signature]
            response = requests.post(self.groups_url, json=group.to_json(), headers=self.headers)
            response = self.__handle_response(response)

        return self.get_group(group.id)


    def post_invitation(self, invitation):
        """
        Posts the invitation. Upon success, returns the posted Invitation object.
        If the invitation is unsigned, signs it using the client's default signature.
        """
        if not invitation.signatures: invitation.signatures = [self.signature]
        if not invitation.writers: invitation.writers = [self.signature]
        response = requests.post(self.invitations_url, json = invitation.to_json(), headers = self.headers)
        response = self.__handle_response(response)

        return self.get_invitation(invitation.id)

    def post_note(self, note):
        """
        Posts the note. Upon success, returns the posted Note object.
        If the note is unsigned, signs it using the client's default signature
        """
        if not note.signatures: note.signatures = [self.signature]
        response = requests.post(self.notes_url, json = note.to_json(), headers = self.headers)
        response = self.__handle_response(response)

        return self.get_note(note.id)

    def post_tag(self, tag):
        """posts the note. Upon success, returns the original Note object."""
        response = requests.post(self.tags_url, json = tag.to_json(), headers = self.headers)
        response = self.__handle_response(response)

        return self.get_tag(tag.id)

    def send_mail(self, subject, recipients, message):
        response = requests.post(self.mail_url, json = {'groups': recipients, 'subject': subject , 'message': message}, headers = self.headers)
        response = self.__handle_response(response)

        return response.json()

    def add_members_to_group(self, group, members):
        def add_member(group,members):
            response = requests.put(self.groups_url + '/members', json = {'id': group, 'members': members}, headers = self.headers)
            response = self.__handle_response(response)
            return self.get_group(response.json()['id'])

        if type(members)==str:
            return add_member(group.id,[members])
        if type(members)==list:
            return add_member(group.id,members)

    def remove_members_from_group(self, group, members):
        def remove_member(group,members):
            response = requests.delete(self.groups_url + '/members', json = {'id': group, 'members': members}, headers = self.headers)
            response = self.__handle_response(response)
            return self.get_group(response.json()['id'])

        if type(members)==str:
            return remove_member(group.id,[members])
        if type(members)==list:
            return remove_member(group.id,members)

    def search_notes(self, term, content = 'all', group = 'all'):
        response = requests.get(self.notes_url + '/search', params = {'term': term, 'content': content, 'group': group}, headers = self.headers)
        response = self.__handle_response(response)
        return [Note.from_json(n) for n in response.json()['notes']]

class Group(object):
    def __init__(self, id, cdate = None, ddate = None, writers = None, members = None, readers = None, nonreaders = None, signatories = None, signatures = None, web = None):
        # post attributes
        self.id=id
        self.cdate=cdate
        self.ddate=ddate
        self.writers = [] if writers==None else writers
        self.members = [] if members==None else members
        self.readers = ['everyone'] if readers==None else readers
        self.nonreaders = [] if nonreaders==None else nonreaders
        self.signatories = [self.id] if signatories==None else signatories
        self.signatures = [] if signatures==None else signatures
        self.web=None
        if web != None:
            with open(web) as f:
                self.web = f.read()

    def to_json(self):
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
        if self.web !=None:
            body['web']=self.web
        return body

    @classmethod
    def from_json(Group,g):
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

    def __str__(self):
        return '{:12}'.format('id: ')+self.id+'\n{:12}'.format('members: ')+', '.join(self.members)

    def add_member(self, member):
        if type(member) is Group:
            self.members.append(member.id)
        else:
            self.members.append(str(member))
        return self

    def remove_member(self, member):
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

    def post(self, client):
        client.post_group(self)

class Invitation(object):
    def __init__(self, id, writers=None, invitees=None, noninvitees=None, readers=None, nonreaders=None, reply=None, web=None, process=None, signatures=None, duedate=None, cdate=None, rdate=None, ddate=None, multiReply=None, taskCompletionCount=None):

        default_reply = {
            'forum': None,
            'replyto': None,
            'readers': {'values': ['everyone']},
            'signatures': {'values-regex': '~.*'},
            'writers': {'values-regex': '~.*'},
            'content':{}
        }

        self.id = id
        self.cdate = cdate
        self.rdate = rdate
        self.ddate = ddate
        self.duedate = duedate
        self.readers = ['everyone'] if readers==None else readers
        self.nonreaders = [] if nonreaders==None else nonreaders
        self.writers = [] if readers==None else writers
        self.invitees = ['~'] if invitees==None else invitees
        self.noninvitees = [] if noninvitees==None else noninvitees
        self.signatures = [] if signatures==None else signatures
        self.multiReply = multiReply
        self.taskCompletionCount = taskCompletionCount
        self.reply = default_reply if reply==None else reply
        self.web = None
        if web != None:
            with open(web) as f:
                self.web = f.read()
        self.process = None
        if process != None:
            with open(process) as f:
                self.process = f.read()

    def to_json(self):
        body = {
            'id': self.id,
            'cdate': self.cdate,
            'rdate': self.rdate,
            'ddate': self.ddate,
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
            'web': self.web
        }

        if hasattr(self,'web'):
            body['web']=self.web
        if hasattr(self,'process'):
            body['process']=self.process
        return body

    @classmethod
    def from_json(Invitation,i):
        invitation = Invitation(i['id'],
            cdate = i.get('cdate'),
            rdate = i.get('rdate'),
            ddate = i.get('ddate'),
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
        return invitation

    def add_reply_content(Invitation, fieldname='field', description=None, constraint=None, order=0, required=True):

        predefined_content = {
            'title': {
                    'description': 'Title of paper.',
                    'order': 1,
                    'value-regex': '.{1,250}',
                    'required':True
            },
            'authors': {
                'description': 'Comma separated list of author names, as they appear in the paper.',
                'order': 2,
                'values-regex': "[^;,\\n]+(,[^,\\n]+)*",
                'required':True
            },
            'authorids': {
                'description': 'Comma separated list of author email addresses, in the same order as above.',
                'order': 3,
                'values-regex': "[^;,\\n]+(,[^,\\n]+)*",
                'required':True
            },
            'TL;DR': {
                'description': '\"Too Long; Didn\'t Read\": a short sentence describing your paper',
                'order': 3,
                'value-regex': '[^\\n]{0,250}',
                'required':False
            },
            'abstract': {
                'description': 'Abstract of paper.',
                'order': 4,
                'value-regex': '[\\S\\s]{1,5000}',
                'required':True
            },
            'pdf': {
                'description': 'Either upload a PDF file or provide a direct link to your PDF on ArXiv (link must begin with http(s) and end with .pdf)',
                'order': 5,
                'value-regex': 'upload|(http|https):\/\/.+\.pdf',
                'required':True
            },
            'conflicts': {
                'description': 'Comma separated list of email domains of people who would have a conflict of interest in reviewing this paper, (e.g., cs.umass.edu;google.com, etc.).',
                'order': 100,
                'values-regex': "[^;,\\n]+(,[^,\\n]+)*",
                'required':True
            }
        }

        if fieldname in predefined_content.keys():
            Invitation.reply['content'][fieldname] = predefined_content[fieldname].copy()

        if description:
            Invitation.reply['content'][fieldname]['description'] = description

        if order:
            Invitation.reply['content'][fieldname]['order'] = order

        if required != None:
            Invitation.reply['content'][fieldname]['required'] = required

        return Invitation


class Note(object):
    def __init__(self, id=None, original=None, number=None, cdate=None, tcdate=None, ddate=None, content=None, forum=None, referent=None, invitation=None, replyto=None, active=None, readers=None, nonreaders=None, signatures=None, writers=None):
        self.id = id
        self.original = original
        self.number = number
        self.cdate = cdate
        self.tcdate = tcdate
        self.ddate = ddate
        self.content = {} if content==None else content
        self.forum = forum
        self.referent = referent
        self.invitation = invitation
        self.replyto = replyto
        self.active = active or True
        self.readers = ['everyone'] if readers==None else readers
        self.nonreaders = [] if nonreaders==None else nonreaders
        self.signatures = [] if signatures==None else signatures
        self.writers = [] if writers==None else writers
        self.number = number

    def to_json(self):
        body = {
            'id': self.id,
            'original': self.original,
            'cdate':self.cdate,
            'tcdate': self.tcdate,
            'ddate': self.ddate,
            'number': self.number,
            'content': self.content,
            'forum': self.forum,
            'referent': self.referent,
            'invitation': self.invitation,
            'replyto': self.replyto,
            'active': self.active,
            'readers': self.readers,
            'nonreaders': self.nonreaders,
            'signatures': self.signatures,
            'writers': self.writers,
            'number':self.number
        }
        return body

    @classmethod
    def from_json(Note,n):
        note = Note(
        id = n.get('id'),
        original = n.get('original'),
        number = n.get('number'),
        cdate = n.get('cdate'),
        tcdate = n.get('tcdate'),
        ddate=n.get('ddate'),
        content=n.get('content'),
        forum=n.get('forum'),
        referent=n.get('referent'),
        invitation=n.get('invitation'),
        replyto=n.get('replyto'),
        active=n.get('active'),
        readers=n.get('readers'),
        nonreaders=n.get('nonreaders'),
        signatures=n.get('signatures'),
        writers=n.get('writers')
        )
        return note

class Tag(object):
    def __init__(self, id=None, cdate=None, tcdate=None, ddate=None, tag=None, forum=None, invitation=None, replyto=None, active=None, readers=None, nonreaders=None, signatures=None):
        self.id = id
        self.cdate = cdate
        self.tcdate = tcdate
        self.ddate = ddate
        self.tag = tag
        self.forum = forum
        self.invitation = invitation
        self.replyto = replyto
        self.readers = [] if readers==None else readers
        self.nonreaders = [] if nonreaders==None else nonreaders
        self.signatures = [] if signatures==None else signatures

    def to_json(self):
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
