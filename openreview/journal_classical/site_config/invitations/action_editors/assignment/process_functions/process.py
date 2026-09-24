def process_update(client, edge, invitation, existing_edge):
    """Keep the Journal Python dateprocess entry point as the first token."""
    try:
        return _process_update_with_selected_template(
            client, edge, invitation, existing_edge
        )
    except Exception:
        raise openreview.OpenReviewException(
            'Action Editor assignment process failed.'
        ) from None

# {{PYTHON_SCRIPT_FILE:invitations/venue/ae_assignment_continuity.py}}
# {{PYTHON_SCRIPT_FILE:invitations/venue/previous_submission_ae_reader_bridge.py}}

INITIAL_ASSIGNMENT_TEMPLATE = "{{EMAIL_TEMPLATE_JSON:ae/assignment_initial.txt}}"
CONTINUITY_ASSIGNMENT_TEMPLATE = "{{EMAIL_TEMPLATE_JSON:ae/assignment_continuity.txt}}"


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
    from openreview.journal.process import ae_assignment_process as journal_process

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(edge.head)
    if not edge.ddate:
        ensure_previous_submission_access_for_current_ae(client, journal, submission)
    continuity = (
        not edge.ddate
        and active_prior_ae_assignment(client, journal, submission, edge.tail)
    )
    template = CONTINUITY_ASSIGNMENT_TEMPLATE if continuity else INITIAL_ASSIGNMENT_TEMPLATE
    wrapped_client = _AssignmentTemplateClient(
        client, journal.get_action_editors_id(), template
    )
    journal_process.openreview = openreview
    journal_process.datetime = datetime
    original_journal_factory = openreview.journal.Journal
    openreview.journal.Journal = lambda: journal
    try:
        return journal_process.process_update(
            wrapped_client, edge, invitation, existing_edge
        )
    finally:
        openreview.journal.Journal = original_journal_factory
