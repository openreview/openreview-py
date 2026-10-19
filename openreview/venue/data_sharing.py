import os
import datetime
import tempfile
import openreview
from openreview import tools


class VenueDataSharing():
    """Requests from one venue to share data with another venue, hosted in the support domain.

    The invitations are signed by the support group, so the process functions run as support,
    except the Run invitation, which is signed by the super user so its process can read the
    submissions of both venues.

    The first type of request is a dual submission check: the program chairs of one venue
    request it, the program chairs of the other venue approve it, and support runs
    :meth:`openreview.venue.Venue.compute_dual_submission_metadata` and attaches the CSV to
    the request forum.
    """

    def __init__(self, client, support_group_id):
        self.client = client
        self.support_group_id = support_group_id
        self.meta_invitation_id = f'{support_group_id}/-/Edit'
        self.group_id = f'{support_group_id}/Venue_Data_Sharing'
        self.request_invitation_id = f'{self.group_id}/-/Dual_Submission_Check_Request'
        self.run_invitation_id = f'{self.group_id}/-/Dual_Submission_Check_Run'

    def get_approval_invitation_id(self, number):
        return f'{self.group_id}/Dual_Submission_Check{number}/-/Approval'

    def get_comment_invitation_id(self, number):
        return f'{self.group_id}/Dual_Submission_Check{number}/-/Comment'

    def get_results_invitation_id(self, number):
        return f'{self.group_id}/Dual_Submission_Check{number}/-/Results'

    def get_process_content(self, file_name):
        with open(os.path.join(os.path.dirname(__file__), 'process', file_name)) as f:
            return f.read().replace("SUPPORT_GROUP = ''", f"SUPPORT_GROUP = '{self.support_group_id}'")

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
            'comment': {
                'order': 6,
                'description': 'Message to the program chairs of the other venue (optional).',
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

    def create_request_invitations(self, request):

        venue_id = request.content['venue_id']['value']
        alternate_venue_id = request.content['alternate_venue_id']['value']
        participants = [self.support_group_id, venue_id, alternate_venue_id]

        approval_invitation_id = self.get_approval_invitation_id(request.number)
        self.post_invitation_edit(openreview.api.Invitation(
            id=approval_invitation_id,
            invitees=[alternate_venue_id],
            readers=participants,
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            maxReplies=1,
            process=self.get_process_content('data_sharing_approval_process.py'),
            edit={
                'signatures': [alternate_venue_id],
                'readers': participants,
                'writers': [self.support_group_id, alternate_venue_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': approval_invitation_id,
                            'optional': True
                        }
                    },
                    'forum': request.id,
                    'replyto': request.id,
                    'signatures': ['${3/signatures}'],
                    'readers': participants,
                    'writers': [self.support_group_id, alternate_venue_id],
                    'content': {
                        'status': {
                            'order': 1,
                            'description': f'Do you approve sharing the submissions of {alternate_venue_id} with {venue_id} to check for dual submissions? The program chairs of both venues will get the titles, abstracts and authors of the most similar pairs of submissions.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['Approved', 'Rejected'],
                                    'input': 'radio'
                                }
                            }
                        },
                        'approval_comment': {
                            'order': 2,
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
        ))

        comment_invitation_id = self.get_comment_invitation_id(request.number)
        self.post_invitation_edit(openreview.api.Invitation(
            id=comment_invitation_id,
            invitees=participants,
            readers=participants,
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            process=self.get_process_content('data_sharing_comment_process.py'),
            edit={
                'signatures': {
                    'param': {
                        'items': [{ 'value': participant, 'optional': True } for participant in participants]
                    }
                },
                'readers': participants,
                'writers': [self.support_group_id, '${2/signatures}'],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': comment_invitation_id,
                            'optional': True
                        }
                    },
                    'forum': request.id,
                    'replyto': {
                        'param': {
                            'withForum': request.id
                        }
                    },
                    'signatures': ['${3/signatures}'],
                    'readers': participants,
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
        ))

        ## posted by the Run process, or by support with a CSV computed by hand
        results_invitation_id = self.get_results_invitation_id(request.number)
        self.post_invitation_edit(openreview.api.Invitation(
            id=results_invitation_id,
            invitees=[self.support_group_id],
            readers=participants,
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            edit={
                'signatures': [self.support_group_id],
                'readers': participants,
                'writers': [self.support_group_id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': results_invitation_id,
                            'optional': True
                        }
                    },
                    'forum': request.id,
                    'replyto': request.id,
                    'signatures': ['${3/signatures}'],
                    'readers': participants,
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
        ))

    def get_venue_info(self, venue_id):
        """Returns the short name and the program chairs group id of a venue."""
        venue_group = self.client.get_group(venue_id)
        short_name = venue_group.content.get('subtitle', {}).get('value') or venue_id
        program_chairs_id = venue_group.content.get('program_chairs_id', {}).get('value', f'{venue_id}/Program_Chairs')
        return short_name, program_chairs_id

    def get_forum_url(self, request_id):
        return f'{tools.get_site_url(self.client)}/forum?id={request_id}'

    def post_message(self, recipients, subject, message):
        return self.client.post_message(
            subject=subject,
            recipients=recipients,
            message=message,
            invitation=self.meta_invitation_id,
            signature=self.support_group_id
        )

    def post_status(self, request_id, status, status_message=None):
        """Updates the status of a request; only the process functions do it, through the meta invitation."""
        content = {
            'status': { 'value': status }
        }
        if status_message:
            content['status_message'] = { 'value': status_message, 'readers': [self.support_group_id] }

        return self.client.post_note_edit(
            invitation=self.meta_invitation_id,
            readers=[self.support_group_id],
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            note=openreview.api.Note(
                id=request_id,
                content=content
            )
        )

    def run_dual_submission_check(self, request, job_id=None):
        """Computes the dual submission metadata of a request and attaches the CSV to it.

        The client must be able to read the submissions of both venues, e.g. the super user.

        :param request: Dual_Submission_Check_Request note
        :type request: openreview.api.Note
        :param job_id: Existing similarity job id to reuse instead of computing the scores again
        :type job_id: str, optional
        """
        venue_id = request.content['venue_id']['value']
        alternate_venue_id = request.content['alternate_venue_id']['value']
        top_percent_cutoff = request.content['top_percent_cutoff']['value']
        author_overlap_only = request.content['author_overlap_only']['value']
        forum_url = self.get_forum_url(request.id)

        short_name, program_chairs_id = self.get_venue_info(venue_id)
        alternate_short_name, alternate_program_chairs_id = self.get_venue_info(alternate_venue_id)

        ## the approval can not change once the data is being shared
        self.post_invitation_edit(openreview.api.Invitation(
            id=self.get_approval_invitation_id(request.number),
            expdate=openreview.tools.datetime_millis(datetime.datetime.now())
        ), replacement=False)

        try:
            venue = openreview.venue.helpers.get_venue(self.client, venue_id, support_user=self.support_group_id)
            alternate_venue = openreview.venue.helpers.get_venue(self.client, alternate_venue_id, support_user=self.support_group_id)

            self.post_message(
                recipients=[program_chairs_id, alternate_program_chairs_id],
                subject=f'Dual submission check started: {short_name} and {alternate_short_name}',
                message=f'''The OpenReview support team started the dual submission check between {short_name} and {alternate_short_name}.

Computing the similarity between the submissions of both venues can take several hours. You will receive another email when the results are available.

You can view the request here: {forum_url}

The OpenReview Team'''
            )

            with tempfile.TemporaryDirectory() as output_dir:
                venue.compute_dual_submission_metadata(
                    alternate_venue,
                    output_dir,
                    top_percent_cutoff=top_percent_cutoff,
                    job_id=job_id,
                    author_overlap_only=author_overlap_only
                )
                ## the output directory only contains the CSV file
                csv_path = os.path.join(output_dir, os.listdir(output_dir)[0])
                ## only users with a profile can upload files and the token of a process function
                ## has none, impersonating the support group gives a token with a profile
                upload_client = openreview.api.OpenReviewClient(baseurl=self.client.baseurl, token=self.client.token)
                upload_client.impersonate(self.support_group_id)
                results_invitation_id = self.get_results_invitation_id(request.number)
                results_url = upload_client.put_attachment(csv_path, results_invitation_id, 'results')

            results_edit = self.client.post_note_edit(
                invitation=results_invitation_id,
                signatures=[self.support_group_id],
                note=openreview.api.Note(
                    content={
                        'results': { 'value': results_url }
                    }
                )
            )
            self.post_status(request.id, 'Completed')

        except Exception as e:
            self.post_status(request.id, 'Failed', status_message=repr(e))
            self.post_message(
                recipients=[self.support_group_id],
                subject=f'Dual submission check failed: {short_name} and {alternate_short_name}',
                message=f'''The dual submission check between {short_name} and {alternate_short_name} failed with the following error:

{repr(e)}

Check the process logs of the request, then run it again: {forum_url}'''
            )
            raise e

        self.post_message(
            recipients=[program_chairs_id, alternate_program_chairs_id, self.support_group_id],
            subject=f'Dual submission check completed: {short_name} and {alternate_short_name}',
            message=f'''The dual submission check between {short_name} and {alternate_short_name} has completed.

You can download the results here: {forum_url}&noteId={results_edit['note']['id']}

The OpenReview Team'''
        )
