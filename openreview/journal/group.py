from .. import openreview
from openreview.api import Group
from openreview.journal.templates import *

import os
import json

class GroupBuilder(object):

    def __init__(self, journal):
        self.client = journal.client
        self.journal = journal

    def post_group(self, group):
        self.client.post_group_edit(
            invitation = self.journal.get_meta_invitation_id(),
            readers = [self.journal.venue_id],
            writers = [self.journal.venue_id],
            signatures = ['~Super_User1' if group.id == self.journal.venue_id else self.journal.venue_id],
            group = group
        )
        return self.client.get_group(group.id)

    def set_group_variable(self, group_id, variable_name, value):

        group = self.client.get_group(group_id)
        group.web = group.web.replace(f"var {variable_name} = '';", f"var {variable_name} = '{value}';")
        self.post_group(group)
    
    def get_update_content(self, current_content, new_content):
        update_content = {}

        for key, value in current_content.items():
            if key in new_content and value != new_content[key]:
                update_content[key] = new_content[key]
            
            if key not in new_content:
                update_content[key] = { 'delete': True }

        for key, value in new_content.items():
            if key not in current_content:
                update_content[key] = new_content[key]
        return update_content
    
    def set_groups(self, support_role, editors):
        venue_id = self.journal.venue_id
        editor_in_chief_id = self.journal.get_editors_in_chief_id()
        reviewer_report_form = self.journal.get_reviewer_report_form()
        additional_committee = [self.journal.get_action_editors_archived_id()] if self.journal.has_archived_action_editors() else []

        ## venue group
        venue_group = openreview.tools.get_group(self.client, venue_id)
        if not venue_group:
            venue_group=self.post_group(Group(id=venue_id,
                            readers=['everyone'],
                            writers=[venue_id],
                            signatures=['~Super_User1'],
                            signatories=[venue_id],
                            members=[support_role],
                            host=venue_id
                            ))
            venue_group.content = {}

            self.client.add_members_to_group('host', venue_id)
            self.client.add_members_to_group('venues', venue_id)
            self.client.add_members_to_group('active_venues', venue_id)

        ## Update settings
        content = {
            'title': { 'value': self.journal.full_name },
            'subtitle': { 'value': self.journal.short_name },
            'website': { 'value': self.journal.website },
            'contact': { 'value': self.journal.contact_info },
            'message_sender': { 'value': self.journal.get_message_sender() },
            'submission_id': { 'value': self.journal.get_author_submission_id() },
            'under_review_venue_id': { 'value': self.journal.under_review_venue_id },
            'decision_pending_venue_id': { 'value': self.journal.decision_pending_venue_id },
            'preferred_emails_invitation_id': { 'value': self.journal.get_preferred_emails_invitation_id() },
        }

        if self.journal.get_certifications():
            content['certifications'] = { 'value': self.journal.get_certifications() }
        if self.journal.get_eic_certifications():
            content['eic_certifications'] = { 'value': self.journal.get_eic_certifications() }
        if self.journal.has_expert_reviewers():
            content['expert_reviewer_certification'] = { 'value': self.journal.get_expert_reviewer_certification() }
        if self.journal.get_event_certifications():
            content['event_certifications'] = { 'value': self.journal.get_event_certifications() }
        if self.journal.get_website_url('videos'):
            content['videos_url'] = { 'value': self.journal.get_website_url('videos') }

        update_content = self.get_update_content(venue_group.content, content)
        if update_content:
            self.client.post_group_edit(
                invitation = self.journal.get_meta_invitation_id(),
                readers = [venue_id],
                writers = [venue_id],
                signatures = [venue_id],
                group = openreview.api.Group(
                    id = venue_id,
                    content = update_content
                )
            )            

        ## editor in chief
        editor_in_chief_group = openreview.tools.get_group(self.client, editor_in_chief_id)
        if not editor_in_chief_group:
            content = {}
            content['new_submission_email_template_script'] = { 'value': eic_new_submission_template }            
            editor_in_chief_group=self.post_group(Group(id=editor_in_chief_id,
                            readers=['everyone'],
                            writers=[venue_id, editor_in_chief_id],
                            signatures=[venue_id],
                            signatories=[editor_in_chief_id, venue_id],
                            members=editors,
                            content=content
                            ))
        with open(os.path.join(os.path.dirname(__file__), 'webfield/editorsInChiefWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{self.journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.journal.get_author_submission_id() + "';")
            content = content.replace("var EDITORS_IN_CHIEF_NAME = '';", "var EDITORS_IN_CHIEF_NAME = '" + self.journal.editors_in_chief_name + "';")
            content = content.replace("var EDITORS_IN_CHIEF_EMAIL = '';", "var EDITORS_IN_CHIEF_EMAIL = '" + self.journal.get_editors_in_chief_email() + "';")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + self.journal.reviewers_name + "';")
            content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + self.journal.action_editors_name + "';")
            content = content.replace("var NUMBER_OF_REVIEWERS = 3;", "var NUMBER_OF_REVIEWERS = " + str(self.journal.get_number_of_reviewers()) + ";")
            content = content.replace("var PREFERRED_EMAILS_ID = '';", "var PREFERRED_EMAILS_ID = '" + self.journal.get_preferred_emails_invitation_id() + "';")
            if self.journal.request_form_id:
                content = content.replace("var JOURNAL_REQUEST_ID = '';", "var JOURNAL_REQUEST_ID = '" + self.journal.request_form_id + "';")
            if reviewer_report_form:
                content = content.replace("var REVIEWER_REPORT_ID = '';", "var REVIEWER_REPORT_ID = '" + reviewer_report_form + "';")

            editor_in_chief_group.web = content
            self.post_group(editor_in_chief_group)

        editors=""
        for m in editor_in_chief_group.members:
            name=m.replace('~', ' ').replace('_', ' ')[:-1]
            editors+=f'[{name}](https://openreview.net/profile?id={m})  \n'

        instructions = f'''
**Editors-in-chief:**  
{editors}

**Managing Editors:**  
[{openreview.tools.pretty_id(support_role)}](https://openreview.net/profile?id={support_role})

{self.journal.full_name} ({venue_id}) is a venue for dissemination of machine learning research that is intended to complement JMLR while supporting the unmet needs of a growing ML community.  

- {venue_id} emphasizes technical correctness over subjective significance, in order to ensure we facilitate scientific discourses on topics that are deemed less significant by contemporaries but may be so in the future.
- {venue_id} caters to the shorter format manuscripts that are usually submitted to conferences, providing fast turnarounds and double blind reviewing.
- {venue_id} employs a rolling submission process, shortened review period, flexible timelines, and variable manuscript length, to enable deep and sustained interactions among authors, reviewers, editors and readers.
- {venue_id} does not accept submissions that have any overlap with previously published work.

For more information on {venue_id}, visit [{self.journal.website}](http://{self.journal.website})
'''
        if self.journal.has_expert_reviewers():
            instructions += f'''
            
Visit [this page](https://openreview.net/group?id={self.journal.get_expert_reviewers_id()}) for the list of our Expert Reviewers.
'''

        with open(os.path.join(os.path.dirname(__file__), 'webfield/homepage.js')) as f:
            content = f.read()
            content = content.replace("const instructions = ''", "const instructions = `" + instructions + "`")
            if not venue_group.web:
                venue_group.web = content
                self.post_group(venue_group)

        ## Add editors in chief to have all the permissions
        self.client.add_members_to_group(venue_group, editor_in_chief_id)

        ## publication editors group
        if self.journal.has_publication_chairs():
            publication_chairs_id = self.journal.get_publication_chairs_id()
            publication_chairs_group = openreview.tools.get_group(self.client, publication_chairs_id)
            if not publication_chairs_group:
                publication_chairs_group=self.post_group(Group(id=publication_chairs_id,
                                readers=['everyone'],
                                writers=[venue_id],
                                signatures=[venue_id],
                                signatories=[venue_id, publication_chairs_id],
                                members=[]))

        ## action editors group
        action_editors_id = self.journal.get_action_editors_id()
        action_editor_group = openreview.tools.get_group(self.client, action_editors_id)
        if not action_editor_group:
            content = {}
            content['assignment_email_template_script'] = { 'value': ae_assignment_email_template }            
            content['unassignment_email_template_script'] = { 'value': ae_unassignment_email_template }
            content['eic_as_author_email_template_script'] = { 'value': ae_assignment_eic_as_author_email_template }
            content['camera_ready_verification_email_template_script'] = { 'value': ae_camera_ready_verification_email_template }       
            content['official_recommendation_starts_email_template_script'] = { 'value': ae_official_recommendation_starts_email_template }
            content['official_recommendation_ends_email_template_script'] = { 'value': ae_official_recommendation_ends_email_template } 
            content['discussion_starts_email_template_script'] = { 'value': ae_discussion_starts_email_template }
            content['discussion_too_many_reviewers_email_template_script'] = { 'value': ae_discussion_too_many_reviewers_email_template }
            content['reviewer_assignment_starts_email_template_script'] = { 'value': ae_reviewer_assignment_starts_email_template }
            action_editor_group=self.post_group(Group(id=action_editors_id,
                            readers=['everyone'],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[],
                            content=content))

        with open(os.path.join(os.path.dirname(__file__), 'webfield/actionEditorWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{self.journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.journal.get_author_submission_id() + "';")
            content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + self.journal.action_editors_name + "';")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + self.journal.reviewers_name + "';")
            content = content.replace("var SUBMISSION_GROUP_NAME = '';", "var SUBMISSION_GROUP_NAME = '" + self.journal.submission_group_name + "';")
            content = content.replace("var NUMBER_OF_REVIEWERS = 3;", "var NUMBER_OF_REVIEWERS = " + str(self.journal.get_number_of_reviewers()) + ";")
            content = content.replace("var PREFERRED_EMAILS_ID = '';", "var PREFERRED_EMAILS_ID = '" + self.journal.get_preferred_emails_invitation_id() + "';")
            if self.journal.request_form_id:
                content = content.replace("var JOURNAL_REQUEST_ID = '';", "var JOURNAL_REQUEST_ID = '" + self.journal.request_form_id + "';")
            if reviewer_report_form:
                content = content.replace("var REVIEWER_REPORT_ID = '';", "var REVIEWER_REPORT_ID = '" + reviewer_report_form + "';")

            action_editor_group.web = content
            self.post_group(action_editor_group)

        if self.journal.get_event_certifications():
            event_group = openreview.tools.get_group(self.client, f'{venue_id}/Event_Certifications')
            if not event_group:
                event_group=self.post_group(Group(id=f'{venue_id}/Event_Certifications',
                                readers=['everyone'],
                                writers=[venue_id],
                                signatures=[venue_id],
                                signatories=[venue_id],
                                members=[]))            
            with open(os.path.join(os.path.dirname(__file__), 'webfield/eventCertificationsWebfield.js')) as f:
                content = f.read()
                if not event_group.web:
                    event_group.web = content
                    self.post_group(event_group)            

        ## action editors invited group
        action_editors_invited_id = f'{action_editors_id}/Invited'
        action_editors_invited_group = openreview.tools.get_group(self.client, action_editors_invited_id)
        if not action_editors_invited_group:
            self.post_group(Group(id=action_editors_invited_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## action editors declined group
        action_editors_declined_id = f'{action_editors_id}/Declined'
        action_editors_declined_group = openreview.tools.get_group(self.client, action_editors_declined_id)
        if not action_editors_declined_group:
            self.post_group(Group(id=action_editors_declined_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))
            
        ## archived action editors group
        action_editors_archived_id = f'{action_editors_id}/Archived'
        action_editor_archived_group = openreview.tools.get_group(self.client, action_editors_archived_id)
        if not action_editor_archived_group:
            action_editor_archived_group=self.post_group(Group(id=action_editors_archived_id,
                            readers=['everyone'],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]))
        with open(os.path.join(os.path.dirname(__file__), 'webfield/actionEditorWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{self.journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.journal.get_author_submission_id() + "';")
            content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + self.journal.action_editors_name + "';")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + self.journal.reviewers_name + "';")
            content = content.replace("var SUBMISSION_GROUP_NAME = '';", "var SUBMISSION_GROUP_NAME = '" + self.journal.submission_group_name + "';")
            content = content.replace("var NUMBER_OF_REVIEWERS = 3;", "var NUMBER_OF_REVIEWERS = " + str(self.journal.get_number_of_reviewers()) + ";")
            if reviewer_report_form:
                content = content.replace("var REVIEWER_REPORT_ID = '';", "var REVIEWER_REPORT_ID = '" + reviewer_report_form + "';")

            action_editor_archived_group.web = content
            self.post_group(action_editor_archived_group)            

        ## reviewers group
        reviewers_id = self.journal.get_reviewers_id()
        reviewer_group = openreview.tools.get_group(self.client, reviewers_id)
        if not reviewer_group:
            content = {}
            content['assignment_email_template_script'] = { 'value': reviewer_assignment_email_template }            
            content['unassignment_email_template_script'] = { 'value': reviewer_unassignment_email_template }
            content['discussion_starts_email_template_script'] = { 'value': reviewer_discussion_starts_email_template }
            content['official_recommendation_starts_email_template_script'] = { 'value': reviewer_official_recommendation_starts_email_template }
            reviewer_group = Group(id=reviewers_id,
                            readers=[venue_id, action_editors_id, reviewers_id] + additional_committee,
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[],
                            content=content
                            )
        with open(os.path.join(os.path.dirname(__file__), 'webfield/reviewersWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{self.journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.journal.get_author_submission_id() + "';")
            content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + self.journal.action_editors_name + "';")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + self.journal.reviewers_name + "';")
            content = content.replace("var WEBSITE = '';", "var WEBSITE = '" + self.journal.website + "';")
            reviewer_group.web = content
            self.post_group(reviewer_group)

        ## archived reviewers group
        if self.journal.has_archived_reviewers:
            archived_reviewers_id = self.journal.get_reviewers_archived_id()
            reviewer_group = openreview.tools.get_group(self.client, archived_reviewers_id)
            if not reviewer_group:
                reviewer_group = Group(id=archived_reviewers_id,
                                readers=[venue_id, action_editors_id, archived_reviewers_id] + additional_committee,
                                writers=[venue_id],
                                signatures=[venue_id],
                                signatories=[venue_id],
                                members=[]
                                )
            with open(os.path.join(os.path.dirname(__file__), 'webfield/archivedReviewersWebfield.js')) as f:
                content = f.read()
                content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
                content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{self.journal.short_name}";')
                content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.journal.get_author_submission_id() + "';")
                content = content.replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = '" + self.journal.action_editors_name + "';")
                content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + self.journal.reviewers_name + "';")
                content = content.replace("var WEBSITE = '';", "var WEBSITE = '" + self.journal.website + "';")
                reviewer_group.web = content
                self.post_group(reviewer_group)

        ## reviewers invited group
        reviewers_invited_id = f'{reviewers_id}/Invited'
        reviewers_invited_group = openreview.tools.get_group(self.client, reviewers_invited_id)
        if not reviewers_invited_group:
            self.post_group(Group(id=reviewers_invited_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## reviewers declined group
        reviewers_declined_id = f'{reviewers_id}/Declined'
        reviewers_declined_group = openreview.tools.get_group(self.client, reviewers_declined_id)
        if not reviewers_declined_group:
            self.post_group(Group(id=reviewers_declined_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))

        ## reviewers reported group
        reviewers_reported_id = self.journal.get_reviewers_reported_id()
        reviewers_reported_group = openreview.tools.get_group(self.client, reviewers_reported_id)
        if not reviewers_reported_group:
            self.post_group(Group(id=reviewers_reported_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))
            
        ## reviewers volunteers group
        reviewers_volunteers_id = self.journal.get_reviewers_volunteers_id()
        reviewers_volunteers_group = openreview.tools.get_group(self.client, reviewers_volunteers_id)
        if not reviewers_volunteers_group:
            self.post_group(Group(id=reviewers_volunteers_id,
                            readers=[venue_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[],
                            members=[]))            
            
        ## expert reviewer group
        if self.journal.has_expert_reviewers():
            expert_reviewers_id = self.journal.get_expert_reviewers_id()
            expert_reviewers_group = openreview.tools.get_group(self.client, expert_reviewers_id)
            if not expert_reviewers_group:
                with open(os.path.join(os.path.dirname(__file__), 'webfield/expertReviewerWebfield.js')) as f:
                    content = f.read()                
                    self.post_group(Group(id=expert_reviewers_id,
                                    readers=['everyone'],
                                    writers=[venue_id],
                                    signatures=[venue_id],
                                    signatories=[],
                                    members=[],
                                    web=content))        

        ## authors group
        authors_id = self.journal.get_authors_id()
        authors_group = openreview.tools.get_group(self.client, authors_id)
        if not authors_group:
            content = {}
            content['new_submission_email_template_script'] = { 'value': author_new_submission_email_template }
            content['ae_recommendation_email_template_script'] = { 'value': author_ae_recommendation_email_template }
            content['discussion_starts_email_template_script'] = { 'value': author_discussion_starts_email_template }
            content['official_recommendation_starts_email_template_script'] = { 'value': author_official_recommendation_starts_email_template }          
            content['decision_accept_as_is_email_template_script'] = { 'value': author_decision_accept_as_is_email_template }
            content['decision_accept_revision_email_template_script'] = { 'value': author_decision_accept_revision_email_template }
            content['decision_reject_email_template_script'] = { 'value': author_decision_reject_email_template }
            content['desk_reject_email_template_script'] = { 'value': author_desk_reject_email_template }
            authors_group = Group(id=authors_id,
                            readers=[venue_id, authors_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[],
                            content=content)

        with open(os.path.join(os.path.dirname(__file__), 'webfield/authorsWebfield.js')) as f:
            content = f.read()
            content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + venue_id + "';")
            content = content.replace("var SHORT_PHRASE = '';", f'var SHORT_PHRASE = "{self.journal.short_name}";')
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + self.journal.get_author_submission_id() + "';")
            content = content.replace("var WEBSITE = '';", "var WEBSITE = '" + self.journal.website + "';")
            authors_group.web = content
            self.post_group(authors_group)

    def setup_submission_groups(self, note):
        venue_id = self.journal.venue_id
        paper_group_id=f'{venue_id}/{self.journal.submission_group_name}{note.number}'
        paper_group=openreview.tools.get_group(self.client, paper_group_id)
        if not paper_group:
            paper_group=self.post_group(Group(id=paper_group_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id]
            ))

        authors_group_id=f'{paper_group.id}/{self.journal.authors_name}'
        authors_group=self.post_group(Group(id=authors_group_id,
            readers=[venue_id, authors_group_id],
            writers=[venue_id],
            signatures=[venue_id],
            signatories=[venue_id, authors_group_id],
            members=note.content['authorids']['value'] ## always update authors
        ))
        self.client.add_members_to_group(f'{venue_id}/{self.journal.authors_name}', authors_group_id)

        action_editors_group_id=f'{paper_group.id}/{self.journal.action_editors_name}'
        reviewers_group_id=f'{paper_group.id}/{self.journal.reviewers_name}'

        action_editors_group=openreview.tools.get_group(self.client, action_editors_group_id)
        if not action_editors_group:
            action_editors_group=self.post_group(Group(id=action_editors_group_id,
                readers=['everyone'],
                nonreaders=[authors_group_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[venue_id],
                members=[],
                anonids=True
            ))

        reviewers_group=openreview.tools.get_group(self.client, reviewers_group_id)
        if not reviewers_group:
            reviewers_group=self.post_group(Group(id=reviewers_group_id,
                readers=[venue_id, action_editors_group_id, reviewers_group_id],
                deanonymizers=[venue_id, action_editors_group_id, reviewers_group_id],
                nonreaders=[authors_group_id],
                writers=[venue_id, action_editors_group_id],
                signatures=[venue_id],
                signatories=[venue_id],
                members=[],
                anonids=True
            ))

        ## solicit reviewers group
        solicit_reviewers_id = self.journal.get_solicit_reviewers_id(number=note.number)
        solicit_reviewers_group = openreview.tools.get_group(self.client, solicit_reviewers_id)
        if not solicit_reviewers_group:
            self.post_group(Group(id=solicit_reviewers_id,
                readers=[venue_id, action_editors_group_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[],
                members=[]))

        declined_solicit_reviewers_id = self.journal.get_solicit_reviewers_id(number=note.number, declined=True)
        declined_solicit_reviewers_group = openreview.tools.get_group(self.client, declined_solicit_reviewers_id)
        if not declined_solicit_reviewers_group:
            self.post_group(Group(id=declined_solicit_reviewers_id,
                readers=[venue_id, action_editors_group_id],
                writers=[venue_id],
                signatures=[venue_id],
                signatories=[],
                members=[]))
            

    def set_impersonators(self, impersonators):
        return self.post_group(openreview.api.Group(
            id = self.journal.venue_id,
            impersonators = impersonators
        ))
