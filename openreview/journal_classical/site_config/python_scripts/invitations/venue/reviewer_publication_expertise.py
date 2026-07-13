PUBLICATION_EXPERTISE_CONFIG = {{REVIEWER_PUBLICATION_EXPERTISE_CONFIG_JSON}}


def normalize_publication_venue(value):
    normalized = str(value or "").lower().replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def publication_content_value(item, key):
    content = getattr(item, "content", None)
    if isinstance(item, dict):
        value = item.get(key)
        if value is None:
            content = item.get("content")
        else:
            return value.get("value") if isinstance(value, dict) and "value" in value else value
    if isinstance(content, dict):
        value = content.get(key)
        return value.get("value") if isinstance(value, dict) and "value" in value else value
    return None


def profile_publications(profile):
    content = getattr(profile, "content", {}) or {}
    for key in ("publications", "pubs"):
        value = content.get(key)
        if isinstance(value, list):
            return value
    return []


def publication_key(publication, index):
    identifier = getattr(publication, "id", None) or (publication.get("id") if isinstance(publication, dict) else None)
    if identifier:
        return str(identifier)
    title = publication_content_value(publication, "title")
    year = publication_content_value(publication, "year")
    return f"{title or 'untitled'}::{year or index}"


def publication_venue_values(publication):
    values = []
    for key in ("venueid", "venue", "venue_name", "journal", "booktitle"):
        value = publication_content_value(publication, key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    return values


def venue_indexes(config):
    alias_to_key = {}
    acronym_to_key = {}
    for key, venue in config["canonical_venues"].items():
        acronym = str(venue.get("acronym") or key)
        acronym_to_key[normalize_publication_venue(acronym)] = key
        for alias in venue.get("aliases", []):
            normalized = normalize_publication_venue(alias)
            if normalized:
                alias_to_key[normalized] = key
    return alias_to_key, acronym_to_key


def publication_venue_weight(raw_venue, config):
    normalized = normalize_publication_venue(raw_venue)
    unmatched_weight = float(config.get("unmatched_publication_weight", 0.75))
    if not normalized:
        return 0.0
    if "workshop" in normalized:
        return unmatched_weight

    alias_to_key, acronym_to_key = venue_indexes(config)
    matched_key = alias_to_key.get(normalized) or acronym_to_key.get(normalized)
    if matched_key:
        return float(config["canonical_venues"][matched_key]["weight"])

    for key, venue in config["canonical_venues"].items():
        for pattern in venue.get("patterns", []):
            if re.search(pattern, normalized):
                return float(config["canonical_venues"][key]["weight"])

    return unmatched_weight


def publication_weight(publication, config):
    values = publication_venue_values(publication)
    if not values:
        return 0.0
    weights = [publication_venue_weight(value, config) for value in values]
    configured_weights = [weight for weight in weights if weight != float(config.get("unmatched_publication_weight", 0.75))]
    return configured_weights[0] if configured_weights else weights[0]


def publication_effective_count(publications, config):
    matched_weighted_count = 0.0
    unmatched_weighted_count = 0.0
    unmatched_weight = float(config.get("unmatched_publication_weight", 0.75))
    seen_keys = set()
    for index, publication in enumerate(publications or []):
        key = publication_key(publication, index)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        weight = publication_weight(publication, config)
        if weight == unmatched_weight:
            unmatched_weighted_count += weight
        else:
            matched_weighted_count += weight
    cap = float(config["publication_score_cap"])
    unmatched_credit_cap = cap / 2.0
    return matched_weighted_count + min(unmatched_weighted_count, unmatched_credit_cap)


def reviewer_publication_effective_count(client, profile_id):
    profile = openreview.tools.get_profile(client, profile_id, with_publications=True)
    if not profile:
        raise openreview.OpenReviewException(f"Could not load OpenReview profile {profile_id} for reviewer publication expertise.")
    return publication_effective_count(profile_publications(profile), PUBLICATION_EXPERTISE_CONFIG)


def add_member_to_group_if_needed(client, venue_id, group_id, profile_id):
    group = client.get_group(group_id)
    members = list(group.members or [])
    if profile_id in members:
        return False
    members.append(profile_id)
    client.post_group_edit(
        invitation=f"{venue_id}/-/Edit",
        signatures=[venue_id],
        group=openreview.api.Group(id=group_id, members=members),
    )
    return True


def remove_member_from_group_if_present(client, venue_id, group_id, profile_id):
    group = client.get_group(group_id)
    members = list(group.members or [])
    if profile_id not in members:
        return False
    members = [member for member in members if member != profile_id]
    client.post_group_edit(
        invitation=f"{venue_id}/-/Edit",
        signatures=[venue_id],
        group=openreview.api.Group(id=group_id, members=members),
    )
    return True


def route_reviewer_pool_by_publication_expertise(client, venue_id, profile_id, reviewers_id, min_effective_count):
    effective_count = reviewer_publication_effective_count(client, profile_id)
    if effective_count >= float(min_effective_count):
        add_member_to_group_if_needed(client, venue_id, reviewers_id, profile_id)
        return "reviewer"
    return "below_threshold"
