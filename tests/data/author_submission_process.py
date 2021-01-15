def process(client, edit, invitation):
    venue_id='.TMLR'
    note=edit.note

    paper_group=client.post_group(openreview.Group(id=f'{venue_id}/Paper{note.number}',
        readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        signatories=[venue_id]
    ))

    authors_group_id=f'{paper_group.id}/Authors'
    authors_group=client.post_group(openreview.Group(id=authors_group_id,
        readers=[venue_id, authors_group_id],
        writers=[venue_id],
        signatures=[venue_id],
        signatories=[venue_id, authors_group_id],
        members=note.content['authorids']['value']
    ))

    action_editors_group_id=f'{paper_group.id}/AEs'
    action_editors_group=client.post_group(openreview.Group(id=action_editors_group_id,
        readers=[venue_id, action_editors_group_id],
        nonreaders=[authors_group_id],
        writers=[venue_id],
        signatures=[venue_id],
        signatories=[venue_id, action_editors_group_id],
        members=[]
    ))

    reviewers_group_id=f'{paper_group.id}/Reviewers'
    reviewers_group=client.post_group(openreview.Group(id=reviewers_group_id,
        readers=[venue_id, action_editors_group_id],
        nonreaders=[authors_group_id],
        writers=[venue_id, action_editors_group_id],
        signatures=[venue_id],
        signatories=[venue_id],
        members=[]
    ))

    ## TODO: create this invitation using an invitation
    review_invitation_id=f'{paper_group.id}/-/Review'

    process_function='''def process(client, edit, invitation):
    venue_id='.TMLR'
    note=edit.note

    ## TODO: send message to the reviewer, AE confirming the review was posted

    review_note=client.get_note(note.id)
    if review_note.readers == ['everyone']:
        return

    paper_number=client.get_note(note.forum).number
    reviews=client.get_notes(forum=note.forum, invitation=edit.invitation)
    if len(reviews) == 3:
        invitation = client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=openreview.Invitation(id=edit.invitation,
                signatures=[venue_id],
                edit={
                    'signatures': { 'values': [ '${{note.id}.signatures}' ] },
                    'readers': { 'values': [venue_id, f'.TMLR/Paper{paper_number}/AEs', '${{note.id}.signatures}'] },
                    'note': {
                        'readers': { 'values': ['everyone'] }
                    }
                }
            )
        )
    '''

    invitation = client.post_invitation_edit(readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=openreview.Invitation(id=review_invitation_id,
            invitees=[venue_id, f"{paper_group.id}/Reviewers", f'{paper_group.id}/AEs'],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values-regex': f'{paper_group.id}/AnonReviewer.*|{paper_group.id}/AEs' },
                'readers': { 'values': [ venue_id, f'{paper_group.id}/AEs', '${signatures}'] },
                'writers': { 'values': [ venue_id, f'{paper_group.id}/AEs', '${signatures}'] },
                'note': {
                    'forum': { 'value': note.id },
                    'replyto': { 'value': note.id },
                    'signatures': { 'values': ['${signatures}'] },
                    'readers': { 'values': [ venue_id, f'{paper_group.id}/AEs', '${signatures}'] },
                    'writers': { 'values': [ venue_id, f'{paper_group.id}/AEs', '${signatures}'] },
                    'content': {
                        'title': {
                            'value': {
                                'order': 1,
                                'value-regex': '.{0,500}',
                                'description': 'Brief summary of your review.',
                                'required': True
                            }
                        },
                        'review': {
                            'value': {
                                'order': 2,
                                'value-regex': '[\\S\\s]{1,200000}',
                                'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                                'required': True,
                                'markdown': True
                            }
                        },
                        'suggested_changes': {
                            'value': {
                                'order': 2,
                                'value-regex': '[\\S\\s]{1,200000}',
                                'description': 'List of suggested revisions to support acceptance (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                                'required': True,
                                'markdown': True
                            }
                        },
                        'recommendation': {
                            'value': {
                                'order': 3,
                                'value-radio': [
                                    'Accept',
                                    'Reject'
                                ],
                                'required': True
                            }
                        },
                        'confidence': {
                            'value': {
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
                        },
                        'certification_recommendation': {
                            'value': {
                                'order': 5,
                                'value-radio': [
                                    'Featured article',
                                    'Outstanding article'
                                ],
                                'required': False
                            },
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/AEs', '${signatures}']
                            }
                        },
                        'certification_confidence': {
                            'value': {
                                'order': 6,
                                'value-radio': [
                                    '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature',
                                    '4: The reviewer is confident but not absolutely certain that the evaluation is correct',
                                    '3: The reviewer is fairly confident that the evaluation is correct',
                                    '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper',
                                    '1: The reviewer\'s evaluation is an educated guess'
                                ],
                                'required': False
                            },
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/AEs', '${signatures}']
                            }
                        }
                    }
                }
            },
            process_string=process_function
    ))

    # revision_invitation_id=f'{paper_group.id}/-/Revision'
    # invitation = client.post_invitation_edit(readers=[venue_id],
    #     writers=[venue_id],
    #     signatures=[venue_id],
    #     invitation=openreview.Invitation(id=revision_invitation_id,
    #         invitees=[f"{paper_group.id}/Authors"],
    #         readers=['everyone'],
    #         writers=[venue_id],
    #         signatures=[venue_id],
    #         reply={
    #             'referent': { 'value': note.id },
    #             'signatures': { 'values': [f'{paper_group.id}/Authors'] },
    #             'readers': { 'values': [ venue_id, '${signatures}', f'{paper_group.id}/AEs', f'{paper_group.id}/Authors']},
    #             'writers': { 'values': [ venue_id, '${signatures}', f'{paper_group.id}/Authors']},
    #             'note': {
    #                 'forum': { 'value': note.id },
    #                 'content': {
    #                     'title': {
    #                         'value': {
    #                             'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
    #                             'order': 1,
    #                             'value-regex': '.{1,250}',
    #                             'required':False
    #                         }
    #                     },
    #                     'abstract': {
    #                         'value': {
    #                             'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
    #                             'order': 4,
    #                             'value-regex': '[\\S\\s]{1,5000}',
    #                             'required':False
    #                         }
    #                     },
    #                     'authors': {
    #                         'value': {
    #                             'description': 'Comma separated list of author names.',
    #                             'order': 2,
    #                             'values-regex': '[^;,\\n]+(,[^,\\n]+)*',
    #                             'required':False,
    #                             'hidden': True
    #                         },
    #                         'readers': {
    #                             'values': [ venue_id, '${signatures}', f'{paper_group.id}/Authors']
    #                         }
    #                     },
    #                     'authorids': {
    #                         'value': {
    #                             'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
    #                             'order': 3,
    #                             'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
    #                             'required':False
    #                         },
    #                         'readers': {
    #                             'values': [ venue_id, '${signatures}', f'{paper_group.id}/Authors']
    #                         }
    #                     },
    #                     'pdf': {
    #                         'value': {
    #                             'description': 'Upload a PDF file that ends with .pdf',
    #                             'order': 5,
    #                             'value-file': {
    #                                 'fileTypes': ['pdf'],
    #                                 'size': 50
    #                             },
    #                             'required':False
    #                         }
    #                     },
    #                     "supplementary_material": {
    #                         'value': {
    #                             "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
    #                             "order": 6,
    #                             "value-file": {
    #                                 "fileTypes": [
    #                                     "zip",
    #                                     "pdf"
    #                                 ],
    #                                 "size": 100
    #                             },
    #                             "required": False
    #                         },
    #                         'readers': {
    #                             'values': [ venue_id, '${signatures}', f'{paper_group.id}/AEs', f'{paper_group.id}/Reviewers', f'{paper_group.id}/Authors' ]
    #                         }
    #                     }
    #                 }
    #             }
    #         }))

    comment_invitation_id=f'{paper_group.id}/-/Comment'
    invitation = client.post_invitation_edit(readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=openreview.Invitation(id=comment_invitation_id,
            invitees=['everyone'],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values-regex': '~.*' },
                'readers': { 'values': [ venue_id, f'{paper_group.id}/AEs', '${signatures}']},
                'writers': { 'values': [ venue_id, f'{paper_group.id}/AEs', '${signatures}']},
                'note': {
                    'forum': { 'value': note.id },
                    'signatures': { 'values': ['${signatures}'] },
                    'readers': { 'values': [ 'everyone']},
                    'writers': { 'values': [ venue_id, f'{paper_group.id}/AEs', '${signatures}']},
                    'content': {
                        'title': {
                            'value': {
                                'order': 0,
                                'value-regex': '.{1,500}',
                                'description': 'Brief summary of your comment.',
                                'required': True
                            }
                        },
                        'comment': {
                            'value': {
                                'order': 1,
                                'value-regex': '[\\S\\s]{1,5000}',
                                'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                                'required': True,
                                'markdown': True
                            }
                        }
                    }
                }
            }))

    moderate_invitation_id=f'{paper_group.id}/-/Moderate'
    invitation = client.post_invitation_edit(readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=openreview.Invitation(id=moderate_invitation_id,
            invitees=[venue_id, f'{paper_group.id}/AEs'],
            readers=[venue_id, f'{paper_group.id}/AEs'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'forum': note.id,
                'signatures': { 'values-regex': f'{paper_group.id}/AEs|{venue_id}$' },
                'readers': { 'values': [ venue_id, f'{paper_group.id}/AEs']},
                'writers': { 'values': [ venue_id, f'{paper_group.id}/AEs']},
                'note': {
                    'id': { 'value-invitation': comment_invitation_id },
                    'readers': {
                        'values': ['everyone']
                    },
                    'writers': {
                        'values': [venue_id, f'{paper_group.id}/AEs']
                    },
                    'signatures': { 'values-regex': '~.*' },
                    'content': {
                        'title': {
                            'value': {
                                'order': 0,
                                'value-regex': '.{1,500}',
                                'description': 'Brief summary of your comment.',
                                'required': True
                            },
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/AEs', '${signatures}']
                            }
                        },
                        'comment': {
                            'value': {
                                'order': 1,
                                'value-regex': '[\\S\\s]{1,5000}',
                                'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                                'required': True,
                                'markdown': True
                            },
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/AEs', '${signatures}']
                            }
                        }
                    }
                }
            }
        )
    )


