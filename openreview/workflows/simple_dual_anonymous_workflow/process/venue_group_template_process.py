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

    exclusion_workflow_invitations  = [
        f'{venue_id}/-/Edit',
        f'/{venue_id}/Submission[0-9]+/',
        f'/{venue_id}/-/Venue.*/',
        f'{venue_id}/Reviewers/-/Message', # TODO: parametrize group names and invitation names
        f'/{venue_id}/Reviewers/-/(?!Submission_Group$).*/', # matching invitations
        f'{venue_id}/Authors/-/Message',
        f'/{venue_id}/Reviewers_Invited/-/(?!Response$).*/',
        f'{venue_id}/-/Message',
    ]

    client.post_group_edit(
        invitation=invitation_edit['invitation']['id'],
        signatures=['~Super_User1'],
        group=openreview.api.Group(
            id=venue_id,
            content={
                'meta_invitation_id': { 'value': invitation_edit['invitation']['id'] },
                'rejected_venue_id': { 'value': f'{venue_id}/Rejected' }, ## Move this to the Rejected invitation process,
                'exclusion_workflow_invitations': { 'value': exclusion_workflow_invitations }
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
                                'type': 'script'
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

    client.post_invitation_edit(
        invitations=f'{support_user}/Simple_Dual_Anonymous/Venue_Configuration_Request/-/Venue_Message_Template',
        signatures=[support_user],
        content={
            'venue_id': { 'value': venue_id },
            'message_reply_to': { 'value': edit.group.content['contact']['value'] },
            'venue_short_name': { 'value': edit.group.content['subtitle']['value'] },
            'venue_from_email': { 'value': f"{edit.group.content['subtitle']['value'].replace(' ', '').replace(':', '-').replace('@', '').replace('(', '').replace(')', '').replace(',', '-').lower()}-notifications@openreview.net" }
        },
        invitation=openreview.api.Invitation(),
        await_process=True
    )     