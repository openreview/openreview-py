import openreview

import os
import json

class Agora(object):

    def __init__(self, client, support_group_id, superuser, editor_id):

        venue_group = openreview.Group(
            id='-Agora',
            readers=['everyone'],
            writers=[support_group_id],
            signatures=[support_group_id],
            signatories=[],
            members=[],

        )
        client.post_group(venue_group)

        covid_group_id = '-Agora/COVID-19'
        covid_group = openreview.Group(
            id=covid_group_id,
            readers=['everyone'],
            writers=[support_group_id],
            signatures=[support_group_id],
            signatories=[],
            members=[],
        )

        covid_editors = '{}/Editors'.format(covid_group_id)

        header = {
            "title": "Agora (ἀγορά) COVID-19",
            "subtitle": "OpenReview public space for COVID-19 related articles",
            "location": "Everywhere",
            "date": "Ongoing",
            "website": "https://openreview.net",
            "instructions": '''
            <p>
                <strong>Editor-in-chief:</strong><br>
                <p>This venue is managed by a group of Editors-in-Chief who check each submission and decide whether to release it to the public or not. The Editors-in-Chief determine the editors for each submitted article.
                To see the list of members, click <a href="https://openreview.net/group?id={covid_editors}">here</a>.</p>
            </p>
            <p>
                <strong>Submission:</strong><br>
                <p>Anyone with an OpenReview profile can submit an article. The article submission form also allows the authors to suggest one or more "editors" by specifying their OpenReview usernames (e.g. "~Jane_Doe1").
                Before the submitted article is made visible to the public, it goes to the Editor-in-Chief who examines it briefly, checking for spam but not for scientific validity. If it is not spam, the article is made visible, and editors are assigned to the paper.
                Authors can upload a revision to any part of their submission at any time.  The full history of past uploads will always be available through the "Show Revisions" option.</p>
            </p>
            <p>
                <strong>Editor:</strong><br>
                <p>The Editor-in-Chief decides on assigned editors, following the suggestions of the authors or making their own choices.  The editor assignments are non-anonymous.
                The article authors can edit their list of requested editors by revising their submission. The Editor-in-Chief can add or remove editors from the article at any time.</p>
            </p>
            <p>
                <strong>Reviewers:</strong><br>
                <p>Only assigned reviewers can review or comment on the article. Reviews are public and reviewers are non-anonymous.
                Editors of the article can add (or remove) people from the reviewers group by adding/removing their OpenReview usernames to the "Assigned Reviewers" field of the article.
                Any logged-in user can suggest reviewers for an article and an assigned editor will decide to add them to the reviewers group them or not.</p>
            </p>
            <p>
                <strong>Questions or Concerns:</strong><br>
                Please contact the OpenReview support team at
                <a href="mailto:info@openreview.net">info@openreview.net</a> with any questions or concerns.
            </p>
            '''.format(covid_editors=covid_editors),
            "deadline": "",
            "contact": "info@openreview.net"
        }

        with open(os.path.join(os.path.dirname(__file__), 'webfield/homepage.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '-Agora/COVID-19';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '-Agora/COVID-19/-/Submission';")
            content = content.replace("var ARTICLE_ID = '';", "var ARTICLE_ID = '-Agora/COVID-19/-/Article';")
            content = content.replace("var DESK_REJECTED_SUBMISSION_ID = '';", "var DESK_REJECTED_SUBMISSION_ID = '-Agora/COVID-19/-/Desk_Rejected';")

            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            covid_group.web = content
            client.post_group(covid_group)



        covid_group_editor = openreview.Group(
            id=covid_editors,
            readers=['everyone'],
            writers=[support_group_id],
            signatures=[support_group_id],
            signatories=[covid_editors],
            members=[editor_id],
        )
        client.post_group(covid_group_editor)


        covid_group_editor = openreview.Group(
            id='{}/Blocked'.format(covid_group_id),
            readers=['everyone'],
            writers=[support_group_id, covid_editors],
            signatures=[support_group_id],
            signatories=[],
            members=[],
        )
        client.post_group(covid_group_editor)

        content = {
            'title': {
                'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                'order': 1,
                'value-regex': '.{1,250}',
                'required':True
            },
            'one_liner': {
                'description': 'A short sentence describing your paper',
                'order': 2,
                'value-regex': '[^\\n]{0,250}',
                'required':False
            },
            'abstract': {
                'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                'order': 3,
                'value-regex': '[\\S\\s]{1,5000}',
                'required':True
            },
            'authors': {
                'description': 'Comma separated list of author names.',
                'order': 4,
                'values-regex': "[^;,\\n]+(,[^,\\n]+)*",
                'required':True,
                'hidden':True
            },
            'authorids': {
                'description': 'Comma separated list of author email addresses, lowercased, in the same order as above. For authors with existing OpenReview accounts, please make sure that the provided email address(es) match those listed in the author\'s profile.',
                'order': 5,
                'values-regex': "~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})",
                'required':True
            },
            'requested_editors': {
                'description': 'Comma separated list of editor email addresses or OpenReview profile ids',
                'order': 5,
                'values-regex': "~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})",
                'required':True
            },
            'pdf': {
                'description': 'Upload a PDF file that ends with .pdf or enter a valid url',
                'order': 6,
                'value-file': {
                    'fileTypes': ['pdf'],
                    'size': 50,
                    'regex': 'https?://.+'
                },
                'required':True
            }
        }

        submission_invitation = openreview.Invitation(
            id = '{}/-/Submission'.format(covid_group_id),
            duedate = 2556143999000, # Saturday, December 31, 2050 11:59:59 PM,
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [superuser],
            invitees = ['~'],
            reply = {
                'forum': None,
                'replyto': None,
                'readers': {
                    'values-copied': [
                        support_group_id,
                        covid_editors,
                        '{content.authorids}',
                        '{signatures}'
                    ]
                },
                'writers': {
                    'values-copied': [
                        support_group_id,
                        covid_editors,
                        '{content.authorids}',
                        '{signatures}'
                    ]
                },
                'signatures': {
                    'values-regex': '~.*|{}|{}'.format(support_group_id, covid_editors)
                },
                'content': content
            }
        )
        with open(os.path.join(os.path.dirname(__file__), 'process/submission_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("support = 'OpenReview.net/Support'", "support = '" + support_group_id + "'")
            file_content = file_content.replace("superuser = 'OpenReview.net'", "superuser = '" + superuser + "'")
            submission_invitation.process = file_content
            client.post_invitation(submission_invitation)

        moderate_invitation = openreview.Invitation(
            id = '{}/-/Moderate'.format(covid_group_id),
            invitees = [covid_editors],
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [superuser],
            multiReply = False,
            reply = {
                'content': {
                    'resolution': {
                        'description': 'Select a resolution',
                        'order': 1,
                        'value-dropdown': ['Accept', 'Desk-Reject'],
                        'required':True
                    },
                    'comment': {
                        'description': 'Leave a comment to the authors',
                        'order': 2,
                        'value-regex': "[\\S\\s]{1,5000}",
                        'required':False
                    }
                }
            }
        )
        with open(os.path.join(os.path.dirname(__file__), 'process/moderate_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("support = 'OpenReview.net/Support'", "support = '" + support_group_id + "'")
            moderate_invitation.process = file_content
            client.post_invitation(moderate_invitation)

        article_invitation = openreview.Invitation(
            id = '{}/-/Article'.format(covid_group_id),
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
            invitees = ['~'],
            reply = {
                'forum': None,
                'replyto': None,
                'readers': {
                    'values': ['everyone']
                },
                'writers': {
                    'values': [support_group_id]
                },
                'signatures': {
                    'values-regex': '~.*|{}|{}'.format(support_group_id, covid_editors)
                },
                'content': content
            }
        )
        with open(os.path.join(os.path.dirname(__file__), 'process/article_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("support = 'OpenReview.net/Support'", "support = '" + support_group_id + "'")
            article_invitation.process = file_content
            client.post_invitation(article_invitation)

        desk_reject_invitation = openreview.Invitation(
            id = '{}/-/Desk_Rejected'.format(covid_group_id),
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
            invitees = ['~'],
            reply = {
                'forum': None,
                'replyto': None,
                'readers': {
                    'values-copied': [
                        support_group_id,
                        covid_editors,
                        '{content.authorids}',
                        'signatures'
                    ]
                },
                'writers': {
                    'values-copied': [
                        support_group_id,
                        covid_editors,
                        '{content.authorids}',
                        'signatures'
                    ]
                },
                'signatures': {
                    'values-regex': '~.*|{}|{}'.format(support_group_id, covid_editors)
                },
                'content': content
            }
        )
        client.post_invitation(desk_reject_invitation)


        ##Super invitations
        revision_invitation = openreview.Invitation(
            id = '{}/-/Revision'.format(covid_group_id),
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
            reply = {
                'readers': {
                    'values': ['everyone']
                },
                'content': content
            }
        )
        with open(os.path.join(os.path.dirname(__file__), 'process/revision_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("support = 'OpenReview.net/Support'", "support = '" + support_group_id + "'")
            revision_invitation.process = file_content
            client.post_invitation(revision_invitation)

        assign_editor_invitation = openreview.Invitation(
            id = '{}/-/Assign_Editor'.format(covid_group_id),
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
            reply = {
                'readers': {
                    'values': ['everyone']
                },
                'content': {
                    'assigned_editors': {
                        'description': 'Comma separated list of editor email addresses or OpenReview profile ids. Append the new editors to the list.',
                        'order': 1,
                        'values-regex': "~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})",
                        'required':True
                    }
                }
            }
        )
        with open(os.path.join(os.path.dirname(__file__), 'process/assign_editor_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("support = 'OpenReview.net/Support'", "support = '" + support_group_id + "'")
            assign_editor_invitation.process = file_content
            client.post_invitation(assign_editor_invitation)

        assign_reviewer_invitation = openreview.Invitation(
            id = '{}/-/Assign_Reviewer'.format(covid_group_id),
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
            reply = {
                'readers': {
                    'values': ['everyone']
                },
                'content': {
                    'assigned_reviewers': {
                        'description': 'Comma separated list of reviewer email addresses or OpenReview profile ids. Append the new reviewers to the list.',
                        'order': 1,
                        'values-regex': "~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})",
                        'required':True
                    }
                }
            }
        )
        with open(os.path.join(os.path.dirname(__file__), 'process/assign_reviewer_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("support = 'OpenReview.net/Support'", "support = '" + support_group_id + "'")
            assign_reviewer_invitation.process = file_content
            client.post_invitation(assign_reviewer_invitation)

        review_invitation = openreview.Invitation(
            id = '{}/-/Review'.format(covid_group_id),
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
            multiReply = False,
            reply = {
                'content': {
                    'title': {
                        'description': 'Brief summary of your review.',
                        'order': 1,
                        'value-regex': ".{0,500}",
                        'required':True
                    },
                    'review': {
                        'description': 'You can include Markdown formatting and LaTeX forumulas, for more information see https://openreview.net/faq , max length: 5000',
                        'order': 2,
                        'value-regex': "[\\S\\s]{1,5000}",
                        'required':True,
                        'markdown':True
                    }
                }
            }
        )
        with open(os.path.join(os.path.dirname(__file__), 'process/review_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("support = 'OpenReview.net/Support'", "support = '" + support_group_id + "'")
            review_invitation.process = file_content
            client.post_invitation(review_invitation)

        suggest_reviewer_invitation = openreview.Invitation(
            id = '{}/-/Suggest_Reviewers'.format(covid_group_id),
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
            multiReply = True,
            reply = {
                'content': {
                    'suggested_reviewers': {
                        'description': 'Comma separated list of reviewer email addresses or OpenReview profile ids',
                        'order': 1,
                        'values-regex': "~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})",
                        'required':True
                    },
                    'comment': {
                        'description': 'Why are you suggesting this reviewer?',
                        'order': 2,
                        'value-regex': "[\\S\\s]{1,5000}",
                        'required':True
                    }
                }
            }
        )
        with open(os.path.join(os.path.dirname(__file__), 'process/suggest_reviewer_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("support = 'OpenReview.net/Support'", "support = '" + support_group_id + "'")
            suggest_reviewer_invitation.process = file_content
            client.post_invitation(suggest_reviewer_invitation)

        comment_invitation = openreview.Invitation(
            id = '{}/-/Comment'.format(covid_group_id),
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
            multiReply = True,
            reply = {
                'content': {
                    'title': {
                        'description': 'Comment title',
                        'order': 1,
                        'value-regex': ".{0,500}",
                        'required':True
                    },
                    'comment': {
                        'description': 'You can include Markdown formatting and LaTeX forumulas, for more information see https://openreview.net/faq , max length: 5000',
                        'order': 2,
                        'value-regex': "[\\S\\s]{1,5000}",
                        'required':True,
                        'markdown':True
                    }
                }
            }
        )
        with open(os.path.join(os.path.dirname(__file__), 'process/comment_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("support = 'OpenReview.net/Support'", "support = '" + support_group_id + "'")
            comment_invitation.process = file_content
            client.post_invitation(comment_invitation)
