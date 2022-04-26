submission_template = {
    'id': 'OpenReview.net/Support/-/Submission_Template', ## template should be part of the name?
    'invitees': ['active_venues'], ## how to give access to the PCs only from all the venues
    'readers': ['everyone'],
    'writers': ['OpenReview.net/Support'],
    'signatures': ['OpenReview.net/Support'],
    'edit': {
        'readers': ['OpenReview.net/Support', '${content.venueid.value}'],
        'writers': ['OpenReview.net/Support', '${content.venueid.value}'],
        'signatures': ['${content.venueid.value}'],
        'content': {
            'venueid': { 
                'value': {
                    'param': {
                        'description': 'Venue id',
                        'memberOf': 'active_venues' ## any other validation? can we use any group id as venueid?
                    }
                },
                'order': 1,
                'type': 'group'
            }, 
            'name': { 
                'value': {
                    'param': {
                        'regex': '.*',
                        'description': 'Submission name.', 
                        'optional': True
                    }
                },
                'order': 2,
                'type': 'string'
            },
            'cdate': {
                'value': {
                    'param': { 
                        'range': [ 0, 9999999999999 ],
                        'description': 'Activation date.'
                    },
                },
                'order': 3,
                'type': 'date',
            },
            'duedate': {
                'value': {
                    'param': { 
                        'description': 'Submission due date.',
                        'range': [ 0, 9999999999999 ] 
                    },
                },
                'order': 4,
                'type': 'date'
            },      
        },
        'invitation': {
            'id': '${../content.venueid.value}/-/${../content.name.value}',
            'signatures': ['${../content.venueid.value}'],
            'readers': ['everyone'],
            'writers': ['${signatures}'],
            'invitees': ['~'],
            'cdate': { '${../content.cdate.value}' },
            'duedate': { '${../content.duedate.value}' },
            'process': '''
def process(client, edit, invitation):
    ## 1. Create paper group: submission_group_id = f'{invitation.content.venueid.value}/${../content.name.value}{edit.note.number}' ## Example: TMLR/Submission1
    ## 2. Create author paper author_submission_group_id = f'{submission_group_id}/Authors' ## Example: TMLR/Submission1/Authors
    ## 3. Add authorids as members of the group
    ## 4. Send confirmation email to the author group
    ''',
            'edit': {
                'signatures': { 'param': { 'regex': '~.*' }},
                'readers': ['${../../content.venueid.value}', '${../../content.venueid.value}/${../../content.name.value}\\${note.number}/Authors'], ## note.number needs to be escaped. It is defined at note creation
                'writers': ['${../..content.venueid.value}'],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': '${edit.invitation}', ## can I reference the invitation id of the edit
                            'optional': True
                        }
                    },
                    'signatures': ['${../../../content.venueid.value}/${../../../content.name.value}\\${note.number}/Authors'],
                    'readers': ['${../../../content.venueid.value}', '${../../../content.venueid.value}/${../../../content.name.value}\\${note.number}/Authors'],
                    'writers': ['${../../../content.venueid.value}', '${../../../content.venueid.value}/${../../../content.name.value}\\${note.number}/Authors'],
                    'content': {
                        'title': {
                            'order': 1, ## we store this value in the invitation edit but we don't store it in the note, should we assume that only 'value' and 'readers' will be saved in the note content?
                            'type': 'string', 
                            'value': { 
                                'param': { 
                                    'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$', ## Same here.
                                    'regex': '.{1,250}' 
                                } 
                            }
                        },
                        'authors': {
                            'order': 2,
                            'type': 'string[]', 
                            'value': { 
                                'param': { 
                                    'description': 'Comma separated list of author names.',
                                    'regex': '[^;,\\n]+(,[^,\\n]+)*' 
                                },
                               'hidden': True
                            },
                            'readers': [ '${../../../../content.venueid.value}', '${../../../../content.venueid.value}/${../../../../.content.name.value}\\${note.number}/Authors']
                        },
                        'authorids': {
                            'order': 3,
                            'type': 'group[]',
                            'value': { 
                                'param': { 
                                    'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                                    'regex': r'~.*' 
                                }
                            },
                            'readers': [ '${../../../../content.venueid.value}', '${../../../../content.venueid.value}/${../../../../content.name.value}\\${note.number}/Authors']
                        },
                        'keywords': {
                            'order': 4,
                            'type': 'string[]', 
                            'value': { 
                                'param': { 
                                    'description': 'Comma separated list of keywords',
                                    'regex': '(^$)|[^;,\\n]+(,[^,\\n]+)*' 
                                }
                            }
                        },
                        'abstract': {
                            'order': 5,
                            'type': 'string', 
                            'value': { 
                                'param': { 
                                    'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                                    'regex': '^[\\S\\s]{1,5000}$', 
                                    'maxLength': 5000,
                                    'markdown': True
                                }
                            }
                        },
                        'TL;DR': {
                            'order': 6,
                            'type': 'string', 
                            'value': { 
                                'param': { 
                                    'description': '\"Too Long; Didn\'t Read\": a short sentence describing your paper',
                                    'regex': '^[\\S\\s]{1,500}$', 
                                    'maxLength': 500 
                                }
                            },
                        },
                        'pdf': {
                            'order': 7,
                            'type': 'file',
                            'value': {
                                'param': {
                                    'description': 'Upload a PDF file that ends with .pdf.',
                                    'value-file': {
                                        'fileTypes': ['pdf'],
                                        'size': 50
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


review_template = {
    'id': 'OpenReview.net/Support/-/Review_Template', ## template should be part of the name?
    'invitees': ['active_venues'], ## how to give access to the PCs only from all the venues
    'readers': ['everyone'],
    'writers': ['OpenReview.net'],
    'signatures': ['OpenReview.net'],
    'edit': {
        'readers': ['OpenReview.net/Support', '${content.venueid.value}'],
        'writers': ['OpenReview.net/Support', '${content.venueid.value}'],
        'signatures': ['${content.venueid.value}'],        
        'params': {
            'venueid': { 'type': 'group' }, ## any other validation? can we use any group id as venueid?
            'name': { 'type': 'string', 'default': 'Official_Review'},
            'submission_name': { 'type': 'string'}, ## need to know the submission name to validate and create the paper groups
            'cdate': { 'type': 'date', 'range': [ 0, 9999999999999 ] },
            'duedate': { 'type': 'date', 'range': [ 0, 9999999999999 ] }       
        },
        'invitation': {
            'id': '${../content.venueid.value}/-/${../content.name.value}',
            'signatures': ['${../content.venueid.value}'],
            'readers': ['${signatures}'],
            'writers': ['${signatures}'],
            'invitees': ['${signatures}'],
            'cdate': { '${../params.cdate}' },
            'duedate': { '${../params.duedate}' },
            'dateprocesses': [{
                'dates': ['#{cdate}'],
                'script': '''
def process(client, invitation):
    submissions = client.get_notes(invitation='${../../content.venueid.value}/-/${../../params.submission_name}')
    ## Create review invitations for all the active submissions
    for submission in submissions:
        client.post_invitation_edit({
            invitation: '${../../content.venueid.value}/-/${../../content.name.value}',
            params: {
                noteId: submission.id,
                noteNumber: submission.number
            }
        })
    '''
            }],        
            'edit': {
                'signatures': ['${../../content.venueid.value}'],
                'readers': ['${signatures}'],
                'writers': ['${signatures}'],
                'params': {
                    'noteId': { 'type': 'note', 'withInvitation': '${../../content.venueid.value}/-/${../../params.submission_name}' }, ## any other validation? use withInvitation?
                    'noteNumber': { 'type': 'integer'},
                    'submissionGroupId': '${../../content.venueid.value}/${../../params.submission_name}${noteNumber}' ## constant so I can use it in several places
                },                
                'invitation': {
                    'id': '${../../params.submissionGroupId}/-/${../../../content.name.value}',
                    'signatures': ['${../../../content.venueid.value}'],
                    'readers': ['everyone'], ## everyone or just the reviewers?
                    'writers': ['${signatures}'],
                    'invitees': ['${../../params.submissionGroupId}/Reviewers'], ## should we parametrize the role names?
                    'cdate': { '${../../../params.cdate}' },
                    'duedate': { '${../../../params.duedate}' },
                    'process': '''
def process(client, edit, invitation):
    ## send confirmation email to the reviewer
    ## add the reviewer to the submitted group (?)
                    ''',
                    'edit': {
                        'signatures': { 'param': { 'regex': '${../../../params.submissionGroupId}/Reviewer_', 'type': 'group' }},
                        'readers': ['${../../../../content.venueid.value}', '${signatures}'], 
                        'writers': ['${../../../../content.venueid.value}'],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': '${../../../../id}', ## can I reference the invitation id of the edit
                                    'optional': True
                                }
                            },
                            'forum': '${../../params.noteId}',
                            'replyto': '${../../params.noteId}',
                            'signatures': ['${../signatures}'], ## how to resolve this in the UI?
                            'readers': ['${../../../../../content.venueid.value}', '${signatures}'],
                            'writers': ['${../../../../../content.venueid.value}', '${signatures}'], ## only visible to the submitted reviewer, should we create another template if we want to have public reviews?
                            'content': {
                                'title': {
                                    'order': 1, ## we store this value in the invitation edit but we don't store it in the note, should we assume that only 'value' and 'readers' will be saved in the note content?
                                    'description': 'Brief summary of your review.', ## Same here.
                                    'value': { 'param': { 'type': 'string', 'regex': '.{1,500}' } }
                                },
                                'review': {
                                    'order': 2, 
                                    'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                                    'value': { 'param': { 'type': 'string', 'maxLength': 200000 } },
                                    'presentation': { 'markdown': True }
                                },
                                'rating': {
                                    'order': 3,
                                    'value': { 
                                        'param': { 
                                            'type': 'string',  
                                            'enum': [
                                                '10: Top 5% of accepted papers, seminal paper',
                                                '9: Top 15% of accepted papers, strong accept',
                                                '8: Top 50% of accepted papers, clear accept',
                                                '7: Good paper, accept',
                                                '6: Marginally above acceptance threshold',
                                                '5: Marginally below acceptance threshold',
                                                '4: Ok but not good enough - rejection',
                                                '3: Clear rejection',
                                                '2: Strong rejection',
                                                '1: Trivial or wrong'
                                            ]
                                        } 
                                    },
                                    'presentation': { 'input': 'select' }
                                },
                                'confidence': {
                                    'order': 4,
                                    'value': { 
                                        'param': { 
                                            'type': 'string',  
                                            'enum': [
                                                '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature',
                                                '4: The reviewer is confident but not absolutely certain that the evaluation is correct',
                                                '3: The reviewer is fairly confident that the evaluation is correct',
                                                '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper',
                                                '1: The reviewer\'s evaluation is an educated guess'
                                            ]
                                        } 
                                    },
                                    'presentation': { 'input': 'radio' }
                                }                          
                            }                    
                        }                   
                    }                
                }          
            }
        }
    }
}




submission_release_template = {
    'id': 'OpenReview.net/Support/-/Submission_Release_Template', ## template should be part of the name?
    'invitees': ['active_venues'], ## how to give access to the PCs only from all the venues
    'readers': ['everyone'],
    'writers': ['OpenReview.net'],
    'signatures': ['OpenReview.net'],
    'edit': {
        'readers': ['OpenReview.net/Support', '${content.venueid.value}'],
        'writers': ['OpenReview.net/Support', '${content.venueid.value}'],
        'signatures': ['${content.venueid.value}'],
        'params': {
            'venueid': { 'type': 'group' }, ## any other validation? can we use any group id as venueid?
            'name': { 'type': 'string', 'default': 'Submission_Release'},
            'submission_name': { 'type': 'string'},
            'cdate': { 'type': 'date', 'range': [ 0, 9999999999999 ] }       
        },
        'invitation': {
            'id': '${../content.venueid.value}/-/${../content.name.value}',
            'signatures': ['${../content.venueid.value}'],
            'readers': ['everyone'],
            'writers': ['${signatures}'],
            'invitees': ['${../content.venueid.value}'],
            'cdate': { '${../params.cdate}' },
            'dateprocesses': [{
                'dates': ['#{cdate}'],
                'script': '''
def process(client, invitation):
    submissions = client.get_notes(invitation='${../../content.venueid.value}/-/${../../params.submission_name}')
    ## Set submissions to be under review
    for submission in submissions:
        client.post_invitation_edit({
            invitation: '${../../content.venueid.value}/-/${../../content.name.value}',
            note: {
                id: submission.id
            }
        })
    '''
            }], 
            'edit': {
                'signatures': ['${../..content.venueid.value}'],
                'readers': ['${../../content.venueid.value}', '${../../content.venueid.value}/${../../content.name.value}\\${note.number}/Authors'], ## note.number needs to be escaped. It is defined at note creation
                'writers': ['${../..content.venueid.value}'],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': '${../../../../../content.venueid.value}/-/${../../../../../params.submission_name}'
                        }
                    },
                    'readers': ['everyone'],  ## parametrize readers of have a template per readers combination?
                    'content': {
                        'venue': {
                            'value': 'Under Review for ${../../../../content.venueid.value}'
                        },
                        'venueid': {
                            'value': '${../../../../content.venueid.value}/Under_Review'
                        }                                                                                             
                    }               
                }       
            }
        }    
    }
}
