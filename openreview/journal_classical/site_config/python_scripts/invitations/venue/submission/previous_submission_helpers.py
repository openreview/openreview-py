def parse_forum_id(url):
    if not url or url == "N/A":
        return None
    try:
        from urllib.parse import parse_qs, urlparse
        parsed = urlparse(str(url))
        query = parse_qs(parsed.query)
        forum_ids = query.get("id")
        if forum_ids and forum_ids[0]:
            return forum_ids[0]
    except Exception:
        pass
    if "forum?id=" in str(url):
        return str(url).split("forum?id=", 1)[1].split("&", 1)[0]
    return None


def previous_note_from_content(client, journal, content):
    previous_url = content.get("previous_JMLR_submission_URL", {}).get("value")
    previous_forum_id = parse_forum_id(previous_url)
    if previous_forum_id:
        try:
            return client.get_note(previous_forum_id)
        except Exception:
            return None
    previous_number = content.get("previous_JMLR_submission_number", {}).get("value")
    if previous_number and str(previous_number).strip().isdigit():
        previous_notes = client.get_notes(
            invitation=f"{journal.venue_id}/-/Submission",
            number=int(str(previous_number).strip())
        )
        return previous_notes[0] if previous_notes else None
    return None


def previous_notes_from_list(client, journal, content):
    previous_list = content.get("previous_JMLR_submissions", {}).get("value") or ""
    notes = []
    seen = set()
    for line in str(previous_list).splitlines():
        previous_forum_id = parse_forum_id(line)
        if previous_forum_id and previous_forum_id not in seen:
            try:
                notes.append(client.get_note(previous_forum_id))
                seen.add(previous_forum_id)
                continue
            except Exception:
                pass
        marker = "Paper "
        if marker not in line:
            continue
        number_text = line.split(marker, 1)[1].split("]", 1)[0].split(")", 1)[0].strip()
        if not number_text.isdigit():
            continue
        try:
            previous_notes = client.get_notes(
                invitation=f"{journal.venue_id}/-/Submission",
                number=int(number_text)
            )
            if previous_notes and previous_notes[0].id not in seen:
                notes.append(previous_notes[0])
                seen.add(previous_notes[0].id)
        except Exception:
            pass
    return notes


def previous_submission_chain(client, journal, first_previous_note):
    previous_notes = []
    seen_note_ids = set()
    current_note = first_previous_note
    while current_note and current_note.id not in seen_note_ids:
        seen_note_ids.add(current_note.id)
        previous_notes.append(current_note)
        listed_previous_notes = previous_notes_from_list(client, journal, current_note.content or {})
        if listed_previous_notes:
            for listed_note in listed_previous_notes:
                if listed_note.id not in seen_note_ids:
                    seen_note_ids.add(listed_note.id)
                    previous_notes.append(listed_note)
            break
        current_note = previous_note_from_content(client, journal, current_note.content or {})
    return previous_notes


def previous_submissions_markdown(client, journal, site_url, first_previous_note):
    rows = []
    for previous_note in previous_submission_chain(client, journal, first_previous_note):
        rows.append(f"- [Paper {previous_note.number}]({site_url}/forum?id={previous_note.id})")
    return "\n".join(rows)
