def process(client, edit, invitation):

    support_user = f'{invitation.domain}/Support'
    venue_id = edit.group.id

    invitation_edit = client.post_invitation_edit(invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Edit_Template',
        signatures=['~Super_User1'],
        domain=venue_id
    )

    client.add_members_to_group('venues', venue_id)
    client.add_members_to_group('active_venues', venue_id)
    
    path_components = venue_id.split('/')
    paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]
    for group in paths[:-1]:
        client.post_group_edit(
            invitation=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Venue_Inner_Group_Template',
            signatures=['~Super_User1'],
            group=openreview.api.Group(
                id=group,
           ),
            await_process=True
        )
    root_id = paths[0]
    if root_id == root_id.lower():
        root_id = paths[1]       
    client.add_members_to_group('host', root_id)

    workflow_invitations = [f'{venue_id}/-/Submission', f'{venue_id}/-/Submission_Change_Before_Bidding', f'{venue_id}/-/Withdrawal_Request', f'{venue_id}/-/Withdrawal',
        f'{venue_id}/-/Desk_Rejection', f'{venue_id}/-/Desk_Rejected_Submission', f'{venue_id}/-/Reviewer_Bid',
        f'{venue_id}/-/Reviewer_Conflict', f'{venue_id}/-/Reviewer_Submission_Affinity_Score', f'{venue_id}/-/Deploy_Reviewer_Assignment', f'{venue_id}/-/Review', f'{venue_id}/-/Comment',
        f'{venue_id}/-/Author_Rebuttal', f'{venue_id}/-/Decision', f'{venue_id}/-/Decision_Upload', f'{venue_id}/-/Submission_Change_Before_Reviewing', f'{venue_id}/Reviewers/-/Submission_Group', f'{venue_id}/Reviewers_Invited/-/Response']

    client.post_group_edit(
        invitation=invitation_edit['invitation']['id'],
        signatures=['~Super_User1'],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'meta_invitation_id': { 'value': invitation_edit['invitation']['id'] },
                'rejected_venue_id': { 'value': f'{venue_id}/Rejected' }, ## Move this to the Rejected invitation process,
                'workflow_invitations': { 'value': workflow_invitations }
            }
        )
    )
    
    ## Create invitation to edit the venue group
    client.post_invitation_edit(
        invitations=f'{venue_id}/-/Edit',
        signatures=['~Super_User1'],
        readers=[venue_id],
        writers=['~Super_User1'],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/Venue_Information',
            readers=[venue_id],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            invitees=[venue_id],
            edit={
                'content': {
                    'title': {
                        'order': 2,
                        'description': 'Venue title',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'subtitle': {
                        'order': 3,
                        'description': 'Venue subtitle',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'website': {
                        'order': 4,
                        'description': 'Venue website',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'location': {
                        'order': 5,
                        'description': 'Venue location',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    },
                    'start_date': {
                        'order': 6,
                        'description': 'Venue start date',
                        'value': {
                            'param': {
                                'type': 'date',
                                'range': [ 0, 9999999999999 ],
                            }
                        }
                    },
                    'contact': {
                        'order': 7,
                        'description': 'Venue contact',
                        'value': {
                            'param': {
                                'type': 'string',
                                'maxLength': 100
                            }
                        }
                    }
                },                
                'signatures' : {
                    'param': {
                        'items': [
                            { 'value': venue_id, 'optional': True },
                            { 'value': support_user, 'optional': True }
                        ]
                    }
                },
                'readers': ['everyone'],
                'writers': [venue_id],
                'group': {
                    'id': venue_id,
                    'content': { 
                        'title': { 'value': '${4/content/title/value}'},
                        'subtitle': { 'value': '${4/content/subtitle/value}'},
                        'website': { 'value': '${4/content/website/value}'},
                        'location': { 'value': '${4/content/location/value}'},
                        'start_date': { 'value': '${4/content/start_date/value}'},
                        'contact': { 'value': '${4/content/contact/value}'}                       
                    }

                }
            }
        )
    )

    client.post_invitation_edit(
        invitations=f'{venue_id}/-/Edit',
        signatures=['~Super_User1'],
        readers=[venue_id],
        writers=['~Super_User1'],
        invitation=openreview.api.Invitation(
            id=f'{venue_id}/-/Venue_Homepage',
            readers=[venue_id],
            writers=['~Super_User1'],
            signatures=['~Super_User1'],
            invitees=[venue_id],
            edit={
                'content': {
                    'web': {
                        'order': 1,
                        'description': 'Venue home page',
                        'value': {
                            'param': {
                                'type': 'string',
                                'input': 'textarea',
                                'markdown': True
                            }
                        }
                    }
                },                
                'signatures' : {
                    'param': {
                        'items': [
                            { 'value': venue_id, 'optional': True },
                            { 'value': support_user, 'optional': True }
                        ]
                    }
                },
                'readers': ['everyone'],
                'writers': [venue_id],
                'group': {
                    'id': venue_id,
                    "web": "${2/content/web/value}"
                }
            }
        )
    )    