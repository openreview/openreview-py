#!/usr/bin/python
import requests

import json
import os
import getpass
import ConfigParser
from Crypto.Hash import HMAC, SHA256

class OpenReviewException(Exception):
    pass

class Client(object):

    def __init__(self, baseurl=None, process_dir='../process/', webfield_dir='../webfield/',username=None,password=None):
        """CONSTRUCTOR DOCSTRING"""
        if baseurl==None:
            try:
                self.baseurl = os.environ['OPENREVIEW_BASEURL']
            except KeyError:
                self.baseurl = 'http://localhost:3000'
        else:
            self.baseurl = baseurl

        self.groups_url = self.baseurl+'/groups'
        self.login_url = self.baseurl+'/login'
        self.register_url = self.baseurl+'/register'
        self.invitations_url = self.baseurl+'/invitations'
        self.mail_url = self.baseurl+'/mail'
        self.notes_url = self.baseurl+'/notes'
        self.token = self.__login_user(username,password)
        self.headers = {'Authorization': 'Bearer ' + self.token, 'User-Agent': 'test-create-script'}

    ## PRIVATE FUNCTIONS
    def __handle_response(self,response):
        try:
            response.raise_for_status()
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

    def get_group(self, id):
        """Returns a single Group by id if available"""
        response = requests.get(self.groups_url, params={'id':id}, headers=self.headers)
        response = self.__handle_response(response)

        g = response.json()['groups'][0]
        
        return Group.from_json(g)


    def get_invitation(self, id):
        """Returns a single invitation by id if available"""
        response = requests.get(self.invitations_url, params={'id':id}, headers=self.headers)
        response = self.__handle_response(response)

        i = response.json()['invitations'][0]

        return Invitation.from_json(i)


    def get_note(self, id):
        """Returns a single note by id if available"""
        response = requests.get(self.notes_url, params={'id':id}, headers=self.headers)
        response = self.__handle_response(response)

        n = response.json()['notes'][0]
        return Note.from_json(n)


    def get_groups(self, prefix=None, regex=None, member=None, host=None, signatory=None):
        """Returns a list of Group objects based on the filters provided."""
        groups=[]
        params = {}
        if prefix!=None:
            params['regex'] = prefix+'.*'
        if regex!=None:
            params['regex'] = regex
        if member!=None:
            params['member'] = member
        if host!=None:
            params['host'] = host
        if signatory!=None:
            params['signatory'] = signatory

        response = requests.get(self.groups_url, params=params, headers=self.headers)
        response = self.__handle_response(response)

        for g in response.json()['groups']:
            groups.append(Group.from_json(g))

        groups.sort(key=lambda x: x.id)

        return groups
        

    def get_invitations(self, id=None, invitee=None, replytoNote=None, replyForum=None, signature=None, note=None):
        """Returns a list of Group objects based on the filters provided."""
        invitations=[]
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

        response = requests.get(self.invitations_url, params=params, headers=self.headers)
        response = self.__handle_response(response)

        for i in response.json()['invitations']:
            invitation = Invitation.from_json(i)
            invitations.append(invitation)
        invitations.sort(key=lambda x: x.id)
        return invitations


    def get_notes(self, id=None, forum=None, invitation=None, replyto=None, tauthor=None, signature=None, writer=None, includeTrash=None):
        """Returns a list of Note objects based on the filters provided."""
        notes=[]
        params = {}
        if id!=None:
            params['id'] = id
        if forum!=None:
            params['forum'] = forum
        if invitation!=None:
            params['invitation'] = invitation
        if replyto!=None:
            params['replyto'] = replyto
        if tauthor!=None:
            params['tauthor'] = tauthor
        if signature!=None:
            params['signature'] = signature
        if writer!=None:
            params['writer']=writer
        if includeTrash==True:
            params['trash']=True

        response = requests.get(self.notes_url, params=params, headers=self.headers)
        response = self.__handle_response(response)

        for n in response.json()['notes']:
            note = Note.from_json(n)
            notes.append(note)
        return notes

    def exists(self, groupid):
        try:
            self.get_group(groupid)
        except OpenReviewException:
            return False
        return True   
        

    def post_group(self, group, overwrite=True):
        """posts the group. Upon success, returns the original Group object."""

        if overwrite or not self.exists(group.id):
            response = requests.post(self.groups_url, json=group.to_json(), headers=self.headers)
            response = self.__handle_response(response)

        return group


    def post_invitation(self, invitation):
        """posts the invitation. Upon success, returns the original Invitation object."""
        response = requests.post(self.invitations_url, json=invitation.to_json(), headers=self.headers)
        response = self.__handle_response(response)

        return invitation

    def post_note(self, note):
        """posts the note. Upon success, returns the original Note object."""
        response = requests.post(self.notes_url, json=note.to_json(), headers=self.headers)
        response = self.__handle_response(response)
        
        return note

    def send_mail(self, subject, recipients, message):
        response = requests.post(self.mail_url, json={'groups': recipients, 'subject': subject , 'message': message}, headers=self.headers)
        response = self.__handle_response(response)

        return response

    def add_members_to_group(self, group, members):
        def add_member(group,members):     
            response = requests.put(self.groups_url+'/members', json={'id':group,'members':members}, headers=self.headers)
            response = self.__handle_response(response)
            return self.get_group(response.json()['id'])

        if type(members)==str:
            return add_member(group.id,[members])
        if type(members)==list:
            return add_member(group.id,members)
    
    def remove_members_from_group(self, group, members):
        def remove_member(group,members):     
            response = requests.delete(self.groups_url+'/members', json={'id':group,'members':members}, headers=self.headers)
            response = self.__handle_response(response)
            return self.get_group(response.json()['id'])

        if type(members)==str:
            return remove_member(group.id,[members])
        if type(members)==list:
            return remove_member(group.id,members)

class Group(object):
    
    def __init__(self, id, cdate=None, ddate=None, writers=None, members=None, readers=None, nonreaders=None, signatories=None, signatures=None, web=None):
        # post attributes
        self.id=id
        self.cdate=cdate
        self.ddate=ddate
        self.writers=writers
        self.members=members
        self.readers=readers
        self.nonreaders=nonreaders
        self.signatories=signatories
        self.signatures=signatures
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
    def __init__(self, inviter, suffix, writers=None, invitees=None, noninvitees=None, readers=None, nonreaders=None, reply=None, web=None, process=None, signatures=None, duedate=None, cdate=None, rdate=None, ddate=None):
        self.id = inviter+'/-/'+suffix
        self.cdate=cdate
        self.rdate=rdate
        self.ddate=ddate
        self.duedate=duedate
        self.readers=readers
        self.nonreaders=nonreaders
        self.writers=writers
        self.invitees=invitees
        self.noninvitees=noninvitees
        self.signatures=signatures
        self.reply={} if reply==None else reply
        self.web = None
        self.process = None
        if web != None:
            with open(web) as f:
                self.web = f.read()
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
            'reply':self.reply,
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
        invitation = Invitation(i['id'].split('/-/')[0],
            i['id'].split('/-/')[1],
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
            reply = i.get('reply')
            )
        if 'web' in i:
            invitation.web = i['web']
        if 'process' in i:
            invitation.process = i['process']
        return invitation

    def add_invitee(self, invitee):
        if type(invitee) is Group:
            self.invitees.append(invitee.id)
        else:
            self.invitees.append(str(invitee))
        return self

    def add_noninvitee(self, noninvitee):
        if type(noninvitee) is Group:
            if self.noninvitees!=None:
                self.noninvitees.append(noninvitee.id)
            else:
                self.noninvitees=[noninvitee.id]
        else:
            if self.noninvitees!=None:
                self.noninvitees.append(str(noninvitee))
            else:
                self.noninvitees=[str(noninvitee)]
        return self

class Note(object):
    def __init__(self, id=None, number=None, cdate=None, tcdate=None, ddate=None, content=None, forum=None, invitation=None, replyto=None, active=None, readers=None, nonreaders=None, signatures=None, writers=None):
        self.id = id
        self.number = number
        self.cdate = cdate
        self.tcdate=tcdate
        self.ddate=ddate
        self.content = content
        self.forum = forum
        self.invitation = invitation
        self.replyto = replyto
        self.active = active or True
        self.readers = readers
        self.nonreaders = nonreaders
        self.signatures = signatures
        self.writers = writers
        self.number = number

    def to_json(self):
        body = {
            'id': self.id,
            'cdate':self.cdate,
            'tcdate': self.tcdate,
            'ddate': self.ddate,
            'number': self.number,
            'content': self.content,
            'forum': self.forum,
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
        id = n['id'],
        number = n['number'],
        cdate = n.get('cdate'),
        tcdate = n['tcdate'],
        ddate=n.get('ddate'),
        content=n.get('content'),
        forum=n.get('forum'),
        invitation=n.get('invitation'),
        replyto=n.get('replyto'),
        active=n.get('active'),
        readers=n.get('readers'),
        nonreaders=n.get('nonreaders'),
        signatures=n.get('signatures'),
        writers=n.get('writers')
        )
        return note
