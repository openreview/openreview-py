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
                        'description': 'Official Review name.', 
                        'optional': True,
                        'default': 'Official_Review'
                    }
                },
                'order': 2,
                'type': 'string'
            },
            'submission_name': { 
                'value': {
                    'param': {
                        'regex': '.*',
                        'description': 'Submission name.'
                    }
                },
                'order': 3,
                'type': 'string'
            },            
            'cdate': {
                'value': {
                    'param': { 
                        'range': [ 0, 9999999999999 ],
                        'description': 'Activation date.'
                    },
                },
                'order': 4,
                'type': 'date',
            },
            'duedate': {
                'value': {
                    'param': { 
                        'description': 'Submission due date.',
                        'range': [ 0, 9999999999999 ] 
                    },
                },
                'order': 5,
                'type': 'date'
            },     
        },
        'invitation': {
            'id': '${../content.venueid.value}/-/${../content.name.value}',
            'signatures': ['${../content.venueid.value}'],
            'readers': ['${signatures}'],
            'writers': ['${signatures}'],
            'invitees': ['${signatures}'],
            'cdate': { '${../content.cdate.value}' },
            'duedate': { '${../content.duedate.value}' },
            'dateprocesses': [{
                'dates': ['#{cdate}'],
                'script': '''
def process(client, invitation):
    submissions = client.get_notes(invitation='${../../content.venueid.value}/-/${../../content.submission_name.value}')
    ## Create review invitations for all the active submissions
    for submission in submissions:
        client.post_invitation_edit({
            invitation: '${../../content.venueid.value}/-/${../../content.name.value}',
            content: {
                noteId: { 'value': submission.id },
                noteNumber: { 'value': submission.number }
            }
        })
    '''
            }],        
            'edit': {
                'signatures': ['${../../content.venueid.value}'],
                'readers': ['${signatures}'],
                'writers': ['${signatures}'],
                'content': {
                    'noteId': {
                        'value': {
                           'type': 'note', 
                            'param': {
                                'withInvitation': '${../../content.venueid.value}/-/${../../content.submission_name.value}' 
                            }
                        }
                    }, ## any other validation? use withInvitation?
                    'noteNumber': { 
                        'type': 'integer',
                        'value': {
                            'param': {
                                ##???
                            },
                        }
                    },
                    'submissionGroupId': {
                        'value': '${../../content.venueid.value}/${../../content.submission_name.value}${noteNumber}' ## constant so I can use it in several places
                    }
                },                
                'invitation': {
                    'id': '${../../content.submissionGroupId.value}/-/${../../../content.name.value}',
                    'signatures': ['${../../../content.venueid.value}'],
                    'readers': ['everyone'], ## everyone or just the reviewers?
                    'writers': ['${signatures}'],
                    'invitees': ['${../../content.submissionGroupId.value}/Reviewers'], ## should we parametrize the role names?
                    'cdate': { '${../../../content.cdate.value}' },
                    'duedate': { '${../../../content.duedate.value}' },
                    'process': '''
def process(client, edit, invitation):
    ## send confirmation email to the reviewer
    ## add the reviewer to the submitted group (?)
                    ''',
                    'edit': {
                        'signatures': { 'param': { 'regex': '${../../../content.submissionGroupId.value}/Reviewer_' }},
                        'readers': ['${../../../../content.venueid.value}', '${signatures}'], 
                        'writers': ['${../../../../content.venueid.value}'],
                        'note': {
                            'id': {
                                'param': {
                                    'withInvitation': '${../../../../id}', ## can I reference the invitation id of the edit
                                    'optional': True
                                }
                            },
                            'forum': '${../../content.noteId.value}',
                            'replyto': '${../../content.noteId.value}',
                            'signatures': ['${../signatures}'], ## how to resolve this in the UI?
                            'readers': ['${../../../../../content.venueid.value}', '${signatures}'],
                            'writers': ['${../../../../../content.venueid.value}', '${signatures}'], ## only visible to the submitted reviewer, should we create another template if we want to have public reviews?
                            'content': {
                                'title': {
                                    'order': 1, ## we store this value in the invitation edit but we don't store it in the note, should we assume that only 'value' and 'readers' will be saved in the note content?
                                    'type': 'string', 
                                    'value': { 
                                        'param': { 
                                            'description': 'Brief summary of your review.', ## Same here.
                                            'regex': '.{1,500}' 
                                        } 
                                    }
                                },
                                'review': {
                                    'order': 2, 
                                    'type': 'string',
                                    'value': { 
                                        'param': { 
                                            'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                                            'maxLength': 200000,
                                            'markdown': True 
                                        }
                                    }
                                },
                                'rating': {
                                    'order': 3,
                                    'type': 'string',  
                                    'value': { 
                                        'param': { 
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
                                            ],
                                            'input': 'select'
                                        } 
                                    }
                                },
                                'confidence': {
                                    'order': 4,
                                    'type': 'string',  
                                    'value': { 
                                        'param': { 
                                            'enum': [
                                                '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature',
                                                '4: The reviewer is confident but not absolutely certain that the evaluation is correct',
                                                '3: The reviewer is fairly confident that the evaluation is correct',
                                                '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper',
                                                '1: The reviewer\'s evaluation is an educated guess'
                                            ],
                                            'input': 'radio'
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
                        'description': 'Official Review name.', 
                        'optional': True,
                        'default': 'Official_Review'
                    }
                },
                'order': 2,
                'type': 'string'
            },
            'submission_name': { 
                'value': {
                    'param': {
                        'regex': '.*',
                        'description': 'Submission name.'
                    }
                },
                'order': 3,
                'type': 'string'
            },            
            'cdate': {
                'value': {
                    'param': { 
                        'range': [ 0, 9999999999999 ],
                        'description': 'Activation date.'
                    },
                },
                'order': 4,
                'type': 'date',
            }      
        },
        'invitation': {
            'id': '${../content.venueid.value}/-/${../content.name.value}',
            'signatures': ['${../content.venueid.value}'],
            'readers': ['everyone'],
            'writers': ['${signatures}'],
            'invitees': ['${../content.venueid.value}'],
            'cdate': { '${../content.cdate.value}' },
            'dateprocesses': [{
                'dates': ['#{cdate}'],
                'script': '''
def process(client, invitation):
    submissions = client.get_notes(invitation='${../../content.venueid.value}/-/${../../content.submission_name.value}')
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
                            'withInvitation': '${../../../../../content.venueid.value}/-/${../../../../../content.submission_name.value}'
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
