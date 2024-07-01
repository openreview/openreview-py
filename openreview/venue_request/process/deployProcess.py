def process(client, note, invitation):
    from datetime import datetime

    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    conference = openreview.helpers.get_conference(client, note.forum, SUPPORT_GROUP, setup=True)
    conference.create_submission_stage()

    FRONTEND_URL = 'https://openreview.net' ## point always to the live site

    forum = client.get_note(id=note.forum)
    forum.writers = []
    forum = client.post_note(forum)

    readers = [conference.get_program_chairs_id(), SUPPORT_GROUP]

    recruitment_pre_preprocess = '''function(){
    // V1 invitation

    const fieldTokens = {
        "invitation_email_subject": ['invitee_role'],
        "invitation_email_content": ['fullname', 'invitee_role', 'invitation_url', 'contact_info'],
        "accepted_email_template": ['fullname', 'reviewer_name']
    };

    for (const [field, tokens] of Object.entries(fieldTokens)) {
        if (field in note.content) {
            // Check for valid tokens in curly braces
            let regex = /{([^{}]*)}/g;
            let parsedToken = '';
            let matches;
            while ((matches = regex.exec(note.content[field])) !== null) {
                parsedToken = matches[1];
                if (!parsedToken) {
                    done(`Tokens must not be empty. Please use the following tokens in ${field}: ${tokens.toString()}.`);
                }
                if (!tokens.includes(parsedToken)) {
                    done(`Invalid token: ${parsedToken} in ${field} is not supported. Please use the following tokens in this field: ${tokens.toString()}.`);
                }
            }

            // Check for tokens that don't have double curly braces, raise an error.
            for (const token of tokens) {
                regex = new RegExp(`(?<!{)[{]?${token}[}]+|[{]+${token}[}]?(?!})`, 'g');
                while ((matches = regex.exec(note.content[field])) !== null) {
                    parsedToken = matches[0];
                    done(`Invalid token: ${parsedToken} in ${field}. Tokens must be wrapped in double curly braces.`);
                }
            }
        }
    }
    done()
}
'''

    comment_invitation = client.post_invitation(openreview.Invitation(
        id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Comment',
        super=SUPPORT_GROUP + '/-/Comment',
        reply={
            'forum': forum.id,
            'replyto': None,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values': readers
            }
        },
        signatures=['~Super_User1']
    ))

    comment_note = openreview.Note(
        invitation = SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Comment',
        forum = forum.id,
        replyto = forum.id,
        readers = readers,
        writers = [SUPPORT_GROUP],
        signatures = [SUPPORT_GROUP],
        content = {
            'title': 'Your venue is available in OpenReview',
            'comment': '''
Hi Program Chairs,

Thank you for choosing OpenReview to host your upcoming venue.

We recommend making authors aware of OpenReview's moderation policy for newly created profiles in the Call for Papers:
- New profiles created without an institutional email will go through a moderation process that **can take up to two weeks**.
- New profiles created with an institutional email will be activated automatically.

We have set up the venue based on the information that you provided here: {baseurl}/forum?id={noteId}

You can use the following links to access the venue:

- Venue home page: {baseurl}/group?id={conference_id}
- Venue Program Chairs console: {baseurl}/group?id={program_chairs_id}

If you need to make a change to the information provided in your request form, please feel free to revise it directly using the "Revision" button. You can also control several stages of your venue by using the Stage buttons. Note that any change you make will be immediately applied to your venue.
If you have any questions, please refer to our FAQ: https://openreview.net/faq

If you need special features that are not included in your request form, you can post a comment here or contact us at info@openreview.net and we will assist you. We recommend reaching out to us well in advance and setting deadlines for a Monday.  

**OpenReview support is responsive from 9AM - 5PM EST Monday through Friday**. Requests made on weekends or US holidays can expect to receive a response on the next business day.

Best,


The OpenReview Team
            '''.format(baseurl = FRONTEND_URL, noteId = forum.id, conference_id = conference.get_id(), program_chairs_id = conference.get_program_chairs_id())
        }
    )
    client.post_note(comment_note)

    revision_invitation = client.post_invitation(openreview.Invitation(
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
    if forum.content.get('abstract_registration_deadline') and forum.content.get('api_version') =='2' :
        content = revision_invitation.reply['content']
        content['Additional Submission Options']['description'] = 'Configure additional options in the abstract registration form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
        content['remove_submission_options']['description'] = 'Fields to remove from the abstract registration form: abstract, keywords, pdf, TL;DR'
        content['second_deadline_additional_options'] = {
            'order': 23,
            'value-dict': {},
            'description': 'Configure additional options in the full submission form. Use lowercase for the field names and underscores to represent spaces. The UI will auto-format the names, for example: supplementary_material -> Supplementary Material. Valid JSON expected.'
        }
        content['second_deadline_remove_options'] = {
            'order': 23,
            'values-dropdown':  ['abstract','keywords', 'pdf', 'TL;DR'],
            'description': 'Fields to remove from the full submission form: abstract, keywords, pdf, TL;DR'
        }
        revision_invitation.reply['content'] = content
        client.post_invitation(revision_invitation)

    recruitment_email_subject = '[{Abbreviated_Venue_Name}] Invitation to serve as {{invitee_role}}'.replace('{Abbreviated_Venue_Name}', conference.get_short_name())
    recruitment_links = '''To ACCEPT the invitation, please click on the following link:

{{accept_url}}

To DECLINE the invitation, please click on the following link:

{{decline_url}}'''

    if conference.use_recruitment_template:
        recruitment_links = '''To respond the invitation, please click on the following link:

{{invitation_url}}'''

    recruitment_email_body = '''Dear {{fullname}},

You have been nominated by the program chair committee of {Abbreviated_Venue_Name} to serve as {{invitee_role}}. As a respected researcher in the area, we hope you will accept and help us make {Abbreviated_Venue_Name} a success.

You are also welcome to submit papers, so please also consider submitting to {Abbreviated_Venue_Name}.

We will be using OpenReview.net with the intention of have an engaging reviewing process inclusive of the whole community.

{recruitment_links}

Please answer within 10 days.

If you accept, please make sure that your OpenReview account is updated and lists all the emails you are using.  Visit http://openreview.net/profile after logging in.

If you have any questions, please contact {{contact_info}}.

Cheers!

Program Chairs'''.replace('{Abbreviated_Venue_Name}', conference.get_short_name()).replace('{recruitment_links}', recruitment_links)

    accepted_email = '''Thank you for accepting the invitation to be a {{reviewer_name}} for {SHORT_PHRASE}.

The {SHORT_PHRASE} program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.'''.replace('{SHORT_PHRASE}', conference.get_short_name())

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
                    'value-dropdown': conference.get_roles(),
                    'default': conference.get_roles()[0],
                    'required': True,
                    'order': 2
                },
                'invitee_reduced_load': {
                    'description': 'Please enter a comma separated list of reduced load options. When an invitee responds to the reviewing invitation, they will be able to choose a reduced load from this list. Note: This will set the reduced load for everyone in the selected role. If you set a new reduced load for this role in a different recruitment batch, then the value will get overwritten.',
                    'values-regex': '[0-9]+',
                    'default': ['1', '2', '3'],
                    'required': False,
                    'order': 5
                },
                'invitee_details': {
                    'value-regex': '[\\S\\s]{1,50000}',
                    'description': 'Enter a list of invitees with one per line. Either tilde IDs (∼Captain_America1), emails (captain_rogers@marvel.com), or email,name pairs (captain_rogers@marvel.com, Captain America) expected. If only an email address is provided for an invitee, the recruitment email is addressed to "Dear invitee". Do not use parentheses in your list of invitees.',
                    'required': True,
                    'order': 6
                },
                'invitation_email_subject': {
                    'value-regex': '.*',
                    'description': 'Please carefully review the email subject for the recruitment emails. Make sure not to remove the parenthesized tokens.',
                    'order': 7,
                    'required': True,
                    'default': recruitment_email_subject
                },
                'invitation_email_content': {
                    'value-regex': '[\\S\\s]{1,10000}',
                    'description': 'Please carefully review the template below before you click submit to send out recruitment emails. Make sure not to remove the parenthesized tokens.',
                    'order': 8,
                    'required': True,
                    'default': recruitment_email_body
                },
                'accepted_email_template': {
                    'value-regex': '[\\S\\s]{1,10000}',
                    'description': 'Please review the email sent to users when they accept a recruitment invitation. Make sure not to remove the parenthesized tokens.',
                    'order': 9,
                    'hidden': True,
                    'default': accepted_email
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
                    'value-dropdown': conference.get_roles(),
                    'default': conference.get_roles()[0],
                    'required': True,
                    'order': 2
                },
                'invitee_reduced_load': {
                    'description': 'Please enter a comma separated list of reduced load options. If an invitee declines the reviewing invitation, they will be able to choose a reduced load from this list.',
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
                },
                'accepted_email_template': {
                    'value-regex': '[\\S\\s]{1,10000}',
                    'description': 'Please review the email sent to users when they accept a recruitment invitation. Make sure not to remove the parenthesized tokens.',
                    'order': 8,
                    'hidden': True,
                    'default': accepted_email
                }
            }
        },
        signatures = ['~Super_User1'] ##Temporarily use the super user, until we can get a way to send email to invitees
    )

    if isinstance(conference, openreview.venue.Venue) or isinstance(conference, openreview.arr.ARR):
        recruitment_invitation.preprocess = recruitment_pre_preprocess
        remind_recruitment_invitation.preprocess = recruitment_pre_preprocess

        recruitment_invitation.reply['content']['allow_accept_with_reduced_load'] = {
            'description': 'Select "yes" if you want invited Reviewers to choose their reduced load upon acceptance, otherwise this will default to selecting a reduced load when the user declines.',
            'value-radio': ['Yes', 'No'],
            'default': 'No',
            'required': False,
            'order': 4
        }

    if len(conference.get_roles()) > 1:
        recruitment_invitation.reply['content']['allow_role_overlap'] = {
            'description': 'Do you want to allow the overlap of users in different roles? Selecting "Yes" would allow a user to be invited to serve as both a Reviewer and Area Chair.',
            'value-radio': ['Yes', 'No'],
            'default': 'No',
            'required': False,
            'order': 3
        }

    client.post_invitation(recruitment_invitation)
    client.post_invitation(remind_recruitment_invitation)

    bid_stage_content = {
        'bid_start_date': {
            'description': 'When does bidding on submissions begin? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
            'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$'
        },
        'bid_due_date': {
            'description': 'When does bidding on submissions end? Please enter a time and date in GMT using the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
            'value-regex': r'^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
            'required': True
        },
        'bid_count': {
            'description': 'Minimum bids one should make to mark bidding task completed for them. Default is 50.',
            'value-regex': '[0-9]*'
        }
    }
    if 'Yes' in forum.content.get('senior_area_chairs', 'No') and 'Submissions' == forum.content.get('senior_area_chairs_assignment', 'Area Chairs'):
        bid_stage_content['sac_bidding']= {
            'description': 'Do you want to allow senior area chairs to bid on papers?',
            'value-radio': ['Yes', 'No'],
            'default': 'No',
            'required': False
        }
    client.post_invitation(openreview.Invitation(
        id = SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Bid_Stage',
        super = SUPPORT_GROUP + '/-/Bid_Stage',
        invitees = readers,
        reply = {
            'forum': forum.id,
            'referent': forum.id,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            },
            'content': bid_stage_content
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

    if (forum.content.get('ethics_chairs_and_reviewers') == 'Yes, our venue has Ethics Chairs and Reviewers'):
        client.post_invitation(openreview.Invitation(
            id = SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Ethics_Review_Stage',
            super = SUPPORT_GROUP + '/-/Ethics_Review_Stage',
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
    submission_revision_readers = []
    submission_revision_readers.extend(readers)
    if forum.content.get('api_version') == '2' and forum.content.get('publication_chairs', 'No') == 'Yes, our venue has Publication Chairs':
        submission_revision_readers.append(conference.get_publication_chairs_id())
    client.post_invitation(openreview.Invitation(
        id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Submission_Revision_Stage',
        super=SUPPORT_GROUP + '/-/Submission_Revision_Stage',
        invitees=submission_revision_readers,
        reply={
            'forum': forum.id,
            'referent': forum.id,
            'readers' : {
                'description': 'The users who will be allowed to read the above content.',
                'values' : submission_revision_readers
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

    # always post Paper_Matching_Setup invitation
    matching_group_ids = [conference.get_committee_id(r) for r in conference.reviewer_roles]
    if conference.use_area_chairs:
        area_chairs = [conference.get_committee_id(r) for r in conference.area_chair_roles]
        matching_group_ids = matching_group_ids + area_chairs
    if conference.use_senior_area_chairs:
        senior_area_chairs = [conference.get_committee_id(r) for r in conference.senior_area_chair_roles]
        matching_group_ids = matching_group_ids + senior_area_chairs
    matching_invitation = openreview.Invitation(
        id = SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Paper_Matching_Setup',
        super = SUPPORT_GROUP + '/-/Paper_Matching_Setup',
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
                    'value': 'Paper Matching Setup',
                    'required': True,
                    'order': 1
                },
                'matching_group': {
                    'description': 'Please select the group you want to set up matching for.',
                    'value-dropdown' : matching_group_ids,
                    'required': True,
                    'order': 2
                },
                'compute_conflicts': {
                    'description': 'Please select whether you want to compute conflicts of interest between the matching group and submissions. Select the conflict policy below or "No" if you don\'t want to compute conflicts.',
                    'value-radio': ['Default', 'NeurIPS', 'No'],
                    'required': True,
                    'order': 3
                },
                'compute_conflicts_N_years': {
                    'description': 'If conflict policy was selected, enter the number of the years we should use to get the information from the OpenReview profile in order to detect conflicts. Leave it empty if you want to use all the available information.',
                    'value-regex': '[0-9]+',
                    'required': False,
                    'order': 4
                },            
                'compute_affinity_scores': {
                    'description': 'Please select whether you would like affinity scores to be computed and uploaded automatically. Select the model you want to use to compute the affinity scores or "No" if you don\'t want to compute affinity scores. The model "specter2+scincl" has the best performance, refer to our expertise repository for more information on the models: https://github.com/openreview/openreview-expertise.',
                    'order': 5,
                    'value-radio': ['specter+mfr', 'specter2', 'scincl', 'specter2+scincl','No'],
                    'required': True,
                },
                'upload_affinity_scores': {
                    'description': 'If you would like to use your own affinity scores, upload a CSV file containing affinity scores for reviewer-paper pairs (one reviewer-paper pair per line in the format: submission_id, reviewer_id, affinity_score)',
                    'order': 6,
                    'value-file': {
                        'fileTypes': ['csv'],
                        'size': 50
                    },
                    'required': False
                }
            }
        },
        signatures = ['~Super_User1']
    )
    print('posting paper matching setup invitation!!')
    client.post_invitation(matching_invitation)

    replies = client.get_notes(forum=forum.id, invitation=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Comment')
    for reply in replies:
        reply.readers = readers
        client.post_note(reply)

    client.post_invitation(openreview.Invitation(
        id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Recruitment_Status',
        super=SUPPORT_GROUP + '/-/Recruitment_Status',
        reply={
            'forum': forum.id,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values': readers
            }
        },
        signatures=['~Super_User1']
    ))

    client.post_invitation(openreview.Invitation(
        id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Remind_Recruitment_Status',
        super=SUPPORT_GROUP + '/-/Remind_Recruitment_Status',
        reply={
            'forum': forum.id,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values': readers
            }
        },
        signatures=['~Super_User1']
    ))

    client.post_invitation(openreview.Invitation(
        id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Paper_Matching_Setup_Status',
        super=SUPPORT_GROUP + '/-/Paper_Matching_Setup_Status',
        reply={
            'forum': forum.id,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values': readers
            }
        },
        signatures=['~Super_User1']
    ))

    client.post_invitation(openreview.Invitation(
        id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Stage_Error_Status',
        super=SUPPORT_GROUP + '/-/Stage_Error_Status',
        reply={
            'forum': forum.id,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values': readers
            }
        },
        signatures=['~Super_User1']
    ))

    client.post_invitation(openreview.Invitation(
        id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Decision_Upload_Status',
        super=SUPPORT_GROUP + '/-/Decision_Upload_Status',
        reply={
            'forum': forum.id,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values': readers
            }
        },
        signatures=['~Super_User1']
    ))

    if forum.content.get('api_version') == '2':

        if forum.content.get('preferred_emails_groups', []):
            conference.invitation_builder.set_preferred_emails_invitation()
            conference.group_builder.create_preferred_emails_readers_group()
        
        # registration task stages
        client.post_invitation(openreview.Invitation(
            id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Reviewer_Registration',
            super=SUPPORT_GROUP + '/-/Reviewer_Registration',
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

        if (forum.content.get('Area Chairs (Metareviewers)') == "Yes, our venue has Area Chairs"):
            client.post_invitation(openreview.Invitation(
            id=SUPPORT_GROUP + '/-/Request' + str(forum.number) + '/Area_Chair_Registration',
            super=SUPPORT_GROUP + '/-/Area_Chair_Registration',
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

