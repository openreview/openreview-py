def process(client, edit, invitation):
    venue_id='.TMLR'
    note=edit.note

    journal = openreview.journal.Journal()

    journal.invitation_builder.set_camera_ready_revision_invitation(journal, note)

    client.post_message(
        recipients=[journal.get_action_editors_id(number=note.number)],
        subject=f'''[{journal.short_name}] Evaluate reviewers and submit decision for TMLR submission {note.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

Thank you for overseeing the review process for TMLR submission "{submission.content['title']['value']}".

All reviewers have submitted their official recommendation of a decision for the submission. Therefore it is now time for you to determine a decision for the submission. Before doing so:

Make sure you have sufficiently discussed with the authors (and possibly the reviewers) any concern you may have about the submission.
Rate the quality of the reviews submitted by the reviewers. You will not be able to submit your decision until these ratings have been submitted.

We ask that you submit your decision within 1 week ({duedate.strftime("%b %d")}). To do so, please follow this link: https://openreview.net/forum?id={submission.id}

The possible decisions are:
Accept as is: once its camera ready version is submitted, the manuscript will be marked as accepted.
Accept with minor revision: to use if you wish to request some specific revisions to the manuscript, to be specified explicitly in your decision comments. These revisions will be expected from the authors when they submit their camera ready version.
Reject: the paper is rejected, but you may indicate whether you would be willing to consider a significantly revised version of the manuscript. Such a revised submission will need to be entered as a new submission, that will also provide a link to this rejected submission as well as a description of the changes made since.

Your decision may also include certification(s) recommendations for the submission (in case of an acceptance).

For more details and guidelines on performing your review, visit jmlr.org/tmlr .

We thank you for your essential contribution to TMLR!

''',
        replyTo=journal.contact_info
    )
