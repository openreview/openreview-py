import openreview
from enum import Enum
from datetime import datetime

class ARRStage(object):
    """
    Wraps around several types of stages and is used to add new actions to an ARR cycle

    Attributes:
        type (ARRStage.Type): Indicator of the underlying OpenReview class
        group_id (str, optional): Members of this group ID will be submitting or using this stage
        required_fields (list): The list of fields that must be present in the ARR configurator to modify the stage
        super_invitation_id (str): The ID of the super invitation, or the single invitation for registration stages
        stage_arguments (dict): Arguments for either the stage class or the stage note posted to the venue request form
        date_levels (int): Number of levels to traverse to update the dates 
            (registration stages have theirs at the top level=1,
            review stages need to modify the submission-level invitations at level=2)
        start_date (datetime): When the users will be able to perform this action
        due_date (datetime): If set, the date which will appear in the users' consoles
        exp_date (datetime): The date when users will no longer be able to perform the action
        extend (function): The function performs any additional changes need to be made on top of the stage
            This function must take as arguments:
                client (openreview.api.OpenReviewClient)
                venue (openreview.venue.Venue)
                invitation_builder (openreview.arr.InvitationBuilder)
                request_form_note (openreview.api.Note)


    """

    class Type(Enum):
        """
        Enum defining the possible types of stages within the process.

        Attributes:
            REGISTRATION_STAGE (0): Represents a registration phase.
            CUSTOM_STAGE (1): Represents a custom-configured phase.
            STAGE_NOTE (2): Represents an informational or note-taking phase.
        """
        REGISTRATION_STAGE = 0
        CUSTOM_STAGE = 1
        STAGE_NOTE = 2

    SUPPORTED_STAGES = {
        'Official_Review': 'Review_Stage',
        'Meta_Review': 'Meta_Review_Stage',
        'Official_Comment': 'Comment_Stage',
        'Ethics_Review': 'Ethics_Review_Stage'
    }

    def __init__(self,
        type = None,
        group_id = None,
        required_fields = None,
        super_invitation_id = None,
        stage_arguments = None,
        date_levels = None,
        start_date = None,
        due_date = None,
        exp_date = None,
        process = None,
        preprocess = None,
        extend = None
    ):
        self.type : ARRStage.Type = type
        self.group_id: str = group_id
        self.required_fields: list = required_fields
        self.super_invitation_id: str = super_invitation_id
        self.stage_arguments: dict = stage_arguments
        self.date_levels: int = date_levels
        self.extend: function = extend
        self.process: str = process
        self.preprocess: str = preprocess

        self.start_date: datetime = datetime.strptime(
            start_date, '%Y/%m/%d %H:%M:%S'
        ) if start_date is not None else start_date

        self.due_date: datetime = datetime.strptime(
            due_date, '%Y/%m/%d %H:%M:%S'
        ) if due_date is not None else due_date

        self.exp_date: datetime = datetime.strptime(
            exp_date, '%Y/%m/%d %H:%M:%S'
        ) if exp_date is not None else exp_date

        # Parse and add start dates to stage arguments
        if self.type == ARRStage.Type.CUSTOM_STAGE:
            self.stage_arguments['start_date'] = self._format_date(self.start_date)
            self.stage_arguments['due_date'] = self._format_date(self.due_date)
            self.stage_arguments['exp_date'] = self._format_date(self.exp_date)
        elif self.type == ARRStage.Type.REGISTRATION_STAGE:
            self.stage_arguments['start_date'] = self.start_date
            self.stage_arguments['due_date'] = self.due_date
            self.stage_arguments['expdate'] = self.exp_date
        elif self.type == ARRStage.Type.STAGE_NOTE:
            stage_dates = self._get_stage_note_dates(format_type='strftime')
            self.stage_arguments['content'].update(stage_dates)

    def _get_stage_note_dates(self, format_type):
        dates = {}
        if 'Official_Review' in self.super_invitation_id:
            dates['review_start_date'] = self._format_date(self.start_date, format_type)
            dates['review_deadline'] = self._format_date(self.due_date, format_type)
            dates['review_expiration_date'] = self._format_date(self.exp_date, format_type)
        elif 'Meta_Review' in self.super_invitation_id:
            dates['meta_review_start_date'] = self._format_date(self.start_date, format_type)
            dates['meta_review_deadline'] = self._format_date(self.due_date, format_type)
            dates['meta_review_expiration_date'] = self._format_date(self.exp_date, format_type)
        elif 'Ethics_Review' in self.super_invitation_id:
            dates['ethics_review_start_date'] = self._format_date(self.start_date, format_type)
            dates['ethics_review_deadline'] = self._format_date(self.due_date, format_type)
            dates['ethics_review_expiration_date'] = self._format_date(self.exp_date, format_type)
        elif 'Official_Comment' in self.super_invitation_id:
            dates['commentary_start_date'] = self._format_date(self.start_date, format_type)
            dates['commentary_end_date'] = self._format_date(self.exp_date, format_type)

        return dates

    def _format_date(self, date, format_type='millis', date_format='%Y/%m/%d'):
        if date is None:
            return None
        if format_type == 'millis':
            return openreview.tools.datetime_millis(date)
        elif format_type == 'strftime':
            return date.strftime(date_format)
        else:
            raise ValueError("Invalid format_type specified")

    def _post_new_dates(self, client, venue):
        meta_invitation_id = venue.get_meta_invitation_id()
        venue_id = venue.id
        invitation_id = self.super_invitation_id

        invitation_edit_invitation_dates = {}
        if self.start_date:
            invitation_edit_invitation_dates['cdate'] = openreview.tools.datetime_millis(self.start_date)
        if self.due_date:
            invitation_edit_invitation_dates['duedate'] = openreview.tools.datetime_millis(self.due_date)
        if self.exp_date:
            invitation_edit_invitation_dates['expdate'] = openreview.tools.datetime_millis(self.exp_date)
        if self.type == ARRStage.Type.REGISTRATION_STAGE:
            client.post_invitation_edit(
                invitations=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=openreview.api.Invitation(
                    id=invitation_id,
                    cdate=openreview.tools.datetime_millis(self.start_date),
                    duedate=openreview.tools.datetime_millis(self.due_date),
                    expdate=openreview.tools.datetime_millis(self.exp_date)
                )
            )
        elif self.type == ARRStage.Type.CUSTOM_STAGE:
            client.post_invitation_edit(
                invitations=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=openreview.api.Invitation(
                    id=invitation_id,
                    edit={
                        'invitation': invitation_edit_invitation_dates
                    }
                )
            )
        elif self.type == ARRStage.Type.STAGE_NOTE:
            domain = client.get_group(venue_id)
            client_v1 = openreview.Client(
                baseurl=openreview.tools.get_base_urls(client)[0],
                token=client.token
            )
            request_form = client_v1.get_note(domain.content['request_form_id']['value'])
            support_group = request_form.invitation.split('/-/')[0]
            invitation_name = self.super_invitation_id.split('/')[-1]
            stage_name = ARRStage.SUPPORTED_STAGES[invitation_name]

            latest_reference = client_v1.get_references(
                referent=request_form.id,
                invitation=f"{support_group}/-/Request{request_form.number}/{stage_name}"
            )[0]
            stage_dates = self._get_stage_note_dates(format_type='strftime')
            latest_reference.content.update(stage_dates)

            stage_note = openreview.Note(
                content = latest_reference.content,
                forum = latest_reference.forum,
                invitation = latest_reference.invitation,
                readers = latest_reference.readers,
                referent = latest_reference.referent,
                replyto = latest_reference.replyto,
                signatures = ['~Super_User1'],
                writers = []
            )
            client_v1.post_note(stage_note)

    def set_stage(self, client_v1, client, venue, invitation_builder, request_form_note):
        # Find invitation
        if openreview.tools.get_invitation(client, self.super_invitation_id):
            self._post_new_dates(client, venue)
        else:
            if self.type == ARRStage.Type.REGISTRATION_STAGE:
                venue.registration_stages = [openreview.stages.RegistrationStage(**self.stage_arguments)]
                venue.create_registration_stages()
                if self.process or self.preprocess:
                    invitation = openreview.api.Invitation(
                        id=self.super_invitation_id,
                        signatures=[venue.id],
                        process=None if not self.process else invitation_builder.get_process_content(self.process),
                        preprocess=None if not self.preprocess else invitation_builder.get_process_content(self.preprocess)
                    )
                    client.post_invitation_edit(
                        invitations=venue.get_meta_invitation_id(),
                        readers=[venue.id],
                        writers=[venue.id],
                        signatures=[venue.id],
                        invitation=invitation
                    )

            elif self.type == ARRStage.Type.CUSTOM_STAGE:
                venue.custom_stage = openreview.stages.CustomStage(**self.stage_arguments)
                invitation_builder.set_custom_stage_invitation(
                    process_script = self.process,
                    preprocess_script = self.preprocess
                )
            elif self.type == ARRStage.Type.STAGE_NOTE:
                stage_note = openreview.Note(**self.stage_arguments)
                client_v1.post_note(stage_note)

            if self.extend:
                self.extend(
                    client, venue, invitation_builder, request_form_note
                )

def setup_arr_invitations(arr_invitation_builder):
    arr_invitation_builder.set_arr_configuration_invitation()
    arr_invitation_builder.set_arr_scheduler_invitation()
    arr_invitation_builder.set_preprint_release_submission_invitation()

def flag_submission(
        client,
        edit,
        invitation,
        flagging_info
):
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_name = domain.get_content_value('subtitle')
    forum = client.get_note(id=edit.note.forum, details='replies')

    ethics_flag_field = list(flagging_info['ethics_flag_field'].keys())[0]
    violation_fields = list(flagging_info['violation_fields'].keys())
    violation_default = flagging_info['violation_fields']
    ethics_flag_default = flagging_info['ethics_flag_field'][ethics_flag_field]
    reply_name = flagging_info['reply_name']

    ethics_flag_edits = client.get_note_edits(note_id=edit.note.forum, invitation=f"{venue_id}/-/Ethics_Review_Flag")
    dsv_flag_edits = client.get_note_edits(note_id=edit.note.forum, invitation=f"{venue_id}/-/Desk_Reject_Verification_Flag")

    dsv_flagged = forum.content.get('flagged_for_desk_reject_verification', {}).get('value')
    ethics_flagged = forum.content.get('flagged_for_ethics_review', {}).get('value')
    has_ethic_flag_history = len(ethics_flag_edits) > 0
    has_dsv_flag_history = len(dsv_flag_edits) > 0

    def post_flag(invitation_name, value=False):
       return client.post_note_edit(
            invitation=f'{venue_id}/-/{invitation_name}_Flag',
            note=openreview.api.Note(
                id=edit.note.forum,
                content={f'flagged_for_{invitation_name.lower()}': {'value': value}}
            ),
            signatures=[venue_id]
        )
    
    def check_field_not_violated(note, field):
        if isinstance(violation_default[field], list):
            return note.get(field, {}).get('value', violation_default[field][0]) in violation_default[field]
        return note.get(field, {}).get('value', violation_default[field]) == violation_default[field]

    needs_ethics_review = edit.note.content.get(ethics_flag_field, {}).get('value', ethics_flag_default) != ethics_flag_default

    if edit.note.ddate:
        print('deleting note, checking for unflagged consensus')
        # Check for DSV unflagging
        checklists = list(filter(
           lambda reply: any(reply_name in inv for inv in reply['invitations']),
           forum.details['replies']
        ))

        print(f"{len(checklists)} valid responses for unflagging")

        dsv_unflag = True
        for checklist in checklists:
            dsv_unflag = dsv_unflag and all(check_field_not_violated(checklist['content'], field) for field in violation_fields)

        if dsv_unflag and has_dsv_flag_history:
            post_flag(
                'Desk_Reject_Verification',
                value = False
            )

        ethics_unflag = True
        for checklist in checklists:
            ethics_unflag = ethics_unflag and checklist['content'].get(ethics_flag_field, {}).get('value', ethics_flag_default) == ethics_flag_default

        if ethics_unflag and has_ethic_flag_history:
            post_flag(
                'Ethics_Review',
                value = False
            )
                

    # Desk Rejection Flagging
    print('checking for dsv')
    if not all(check_field_not_violated(edit.note.content, field) for field in violation_fields) and not dsv_flagged:
        print('flagging dsv')
        post_flag(
           'Desk_Reject_Verification',
           value = True
        )
    else:
        # Check for unflagging
        checklists = list(filter(
           lambda reply: any(reply_name in inv for inv in reply['invitations']),
           forum.details['replies']
        ))

        print(f"{len(checklists)} valid responses for unflagging")

        dsv_unflag = True
        for checklist in checklists:
            dsv_unflag = dsv_unflag and all(check_field_not_violated(checklist['content'], field) for field in violation_fields)

        if dsv_unflag and has_dsv_flag_history and dsv_flagged:
            post_flag(
                'Desk_Reject_Verification',
                value = False
            )
    
    # Ethics Flagging
    if needs_ethics_review and not has_ethic_flag_history:
        print('flagging ethics and emailing')
        post_flag(
           'Ethics_Review',
           value = True
        )
        subject = f'[{short_name}] A submission has been flagged for ethics reviewing'
        message = '''Paper {} has been flagged for ethics review.

        To view the submission, click here: https://openreview.net/forum?id={}'''.format(forum.number, forum.id)
        client.post_message(
            recipients=[domain.content['ethics_chairs_id']['value']],
            ignoreRecipients=[edit.tauthor],
            subject=subject,
            message=message
        )

        checklists = list(filter(
           lambda reply: any(reply_name in inv for inv in reply['invitations']),
           forum.details['replies']
        ))
        for checklist in checklists:
            new_readers = [
                domain.content['ethics_chairs_id']['value'],
                f"{venue_id}/{domain.content['ethics_reviewers_name']['value']}",
            ] + checklist['readers']
            client.post_note_edit(
                invitation=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=checklist['id'],
                    readers=new_readers
                )
            )

    elif needs_ethics_review and has_ethic_flag_history and not ethics_flagged:
       print('flagging ethics')
       post_flag(
           'Ethics_Review',
           value = True
        )
    elif not needs_ethics_review and ethics_flagged:
        # Check for unflagged
        checklists = list(filter(
            lambda reply: any(reply_name in inv for inv in reply['invitations']),
            forum.details['replies']
        ))

        print(f"{len(checklists)} valid responses for unflagging")

        ethics_unflag = True
        for checklist in checklists:
            ethics_unflag = ethics_unflag and checklist['content'].get(ethics_flag_field, {}).get('value', ethics_flag_default) == ethics_flag_default

        if ethics_unflag and has_ethic_flag_history and ethics_flagged:
            post_flag(
                'Ethics_Review',
                value = False
            )