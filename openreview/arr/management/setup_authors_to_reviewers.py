def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    from openreview.venue import matching
    from openreview.arr.invitation import InvitationBuilder
    import random
    import string

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    request_form_id = domain.content['request_form_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    request_form = client_v1.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]
    venue = openreview.helpers.get_conference(client_v1, request_form_id, support_group)
    reviewers_group = client.get_group(venue.get_reviewers_id())

    # Load authors submitted forms
    author_forms = client.get_all_notes(
        invitation=f"{venue.get_authors_id()}/-/{InvitationBuilder.SUBMITTED_AUTHORS_NAME}"
    )
    # Load existing reviewer registration and license forms
    reviewer_forms = client.get_all_notes(
        invitation=f"{venue.get_reviewers_id()}/-/{InvitationBuilder.REGISTRATION_NAME}"
    )
    reviewer_license_forms = client.get_all_notes(
        invitation=f"{venue.get_reviewers_id()}/-/{InvitationBuilder.REVIEWER_LICENSE_NAME}"
    )
    reviewer_load_forms = client.get_all_notes(
        invitation=f"{venue.get_reviewers_id()}/-/{InvitationBuilder.MAX_LOAD_AND_UNAVAILABILITY_NAME}"
    )

    # Load profiles from author and reviewer signatures
    author_signatures = [n.signatures[0] for n in author_forms]
    reviewer_signatures = [n.signatures[0] for n in reviewer_forms]
    reviewer_license_signatures = [n.signatures[0] for n in reviewer_license_forms]
    reviewer_load_signatures = [n.signatures[0] for n in reviewer_load_forms]
    all_profiles = openreview.tools.get_profiles(client, author_signatures + reviewer_signatures + reviewer_license_signatures + reviewer_load_signatures)
    name_to_id = {}
    for profile in all_profiles:
        filtered_names = filter(
            lambda obj: 'username' in obj and len(obj['username']) > 0,
            profile.content.get('names', [])
        )
        for name_obj in filtered_names:
            name_to_id[name_obj['username']] = profile.id
    submitted_reviewer_ids = set(name_to_id[n.signatures[0]] for n in reviewer_forms)
    submitted_reviewer_license_ids = set(name_to_id[n.signatures[0]] for n in reviewer_license_forms)
    submitted_reviewer_load_ids = set(name_to_id[n.signatures[0]] for n in reviewer_load_forms)
    # author_form -> registration form
    DEFAULT_REGISTRATION_CONTENT = {
        'profile_confirmed': 'Yes',
        'expertise_confirmed': 'Yes',
        'domains': 'Yes',
        'emails': 'Yes',
        'DBLP': 'Yes',
        'semantic_scholar': 'Yes'
    }
    REGISTRATION_FORM_MAPPING = {
        "confirm_your_profile_has_past_domains": "domains",
        "confirm_your_profile_has_all_email_addresses": "emails",
        "indicate_languages_you_study": "languages_studied",
        "indicate_your_research_areas": "research_area",
        "confirm_your_openreview_profile_contains_a_dblp_link": "DBLP", # DBLP should just be ticked
        "confirm_your_openreview_profile_contains_a_semantic_scholar_link": "semantic_scholar", # This should also be ticked
    }
    # author_form -> license_form
    LICENSE_FORM_MAPPING = {
        "agreement": "agreement",
        "attribution": "attribution",
    }

    # Filter by authors in the invitation content
    ## assume authors in invitations are profile IDs
    author_names = invitation.content.get('authors', {}).get('value', [])
    author_forms = [a for a in author_forms if name_to_id[a.signatures[0]] in author_names]

    for author_form in author_forms:
        author_id = name_to_id[author_form.signatures[0]]
        print(f"Processing author {author_id}...")
        # Add author to reviewers group
        if author_id not in reviewers_group.members:
            print(f"Adding author {author_id} to reviewers group")
            client.add_members_to_group(reviewers_group, author_id)

        # Copy to registration
        if author_id not in submitted_reviewer_ids and \
            'indicate_your_research_areas' in author_form.content: ## This is required in registration
            template_registration_content = {
                'profile_confirmed': { 'value': 'Yes' },
                'expertise_confirmed': { 'value': 'Yes' }
            }
            for key, value in REGISTRATION_FORM_MAPPING.items():
                if key in author_form.content:
                    # Handle DBLP and Semantic Scholar special cases
                    if 'dblp' in key or 'semantic_scholar' in key:
                        template_registration_content[value] = { 'value': 'Yes' }
                    else:
                        template_registration_content[value] = author_form.content[key]
            print(f"Copying registration content to {author_id}")
            client.post_note_edit(
                invitation=f"{venue.get_reviewers_id()}/-/{InvitationBuilder.REGISTRATION_NAME}",
                signatures=[author_id],
                note=openreview.api.Note(
                    content=template_registration_content
                )
            )
        
        # Copy to license
        if author_id not in submitted_reviewer_license_ids:
            template_license_content = {}
            for key, value in LICENSE_FORM_MAPPING.items():
                if key in author_form.content:
                    template_license_content[value] = author_form.content[key]
            print(f"Copying license content to {author_id}")
            client.post_note_edit(
                invitation=f"{venue.get_reviewers_id()}/-/{InvitationBuilder.REVIEWER_LICENSE_NAME}",
                signatures=[author_id],
                note=openreview.api.Note(
                    content=template_license_content
                )
            )

        # Copy to reviewer load
        if author_id not in submitted_reviewer_load_ids:
            meta_data_donation = None
            if 'meta_data_donation' in author_form.content:
                if 'yes' in author_form.content['meta_data_donation']['value'].lower():
                    meta_data_donation = {'value': "Yes, I consent to donating anonymous metadata of my review for research."}
                else:
                    meta_data_donation = {'value': "No, I do not consent to donating anonymous metadata of my review for research."}
            else:
                meta_data_donation = {'value': "No, I do not consent to donating anonymous metadata of my review for research."}
            client.post_note_edit(
                invitation=f"{venue.get_reviewers_id()}/-/{InvitationBuilder.MAX_LOAD_AND_UNAVAILABILITY_NAME}",
                signatures=[author_id],
                note=openreview.api.Note(
                    content={
                        'maximum_load_this_cycle': { 'value': 4 }, ## TODO: Remove this hardcoded value
                        'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' },
                        'meta_data_donation': meta_data_donation
                    }
                )
            )
                    
