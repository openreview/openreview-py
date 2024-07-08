from .. import openreview
import os
import json

class Agora(object):

    def __init__(self, client, support_group_id, superuser, editor_id):
        self.client_v2 = openreview.api.OpenReviewClient(baseurl=openreview.tools.get_base_urls(client)[1], token=client.token)

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
            "subtitle": "A venue for open discussion of research articles related to COVID-19",
            "location": "Everywhere",
            "date": "Ongoing",
            "website": "https://openreview.net",
            "instructions": '''
            <p>
                <strong>Editor-in-chief:</strong> {editor_id}
            </p>
            <p>
                <strong>Submission, Reviewing, Commenting, and Approval Workflow:</strong><br>
                <p>Any OpenReview logged-in user may submit an article. The article submission form allows the Authors to suggest for their article one or
                multiple Editors (from among people who have created OpenReview profiles). The article is not immediately visible to the public, but is sent
                to the Editors-in-Chief, any of whom may perform a basic evaluation of the submission (e.g. checking for spam). If not immediately rejected
                at this step, an Editor-in-Chief assigns one or more Editors to the article (perhaps from the authors’ suggestions, perhaps from their own choices),
                and the article is made visible to the public. Authors may upload revisions to any part of their submission at any time. (The full history of past
                revisions is  available through the "Show Revisions" link.)</p>
            </p>
            <p>
                Assigned Editors are non-anonymous. The article Authors may revise their list of requested editors by revising their submission. The Editors-in-Chief
                may add or remove Editors for the article at any time.
            </p>
            <p>
                Reviewers are assigned to the article by any of the Editors of the article.  Any of the Editors can add (or remove) Reviewers at any time. Any logged-in
                user can suggest additional Reviewers for this article; these suggestions are public and non-anonymous.  (Thus the public may apply social pressure on
                the Editors for diversity of views in reviewing and commenting.) To avoid spam, only assigned Reviewers, Editors and the Editors-in-Chief can contribute
                comments (or reviews) on the article.  Such comments are public and associated with their non-anonymous reviewers.  There are no system-enforced deadlines
                for any of the above steps, (although social pressure may be applied out-of-band).
            </p>
            <p>
                At some point, any of the Editors may contribute a meta-review, making an Approval recommendation to the Editors-in-Chief.  Any of the Editors-in-Chief may
                 at any time add or remove the venue’s Approval from the article (indicating a kind of “acceptance” of the article).
            </p>
            <p>
                For questions about editorial content and process, email the Editors-in-Chief.<br>
                For questions about software infrastructure or profiles, email the OpenReview support team at
                <a href="mailto:info@openreview.net">info@openreview.net</a>.
            </p>
            '''.format(editor_id=editor_id),
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
            self.client_v2.add_members_to_group('venues', covid_group.id)



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
            id = '{}/-/Moderation'.format(covid_group_id),
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
            id = '{}/-/Editors_Assignment'.format(covid_group_id),
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
            id = '{}/-/Reviewers_Assignment'.format(covid_group_id),
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

        meta_review_invitation = openreview.Invitation(
            id = '{}/-/Meta_Review'.format(covid_group_id),
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
            multiReply = False,
            reply = {
                'content': {
                    'title': {
                        'description': 'Brief summary of your meta review.',
                        'order': 1,
                        'value-regex': ".{0,500}",
                        'required':True
                    },
                    'metareview': {
                        'description': 'You can include Markdown formatting and LaTeX forumulas, for more information see https://openreview.net/faq , max length: 5000',
                        'order': 2,
                        'value-regex': "[\\S\\s]{1,5000}",
                        'required':True,
                        'markdown':True
                    },
                    'recommendation': {
                        'order': 3,
                        'value-dropdown': [
                            'Accept',
                            'Needs more work'
                        ],
                        'required': True
                    }
                }
            }
        )
        with open(os.path.join(os.path.dirname(__file__), 'process/meta_review_process.py')) as f:
            file_content = f.read()
            file_content = file_content.replace("support = 'OpenReview.net/Support'", "support = '" + support_group_id + "'")
            meta_review_invitation.process = file_content
            client.post_invitation(meta_review_invitation)

        suggest_reviewer_invitation = openreview.Invitation(
            id = '{}/-/Reviewers_Suggestion'.format(covid_group_id),
            readers = ['everyone'],
            writers = [support_group_id],
            signatures = [support_group_id],
            multiReply = True,
            reply = {
                'content': {
                    'suggested_reviewers': {
                        'description': 'Comma separated list of reviewer email addresses or OpenReview profile ids',
                        'order': 2,
                        'values-regex': "~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})",
                        'required':True
                    },
                    'comment': {
                        'description': 'Why are you suggesting this reviewer?',
                        'order': 3,
                        'value-regex': "[\\S\\s]{1,200}",
                        'required':False
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
