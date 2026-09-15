import pytest

from openreview.journal import Journal, JournalRequest
from openreview.journal.invitation import InvitationBuilder


def make_journal(settings=None):
    return Journal(
        client=None,
        venue_id='TestJournal',
        secret_key='secret',
        contact_info='editors@example.com',
        full_name='Test Journal',
        short_name='TJ',
        settings=settings or {},
    )


def test_missing_setting_preserves_private_reader_lists():
    journal = make_journal({
        'submission_public': False,
        'release_submission_after_acceptance': False,
    })

    assert journal.get_under_review_submission_readers(7) == [
        'TestJournal',
        'TestJournal/Action_Editors',
        'TestJournal/Paper7/Reviewers',
        'TestJournal/Paper7/Authors',
    ]
    assert journal.get_release_review_readers(7) == [
        'TestJournal/Editors_In_Chief',
        'TestJournal/Action_Editors',
        'TestJournal/Paper7/Reviewers',
        'TestJournal/Paper7/Authors',
    ]
    assert journal.get_release_decision_readers(7) == [
        'TestJournal/Editors_In_Chief',
        'TestJournal/Action_Editors',
        'TestJournal/Paper7/Reviewers',
        'TestJournal/Paper7/Authors',
    ]
    assert journal.get_release_authors_readers(7) == [
        'TestJournal/Editors_In_Chief',
        'TestJournal/Action_Editors',
        'TestJournal/Paper7/Authors',
    ]
    assert journal.get_official_comment_readers(7) == [
        'TestJournal/Editors_In_Chief',
        'TestJournal/Action_Editors',
        'TestJournal/Paper7/Action_Editors',
        'TestJournal/Paper7/Reviewers',
        'TestJournal/Paper7/Reviewer_.*',
        'TestJournal/Paper7/Authors',
    ]


def test_all_setting_matches_missing_setting():
    base = {
        'submission_public': False,
        'release_submission_after_acceptance': False,
    }
    missing = make_journal(base)
    explicit = make_journal({**base, 'action_editor_paper_visibility': 'all'})

    reader_methods = (
        'get_under_review_submission_readers',
        'get_release_review_readers',
        'get_release_decision_readers',
        'get_release_authors_readers',
        'get_official_comment_readers',
    )
    for method_name in reader_methods:
        assert getattr(explicit, method_name)(7) == getattr(missing, method_name)(7)


def test_assigned_only_uses_dynamic_paper_group_for_private_records():
    journal = make_journal({
        'submission_public': False,
        'release_submission_after_acceptance': False,
        'action_editor_paper_visibility': 'assigned_only',
    })
    paper_ae = 'TestJournal/Paper7/Action_Editors'

    for readers in (
        journal.get_under_review_submission_readers(7),
        journal.get_release_review_readers(7),
        journal.get_release_decision_readers(7),
        journal.get_release_authors_readers(7),
        journal.get_official_comment_readers(7),
    ):
        assert paper_ae in readers
        assert 'TestJournal/Action_Editors' not in readers

    assert journal.get_official_comment_readers(7).count(paper_ae) == 1


def test_assigned_only_does_not_make_public_records_private():
    journal = make_journal({
        'submission_public': True,
        'action_editor_paper_visibility': 'assigned_only',
    })

    assert journal.get_under_review_submission_readers(7) == ['everyone']
    assert journal.get_release_review_readers(7) == ['everyone']
    assert journal.get_release_decision_readers(7) == ['everyone']
    assert journal.get_release_authors_readers(7) == ['everyone']


def test_invalid_setting_fails_when_journal_is_constructed():
    with pytest.raises(
        ValueError,
        match='action_editor_paper_visibility must be one of: all, assigned_only',
    ):
        make_journal({'action_editor_paper_visibility': 'paper_chairs'})


def test_journal_request_default_exposes_legacy_mode():
    request = object.__new__(JournalRequest)
    settings = request.get_request_form_content()['settings']['value']['param']['default']

    assert settings['action_editor_paper_visibility'] == 'all'


def capture_invitation(settings, method_name):
    journal = make_journal(settings)
    builder = object.__new__(InvitationBuilder)
    builder.journal = journal
    builder.process_script = 'native process'
    captured = []
    builder.save_super_invitation = lambda *args: captured.append(args)
    builder.save_invitation = lambda invitation: captured.append((invitation,))
    builder.get_process_content = lambda path: path

    getattr(builder, method_name)()

    assert len(captured) == 1
    return captured[0][-1]


def test_under_review_schema_changes_only_private_readers():
    common = {'submission_public': False}
    baseline = capture_invitation(common, 'set_under_review_invitation')
    assigned = capture_invitation(
        {**common, 'action_editor_paper_visibility': 'assigned_only'},
        'set_under_review_invitation',
    )

    assert baseline.invitees == assigned.invitees
    assert baseline.writers == assigned.writers
    assert baseline.signatures == assigned.signatures
    assert baseline.edit['writers'] == assigned.edit['writers']
    assert baseline.edit['signatures'] == assigned.edit['signatures']
    assert baseline.edit['readers'][1] == 'TestJournal/Action_Editors'
    assert assigned.edit['readers'][1] == (
        'TestJournal/Paper${2/note/number}/Action_Editors'
    )
    assert baseline.edit['note']['readers'][1] == 'TestJournal/Action_Editors'
    assert assigned.edit['note']['readers'][1] == (
        'TestJournal/Paper${2/number}/Action_Editors'
    )


def test_decision_release_schema_changes_only_note_readers():
    common = {
        'submission_public': False,
        'release_submission_after_acceptance': False,
    }
    baseline = capture_invitation(common, 'set_decision_release_invitation')
    assigned = capture_invitation(
        {**common, 'action_editor_paper_visibility': 'assigned_only'},
        'set_decision_release_invitation',
    )

    for field in ('invitees', 'writers', 'signatures'):
        assert baseline[field] == assigned[field]
    assert baseline['edit']['writers'] == assigned['edit']['writers']
    assert baseline['edit']['signatures'] == assigned['edit']['signatures']
    assert baseline['edit']['note']['readers'][1] == 'TestJournal/Action_Editors'
    assert assigned['edit']['note']['readers'][1] == (
        'TestJournal/Paper${5/content/noteNumber/value}/Action_Editors'
    )
