"""Project JMLR publication fields that Journal's accepted callback does not own."""


def _content_value(content, key, default=None):
    value = (content or {}).get(key, default)
    if isinstance(value, dict) and 'value' in value:
        return value['value']
    return value


def build_publication_metadata(base_metadata, root_content, track_publication_policy):
    """Return common metadata plus canonical track and explicit website fields.

    ``root_content`` is the final root note content. ``track_publication_policy``
    is the validated build-time map embedded in the stored callback. No value is
    inferred from manuscript, abstract, cover-letter, or supplement prose.
    """
    metadata = dict(base_metadata)
    for reserved in ('track_id', 'track_name', 'track_url', 'special_issue', 'extra_links'):
        metadata.pop(reserved, None)

    track_id = _content_value(root_content, 'track_id')
    if not isinstance(track_id, str) or not track_id:
        raise ValueError('Publication metadata requires the canonical track_id.')
    metadata['track_id'] = track_id

    policy = (track_publication_policy or {}).get(track_id, {})
    if policy.get('special_issue'):
        metadata['special_issue'] = policy['special_issue']

    code_url = _content_value(root_content, 'code')
    if code_url:
        metadata['extra_links'] = [['code', code_url]]
    return metadata
