def process(client, note, invitation):
    import datetime

    previous_configurations = client.get_references(
        referent=note.forum,
        invitation=note.invitation
    )

    extension_start_date = note.content.get('author_response_extension_start_date')
    if not extension_start_date:
        return

    close_author_response_date = note.content.get('close_author_response_date')
    if not close_author_response_date:
        for configuration in previous_configurations:
            if configuration.content.get('close_author_response_date'):
                close_author_response_date = configuration.content['close_author_response_date']
                break

    if not close_author_response_date:
        return

    def parse_date(date):
        try:
            return datetime.datetime.strptime(date.strip(), '%Y/%m/%d %H:%M')
        except ValueError:
            return datetime.datetime.strptime(date.strip(), '%Y/%m/%d')

    if parse_date(extension_start_date) <= parse_date(close_author_response_date):
        raise openreview.OpenReviewException(
            'The author response extension start date must be after the close author response date.'
        )
