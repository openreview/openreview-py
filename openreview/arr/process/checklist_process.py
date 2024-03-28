def process(client, edit, invitation):
    from openreview.arr.helpers import flag_submission
    flagging_info = {
        'reply_name': 'Checklist',
        'violation_fields' : {
            'appropriateness': 'Yes',
            'formatting': 'Yes',
            'length': 'Yes',
            'anonymity': 'Yes',
            'responsible_checklist': 'Yes',
            'limitations': 'Yes'
        },
        'ethics_flag_field': {
            'need_ethics_review': 'No'
        }
    }
    flag_submission(
        client,
        edit,
        invitation,
        flagging_info
    )