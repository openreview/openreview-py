def process(client, note, invitation):
    decision_options = note.content.get('decision_options')
    accept_decision_options = note.content.get('accept_decision_options')
 
    if decision_options:
        decision_options = [s.translate(str.maketrans('', '', '"\'')).strip() for s in decision_options.split(',')]
    else: # default vals are used
        return

    if all('Accept' not in d for d in decision_options) and not accept_decision_options:
        raise openreview.OpenReviewException('Please specify the accept options in "Accept Decision Options"')

    if accept_decision_options:
        accept_decision_options = [s.translate(str.maketrans('', '', '"\'')).strip() for s in accept_decision_options.split(',')]
        if any(d not in decision_options for d in accept_decision_options):
            raise openreview.OpenReviewException('All accept decision options must be included in "Decision Options"')