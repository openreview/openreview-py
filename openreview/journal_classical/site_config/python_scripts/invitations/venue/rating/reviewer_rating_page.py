def reviewer_rating_page_invitation_id(rating_invitation_id):
    return str(rating_invitation_id)


def reviewer_rating_form_url(site_url, rating_invitation_id):
    import urllib.parse

    return (
        site_url.rstrip('/')
        + '/invitation?'
        + urllib.parse.urlencode({'id': rating_invitation_id})
    )


def refresh_reviewer_rating_page(client, journal, submission, rating_invitation, review=None):
    import json
    identity_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_identity_continuity.py}}", identity_namespace)
    signature_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/anonymous_signature_helpers.py}}", signature_namespace)
    helper_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/rating/reviewer_rating_helpers.py}}", helper_namespace)
    content_value = helper_namespace['rating_content_value']
    edit_content_default = helper_namespace['rating_edit_content_default']
    review_html = helper_namespace['reviewer_rating_review_text']
    page_status_label = helper_namespace['reviewer_rating_page_status_label']

    reviewer_anon_id = (
        content_value(rating_invitation, 'reviewerAnonId')
        or edit_content_default(rating_invitation, 'reviewer_anon_id')
        or rating_invitation.id.split('/Reviewer_')[-1].split('/')[0]
    )
    reviewer_label = identity_namespace['reviewer_display_label'](
        submission,
        reviewer_profile_id=content_value(rating_invitation, 'reviewerProfileId') or edit_content_default(rating_invitation, 'reviewer_profile_id'),
        current_anon_id=reviewer_anon_id
    )
    default_timeliness = (
        content_value(rating_invitation, 'defaultTimeliness')
        or edit_content_default(rating_invitation, 'timeliness')
    )
    if not review:
        review_note_id = (
            content_value(rating_invitation, 'reviewNoteId')
            or edit_content_default(rating_invitation, 'review_note_id')
        )
        if review_note_id:
            try:
                review = client.get_note(review_note_id)
            except Exception as error:
                print(f'Could not load reviewer rating context review note {review_note_id}: {error}')
    if not review:
        reviewer_signature = rating_invitation.id.rsplit('/-/Rating', 1)[0]
        try:
            for candidate in client.get_notes(forum=submission.id, invitation=journal.get_review_id(number=submission.number)):
                if reviewer_signature in (candidate.signatures or []):
                    review = candidate
                    break
        except Exception as error:
            print(f'Could not load reviewer rating context reviews for Paper{submission.number}: {error}')
    status_label = page_status_label(review, default_timeliness)

    context_text = (
        str(reviewer_label) + ': ' + status_label
        + '\n\n'
        + review_html(review, reviewer_label)
        + '\n\nUse this form to record reviewer quality, timeliness, problem reports, and optional comments.'
    )

    content = rating_invitation.edit.get('note', {}).get('content', {}) if isinstance(rating_invitation.edit, dict) else {}
    ae_signature_ids = []
    try:
        action_editors = set(client.get_group(journal.get_action_editors_id(submission.number)).members or [])
        for group in client.get_groups(prefix=f'{journal.venue_id}/Paper{submission.number}/Action_Editor_'):
            if action_editors.intersection(set(group.members or [])):
                ae_signature_ids.append(group.id)
    except Exception as error:
        print(f'Could not load action editor signatures for reviewer rating on Paper{submission.number}: {error}')
    if ae_signature_ids and isinstance(rating_invitation.edit, dict):
        signature_namespace['apply_anonymous_action_editor_signatures'](rating_invitation, journal, submission.number)
        action_editor_signature = sorted(ae_signature_ids)[0]
    else:
        action_editor_signature = ''
    rating_invitation.preprocess = "{{PYTHON_SCRIPT_JSON:invitations/venue/rating/edit_preprocess.py}}"
    if 'rating' in content:
        content['rating']['order'] = 2
    if 'timeliness' in content:
        content['timeliness']['order'] = 3
    content['resubmission_auto_assignment'] = {
        'order': 4,
        'description': 'Select this reviewer for automatic assignment if the paper is resubmitted.',
        'value': {
            'param': {
                'type': 'string',
                'enum': [
                    'Select this reviewer for automatic assignment if the paper is resubmitted.'
                ],
                'input': 'checkbox',
                'optional': True,
                'deletable': True
            }
        }
    }
    if 'comment' in content:
        content['comment']['order'] = 5
    rating_invitation.process = """def process(client, edit, invitation):
    import datetime

    meta_invitation = client.get_invitation(invitation.invitations[0])
    script = getattr(meta_invitation, 'process', None)
    if not script:
        script = meta_invitation.content["process_script"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime
    }
    exec(script, funcs)
    funcs['process'](client, edit, invitation)
"""
    content['reviewer_rating_context'] = {
        'order': 1,
        'description': context_text,
        'value': {
            'param': {
                'type': 'string',
                'const': f'{reviewer_label} rating context'
            }
        }
    }
    site_url = "{{SITE_URL}}".rstrip("/")
    rating_invitation.web = (
        "{{PYTHON_SCRIPT_JSON:invitations/venue/rating/reviewer_rating_page_web.js}}"
        .replace('__JMLR_RATING_PAGE_JSON__', json.dumps({
            'ratingInvitationId': rating_invitation.id,
            'forumId': rating_invitation.edit.get('note', {}).get('forum'),
            'replytoId': rating_invitation.edit.get('note', {}).get('replyto'),
            'reviewerAnonId': reviewer_anon_id,
            'reviewerLabel': reviewer_label,
            'reviewerProfileId': edit_content_default(rating_invitation, 'reviewer_profile_id'),
            'reviewNoteId': content_value(rating_invitation, 'reviewNoteId') or edit_content_default(rating_invitation, 'review_note_id'),
            'defaultRating': content_value(rating_invitation, 'defaultRating') or edit_content_default(rating_invitation, 'rating') or 'No rating',
            'defaultTimeliness': default_timeliness or 'On time',
            'defaultResubmissionAutoAssignment': False,
            'contextText': context_text,
            'actionEditorSignature': action_editor_signature,
            'readers': rating_invitation.edit.get('note', {}).get('readers', []),
            'nonreaders': rating_invitation.edit.get('note', {}).get('nonreaders', []),
            'writers': rating_invitation.edit.get('note', {}).get('writers', []),
            'returnUrl': site_url + '/forum?id=' + str(rating_invitation.edit.get('note', {}).get('forum') or '')
        }))
    )
    rating_invitation.maxReplies = max(getattr(rating_invitation, 'maxReplies', 0) or 0, 100)
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=rating_invitation,
        replacement=True
    )


def expire_reviewer_rating_page(client, journal, rating_invitation_id, now):
    return
