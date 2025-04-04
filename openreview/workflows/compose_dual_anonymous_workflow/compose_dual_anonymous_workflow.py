import openreview.api
import openreview
from openreview.api import Invitation
import os

class Compose_Dual_Anonymous_Workflow():

    def __init__(self, client, support_group_id, super_id):
        self.support_group_id = support_group_id        #openreview.net/Support
        self.client = client
        self.super_id = super_id                        #openreview.net
        self.meta_invitation_id = f'{super_id}/-/Edit'  #openreview.net/-/Edit
        self.update_wait_time = 5000
        self.update_date_string = "#{4/mdate} + " + str(self.update_wait_time)
        self.invitation_edit_process = '''def process(client, invitation):
    domain = client.get_group(invitation.domain)
    meta_invitation = client.get_invitation(domain.content['meta_invitation_id']['value'])
    script = meta_invitation.content["invitation_edit_script"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
'''
        self.group_edit_process = '''def process(client, invitation):
    domain = client.get_group(invitation.domain)
    meta_invitation = client.get_invitation(domain.content['meta_invitation_id']['value'])
    script = meta_invitation.content["group_edit_script"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index
    }
    exec(script, funcs)
    funcs['process'](client, invitation)
'''

    def setup(self):
        self.set_meta_invitation()
        self.set_reviewers_dual_anonymous_invitation()
        self.set_deploy_invitation()
        self.set_comment_invitation()
        self.set_venues_homepage()
        self.set_workflow_group()

        # setup group template invitations
        self.setup_automated_administrator_group_template_invitation()
        self.setup_venue_group_template_invitation()
        self.setup_inner_group_template_invitation()
        self.setup_program_chairs_group_template_invitation()
        
        # Area Chair related group templates
        self.setup_area_chairs_group_template_invitation()
        
        # Reviewer related group templates
        self.setup_reviewers_group_template_invitation()
        self.setup_reviewers_invited_group_template_invitation()
        self.setup_reviewers_declined_group_template_invitation()
        self.setup_reviewers_submission_group_template_invitation()
        
        # Other group templates
        self.setup_authors_group_template_invitation()
        self.setup_authors_accepted_group_template_invitation()

        # setup workflow template invitations
        self.setup_submission_template_invitation()
        self.setup_submission_change_before_bidding_template_invitation()
        self.setup_submission_change_before_reviewing_template_invitation()
        
        # Review process templates
        self.setup_review_template_invitation()
        self.setup_review_release_template_invitation()
        
        # Meta review template for Area Chairs
        self.setup_meta_review_template_invitation()
        
        # Paper matching templates
        self.setup_reviewer_bid_template_invitation()
        self.setup_reviewer_conflict_template_invitation()
        self.setup_reviewer_affinity_score_template_invitation()
        self.setup_reviewer_assignment_template_invitation()
        self.setup_reviewers_assignment_configuration_template_invitation()
        self.setup_reviewer_custom_max_papers_template_invitation()
        self.setup_reviewer_custom_user_demands_template_invitation()
        self.setup_reviewer_proposed_assignment_template_invitation()
        self.setup_reviewer_aggregate_score_template_invitation()
        
        # Other templates
        self.setup_official_comment_template_invitation()
        self.setup_rebuttal_template_invitation()
        self.setup_decision_template_invitation()
        self.setup_decision_upload_template_invitation()
        self.setup_withdrawal_request_template_invitation()
        self.setup_withdrawal_template_invitation()
        self.setup_withdrawn_submission_template_invitation()
        self.setup_withdrawal_expiration_template_invitation()
        self.setup_unwithdrawal_template_invitation()
        self.setup_desk_rejection_template_invitation()
        self.setup_desk_rejected_submission_template_invitation()
        self.setup_desk_reject_expiration_template_invitation()
        self.setup_desk_rejection_reversion_template_invitation()
        self.setup_email_decisions_template_invitation()
        
    def get_process_content(self, file_path):
        process = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            process = f.read()
            return process

    def get_webfield_content(self, file_path):
        webfield = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            webfield = f.read()
            return webfield
        
    def post_invitation_edit(self, invitation):
        return self.client.post_invitation_edit(invitations=self.meta_invitation_id,
            readers=['~Super_User1'],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            invitation=invitation,
            replacement=True
        )
        
    def set_meta_invitation(self):
        invitation = Invitation(id=f'{self.support_group_id}/Compose_Dual_Anonymous/-/Meta',
                                invitees=[self.super_id],
                                readers=[self.super_id, self.support_group_id],
                                writers=[self.super_id],
                                signatures=[self.super_id],
                                content={
                                    'invitation_edit_script': {
                                        'value': self.get_process_content('process/invitation_edit_process.py')
                                    },
                                    'group_edit_script': {
                                        'value': self.get_process_content('process/group_edit_process.py')
                                    },
                                    'deploy_script': {
                                        'value': self.get_process_content('process/deploy_process.py')
                                    }
                                })
        self.post_invitation_edit(invitation)
        
    def set_deploy_invitation(self):
        invitation = Invitation(id=f'{self.support_group_id}/Compose_Dual_Anonymous/Venue_Configuration_Request/-/Deploy',
                               invitees=[self.support_group_id],
                               readers=[self.support_group_id],
                               writers=[self.support_group_id],
                               signatures=[self.support_group_id],
                               process=self.get_process_content('process/deploy_process.py'))
        self.post_invitation_edit(invitation)
        
    def set_reviewers_dual_anonymous_invitation(self):
        super_id = self.super_id
        support_group_id = self.support_group_id
        conference_venue_invitation_id = f'{support_group_id}/Compose_Dual_Anonymous/-/Venue_Configuration_Request'

        reply = {
            'official_venue_name': {
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 250,
                        'input': 'text'
                    }
                },
                'description': 'Enter the full name of the venue, such as "Thirty-ninth International Conference on Machine Learning".',
                'order': 1
            },
            'abbreviated_venue_name': {
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 50,
                        'input': 'text'
                    }
                },
                'description': 'Enter the venue acronym, such as "ICML 2022".',
                'order': 2
            },
            'venue_id': {
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 50,
                        'input': 'text',
                        'regex': '^[^\\s,]+$'
                    }
                },
                'description': 'Choose an ID for the venue. Try to follow the format: Conference.Year (e.g. ICML.2022, ICLR.2021, InternetMeasurement.2023). The venue ID will appear in the URL of your conference pages.',
                'order': 3
            },
            'venue_website_url': {
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 500,
                        'input': 'text',
                        'optional': True
                    }
                },
                'description': '(Optional) Enter the venue website URL.',
                'order': 4
            },
            'contact_email': {
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 100,
                        'input': 'text',
                        'regex': '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
                    }
                },
                'description': 'Enter the contact email address for this venue. For example: "info@venue.org". Recommendation: create a mailing list specifically for your venue.',
                'order': 5
            },
            'program_chair_emails': {
                'value': {
                    'param': {
                        'type': 'string[]',
                        'regex': '^[^;,]*$'
                    }
                },
                'description': 'Comma separated list of Program Chair email addresses.',
                'order': 6
            },
            'venue_start_date': {
                'value': {
                    'param': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ],
                        'optional': True
                    }
                },
                'description': '(Optional) When does the venue start? This is used to customize the home page of the venue.',
                'order': 7
            },
            'submission_start_date': {
                'value': {
                    'param': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ]
                    }
                },
                'description': 'When does the submission period start? The submission form will not be accessible to authors before this date.',
                'order': 8
            },
            'submission_deadline': {
                'value': {
                    'param': {
                        'type': 'date',
                        'range': [ 0, 9999999999999 ]
                    }
                },
                'description': 'When does the submission period end? Authors will not be able to edit their submissions after this date.',
                'order': 9,
                'required': True
            },
            'location': {
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 2048,
                        'input': 'text',
                        'optional': True
                    }
                },
                'description': '(Optional) Where is the event located? (City, State/Province, Country)',
                'order': 10
            },
            'submission_license': {
                'value': {
                    'param': {
                        'type': 'string[]',
                        'enum': [
                            'CC BY 4.0',
                            'CC BY-SA 4.0',
                            'CC BY-NC 4.0',
                            'CC BY-ND 4.0',
                            'CC BY-NC-SA 4.0',
                            'CC BY-NC-ND 4.0',
                            'CC0 1.0'
                        ],
                        'input': 'select'
                    }
                },
                'description': 'Which Creative Commons license(s) would you like to be available to authors?',
                'order': 11,
                'required': True
            }
        }

        invitation = Invitation(id=conference_venue_invitation_id,
                              invitees=[self.support_group_id],
                              readers=[self.super_id, self.support_group_id],
                              writers=[self.super_id],
                              signatures=[self.super_id],
                              edit={
                                  'signatures': { 'param': { 'items': [ { 'value': self.support_group_id }]} },
                                  'readers': [ self.super_id, self.support_group_id ],
                                  'writers': [ self.super_id, self.support_group_id ],
                                  'content': reply,
                                  'note': {
                                      'id': {
                                         'param': {
                                             'withInvitation': conference_venue_invitation_id,
                                             'optional': True
                                         }
                                      },
                                      'ddate': {
                                          'param': {
                                              'range': [ 0, 9999999999999 ],
                                              'optional': True,
                                              'deletable': True
                                          }
                                      },
                                      'signatures': [ self.support_group_id ],
                                      'readers': [ self.super_id, self.support_group_id ],
                                      'writers': [ self.super_id, self.support_group_id ],
                                      'content': reply
                                  }
                              })
        self.post_invitation_edit(invitation)
        
    def set_comment_invitation(self):
        comment_invitation = Invitation(id=f'{self.support_group_id}/Compose_Dual_Anonymous/Venue_Configuration_Request/-/Comment',
                                invitees=[self.support_group_id],
                                readers=[self.super_id, self.support_group_id],
                                writers=[self.super_id],
                                signatures=[self.super_id],
                                process=self.get_process_content('process/venue_comment_process.py'),
                                edit={
                                    'signatures': { 'param': { 'items': [ { 'value': self.support_group_id }]} },
                                    'readers': [ self.super_id, self.support_group_id ],
                                    'writers': [ self.super_id, self.support_group_id ],
                                    'note': {
                                        'signatures': [self.support_group_id],
                                        'readers': [ self.super_id, self.support_group_id ],
                                        'writers': [ self.super_id, self.support_group_id ],
                                        'replyto': {
                                            'param': {
                                                'withInvitation': f'{self.support_group_id}/Compose_Dual_Anonymous/-/Venue_Configuration_Request'
                                            }
                                        },
                                        'content': {
                                            'title': {
                                                'order': 1,
                                                'value': {
                                                    'param': {
                                                        'type': 'string',
                                                        'maxLength': 500,
                                                        'input': 'text'
                                                    }
                                                }
                                            },
                                            'comment': {
                                                'order': 2,
                                                'value': {
                                                    'param': {
                                                        'type': 'string',
                                                        'maxLength': 200000,
                                                        'input': 'textarea',
                                                        'markdown': True
                                                    }
                                                }
                                            }
                                        }
                                    }
                                })

        self.post_invitation_edit(comment_invitation)

    def set_venues_homepage(self):
        homepage_invitation = Invitation(id=f'{self.support_group_id}/Compose_Dual_Anonymous/-/Homepage',
                                invitees=[self.support_group_id],
                                readers=[self.super_id, self.support_group_id],
                                writers=[self.super_id],
                                signatures=[self.super_id],
                                edit={
                                    'signatures': { 'param': { 'items': [ { 'value': self.support_group_id }]} },
                                    'readers': [ self.super_id, self.support_group_id ],
                                    'writers': [ self.super_id, self.support_group_id ],
                                    'note': {
                                        'id': {
                                         'param': {
                                             'withInvitation': f'{self.support_group_id}/Compose_Dual_Anonymous/-/Homepage',
                                             'optional': True
                                         }
                                        },
                                        'signatures': [self.support_group_id],
                                        'readers': [ self.super_id, self.support_group_id ],
                                        'writers': [ self.super_id, self.support_group_id ],
                                        'content': {
                                            'title': {
                                                'order': 1,
                                                'value': {
                                                    'param': {
                                                        'type': 'string',
                                                        'maxLength': 500,
                                                        'input': 'text',
                                                        'default': 'Compose Dual Anonymous Workflow'
                                                    }
                                                }
                                            },
                                            'description': {
                                                'order': 2,
                                                'value': {
                                                    'param': {
                                                        'type': 'string',
                                                        'maxLength': 50000,
                                                        'input': 'textarea',
                                                        'markdown': True,
                                                        'default': '''This workflow is designed for dual-anonymous conferences with Program Chairs, Area Chairs, and Reviewers. 

This is a standard workflow which includes:

- OpenReview paper submissions with revisions
- Reviewer bidding, constraints, and assignments
- Area Chair assignments and meta-reviews
- Decisions and notifications'''
                                                    }
                                                }
                                            }
                                        }
                                    }
                                })
        self.post_invitation_edit(homepage_invitation)

    def set_workflow_group(self):
        group = openreview.api.Group(
            id='openreview.net/Support/Compose_Dual_Anonymous',
            readers=[self.super_id, self.support_group_id],
            writers=[self.super_id],
            signatures=[self.super_id],
            signatories=[self.super_id],
            members=[],
        )
        self.client.post_group(group)

    # Area Chair group template invitation
    def setup_area_chairs_group_template_invitation(self):
        invitation = Invitation(id=f'{self.support_group_id}/Compose_Dual_Anonymous/Venue_Configuration_Request/-/Area_Chairs_Group_Template',
                                invitees=[self.support_group_id],
                                readers=[self.support_group_id],
                                writers=[self.support_group_id],
                                signatures=[self.support_group_id],
                                process=self.get_process_content('process/area_chairs_group_template_process.py'),
                                edit={
                                    'signatures': { 'param': { 'items': [ { 'value': '~Super_User1' }]} },
                                    'readers': [ self.support_group_id ],
                                    'writers': [ self.support_group_id ],
                                    'content': {
                                        'venue_id': {
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 500,
                                                    'regex': '^[^,\\s]+$'
                                                }
                                            },
                                            'description': 'Enter the venue ID. This is the group ID that represents the conference in OpenReview (e.g. ICLR.cc/2024/Conference).',
                                            'order': 1
                                        },
                                        'area_chairs_name': {
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 500,
                                                    'regex': '^[^,\\s]+$'
                                                }
                                            },
                                            'description': 'Enter the name of the area chairs group (e.g. "Area_Chairs").',
                                            'order': 2
                                        }
                                    },
                                    'group': {
                                        'id': {
                                            'param': {
                                                'withValue': lambda v: f"{v['venue_id']['value']}/{v['area_chairs_name']['value']}" if 'venue_id' in v and 'area_chairs_name' in v else '',
                                                'optional': True
                                            }
                                        },
                                        'signatures': ['~Super_User1'],
                                        'readers': ['${3/content/venue_id/value}'],
                                        'writers': ['${3/content/venue_id/value}'],
                                        'members': [],
                                        'signatories': ['${3/id}']
                                    }
                                })
        self.post_invitation_edit(invitation)

    # Meta-review template invitation
    def setup_meta_review_template_invitation(self):
        invitation = Invitation(id=f'{self.support_group_id}/Compose_Dual_Anonymous/Venue_Configuration_Request/-/Meta_Review_Template',
                                invitees=[self.support_group_id],
                                readers=[self.support_group_id],
                                writers=[self.support_group_id],
                                signatures=[self.support_group_id],
                                edit={
                                    'signatures': { 'param': { 'items': [ { 'value': self.support_group_id }]} },
                                    'readers': [ self.support_group_id ],
                                    'writers': [ self.support_group_id ],
                                    'content': {
                                        'venue_id': {
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 500,
                                                    'regex': '^[^,\\s]+$'
                                                }
                                            }
                                        },
                                        'venue_id_pretty': { 'value': { 'param': { 'type': 'string', 'maxLength': 500 } } },
                                        'name': {
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 500,
                                                    'regex': '^[^,\\s]+$'
                                                }
                                            }
                                        },
                                        'area_chairs_name': {
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 500,
                                                    'regex': '^[^,\\s]+$'
                                                }
                                            }
                                        },
                                        'activation_date': {
                                            'value': {
                                                'param': {
                                                    'type': 'integer'
                                                }
                                            }
                                        },
                                        'due_date': {
                                            'value': {
                                                'param': {
                                                    'type': 'integer'
                                                }
                                            }
                                        },
                                        'expiration_date': {
                                            'value': {
                                                'param': {
                                                    'type': 'integer',
                                                    'optional': True
                                                }
                                            }
                                        },
                                        'submission_name': {
                                            'value': {
                                                'param': {
                                                    'type': 'string',
                                                    'maxLength': 500,
                                                    'regex': '^[^,\\s]+$'
                                                }
                                            }
                                        }
                                    },
                                    'invitation': {
                                        'id': {
                                            'param': {
                                                'withValue': lambda v: f"{v['venue_id']['value']}/{v['area_chairs_name']['value']}/-/{v['name']['value']}",
                                                'optional': True
                                            }
                                        },
                                        'signatures': ['${3/content/venue_id/value}'],
                                        'readers': ['${3/content/venue_id/value}'],
                                        'writers': ['${3/content/venue_id/value}'],
                                        'invitees': ['${3/content/venue_id/value}/${3/content/submission_name/value}${{2/id}/number}/${3/content/area_chairs_name/value}'],
                                        'cdate': '${3/content/activation_date/value}',
                                        'duedate': '${3/content/due_date/value}',
                                        'expdate': '${3/content/expiration_date/value}',
                                        'edit': {
                                            'signatures': {
                                                'param': {
                                                    'items': [
                                                        { 'prefix': '${3/content/venue_id/value}/${3/content/area_chairs_name/value}/.*' }
                                                    ]
                                                }
                                            },
                                            'readers': ['${3/content/venue_id/value}'],
                                            'nonreaders': [],
                                            'writers': ['${3/content/venue_id/value}', '${2/signatures}'],
                                            'note': {
                                                'id': {
                                                    'param': {
                                                        'withInvitation': '${4/id}',
                                                        'optional': True
                                                    }
                                                },
                                                'forum': {
                                                    'param': {
                                                        'withPattern': { 
                                                            'prefix': f".*", 
                                                            'optional': True 
                                                        }
                                                    }
                                                },
                                                'ddate': {
                                                    'param': {
                                                        'range': [ 0, 9999999999999 ],
                                                        'optional': True,
                                                        'deletable': True
                                                    }
                                                },
                                                'signatures': ['${4/signatures}'],
                                                'readers': [
                                                    "openreview.net/Support",
                                                    "${3/content/venue_id/value}",
                                                    "${3/content/venue_id/value}/Program_Chairs",
                                                    "${3/content/venue_id/value}/${3/content/submission_name/value}${{2/forum}/number}/${3/content/area_chairs_name/value}",
                                                    "${3/content/venue_id/value}/${3/content/submission_name/value}${{2/forum}/number}/Reviewers",
                                                    "${4/signatures}"
                                                ],
                                                'writers': ['${3/content/venue_id/value}', '${4/signatures}'],
                                                'content': {
                                                    'title': {
                                                        'order': 1,
                                                        'value': { 'param': { 'type': 'string', 'maxLength': 500, 'input': 'text', 'default': '${3/content/name/value}' } }
                                                    },
                                                    'recommendation': {
                                                        'order': 2,
                                                        'value': { 
                                                            'param': { 
                                                                'type': 'string', 
                                                                'input': 'radio',
                                                                'enum': ['Accept', 'Reject'],
                                                                'optional': True
                                                            }
                                                        }
                                                    },
                                                    'confidence': {
                                                        'order': 3,
                                                        'value': { 
                                                            'param': { 
                                                                'type': 'string', 
                                                                'input': 'radio',
                                                                'enum': [
                                                                    '5: The area chair is absolutely certain',
                                                                    '4: The area chair is confident but not absolutely certain',
                                                                    '3: The area chair is somewhat confident',
                                                                    '2: The area chair is not very confident',
                                                                    '1: The area chair is not at all confident'
                                                                ],
                                                                'optional': True
                                                            }
                                                        }
                                                    },
                                                    'metareview': {
                                                        'order': 4,
                                                        'value': { 'param': { 'type': 'string', 'maxLength': 200000, 'input': 'textarea', 'markdown': True } }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                })
        self.post_invitation_edit(invitation)

    # Implement the remaining methods similar to simple_dual_anonymous_workflow.py
    # but with modifications to support area chairs