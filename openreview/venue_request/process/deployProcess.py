def process(client, note, invitation):
    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    conference = openreview.helpers.get_conference(client, note.forum, SUPPORT_GROUP)
    conference_group = client.get_group(conference.get_id())
    FRONTEND_URL = 'https://openreview.net' ## point always to the live site

    client.add_members_to_group(conference_group, SUPPORT_GROUP)

    forum = client.get_note(id=note.forum)
    comment_readers = forum.content.get('Contact Emails', []) + forum.content.get('program_chair_emails', []) + [SUPPORT_GROUP]
    comment_note = openreview.Note(
        invitation = SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Comment',
        forum = forum.id,
        replyto = forum.id,
        readers = comment_readers,
        writers = [SUPPORT_GROUP],
        signatures = [SUPPORT_GROUP],
        content = {
            'title': 'Your venue is available in OpenReview',
            'comment': '''
Hi Program Chairs,

Thank you for choosing OpenReview to host your upcoming venue.

We have set up the venue based on the information that you provided here: {baseurl}/forum?id={noteId}

You can use the following links to access the venue:

- Venue home page: {baseurl}/group?id={conference_id}
- Venue Program Chairs console: {baseurl}/group?id={program_chairs_id}

If you need to make a change to the information provided in your request form, please feel free to revise it directly using the "Revision" button. You can also control several stages of your venue by using the Stage buttons. Note that any change you make will be immediately applied to your venue.
If you have any questions, please refer to our FAQ: https://openreview.net/faq

If you need special features that are not included in your request form, you can post a comment here or contact us at info@openreview.net and we will assist you.

Best,


The OpenReview Team
            '''.format(baseurl = FRONTEND_URL, noteId = forum.id, conference_id = conference.get_id(), program_chairs_id = conference.get_program_chairs_id())
        }
    )
    client.post_note(comment_note)

    forum.writers = []
    forum = client.post_note(forum)

    readers = [conference.get_program_chairs_id(), SUPPORT_GROUP]

    client.post_invitation(openreview.Invitation(
        id = SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Revision',
        super = SUPPORT_GROUP + '/-/Revision',
        invitees = readers,
        reply = {
            'forum': forum.id,
            'referent': forum.id,
            'readers' : {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            }
        },
        signatures = ['~Super_User1']
    ))

    recruitment_email_subject = '[{Abbreviated_Venue_Name}] Invitation to serve as {invitee_role}'.replace('{Abbreviated_Venue_Name}', conference.get_short_name())
    recruitment_email_body = '''Dear {name},

You have been nominated by the program chair committee of {Abbreviated_Venue_Name} to serve as {invitee_role}. As a respected researcher in the area, we hope you will accept and help us make {Abbreviated_Venue_Name} a success.

You are also welcome to submit papers, so please also consider submitting to {Abbreviated_Venue_Name}.

We will be using OpenReview.net with the intention of have an engaging reviewing process inclusive of the whole community.

To ACCEPT the invitation, please click on the following link:

{accept_url}

To DECLINE the invitation, please click on the following link:

{decline_url}

Please answer within 10 days.

If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using.  Visit http://openreview.net/profile after logging in.

If you have any questions, please contact info@openreview.net.

Cheers!

Program Chairs'''.replace('{Abbreviated_Venue_Name}', conference.get_short_name())

    recruitment_invitation = openreview.Invitation(
        id = SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Recruitment',
        super = SUPPORT_GROUP + '/-/Recruitment',
        invitees = readers,
        reply = {
            'forum': forum.id,
            'replyto': forum.id,
            'readers' : {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            },
            'writers': {
                'values':[],
            },
            'content': {
                'title': {
                    'value': 'Recruitment',
                    'required': True,
                    'order': 1
                },
                'invitee_role': {
                    'description': 'Please select the role of the invitees in the venue.',
                    'value-radio': ['reviewer'],
                    'default': 'reviewer',
                    'required': True,
                    'order': 2
                },
                'invitee_reduced_load': {
                    'description': 'Please enter a comma separated list of reduced load options. If an invitee declines the reviewing invitation, they will be able to choose a reduced load from this list. (For reviewer role only)',
                    'values-regex': '[0-9]+',
                    'default': ['1', '2', '3'],
                    'required': False,
                    'order': 3
                },
                'invitee_details': {
                    'value-regex': '[\\S\\s]{1,50000}',
                    'description': 'Email,Name pairs expected with each line having only one invitee\'s details. E.g. captain_rogers@marvel.com, Captain America',
                    'required': True,
                    'order': 4
                },
                'invitation_email_subject': {
                    'value-regex': '.*',
                    'description': 'Please carefully review the email subject for the recruitment emails. Make sure not to remove the parenthesized tokens.',
                    'order': 5,
                    'required': True,
                    'default': recruitment_email_subject
                },
                'invitation_email_content': {
                    'value-regex': '[\\S\\s]{1,10000}',
                    'description': 'Please carefully review the template below before you click submit to send out recruitment emails. Make sure not to remove the parenthesized tokens.',
                    'order': 6,
                    'required': True,
                    'default': recruitment_email_body
                }
            }
        },
        signatures = ['~Super_User1'] ##Temporarily use the super user, until we can get a way to send email to invitees
    )

    remind_recruitment_invitation = openreview.Invitation(
        id = SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Remind_Recruitment',
        super = SUPPORT_GROUP + '/-/Remind_Recruitment',
        invitees = readers,
        reply = {
            'forum': forum.id,
            'replyto': forum.id,
            'readers' : {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            },
            'content': {
                'title': {
                    'value': 'Remind Recruitment',
                    'required': True,
                    'order': 1
                },
                'invitee_role': {
                    'description': 'Please select the role of the invitees you would like to remind.',
                    'value-radio': ['reviewer'],
                    'default': 'reviewer',
                    'required': True,
                    'order': 2
                },
                'invitee_reduced_load': {
                    'description': 'Please enter a comma separated list of reduced load options. If an invitee declines the reviewing invitation, they will be able to choose a reduced load from this list. (For reviewer role only)',
                    'values-regex': '[0-9]+',
                    'default': ['1', '2', '3'],
                    'required': False,
                    'order': 3
                },
                'invitation_email_subject': {
                    'value-regex': '.*',
                    'description': 'Please carefully review the email subject for the reminder emails. Make sure not to remove the parenthesized tokens.',
                    'order': 4,
                    'required': True,
                    'default': recruitment_email_subject
                },
                'invitation_email_content': {
                    'value-regex': '[\\S\\s]{1,10000}',
                    'description': 'Please carefully review the template below before you click submit to send out reminder emails. Make sure not to remove the parenthesized tokens.',
                    'order': 5,
                    'required': True,
                    'default': recruitment_email_body
                }
            }
        },
        signatures = ['~Super_User1'] ##Temporarily use the super user, until we can get a way to send email to invitees
    )

    if (forum.content.get('Area Chairs (Metareviewers)') == "Yes, our venue has Area Chairs") :
        recruitment_invitation.reply['content']['invitee_role']['value-radio'] = ['reviewer', 'area chair']
        remind_recruitment_invitation.reply['content']['invitee_role']['value-radio'] = ['reviewer', 'area chair']
        if (forum.content.get('senior_area_chairs') == "Yes, our venue has Senior Area Chairs") :
            recruitment_invitation.reply['content']['invitee_role']['value-radio'] = ['reviewer', 'area chair', 'senior area chair']
            remind_recruitment_invitation.reply['content']['invitee_role']['value-radio'] = ['reviewer', 'area chair', 'senior area chair']

    client.post_invitation(recruitment_invitation)
    client.post_invitation(remind_recruitment_invitation)

    if 'Reviewer Bid Scores' in forum.content.get('Paper Matching', []):
        client.post_invitation(openreview.Invitation(
            id = SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Bid_Stage',
            super = SUPPORT_GROUP + '/-/Bid_Stage',
            invitees = readers,
            reply = {
                'forum': forum.id,
                'referent': forum.id,
                'readers' : {
                    'description': 'The users who will be allowed to read the above content.',
                    'values' : readers
                }
            },
            signatures = ['~Super_User1']
        ))

    client.post_invitation(openreview.Invitation(
        id = SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Review_Stage',
        super = SUPPORT_GROUP + '/-/Review_Stage',
        invitees = readers,
        reply = {
            'forum': forum.id,
            'referent': forum.id,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            }
        },
        signatures = ['~Super_User1']
    ))

    if (forum.content.get('Area Chairs (Metareviewers)') == "Yes, our venue has Area Chairs") :
        client.post_invitation(openreview.Invitation(
            id = SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Meta_Review_Stage',
            super = SUPPORT_GROUP + '/-/Meta_Review_Stage',
            invitees = readers,
            reply = {
                'forum': forum.id,
                'referent': forum.id,
                'readers' : {
                    'description': 'The users who will be allowed to read the above content.',
                    'values' : readers
                }
            },
            signatures = ['~Super_User1']
        ))

    # decision_stage_invitation
    client.post_invitation(openreview.Invitation(
        id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Decision_Stage',
        super=SUPPORT_GROUP + '/-/Decision_Stage',
        invitees=readers,
        reply={
            'forum': forum.id,
            'referent': forum.id,
            'readers' : {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            }
        },
        signatures=['~Super_User1']
    ))

    # comment_stage_invitation
    client.post_invitation(openreview.Invitation(
        id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Comment_Stage',
        super=SUPPORT_GROUP + '/-/Comment_Stage',
        reply={
            'forum': forum.id,
            'referent': forum.id,
            'readers' : {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            }
        },
        signatures=['~Super_User1']
    ))

    # revision_stage_invitation
    client.post_invitation(openreview.Invitation(
        id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Submission_Revision_Stage',
        super=SUPPORT_GROUP + '/-/Submission_Revision_Stage',
        invitees=readers,
        reply={
            'forum': forum.id,
            'referent': forum.id,
            'readers' : {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            }
        },
        signatures=['~Super_User1']
    ))

    # post submission stage
    client.post_invitation(openreview.Invitation(
        id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Post_Submission',
        super=SUPPORT_GROUP + '/-/Post_Submission',
        invitees=readers,
        reply={
            'forum': forum.id,
            'referent': forum.id,
            'readers' : {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            }
        },
        signatures=['~Super_User1']
    ))
