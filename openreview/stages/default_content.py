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

comment_v2 = {
    'title': {
        'order': 1,
        'description': '(Optional) Brief summary of your comment.',
        'value': {
            'param': {
                'type': 'string',
                'maxLength': 500,
                'optional': True,
                'deletable': True
            }
        }
    },
    'comment': {
        'order': 2,
        'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
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

desk_reject_v2 = {
    'title': {
        'order': 1,
        'description': 'Title',
        'value': {
            'param': {
                'type': 'string',
                'const': 'Submission Desk Rejected by Program Chairs'
            }
        }
    },
    'desk_reject_comments': {
        'order': 2,
        'description': 'Brief summary of reasons for marking this submission as desk rejected',
        'value': {
            'param': {
                'type': 'string',
                'maxLength': 10000,
                'input': 'textarea'
            }
        }
    }
}

desk_reject_reversion_v2 = {
    'revert_desk_rejection_confirmation': {
        'value': {
            'param': {
                'type': 'string',
                'enum': [
                    'We approve the reversion of desk-rejected submission.'
                ],
                'input': 'checkbox'
            }
        },
        'description': 'Please confirm to revert the desk-rejection.',
        'order': 1
    },
    'comment': {
        'order': 2,
        'description': 'Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
        'value': {
            'param': {
                'type': 'string',
                'maxLength': 200000,
                'input': 'textarea',
                'optional': True,
                'deletable': True,
                'markdown': True
            }
        }
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
                'type': 'integer',
                'enum': [
                    { 'value': 10, 'description': '10: Top 5% of accepted papers, seminal paper' },
                    { 'value': 9, 'description': '9: Top 15% of accepted papers, strong accept' },
                    { 'value': 8, 'description': '8: Top 50% of accepted papers, clear accept' },
                    { 'value': 7, 'description': '7: Good paper, accept' },
                    { 'value': 6, 'description': '6: Marginally above acceptance threshold' },
                    { 'value': 5, 'description': '5: Marginally below acceptance threshold' },
                    { 'value': 4, 'description': '4: Ok but not good enough - rejection' },
                    { 'value': 3, 'description': '3: Clear rejection' },
                    { 'value': 2, 'description': '2: Strong rejection' },
                    { 'value': 1, 'description': '1: Trivial or wrong' }
                ],
                'input': 'radio'
            }
        }
    },
    'confidence': {
        'order': 4,
        'value': {
            'param': {
                'type': 'integer',
                'enum': [
                    { 'value': 5, 'description': '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature' },
                    { 'value': 4, 'description': '4: The reviewer is confident but not absolutely certain that the evaluation is correct' },
                    { 'value': 3, 'description': '3: The reviewer is fairly confident that the evaluation is correct' },
                    { 'value': 2, 'description': '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper' },
                    { 'value': 1, 'description': '1: The reviewer\'s evaluation is an educated guess' }
                ],
                'input': 'radio'
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

ethics_review_v2 = {
    "recommendation": {
        'order': 1,
        'value': {
            'param': {
                'type': 'string',
                'input': 'radio',
                'enum': [
                    "1: No serious ethical issues",
                    "2: Serious ethical issues that need to be addressed in the final version",
                    "3: Paper should be rejected due to ethical issues"
                ]
            }
        }
    },
    "ethics_review": {
        'order': 2,
        'description': 'Provide justification for your suggested ethics issues. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq.',
        'value': {
            'param': {
                'type': 'string',
                'maxLength': 200000,
                'markdown': True,
                'input': 'textarea',
                'optional': True,
                'deletable': True
            }
        }
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

meta_review_v2 = {
    'metareview': {
        'order': 1,
        'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons. Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
        'value': {
            'param': {
                'type': 'string',
                'maxLength': 5000,
                'markdown': True,
                'input': 'textarea'
            }
        }
    },
    'recommendation': {
        'order': 2,
        'value': {
            'param': {
                'type': 'string',
                'enum': [
                    'Accept (Oral)',
                    'Accept (Poster)',
                    'Reject'
                ],
                'input': 'radio'
            }
        }
    },
    'confidence': {
        'order': 3,
        'value': {
            'param': {
                'type': 'integer',
                'enum': [
                    { 'value': 5, 'description': '5: The area chair is absolutely certain' },
                    { 'value': 4, 'description': '4: The area chair is confident but not absolutely certain' },
                    { 'value': 3, 'description': '3: The area chair is somewhat confident' },
                    { 'value': 2, 'description': '2: The area chair is not sure' },
                    { 'value': 1, 'description': '1: The area chair\'s evaluation is an educated guess' }
                ],
                'input': 'radio'                
            }
        }
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
        'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author by completing first, middle, and last names as well as author email address.',
        'value': {
            'param': {
                'type': 'profile[]',
                'regex': r"^~\S+$|^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
                'mismatchError': 'must be a valid email or profile ID'
            }
        }
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
                'deletable': True,
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

paper_recruitment_v2 = {
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
                'deletable': True,
                'input': 'textarea'
            }
        }
    },
    'submission_id': {
        'order': 6,
        'description': 'submission id',
        'value': {
            'param': {
                'type': 'string',
                'regex': '.*'
            }
        }
    },
    'inviter': {
        'order': 7,
        'description': 'inviter id',
        'value': {
            'param': {
                'type': 'string',
                'regex': '.*'
            }
        }
    }
}

decision_v2 = {
    'title': {
        'order': 1,
        'value': 'Paper Decision'
    },
    'decision': {
        'order': 2,
        'description': 'Decision',
        'value': {
            'param': {
                'type': 'string',
                'enum': [
                    'Accept (Oral)',
                    'Accept (Poster)',
                    'Reject'
                ],
                'input': 'radio'
            }
        }
    },
    'comment': {
        'order': 3,
        'value': {
            'param': {
                'type': 'string',
                'markdown': True,
                'input': 'textarea',
                'optional': True,
                'deletable': True
            }
        }
    }
}

rebuttal_v2 = {
    'rebuttal': {
        'order': 1,
        'description': 'Rebuttals can include Markdown formatting and LaTeX forumulas, for more information see https://openreview.net/faq , max length: 2500',
        'value': {
            'param': {
                'type': 'string',
                'maxLength': 2500,
                'markdown': True,
                'input': 'textarea'
            }
        }
    }
}