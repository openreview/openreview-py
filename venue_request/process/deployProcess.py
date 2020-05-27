def process(client, note, invitation):
    print('client:', client.baseurl)
    print('note:', note.id)
    print('invitation:', invitation.id)
    conference = openreview.helpers.get_conference(client, note.forum)
    conference_group = client.get_group(conference.get_id())
    print(conference_group.id)
    client.add_members_to_group(conference_group, "OpenReview.net/Support")

    forum = client.get_note(id=note.forum)
    comment_readers = forum.content.get('Contact Emails', []) + forum.content.get('program_chair_emails', []) + ['OpenReview.net/Support']
    comment_note = openreview.Note(
        invitation = 'OpenReview.net/Support/-/Request' + str(forum.number) + '/Comment',
        forum = forum.id,
        replyto = forum.id,
        readers = comment_readers,
        writers = ['OpenReview.net/Support'],
        signatures = ['OpenReview.net/Support'],
        content = {
            'title': 'Your venue is available in OpenReview',
            'comment': '''
Hi Program Chairs,

Thanks for submitting a venue request.

We have set up the venue based on the information that you provided here: {baseurl}/forum?id={noteId}

You can use the following links to access to the venue:

Venue home page: {baseurl}/group?id={conference_id}
Venue Program Chairs console: {baseurl}/group?id={program_chairs_id}

If you need to make a change to the information provided in your request form, please feel free to revise it directly. You can also control several stages of your venue by using the Stage buttons. Note that any change you make will be immediately applied to your venue.

If you need special features that are not included in your request form, you can post a comment here or contact us at info@openreview.net and we will assist you.

Thanks!

OpenReview Team
            '''.format(baseurl = client.baseurl, noteId = forum.id, conference_id = conference.get_id(), program_chairs_id = conference.get_program_chairs_id())
        }
    )
    client.post_note(comment_note)

    forum.writers = []
    forum = client.post_note(forum)

    readers = [conference.get_program_chairs_id(), 'OpenReview.net/Support']

    revision_invitation = client.post_invitation(openreview.Invitation(
        id = 'OpenReview.net/Support/-/Request' + str(forum.number) + '/Revision',
        super = 'OpenReview.net/Support/-/Revision',
        invitees = readers,
        reply = {
            'forum': forum.id,
            'referent': forum.id,
            'readers' : {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            }
        },
        signatures = ['OpenReview.net/Support']
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
        id = 'OpenReview.net/Support/-/Request' + str(forum.number) + '/Recruitment',
        super = 'OpenReview.net/Support/-/Recruitment',
        invitees = readers,
        reply = {
            'forum': forum.id,
            'replyto': forum.id,
            'readers' : {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            },'writers': {
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
                'invitee_details': {
                    'value-regex': '[\\S\\s]{1,50000}',
                    'description': 'Email,Name pairs expected with each line having only one invitee\'s details. E.g. captain_rogers@marvel.com, Captain America',
                    'required': True,
                    'order': 3
                },
                'invitation_email_subject': {
                    'value-regex': '.*',
                    'description': 'Please carefully review the email subject for the recruitment emails. Make sure not to remove the parenthesized tokens.',
                    'order': 4,
                    'required': True,
                    'default': recruitment_email_subject
                },
                'invitation_email_content': {
                    'value-regex': '[\\S\\s]{1,10000}',
                    'description': 'Please carefully review the template below before you click submit to send out recruitment emails. Make sure not to remove the parenthesized tokens.',
                    'order': 5,
                    'required': True,
                    'default': recruitment_email_body
                }
            }
        },
        signatures = ['~Super_User1'] ##Temporarily use the super user, until we can get a way to send email to invitees
    )

    if (forum.content['Area Chairs (Metareviewers)'] == "Yes, our venue has Area Chairs") :
        recruitment_invitation.reply['content']['invitee_role']['value-radio'] = ['reviewer', 'area chair']

    posted_recruitment_invitation = client.post_invitation(recruitment_invitation)

    if 'Reviewer Bid Scores' in forum.content.get('Paper Matching', []):
        bid_stage_invitation = client.post_invitation(openreview.Invitation(
            id = 'OpenReview.net/Support/-/Request' + str(forum.number) + '/Bid_Stage',
            super = 'OpenReview.net/Support/-/Bid_Stage',
            invitees = readers,
            reply = {
                'forum': forum.id,
                'referent': forum.id,
                'readers' : {
                    'description': 'The users who will be allowed to read the above content.',
                    'values' : readers
                }
            },
            signatures = ['OpenReview.net/Support']
        ))

    review_stage_content = None
    if forum.content.get('Open Reviewing Policy', None) == 'Submissions and reviews should both be public.':
        review_stage_content = {
            'review_start_date': {
                'description': 'When does reviewing of submissions begin? Please use the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': '^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'order': 10
            },
            'review_deadline': {
                'description': 'When does reviewing of submissions end? Please use the following format: YYYY/MM/DD HH:MM (e.g. 2019/01/31 23:59)',
                'value-regex': '^[0-9]{4}\/([1-9]|0[1-9]|1[0-2])\/([1-9]|0[1-9]|[1-2][0-9]|3[0-1])(\s+)?((2[0-3]|[01][0-9]|[0-9]):[0-5][0-9])?(\s+)?$',
                'required': True,
                'order': 11
            },
            'make_reviews_public': {
                'description': 'Should the reviews be made public immediately upon posting? Based on your earlier selections, default is "Yes, reviews should be revealed publicly when they are posted".',
                'value-radio': [
                    'Yes, reviews should be revealed publicly when they are posted',
                    'No, reviews should NOT be revealed publicly when they are posted'
                ],
                'required': True,
                'default': 'Yes, reviews should be revealed publicly when they are posted',
                'order': 24
            },
            'release_reviews_to_authors': {
                'description': 'Should the reviews be visible to paper\'s authors immediately upon posting? Based on your earlier selections, default is "Yes, reviews should be revealed publicly when they are posted".',
                'value-radio': [
                    'Yes, reviews should be revealed when they are posted to the paper\'s authors',
                    'No, reviews should NOT be revealed when they are posted to the paper\'s authors'
                ],
                'required': True,
                'default': 'Yes, reviews should be revealed publicly when they are posted',
                'order': 25
            },
            'release_reviews_to_reviewers': {
                'description': 'Should the reviews be visible immediately upon posting to paper\'s reviewers regardless of whether they have reviewed the paper or not? Based on your earlier selections, default is "Yes, reviews should be immediately revealed to the all paper\'s reviewers".',
                'value-radio': [
                    'Yes, reviews should be immediately revealed to the all paper\'s reviewers',
                    'No, reviews should be immediately revealed only to the reviewers who have already reviewed the paper'
                ],
                'required': True,
                'default': 'Yes, reviews should be immediately revealed to the all paper\'s reviewers',
                'order': 26
            },
            'email_program_chairs_about_reviews': {
                'description': 'Should Program Chairs be emailed when each review is received? Default is "No, do not email program chairs about received reviews".',
                'value-radio': [
                    'Yes, email program chairs for each review received',
                    'No, do not email program chairs about received reviews'],
                'required': True,
                'default': 'No, do not email program chairs about received reviews',
                'order': 27
            },
            'additional_review_form_options': {
                'order' : 28,
                'value-dict': {},
                'required': False,
                'description': 'Configure additional options in the review form. Valid JSON expected.'
            },
            'remove_review_form_options': {
                'order': 29,
                'value-regex': '^[^,]+(,\s*[^,]*)*$',
                'required': False,
                'description': 'Comma separated list of fields (review, rating, confidence) that you want removed from the review form.'
            }
        }

    review_stage_invitation = client.post_invitation(openreview.Invitation(
        id = 'OpenReview.net/Support/-/Request' + str(forum.number) + '/Review_Stage',
        super = 'OpenReview.net/Support/-/Review_Stage',
        invitees = readers,
        reply = {
            'forum': forum.id,
            'referent': forum.id,
            'readers': {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            },
            'content': review_stage_content
        },
        signatures = ['OpenReview.net/Support']
    ))

    if (forum.content['Area Chairs (Metareviewers)'] == "Yes, our venue has Area Chairs") :
        metareview_stage_invitation = client.post_invitation(openreview.Invitation(
            id = 'OpenReview.net/Support/-/Request' + str(forum.number) + '/Meta_Review_Stage',
            super = 'OpenReview.net/Support/-/Meta_Review_Stage',
            invitees = readers,
            reply = {
                'forum': forum.id,
                'referent': forum.id,
                'readers' : {
                    'description': 'The users who will be allowed to read the above content.',
                    'values' : readers
                }
            },
            signatures = [conference.get_program_chairs_id()]
        ))

    decision_stage_invitation = client.post_invitation(openreview.Invitation(
        id = 'OpenReview.net/Support/-/Request' + str(forum.number) + '/Decision_Stage',
        super = 'OpenReview.net/Support/-/Decision_Stage',
        invitees = readers,
        reply = {
            'forum': forum.id,
            'referent': forum.id,
            'readers' : {
                'description': 'The users who will be allowed to read the above content.',
                'values' : readers
            }
        },
        signatures = ['OpenReview.net/Support']
    ))
