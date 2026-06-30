def process(client, edit, invitation):
  import re

  journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
  site_url = "{{SITE_URL}}"
  previous_submission_namespace = {}
  exec("{{PYTHON_SCRIPT_JSON:invitations/venue/submission/previous_submission_helpers.py}}", previous_submission_namespace)
  previous_note_from_content = previous_submission_namespace["previous_note_from_content"]
  previous_notes_from_list = previous_submission_namespace["previous_notes_from_list"]
  previous_submission_chain = previous_submission_namespace["previous_submission_chain"]
  previous_submissions_markdown = previous_submission_namespace["previous_submissions_markdown"]
  parse_forum_id = previous_submission_namespace["parse_forum_id"]

  def is_openreview_profile_id(value):
    return bool(re.match(r"^~[A-Za-z0-9_]+[0-9]*$", str(value or "").strip()))

  def parse_author_list():
    raw_author_list = edit.note.content.get("author_list", {}).get("value") or ""
    if "\n" in raw_author_list or "\r" in raw_author_list:
      raise openreview.OpenReviewException(
        "Author List must use comma-separated OpenReview profile IDs only. Line breaks are not allowed."
      )
    authorids = []
    for part in raw_author_list.split(","):
      author_id = part.strip()
      if author_id:
        authorids.append(author_id)

    if not authorids:
      raise openreview.OpenReviewException(
        "Author List is required. List every author by OpenReview profile ID, in paper order, for example: ~First_Author1, ~Second_Author1."
      )

    authors = []
    normalized_authorids = []

    def profile_display_name(profile, fallback):
      content = getattr(profile, "content", {}) or {}
      names = content.get("names") or []
      preferred_name = None
      for name in names:
        if name and name.get("preferred"):
          preferred_name = name
          break
      if not preferred_name and names:
        preferred_name = names[0] or {}
      if preferred_name:
        fullname = preferred_name.get("fullname")
        if fullname:
          return fullname
        parts = [
          preferred_name.get("first"),
          preferred_name.get("middle"),
          preferred_name.get("last")
        ]
        joined = " ".join([str(part).strip() for part in parts if part])
        if joined:
          return joined
      return fallback

    def profile_affiliation(profile, fallback):
      content = getattr(profile, "content", {}) or {}
      history = content.get("history") or []
      current_history = None
      for item in history:
        if item and not item.get("end"):
          current_history = item
          break
      if not current_history and history:
        current_history = history[0] or {}
      institution = (current_history or {}).get("institution")
      if isinstance(institution, str) and institution.strip():
        return institution.strip()
      if isinstance(institution, dict) and institution.get("name"):
        return str(institution.get("name")).strip()
      return fallback

    def authoritative_profile_metadata(author_id, index):
      try:
        profile = client.get_profile(author_id)
      except Exception:
        raise openreview.OpenReviewException(
          f"Author List line {index} has an OpenReview profile ID that could not be resolved: {author_id}."
        )
      if not profile:
        raise openreview.OpenReviewException(
          f"Author List line {index} has an OpenReview profile ID that could not be resolved: {author_id}."
        )
      return getattr(profile, "id", None) or author_id, profile_display_name(profile, author_id)

    for index, author_id in enumerate(authorids, start=1):
      if not is_openreview_profile_id(author_id):
        raise openreview.OpenReviewException(
          f"Author List entry {index} must be a valid OpenReview profile ID like ~First_Author1. Email addresses and names are not allowed: {author_id}."
        )
      author_id, author_name = authoritative_profile_metadata(author_id, index)
      if author_id in normalized_authorids:
        raise openreview.OpenReviewException(
          f"Author List contains a duplicate OpenReview profile ID: {author_id}."
        )
      authors.append(author_name)
      normalized_authorids.append(author_id)

    edit.note.content["author_list"] = {"value": ", ".join(normalized_authorids)}
    edit.note.content["authors"] = {"value": authors}
    edit.note.content["authorids"] = {"value": normalized_authorids}
    return normalized_authorids

  def validate_conflict_of_interests():
    if "conflict_of_interests" not in edit.note.content:
      return
    raw_coi = edit.note.content.get("conflict_of_interests", {}).get("value") or ""
    if "\n" in raw_coi or "\r" in raw_coi:
      raise openreview.OpenReviewException(
        "Conflict Of Interests must use comma-separated OpenReview profile IDs only. Line breaks are not allowed."
      )
    conflict_ids = []
    for part in raw_coi.split(","):
      conflict_id = part.strip()
      if conflict_id:
        conflict_ids.append(conflict_id)

    if not conflict_ids:
      return
    if len(conflict_ids) == 1 and conflict_ids[0].lower() in ["n/a", "na", "none", "no conflicts"]:
      edit.note.content["conflict_of_interests"] = {"value": ""}
      return

    normalized_conflict_ids = []
    for index, conflict_id in enumerate(conflict_ids, start=1):
      if not is_openreview_profile_id(conflict_id):
        raise openreview.OpenReviewException(
          f"Conflict Of Interests entry {index} must be a valid OpenReview profile ID like ~First_Author1. "
          "List other conflicts in the Cover Letter instead; they may not be processed as structured conflicts."
        )
      try:
        profile = client.get_profile(conflict_id)
      except Exception:
        raise openreview.OpenReviewException(
          f"Conflict Of Interests entry {index} has an OpenReview profile ID that could not be resolved: {conflict_id}."
        )
      if not profile:
        raise openreview.OpenReviewException(
          f"Conflict Of Interests entry {index} has an OpenReview profile ID that could not be resolved: {conflict_id}."
        )
      resolved_id = getattr(profile, "id", None) or conflict_id
      if resolved_id in normalized_conflict_ids:
        raise openreview.OpenReviewException(
          f"Conflict Of Interests contains a duplicate OpenReview profile ID: {resolved_id}."
        )
      normalized_conflict_ids.append(resolved_id)

    edit.note.content["conflict_of_interests"] = {"value": ", ".join(normalized_conflict_ids)}

  def get_submitter_profile_id():
    candidates = []
    tauthor = getattr(edit, "tauthor", None)
    if tauthor:
      candidates.append(tauthor)
    candidates.extend(getattr(edit, "signatures", None) or [])
    candidates.extend(getattr(edit.note, "signatures", None) or [])

    for candidate in candidates:
      if not candidate or not isinstance(candidate, str):
        continue
      if candidate.startswith("~"):
        return candidate
      if "@" not in candidate:
        continue
      try:
        profile = client.get_profile(candidate)
        profile_id = getattr(profile, "id", None)
        if profile_id:
          return profile_id
      except Exception:
        continue
    return None

  def profile_identity_values(value):
    values = []
    def add(candidate):
      if candidate and isinstance(candidate, str) and candidate not in values:
        values.append(candidate)
    add(value)
    if not value or not isinstance(value, str):
      return values
    if not (value.startswith("~") or "@" in value):
      return values
    try:
      profile = client.get_profile(value)
    except Exception:
      return values
    if not profile:
      return values
    add(getattr(profile, "id", None))
    try:
      add(profile.get_preferred_email())
    except Exception:
      pass
    profile_content = getattr(profile, "content", {}) or {}
    add(profile_content.get("preferredEmail"))
    for email in profile_content.get("emails", []) or []:
      add(email)
    for email in profile_content.get("preferredEmails", []) or []:
      add(email)
    return values

  def ensure_eic_author_constraints(authorids):
    try:
      eic_group = client.get_group(journal.get_editors_in_chief_id())
    except Exception:
      return
    author_identity_set = set(authorids or [])
    eic_members = list(getattr(eic_group, "members", None) or [])
    if not eic_members:
      return
    non_authored_eic_members = []
    authored_eic_members = []
    for eic_member in eic_members:
      eic_identity_values = set(profile_identity_values(eic_member))
      if eic_identity_values.intersection(author_identity_set):
        authored_eic_members.append(eic_member)
      else:
        non_authored_eic_members.append(eic_member)
    if len(authored_eic_members) > 1:
      raise openreview.OpenReviewException(
        "This submission lists multiple current editors-in-chief as authors. "
        "A paper may not have more than one current editor-in-chief as an author."
      )
    if not non_authored_eic_members:
      raise openreview.OpenReviewException(
        "This submission lists every current editor-in-chief as an author. "
        "At least one non-author editor-in-chief must remain available to administer the paper."
      )

  def normalize_previous_submission_reference():
    raw_number = edit.note.content.get("previous_JMLR_submission_number", {}).get("value")
    raw_url = edit.note.content.get("previous_JMLR_submission_URL", {}).get("value")

    if raw_number is None:
      raw_number = ""
    raw_number = str(raw_number).strip()

    if not raw_number and raw_url and raw_url != "N/A":
      return

    if not raw_number or raw_number.upper() == "N/A":
      edit.note.content["previous_JMLR_submission_number"] = hidden_new_submission_field("N/A")
      edit.note.content["previous_JMLR_submission_URL"] = hidden_new_submission_field("N/A")
      edit.note.content.pop("previous_JMLR_submissions", None)
      hide_new_submission_only_fields()
      return

    if not raw_number.isdigit():
      raise openreview.OpenReviewException(
        "Previous JMLR Submission Number must be a paper number, such as 123, or N/A for a new submission."
      )

    previous_number = int(raw_number)
    previous_notes = client.get_notes(
      invitation=f"{journal.venue_id}/-/Submission",
      number=previous_number
    )
    if not previous_notes:
      raise openreview.OpenReviewException(
        f"Could not find JMLR submission number {previous_number}. Please check the previous JMLR submission number."
      )

    previous_note = previous_notes[0]
    if raw_url and raw_url != "N/A":
      previous_url_note_id = parse_forum_id(raw_url)
      if previous_url_note_id and previous_url_note_id != previous_note.id:
        raise openreview.OpenReviewException(
          "Previous JMLR Submission Number and the internal previous submission URL do not match. "
          "Please re-enter the previous JMLR submission number and try submitting again."
        )
    previous_url = f"{site_url}/forum?id={previous_note.id}"
    edit.note.content["previous_JMLR_submission_number"] = internal_content_field(str(previous_note.number))
    edit.note.content["previous_JMLR_submission_URL"] = internal_content_field(previous_url)
    edit.note.content["previous_JMLR_submissions"] = {"value": previous_submissions_markdown(client, journal, site_url, previous_note)}

  def internal_content_field(value):
    return {"value": value, "readers": [journal.venue_id]}

  def hidden_new_submission_field(value):
    return {"value": value, "readers": [journal.venue_id]}

  def hide_new_submission_only_fields():
    response_field = edit.note.content.get("response_to_reviewers")
    response_value = response_field.get("value") if response_field else None
    if not response_value:
      edit.note.content.pop("response_to_reviewers", None)
    elif str(response_value).strip().upper() == "N/A":
      edit.note.content["response_to_reviewers"] = hidden_new_submission_field("N/A")

  def author_names_from_content(content):
    derived_authors = content.get("authors", {}).get("value") or []
    if derived_authors:
      return derived_authors
    raw_author_list = content.get("author_list", {}).get("value") or ""
    author_names = []
    if raw_author_list:
      for line in raw_author_list.splitlines():
        line = line.strip()
        if not line:
          continue
        author_names.append(line.split(",")[0].strip())
      if author_names:
        return author_names
    return content.get("authors", {}).get("value") or []

  def normalize_author_name(name):
    import re
    normalized = re.sub(r"\s+", " ", str(name or "").strip().lower())
    if not normalized:
      return ""
    if "," in normalized:
      last, rest = normalized.split(",", 1)
      rest_parts = [part for part in rest.strip().split(" ") if part]
      last_parts = [part for part in last.strip().split(" ") if part]
      if rest_parts and last_parts:
        return f"{rest_parts[0]} {last_parts[0]}"
    parts = [part for part in normalized.replace(",", " ").split(" ") if part]
    if len(parts) >= 2:
      return f"{parts[0]} {parts[-1]}"
    return parts[0] if parts else ""

  def normalized_author_name_multiset(author_names):
    counts = {}
    for author_name in author_names:
      normalized_name = normalize_author_name(author_name)
      if not normalized_name:
        continue
      counts[normalized_name] = counts.get(normalized_name, 0) + 1
    return counts

  def author_name_diff(previous_author_names, current_author_names):
    previous_counts = normalized_author_name_multiset(previous_author_names)
    current_counts = normalized_author_name_multiset(current_author_names)
    added = []
    removed = []
    for normalized_name in sorted(set(previous_counts.keys()) | set(current_counts.keys())):
      previous_count = previous_counts.get(normalized_name, 0)
      current_count = current_counts.get(normalized_name, 0)
      if current_count > previous_count:
        added.extend([normalized_name] * (current_count - previous_count))
      elif previous_count > current_count:
        removed.extend([normalized_name] * (previous_count - current_count))
    return added, removed

  def authorids_from_content(content):
    values = content.get("authorids", {}).get("value") or []
    if not isinstance(values, list):
      return []
    return [str(value).strip() for value in values if str(value).strip()]

  def normalized_author_id_multiset(authorids):
    counts = {}
    for authorid in authorids:
      normalized_id = str(authorid or "").strip()
      if "@" in normalized_id:
        normalized_id = normalized_id.lower()
      if not normalized_id:
        continue
      counts[normalized_id] = counts.get(normalized_id, 0) + 1
    return counts

  def author_identity_diff(previous_content, current_content):
    previous_authorids = authorids_from_content(previous_content)
    current_authorids = authorids_from_content(current_content)
    if previous_authorids and current_authorids:
      previous_counts = normalized_author_id_multiset(previous_authorids)
      current_counts = normalized_author_id_multiset(current_authorids)
      added = []
      removed = []
      for normalized_id in sorted(set(previous_counts.keys()) | set(current_counts.keys())):
        previous_count = previous_counts.get(normalized_id, 0)
        current_count = current_counts.get(normalized_id, 0)
        if current_count > previous_count:
          added.extend([normalized_id] * (current_count - previous_count))
        elif previous_count > current_count:
          removed.extend([normalized_id] * (previous_count - current_count))
      return added, removed
    return author_name_diff(
      author_names_from_content(previous_content),
      author_names_from_content(current_content)
    )

  def current_note_id():
    note_id = getattr(edit.note, "id", None)
    return note_id if isinstance(note_id, str) else None

  def reject_duplicate_direct_resubmission(previous_note):
    current_id = current_note_id()
    expected_previous_url = f"{site_url}/forum?id={previous_note.id}"
    candidate_submissions = client.get_notes(invitation=f"{journal.venue_id}/-/Submission")
    for candidate in candidate_submissions:
      if candidate.id == current_id:
        continue
      previous_url = candidate.content.get("previous_JMLR_submission_URL", {}).get("value")
      previous_number = candidate.content.get("previous_JMLR_submission_number", {}).get("value")
      points_to_previous = parse_forum_id(previous_url) == previous_note.id
      if not points_to_previous and str(previous_number or "").strip() == str(previous_note.number):
        points_to_previous = True
      if not points_to_previous:
        continue
      raise openreview.OpenReviewException(
        f"JMLR submission {candidate.number} already resubmits previous JMLR submission {previous_note.number}. "
        "Submit a later revision against the latest JMLR round instead of creating another direct resubmission."
      )

  def require_response_to_reviewers_pdf_for_resubmission():
    reply_value = edit.note.content.get("response_to_reviewers", {}).get("value")
    if not reply_value:
      raise openreview.OpenReviewException(
        "Response to Reviewers PDF is required for resubmissions. Use the file chooser to upload a PDF response to the previous reviewers before submitting."
      )

  authorids = parse_author_list()
  validate_conflict_of_interests()
  ensure_eic_author_constraints(authorids)
  normalize_previous_submission_reference()
  if not edit.note.content.get("pdf", {}).get("value"):
    raise openreview.OpenReviewException("Main Paper PDF is required. Use the file chooser to upload the main paper PDF before submitting.")
  submitter_profile_id = get_submitter_profile_id()
  if not submitter_profile_id or submitter_profile_id not in authorids:
    raise openreview.OpenReviewException(
      "The submitting author must be included in Author List using their OpenReview profile ID, not an email address. "
      "Search your name or email in OpenReview and select your profile result, or open your OpenReview profile from "
      "the account menu and copy the ID that starts with ~."
    )

  if edit.note.content["previous_JMLR_submission_URL"]["value"] != "N/A":
    require_response_to_reviewers_pdf_for_resubmission()
    try:
      url = edit.note.content["previous_JMLR_submission_URL"]["value"]
      submission_id = parse_forum_id(url)
      if not submission_id:
        raise openreview.OpenReviewException("Missing previous submission forum id")
      previous_review_note = client.get_note(submission_id)
    except:
        raise openreview.OpenReviewException("Failed to resolve the Previous JMLR Submission Number. Please check the previous JMLR submission number.")

    reject_duplicate_direct_resubmission(previous_review_note)

    previous_author_names = author_names_from_content(previous_review_note.content)
    current_author_names = author_names_from_content(edit.note.content)
    added_author_names, removed_author_names = author_identity_diff(previous_review_note.content, edit.note.content)
    if added_author_names or removed_author_names:
      edit.note.content.pop("author_change_confirmed", None)
      edit.note.content["previous_author_names"] = internal_content_field("\n".join(previous_author_names))
      edit.note.content["current_author_names"] = internal_content_field("\n".join(current_author_names))
      edit.note.content["author_change_summary"] = {
        "value": "Added: " + (", ".join(added_author_names) or "None") + "; Removed: " + (", ".join(removed_author_names) or "None"),
        "readers": [journal.venue_id]
      }
    else:
      for field_name in [
        "author_change_confirmed",
        "previous_author_names",
        "current_author_names",
        "author_change_summary"
      ]:
        edit.note.content.pop(field_name, None)

    previous_decisions = client.get_notes(
        forum=previous_review_note.id,
        invitation=journal.get_ae_decision_id(number=previous_review_note.number)
    )
    allowed_resubmission_decisions = {
      "Reject with encouragement to resubmit",
      "Accept after minor revisions",
      "Accept with minor revision"
    }
    if not any(
        decision.content.get("recommendation", {}).get("value") in allowed_resubmission_decisions
        for decision in previous_decisions
    ):
        raise openreview.OpenReviewException(
            "The previous JMLR submission must have a decision of Reject with encouragement to resubmit "
            "or Accept after minor revisions before it can be resubmitted."
        )
  else:
    for field_name in [
      "previous_JMLR_submission_number",
      "previous_JMLR_submission_URL",
      "previous_JMLR_submissions",
      "response_to_reviewers",
      "author_change_confirmed",
      "previous_author_names",
      "current_author_names",
      "author_change_summary"
    ]:
      edit.note.content.pop(field_name, None)
