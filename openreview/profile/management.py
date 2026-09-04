import os
import openreview
from openreview.stages import *
from .arxiv_subject_areas import *

class ProfileManagement():

    def __init__(self, client, super_user):

        self.client = client
        self.super_user = super_user
        self.support_group_id = f'{self.super_user}/Support'
        self.author_rename_invitation_id = f'{self.support_group_id}/-/Author_Rename'
        self.meta_invitation_id = f'{self.super_user}/-/Edit'
        self.public_article_group_id = f'{self.super_user}/Public_Article'
        self.public_article_meta_invitation_id = f'{self.public_article_group_id}/-/Edit'
        self.dblp_group_id = f'{self.public_article_group_id}/DBLP.org'
        self.arxiv_group_id = f'{self.public_article_group_id}/arXiv.org'
        self.orcid_group_id = f'{self.public_article_group_id}/ORCID.org'


    def setup(self):
        self.set_profile_moderation_invitations()
        self.set_profile_edit_invitations()
        self.set_remove_name_invitations()
        self.set_remove_email_invitations()
        self.set_archive_invitations()
        self.set_merge_profiles_invitations()
        self.set_public_article_invitations()
        self.set_dblp_invitations()
        self.set_deprecated_dblp_ivitations()
        self.set_arxiv_invitations()
        self.set_orcid_invitations()
        self.set_anonymous_preprint_invitations()
        self.set_news_article_invitations()

    def get_process_content(self, file_path):
        process = None
        with open(os.path.join(os.path.dirname(__file__), file_path)) as f:
            process = f.read()
            return process        

    def set_profile_moderation_invitations(self):

        self.client.post_invitation_edit(
            invitations=f'{self.super_user}/-/Edit',
            signatures=[self.super_user],
            invitation=openreview.api.Invitation(
                id=f'{self.support_group_id}/-/Profile_Moderation_Label',
                readers=[self.support_group_id],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                invitees=[self.support_group_id],
                tag={
                    'id': {
                        'param': {
                            'withInvitation': f'{self.support_group_id}/-/Profile_Moderation_Label',
                            'optional': True
                        }
                    },
                    'readers': [self.support_group_id],
                    'writers': [self.support_group_id],
                    'signature': self.support_group_id,
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'cdate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True
                        }
                    },                    
                    'profile': {
                        'param': {
                            'regex': '^~.*'
                        }
                    },
                    'label': {
                        'param': {
                            'regex': '.*'
                        }
                    },
                },
                web='''// Webfield component
return {
  component: 'ProfileTagsViewer',
  version: 1,
  properties: {
    tagInvitation: entity.id,
    instructions:'Profiles that were tagged by support staff for moderation reasons.',
    title: 'Moderation Labels'
  }
}
'''
            )
        )

        with open(os.path.join(os.path.dirname(__file__), 'process/profile_blocked_status_process.py'), 'r') as f:
            file_content = f.read()

        self.client.post_invitation_edit(
            invitations=f'{self.super_user}/-/Edit',
            signatures=[self.super_user],
            invitation=openreview.api.Invitation(
                id=f'{self.support_group_id}/-/Profile_Blocked_Status',
                readers=[self.support_group_id, 'active_venues'],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                invitees=[self.support_group_id],
                process=file_content,
                tag={
                    'id': {
                        'param': {
                            'withInvitation': f'{self.support_group_id}/-/Profile_Blocked_Status',
                            'optional': True
                        }
                    },
                    'readers': {
                        'param': {
                            'items': [
                                { 'value': self.support_group_id, 'optional': False },
                                { 'inGroup': 'venues', 'optional': True }
                            ]                            
                        }
                    },
                    'writers': [self.support_group_id],
                    'signature': self.support_group_id,
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'cdate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True
                        }
                    },
                    'profile': {
                        'param': {
                            'regex': '^~.*'
                        }
                    },
                    'label': {
                        'param': {
                            'regex': '.*'
                        }
                    },
                },
                web='''// Webfield component
return {
  component: 'ProfileTagsViewer',
  version: 1,
  properties: {
    tagInvitation: entity.id,
    instructions:'Profiles blocked from participating in venues. This tag is added by support staff after reviewing the user\\'s profile and activity history. If you think this is a mistake, please contact support.',
    title: 'Blocked Profiles'
  }
}
'''
            )
        )                
    
        self.client.post_invitation_edit(
            invitations=f'{self.super_user}/-/Edit',
            signatures=[self.super_user],
            invitation=openreview.api.Invitation(
                id=f'{self.support_group_id}/-/Vouch',
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.support_group_id],
                invitees=['~'],
                preprocess=self.get_process_content('process/vouch_pre_process.py'),
                process=self.get_process_content('process/vouch_process.py'),
                content={
                    'lifetimeLimit': { 'value': 20 },
                    'monthLimit': { 'value': 5 }
                },
                tag={
                    'id': {
                        'param': {
                            'withInvitation': f'{self.support_group_id}/-/Vouch',
                            'optional': True
                        }
                    },
                    'readers': ['everyone'],
                    'writers': [self.support_group_id],
                    'signature': {
                        'param': {
                            'regex': '^~.*' 
                        }
                    },
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'profile': {
                        'param': {
                            'regex': '^~.*'
                        }
                    },
                    'label': {
                        'param': {
                            'regex': '.*',
                            'optional': True
                        }
                    }
                },
                web='''// Webfield component
return {
  component: 'ProfileTagsViewer',
  version: 1,
  properties: {
    tagInvitation: entity.id,
    instructions:'Profiles that have been activated because another OpenReview user vouched for them.',
    title: 'Vouched Profiles'
  }
}
'''
            )
        )

    def set_profile_edit_invitations(self):
        '''
        Profile edit invitations used during moderation. A profile edit records an assertion
        about a profile (it never modifies the profile itself), so these invitations replace
        the moderation tag invitations with structured, per-field records that follow the
        profile schema.
        '''

        ## Posted by support after reviewing an identity document uploaded by the user:
        ## confirms the profile name and date of birth. The record is visible to the
        ## profile owner and the support team only.
        self.client.post_invitation_edit(
            invitations=self.meta_invitation_id,
            signatures=[self.super_user],
            invitation=openreview.api.Invitation(
                id=f'{self.support_group_id}/-/Identity_Verification',
                invitees=[self.support_group_id],
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                edit={
                    'signatures': [self.support_group_id],
                    'readers': ['${2/profile/id}', self.support_group_id],
                    'writers': [self.support_group_id],
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'profile': {
                        'id': {
                            'param': {
                                'type': 'profile',
                                'regex': '^~.+$'
                            }
                        },
                        'content': {
                            'names': {
                                'value': {
                                    'param': {
                                        'type': 'object{}',
                                        'change': 'add',
                                        'optional': True,
                                        'properties': {
                                            'fullname': { 'param': { 'type': 'string', 'minLength': 1 } }
                                        }
                                    }
                                }
                            },
                            'dob': {
                                'value': {
                                    'param': {
                                        'type': 'integer',
                                        'range': [ 0, 9999999999999 ],
                                        'optional': True
                                    }
                                }
                            }
                        }
                    }
                }
            )
        )

        ## Posted by support after reviewing a document proving institution affiliation:
        ## confirms the institution domain, name and the position held. The record is
        ## public so anyone can see the affiliation was verified.
        self.client.post_invitation_edit(
            invitations=self.meta_invitation_id,
            signatures=[self.super_user],
            invitation=openreview.api.Invitation(
                id=f'{self.support_group_id}/-/Affiliation_Verification',
                invitees=[self.support_group_id],
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                edit={
                    'signatures': [self.support_group_id],
                    'readers': ['everyone'],
                    'writers': [self.support_group_id],
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'profile': {
                        'id': {
                            'param': {
                                'type': 'profile',
                                'regex': '^~.+$'
                            }
                        },
                        'content': {
                            'history': {
                                'value': {
                                    'param': {
                                        'type': 'object{}',
                                        'change': 'add',
                                        'optional': True,
                                        'properties': {
                                            'position': { 'param': { 'type': 'string', 'minLength': 1 } },
                                            'start': { 'param': { 'type': 'integer', 'range': [ 1900, 2100 ], 'optional': True } },
                                            'end': { 'param': { 'type': 'integer', 'range': [ 1900, 2100 ], 'optional': True } },
                                            'institution': {
                                                'param': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'domain': { 'param': { 'type': 'string', 'minLength': 1 } },
                                                        'name': { 'param': { 'type': 'string', 'optional': True } }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            )
        )

        ## Posted by support after reviewing a parental consent document for a minor:
        ## confirms the parent relation declared in the profile. Not public because we
        ## never disclose that a profile belongs to a minor: the record is visible to
        ## the profile owner and the support team only.
        self.client.post_invitation_edit(
            invitations=self.meta_invitation_id,
            signatures=[self.super_user],
            invitation=openreview.api.Invitation(
                id=f'{self.support_group_id}/-/Parent_Consent',
                invitees=[self.support_group_id],
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                edit={
                    'signatures': [self.support_group_id],
                    'readers': ['${2/profile/id}', self.support_group_id],
                    'writers': [self.support_group_id],
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'profile': {
                        'id': {
                            'param': {
                                'type': 'profile',
                                'regex': '^~.+$'
                            }
                        },
                        'content': {
                            'relations': {
                                'value': {
                                    'param': {
                                        'type': 'object{}',
                                        'change': 'add',
                                        'optional': True,
                                        'properties': {
                                            'relation': { 'param': { 'type': 'string', 'minLength': 1 } },
                                            'name': { 'param': { 'type': 'string', 'optional': True } },
                                            'email': { 'param': { 'type': 'string', 'regex': r'([a-z0-9_\-.]{1,}@[a-z0-9_\-.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-.]{1,}@[a-z0-9_\-.]{2,}\.[a-z]{2,})', 'optional': True } },
                                            'start': { 'param': { 'type': 'integer', 'range': [ 1900, 2100 ], 'optional': True } },
                                            'end': { 'param': { 'type': 'integer', 'range': [ 1900, 2100 ], 'optional': True } }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            )
        )

        ## Posted automatically by moderate_profile: records the new state of the
        ## profile and the reason for the decision. Informative only; the state itself
        ## is changed through the moderation endpoint. The state and reason live in the
        ## edit content because they describe the moderation decision, not profile
        ## content. The labels enum is the controlled vocabulary of moderation reasons:
        ## the edit schema enforces that every record uses labels from this set, and the
        ## support team can add/edit/remove them by editing the invitation instead of
        ## changing the UI code. An entry's description is the default message the
        ## moderation UI offers for that label; the message actually sent is free text
        ## stored in reason. {{issuedByCurrentInstitution}} is replaced by the UI with
        ## "issued by <current institution> " when the profile has a current
        ## affiliation, and removed otherwise.
        self.client.post_invitation_edit(
            invitations=self.meta_invitation_id,
            signatures=[self.super_user],
            invitation=openreview.api.Invitation(
                id=f'{self.support_group_id}/-/Profile_State',
                invitees=[self.support_group_id],
                readers=['everyone'],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                edit={
                    'signatures': [self.support_group_id],
                    'readers': ['${2/profile/id}', self.support_group_id],
                    'writers': [self.support_group_id],
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'content': {
                        'state': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['Active', 'Active Automatic', 'Active Institutional', 'Inactive', 'Blocked', 'Limited', 'Rejected', 'Merged', 'Deleted', 'Needs Moderation']
                                }
                            }
                        },
                        'reason': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'optional': True
                                }
                            }
                        },
                        ## Short labels of the selected moderation reasons, for compact
                        ## display; reason keeps the full message sent to the user.
                        'labels': {
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'optional': True,
                                    'input': 'select',
                                    'enum': [
                                        {
                                            'value': 'Institutional Email is missing',
                                            'description': 'Please add and confirm an institutional email {{issuedByCurrentInstitution}}to your profile. Please make sure the verification token is entered and verified.\n\nIf your affiliation {{issuedByCurrentInstitution}}is not current, please update your profile with your current affiliation and associated institutional email.\n\nIf your institution does not provide you with an email, please use our contact form at https://openreview.net/contact, and make sure your profile is filled out completely: https://docs.openreview.net/getting-started/creating-an-openreview-profile/expediting-profile-activation'
                                        },
                                        {
                                            'value': 'Institutional Email is added but not confirmed',
                                            'description': 'Please confirm the institutional email in your profile by clicking the "Confirm" button next to the email and enter the verification token received.'
                                        },
                                        {
                                            'value': 'DBLP link is a disambiguation page',
                                            'description': 'The DBLP link you have provided is a disambiguation page and is not intended to be used as a bibliography. Please select the correct bibliography page listed under "Other persons with a similar name". If your page is not listed please contact the DBLP team so they can add your bibliography page. We recommend providing a different bibliography homepage when resubmitting to OpenReview moderation.'
                                        },
                                        {
                                            'value': 'Homepage is invalid',
                                            'description': "The homepage url provided in your profile is invalid or does not display your name/email used to register so your identity can't be determined."
                                        },
                                        {
                                            'value': 'Profile name is invalid',
                                            'description': 'The name in your profile does not match the name listed in your homepage or is invalid.'
                                        },
                                        {
                                            'value': 'ORCID profile is incomplete',
                                            'description': "The ORCID profile you've provided as a homepage is empty or does not match the Career & Education history you've provided."
                                        },
                                        {
                                            'value': 'Request supervisor or coauthor to vouch',
                                            'description': 'Please ask a supervisor, coauthor, or colleague who already has an active OpenReview profile with a confirmed institutional email to vouch for you.\n\nThey should add your profile ID to the Relations section of their profile, save their profile, and then click the vouch button next to your name.\n\nYour profile will be activated automatically once they vouch.\n\nIf no such person is available, please use our contact form at https://openreview.net/contact, and make sure your profile is filled out completely: https://docs.openreview.net/getting-started/creating-an-openreview-profile/expediting-profile-activation'
                                        },
                                        {
                                            'value': 'Profiles cannot represent an organization',
                                            'description': 'Profiles can only represent an individual, we do not allow profiles to be created for an organization.'
                                        },
                                        {
                                            'value': 'Education/career history is incomplete',
                                            'description': 'Please complete your full education and career history in your profile, not just your current position.\n\nA complete history helps us verify your identity and is required for profile activation. If you are currently an independent researcher, please find more information here:\nhttps://docs.openreview.net/getting-started/frequently-asked-questions/i-am-an-independent-researcher-how-do-i-sign-up'
                                        },
                                        {
                                            'value': 'Documentation / ID requests',
                                            'description': "To proceed with activation and verify your affiliation, please provide a document from each of the following categories:\n\nA photo ID (government ID, passport, or driver's license) to verify your identity.\n\nA certificate or official document proving your affiliation with the institution listed in your profile (e.g. enrollment letter, employee ID, or student ID).\n\nWe handle all documents in accordance with our privacy policy and delete them after verification is complete.\n\nPlease upload the requested documents using the following link:\n\n{{documentVerificationLink}}\n\nOnce you have uploaded all of the requested documents, use the activation link in this email to update and resubmit your profile."
                                        },
                                        {
                                            'value': 'Consent form required for underage researchers',
                                            'description': 'OpenReview welcomes younger researchers, aged 13 and above, to participate in scholarly peer review.\n\nIf you are at least 13 and under 18 years of age, you must submit a consent form to activate your profile. More information can be found here: https://docs.openreview.net/getting-started/creating-an-openreview-profile/information-for-high-school-students\n\nPlease upload the completed consent form using the following link. Do not email the form directly to OpenReview.\n\n{{underageConsentLink}}\n\nOnce you have uploaded the consent form, use the activation link in this email to update and resubmit your profile.'
                                        },
                                        ## Labels used outside the rejection flow (no
                                        ## default message)
                                        {
                                            'value': 'Suspicious Activity'
                                        },
                                        {
                                            'value': 'Terms of Service Violation'
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    'profile': {
                        'id': {
                            'param': {
                                'type': 'profile',
                                'regex': '^~.+$'
                            }
                        }
                    }
                }
            )
        )

    def set_public_article_invitations(self):
        

        public_article_group = openreview.tools.get_group(self.client, self.public_article_group_id)
        if public_article_group is None:
            self.client.post_group_edit(
                invitation = self.meta_invitation_id,
                signatures = [self.support_group_id],
                group = openreview.api.Group(
                    id = self.public_article_group_id,
                    readers = ['everyone'],
                    writers = [self.public_article_group_id],
                    nonreaders = [],
                    signatures = [self.support_group_id],
                    signatories = [self.public_article_group_id],
                    members = []
                )
            )

        
        self.client.post_invitation_edit(
            invitations = None,
            signatures = [self.super_user],
            invitation = openreview.api.Invitation(
                id=self.public_article_meta_invitation_id,
                invitees=[self.arxiv_group_id, self.dblp_group_id, self.orcid_group_id, self.support_group_id],
                readers=[self.arxiv_group_id, self.dblp_group_id, self.orcid_group_id, self.support_group_id],
                signatures=[self.public_article_group_id],
                edit=True
            )
        )

        authorship_claim_invitation_id = f'{self.public_article_group_id}/-/Authorship_Claim'

        self.client.post_invitation_edit(
            invitations = self.public_article_meta_invitation_id,
            signatures = [self.public_article_group_id],
            replacement=True,
            invitation = openreview.api.Invitation(
                id=authorship_claim_invitation_id,
                readers=['everyone'],
                writers=[self.public_article_group_id],
                signatures=[self.public_article_group_id],
                invitees=['~', self.dblp_group_id, self.arxiv_group_id, self.orcid_group_id, self.support_group_id],
                preprocess=self.get_process_content('process/author_coreference_pre_process.js'),
                edit={
                    'readers': ['everyone'],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True },
                                { 'value': self.dblp_group_id, 'optional': True },
                                { 'value': self.arxiv_group_id, 'optional': True },
                                { 'value': self.orcid_group_id, 'optional': True }
                            ]
                        } 
                    },
                    'writers':  [self.public_article_group_id],
                    'content': {
                        'author_index': {
                            'order': 1,
                            'description': 'Enter the 0 based index of the author in the author list. The author name listed in that position must match with one of your names in your profile.',
                            'value': {
                                'param': {
                                    'type': 'integer'
                                }
                            }
                        },
                        'author_id' : {
                            'order': 2,
                            'description': 'Enter the author id that matches with the author name in the author list.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '^~.*',
                                }
                            }
                        },
                        'author_name': {
                            'order': 3,
                            'description': 'Enter the author name at the given index.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                }
                            }
                        },
                    },
                    'note': {
                        'id': {
                            'param': {
                                'withVenueid': self.public_article_group_id
                            }
                        },
                        'content': {
                            'authors': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'const': {
                                            'replace': {
                                                'index': '${6/content/author_index/value}',
                                                'value': {
                                                    'fullname': '${7/content/author_name/value}',
                                                    'username': '${7/content/author_id/value}'
                                                }
                                            }
                                        },
                                        'hidden': True
                                    }
                                }
                            }
                        }
                    }
                }
            )
        )

        author_removal_invitation_id = f'{self.public_article_group_id}/-/Author_Removal'

        self.client.post_invitation_edit(
            invitations = self.public_article_meta_invitation_id,
            signatures = [self.public_article_group_id],
            replacement=True,
            invitation = openreview.api.Invitation(
                id=author_removal_invitation_id,
                readers=['everyone'],
                writers=[self.public_article_group_id],
                signatures=[self.public_article_group_id],
                invitees=['~', self.dblp_group_id, self.arxiv_group_id, self.orcid_group_id, self.support_group_id],
                preprocess=self.get_process_content('process/author_removal_pre_process.js'),
                edit={
                    'readers': ['everyone'],
                    'signatures': {
                        'param': {
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True },
                                { 'value': self.dblp_group_id, 'optional': True },
                                { 'value': self.arxiv_group_id, 'optional': True },
                                { 'value': self.orcid_group_id, 'optional': True }
                            ]
                        }
                    },
                    'writers':  [self.public_article_group_id],
                    'content': {
                        'author_index': {
                            'order': 1,
                            'description': 'Enter the 0 based index of the author in the author list. The author name listed in that position must match with one of your names in your profile.',
                            'value': {
                                'param': {
                                    'type': 'integer'
                                }
                            }
                        },
                        'author_id' : {
                            'order': 2,
                            'description': 'Enter the author id that matches with the author name in the author list.',
                            'value': {
                                'param': {
                                    'const': '',
                                    'hidden': True
                                }
                            }
                        },
                        'author_name': {
                            'order': 3,
                            'description': 'Enter the author name at the given index.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                }
                            }
                        },
                    },
                    'note': {
                        'id': {
                            'param': {
                                'withVenueid': self.public_article_group_id
                            }
                        },
                        'content': {
                            'authors': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'const': {
                                            'replace': {
                                                'index': '${6/content/author_index/value}',
                                                'value': {
                                                    'fullname': '${7/content/author_name/value}',
                                                    'username': '${7/content/author_id/value}'
                                                }
                                            }
                                        },
                                        'hidden': True
                                    }
                                }
                            }
                        }
                    }
                }
            )
        )        

        # Disable for now
        # public_article_discussion_invitation_id = f'{self.public_article_group_id}/-/Discussion_Allowed'

        # self.client.post_invitation_edit(
        #     invitations = self.public_article_meta_invitation_id,
        #     signatures = [self.public_article_group_id],
        #     invitation = openreview.api.Invitation(
        #         id=public_article_discussion_invitation_id,
        #         readers=[self.public_article_group_id, self.dblp_group_id, self.arxiv_group_id],
        #         writers=[self.public_article_group_id],
        #         signatures=[self.public_article_group_id],
        #         invitees=[self.public_article_group_id, self.dblp_group_id, self.arxiv_group_id],
        #         edit={
        #             'readers': ['everyone'],
        #             'signatures': {
        #                 'param': {
        #                     'items': [
        #                         { 'value': self.dblp_group_id, 'optional': True },
        #                         { 'value': self.arxiv_group_id, 'optional': True },
        #                         { 'value': self.support_group_id, 'optional': True }
        #                     ]
        #                 }
        #             },
        #             'writers':  [self.public_article_group_id],
        #             'note': {
        #                 'id': {
        #                     'param': {
        #                         'withVenueid': self.public_article_group_id
        #                     }
        #                 },
        #                 'content': {
        #                     'discussion_allowed': {
        #                         'order': 1,
        #                         'value': True,
        #                         'readers': [self.public_article_group_id],
        #                     }
        #                 }
        #             }                                        
        #         }
        #     )
        # )        

        # comment_invitation_id = f'{self.public_article_group_id}/-/Comment'

        # self.client.post_invitation_edit(
        #     invitations = self.public_article_meta_invitation_id,
        #     signatures = [self.public_article_group_id],
        #     invitation = openreview.api.Invitation(
        #         id=comment_invitation_id,
        #         readers=['everyone'],
        #         writers=[self.public_article_group_id],
        #         signatures=['~Super_User1'], # be able to create tags on behalf of the authors and signatures
        #         invitees=['everyone'],
        #         process=self.get_process_content('process/open_comment_process.py'),
        #         edit={
        #             'readers': ['everyone'],
        #             'signatures': {
        #                 'param': {
        #                     'items': [
        #                         { 'prefix': '~.*', 'optional': True },
        #                         { 'value': self.support_group_id, 'optional': True }
        #                     ]
        #                 }
        #             },
        #             'writers': [self.public_article_group_id, '${2/signatures}'],
        #             'note': {
        #                 'id': {
        #                     'param': {
        #                         'withInvitation': comment_invitation_id,
        #                         'optional': True
        #                     }
        #                 },
        #                 'forum': {
        #                     'param': {
        #                         'withVenueid': self.public_article_group_id
        #                     }
        #                 },
        #                 'replyto': {
        #                     'param': {
        #                         'withForum': '${1/forum}'
        #                     }
        #                 },
        #                 'readers': ['everyone'],
        #                 'signatures': ['${3/signatures}'],
        #                 'writers': ['${3/writers}'],
        #                 'content': {
        #                     'comment': {
        #                         'order': 1,
        #                         'description': 'Comments are public and you can subscribe/unsubscribe to email notifications.',
        #                         'value': {
        #                             'param': {
        #                                 'type': 'string',
        #                                 'maxLength': 5000,
        #                                 'markdown': True,
        #                                 'input': 'textarea'
        #                             }
        #                         }
        #                     }
        #                 }
        #             }                                        
        #         }
        #     )
        # )

        # subscription_invitation_id = f'{self.public_article_group_id}/-/Notification_Subscription'

        # self.client.post_invitation_edit(
        #     invitations = self.public_article_meta_invitation_id,
        #     signatures = [self.public_article_group_id],
        #     invitation = openreview.api.Invitation(
        #         id=subscription_invitation_id,
        #         description='Subscribe to email notifications for this forum.',
        #         readers=['everyone'],
        #         writers=[self.public_article_group_id],
        #         signatures=[self.public_article_group_id],
        #         invitees=['everyone'],
        #         maxReplies=1,
        #         content={
        #             'presentation': {
        #                 'value': {
        #                     'tag': 'Subscribed',
        #                     'noTag': 'Subscribe'
        #                 }
        #             }
        #         },
        #         tag={
        #             'id': {
        #                 'param': {
        #                     'withInvitation': subscription_invitation_id,
        #                     'optional': True
        #                 }
        #             },
        #             'forum': {
        #                 'param': {
        #                     'withVenueid': self.public_article_group_id
        #                 }
        #             },
        #             'note': '${1/forum}',
        #             'ddate': {
        #                 'param': {
        #                     'range': [ 0, 9999999999999 ],
        #                     'optional': True,
        #                     'deletable': True
        #                 }
        #             },
        #             'readers': ['everyone'],
        #             'signature': {
        #                 'param': {
        #                     'enum': [
        #                         { 'prefix': '~.*' }
        #                     ]
        #                 }
        #             },
        #             'writers': ['${2/signature}'],
        #             'label': '🔔'
        #         }
        #     )
        # )                                                          

        # bookmark_invitation_id = f'{self.public_article_group_id}/-/Bookmark'

        # self.client.post_invitation_edit(
        #     invitations = self.public_article_meta_invitation_id,
        #     signatures = [self.public_article_group_id],
        #     invitation = openreview.api.Invitation(
        #         id=bookmark_invitation_id,
        #         description='Bookmark this forum.',
        #         readers=['everyone'],
        #         writers=[self.public_article_group_id],
        #         signatures=[self.public_article_group_id],
        #         invitees=['everyone'],
        #         maxReplies=1,
        #         content={
        #             'presentation': {
        #                 'value': {
        #                     'tag': 'Bookmarked',
        #                     'noTag': 'Bookmark'
        #                 }
        #             }
        #         },                
        #         tag={
        #             'id': {
        #                 'param': {
        #                     'withInvitation': bookmark_invitation_id,
        #                     'optional': True
        #                 }
        #             },
        #             'forum': {
        #                 'param': {
        #                     'withVenueid': self.public_article_group_id
        #                 }
        #             },
        #             'note': '${1/forum}',
        #             'ddate': {
        #                 'param': {
        #                     'range': [ 0, 9999999999999 ],
        #                     'optional': True,
        #                     'deletable': True
        #                 }
        #             },
        #             'readers': ['everyone'],
        #             'signature': {
        #                 'param': {
        #                     'enum': [
        #                         { 'prefix': '~.*' }
        #                     ]
        #                 }
        #             },
        #             'writers': ['${2/signature}'],
        #             'label': '🔖'
        #         }
        #     )
        # )                                    

    def set_deprecated_dblp_ivitations(self):

        dblp_group_id = 'DBLP.org'
        dblp_uploader_group_id = f'{dblp_group_id}/Uploader'

        dblp_group = openreview.tools.get_group(self.client, dblp_group_id)
        if dblp_group is None:
            self.client.post_group_edit(
                invitation = f'{self.super_user}/-/Edit',
                signatures = [self.super_user],
                group = openreview.api.Group(
                    id = dblp_group_id,
                    readers = ['everyone'],
                    writers = [dblp_group_id],
                    nonreaders = [],
                    signatures = ['~Super_User1'],
                    signatories = [dblp_group_id],
                    members = []
                )
            )

        meta_invitation_id = f'{dblp_group_id}/-/Edit'
        self.client.post_invitation_edit(
            invitations = None,
            signatures = [self.super_user],
            invitation = openreview.api.Invitation(
                id=meta_invitation_id,
                invitees=[dblp_uploader_group_id],
                readers=[dblp_group_id, dblp_uploader_group_id],
                signatures=[dblp_group_id],                
                edit=True
            )
        )

        dblp_uploader_group = openreview.tools.get_group(self.client, dblp_uploader_group_id)
        if dblp_uploader_group is None:
            self.client.post_group_edit(
                invitation = meta_invitation_id,
                signatures = [dblp_group_id],
                group = openreview.api.Group(
                    id = dblp_uploader_group_id,
                    readers = [dblp_uploader_group_id],
                    writers = [dblp_group_id],
                    nonreaders = [],
                    signatures = [dblp_group_id],
                    signatories = [dblp_group_id],
                    members = []
                )
            )

        record_invitation_id = f'{dblp_group_id}/-/Record'
        with open(os.path.join(os.path.dirname(__file__), 'process/deprecated_dblp_record_process.js'), 'r') as f:
            file_content = f.read()

        self.client.post_invitation_edit(
            invitations = meta_invitation_id,
            signatures = [dblp_group_id],
            invitation = openreview.api.Invitation(
                id=record_invitation_id,
                readers=['everyone'],
                writers=[dblp_group_id],
                signatures=[dblp_group_id],
                invitees=['~'],
                process=file_content,
                edit={
                    'readers': ['everyone'],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True },
                                { 'value': dblp_uploader_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers':  [dblp_uploader_group_id],
                    'content': {
                        'xml': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        }
                    },
                    'note': {
                        'signatures': [ '${3/signatures}' ],
                        'readers': ['everyone'],
                        'writers': [ '~'],
                        'license': 'CC BY-SA 4.0',
                        'content': {
                            'title': {
                                'order': 1,
                                'description': 'Title of paper.',
                                'value': { 
                                    'param': { 
                                        'type': 'string',
                                        'regex': '^.{1,250}$'
                                    }
                                }
                            },
                            'authors': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'type': 'string[]',
                                        'regex': '[^;,\\n]+(,[^,\\n]+)*'
                                    }
                                }
                            },
                            'authorids': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'type': 'string[]',
                                        'optional': True
                                    }
                                }
                            },                        
                            'venue': {
                                'order': 3,
                                'description': 'Enter the venue where the paper was published.',
                                'value': {
                                    'param': {
                                        'type': 'string'
                                    }
                                }
                            },
                            'venueid': {
                                'order': 4,
                                'value': {
                                    'param': {
                                        'type': "string",
                                        'const': dblp_group_id,
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )

        author_coreference_invitation_id = f'{dblp_group_id}/-/Author_Coreference'

        with open(os.path.join(os.path.dirname(__file__), 'process/deprecated_dblp_author_coreference_pre_process.js'), 'r') as f:
            file_content = f.read()

        self.client.post_invitation_edit(
            invitations = meta_invitation_id,
            signatures = [dblp_group_id],
            invitation = openreview.api.Invitation(
                id=author_coreference_invitation_id,
                readers=['everyone'],
                writers=[dblp_group_id],
                signatures=[dblp_group_id],
                invitees=['~'],
                preprocess=file_content,
                edit={
                    'readers': ['everyone'],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True },
                                { 'value': dblp_uploader_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers':  [dblp_group_id],
                    'content': {
                        'author_index': {
                            'order': 1,
                            'description': 'Enter the 0 based index of the author in the author list. The author name listed in that position must match with one of your names in your profile.',
                            'value': {
                                'param': {
                                    'type': 'integer'
                                }
                            }
                        },
                        'author_id' : {
                            'order': 2,
                            'description': 'Enter the author id that matches with the author name in the author list.',
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        },
                    },
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': record_invitation_id
                            }
                        },
                        'content': {
                            'authorids': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'const': {
                                            'replace': {
                                                'index': '${6/content/author_index/value}',
                                                'value': '${6/content/author_id/value}'
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )

        abstract_invitation_id = f'{dblp_group_id}/-/Abstract'

        self.client.post_invitation_edit(
            invitations = meta_invitation_id,
            signatures = [dblp_group_id],
            invitation = openreview.api.Invitation(
                id=abstract_invitation_id,
                readers=[dblp_uploader_group_id],
                writers=[dblp_group_id],
                signatures=[dblp_group_id],
                invitees=[dblp_uploader_group_id],
                edit={
                    'readers': ['everyone'],
                    'signatures': [dblp_uploader_group_id],
                    'writers':  [dblp_group_id, dblp_uploader_group_id],
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': record_invitation_id
                            }
                        },
                        'content': {
                            'abstract': {
                                'order': 1,
                                'value': {
                                    'param': {
                                        'type': 'string'
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )                                          



    
    def set_dblp_invitations(self):

        dblp_uploader_group_id = f'{self.dblp_group_id}/Uploader'

        dblp_group = openreview.tools.get_group(self.client, self.dblp_group_id)
        if dblp_group is None:
            self.client.post_group_edit(
                invitation = self.public_article_meta_invitation_id,
                signatures = [self.support_group_id],
                group = openreview.api.Group(
                    id = self.dblp_group_id,
                    readers = ['everyone'],
                    writers = [self.dblp_group_id],
                    nonreaders = [],
                    signatures = [self.support_group_id],
                    signatories = [self.dblp_group_id],
                    members = []
                )
            )

        dblp_uploader_group = openreview.tools.get_group(self.client, dblp_uploader_group_id)
        if dblp_uploader_group is None:
            self.client.post_group_edit(
                invitation = self.public_article_meta_invitation_id,
                signatures = [self.dblp_group_id],
                group = openreview.api.Group(
                    id = dblp_uploader_group_id,
                    readers = [dblp_uploader_group_id],
                    writers = [self.dblp_group_id],
                    nonreaders = [],
                    signatures = [self.dblp_group_id],
                    signatories = [self.dblp_group_id],
                    members = []
                )
            )

        record_invitation_id = f'{self.dblp_group_id}/-/Record'

        self.client.post_invitation_edit(
            invitations = self.public_article_meta_invitation_id,
            signatures = [self.dblp_group_id],
            replacement=True,
            invitation = openreview.api.Invitation(
                id=record_invitation_id,
                readers=['everyone'],
                writers=[self.dblp_group_id],
                signatures=[self.dblp_group_id],
                invitees=['~'],
                post_processes=[
                    {
                        'script': self.get_process_content('process/dblp_record_process.js'),
                    },
                    {
                        'script': self.get_process_content('process/dblp_record_post_process.js'),
                        'dependsOn': 0
                    }
                ],
                edit={
                    'readers': ['everyone'],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True },
                                { 'value': dblp_uploader_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers':  [dblp_uploader_group_id],
                    'content': {
                        'xml': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'input': 'textarea',
                                }
                            }
                        }
                    },
                    'note': {
                        'signatures': [ '${3/signatures}' ],
                        'readers': ['everyone'],
                        'writers': [ '~', self.dblp_group_id, self.support_group_id],
                        'license': 'CC BY-SA 4.0',                       
                        'externalId': {
                            'param': {
                                'regex': 'dblp:.*'
                            }
                        },                        
                        'content': {
                            'title': {
                                'order': 1,
                                'description': 'Title of paper.',
                                'value': { 
                                    'param': { 
                                        'type': 'string',
                                        'regex': '^.{1,250}$'
                                    }
                                }
                            },
                            'authors': {
                                'order': 2,
                                'description': 'Authors of paper.',
                                'value': {
                                    'param': {
                                        'type': 'author{}',
                                        'properties': {
                                            'fullname': { 'param': { 'type': 'string' } },
                                            'username': { 'param': { 'type': 'string' } },
                                        },
                                    }
                                }
                            },
                            'venue': {
                                'order': 3,
                                'description': 'Enter the venue where the paper was published.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'hidden': True
                                    }
                                }
                            },
                            'venueid': {
                                'order': 4,
                                'value': {
                                    'param': {
                                        'type': "string",
                                        'const': self.dblp_group_id,
                                        'hidden': True
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )

        abstract_invitation_id = f'{self.dblp_group_id}/-/Abstract'

        self.client.post_invitation_edit(
            invitations = self.public_article_meta_invitation_id,
            signatures = [self.dblp_group_id],
            invitation = openreview.api.Invitation(
                id=abstract_invitation_id,
                readers=[dblp_uploader_group_id],
                writers=[self.dblp_group_id],
                signatures=[self.dblp_group_id],
                invitees=[dblp_uploader_group_id],
                edit={
                    'readers': ['everyone'],
                    'signatures': [dblp_uploader_group_id],
                    'writers':  [self.dblp_group_id, dblp_uploader_group_id],
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': record_invitation_id
                            }
                        },
                        'content': {
                            'abstract': {
                                'order': 1,
                                'value': {
                                    'param': {
                                        'type': 'string'
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )


    def set_arxiv_invitations(self):

        arxiv_uploader_group_id = f'{self.arxiv_group_id}/Uploader'

        arxiv_group = openreview.tools.get_group(self.client, self.arxiv_group_id)
        if arxiv_group is None:
            self.client.post_group_edit(
                invitation = self.public_article_meta_invitation_id,
                signatures = [self.super_user],
                group = openreview.api.Group(
                    id = self.arxiv_group_id,
                    readers = ['everyone'],
                    writers = [self.arxiv_group_id],
                    nonreaders = [],
                    signatures = ['~Super_User1'],
                    signatories = [self.arxiv_group_id],
                    members = []
                )
            )

        dblp_uploader_group = openreview.tools.get_group(self.client, arxiv_uploader_group_id)
        if dblp_uploader_group is None:
            self.client.post_group_edit(
                invitation = self.public_article_meta_invitation_id,
                signatures = [self.arxiv_group_id],
                group = openreview.api.Group(
                    id = arxiv_uploader_group_id,
                    readers = [arxiv_uploader_group_id],
                    writers = [self.arxiv_group_id],
                    nonreaders = [],
                    signatures = [self.arxiv_group_id],
                    signatories = [self.arxiv_group_id],
                    members = []
                )
            )

        record_invitation_id = f'{self.arxiv_group_id}/-/Record'

        self.client.post_invitation_edit(
            invitations = self.public_article_meta_invitation_id,
            signatures = [self.arxiv_group_id],
            replacement=True,
            invitation = openreview.api.Invitation(
                id=record_invitation_id,
                readers=['everyone'],
                writers=[self.arxiv_group_id],
                signatures=[self.arxiv_group_id],
                invitees=['~'],
                humanVerificationRequired=openreview.tools.DEFAULT_HUMAN_VERIFICATION,
                process=self.get_process_content('process/arxiv_record_process.js'),
                edit={
                    'readers': ['everyone'],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True },
                                { 'value': arxiv_uploader_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers':  [arxiv_uploader_group_id],
                    'content': {
                        'xml': {
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'input': 'textarea',
                                }
                            }
                        }
                    },                    
                    'note': {
                        'signatures': [ '${3/signatures}' ],
                        'readers': ['everyone'],
                        'writers': [ '~', self.arxiv_group_id, self.support_group_id],
                        'license': 'CC BY-SA 4.0',
                        'id': {
                            'param': {
                                'withInvitation': record_invitation_id,
                                'optional': True
                            }
                        },
                        'externalId': {
                            'param': {
                                'regex': 'arxiv:.*'
                            }
                        },                        
                        'pdate': {
                            'param': {
                                'range': [ 0, 9999999999999 ]
                            }
                        },
                        'mdate': {
                            'param': {
                                'range': [ 0, 9999999999999 ]
                            }
                        },                         
                        'content': {
                            'title': {
                                'order': 1,
                                'description': 'Title of paper.',
                                'value': { 
                                    'param': { 
                                        'type': 'string',
                                        'regex': '^.{1,250}$'
                                    }
                                }
                            },
                            'authors': {
                                'order': 2,
                                'description': 'Authors of paper.',
                                'value': {
                                    'param': {
                                        'type': 'author{}',
                                        'properties': {
                                            'fullname': { 'param': { 'type': 'string' } },
                                            'username': { 'param': { 'type': 'string' } },
                                        },
                                    }
                                }
                            },
                            'abstract': {
                                'order': 3,
                                'description': 'Abstract of paper.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'markdown': True,
                                        'input': 'textarea',
                                        'optional': True
                                    }
                                }
                            },
                            'subject_areas': {
                                'order': 4,
                                'description': 'Subject areas of paper.',
                                'value': {
                                    'param': {
                                        'type': 'string[]',
                                        'items': categories,
                                        'optional': True,
                                        'input': 'select',
                                    }
                                }
                            },
                            'pdf': {
                                'order': 5,
                                'description': 'Link to the PDF paper.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'regex': 'https?://arxiv.org/pdf/.*',
                                        'optional': True
                                    }
                                }
                            },
                            'venue': {
                                'order': 6,
                                'description': 'Enter the venue where the paper was published.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'const': 'arXiv',
                                        'hidden': True
                                    }
                                }
                            },
                            'venueid': {
                                'order': 7,
                                'value': {
                                    'param': {
                                        'type': "string",
                                        'const': self.public_article_group_id,
                                        'hidden': True
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )               

    def set_orcid_invitations(self):

        orcid_uploader_group_id = f'{self.orcid_group_id}/Uploader'

        orcid_group = openreview.tools.get_group(self.client, self.orcid_group_id)
        if orcid_group is None:
            self.client.post_group_edit(
                invitation = self.public_article_meta_invitation_id,
                signatures = [self.support_group_id],
                group = openreview.api.Group(
                    id = self.orcid_group_id,
                    readers = ['everyone'],
                    writers = [self.orcid_group_id],
                    nonreaders = [],
                    signatures = [self.support_group_id],
                    signatories = [self.orcid_group_id],
                    members = []
                )
            )

        orcid_uploader_group = openreview.tools.get_group(self.client, orcid_uploader_group_id)
        if orcid_uploader_group is None:
            self.client.post_group_edit(
                invitation = self.public_article_meta_invitation_id,
                signatures = [self.orcid_group_id],
                group = openreview.api.Group(
                    id = orcid_uploader_group_id,
                    readers = [orcid_uploader_group_id],
                    writers = [self.orcid_group_id],
                    nonreaders = [],
                    signatures = [self.orcid_group_id],
                    signatories = [self.orcid_group_id],
                    members = []
                )
            )

        record_invitation_id = f'{self.orcid_group_id}/-/Record'

        self.client.post_invitation_edit(
            invitations = self.public_article_meta_invitation_id,
            signatures = [self.orcid_group_id],
            replacement=True,
            invitation = openreview.api.Invitation(
                id=record_invitation_id,
                readers=['everyone'],
                writers=[self.orcid_group_id],
                signatures=[self.orcid_group_id],
                invitees=['~'],
                post_processes=[
                    {
                        'script': self.get_process_content('process/orcid_record_process.js'),
                    },
                    {
                        'script': self.get_process_content('process/orcid_record_post_process.js'),
                        'dependsOn': 0
                    }
                ],
                edit={
                    'readers': ['everyone'],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True },
                                { 'value': orcid_uploader_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers':  [orcid_uploader_group_id],
                    'content': {
                        'json': {
                            'value': {
                                'param': {
                                    'type': 'json',
                                    'input': 'textarea',
                                }
                            }
                        }
                    },
                    'note': {
                        'signatures': [ '${3/signatures}' ],
                        'readers': ['everyone'],
                        'writers': [ '~', self.orcid_group_id, self.support_group_id],
                        'license': 'CC BY-SA 4.0',                        
                        'externalId': {
                            'param': {
                                'regex': 'doi:.*'
                            }
                        },                        
                        'content': {
                            'title': {
                                'order': 1,
                                'description': 'Title of paper.',
                                'value': { 
                                    'param': { 
                                        'type': 'string',
                                        'regex': '^.{1,250}$'
                                    }
                                }
                            },
                            'authors': {
                                'order': 2,
                                'description': 'Authors of paper.',
                                'value': {
                                    'param': {
                                        'type': 'author{}',
                                        'properties': {
                                            'fullname': { 'param': { 'type': 'string' } },
                                            'username': { 'param': { 'type': 'string' } },
                                        },
                                    }
                                }
                            },
                            'venue': {
                                'order': 3,
                                'description': 'Enter the venue where the paper was published.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'hidden': True
                                    }
                                }
                            },
                            'venueid': {
                                'order': 4,
                                'value': {
                                    'param': {
                                        'type': "string",
                                        'const': self.public_article_group_id,
                                        'hidden': True
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )

        abstract_invitation_id = f'{self.orcid_group_id}/-/Abstract'

        self.client.post_invitation_edit(
            invitations = self.public_article_meta_invitation_id,
            signatures = [self.orcid_group_id],
            invitation = openreview.api.Invitation(
                id=abstract_invitation_id,
                readers=[orcid_uploader_group_id],
                writers=[self.orcid_group_id],
                signatures=[self.orcid_group_id],
                invitees=[orcid_uploader_group_id],
                edit={
                    'readers': ['everyone'],
                    'signatures': [orcid_uploader_group_id],
                    'writers':  [self.orcid_group_id, orcid_uploader_group_id],
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': record_invitation_id
                            }
                        },
                        'content': {
                            'abstract': {
                                'order': 1,
                                'value': {
                                    'param': {
                                        'type': 'string'
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )    
    
    def set_remove_name_invitations(self):

        content = {
            'name': {
                'order': 1,
                'description': 'Name that want to be removed.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': '.*'
                    }
                }
            },
            'usernames': {
                'order': 2,
                'description': 'Usernames that want to be removed.',
                'value': {
                    'param': {
                        'type': 'string[]',
                        'regex': '~.*'
                    }
                }
            },
            'comment': {
                'order': 3,
                'description': 'Reason why you want to delete your name.',
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 5000,
                        'markdown': True,
                        'input': 'textarea',
                        'optional': True
                    }
                }
            },
            'status': {
                'value': 'Pending'
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_process.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("REMOVAL_DECISION_INVITATION_ID = ''", "REMOVAL_DECISION_INVITATION_ID = '" + f'{self.support_group_id}/-/Profile_Name_Removal_Decision' + "'")
                
            with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_pre_process.py'), 'r') as pre:
                pre_file_content = pre.read()
                self.client.post_invitation_edit(
                    invitations=f'{self.super_user}/-/Edit',
                    signatures=[self.super_user],
                    invitation=openreview.api.Invitation(                    
                        id=f'{self.support_group_id}/-/Profile_Name_Removal',
                        readers=['~'],
                        writers=[self.support_group_id],
                        signatures=[self.super_user],
                        invitees=['~'],
                        process=file_content,
                        preprocess=pre_file_content,
                        edit={
                            'readers': [self.support_group_id],
                            'writers': [self.support_group_id],
                            'signatures': {
                                'param': {
                                    'items': [
                                        { 'prefix': '~.*', 'optional': True },
                                        { 'value': self.support_group_id, 'optional': True } 
                                    ]
                                }
                            },
                            'note': {
                                'readers': [self.support_group_id, '${3/signatures}'],
                                'writers': [self.support_group_id],
                                'signatures': ['${3/signatures}'],
                                'content': content
                            }
                        }
                    )
                )        
    

        content = {
            'status': {
                'order': 1,
                'description': 'Decision status.',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': ['Accepted', 'Rejected']
                    }
                }
            },
            'support_comment': {
                'order': 2,
                'description': 'Justify the decision.',
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 5000,
                        'markdown': True,
                        'input': 'textarea',
                        'optional': True
                    }
                }
            }            
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_decision_process.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("AUTHOR_RENAME_INVITATION_ID = ''", "AUTHOR_RENAME_INVITATION_ID = '" + self.author_rename_invitation_id + "'")

            with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_name_decision_pre_process.py'), 'r') as pre:
                pre_file_content = pre.read()

        self.client.post_invitation_edit(
            invitations=f'{self.super_user}/-/Edit',
            signatures=[self.super_user],
            invitation=openreview.api.Invitation(
                id=f'{self.support_group_id}/-/Profile_Name_Removal_Decision',
                readers=[self.support_group_id],
                writers=[self.support_group_id],
                signatures=[self.super_user],
                invitees=[self.support_group_id],
                process=file_content,
                preprocess=pre_file_content,
                edit={
                    'readers': [self.support_group_id],
                    'writers': [self.support_group_id],
                    'signatures': [self.support_group_id],
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': f'{self.support_group_id}/-/Profile_Name_Removal'
                            }
                        },
                        'content': content
                    }
                }
            )
        )

        baseurl_v1, baseurl_v2 = openreview.tools.get_base_urls(self.client)
        client_v1 = openreview.Client(baseurl=baseurl_v1, token=self.client.token)        
        client_v1.post_invitation(openreview.Invitation(
            id=self.author_rename_invitation_id,
            readers=[self.support_group_id],
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            invitees=[self.support_group_id],
            reply={
                'readers': {
                    'values-regex': '.*'
                },
                'writers': {
                    'values':[self.support_group_id],
                },
                'signatures': {
                    'values': [self.support_group_id]
                },
                'content': {
                    'authors': {
                        'values-regex': '.*'
                    },
                    'authorids': {
                        'values-regex': '.*'
                    }
                }
            }
        ))            

    def set_remove_email_invitations(self):

        content = {
            'email': {
                'order': 1,
                'description': 'email that want to be removed.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
                    }
                }
            },
            'profile_id': {
                'order': 2,
                'description': 'profile id where the email associated with.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': '^~.*'
                    }
                }
            },
            'comment': {
                'order': 3,
                'description': 'Reason why you want to delete your name.',
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

        with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_email_process.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("AUTHOR_RENAME_INVITATION_ID = ''", "AUTHOR_RENAME_INVITATION_ID = '" + self.author_rename_invitation_id + "'")
            with open(os.path.join(os.path.dirname(__file__), 'process/request_remove_email_pre_process.py'), 'r') as pre:
                pre_file_content = pre.read()
                self.client.post_invitation_edit(
                    invitations=f'{self.super_user}/-/Edit',
                    signatures=[self.super_user],
                    invitation=openreview.api.Invitation(
                        id=f'{self.support_group_id}/-/Profile_Email_Removal',
                        readers=[self.support_group_id],
                        writers=[self.support_group_id],
                        signatures=[self.super_user],
                        invitees=[self.support_group_id],
                        process=file_content,
                        preprocess=pre_file_content,
                        edit={
                            'readers': [self.support_group_id],
                            'writers': [self.support_group_id],
                            'signatures': [self.support_group_id],
                            'note': {
                                'readers': [self.support_group_id],
                                'writers': [self.support_group_id],
                                'signatures': [self.support_group_id],
                                'content': content
                            }
                        }
                    )
                )

    def set_archive_invitations(self):

        archive_group_id = f'{self.super_user}/Archive'

        self.client.post_invitation_edit(invitations=None,
            readers=[archive_group_id],
            writers=[archive_group_id],
            signatures=['~Super_User1'],
            invitation=openreview.api.Invitation(id=f'{archive_group_id}/-/Edit',
                invitees=[archive_group_id],
                readers=[archive_group_id],
                signatures=['~Super_User1'],
                edit=True
            )
        )        

        archive_group = openreview.api.Group(
            id = archive_group_id,
            readers = ['everyone'],
            writers = [archive_group_id],
            signatures = [self.super_user],
            signatories = [archive_group_id]
        )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/archiveWebfield.js'), 'r') as f:
            file_content = f.read()
            archive_group.web = file_content

            self.client.post_group_edit(
                invitation = f'{archive_group_id}/-/Edit',
                signatures = ['~Super_User1'],
                group = archive_group)

        self.client.post_invitation_edit(
            invitations = f'{archive_group_id}/-/Edit',
            signatures = [archive_group_id],
            invitation = openreview.api.Invitation(
                id=f'{archive_group.id}/-/Direct_Upload',
                readers=['~'],
                writers=[self.support_group_id],
                signatures=[archive_group_id],
                invitees=['~'],
                humanVerificationRequired=openreview.tools.DEFAULT_HUMAN_VERIFICATION,
                edit={
                    'readers': ['everyone'],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers':  ['${2/signatures}'],
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': f'{archive_group.id}/-/Direct_Upload',
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
                        'pdate': {
                            'param': {
                                'range': [ 0, 9999999999999 ]
                            }
                        },
                        'signatures': [ '${3/signatures}' ],
                        'readers': ['everyone'],
                        'writers': [ '${2/content/authorids/value}'],
                        'license': {
                            'param': {
                                'enum': [ 
                                    { 'value': 'CC BY 4.0', 'description': 'CC BY 4.0' },
                                    { 'value': 'CC BY-SA 4.0', 'description': 'CC BY-SA 4.0' },
                                    { 'value': 'CC BY-NC 4.0', 'description': 'CC BY-NC 4.0' },
                                    { 'value': 'CC BY-ND 4.0', 'description': 'CC BY-ND 4.0' },
                                    { 'value': 'CC BY-NC-SA 4.0', 'description': 'CC BY-NC-SA 4.0' },
                                    { 'value': 'CC BY-NC-ND 4.0', 'description': 'CC BY-NC-ND 4.0' },
                                    { 'value': 'CC0 1.0', 'description': 'CC0 1.0' },
                                    { 'value': 'WM2024 Conference', 'description': 'WM2024 Conference' },
                                    { 'value': 'arXiv.org perpetual, non-exclusive license', 'description': 'arXiv.org perpetual, non-exclusive license' },
                                ]
                            }
                        },
                        'content': {
                            'title': {
                                'order': 1,
                                'description': 'Title of paper.',
                                'value': { 
                                    'param': { 
                                        'type': 'string',
                                        'regex': '^.{1,250}$'
                                    }
                                }
                            },
                            'authors': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'type': 'string[]',
                                        'regex': '[^;,\\n]+(,[^,\\n]+)*',
                                        'hidden': True
                                    }
                                }
                            },
                            'authorids': {
                                'order': 3,
                                'description': 'Search author profile by name or profile ID. If the profile is not found, you can add the author by completing name as well as author email address.',
                                'value': {
                                    'param': {
                                        'type': 'profile{}',
                                        'regex': r"^~\S+$|^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
                                        'mismatchError': 'must be a valid email or profile ID'
                                    }
                                }
                            },                        
                            'abstract': {
                                'order': 4,
                                'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 5000,
                                        'markdown': True,
                                        'input': 'textarea'
                                    }
                                }
                            },
                            'pdf': {
                                'order': 5,
                                'description': 'Upload a PDF file that ends with .pdf.',
                                'value': {
                                    'param': {
                                        'type': 'file',
                                        'maxSize': 50,
                                        'extensions': ['pdf'],
                                        'optional': True,
                                        'deletable': True
                                    }
                                }
                            },
                            'html': {
                                'order': 6,
                                'description': 'Enter a URL to a PDF file.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'regex': r'(http|https):\/\/.+',
                                        'optional': True,
                                        'deletable': True
                                    }
                                }
                            },
                            'venue': {
                                'order': 7,
                                'description': 'Enter the venue where the paper was published.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'optional': True
                                    }
                                }
                            },
                            'venueid': {
                                'value': {
                                    'param': {
                                        'type': "string",
                                        'const': archive_group.id,
                                        'hidden': True
                                    }
                                }
                            }
                        }
                    }                                        
                }
            )
        )

        with open(os.path.join(os.path.dirname(__file__), 'process/archive_comment_process.py'), 'r') as f:
            process_content = f.read()

        self.client.post_invitation_edit(
            invitations = f'{archive_group.id}/-/Edit',
            signatures = [archive_group.id],
            invitation = openreview.api.Invitation(id=f'{archive_group.id}/-/Comment',
                invitees=[archive_group.id],
                readers=[archive_group.id],
                writers=[archive_group.id],
                signatures=[archive_group.id],
                content={
                    'comment_process_script': {
                        'value': process_content
                    }
                },
                edit={
                    'signatures': [archive_group.id],
                    'readers': [archive_group.id],
                    'writers': [archive_group.id],
                    'content': {
                        'noteNumber': {
                            'value': {
                                'param': {
                                    'type': 'integer'
                                }
                            }
                        },
                        'noteId': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        }
                    },
                    'replacement': True,
                    'invitation': {
                        'id': f'{archive_group.id}/Submission${{2/content/noteNumber/value}}/-/Comment',
                        'signatures': [ archive_group.id ],
                        'readers': ['everyone'],
                        'writers': [archive_group.id],
                        'invitees': ['everyone'],
                        'process': '''def process(client, edit, invitation):
        meta_invitation = client.get_invitation(invitation.invitations[0])
        script = meta_invitation.content['comment_process_script']['value']
        funcs = {
            'openreview': openreview
        }
        exec(script, funcs)
        funcs['process'](client, edit, invitation)
    ''',
                        'edit': {
                            'signatures': { 
                                'param': { 
                                    'items': [
                                        { 'prefix': '~.*' }
                                    ] 
                                }
                            },
                            'readers': ['${2/note/readers}'],
                            'writers': [archive_group.id],
                            'note': {
                                'id': {
                                    'param': {
                                        'withInvitation': f'{archive_group.id}/Submission${{6/content/noteNumber/value}}/-/Comment',
                                        'optional': True
                                    }
                                },
                                'forum': '${4/content/noteId/value}',
                                'replyto': { 
                                    'param': {
                                        'withForum': '${6/content/noteId/value}', 
                                    }
                                },
                                'ddate': {
                                    'param': {
                                        'range': [ 0, 9999999999999 ],
                                        'optional': True,
                                        'deletable': True
                                    }
                                },
                                'signatures': ['${3/signatures}'],
                                'readers': ['everyone'],
                                'writers': [archive_group.id, '${3/signatures}'],
                                'content': default_content.comment_v2.copy()
                            }
                        }
                    }

                }
            )
        )        

    def set_anonymous_preprint_invitations(self):

        anonymous_group_id = f'{self.super_user}/Anonymous_Preprint'
        author_anonymous_group_id = f'{anonymous_group_id}/Submission${{2/note/number}}/Authors'

        self.client.post_invitation_edit(invitations=None,
            readers=[anonymous_group_id],
            writers=[anonymous_group_id],
            signatures=['~Super_User1'],
            invitation=openreview.api.Invitation(id=f'{anonymous_group_id}/-/Edit',
                invitees=[anonymous_group_id],
                readers=[anonymous_group_id],
                signatures=['~Super_User1'],
                edit=True
            )
        )        
        
        anonymous_group = openreview.api.Group(
            id = anonymous_group_id,
            readers = ['everyone'],
            writers = [anonymous_group_id],
            signatures = [self.super_user],
            signatories = [anonymous_group_id]
        )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/anonymousWebfield.js'), 'r') as f:
            file_content = f.read()
            anonymous_group.web = file_content

            self.client.post_group_edit(
                invitation = f'{anonymous_group_id}/-/Edit',
                signatures = ['~Super_User1'],
                group = anonymous_group)
            

        self.client.add_members_to_group('venues', [anonymous_group_id])
        self.client.add_members_to_group('active_venues', [anonymous_group_id])            
            
        with open(os.path.join(os.path.dirname(__file__), 'process/anonymous_preprint_submission_process.py'), 'r') as f:
            process_content = f.read()

        self.client.post_invitation_edit(
            invitations = f'{anonymous_group_id}/-/Edit',
            signatures = [anonymous_group_id],
            invitation = openreview.api.Invitation(
                id=f'{anonymous_group_id}/-/Submission',
                readers=['~'],
                writers=[anonymous_group_id],
                signatures=[anonymous_group_id],
                invitees=['~'],
                edit={
                    'readers': [ anonymous_group_id, author_anonymous_group_id],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': anonymous_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers': [ anonymous_group_id, author_anonymous_group_id],
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': f'{anonymous_group_id}/-/Submission',
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
                        'odate': '${2/cdate}',
                        'signatures': [ f'{anonymous_group_id}/Submission${{2/number}}/Authors' ],
                        'readers': ['everyone'],
                        'writers': [ anonymous_group_id, f'{anonymous_group_id}/Submission${{2/number}}/Authors'],
                        'license': {
                            'param': {
                                'enum': [ 
                                    { 'value': 'CC BY 4.0', 'description': 'CC BY 4.0' },
                                    { 'value': 'CC BY-SA 4.0', 'description': 'CC BY-SA 4.0' },
                                    { 'value': 'CC BY-NC 4.0', 'description': 'CC BY-NC 4.0' },
                                    { 'value': 'CC BY-ND 4.0', 'description': 'CC BY-ND 4.0' },
                                    { 'value': 'CC BY-NC-SA 4.0', 'description': 'CC BY-NC-SA 4.0' },
                                    { 'value': 'CC BY-NC-ND 4.0', 'description': 'CC BY-NC-ND 4.0' },
                                    { 'value': 'CC0 1.0', 'description': 'CC0 1.0' } 
                                ]
                            }
                        },
                        'content': {
                            'title': {
                                'order': 1,
                                'description': 'Title of paper.',
                                'value': { 
                                    'param': { 
                                        'type': 'string',
                                        'regex': '^.{1,250}$'
                                    }
                                }
                            },
                            'authors': {
                                'order': 2,
                                'value': {
                                    'param': {
                                        'type': 'string[]',
                                        'regex': '[^;,\\n]+(,[^,\\n]+)*',
                                        'hidden': True
                                    }
                                },
                                'readers': [ anonymous_group_id, f'{anonymous_group_id}/Submission${{4/number}}/Authors']
                            },
                            'authorids': {
                                'order': 3,
                                'description': 'Search author profile by name or profile ID. If the profile is not found, you can add the author by completing name as well as author email address.',
                                'value': {
                                    'param': {
                                        'type': 'profile{}',
                                        'regex': r"^~\S+$|^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
                                        'mismatchError': 'must be a valid email or profile ID'
                                    }
                                },
                                'readers': [ anonymous_group_id, f'{anonymous_group_id}/Submission${{4/number}}/Authors']
                            },
                            'keywords': {
                                'description': 'Comma separated list of keywords.',
                                'order': 4,
                                'value': {
                                    'param': {
                                        'type': 'string[]',
                                        'regex': '.+'
                                    }
                                }
                            },
                            'TLDR': {
                                'order': 5,
                                'description': '\"Too Long; Didn\'t Read\": a short sentence describing your paper',
                                'value': {
                                    'param': {
                                        'fieldName': 'TL;DR',
                                        'type': 'string',
                                        'maxLength': 250,
                                        'optional': True,
                                        'deletable': True
                                    }
                                }        
                            },                                                    
                            'abstract': {
                                'order': 6,
                                'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'maxLength': 5000,
                                        'markdown': True,
                                        'input': 'textarea'
                                    }
                                }
                            },
                            'pdf': {
                                'order': 7,
                                'description': 'Upload a PDF file that ends with .pdf.',
                                'value': {
                                    'param': {
                                        'type': 'file',
                                        'maxSize': 50,
                                        'extensions': ['pdf']
                                    }
                                }
                            },
                            'venue': {
                                'order': 7,
                                'description': 'Enter the venue where the paper was published.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'const': 'Anonymous Preprint Submission',
                                        'hidden': True
                                    }
                                }
                            },
                            'venueid': {
                                'value': {
                                    'param': {
                                        'type': "string",
                                        'const': anonymous_group_id,
                                        'hidden': True
                                    }
                                }
                            }
                        }
                    }                                        
                },
                process=process_content
            )
        )

        with open(os.path.join(os.path.dirname(__file__), 'process/anonymous_preprint_comment_process.py'), 'r') as f:
            process_content = f.read()

        self.client.post_invitation_edit(
            invitations = f'{anonymous_group_id}/-/Edit',
            signatures = [anonymous_group_id],
            invitation = openreview.api.Invitation(id=f'{anonymous_group_id}/-/Comment',
                invitees=[anonymous_group_id],
                readers=[anonymous_group_id],
                writers=[anonymous_group_id],
                signatures=[anonymous_group_id],
                content={
                    'comment_process_script': {
                        'value': process_content
                    }
                },
                edit={
                    'signatures': [anonymous_group_id],
                    'readers': [anonymous_group_id],
                    'writers': [anonymous_group_id],
                    'content': {
                        'noteNumber': {
                            'value': {
                                'param': {
                                    'type': 'integer'
                                }
                            }
                        },
                        'noteId': {
                            'value': {
                                'param': {
                                    'type': 'string'
                                }
                            }
                        }
                    },
                    'replacement': True,
                    'invitation': {
                        'id': f'{anonymous_group_id}/Submission${{2/content/noteNumber/value}}/-/Comment',
                        'signatures': [ anonymous_group_id ],
                        'readers': ['everyone'],
                        'writers': [anonymous_group_id],
                        'invitees': ['everyone'],
                        'process': '''def process(client, edit, invitation):
        meta_invitation = client.get_invitation(invitation.invitations[0])
        script = meta_invitation.content['comment_process_script']['value']
        funcs = {
            'openreview': openreview
        }
        exec(script, funcs)
        funcs['process'](client, edit, invitation)
    ''',
                        'edit': {
                            'signatures': { 
                                'param': { 
                                    'items': [
                                        { 'prefix': '~.*', 'optional': True },
                                        { 'value': f'{anonymous_group_id}/Submission${{7/content/noteNumber/value}}/Authors', 'optional': True },
                                    ] 
                                }
                            },
                            'readers': ['${2/note/readers}'],
                            'writers': [anonymous_group_id],
                            'note': {
                                'id': {
                                    'param': {
                                        'withInvitation': f'{anonymous_group_id}/Submission${{6/content/noteNumber/value}}/-/Comment',
                                        'optional': True
                                    }
                                },
                                'forum': '${4/content/noteId/value}',
                                'replyto': { 
                                    'param': {
                                        'withForum': '${6/content/noteId/value}', 
                                    }
                                },
                                'ddate': {
                                    'param': {
                                        'range': [ 0, 9999999999999 ],
                                        'optional': True,
                                        'deletable': True
                                    }
                                },
                                'signatures': ['${3/signatures}'],
                                'readers': ['everyone'],
                                'writers': [anonymous_group_id, '${3/signatures}'],
                                'content': default_content.comment_v2.copy()
                            }
                        }
                    }

                }
            )
        )        
    
    def set_merge_profiles_invitations(self):

        content = {
            'email': {
                'order': 1,
                'description': 'email of the user making the request.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
                        'mismatchError': 'must be a valid email',
                        'optional': True
                    }
                }
            },
            'left': {
                'order': 2,
                'description': 'Username or email that want to be merged.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': r'^~[^\d\s]+[1-9][0-9]*$|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                        'mismatchError': 'must be a valid email or profile ID'
                    }
                }
            },
            'right': {
                'order': 3,
                'description': 'Username or email that want to be merged.',
                'value': {
                    'param': {
                        'type': 'string',
                        'regex': r'^~[^\d\s]+[1-9][0-9]*$|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                        'mismatchError': 'must be a valid email or profile ID'
                    }
                }
            },
            'comment': {
                'order': 4,
                'description': 'Reason why you want to delete your name.',
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 5000,
                        'markdown': True,
                        'input': 'textarea',
                        'optional': True
                    }
                }
            },
            'status': {
                'value': 'Pending'
            }
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_merge_profiles_process.py'), 'r') as f:
            file_content = f.read()
            self.client.post_invitation_edit(
                invitations = f'{self.super_user}/-/Edit',
                signatures = [self.super_user],
                invitation = openreview.api.Invitation(
                    id=f'{self.support_group_id}/-/Profile_Merge',
                    readers=['everyone'],
                    writers=[self.support_group_id],
                    signatures=[self.super_user],
                    invitees=['~', '(guest)'],
                    process=file_content,
                    edit={
                        'readers': [self.support_group_id, '${2/note/content/right/value}', '${2/note/content/left/value}'],
                        'writers': [self.support_group_id],
                        'signatures': {
                            'param': {
                                'items': [
                                    { 'prefix': '~.*', 'optional': True },
                                    { 'value': self.support_group_id, 'optional': True },
                                    { 'value': '(guest)', 'optional': True } 
                                ]
                            }
                        },
                        'note': {
                            'readers': ['${3/readers}'],
                            'writers': ['${3/writers}'],
                            'signatures': ['${3/signatures}'],
                            'content': content
                        }
                    }
                )
            )        
    

        content = {
            'status': {
                'order': 1,
                'description': 'Decision status.',
                'value': {
                    'param': {
                        'type': 'string',
                        'enum': ['Accepted', 'Rejected', 'Ignored']
                    }
                }
            },
            'support_comment': {
                'order': 2,
                'description': 'Justify the decision.',
                'value': {
                    'param': {
                        'type': 'string',
                        'maxLength': 5000,
                        'markdown': True,
                        'input': 'textarea',
                        'optional': True
                    }
                }
            }            
        }

        with open(os.path.join(os.path.dirname(__file__), 'process/request_merge_profiles_decision_process.py'), 'r') as f:
            file_content = f.read()
            file_content = file_content.replace("SUPPORT_USER_ID = ''", "SUPPORT_USER_ID = '" + self.support_group_id + "'")
            file_content = file_content.replace("AUTHOR_RENAME_INVITATION_ID = ''", "AUTHOR_RENAME_INVITATION_ID = '" + self.author_rename_invitation_id + "'")
            self.client.post_invitation_edit(
                invitations = f'{self.super_user}/-/Edit',
                signatures = [self.super_user],
                invitation = openreview.api.Invitation(
                    id=f'{self.support_group_id}/-/Profile_Merge_Decision',
                    readers=[self.support_group_id],
                    writers=[self.support_group_id],
                    signatures=[self.super_user],
                    invitees=[self.support_group_id],
                    process=file_content,
                    edit={
                        'readers': [self.support_group_id],
                        'writers': [self.support_group_id],
                        'signatures': [self.support_group_id],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': f'{self.support_group_id}/-/Profile_Merge'
                                }
                            },
                            'content': content
                        }
                    }
                )
            )           

    def set_news_article_invitations(self):

        news_article_group_id = f'{self.super_user}/News'

        self.client.post_invitation_edit(invitations=None,
            readers=[news_article_group_id],
            writers=[news_article_group_id],
            signatures=['~Super_User1'],
            invitation=openreview.api.Invitation(id=f'{news_article_group_id}/-/Edit',
                invitees=[news_article_group_id],
                readers=[news_article_group_id],
                signatures=['~Super_User1'],
                edit=True
            )
        )        

        news_group = openreview.api.Group(
            id = news_article_group_id,
            readers = ['everyone'],
            writers = [news_article_group_id],
            signatures = [self.super_user],
            signatories = [news_article_group_id]
        )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/newsWebfield.js'), 'r') as f:
            file_content = f.read()
            news_group.web = file_content

            self.client.post_group_edit(
                invitation = f'{news_article_group_id}/-/Edit',
                signatures = ['~Super_User1'],
                group = news_group)

        self.client.post_invitation_edit(
            invitations = f'{news_article_group_id}/-/Edit',
            signatures = [news_article_group_id],
            invitation = openreview.api.Invitation(
                id=f'{news_group.id}/-/Article',
                readers=[news_article_group_id],
                writers=[news_article_group_id],
                signatures=[news_article_group_id],
                invitees=[news_article_group_id],
                edit={
                    'readers': [news_article_group_id, '${2/signatures}'],
                    'signatures': { 
                        'param': { 
                            'items': [
                                { 'prefix': '~.*', 'optional': True },
                                { 'value': self.support_group_id, 'optional': True },
                                { 'value': news_article_group_id, 'optional': True } 
                            ]
                        } 
                    },
                    'writers':  ['${2/signatures}'],
                    'ddate': {
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'note': {
                        'id': {
                            'param': {
                                'withInvitation': f'{news_group.id}/-/Article',
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
                        'cdate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                            }
                        },
                        'mdate': {
                            'param': {
                                'range': [ 0, 9999999999999 ],
                            }
                        },
                        'signatures': [ '${3/signatures}' ],
                        'readers': { 
                            'param': { 
                                'items': [
                                    { 'value': 'everyone', 'optional': True },
                                    { 'value': news_article_group_id, 'optional': True } 
                                ]
                            } 
                        },
                        'writers': [ '${3/signatures}'],
                        'license': 'CC BY 4.0',
                        'content': {
                            'title': {
                                'order': 1,
                                'description': 'Title of paper.',
                                'value': { 
                                    'param': { 
                                        'type': 'string',
                                        'regex': '^.{1,250}$'
                                    }
                                }
                            },
                            'authors': {
                                'order': 2,
                                'description': 'Names of authors.',
                                'value': { 
                                    'param': { 
                                        'type': "string[]",
                                        'regex': '[^;,\\n]+(,[^,\\n]+)*',
                                        'hidden': True
                                    }
                                }
                            },
                            'authorids': {
                                'order': 3,
                                'description': 'Search author profile by first, middle and last name or email address.',
                                'value': { 
                                    'param': {
                                        'type': 'group{}',
                                        'regex': r".*",
                                        'mismatchError': 'must be a valid profile ID'
                                    }
                                }
                            },
                            'article': {
                                'order': 4,
                                'description': 'Content of the news article. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                                'value': { 
                                    'param': { 
                                        'fieldName': ' ',
                                        'type': 'string',
                                        'markdown': True,
                                        'input': 'textarea'
                                    }
                                }
                            },
                            'image_one': {
                                'order': 5,
                                'description': 'Upload an image for your article.',
                                'value': {
                                    'param': {
                                        'type': 'file',
                                        'maxSize': 50,
                                        'extensions': ['png', 'jpg', 'jpeg', 'gif'],
                                        'optional': True,
                                        'deletable': True
                                    }
                                }
                            }                                    
                        }
                    }                                        
                }
            )
        )

        