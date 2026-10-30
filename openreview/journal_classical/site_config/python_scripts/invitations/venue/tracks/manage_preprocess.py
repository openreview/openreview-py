def process(client, edit, invitation):
    # JMLR delta: Journal has no managed-track registry to validate.
    proposed_value = edit.group.content['tracks']['value']
    previous = load_track_records(client)
    proposed = validate_track_records(track_records_from_value(proposed_value), previous=previous)
    edit.group.content['tracks'] = {
        'value': json.dumps(proposed, separators=(',', ':'), ensure_ascii=False)
    }


exec(r'''{{PYTHON_SCRIPT_FILE:invitations/venue/tracks/registry.py}}''')
