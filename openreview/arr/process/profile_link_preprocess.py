def process(client, edit, invitation):
    profile_link_requirements = {
        'confirm_your_openreview_profile_contains_a_DBLP_link': ('a DBLP', 'dblp'),
        'confirm_your_openreview_profile_contains_an_ACL_anthology_URL': ('an ACL Anthology', 'aclanthology'),
        'confirm_your_openreview_profile_contains_your_ORCID_ID': ('an ORCID', 'orcid')
    }

    def has_valid_orcid_checksum(orcid_url):
        identifier = orcid_url.split('/')[-1].replace('-', '')

        total = 0
        for digit in identifier[:15]:
            total = (total + int(digit)) * 2

        checksum = (12 - (total % 11)) % 11
        expected_checksum = 'X' if checksum == 10 else str(checksum)
        return identifier[-1].upper() == expected_checksum

    profile = client.get_profile(edit.signatures[0])
    for confirmation_field, (label, profile_field) in profile_link_requirements.items():
        if confirmation_field not in edit.note.content:
            continue

        selected_option = edit.note.content[confirmation_field]['value']
        if selected_option.startswith('N/A'):
            continue

        profile_value = profile.content.get(profile_field)
        if not profile_value:
            raise openreview.OpenReviewException(
                f'Your OpenReview profile does not contain {label} link, but the selected option indicates that it does. '
                f'Please add the link at https://openreview.net/profile?id={profile.id} before submitting this form.'
            )

        if profile_field == 'orcid' and not has_valid_orcid_checksum(profile_value):
            raise openreview.OpenReviewException(
                'The ORCID iD in your OpenReview profile has an invalid checksum. '
                f'Please correct it at https://openreview.net/profile?id={profile.id} before submitting this form.'
            )
