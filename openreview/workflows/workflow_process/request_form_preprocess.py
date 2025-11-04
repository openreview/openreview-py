def process(client, edit, invitation):

    request_note = edit.note
    venue_agreement = request_note.content['venue_organizer_agreement']['value']

    if len(venue_agreement) != 9:
        raise openreview.OpenReviewException('Please be sure to acknowledge and agree to all terms in the Venue Organizer Agreement.')