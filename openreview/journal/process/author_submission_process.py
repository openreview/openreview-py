def process(client, edit, invitation):
    venue_id='.TMLR'
    note=client.get_note(edit.note.id)

    paper_group_id=f'{venue_id}/Paper{note.number}'
    paper_group=openreview.tools.get_group(client, paper_group_id)
    if not paper_group:
        paper_group=client.post_group(openreview.Group(id=paper_group_id,
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
        members=note.content['authorids']['value'] ## always update authors
    ))
    client.add_members_to_group(f'{venue_id}/Authors', authors_group_id)

    action_editors_group_id=f'{paper_group.id}/Action_Editors'
    reviewers_group_id=f'{paper_group.id}/Reviewers'

    action_editors_group=openreview.tools.get_group(client, action_editors_group_id)
    if not action_editors_group:
        action_editors_group=client.post_group(openreview.Group(id=action_editors_group_id,
            readers=[venue_id, action_editors_group_id, reviewers_group_id],
            nonreaders=[authors_group_id],
            writers=[venue_id],
            signatures=[venue_id],
            signatories=[venue_id, action_editors_group_id],
            members=[]
        ))

    reviewers_group=openreview.tools.get_group(client, reviewers_group_id)
    if not reviewers_group:
        reviewers_group=client.post_group(openreview.Group(id=reviewers_group_id,
            readers=[venue_id, action_editors_group_id, reviewers_group_id],
            deanonymizers=[venue_id, action_editors_group_id],
            nonreaders=[authors_group_id],
            writers=[venue_id, action_editors_group_id],
            signatures=[venue_id],
            signatories=[venue_id],
            members=[],
            anonids=True
        ))

    ## TODO: create this invitation using an invitation
    review_invitation_id=f'{paper_group.id}/-/Review'
    review_invitation=openreview.tools.get_invitation(client, review_invitation_id)
    if review_invitation:
        ## invitations already exists, finish the process function
        return

    rating_process_function='''\'''def process(client, edit, invitation):
    venue_id='.TMLR'
    note=edit.note
    ## check all the ratings are done and enable the Decision invitation
    review=client.get_note(note.replyto)
    review_invitation=review.invitations[0]
    paper_group_id=review_invitation.split('/-/')[0]
    reviews=client.get_notes(invitation=review_invitation)
    ratings=client.get_notes(invitation=f'{paper_group_id}/Reviewer_.*/-/Rating')
    if len(reviews) == len(ratings):
        invitation = client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=f'{paper_group_id}/-/Decision',
                signatures=[venue_id],
                invitees=[venue_id, f'{paper_group_id}/Action_Editors']
            )
        )
    \'''
    '''

    process_function='''def process(client, edit, invitation):
    venue_id='.TMLR'
    note=edit.note
    paper_group_id=edit.invitation.split('/-/')[0]

    ## TODO: send message to the reviewer, AE confirming the review was posted

    ## Create invitation to rate reviews
    signature=edit.signatures[0]
    if signature.startswith(f'{paper_group_id}/Reviewer_'):
        invitation = client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=f'{signature}/-/Rating',
                duedate=1613822400000, ## check duedate
                invitees=[f'{paper_group_id}/Action_Editors'],
                readers=[venue_id, f'{paper_group_id}/Action_Editors'],
                writers=[venue_id],
                signatures=[venue_id],
                maxReplies=1,
                edit={
                    'signatures': { 'values': [f'{paper_group_id}/Action_Editors'] },
                    'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors'] },
                    'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors'] },
                    'note': {
                        'forum': { 'value': note.forum },
                        'replyto': { 'value': note.id },
                        'signatures': { 'values': [f'{paper_group_id}/Action_Editors'] },
                        'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors'] },
                        'writers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors'] },
                        'content': {
                            'rating': {
                                'order': 1,
                                'value': {
                                    'value-radio': [
                                        "Poor - not very helpful",
                                        "Good",
                                        "Outstanding"
                                    ]
                                }
                            }
                        }
                    }
                },
                process_string=''' + rating_process_function + '''
        ))


    review_note=client.get_note(note.id)
    if review_note.readers == ['everyone']:
        return

    reviews=client.get_notes(forum=note.forum, invitation=edit.invitation)
    if len(reviews) == 3:
        # invitation = client.post_invitation_edit(readers=[venue_id],
        #     writers=[venue_id],
        #     signatures=[venue_id],
        #     invitation=Invitation(id=edit.invitation,
        #         signatures=[venue_id],
        #         edit={
        #             'signatures': { 'values': [ '${{note.id}.signatures}' ] },
        #             'readers': { 'values': [venue_id, f'{paper_group_id}/Action_Editors', '${{note.id}.signatures}'] },
        #             'note': {
        #                 'readers': { 'values': ['everyone'] }
        #             }
        #         }
        #     )
        # )

        invitation = client.post_invitation_edit(readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=Invitation(id=f'{paper_group_id}/-/Release_Review',
                bulk=True,
                invitees=[venue_id],
                readers=['everyone'],
                writers=[venue_id],
                signatures=[venue_id],
                edit={
                    'signatures': { 'values': [venue_id ] },
                    'readers': { 'values': [ venue_id, f'{paper_group_id}/Action_Editors', '${{note.id}.signatures}' ] },
                    'writers': { 'values': [ venue_id ] },
                    'note': {
                        'id': { 'value-invitation': edit.invitation },
                        'readers': { 'values': [ 'everyone' ] }
                    }
                }
        ))
    '''

    invitation = client.post_invitation_edit(readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=Invitation(id=review_invitation_id,
            duedate=1613822400000,
            invitees=[venue_id, f"{paper_group.id}/Reviewers"],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            maxReplies=1,
            edit={
                'signatures': { 'values-regex': f'{paper_group.id}/Reviewer_.*|{paper_group.id}/Action_Editors' },
                'readers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}'] },
                'writers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}'] },
                'note': {
                    'id': {
                        'value-invitation': review_invitation_id,
                        'optional': True
                    },                    'forum': { 'value': note.id },
                    'replyto': { 'value': note.id },
                    'ddate': {
                        'int-range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'values': ['${signatures}'] },
                    'readers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}'] },
                    'writers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}'] },
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your review.',
                            'value': {
                                'value-regex': '.{0,500}'
                            }
                        },
                        'review': {
                            'order': 2,
                            'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                            'value': {
                                'value-regex': '[\\S\\s]{1,200000}'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'suggested_changes': {
                            'order': 2,
                            'description': 'List of suggested revisions to support acceptance (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                            'value': {
                                'value-regex': '[\\S\\s]{1,200000}'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        },
                        'recommendation': {
                            'order': 3,
                            'value': {
                                'value-radio': [
                                    'Accept',
                                    'Reject'
                                ]
                            }
                        },
                        'confidence': {
                            'order': 4,
                            'value': {
                                'value-radio': [
                                    '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature',
                                    '4: The reviewer is confident but not absolutely certain that the evaluation is correct',
                                    '3: The reviewer is fairly confident that the evaluation is correct',
                                    '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper',
                                    '1: The reviewer\'s evaluation is an educated guess'
                                ]
                            }
                        },
                        'certification_recommendation': {
                            'order': 5,
                            'value': {
                                'value-radio': [
                                    'Featured article',
                                    'Outstanding article'
                                ]
                            },
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}']
                            }
                        },
                        'certification_confidence': {
                            'order': 6,
                            'value': {
                                'value-radio': [
                                    '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature',
                                    '4: The reviewer is confident but not absolutely certain that the evaluation is correct',
                                    '3: The reviewer is fairly confident that the evaluation is correct',
                                    '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper',
                                    '1: The reviewer\'s evaluation is an educated guess'
                                ]
                            },
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}']
                            }
                        }
                    }
                }
            },
            process_string=process_function
    ))

    revision_process_function='''def process(client, edit, invitation):
    note=client.get_note(edit.note.id)
    paper_group_id=edit.invitation.split('/-/')[0]
    authors_group_id=f'{paper_group_id}/Authors'
    authors_group=openreview.tools.get_group(client, authors_group_id)
    if authors_group:
        authors_group.members=note.content['authorids']['value']
        client.post_group(authors_group)
    '''

    revision_invitation_id=f'{paper_group.id}/-/Revision'
    invitation = client.post_invitation_edit(readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=Invitation(id=revision_invitation_id,
            invitees=[f"{paper_group.id}/Authors"],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [f'{paper_group.id}/Authors'] },
                'readers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors', f'{paper_group.id}/Authors']},
                'writers': { 'values': [ venue_id, f'{paper_group.id}/Authors']},
                'note': {
                    'id': { 'value': note.id },
                    'content': {
                        'title': {
                            'value': {
                                'value-regex': '.{1,250}',
                                'optional': True
                            },
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                            'order': 1
                        },
                        'abstract': {
                            'value': {
                                'value-regex': '[\\S\\s]{1,5000}',
                                'optional': True
                            },
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                            'order': 2,
                        },
                        'authors': {
                            'value': {
                                'values-regex': '[^;,\\n]+(,[^,\\n]+)*',
                                'optional': True
                            },
                            'description': 'Comma separated list of author names.',
                            'order': 3,
                            'presentation': {
                                'hidden': True,
                            },
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/Action_Editors', f'{paper_group.id}/Authors']
                            }
                        },
                        'authorids': {
                            'value': {
                                'values-regex': r'~.*|([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,},){0,}([a-z0-9_\-\.]{1,}@[a-z0-9_\-\.]{2,}\.[a-z]{2,})',
                                'optional': True
                            },
                            'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                            'order': 4,
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/Action_Editors', f'{paper_group.id}/Authors']
                            }
                        },
                        'pdf': {
                            'value': {
                                'value-file': {
                                    'fileTypes': ['pdf'],
                                    'size': 50
                                },
                                'optional': True
                            },
                            'description': 'Upload a PDF file that ends with .pdf',
                            'order': 5,
                        },
                        "supplementary_material": {
                            'value': {
                                "value-file": {
                                    "fileTypes": [
                                        "zip",
                                        "pdf"
                                    ],
                                    "size": 100
                                },
                                "optional": True
                            },
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            "order": 6,
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/Action_Editors', f'{paper_group.id}/Reviewers', f'{paper_group.id}/Authors']
                            }
                        },
                        'previously_submission_url': {
                            'value': {
                                'value-regex': 'https:\/\/openreview\.net\/forum\?id=.*',
                                'optional': True
                            },
                            'description': 'Link to OpenReview page of a previously rejected TMLR submission that this submission is derived from',
                            'order': 7,
                        },
                        'changes_since_last_submission': {
                            'value': {
                                'value-regex': '[\\S\\s]{1,5000}',
                                'optional': True
                            },
                            'description': 'Describe changes since last TMLR submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                            'order': 8,
                        },
                        'competing_interests': {
                            'value': {
                                'value-regex': '[\\S\\s]{1,5000}',
                                'optional': True
                            },
                            'description': 'Supports providing "competing interests" information (which is only viewable by EICs and AEs, but made public if paper accepted). Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                            'order': 9,
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/Action_Editors', f'{paper_group.id}/Authors']
                            }
                        },
                        'human_subject': {
                            'value': {
                                'value-regex': '[\\S\\s]{1,5000}',
                                'optional': True
                            },
                            'description': 'Supports human subject reporting information (which is only viewable by EICs and AEs, but made public if paper accepted). Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                            'order': 10,
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/Action_Editors', f'{paper_group.id}/Authors']
                            }
                        }
                    }
                }
            },
            process_string=revision_process_function
    ))

    public_comment_invitation_id=f'{paper_group.id}/-/Public_Comment'
    invitation = client.post_invitation_edit(readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=Invitation(id=public_comment_invitation_id,
            invitees=['everyone'],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values-regex': f'~.*|{venue_id}/Editors_In_Chief|{paper_group.id}/Action_Editors|{paper_group.id}/Reviewers/.*|{paper_group.id}/Authors' },
                'readers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}']},
                'writers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}']},
                'note': {
                    'id': {
                        'value-invitation': public_comment_invitation_id,
                        'optional': True
                    },
                    'forum': { 'value': note.id },
                    'ddate': {
                        'int-range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'values': ['${signatures}'] },
                    'readers': { 'values': [ 'everyone']},
                    'writers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}']},
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your comment.',
                            'value': {
                                'value-regex': '.{1,500}'
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                            'value': {
                                'value-regex': '[\\S\\s]{1,5000}'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        }
                    }
                }
            }))

    official_comment_invitation_id=f'{paper_group.id}/-/Official_Comment'
    invitation = client.post_invitation_edit(readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=Invitation(id=official_comment_invitation_id,
            invitees=[venue_id, f'{paper_group.id}/Action_Editors', f'{paper_group.id}/Reviewers'],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values-regex': f'{venue_id}/Editors_In_Chief|{paper_group.id}/Action_Editors|{paper_group.id}/Reviewers/.*' },
                'readers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors', f'{paper_group.id}/Reviewers']},
                'writers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}']},
                'note': {
                    'id': {
                        'value-invitation': public_comment_invitation_id,
                        'optional': True
                    },
                    'forum': { 'value': note.id },
                    'ddate': {
                        'int-range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'values': ['${signatures}'] },
                    'readers': { 'values-dropdown': [f'{venue_id}/Editors_In_Chief', f'{paper_group.id}/Action_Editors', f'{paper_group.id}/Reviewers']},
                    'writers': { 'values': ['${signatures}']},
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your comment.',
                            'value': {
                                'value-regex': '.{1,500}'
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                            'value': {
                                'value-regex': '[\\S\\s]{1,5000}'
                            },
                            'presentation': {
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
        invitation=Invitation(id=moderate_invitation_id,
            invitees=[venue_id, f'{paper_group.id}/Action_Editors'],
            readers=[venue_id, f'{paper_group.id}/Action_Editors'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values-regex': f'{paper_group.id}/Action_Editors|{venue_id}$' },
                'readers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors']},
                'writers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors']},
                'note': {
                    'id': { 'value-invitation': public_comment_invitation_id },
                    'forum': { 'value': note.id },
                    'readers': {
                        'values': ['everyone']
                    },
                    'writers': {
                        'values': [venue_id, f'{paper_group.id}/Action_Editors']
                    },
                    'signatures': { 'values-regex': '~.*', 'optional': True },
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Brief summary of your comment.',
                            'value': {
                                'value-regex': '.{1,500}'
                            },
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}']
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                            'value': {
                                'value-regex': '[\\S\\s]{1,5000}'
                            },
                            'presentation': {
                                'markdown': True
                            },
                            'readers': {
                                'values': [ venue_id, f'{paper_group.id}/Action_Editors', '${signatures}']
                            }
                        }
                    }
                }
            }
        )
    )

    invitation = client.post_invitation_edit(readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=Invitation(id=f'{paper_group.id}/-/Decision',
            duedate=1613822400000,
            invitees=[], # no invitees, activate when all the ratings are complete
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            edit={
                'signatures': { 'values': [f'{paper_group.id}/Action_Editors'] },
                'readers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors'] },
                'writers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors'] },
                'note': {
                    'id': {
                        'value-invitation': f'{paper_group.id}/-/Decision',
                        'optional': True
                    },
                    'forum': { 'value': note.forum },
                    'replyto': { 'value': note.forum },
                    'ddate': {
                        'int-range': [ 0, 9999999999999 ],
                        'optional': True,
                        'nullable': True
                    },
                    'signatures': { 'values': [f'{paper_group.id}/Action_Editors'] },
                    'readers': { 'values': [ 'everyone' ] },
                    'writers': { 'values': [ venue_id, f'{paper_group.id}/Action_Editors'] },
                    'content': {
                        'recommendation': {
                            'order': 1,
                            'value': {
                                'value-radio': [
                                    'Accept as is',
                                    'Accept with revisions',
                                    'Reject'
                                ]
                            }
                        },
                        'comment': {
                            'order': 2,
                            'description': 'TODO (max 200000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                            'value': {
                                'value-regex': '[\\S\\s]{1,200000}'
                            },
                            'presentation': {
                                'markdown': True
                            }
                        }
                    }
                }
            },
            process_string='''def process(client, edit, invitation):
    venue_id='.TMLR'
    note=edit.note
    paper_group_id=edit.invitation.split('/-/')[0]

    if note.content['recommendation']['value'] == 'Reject':
        return

    invitation_name= 'Camera_Ready_Revision' if note.content['recommendation']['value'] == 'Accept as is' else 'Revision'

    revision_invitation_id=f'{paper_group_id}/-/{invitation_name}'
    invitation = client.post_invitation_edit(readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        invitation=Invitation(id=revision_invitation_id,
            invitees=[f"{paper_group_id}/Authors"],
            readers=['everyone'],
            writers=[venue_id],
            signatures=[venue_id],
            duedate=1613822400000,
            edit={
                'signatures': { 'values': [f'{paper_group_id}/Authors'] },
                'readers': { 'values': ['everyone']},
                'writers': { 'values': [ venue_id, f'{paper_group_id}/Authors']},
                'note': {
                    'id': { 'value': note.forum },
                    'forum': { 'value': note.forum },
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                            'value': {
                                'value-regex': '.{1,250}',
                                'optional':True
                            }
                        },
                        'abstract': {
                            'order': 4,
                            'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$',
                            'value': {
                                'value-regex': '[\\S\\s]{1,5000}',
                                'optional':True
                            }
                        },
                        'authors': {
                            'order': 2,
                            'description': 'Comma separated list of author names.',
                            'presentation': {
                                'hidden': True,
                            },
                            'value': {
                                'values-regex': '.*',
                                'optional':True
                            }
                        },
                        'authorids': {
                            'order': 3,
                            'description': 'Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author completing first, middle, last and name and author email address.',
                            'value': {
                                'values-regex': r'~.*|.*',
                                'optional':True
                            }
                        },
                        'pdf': {
                            'order': 5,
                            'description': 'Upload a PDF file that ends with .pdf',
                            'value': {
                                'value-file': {
                                    'fileTypes': ['pdf'],
                                    'size': 50
                                },
                                'optional':True
                            }
                        },
                        "supplementary_material": {
                            "order": 6,
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            'value': {
                                "value-file": {
                                    "fileTypes": [
                                        "zip",
                                        "pdf"
                                    ],
                                    "size": 100
                                },
                                "optional": True
                            }
                        },
                        "video": {
                            "order": 6,
                            "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                            'value': {
                                "value-file": {
                                    "fileTypes": [
                                        "mp4"
                                    ],
                                    "size": 100
                                }
                            }
                        }
                    }
                }
            }))
'''
    ))


