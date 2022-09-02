bid = {
    'tag': {
        'description': 'Bid description',
        'order': 1,
        'value-radio': [
            'Very High',
            'High',
            'Neutral',
            'Low',
            'Very Low',
            'No Bid'
        ],
        'required':True
    }
}

comment = {
    'title': {
        'order': 0,
        'value-regex': '.{1,500}',
        'description': 'Brief summary of your comment.',
        'required': True
    },
    'comment': {
        'order': 1,
        'value-regex': '[\\S\\s]{1,5000}',
        'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
        'required': True,
        'markdown': True
    }
}

withdraw = {
    'title': {
        'value': 'Submission Withdrawn by the Authors',
        'order': 1
    },
    'withdrawal confirmation': {
        'description': 'Please confirm to withdraw.',
        'value-radio': [
            'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.'
        ],
        'order': 2,
        'required': True
    }
}

desk_reject = {
    'title': {
        'value': 'Submission Desk Rejected by Program Chairs',
        'order': 1
    },
    'desk_reject_comments': {
        'description': 'Brief summary of reasons for marking this submission as desk rejected',
        'value-regex': '[\\S\\s]{1,10000}',
        'order': 2,
        'required': True
    }
}


review_rating = {
    "review_quality": {
        "description": "How helpful is this review:",
        "order": 1,
        "required": True,
        "value-radio": [
            "Poor - not very helpful",
            "Good",
            "Outstanding"
        ]
    }
}

review = {
    'title': {
        'order': 1,
        'value-regex': '.{0,500}',
        'description': 'Brief summary of your review.',
        'required': True
    },
    'review': {
        'order': 2,
        'value-regex': '[\\S\\s]{1,200000}',
        'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
        'required': True,
        'markdown': True
    },
    'rating': {
        'order': 3,
        'value-dropdown': [
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
        'required': True
    },
    'confidence': {
        'order': 4,
        'value-radio': [
            '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature',
            '4: The reviewer is confident but not absolutely certain that the evaluation is correct',
            '3: The reviewer is fairly confident that the evaluation is correct',
            '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper',
            '1: The reviewer\'s evaluation is an educated guess'
        ],
        'required': True
    }
}


review_v2 = {
    'title': {
        'order': 1,
        'description': 'Brief summary of your review.',
        'value': {
            'param': {
                'type': 'string',
                'regex': '.{0,500}',
            }
        }
    },
    'review': {
        'order': 2,
        'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
        'value': {
            'param': {
                'type': 'string',
                'maxLength': 200000,
                'markdown': True,
                'input': 'textarea'
            }
        }
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
        }
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
        }
    }
}

ethics_review = {
    "recommendation": {
        "order": 1,
        "value-radio": [
            "1: No serious ethical issues",
            "2: Serious ethical issues that need to be addressed in the final version",
            "3: Paper should be rejected due to ethical issues"
      ],
      "description": "Please select your ethical recommendation",
      "required": True
    },
    "ethics_review": {
      "order": 2,
      "value-regex": "[\\S\\s]{1,200000}",
      "description": "Provide justification for your suggested ethics issues. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.",
      "required": False,
      "markdown": True
    }
}

meta_review = {
    'metareview': {
        'order': 1,
        'value-regex': '[\\S\\s]{1,5000}',
        'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons. Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
        'required': True,
        'markdown': True
    },
    'recommendation': {
        'order': 2,
        'value-dropdown': [
            'Accept (Oral)',
            'Accept (Poster)',
            'Reject'
        ],
        'required': True
    },
    'confidence': {
        'order': 3,
        'value-radio': [
            '5: The area chair is absolutely certain',
            '4: The area chair is confident but not absolutely certain',
            '3: The area chair is somewhat confident',
            '2: The area chair is not sure',
            '1: The area chair\'s evaluation is an educated guess'
        ],
        'required': True
    }
}

submission = {
    'title': {
        'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
        'order': 1,
        'value-regex': '(?!^ +$)^.{1,250}$',
        'required':True
    },
    'authors': {
        'description': 'Comma separated list of author names.',
        'order': 2,
        'values-regex': '[^;,\\n]+(,[^,\\n]+)*',
        'required':True,
        'hidden': True,
    },
    'authorids': {
        'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author by completing first, middle, and last names as well as author email address.',
        'order': 3,
        'values-regex': r'^~\S+$|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
        'required':True
    },
    'keywords': {
        'description': 'Comma separated list of keywords.',
        'order': 6,
        'values-regex': '(^$)|[^;,\\n]+(,[^,\\n]+)*'
    },
    'TL;DR': {
        'description': '\"Too Long; Didn\'t Read\": a short sentence describing your paper',
        'order': 7,
        'value-regex': '[^\\n]{0,250}',
        'required':False
    },
    'abstract': {
        'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
        'order': 8,
        'value-regex': '[\\S\\s]{1,5000}',
        'required':True
    },
    'pdf': {
        'description': 'Upload a PDF file that ends with .pdf',
        'order': 9,
        'value-file': {
            'fileTypes': ['pdf'],
            'size': 50
        },
        'required':True
    }
}

submission_v2 = {
    'title': {
        'order': 1,
        'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
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
        'description': 'Search author profile by first, middle and last name or email address. All authors must have an OpenReview profile.',
        'value': {
            'param': {
                'type': 'group[]',
                'regex': '~.*'
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
                'extensions': ['pdf']
            }
        }
    },
    "previous_submission_url": {
        'order': 6,
        'description': 'If a version of this submission was previously rejected, give the OpenReview link to the original submission (which must still be anonymous) and describe the changes below.',
        'value':{
            'param': {
                'type': 'string',
                'regex': 'https:\\/\\/openreview\\.net\\/forum\\?id=.*',
                'optional': True
            }
        }
    },
    'changes_since_last_submission': {
        'order': 7,
        'description': 'Describe changes since last submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
        'value': {
            'param': {
                'type': 'string',
                'maxLength': 5000,
                'optional': True,
                'markdown': True,
                'input': 'textarea'
            }
        }
    },
    "submission_length": {
        'order': 8,
        'description': 'Check if this is a regular length submission, i.e. the main content (all pages before references and appendices) is 12 pages or less. Note that the review process may take significantly longer for papers longer than 12 pages.',
        'value': {
            'param': {
                'type': 'string',
                'enum': [
                    'Regular submission (no more than 12 pages of main content)',
                    'Long submission (more than 12 pages of main content)'
                ],
                'input': 'radio'
            }
        }
    }
}

recruitment = {
    'title': {
        'description': '',
        'order': 1,
        'value': 'Recruit response',
        'required':True
    },
    'user': {
        'description': 'email address',
        'order': 2,
        'value-regex': '.*',
        'required':True
    },
    'key': {
        'description': 'Email key hash',
        'order': 3,
        'value-regex': '.{0,100}',
        'required':True
    },
    'response': {
        'description': 'Invitation response',
        'order': 4,
        'value-radio': ['Yes', 'No'],
        'required':True
    },
    'comment': {
        'order': 6,
        'value-regex': '[\\S\\s]{1,5000}',
        'description': '(Optionally) Leave a comment to the organizers of the venue.',
        'required': False,
        'markdown': False
    }
}

recruitment_v2 = {
    'title': {
        'order': 1,
        'description': 'Title',
        'value': { 
            'param': { 
                'type': 'string',
                'const': 'Recruit response'
            }
        }
    },
    'user': {
        'order': 2,
        'description': 'email address',
        'value': { 
            'param': { 
                'type': 'string',
                'regex': '.*'
            }
        }
    },
    'key': {
        'order': 3,
        'description': 'Email key hash',
        'value': { 
            'param': { 
                'type': 'string',
                'regex': '.{0,100}'
            }
        }
    },
    "response": {
        'order': 4,
        'description': 'Invitation response',
        'value': {
            'param': {
                'type': 'string',
                'enum': ['Yes', 'No'],
                'input': 'radio'
            }
        }
    },
    'comment': {
        'order': 5,
        'description': '(Optionally) Leave a comment to the organizers of the venue.',
        'value': {
            'param': {
                'type': 'string',
                'maxLength': 5000,
                'optional': True,
                'input': 'textarea'
            }
        }
    }
}

paper_recruitment = {
    'title': {
        'description': '',
        'order': 1,
        'value': 'Recruit response',
        'required':True
    },
    'user': {
        'description': 'email address',
        'order': 2,
        'value-regex': '.*',
        'required':True
    },
    'key': {
        'description': 'Email key hash',
        'order': 3,
        'value-regex': '.{0,100}',
        'required':True
    },
    'response': {
        'description': 'Invitation response',
        'order': 4,
        'value-radio': ['Yes', 'No'],
        'required':True
    },
    'comment': {
        'order': 5,
        'value-regex': '[\\S\\s]{1,5000}',
        'description': '(Optional) Write a comment that you want to share with the organizers.',
        'required': False,
        'markdown': False
    },
    'submission_id': {
        'description': 'submission id',
        'order': 6,
        'value-regex': '.*',
        'required':True
    },
    'inviter': {
        'description': 'inviter id',
        'order': 7,
        'value-regex': '.*',
        'required':True
    }
}
