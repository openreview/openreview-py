def process(client, edit, invitation):
    emergency_reviewing_agreement = edit.note.content.get('emergency_reviewing_agreement', {}).get('value')
    emergency_load = edit.note.content.get('emergency_load', {}).get('value')
    research_area = edit.note.content.get('research_area', {}).get('value')

    if 'Yes' in emergency_reviewing_agreement:
        if not emergency_load:
            raise openreview.OpenReviewException('You have agreed to emergency reviewing, please enter the additional load that you want to be assigned.')
        if not research_area:
            raise openreview.OpenReviewException('You have agreed to emergency reviewing, please enter your closest relevant research areas.')