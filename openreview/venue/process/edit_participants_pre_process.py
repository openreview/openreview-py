def process(client, edit, invitation):

    participants = [participant.replace('${3/content/noteNumber/value}', '') for participant in edit.content['participants']['value']]
    readers = [reader['value'].replace('${8/content/noteNumber/value}', '') for reader in edit.content['reply_readers']['value']]

    for participant in participants:
        if participant not in readers:
            participant = participant.split('/')[-1]
            raise openreview.OpenReviewException(f' The participant {openreview.tools.pretty_id(participant)} must also be readers of comments')