submission_template = {
    'id': 'OpenReview.net/Support/-/Submission_Template', ## template should be part of the name?
    'invitees': ['active_venues'], ## how to give access to the PCs only from all the venues
    'readers': ['everyone'],
    'writers': ['OpenReview.net'],
    'signatures': ['OpenReview.net'],
    'params': {
        'venueid': { 'type': 'group' }, ## any other validation? can we use any group id as venueid?
        'name': { 'type': 'string', 'default': 'Submission'},
        'cdate': { 'type': 'date', 'range': [ 0, 9999999999999 ] },
        'duedate': { 'type': 'date', 'range': [ 0, 9999999999999 ] }       
    },
    'invitation': {
        'id': '${..params.venueid}/-/${..params.name}',
        'signatures': ['${..params.venueid}'],
        'readers': ['everyone'],
        'writers': ['${signatures}'],
        'invitees': ['~'],
        'cdate': { '${..params.cdate}' },
        'duedate': { '${..params.duedate}' },
        'process': '''
def process(client, edit, invitation):
    ## 1. Create paper group: submission_group_id = f'${...params.venueid}/${...params.name}{edit.note.number}' ## Example: TMLR/Submission1
    ## 2. Create author paper author_submission_group_id = f'{submission_group_id}/Authors' ## Example: TMLR/Submission1/Authors
    ## 3. Add authorids as members of the group
    ## 4. Send confirmation email to the author group
''',
        'edit': {
            'signatures': { 'regex': '~.*', 'type': 'group' }},
            'readers': ['${...params.venueid}', '${...params.venueid}/${...params.name}\\${note.number}/Authors'], ## note.number needs to be escaped. It is defined at note creation
            'writers': ['${...params.venueid}'],
            'note': {
                'id': {
                    'param': {
                        'withInvitation': '${edit.invitation}', ## can I reference the invitation id of the edit
                        'optional': True
                    }
                },
                'signatures': ['${....params.venueid}/${....params.name}\\${note.number}/Authors'],
                'readers': ['${....params.venueid}', '${....params.venueid}/${....params.name}\\${note.number}/Authors'],
                'writers': ['${....params.venueid}', '${....params.venueid}/${....params.name}\\${note.number}/Authors'],
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
                        'value': { 'param': { 'type': 'string[]', 'regex': '[^;,\\n]+(,[^,\\n]+)*' } }
                    },
                    'authorids': {
                        'order': 3,
                        'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                        'value': { 'param': { 'type': 'group[]', 'regex': r'~.*' } }
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