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
        'description': 'Your comment or reply (max 5000 characters).',
        'required': True
    }
}
review_rating = {
    'title': {
        'order': 1,
        'value': 'Review Rating',
        'required': True
    },
    'novelty': {
        'order': 2,
        'value-dropdown': ['Very High', 'High', 'Neutral', 'Low', 'Very Low'],
        'description': 'Indicate your agreement with the following: This paper is highly novel.',
        'required': True
    },
    'soundness': {
        'order': 2,
        'value-dropdown': ['Very High', 'High', 'Neutral', 'Low', 'Very Low'],
        'description': 'Indicate your agreement with the following: This paper is technically sound.',
        'required': True
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
        'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons (max 200000 characters).',
        'required': True
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

meta_review = {
    'title': {
        'order': 1,
        'value-regex': '.{1,500}',
        'description': 'Brief summary of your review.',
        'required': True
    },
    'metareview': {
        'order': 2,
        'value-regex': '[\\S\\s]{1,5000}',
        'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons.',
        'required': True
    },
    'recommendation': {
        'order': 3,
        'value-dropdown': [
            'Accept (Oral)',
            'Accept (Poster)',
            'Reject',
            'Invite to Workshop Track'
        ],
        'required': True
    },
    'confidence': {
        'order': 4,
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
        'description': 'Title of paper.',
        'order': 1,
        'value-regex': '.{1,250}',
        'required':True
    },
    'authors': {
        'description': 'Comma separated list of author names. Please provide real names; identities will be anonymized.',
        'order': 2,
        'values-regex': "[^;,\\n]+(,[^,\\n]+)*",
        'required':True
    },
    'authorids': {
        'description': 'Comma separated list of author email addresses, lowercased, in the same order as above. For authors with existing OpenReview accounts, please make sure that the provided email address(es) match those listed in the author\'s profile. Please provide real emails; identities will be anonymized.',
        'order': 3,
        'values-regex': "([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{2,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})",
        'required':True
    },
    'keywords': {
        'description': 'Comma separated list of keywords.',
        'order': 6,
        'values-regex': "(^$)|[^;,\\n]+(,[^,\\n]+)*"
    },
    'TL;DR': {
        'description': '\"Too Long; Didn\'t Read\": a short sentence describing your paper',
        'order': 7,
        'value-regex': '[^\\n]{0,250}',
        'required':False
    },
    'abstract': {
        'description': 'Abstract of paper.',
        'order': 8,
        'value-regex': '[\\S\\s]{1,5000}',
        'required':True
    },
    'pdf': {
        'description': 'Upload a PDF file that ends with .pdf',
        'order': 9,
        'value-regex': 'upload',
        'required':True
    }
}

recruitment = {
    'email': {
        'description': 'email address',
        'order': 1,
        'value-regex': '.*@.*',
        'required':True
    },
    'key': {
        'description': 'Email key hash',
        'order': 2,
        'value-regex': '.{0,100}',
        'required':True
    },
    'response': {
        'description': 'Invitation response',
        'order': 3,
        'value-radio': ['Yes', 'No'],
        'required':True
    }
}
