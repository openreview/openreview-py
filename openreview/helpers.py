from .venue.helpers import get_venue  # noqa: F401


def get_conference(client, request_form_id, support_user='OpenReview.net/Support', setup=False):
    from .conference.helpers import get_conference as _get_conference
    return _get_conference(client, request_form_id, support_user, setup)
