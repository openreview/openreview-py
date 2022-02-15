import os
import json
from .. import openreview
from openreview.api import Group
from .. import tools
from openreview import api

class GroupBuilder(object):

    def __init__(self, client):
        self.client = client

    def __build_options(self, default, options):

        merged_options = {}
        for k in default:
            merged_options[k] = default[k]

        for o in options:
            if options[o] is not None:
                merged_options[o] = options[o]

        return merged_options

    def __create_group(self, group_id, group_owner_id, members=[], is_signatory=True, additional_readers=[], exclude_self_reader=False):
        group = tools.get_group(self.client, id = group_id)
        if group is None:
            readers = [self.id, group_owner_id] if exclude_self_reader else [self.id, group_owner_id, group_id]
            return self.client.post_group(Group(
                id = group_id,
                readers = ['everyone'] if 'everyone' in additional_readers else readers + additional_readers,
                writers = [self.id, group_owner_id],
                signatures = [self.id],
                signatories = [self.id, group_id] if is_signatory else [self.id, group_owner_id],
                members = members))
        else:
            return self.client.add_members_to_group(group, members)

    def __should_update(self, entity):
        return entity.details.get('writable', False) and (not entity.web or entity.web.startswith('// webfield_template'))
    
    def __update_group(self, group, content, signature=None):
        current_group=self.client.get_group(group.id)
        if signature:
            current_group.signatures=[signature]
        if self.__should_update(current_group):
            current_group.web = content
            return self.client.post_group(current_group)
        else:
            return current_group

    def set_groups(self, venue):
        venue_config = venue.venue_config
        venue_id = venue_config.venue_id
        path_components = venue_config.venue_id.split('/')
        paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]
        groups = []

        for p in paths:
            group = tools.get_group(self.client, id = p)
            if group is None:
                group = self.client.post_group(Group(
                    id = p,
                    readers = ['everyone'],
                    nonreaders = [],
                    writers = [p],
                    signatories = [p],
                    signatures = ['~Super_User1'],
                    members = [],
                    details = { 'writable': True })
                )

            groups.append(group)
        
        for i, g in enumerate(groups[:-1]):
            self.set_landing_page(g, groups[i-1] if i > 0 else None)

        root_id = groups[0].id
        if root_id == root_id.lower():
            root_id = groups[1].id
        self.client.add_members_to_group('host', root_id)

        #setup homepage webfield
        home_group = groups[-1]
        parent_group_id = groups[-2].id if len(groups) > 1 else ''
        header = venue.get_homepage_options()

        with open(os.path.join(os.path.dirname(__file__), 'webfields/homepage.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + home_group.id + "';")
            content = content.replace("var PARENT_GROUP_ID = '';", "var PARENT_GROUP_ID = '" + parent_group_id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + venue.get_submission_id() + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + venue.get_blind_submission_id() + "';")
            home_group.web = content
            self.client.post_group(home_group)
        
        ## program chairs
        ## To-Do: add PC console webfield
        program_chair_id = venue.get_program_chairs_id()
        program_chair_group = openreview.tools.get_group(self.client, program_chair_id)
        if not program_chair_group:
            program_chair_group = self.client.post_group(Group(id=program_chair_id,
                        readers=[venue_id, program_chair_id],
                        writers=[venue_id],
                        signatures=[venue_id],
                        signatories=[venue_id, program_chair_id],
                        members=venue_config.program_chair_ids
            ))

        ## Add program chairs to have all the permissions
        self.client.add_members_to_group(home_group, program_chair_id)

        ## To-Do: add AC console webfield
        if venue_config.use_area_chairs:
            ## area chair group
            area_chair_id = venue.get_area_chairs_id()
            area_chair_group = openreview.tools.get_group(self.client, area_chair_id)
            if not area_chair_group:
                area_chair_group=self.client.post_group(Group(id=area_chair_id,
                                readers=[venue_id, program_chair_id],
                                writers=[venue_id],
                                signatures=[venue_id],
                                signatories=[venue_id, program_chair_id],
                                members=[]))
            
            ## area chair invited group
            area_chair_invited_id = f'{area_chair_id}/Invited'
            area_chair_invited_group = openreview.tools.get_group(self.client, area_chair_invited_id)
            if not area_chair_invited_group:
                area_chair_invited_group = self.client.post_group(Group(id=area_chair_invited_id,
                                readers=[venue_id, program_chair_id, area_chair_invited_id],
                                writers=[venue_id, program_chair_id],
                                signatures=[venue_id],
                                signatories=[venue_id, area_chair_invited_id],
                                members=[]))

            ## action editors declined group
            area_chair_declined_id = f'{area_chair_id}/Declined'
            area_chair_declined_group = openreview.tools.get_group(self.client, area_chair_declined_id)
            if not area_chair_declined_group:
                area_chair_declined_group = self.client.post_group(Group(id=area_chair_declined_id,
                                readers=[venue_id, program_chair_id, area_chair_declined_id],
                                writers=[venue_id, program_chair_id],
                                signatures=[venue_id],
                                signatories=[venue_id, area_chair_declined_id],
                                members=[]))

        ## reviewers group
        reviewers_id = venue.get_reviewers_id()
        reviewer_group = openreview.tools.get_group(self.client, reviewers_id)
        if not reviewer_group:
            committee = [venue_id]
            if venue_config.use_area_chairs:
                committee.append(venue.get_area_chairs_id())
            reviewer_group = self.client.post_group(Group(id=reviewers_id,
                            readers=committee + [reviewers_id],
                            writers=committee,
                            signatures=[venue_id],
                            signatories=[venue_id, reviewers_id],
                            members=[]
                            ))

    def set_landing_page(self, group, parentGroup, options = {}):
        # sets webfield to show links to child groups

        children_groups = self.client.get_groups(regex = group.id + '/[^/]+/?$')

        links = []
        for children in children_groups:
            if not group.web or (group.web and children.id not in group.web):
                links.append({ 'url': '/group?id=' + children.id, 'name': children.id})

        if not group.web:
            # create new webfield using template
            default_header = {
                'title': group.id,
                'description': ''
            }
            header = self.__build_options(default_header, options)

            with open(os.path.join(os.path.dirname(__file__), 'webfields/landingWebfield.js')) as f:
                content = f.read()
                content = content.replace("var GROUP_ID = '';", "var GROUP_ID = '" + group.id + "';")
                if parentGroup:
                    content = content.replace("var PARENT_GROUP_ID = '';", "var PARENT_GROUP_ID = '" + parentGroup.id + "';")
                content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
                content = content.replace("var VENUE_LINKS = [];", "var VENUE_LINKS = " + json.dumps(links) + ";")
                return self.__update_group(group, content)

        elif links:
            # parse existing webfield and add new links
            # get links array without square brackets
            link_str = json.dumps(links)
            link_str = link_str[1:-1]
            start_pos = group.web.find('VENUE_LINKS = [') + len('VENUE_LINKS = [')
            return self.__update_group(group, group.web[:start_pos] +link_str + ','+ group.web[start_pos:])