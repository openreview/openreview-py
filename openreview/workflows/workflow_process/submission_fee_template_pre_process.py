def process(client, edit, invitation):

    venue_id = edit.content['venue_id']['value']
    domain = client.get_group(venue_id)

    activation_date = edit.content['activation_date']['value']
    if not isinstance(activation_date, int):
        activation_date = openreview.tools.datetime_millis(datetime.datetime.now())

    full_submission_invitation_id = domain.get_content_value('full_submission_invitation_id')
    full_submission_invitation = openreview.tools.get_invitation(client, full_submission_invitation_id) if full_submission_invitation_id else None
    if full_submission_invitation and full_submission_invitation.ddate:
        full_submission_invitation = None

    if full_submission_invitation:
        deadline_name = 'Full Submission'
        submission_closes = full_submission_invitation.edit['invitation'].get('expdate')
    else:
        deadline_name = 'Submission'
        submission_invitation = openreview.tools.get_invitation(client, domain.get_content_value('submission_id'))
        submission_closes = submission_invitation.expdate if submission_invitation else None

    if submission_closes and activation_date < submission_closes:
        raise openreview.OpenReviewException(f'The submission fee activation date must be later than or equal to the {deadline_name} deadline + grace period (30 minutes). Please update the {deadline_name} dates first or select a later date.')

    amount = edit.content['amount']['value']
    country_fees = edit.content['country_fees']['value']
    if not isinstance(country_fees, dict):
        raise openreview.OpenReviewException('The fees by country must be an object from ISO 3166-1 alpha-2 codes to fees, for example {"ET": 0, "IN": 1000}.')

    for country, fee in country_fees.items():
        if not re.fullmatch('[A-Z]{2}', country):
            raise openreview.OpenReviewException(f'{country} is not an ISO 3166-1 alpha-2 country code.')
        if not isinstance(fee, int) or isinstance(fee, bool) or fee < 0 or fee > amount:
            raise openreview.OpenReviewException(f'The fee of {country} must be an integer from 0 to the full amount, {amount}.')

    waiver_name = edit.content['waiver_name']['value']
    if 0 in country_fees.values() and not openreview.tools.get_invitation(client, f'{venue_id}/-/{waiver_name}'):
        raise openreview.OpenReviewException(f'Enable the {waiver_name} step first: the fees of 0 are waived through it.')
