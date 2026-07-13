def reviewer_rating_focus_url(site_url, rating_invitation):
    import urllib.parse

    def content_value(note_or_invitation, field_name, default=''):
        field = (getattr(note_or_invitation, 'content', {}) or {}).get(field_name, {})
        if isinstance(field, dict):
            return field.get('value', default)
        return field or default

    params = {
        'id': rating_invitation.id
    }

    return (
        site_url.rstrip('/')
        + '/invitation?'
        + urllib.parse.urlencode(params)
    )


def reviewer_rating_focus_link_html(url, label):
    return '[' + label + '](' + url + ')'
