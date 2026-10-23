import os
import openreview


class VenueDataSharing():
    """Sets up requests from one venue to share data with another venue, hosted in the support domain.

    This class only posts the group and the invitations. The process functions don't use it, so
    they only depend on the openreview-py that the API already has. The per-request Approval,
    Comment and Results invitations come from template invitations that the request process
    fills in.

    The invitations are signed by the support group, so the process functions run as support,
    except the Run invitation, which is signed by the super user so its process can read the
    submissions of both venues.

    The first type of request is a dual submission check: the program chairs of one venue
    request it, the program chairs of the other venue approve it, and support runs
    :meth:`openreview.venue.Venue.compute_dual_submission_metadata` and posts the CSV to
    the request forum.
    """

    def __init__(self, client, support_group_id):
        self.client = client
        self.support_group_id = support_group_id
        self.meta_invitation_id = f'{support_group_id}/-/Edit'
        self.group_id = f'{support_group_id}/Venue_Data_Sharing'
        self.request_invitation_id = f'{self.group_id}/-/Dual_Submission_Check_Request'
        self.run_invitation_id = f'{self.group_id}/-/Dual_Submission_Check_Run'
        self.approval_template_invitation_id = f'{self.group_id}/-/Dual_Submission_Check_Approval'
        self.comment_template_invitation_id = f'{self.group_id}/-/Dual_Submission_Check_Comment'
        self.results_template_invitation_id = f'{self.group_id}/-/Dual_Submission_Check_Results'

    def get_approval_invitation_id(self, number):
        return f'{self.group_id}/Dual_Submission_Check{number}/-/Approval'

    def get_comment_invitation_id(self, number):
        return f'{self.group_id}/Dual_Submission_Check{number}/-/Comment'

    def get_results_invitation_id(self, number):
        return f'{self.group_id}/Dual_Submission_Check{number}/-/Results'

    def get_process_content(self, file_name):
        with open(os.path.join(os.path.dirname(__file__), 'process', file_name)) as f:
            return f.read().replace("SUPPORT_GROUP = ''", f"SUPPORT_GROUP = '{self.support_group_id}'").replace("GROUP_ID = ''", f"GROUP_ID = '{self.group_id}'")

    def post_invitation_edit(self, invitation, replacement=True, signature=None):
        signature = signature or self.support_group_id
        return self.client.post_invitation_edit(
            invitations=self.meta_invitation_id,
            readers=[signature],
            writers=[signature],
            signatures=[signature],
            invitation=invitation,
            replacement=replacement
        )

    def setup(self):
        self.set_group()
        self.set_approval_template_invitation()
        self.set_comment_template_invitation()
        self.set_results_template_invitation()
        self.set_request_invitation()
        self.set_run_invitation()

    def set_group(self):

        with open(os.path.join(os.path.dirname(__file__), 'webfield/dataSharingWebfield.js')) as f:
            webfield = f.read()

        self.client.post_group_edit(
            invitation=self.meta_invitation_id,
            readers=[self.support_group_id],
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            group=openreview.api.Group(
                id=self.group_id,
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.support_group_id],
                signatories=[self.support_group_id],
                web=webfield
            )
        )

    def set_request_invitation(self):

        content = {
            'title': {
                'order': 1,
                'value': {
                    'param': {
                        'type': 'string',
                        'const': 'Dual Submission Check: ${2/venue_id/value} and ${2/alternate_venue_id/value}',
                        'hidden': True
                    }
                }
            },
            'venue_id': {
                'order': 2,
                'description': 'Id of your venue, e.g. ICML.cc/2026/Conference. You must be a program chair of this venue.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': '.{1,250}'
                    }
                }
            },
            'alternate_venue_id': {
                'order': 3,
                'description': 'Id of the other venue whose submissions will be compared with yours, e.g. NeurIPS.cc/2026/Conference. The program chairs of this venue must approve the request.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': '.{1,250}'
                    }
                }
            },
            'top_percent_cutoff': {
                'order': 4,
                'description': 'Percentage of the most similar pairs of submissions to include in the results, e.g. 1 means the top 1%.',
                'value': {
                    'param': {
                        'type': 'float',
                        'range': [0.01, 100],
                        'default': '1'
                    }
                }
            },
            'author_overlap_only': {
                'order': 5,
                'description': 'Only include pairs of submissions that share at least one author.',
                'value': {
                    'param': {
                        'type': 'boolean',
                        'enum': [True, False],
                        'input': 'radio'
                    }
                }
            },
            'submission_statuses': {
                'order': 6,
                'description': 'Submissions of your venue to compare. Leave empty to compare only the active submissions. If your venue already released its decisions, select the accepted, rejected and withdrawn submissions.',
                'value': {
                    'param': {
                        'type': 'string[]',
                        'enum': ['Active', 'Accepted', 'Rejected', 'Withdrawn', 'Desk Rejected'],
                        'optional': True,
                        'deletable': True,
                        'input': 'checkbox'
                    }
                }
            },
            'results_recipients': {
                'order': 7,
                'description': 'Profile ids or emails of the people of your venue who will get the results. Leave empty to share the results with all the program chairs of your venue.',
                'value': {
                    'param': {
                        'type': 'string[]',
                        'regex': '^~.+$|^.+@.+$',
                        'optional': True,
                        'deletable': True
                    }
                }
            },
            'comment': {
                'order': 8,
                'description': 'Message to the program chairs of the other venue (optional). They see your choices above before approving.',
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 5000,
                        'markdown': True,
                        'input': 'textarea',
                        'optional': True,
                        'deletable': True
                    }
                }
            },
            'status': {
                'value': 'Pending Approval'
            }
        }

        self.post_invitation_edit(openreview.api.Invitation(
            id=self.request_invitation_id,
            invitees=['~'],
            readers=['everyone'],
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            preprocess=self.get_process_content('data_sharing_request_pre_process.py'),
            process=self.get_process_content('data_sharing_request_process.py'),
            edit={
                ## only the program chairs of a venue can sign as the venue
                'signatures': ['${2/note/content/venue_id/value}'],
                'readers': ['${2/note/readers}'],
                'writers': [self.support_group_id],
                'note': {
                    'signatures': ['${3/signatures}'],
                    'readers': [self.support_group_id, '${2/content/venue_id/value}', '${2/content/alternate_venue_id/value}'],
                    'writers': [self.support_group_id],
                    'content': content
                }
            }
        ))

    def set_run_invitation(self):

        ## signed by the super user so the process can read the submissions of both venues
        self.post_invitation_edit(openreview.api.Invitation(
            id=self.run_invitation_id,
            invitees=[self.support_group_id],
            readers=[self.support_group_id],
            writers=[self.support_group_id],
            signatures=['~Super_User1'],
            ## computing the similarity scores can take many hours
            post_processes=[{
                'script': self.get_process_content('data_sharing_run_process.py'),
                'timeout': 86400000
            }],
            edit={
                'signatures': [self.support_group_id],
                'readers': [self.support_group_id],
                'writers': [self.support_group_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': self.request_invitation_id
                        }
                    },
                    'content': {
                        'status': {
                            'value': 'Running'
                        },
                        'job_id': {
                            'order': 9,
                            'description': 'Id of an expertise job that already computed the similarity scores (optional). Use it to retry a failed run without computing the scores again.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'optional': True,
                                    'deletable': True
                                }
                            },
                            'readers': [self.support_group_id]
                        }
                    }
                }
            }
        ), signature='~Super_User1')


    def get_template_edit_content(self):
        ## the request process fills these values when it creates the invitations of a request
        return {
            'noteNumber': { 'value': { 'param': { 'type': 'integer' } } },
            'noteId': { 'value': { 'param': { 'type': 'string' } } },
            'venue_id': { 'value': { 'param': { 'type': 'string' } } },
            'alternate_venue_id': { 'value': { 'param': { 'type': 'string' } } }
        }

    def set_approval_template_invitation(self):

        approval_invitation_id = f'{self.group_id}/Dual_Submission_Check${{2/content/noteNumber/value}}/-/Approval'
        self.post_invitation_edit(openreview.api.Invitation(
            id=self.approval_template_invitation_id,
            invitees=[self.support_group_id],
            readers=[self.support_group_id],
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            edit={
                'signatures': [self.support_group_id],
                'readers': [self.support_group_id],
                'writers': [self.support_group_id],
                'content': self.get_template_edit_content(),
                'replacement': True,
                'invitation': {
                    'id': approval_invitation_id,
                    'invitees': ['${3/content/alternate_venue_id/value}'],
                    'readers': [self.support_group_id, '${3/content/venue_id/value}', '${3/content/alternate_venue_id/value}'],
                    'writers': [self.support_group_id],
                    'signatures': [self.support_group_id],
                    'maxReplies': 1,
                    'process': self.get_process_content('data_sharing_approval_process.py'),
                    'edit': {
                        'signatures': ['${4/content/alternate_venue_id/value}'],
                        'readers': [self.support_group_id, '${4/content/venue_id/value}', '${4/content/alternate_venue_id/value}'],
                        'writers': [self.support_group_id, '${4/content/alternate_venue_id/value}'],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': f'{self.group_id}/Dual_Submission_Check${{6/content/noteNumber/value}}/-/Approval',
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'signatures': ['${3/signatures}'],
                            'readers': [self.support_group_id, '${5/content/venue_id/value}', '${5/content/alternate_venue_id/value}'],
                            'writers': [self.support_group_id, '${5/content/alternate_venue_id/value}'],
                            'content': {
                                'status': {
                                    'order': 1,
                                    'description': 'Do you approve sharing the submissions of your venue with the requesting venue to check for dual submissions? The results recipients of both venues will get the titles, abstracts and authors of the most similar pairs of submissions.',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'enum': ['Approved', 'Rejected'],
                                            'input': 'radio'
                                        }
                                    }
                                },
                                'submission_statuses': {
                                    'order': 2,
                                    'description': 'Submissions of your venue to compare. Leave empty to compare only the active submissions. If your venue already released its decisions, select the accepted, rejected and withdrawn submissions.',
                                    'value': {
                                        'param': {
                                            'type': 'string[]',
                                            'enum': ['Active', 'Accepted', 'Rejected', 'Withdrawn', 'Desk Rejected'],
                                            'optional': True,
                                            'deletable': True,
                                            'input': 'checkbox'
                                        }
                                    }
                                },
                                'results_recipients': {
                                    'order': 3,
                                    'description': 'Profile ids or emails of the people of your venue who will get the results. Leave empty to share the results with all the program chairs of your venue.',
                                    'value': {
                                        'param': {
                                            'type': 'string[]',
                                            'regex': '^~.+$|^.+@.+$',
                                            'optional': True,
                                            'deletable': True
                                        }
                                    }
                                },
                                'approval_comment': {
                                    'order': 4,
                                    'description': 'Comment for the program chairs of the requesting venue (optional).',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 5000,
                                            'markdown': True,
                                            'input': 'textarea',
                                            'optional': True,
                                            'deletable': True
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ))

    def set_comment_template_invitation(self):

        comment_invitation_id = f'{self.group_id}/Dual_Submission_Check${{2/content/noteNumber/value}}/-/Comment'
        self.post_invitation_edit(openreview.api.Invitation(
            id=self.comment_template_invitation_id,
            invitees=[self.support_group_id],
            readers=[self.support_group_id],
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            edit={
                'signatures': [self.support_group_id],
                'readers': [self.support_group_id],
                'writers': [self.support_group_id],
                'content': self.get_template_edit_content(),
                'replacement': True,
                'invitation': {
                    'id': comment_invitation_id,
                    'invitees': [self.support_group_id, '${3/content/venue_id/value}', '${3/content/alternate_venue_id/value}'],
                    'readers': [self.support_group_id, '${3/content/venue_id/value}', '${3/content/alternate_venue_id/value}'],
                    'writers': [self.support_group_id],
                    'signatures': [self.support_group_id],
                    'process': self.get_process_content('data_sharing_comment_process.py'),
                    'edit': {
                        'signatures': {
                            'param': {
                                'items': [
                                    { 'value': self.support_group_id, 'optional': True },
                                    { 'value': '${7/content/venue_id/value}', 'optional': True },
                                    { 'value': '${7/content/alternate_venue_id/value}', 'optional': True }
                                ]
                            }
                        },
                        'readers': [self.support_group_id, '${4/content/venue_id/value}', '${4/content/alternate_venue_id/value}'],
                        'writers': [self.support_group_id, '${2/signatures}'],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': f'{self.group_id}/Dual_Submission_Check${{6/content/noteNumber/value}}/-/Comment',
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': {
                                'param': {
                                    'withForum': '${6/content/noteId/value}'
                                }
                            },
                            'signatures': ['${3/signatures}'],
                            'readers': [self.support_group_id, '${5/content/venue_id/value}', '${5/content/alternate_venue_id/value}'],
                            'writers': [self.support_group_id, '${3/signatures}'],
                            'content': {
                                'comment': {
                                    'order': 1,
                                    'description': 'Your comment or reply (max 5000 characters).',
                                    'value': {
                                        'param': {
                                            'type': 'string',
                                            'maxLength': 5000,
                                            'markdown': True,
                                            'input': 'textarea'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ))

    def set_results_template_invitation(self):

        results_invitation_id = f'{self.group_id}/Dual_Submission_Check${{2/content/noteNumber/value}}/-/Results'
        ## posted by the Run process, or by support with a CSV computed by hand
        self.post_invitation_edit(openreview.api.Invitation(
            id=self.results_template_invitation_id,
            invitees=[self.support_group_id],
            readers=[self.support_group_id],
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            edit={
                'signatures': [self.support_group_id],
                'readers': [self.support_group_id],
                'writers': [self.support_group_id],
                'content': self.get_template_edit_content(),
                'replacement': True,
                'invitation': {
                    'id': results_invitation_id,
                    'invitees': [self.support_group_id],
                    'readers': [self.support_group_id, '${3/content/venue_id/value}', '${3/content/alternate_venue_id/value}'],
                    'writers': [self.support_group_id],
                    'signatures': [self.support_group_id],
                    'edit': {
                        'signatures': [self.support_group_id],
                        ## the edit has the CSV too, so it has the same readers as the note
                        'readers': ['${2/note/readers}'],
                        'writers': [self.support_group_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': f'{self.group_id}/Dual_Submission_Check${{6/content/noteNumber/value}}/-/Results',
                                    'optional': True
                                }
                            },
                            'forum': '${4/content/noteId/value}',
                            'replyto': '${4/content/noteId/value}',
                            'signatures': ['${3/signatures}'],
                            ## support and the results recipients of both venues, set by the Run process
                            'readers': {
                                'param': {
                                    'regex': '.+'
                                }
                            },
                            'writers': [self.support_group_id],
                            'content': {
                                'results': {
                                    'order': 1,
                                    'description': 'CSV file with the pairs of submissions that are potential dual submissions.',
                                    'value': {
                                        'param': {
                                            'type': 'file',
                                            'extensions': ['csv'],
                                            'maxSize': 50
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ))
