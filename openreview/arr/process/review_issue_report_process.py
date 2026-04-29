from openreview.stages.arr_content import arr_review_rating_content

REPORT_EVALUATION_NAME = 'Report_Evaluation'
REPORT_EVALUATION_WINDOW_DAYS = 30
REPORT_EVALUATION_WINDOW_MILLIS = REPORT_EVALUATION_WINDOW_DAYS * 24 * 60 * 60 * 1000


def _get_issue_options(report):
    issue_options = []
    for field_name in arr_review_rating_content:
        if field_name == 'justification':
            continue

        field_value = report.content.get(field_name, {}).get('value')
        if isinstance(field_value, list):
            field_value = field_value[0] if field_value else None

        if field_value:
            issue_code = field_name.split('_')[0]
            issue_options.append(f'{issue_code}. {field_value}')

    return issue_options


def _build_report_evaluation_content(report):
    issue_options = _get_issue_options(report)
    if not issue_options:
        return None

    return {
        'justified_issues': {
            'value': {
                'param': {
                    'type': 'string[]',
                    'input': 'checkbox',
                    'enum': issue_options,
                    'optional': True,
                    'deletable': True
                }
            },
            'description': 'Select the reported review issues that you found justified.',
            'order': 1
        },
        'justification': {
            'value': {
                'param': {
                    'type': 'string',
                    'input': 'textarea',
                    'maxLength': 5000,
                    'markdown': True,
                    'optional': True
                }
            },
            'description': 'Optional comments for Program Chairs and Senior Area Chairs about this evaluation.',
            'order': 2
        }
    }


def process(client, edit, invitation):
    domain = client.get_group(edit.domain)
    venue_id = domain.id
    report = client.get_note(edit.note.id)

    if report.ddate or report.tcdate != report.tmdate:
        return

    submission = client.get_note(report.forum)
    evaluation_content = _build_report_evaluation_content(report)
    if not evaluation_content:
        return

    client.post_invitation_edit(
        invitations=f'{venue_id}/-/{REPORT_EVALUATION_NAME}',
        readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        content={
            'noteNumber': {
                'value': submission.number
            },
            'replyId': {
                'value': report.id
            },
            'expdate': {
                'value': report.cdate + REPORT_EVALUATION_WINDOW_MILLIS
            },
            'content': {
                'value': evaluation_content
            }
        },
        invitation=openreview.api.Invitation()
    )
