Conference Builder
==================

Tool to configure a conference from scratch, this builder is still in progress.

Create a builder
----------------

Create an instance of the conference builder. This requires to have an OpenReview client.

	>>> builder = openreview.conference.ConferenceBuilder(client)

Set conference properties
-------------------------

Set the properties that we need to start the conference

    >>> builder.set_conference_id('AKBC.ws/2019/Conference')
    >>> builder.set_conference_name('Automated Knowledge Base Construction')
    >>> builder.set_homepage_header({
    >>>     'title': 'AKBC 2019',
    >>>     'subtitle': 'Automated Knowledge Base Construction',
    >>>     'location': 'Amherst, Massachusetts, United States',
    >>>     'date': 'May 20 - May 21, 2019',
    >>>     'website': 'http://www.akbc.ws/2019/',
    >>>     'instructions': '<p><strong>Important Information</strong>\
    >>>         <ul>\
    >>>         <li>Note to Authors, Reviewers and Area Chairs: Please update your OpenReview profile to have all your recent emails.</li>\
    >>>         <li>AKBC 2019 Conference submissions are now open.</li>\
    >>>         <li>For more details refer to the <a href="http://www.akbc.ws/2019/cfp/">AKBC 2019 - Call for Papers</a>.</li>\
    >>>         </ul></p> \
    >>>         <p><strong>Questions or Concerns</strong></p>\
    >>>         <p><ul>\
    >>>         <li>Please contact the AKBC 2019 Program Chairs at \
    >>>         <a href="mailto:info@akbc.ws">info@akbc.ws</a> with any questions or concerns about conference administration or policy.</li>\
    >>>         <li>Please contact the OpenReview support team at \
    >>>         <a href="mailto:info@openreview.net">info@openreview.net</a> with any questions or concerns about the OpenReview platform.</li>\
    >>>         </ul></p>',
    >>>     'deadline': 'Submission Deadline: Midnight Pacific Time, Friday, October 5, 2019'
    >>> })
    >>> conference = builder.set_double_blind(True)
    >>> conference = builder.set_submission_public(True)
    >>> conference = builder.get_result()

this will setup the home page of the conference: https://opereview.net/group?id=AKBC.ws/2019/Conference

Set Program Chairs
------------------

Set the members of the program chair committee

    >>> conference.set_program_chairs(['pc@mail.com', 'pc2@mail.com'])


Open Submissions
----------------

This call will setup an invitation to submit papers following the conference type, in this case is double blind, and with the submission deadline for Friday, October 5, 2019

    >>> invitation = conference.open_submissions(due_date = datetime.datetime(2019, 10, 5, 23, 59))



Close Submissions
-----------------

The submission will be closed when the current date passes the due date specified in open submissions call. In this case it will force the close of the submissions and it will disable the adition and edition of the papers by the authors. They can not edit the submission anymore

    >>> invitation = conference.close_submissions()


Recruit Reviewers
-----------------

Invite reviewers or area chairs to be part of the conference committee

    >>> conference.recruit_reviewers(['mbok@mail.com', 'mohit@mail.com'])

This will send an email to the reviewers asking for a response to accept or reject the invitation. You can specify the text of the email:

    >>> title = 'Invitation to review'
    >>> message = '''
    >>> Thank you for accepting our invitation to be an Area Chair for the AKBC. With this email, we are inviting you to log on to the OpenReview.
    >>>
    >>> To ACCEPT the invitation, please click on the following link:
    >>>
    >>> {accept_url}
    >>>
    >>> If you changed your mind please DECLINE the invitation by clicking on the following link:
    >>>
    >>> {decline_url}
    >>>
    >>> We’d appreciate an answer within five days. If you have any questions please contact AKBC Program Chairs at <program-chairs@mail.com>.
    >>>
    >>> We are looking forward to your reply.
    >>>
    >>> AKBC Program Chairs
    >>>
    >>> '''
    >>> conference.recruit_reviewers(emails = ['ac1@mail.com', 'ac2@mail.com'], title = title, message = message, reviewers_name = 'Area_Chairs')


