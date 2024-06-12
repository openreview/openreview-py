def process(client, invitation):
    # TODO: Store registration and max load names in domain content to parameterize them

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    import time, calendar
    registration_name = 'Registration'
    max_load_name = 'Max_Load_And_Unavailability_Request'
    reviewer_license_name = 'License_Agreement'

    def _is_identical_content(note_to_post, notes):
        for note in notes:
            is_identical = True
            if set(note.content.keys()) != set(note_to_post.content.keys()):
                continue
            for k, v in note_to_post.content.items():
                if v['value'] != note.content[k]['value']:
                    is_identical = False
            if is_identical:
                return note
        return None

    def _is_not_available(month: str, year: int, current_date: datetime.datetime, posted_date: datetime.datetime) -> bool:
        """
        Check if a user is available based on their next available month and year

        Parameters:
        month (str): Month in plaintext
        year (int): Year as a number
        current_date (datetime.datetime): A datetime object for the next cycle
        posted_date (datetime.datetime): A datetime object for when the note was posted to give context for the selected date

        Returns:
        tuple: (month, year) if the user is unavailable, tuple contains corrected next available date, otherwise return None
        """
        month_number = {v: k for k,v in enumerate(calendar.month_name)}

        if year is None and month is None:
            return None ## If didn't fill out, assume available
        elif year is None and month is not None: ## If no year, infer year by the inputted month and the month it was posted
            next_available_month = month_number[month]
            posted_month = posted_date.month
            if next_available_month >= posted_month:
                year = posted_date.year
            else:
                year = posted_date.year + 1
        elif year is not None and month is None:
            month = 'January' ## Start of the year

        # Validate year
        year = max(current_date.year, year) ## Year must be at least the posted

        # Create a date object for the given month and year
        next_available_date = datetime.datetime(year, month_number[month], 1)
        
        # Compare the given date with the current date
        if next_available_date.year < current_date.year or (next_available_date.year == current_date.year and next_available_date.month <= current_date.month):
            return None ## None = is available
        else:
            return (month, year) ## Tuple = is not available, will be available in tuple

    domain = client.get_group(invitation.domain)
    venue_id = domain.id

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return
    previous_cycle_id = invitation.content['previous_cycle']['value']
    next_cycle_id = venue_id
    
    ## Try and retrieve different groups, notes and edges and change their readership

    # Groups (Reviewers, ACs, SACs, Ethics Reviewers, Ethics Chairs)
    groups = [
        client.get_group(group_id) for group_id in
        [
            domain.content['reviewers_id']['value'].replace(venue_id, previous_cycle_id),
            domain.content['area_chairs_id']['value'].replace(venue_id, previous_cycle_id),
            domain.content['senior_area_chairs_id']['value'].replace(venue_id, previous_cycle_id),
            domain.content['ethics_chairs_id']['value'].replace(venue_id, previous_cycle_id),
            f"{previous_cycle_id}/{domain.content['ethics_reviewers_name']['value']}",
        ]
    ]

    for group in groups:
        role = group.id.split('/')[-1]
        destination_group = client.get_group(f"{next_cycle_id}/{role}")
        missing_members = set(group.members).difference(set(destination_group.members))
        if len(missing_members) > 0:
            client.add_members_to_group(destination_group, list(missing_members))

    # De-duplicate groups (SAEs + AEs -> Reviewers, SAEs -> AEs)
    saes = client.get_group(domain.content['senior_area_chairs_id']['value'])
    aes = client.get_group(domain.content['area_chairs_id']['value'])
    reviewers = client.get_group(domain.content['reviewers_id']['value'])
    sae_reviewers = set(saes.members).intersection(set(reviewers.members))
    ae_reviewers = set(aes.members).intersection(set(reviewers.members))
    sae_aes = set(saes.members).intersection(set(aes.members))

    if len(sae_reviewers) > 0:
        client.remove_members_from_group(reviewers, list(sae_reviewers))
    if len(ae_reviewers) > 0:
        client.remove_members_from_group(reviewers, list(ae_reviewers))
    if len(sae_aes) > 0:
        client.remove_members_from_group(aes, list(sae_aes))

    # Notes (Registraton Notes)
    roles = [
        domain.content['senior_area_chairs_id']['value'].replace(venue_id, previous_cycle_id),
        domain.content['area_chairs_id']['value'].replace(venue_id, previous_cycle_id),
        domain.content['reviewers_id']['value'].replace(venue_id, previous_cycle_id)]
    for role in roles:
        reg_invitation = client.get_invitation(f"{role}/-/{registration_name}")
        next_reg_invitation = client.get_invitation(f"{next_cycle_id}/{role.split('/')[-1]}/-/{registration_name}")

        existing_notes = client.get_all_notes(invitation=next_reg_invitation.id)
        notes = client.get_all_notes(invitation=reg_invitation.id)

        for note in notes:
            if _is_identical_content(note, existing_notes):
                continue
            # Clear note fields
            note.id = None
            note.invitations = None
            note.cdate = None
            note.mdate = None
            note.license = None
            note.readers = [next_cycle_id, note.signatures[0]]
            note.writers = [next_cycle_id, note.signatures[0]]
            note.forum = next_reg_invitation.edit['note']['forum']
            note.replyto = next_reg_invitation.edit['note']['replyto']

            client.post_note_edit(
                invitation=f"{next_cycle_id}/{role.split('/')[-1]}/-/{registration_name}",
                signatures=note.signatures,
                readers=note.readers,
                note=note
            )

    # Reviewer License Notes (Registraton Notes)
    reviewers_id = domain.content['reviewers_id']['value'].replace(venue_id, previous_cycle_id)
    license_invitation = client.get_invitation(f"{reviewers_id}/-/{reviewer_license_name}")
    next_license_invitation = client.get_invitation(f"{next_cycle_id}/{reviewers_id.split('/')[-1]}/-/{reviewer_license_name}")

    existing_notes = client.get_all_notes(invitation=next_license_invitation.id)
    notes = client.get_all_notes(invitation=license_invitation.id)

    for note in notes:
        if _is_identical_content(note, existing_notes):
            continue
        if 'agree for this cycle and all future cycles' not in note.content['agreement']['value'].lower():
            continue
        # Clear note fields
        note.id = None
        note.invitations = None
        note.cdate = None
        note.mdate = None
        note.license = None
        note.readers = [next_cycle_id, note.signatures[0]]
        note.writers = [next_cycle_id, note.signatures[0]]
        note.forum = next_license_invitation.edit['note']['forum']
        note.replyto = next_license_invitation.edit['note']['replyto']

        client.post_note_edit(
            invitation=f"{next_cycle_id}/{reviewers_id.split('/')[-1]}/-/{reviewer_license_name}",
            signatures=note.signatures,
            readers=note.readers,
            note=note
        )

    # Edges (Expertise Edges)
    for role in roles:
        exp_edges = {o['id']['tail']: o['values'] for o in client.get_grouped_edges(
            invitation=f"{role}/-/Expertise_Selection",
            groupby='tail',
            select='head,label')
        }
        existing_exp_edges = {o['id']['tail']: [e['head'] for e in o['values']] for o in client.get_grouped_edges(
            invitation=f"{next_cycle_id}/{role.split('/')[-1]}/-/Expertise_Selection",
            groupby='tail',
            select='head')
        }

        for tail, pub_edges in exp_edges.items():
            for pub_edge in pub_edges:
                if tail in existing_exp_edges and pub_edge['head'] in existing_exp_edges[tail]:
                    continue
                client.post_edge(
                    openreview.api.Edge(
                        invitation=f"{next_cycle_id}/{role.split('/')[-1]}/-/Expertise_Selection",
                        readers=[next_cycle_id, tail],
                        writers=[next_cycle_id, tail],
                        signatures=[tail],
                        head=pub_edge['head'],
                        tail=tail,
                        label=pub_edge['label']
                    )
                )

    # Conditionally post unavailability notes
    month_to_number = {name: number for number, name in enumerate(calendar.month_name)}
    cycle_year = int(venue_id.split('/')[-2])
    cycle_month = month_to_number[venue_id.split('/')[-1]]

    for role in roles:
        load_invitation = client.get_invitation(f"{role}/-/{max_load_name}")
        next_load_invitation = client.get_invitation(f"{next_cycle_id}/{role.split('/')[-1]}/-/{max_load_name}")

        existing_notes = client.get_all_notes(invitation=next_load_invitation.id)
        notes = client.get_all_notes(invitation=load_invitation.id)

        for note in notes:
            next_available_date = _is_not_available(
                note.content.get('next_available_month', {}).get('value'),
                note.content.get('next_available_year', {}).get('value') if note.content.get('next_available_year', {}).get('value') else None,
                datetime.date(cycle_year, cycle_month, 15),
                datetime.datetime.fromtimestamp(int(note.cdate/1000))
            )
            if next_available_date is not None:
                note.id = None
                note.invitations = None
                note.cdate = None
                note.mdate = None
                note.license = None
                note.readers = [next_cycle_id, note.signatures[0]]
                note.writers = [next_cycle_id, note.signatures[0]]
                note.forum = next_load_invitation.edit['note']['forum']
                note.replyto = next_load_invitation.edit['note']['replyto']
                note.content['maximum_load_this_cycle'] = {'value': 0 }
                note.content['next_available_month'] = {'value': next_available_date[0]}
                note.content['next_available_year'] = {'value': next_available_date[1]}
                
                if not _is_identical_content(note, existing_notes):
                    client.post_note_edit(
                        invitation=f"{next_cycle_id}/{role.split('/')[-1]}/-/{max_load_name}",
                        signatures=note.signatures,
                        readers=note.readers,
                        note=note
                    )