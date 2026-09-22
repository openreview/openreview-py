import openreview
import pytest
import datetime
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.venue import Venue
from openreview.stages import SubmissionStage


class TestSignatureTransitiveMembers():
    '''Reviewer identities are visible to the program chairs only, and an area chair is assigned to the same paper as a
    reviewer. The area chair can read the paper's Reviewers group but is not a reader of the reviewer's anonymous id.
    The tests cover two ways the area chair used to learn which reviewer is on the paper.'''

    @pytest.fixture(scope="class")
    def venue(self, openreview_client):
        conference_id = 'TestIdentityVenue.cc'

        venue = Venue(openreview_client, conference_id, 'openreview.net/Support')
        venue.invitation_builder.update_wait_time = 2000
        venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"
        venue.automatic_reviewer_assignment = True
        venue.use_area_chairs = True
        venue.name = 'Identity Venue V2'
        venue.short_name = 'Identity Venue 22'
        venue.website = 'testvenue.org'
        venue.contact = 'testvenue@contact.com'
        venue.reviewer_identity_readers = [openreview.stages.IdentityReaders.PROGRAM_CHAIRS]

        now = datetime.datetime.now()
        venue.submission_stage = SubmissionStage(
            double_blind=True,
            due_date=now + datetime.timedelta(minutes = 30),
            readers=[SubmissionStage.Readers.EVERYONE],
            force_profiles=True,
            remove_fields=['abstract']
        )

        venue.review_stage = openreview.stages.ReviewStage(start_date=now + datetime.timedelta(minutes = 4), due_date=now + datetime.timedelta(minutes = 40))

        return venue

    def test_setup(self, venue, openreview_client, helpers):

        venue.setup(program_chair_ids=['identity_pc@mail.com'])
        venue.create_submission_stage()
        venue.create_review_stage()
        assert openreview_client.get_group('TestIdentityVenue.cc')

        helpers.create_user('identity_pc@mail.com', 'PC Identity', 'One')
        helpers.create_user('identity_reviewer@mail.com', 'Reviewer Identity', 'One')
        helpers.create_user('identity_ac@mail.com', 'AreaChair Identity', 'One')
        helpers.create_user('identity_author@mail.com', 'Author Identity', 'One')

        openreview_client.add_members_to_group('TestIdentityVenue.cc/Reviewers', ['~Reviewer_Identity_One1'])
        openreview_client.add_members_to_group('TestIdentityVenue.cc/Area_Chairs', ['~AreaChair_Identity_One1'])

    def test_submission_stage(self, venue, openreview_client, helpers):

        author_client = OpenReviewClient(username='identity_author@mail.com', password=helpers.strong_password)

        submission_note_1 = author_client.post_note_edit(
            invitation='TestIdentityVenue.cc/-/Submission',
            signatures= ['~Author_Identity_One1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 1 Title' },
                    'authors': { 'value': ['Author Identity One']},
                    'authorids': { 'value': ['~Author_Identity_One1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id'])

    def test_post_submission_stage(self, venue, openreview_client, helpers):

        venue.submission_stage.readers = [SubmissionStage.Readers.REVIEWERS, SubmissionStage.Readers.AREA_CHAIRS]
        venue.submission_stage.start_date = datetime.datetime.now() - datetime.timedelta(seconds = 5)
        venue.submission_stage.due_date = datetime.datetime.now() + datetime.timedelta(seconds = 10)
        venue.submission_stage.exp_date = datetime.datetime.now() + datetime.timedelta(seconds = 90)
        venue.create_submission_stage()

        helpers.await_queue_edit(openreview_client, 'TestIdentityVenue.cc/-/Post_Submission-0-0')
        helpers.await_queue_edit(openreview_client, 'TestIdentityVenue.cc/Reviewers/-/Submission_Group-0-0')
        helpers.await_queue_edit(openreview_client, 'TestIdentityVenue.cc/Area_Chairs/-/Submission_Group-0-0')

        assert openreview_client.get_group('TestIdentityVenue.cc/Submission1/Reviewers')
        assert openreview_client.get_group('TestIdentityVenue.cc/Submission1/Area_Chairs')

    def test_area_chair_can_get_the_anonymous_group_by_id(self, venue, openreview_client, helpers):

        openreview_client.add_members_to_group('TestIdentityVenue.cc/Submission1/Reviewers', ['~Reviewer_Identity_One1'])
        openreview_client.add_members_to_group('TestIdentityVenue.cc/Submission1/Area_Chairs', ['~AreaChair_Identity_One1'])

        # The chairs are not writers of the paper's Reviewers group, since they are not allowed to see the identities
        reviewers_group = openreview_client.get_group('TestIdentityVenue.cc/Submission1/Reviewers')
        assert reviewers_group.readers == ['TestIdentityVenue.cc', 'TestIdentityVenue.cc/Submission1/Area_Chairs', 'TestIdentityVenue.cc/Submission1/Reviewers']
        assert reviewers_group.writers == ['TestIdentityVenue.cc']

        anon_group = openreview_client.get_groups(prefix='TestIdentityVenue.cc/Submission1/Reviewer_')[0]
        assert anon_group.members == ['~Reviewer_Identity_One1']
        assert anon_group.readers == ['TestIdentityVenue.cc', 'TestIdentityVenue.cc/Program_Chairs', anon_group.id]
        assert anon_group.writers == ['TestIdentityVenue.cc']

        openreview_client.flush_members_cache('~AreaChair_Identity_One1')
        ac_client = OpenReviewClient(username='identity_ac@mail.com', password=helpers.strong_password)

        # The area chair is not a reader of the anonymous group, so it is not listed for them
        assert ac_client.get_groups(prefix='TestIdentityVenue.cc/Submission1/Reviewer_') == []

        # Issue 1: a group fetched by id is returned to its writers with its members, and the anonymous group copies
        # the writers of the paper's Reviewers group. Those used to include the area chairs, so the area chair could
        # read the reviewer's identity even though reviewer_identity_readers excludes area chairs. The chairs are
        # writers of the paper's Reviewers group only when they can see the identities now
        with pytest.raises(openreview.OpenReviewException, match=r'is not reader of'):
            ac_client.get_group(anon_group.id)

    def test_area_chair_can_get_notes_signed_by_groups_of_the_reviewer(self, venue, openreview_client, helpers):

        # open the review invitation now
        openreview_client.post_invitation_edit(
            invitations='TestIdentityVenue.cc/-/Edit',
            readers=['TestIdentityVenue.cc'],
            writers=['TestIdentityVenue.cc'],
            signatures=['TestIdentityVenue.cc'],
            invitation=openreview.api.Invitation(id='TestIdentityVenue.cc/-/Official_Review',
                signatures=['TestIdentityVenue.cc'],
                edit = {
                    'invitation': {
                        'cdate': openreview.tools.datetime_millis(datetime.datetime.now()) + 2000
                    }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, 'TestIdentityVenue.cc/-/Official_Review-0-0')
        helpers.await_queue_edit(openreview_client, 'TestIdentityVenue.cc/-/Official_Review-0-1', count=2)
        assert openreview_client.get_invitation('TestIdentityVenue.cc/Submission1/-/Official_Review')

        submission = venue.get_submissions(sort='number:asc')[0]

        reviewer_client = OpenReviewClient(username='identity_reviewer@mail.com', password=helpers.strong_password)
        anon_group_id = reviewer_client.get_groups(prefix='TestIdentityVenue.cc/Submission1/Reviewer_', signatory='~Reviewer_Identity_One1')[0].id

        review_edit = reviewer_client.post_note_edit(
            invitation='TestIdentityVenue.cc/Submission1/-/Official_Review',
            signatures=[anon_group_id],
            note=Note(
                content={
                    'title': { 'value': 'Review for Paper 1' },
                    'review': { 'value': 'good paper' },
                    'rating': { 'value': 10 },
                    'confidence': { 'value': 5 }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        # A note signed by the paper's Reviewers group, readable by the area chair. Nothing in it mentions the reviewer.
        group_note_edit = openreview_client.post_note_edit(
            invitation='TestIdentityVenue.cc/-/Edit',
            signatures=['TestIdentityVenue.cc'],
            readers=['TestIdentityVenue.cc', 'TestIdentityVenue.cc/Submission1/Area_Chairs'],
            writers=['TestIdentityVenue.cc'],
            note=Note(
                forum=submission.id,
                replyto=submission.id,
                signatures=['TestIdentityVenue.cc/Submission1/Reviewers'],
                readers=['TestIdentityVenue.cc', 'TestIdentityVenue.cc/Submission1/Area_Chairs'],
                writers=['TestIdentityVenue.cc'],
                content={
                    'title': { 'value': 'Note signed by the reviewers of the paper' }
                }
            )
        )

        openreview_client.flush_members_cache('~AreaChair_Identity_One1')
        ac_client = OpenReviewClient(username='identity_ac@mail.com', password=helpers.strong_password)

        assert ac_client.get_groups(prefix='TestIdentityVenue.cc/Submission1/Reviewer_') == []
        assert len(ac_client.get_notes(invitation='TestIdentityVenue.cc/Submission1/-/Official_Review')) == 1
        assert ac_client.get_note(group_note_edit['note']['id'])

        # Nothing is signed with the reviewer's profile id
        assert ac_client.get_notes(signature='~Reviewer_Identity_One1') == []

        # Issue 2: with transitiveMembers the API used to expand the profile id to the groups the reviewer is a
        # transitive member of and keep the ones the area chair can read. The anonymous id was dropped, but the paper's
        # Reviewers group, reached through it, was kept, so the note signed by that group was returned and told the
        # area chair that the reviewer is assigned to this paper. The parameter is ignored now
        assert ac_client.get_notes(signature='~Reviewer_Identity_One1', transitive_members=True) == []
