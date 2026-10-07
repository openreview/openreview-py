"""Select private Action Editor readers for the current paper workflow."""


def action_editor_reader(journal, number):
    return (journal.get_action_editors_id(number)
            if journal.settings.get('action_editor_paper_visibility', 'assigned_only') == 'assigned_only'
            else journal.get_action_editors_id())
