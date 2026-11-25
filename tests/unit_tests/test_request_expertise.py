from unittest.mock import MagicMock, patch

from openreview.api import OpenReviewClient


def test_request_expertise_sends_weight_and_top_recent_pubs():
    client = OpenReviewClient(baseurl='https://api.example.org', token='test-token')
    response = MagicMock(status_code=200)
    response.json.return_value = {'jobId': 'job-1'}
    weight = [{'prefix': 'ICLR.cc', 'weight': 2}]

    with patch.object(client.session, 'post', return_value=response) as mock_post:
        client.request_expertise(
            name='test',
            group_id='Venue/Reviewers',
            venue_id='Venue/Submission',
            weight=weight,
            top_recent_pubs=5,
        )

    assert mock_post.call_args.kwargs['json']['dataset'] == {
        'weightSpecification': weight,
        'topRecentPubs': 5,
    }
