def expire_post_decision_invitations(client, journal, submission):
    number = submission.number
    paper_prefix = f'{journal.venue_id}/Paper{number}'
    now = openreview.tools.datetime_millis(datetime.datetime.now())

    def set_invitation_expiration_date(invitation_id, expiration_date):
        # OpenReview-web still displays expired invitations to users with
        # details.writable. ddate removes final post-decision actions from
        # the forum surface instead of merely styling them as expired. Keep
        # expdate equal to ddate so audit/reporting has one terminal date.
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=openreview.api.Invitation(
                id=invitation_id,
                signatures=[journal.venue_id],
                expdate=expiration_date,
                ddate=expiration_date
            ),
            replacement=False
        )

    invitation_ids = {
        journal.get_review_id(number),
        journal.get_reviewer_assignment_id(number),
        journal.get_ae_decision_id(number),
        f'{paper_prefix}/-/Assign_Action_Editor',
        f'{paper_prefix}/-/Decision_Approval',
        f'{paper_prefix}/-/Revision',
        f'{paper_prefix}/-/Reviewer_Rating',
        f'{paper_prefix}/-/Contact_AE'
    }

    post_decision_suffixes = (
        '/-/Review',
        '/Reviewers/-/Assignment',
        '/-/Assign_Action_Editor',
        '/-/Decision',
        '/-/Decision_Approval',
        '/-/Revision',
        '/-/Reviewer_Rating',
        '/-/Contact_AE'
    )

    try:
        for live_invitation in client.get_all_invitations(prefix=paper_prefix):
            if live_invitation.id.endswith(post_decision_suffixes):
                invitation_ids.add(live_invitation.id)
    except Exception as error:
        print(f'Could not list post-decision invitations for {paper_prefix}: {error}')

    for invitation_id in sorted(invitation_ids):
        try:
            set_invitation_expiration_date(invitation_id, now)
        except Exception as error:
            print(f'Could not deactivate {invitation_id}: {error}')


def format_openreview_month_year(timestamp_millis):
    date = datetime.datetime.fromtimestamp(timestamp_millis / 1000.0, datetime.timezone.utc)
    return f'{date.month}/{date.year % 100:02d}'


def get_content_value(note, field_name):
    return note.content.get(field_name, {}).get('value')


reviewer_assignment_edges_namespace = {'openreview': openreview}
exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_assignment_edges.py}}", reviewer_assignment_edges_namespace)


def create_decision_reviewer_rating_invitations(client, journal, submission, decision):
    import datetime

    rating_page_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/rating/reviewer_rating_page.py}}", rating_page_namespace)
    refresh_reviewer_rating_page = rating_page_namespace['refresh_reviewer_rating_page']
    due_date_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/review_due_date_helpers.py}}", due_date_namespace)

    def active_reviewer_edges():
        return due_date_namespace['active_reviewer_assignment_edges'](client, journal, submission)

    def reviewer_signature_by_member():
        signatures = {}
        active_reviewer_tails = {edge.tail for edge in active_reviewer_edges() if edge.tail}
        try:
            for group in client.get_groups(prefix=f'{journal.venue_id}/Paper{submission.number}/Reviewer_'):
                if group.id.endswith('/Reviewer_Scoring_Input'):
                    continue
                for member in group.members or []:
                    if member in active_reviewer_tails:
                        signatures[member] = group.id
        except Exception as error:
            print(f'Could not load anonymous reviewer groups for Paper{submission.number}: {error}')
        return signatures

    def review_by_signature():
        reviews = {}
        try:
            for review in client.get_notes(forum=submission.id, invitation=journal.get_review_id(number=submission.number)):
                if review.ddate:
                    continue
                for signature in review.signatures or []:
                    reviews[signature] = review
        except Exception as error:
            print(f'Could not load submitted reviews for Paper{submission.number}: {error}')
        return reviews

    def effective_review_due_date(reviewer_edge):
        return due_date_namespace['effective_review_due_date_for_edge'](
            client,
            journal,
            submission,
            reviewer_edge
        )

    def derive_timeliness(review, review_due_date):
        timeliness_grace_period_millis = 7 * 24 * 60 * 60 * 1000
        review_due_date_with_grace = review_due_date + timeliness_grace_period_millis if review_due_date else None
        decision_time = decision.tcdate or decision.cdate
        decision_before_due = decision_time and review_due_date and decision_time <= review_due_date
        if not review:
            return 'Review not expected' if decision_before_due else 'Past due'
        if decision_before_due and review.tcdate > decision_time:
            return 'Review not expected'
        return 'Past due' if review_due_date_with_grace and review.tcdate > review_due_date_with_grace else 'On time'

    def set_reviewer_rating_defaults(rating_invitation_id, default_rating, default_timeliness, reviewer_profile_id, review_note_id):
        try:
            rating_invitation = client.get_invitation(rating_invitation_id)
            note_content = rating_invitation.edit['note']['content']
            note_content.setdefault('resubmission_auto_assignment', {
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
            })
            note_content['rating']['value']['param']['default'] = default_rating
            note_content['timeliness']['value']['param']['default'] = default_timeliness
            note_content['resubmission_auto_assignment']['value']['param'].pop('default', None)
            note_content['reviewer_anon_id']['value']['param']['default'] = rating_invitation_id.split('/Reviewer_')[-1].split('/')[0]
            note_content['reviewer_profile_id']['value']['param']['default'] = reviewer_profile_id or ''
            note_content['review_note_id']['value']['param']['default'] = review_note_id or ''
            client.post_invitation_edit(
                invitations=journal.get_meta_invitation_id(),
                signatures=[journal.venue_id],
                invitation=rating_invitation,
                replacement=True
            )
            review = client.get_note(review_note_id) if review_note_id else None
            refresh_reviewer_rating_page(client, journal, submission, rating_invitation, review)
        except Exception as error:
            print(f'Could not set reviewer rating defaults for {rating_invitation_id}: {error}')

    try:
        existing_rating_replies = client.get_note(submission.id, details='replies').details.get('replies', [])
        rated_invitation_ids = {
            reply['invitations'][0]
            for reply in existing_rating_replies
            if reply.get('invitations') and reply['invitations'][0].endswith('/-/Rating')
        }
    except Exception as error:
        print(f'Could not load existing reviewer rating replies for Paper{submission.number}: {error}')
        rated_invitation_ids = set()

    signatures_by_member = reviewer_signature_by_member()
    reviews_by_signature = review_by_signature()
    rating_duedate = openreview.tools.datetime_millis(datetime.datetime.now()) + 7 * 24 * 60 * 60 * 1000
    created_or_refreshed = False

    for reviewer_edge in active_reviewer_edges():
        reviewer_signature = signatures_by_member.get(reviewer_edge.tail)
        if not reviewer_signature or '/Reviewer_' not in reviewer_signature:
            print(f'Could not find anonymous reviewer signature for {reviewer_edge.tail} on Paper{submission.number}')
            continue
        rating_invitation_id = f'{reviewer_signature}/-/Rating'
        if rating_invitation_id in rated_invitation_ids:
            continue
        reviewer_anon_id = reviewer_signature.split('/Reviewer_')[-1]
        review = reviews_by_signature.get(reviewer_signature)
        review_note_id = review.id if review else ''
        replyto_id = review.id if review else decision.id
        review_due_date = effective_review_due_date(reviewer_edge)
        default_timeliness = derive_timeliness(review, review_due_date)
        default_rating = 'Report problem' if not review and default_timeliness == 'Past due' else 'No rating'
        client.post_invitation_edit(
            invitations=f'{journal.venue_id}/-/Rating',
            signatures=[journal.venue_id],
            content={
                'noteNumber': { 'value': submission.number },
                'noteId': { 'value': submission.id },
                'replytoId': { 'value': replyto_id },
                'signature': { 'value': reviewer_signature },
                'duedate': { 'value': rating_duedate },
                'reviewerAnonId': { 'value': reviewer_anon_id },
                'reviewerProfileId': { 'value': reviewer_edge.tail or '' },
                'reviewNoteId': { 'value': review_note_id }
            },
            replacement=True
        )
        set_reviewer_rating_defaults(rating_invitation_id, default_rating, default_timeliness, reviewer_edge.tail, review_note_id)
        created_or_refreshed = True

    return created_or_refreshed


def get_previous_submission_from_url(client, previous_url):
    if not previous_url or previous_url == 'N/A' or 'forum?id=' not in previous_url:
        return None
    note_id = previous_url.split('forum?id=', 1)[1].split('&', 1)[0]
    if not note_id:
        return None
    return client.get_note(note_id)


def get_submission_chain(client, submission):
    chain = [submission]
    seen_note_ids = {submission.id}
    current = submission
    while True:
        previous_url = get_content_value(current, 'previous_JMLR_submission_URL')
        try:
            previous = get_previous_submission_from_url(client, previous_url)
        except Exception as error:
            print(f'Could not resolve previous submission for camera-ready dates: {error}')
            return chain
        if not previous or previous.id in seen_note_ids:
            return chain
        chain.append(previous)
        seen_note_ids.add(previous.id)
        current = previous


def build_openreview_dates_block(client, submission, decision):
    chain = get_submission_chain(client, submission)
    original_submission = chain[-1]
    first_revision = chain[-2] if len(chain) > 1 else None
    accepted_timestamp = decision.tcdate or decision.cdate
    submitted = format_openreview_month_year(original_submission.tcdate or original_submission.cdate)
    revised = format_openreview_month_year((first_revision.tcdate or first_revision.cdate) if first_revision else accepted_timestamp)
    accepted = format_openreview_month_year(accepted_timestamp)
    year = datetime.datetime.fromtimestamp(accepted_timestamp / 1000.0, datetime.timezone.utc).year
    paper_id = build_jmlr_publication_id(year, submission.number)
    return (
        '\\jmlropenreviewdates{\n'
        f'  submitted = {{{submitted}}},\n'
        f'  revised = {{{revised}}},\n'
        f'  accepted = {{{accepted}}},\n'
        f'  paperid = {{{paper_id}}}\n'
        '}'
    )


def build_jmlr_publication_id(year, paper_number):
    return f'{year % 100:02d}-{paper_number % 100000:05d}'


camera_ready_metadata_namespace = {'datetime': datetime}
exec("{{PYTHON_SCRIPT_JSON:invitations/venue/camera_ready_publication_metadata.py}}", camera_ready_metadata_namespace)
build_openreview_dates_block = camera_ready_metadata_namespace['build_openreview_dates_block']
build_jmlr_publication_id = camera_ready_metadata_namespace['build_jmlr_publication_id']


def update_camera_ready_revision_guidance(client, journal, submission, decision):
    invitation_id = f'{journal.venue_id}/Paper{submission.number}/-/Camera_Ready_Revision'
    dates_block = build_openreview_dates_block(client, submission, decision)
    latex_guidance = (
        '\n\nLaTeX metadata:\n'
        '- In your LaTeX source, use this generated OpenReview metadata block exactly as shown:\n\n'
        f'{dates_block}\n\n'
        '- The JMLR publication number uses the accepted year and the last five digits of the OpenReview paper number.\n'
        '- Your camera-ready version requires approval from your Action Editor before publication.'
    )
    try:
        revision_invitation = client.get_invitation(invitation_id)
        pdf_field = revision_invitation.edit['note']['content']['pdf']
        base_description = pdf_field.get('description', '').split('\n\nLaTeX metadata:', 1)[0]
        base_description = base_description.split(' In your LaTeX source, use this generated OpenReview metadata block exactly as shown:', 1)[0].rstrip()
        pdf_field['description'] = base_description + latex_guidance
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=revision_invitation,
            replacement=True
        )
    except Exception as error:
        print(f'Could not update camera-ready LaTeX guidance for {invitation_id}: {error}')


def camera_ready_revision_action_content(journal, submission):
    author_group_id = journal.get_authors_id(number=submission.number)
    invitation_id = journal.get_camera_ready_revision_id(number=submission.number)
    action_url = (
        f'{{SITE_URL}}/forum?id={submission.id}'
        f'&noteId={submission.id}'
        f'&invitationId={invitation_id}'
        f'&role_context={author_group_id}'
    )
    return {
        'camera_ready_revision_action': {
            'value': f'[Camera Ready Revision]({action_url})',
            'readers': [author_group_id]
        }
    }


def create_author_resubmission_invitation(client, journal, submission):
    import urllib.parse

    invitation_id = f'{journal.venue_id}/Paper{submission.number}/-/Resubmission'
    authors_id = journal.get_authors_id(submission.number)
    editors_in_chief_id = journal.get_editors_in_chief_id()
    action_editors_id = journal.get_action_editors_id(submission.number)
    resubmission_readers = [editors_in_chief_id, action_editors_id, authors_id]
    previous_url = f'{{SITE_URL}}/forum?id={submission.id}'
    resubmission_url = (
        f'{{SITE_URL}}/group?'
        + urllib.parse.urlencode({
            'id': journal.venue_id,
            'newSubmission': '1',
            'previous_JMLR_submission_number': str(submission.number),
            'previous_JMLR_submission_URL': previous_url
        })
        + '#new-submission'
    )
    description = (
        f'<p>Submit a revised version of JMLR Paper {submission.number}: '
        f'{submission.content["title"]["value"]}.</p>'
        '<p>Only author ordering changes are allowed for resubmissions. Adding, removing, replacing, '
        'renaming, or otherwise changing authors is not allowed. Impermissible author changes may cause '
        'desk rejection or later rejection at editorial discretion.</p>'
        f'<p><a class="btn btn-primary" href="{resubmission_url}">Start Resubmission</a></p>'
    )
    redirect_web = (
        'var JMLR_RESUBMISSION_URL = ' + repr(resubmission_url) + ';\n'
        'if (typeof window !== "undefined") { window.location.href = JMLR_RESUBMISSION_URL; }\n'
        'return "<p>Redirecting to the JMLR resubmission form.</p>" + '
        '"<p><a class=\\"btn btn-primary\\" href=\\"" + JMLR_RESUBMISSION_URL + "\\">Start Resubmission</a></p>";'
    )
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        readers=resubmission_readers,
        writers=[journal.venue_id],
        invitation=openreview.api.Invitation(
            id=invitation_id,
            signatures=[journal.venue_id],
            readers=resubmission_readers,
            writers=[journal.venue_id],
            invitees=[authors_id],
            description=description,
            web=redirect_web,
            edit={
                'signatures': [authors_id],
                'readers': resubmission_readers,
                'writers': [journal.venue_id],
                'note': {
                    'forum': submission.id,
                    'replyto': submission.id,
                    'signatures': [authors_id],
                    'readers': resubmission_readers,
                    'writers': [journal.venue_id],
                    'content': {
                        'resubmission_url': {
                            'order': 1,
                            'description': 'Open the JMLR resubmission form for this paper.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const': resubmission_url,
                                    'hidden': True
                                }
                            }
                        }
                    }
                }
            },
            process=(
                'def process(client, edit, invitation):\n'
                '    import datetime\n'
                '    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")\n'
                '    helper_note = client.get_note(edit.note.id)\n'
                '    client.post_note_edit(\n'
                '        invitation=journal.get_meta_invitation_id(),\n'
                '        signatures=[journal.venue_id],\n'
                '        note=openreview.api.Note(\n'
                '            id=helper_note.id,\n'
                '            readers=helper_note.readers or [],\n'
                '            writers=[journal.venue_id],\n'
                '            ddate=openreview.tools.datetime_millis(datetime.datetime.now())\n'
                '        )\n'
                '    )\n'
            )
        ),
        replacement=True
    )



def process(client, edit, invitation):

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    venue_id = journal.venue_id
    editors_in_chief_id = f'{venue_id}/Editors_In_Chief'
    super_child_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/super_invitation_child_edit.py}}", super_child_namespace)
    def editor_readers(readers):
        if readers == ['everyone']:
            return [editors_in_chief_id]
        return readers + [editors_in_chief_id] if editors_in_chief_id not in readers else readers

    def unique_values(values):
        result = []
        for value in values:
            if value and value not in result:
                result.append(value)
        return result

    def decision_release_readers(submission):
        return unique_values([
            journal.get_editors_in_chief_id(),
            editors_in_chief_id,
            journal.get_action_editors_id(submission.number),
            journal.get_reviewers_id(submission.number),
            journal.get_authors_id(submission.number)
        ])

    def release_decision_note(submission, decision):
        readers = decision_release_readers(submission)
        release_invitation_id = journal.get_release_decision_id(number=submission.number)
        try:
            release_invitation = client.get_invitation(release_invitation_id)
        except Exception:
            release_invitation = openreview.api.Invitation(id=release_invitation_id)
        release_invitation.signatures = [venue_id]
        release_invitation.readers = [venue_id]
        release_invitation.writers = [venue_id]
        release_invitation.invitees = [venue_id]
        release_invitation.edit = getattr(release_invitation, 'edit', None) or {
            'signatures': [venue_id],
            'readers': readers,
            'writers': [venue_id],
            'note': {
                'id': {
                    'param': {
                        'withInvitation': journal.get_ae_decision_id(number=submission.number)
                    }
                }
            }
        }
        if hasattr(release_invitation, 'ddate'):
            release_invitation.ddate = None
        if hasattr(release_invitation, 'expdate'):
            release_invitation.expdate = None
        release_invitation.edit['readers'] = readers
        release_invitation.edit['nonreaders'] = []
        release_invitation.edit['note']['readers'] = readers
        release_invitation.edit['note']['nonreaders'] = []
        release_invitation.edit['note']['writers'] = [venue_id]
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[venue_id],
            invitation=release_invitation,
            replacement=True
        )
        client.post_note_edit(
            invitation=journal.get_release_decision_id(number=submission.number),
            signatures=[venue_id],
            note=openreview.api.Note(
                id=decision.id
            )
        )

    def run_optional_reviewer_rating_setup(submission, decision):
        try:
            rating_prompt_namespace = {'openreview': openreview}
            exec("{{PYTHON_SCRIPT_JSON:invitations/venue/rating/status_prompt.py}}", rating_prompt_namespace)
            rating_launcher_namespace = {'openreview': openreview}
            exec("{{PYTHON_SCRIPT_JSON:invitations/venue/rating/reviewer_rating_launcher.py}}", rating_launcher_namespace)
            print('Create or refresh reviewer rating actions for all assigned reviewers')
            create_decision_reviewer_rating_invitations(client, journal, submission, decision)
            rating_launcher_namespace['refresh_reviewer_rating_launcher'](client, journal, submission)
            rating_prompt_namespace['refresh_pending_reviewer_rating_prompt'](client, journal, submission)
        except Exception as error:
            print(f'Reviewer rating setup is optional and did not block decision finalization for Paper{submission.number}: {error}')

    def release_assignment_loads_after_decision(submission):
        def release_reviewer_pending_load(reviewer_id):
            pending_review_edges = client.get_edges(
                invitation=journal.get_reviewer_pending_review_id(),
                tail=reviewer_id
            )
            pending_review_edge = pending_review_edges[0] if pending_review_edges else None
            if pending_review_edge and pending_review_edge.weight and pending_review_edge.weight > 0:
                client.post_edge(openreview.api.Edge(
                    id=pending_review_edge.id,
                    invitation=journal.get_reviewer_pending_review_id(),
                    signatures=pending_review_edge.signatures or [venue_id],
                    head=pending_review_edge.head,
                    tail=pending_review_edge.tail,
                    weight=pending_review_edge.weight - 1
                ))

        print('Release reviewer pending-review loads after decision')
        reviewer_assignment_edges = reviewer_assignment_edges_namespace['reviewer_assignment_edges_for_submission'](
            client,
            journal,
            submission,
            active_only=True,
        )
        released_reviewer_ids = set()
        for reviewer_assignment_edge in reviewer_assignment_edges:
            if reviewer_assignment_edge.tail in released_reviewer_ids:
                continue
            released_reviewer_ids.add(reviewer_assignment_edge.tail)
            release_reviewer_pending_load(reviewer_assignment_edge.tail)

    def run_optional_assignment_load_release(submission):
        try:
            release_assignment_loads_after_decision(submission)
        except Exception as error:
            print(f'Assignment load release is optional and did not block decision finalization for Paper{submission.number}: {error}')

    decision_approval = client.get_note(edit.note.id)
    decision = client.get_note(edit.note.replyto)

    ## On update or delete return
    if decision_approval.tcdate != decision_approval.tmdate:
        return

    submission = client.get_note(decision.forum)

    ## Make the decision public
    print('Make decision public')
    release_decision_note(submission, decision)
    run_optional_reviewer_rating_setup(submission, decision)
    run_optional_assignment_load_release(submission)

    if journal.should_archive_previous_year_assignments():
        year_submitted = datetime.datetime.fromtimestamp(submission.tcdate/1000.0).year
        current_year = datetime.datetime.now().year

        if year_submitted < current_year:
            #if submission was submitted previous year, archive assignments once it is finished
            print('Archiving assignments!')
            submission_ae_assignments = client.get_edges(
                invitation=journal.get_action_editors_id(number=submission.number) + '/-/Assignment',
                head=submission.id
            )
            submission_rev_assignments = reviewer_assignment_edges_namespace['reviewer_assignment_edges_for_submission'](
                client,
                journal,
                submission,
                active_only=True,
            )

            for ae_assignment_edge in submission_ae_assignments:
                print(ae_assignment_edge.head, ae_assignment_edge.tail)
                archived_edge = openreview.api.Edge(
                    invitation=journal.get_ae_assignment_id(archived=True),
                    cdate=ae_assignment_edge.cdate,
                    head=ae_assignment_edge.head,
                    tail=ae_assignment_edge.tail,
                    weight=ae_assignment_edge.weight,
                    label=ae_assignment_edge.label
                )
                client.post_edge(archived_edge)
                client.delete_edges(invitation=ae_assignment_edge.invitation, head=ae_assignment_edge.head, tail=ae_assignment_edge.tail, soft_delete=True, wait_to_finish=True)
            
            client.delete_edges(invitation=journal.get_ae_affinity_score_id(), head=submission.id, soft_delete=True, wait_to_finish=True)
            client.delete_edges(invitation=journal.get_ae_recommendation_id(), head=submission.id, soft_delete=True, wait_to_finish=True)
            client.delete_edges(invitation=journal.get_ae_conflict_id(), head=submission.id, soft_delete=True, wait_to_finish=True)
            client.delete_edges(invitation=journal.get_ae_aggregate_score_id(), head=submission.id, soft_delete=True, wait_to_finish=True)
            client.delete_edges(invitation=journal.get_ae_resubmission_score_id(), head=submission.id, soft_delete=True, wait_to_finish=True)

            for reviewer_assignment_edge in submission_rev_assignments:
                print(reviewer_assignment_edge.head, reviewer_assignment_edge.tail)
                archived_edge = openreview.api.Edge(
                    invitation=journal.get_reviewer_assignment_id(archived=True),
                    cdate=reviewer_assignment_edge.cdate,
                    head=reviewer_assignment_edge.head,
                    tail=reviewer_assignment_edge.tail,
                    weight=reviewer_assignment_edge.weight,
                    label=reviewer_assignment_edge.label,
                    signatures=[venue_id]
                )
                client.post_edge(archived_edge)
                client.delete_edges(invitation=reviewer_assignment_edge.invitation, head=reviewer_assignment_edge.head, tail=reviewer_assignment_edge.tail, soft_delete=True, wait_to_finish=True)

            client.delete_edges(invitation=journal.get_reviewer_affinity_score_id(), head=submission.id, soft_delete=True, wait_to_finish=True)
            client.delete_edges(invitation=journal.get_reviewer_conflict_id(), head=submission.id, soft_delete=True, wait_to_finish=True)
            client.delete_edges(invitation=journal.get_reviewer_invite_assignment_id(), head=submission.id, soft_delete=True, wait_to_finish=True)

    print('Check rejection')
    print(decision.content)
    recommendation = decision.content['recommendation']['value']
    if recommendation in ['Reject with encouragement to resubmit', 'Reject without resubmission', 'Reject', 'Accept after minor revisions', 'Accept with minor revision']:
        ## Post a reject edit
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            readers=editor_readers(journal.get_under_review_submission_readers(submission.number)),
            writers=[venue_id],
            signatures=[venue_id],
            note=openreview.api.Note(
                id=submission.id,
                content={
                    '_bibtex': {
                        'value': journal.get_bibtex(submission, journal.rejected_venue_id, anonymous=True)
                    },
                    'venue': {
                        'value': f'Rejected by {journal.short_name}'
                    },
                    'venueid': {
                        'value': journal.rejected_venue_id
                    }
                }
            )
        )
        expire_post_decision_invitations(client, journal, submission)
        if recommendation in ['Reject with encouragement to resubmit', 'Accept after minor revisions', 'Accept with minor revision']:
            create_author_resubmission_invitation(client, journal, submission)
        author_group = client.get_group(journal.get_authors_id())
        if recommendation == 'Reject without resubmission':
            template = author_group.content['decision_reject_without_resubmission_email_template_script']['value']
        elif recommendation in ['Accept after minor revisions', 'Accept with minor revision']:
            template = author_group.content['decision_accept_revision_email_template_script']['value']
        else:
            template = author_group.content['decision_reject_with_resubmission_email_template_script']['value']
        message = template.format(
            short_name=journal.short_name,
            submission_id=submission.id,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
            website=journal.website,
            contact_info=journal.contact_info
        )
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=message,
            replyTo=journal.contact_info,
            signature=venue_id,
            sender=journal.get_message_sender()
        )
        return

    ## Enable Camera Ready Revision
    print('Enable Camera Ready Revision')
    expire_post_decision_invitations(client, journal, submission)
    if journal.should_skip_camera_ready_revision():
        certifications = decision.content.get('certifications', {}).get('value', [])

        content= {
            '_bibtex': {
                'value': journal.get_bibtex(submission, journal.accepted_venue_id, certifications=certifications)
            }
        }

        if certifications:
            content['certifications'] = { 'value': certifications }

        client.post_note_edit(invitation=journal.get_accepted_id(),
            signatures=[venue_id],
            note=openreview.api.Note(id=submission.id,
                pdate = openreview.tools.datetime_millis(datetime.datetime.now()),
                content= content
            )
        )
    else:
        super_child_namespace['refresh_camera_ready_revision_invitation'](client, journal, submission, journal.get_due_date(weeks = journal.get_camera_ready_period_length()))
        update_camera_ready_revision_guidance(client, journal, submission, decision)
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            readers=editor_readers(journal.get_under_review_submission_readers(submission.number)),
            writers=[venue_id],
            signatures=[venue_id],
            note=openreview.api.Note(
                id=submission.id,
                writers=[venue_id, journal.get_authors_id(number=submission.number)],
                content={
                    **camera_ready_revision_action_content(journal, submission),
                    'venue': {
                        'value': f'Camera-ready revision pending for {journal.short_name}'
                    },
                    'venueid': {
                        'value': f'{venue_id}/Camera_Ready_Revision_Pending'
                    }
                }
            )
        )

    duedate = journal.get_due_date(weeks = journal.get_camera_ready_period_length())

    ## Send email to authors
    print('Send email to authors')
    author_group = client.get_group(journal.get_authors_id())
    if recommendation in ['Accept', 'Accept as is']:
        message=author_group.content['decision_accept_as_is_email_template_script']['value'].format(
            short_name=journal.short_name,
            submission_id=submission.id,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            paper_url=f'{{SITE_URL}}/forum?id={submission.id}',
            website=journal.website,
            camera_ready_period_length=journal.get_camera_ready_period_length(),
            camera_ready_duedate=duedate.strftime("%b %d"),
            openreview_dates_block=build_openreview_dates_block(client, submission, decision),
            contact_info=journal.contact_info
        )
        client.post_message(
            invitation=journal.get_meta_invitation_id(),
            recipients=[journal.get_authors_id(number=submission.number)],
            subject=f'''[{journal.short_name}] Decision for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
            message=message,
            replyTo=journal.contact_info,
            signature=venue_id,
            sender=journal.get_message_sender()
        )
        return
