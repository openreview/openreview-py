def process(client, edit, invitation):

    country_fees = edit.content['country_fees']['value']
    if country_fees == { 'delete': True }:
        return

    if not isinstance(country_fees, dict):
        raise openreview.OpenReviewException('The fees by country must be an object from ISO 3166-1 alpha-2 codes to fees, for example {"ET": 0, "IN": 1000}.')

    if not country_fees:
        raise openreview.OpenReviewException('Enter {"delete": true} to remove the fees by country: an empty table can not be saved.')

    fee_invitation = client.get_invitation(invitation.edit['invitation']['id'])
    amount = fee_invitation.get_content_value('amount')
    for country, fee in country_fees.items():
        if not re.fullmatch('[A-Z]{2}', country):
            raise openreview.OpenReviewException(f'{country} is not an ISO 3166-1 alpha-2 country code.')
        if not isinstance(fee, int) or isinstance(fee, bool) or fee < 0 or fee > amount:
            raise openreview.OpenReviewException(f'The fee of {country} must be an integer from 0 to the full amount, {amount}.')

    waiver_name = fee_invitation.get_content_value('waiver_name')
    if 0 in country_fees.values() and not openreview.tools.get_invitation(client, f'{invitation.domain}/-/{waiver_name}'):
        raise openreview.OpenReviewException(f'Enable the {waiver_name} step first: the fees of 0 are waived through it.')
