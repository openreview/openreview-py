def process_update(client, edge, invitation, existing_edge):
    """Keep the Journal Python dateprocess entry point as the first token."""
    return _process_update_with_selected_template(
        client, edge, invitation, existing_edge
    )

# {{PYTHON_SCRIPT_FILE:invitations/venue/under_review/previous_submission_reviewer_policy.py}}

INITIAL_ASSIGNMENT_TEMPLATE = "{{EMAIL_TEMPLATE_JSON:reviewer/assignment_initial.txt}}"
CONTINUITY_ASSIGNMENT_TEMPLATE = "{{EMAIL_TEMPLATE_JSON:reviewer/assignment_continuity.txt}}"


class _GroupTemplateView:
    def __init__(self, group, template):
        self._group = group
        self.content = dict(group.content or {})
        self.content['assignment_email_template_script'] = {'value': template}

    def __getattr__(self, name):
        return getattr(self._group, name)


class _AssignmentTemplateClient:
    def __init__(self, client, group_id, template):
        self._client = client
        self._group_id = group_id
        self._template = template

    def get_group(self, group_id, *args, **kwargs):
        group = self._client.get_group(group_id, *args, **kwargs)
        if group_id == self._group_id:
            return _GroupTemplateView(group, self._template)
        return group

    def __getattr__(self, name):
        return getattr(self._client, name)


def _process_update_with_selected_template(client, edge, invitation, existing_edge):
    import datetime
    from openreview.journal.process import reviewer_assignment_process as journal_process

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(edge.head)
    continuity = (
        not edge.ddate
        and active_prior_reviewer_assignment(client, journal, submission, edge.tail)
    )
    template = CONTINUITY_ASSIGNMENT_TEMPLATE if continuity else INITIAL_ASSIGNMENT_TEMPLATE
    wrapped_client = _AssignmentTemplateClient(
        client, journal.get_reviewers_id(), template
    )
    journal_process.openreview = openreview
    journal_process.datetime = datetime
    original_journal_factory = openreview.journal.Journal
    openreview.journal.Journal = lambda: journal
    try:
        return journal_process.process_update(
            wrapped_client, edge, invitation, existing_edge
        )
    except Exception as error:
        raise openreview.OpenReviewException(
            f'Reviewer assignment side effect failed: '
            f'{type(error).__name__}: {error}'
        ) from error
    finally:
        openreview.journal.Journal = original_journal_factory
