submission_template = {
    'id': 'OpenReview.net/Support/-/Submission_Template', ## template should be part of the name?
    'invitees': ['active_venues'], ## how to give access to the PCs only from all the venues
    'readers': ['everyone'],
    'writers': ['OpenReview.net/Support'],
    'signatures': ['OpenReview.net/Support'],
    'edit': {
        'readers': ['OpenReview.net/Support', '${params.venueid}'],
        'writers': ['OpenReview.net/Support', '${params.venueid}'],
        'signatures': ['${params.venueid}'],
        'params': {
            'venueid': { 'type': 'group' }, ## any other validation? can we use any group id as venueid?
            'name': { 'type': 'string', 'default': 'Submission'},
            'cdate': { 'type': 'date', 'range': [ 0, 9999999999999 ] },
            'duedate': { 'type': 'date', 'range': [ 0, 9999999999999 ] }       
        },
        'invitation': {
            'id': '${../params.venueid}/-/${../params.name}',
            'signatures': ['${../params.venueid}'],
            'readers': ['everyone'],
            'writers': ['${signatures}'],
            'invitees': ['~'],
            'cdate': { '${../params.cdate}' },
            'duedate': { '${../params.duedate}' },
            'process': '''
    def process(client, edit, invitation):
        ## 1. Create paper group: submission_group_id = f'${../params.venueid}/${../params.name}{edit.note.number}' ## Example: TMLR/Submission1
        ## 2. Create author paper author_submission_group_id = f'{submission_group_id}/Authors' ## Example: TMLR/Submission1/Authors
        ## 3. Add authorids as members of the group
        ## 4. Send confirmation email to the author group
    ''',
            'edit': {
                'signatures': { 'param': { 'regex': '~.*', 'type': 'group' }},
                'readers': ['${../../params.venueid}', '${../../params.venueid}/${../../params.name}\\${note.number}/Authors'], ## note.number needs to be escaped. It is defined at note creation
                'writers': ['${../..params.venueid}'],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': '${edit.invitation}', ## can I reference the invitation id of the edit
                            'optional': True
                        }
                    },
                    'signatures': ['${../../../params.venueid}/${../../../params.name}\\${note.number}/Authors'],
                    'readers': ['${../../../params.venueid}', '${../../../params.venueid}/${../../../params.name}\\${note.number}/Authors'],
                    'writers': ['${../../../params.venueid}', '${../../../params.venueid}/${../../../params.name}\\${note.number}/Authors'],
                    'content': {
                        'title': {
                            'order': 1, ## we store this value in the invitation edit but we don't store it in the note, should we assume that only 'value' and 'readers' will be saved in the note content?
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$', ## Same here.
                            'value': { 'param': { 'type': 'string', 'regex': '.{1,250}' } }
                        },
                        'authors': {
                            'order': 2,
                            'description': 'Comma separated list of author names.',
                            'presentation': {
                                'hidden': True
                            },
                            'value': { 'param': { 'type': 'string[]', 'regex': '[^;,\\n]+(,[^,\\n]+)*' } },
                            'readers': [ '${../../../../params.venueid}', '${../../../../params.venueid}/${../../../../.params.name}\\${note.number}/Authors']
                        },
                        'authorids': {
                            'order': 3,
                            'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                            'value': { 'param': { 'type': 'group[]', 'regex': r'~.*' } },
                            'readers': [ '${../../../../params.venueid}', '${../../../../params.venueid}/${../../../../params.name}\\${note.number}/Authors']
                        },
                        'keywords': {
                            'order': 4,
                            'description': 'Comma separated list of keywords',
                            'value': { 'param': { 'type': 'string[]', 'regex': '(^$)|[^;,\\n]+(,[^,\\n]+)*' }}
                        },
                        'abstract': {
                            'order': 5,
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
                            'value': { 'param': { 'type': 'string', 'regex': '^[\\S\\s]{1,5000}$', 'maxLength': 5000 }},
                            'presentation': { 'markdown': True }
                        },
                        'TL;DR': {
                            'order': 6,
                            'description': '\"Too Long; Didn\'t Read\": a short sentence describing your paper',
                            'value': { 'param': { 'type': 'string', 'regex': '^[\\S\\s]{1,500}$', 'maxLength': 500 }},
                        },
                        'pdf': {
                            'order': 7,
                            'description': 'Upload a PDF file that ends with .pdf.',
                            'value': {
                                'param': {
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
        'readers': ['OpenReview.net/Support', '${params.venueid}'],
        'writers': ['OpenReview.net/Support', '${params.venueid}'],
        'signatures': ['${params.venueid}'],        
        'params': {
            'venueid': { 'type': 'group' }, ## any other validation? can we use any group id as venueid?
            'name': { 'type': 'string', 'default': 'Official_Review'},
            'submission_name': { 'type': 'string'}, ## need to know the submission name to validate and create the paper groups
            'cdate': { 'type': 'date', 'range': [ 0, 9999999999999 ] },
            'duedate': { 'type': 'date', 'range': [ 0, 9999999999999 ] }       
        },
        'invitation': {
            'id': '${../params.venueid}/-/${../params.name}',
            'signatures': ['${../params.venueid}'],
            'readers': ['${signatures}'],
            'writers': ['${signatures}'],
            'invitees': ['${signatures}'],
            'cdate': { '${../params.cdate}' },
            'duedate': { '${../params.duedate}' },
            'dateprocesses': [{
                'dates': ['#{cdate}'],
                'script': '''
    def process(client, invitation):
        submissions = client.get_notes(invitation='${../../params.venueid}/-/${../../params.submission_name}')
        ## Create review invitations for all the active submissions
        for submission in submissions:
            client.post_invitation_edit({
                invitation: '${../../params.venueid}/-/${../../params.name}',
                params: {
                    noteId: submission.id,
                    noteNumber: submission.number
                }
            })
    '''
            }],        
            'edit': {
                'signatures': ['${../../params.venueid}'],
                'readers': ['${signatures}'],
                'writers': ['${signatures}'],
                'params': {
                    'noteId': { 'type': 'note', 'withInvitation': '${../../params.venueid}/-/${../../params.submission_name}' }, ## any other validation? use withInvitation?
                    'noteNumber': { 'type': 'integer'},
                    'submissionGroupId': '${../../params.venueid}/${../../params.submission_name}${noteNumber}' ## constant so I can use it in several places
                },                
                'invitation': {
                    'id': '${../../params.submissionGroupId}/-/${../../../params.name}',
                    'signatures': ['${../../../params.venueid}'],
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
                        'readers': ['${../../../../params.venueid}', '${signatures}'], 
                        'writers': ['${../../../../params.venueid}'],
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
                            'readers': ['${../../../../../params.venueid}', '${signatures}'],
                            'writers': ['${../../../../../params.venueid}', '${signatures}'], ## only visible to the submitted reviewer, should we create another template if we want to have public reviews?
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
        'readers': ['OpenReview.net/Support', '${params.venueid}'],
        'writers': ['OpenReview.net/Support', '${params.venueid}'],
        'signatures': ['${params.venueid}'],
        'params': {
            'venueid': { 'type': 'group' }, ## any other validation? can we use any group id as venueid?
            'name': { 'type': 'string', 'default': 'Submission_Release'},
            'submission_name': { 'type': 'string'},
            'cdate': { 'type': 'date', 'range': [ 0, 9999999999999 ] }       
        },
        'invitation': {
            'id': '${../params.venueid}/-/${../params.name}',
            'signatures': ['${../params.venueid}'],
            'readers': ['everyone'],
            'writers': ['${signatures}'],
            'invitees': ['${../params.venueid}'],
            'cdate': { '${../params.cdate}' },
            'dateprocesses': [{
                'dates': ['#{cdate}'],
                'script': '''
    def process(client, invitation):
        submissions = client.get_notes(invitation='${../../params.venueid}/-/${../../params.submission_name}')
        ## Set submissions to be under review
        for submission in submissions:
            client.post_invitation_edit({
                invitation: '${../../params.venueid}/-/${../../params.name}',
                note: {
                    id: submission.id
                }
            })
    '''
            }], 
            'edit': {
                'signatures': ['${../..params.venueid}'],
                'readers': ['${../../params.venueid}', '${../../params.venueid}/${../../params.name}\\${note.number}/Authors'], ## note.number needs to be escaped. It is defined at note creation
                'writers': ['${../..params.venueid}'],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': '${../../../../../params.venueid}/-/${../../../../../params.submission_name}'
                        }
                    },
                    'readers': ['everyone'],  ## parametrize readers of have a template per readers combination?
                    'content': {
                        'venue': {
                            'value': 'Under Review for ${../../../../params.venueid}'
                        },
                        'venueid': {
                            'value': '${../../../../params.venueid}/Under_Review'
                        }                                                                                             
                    }               
                }       
            }
        }    
    }
}