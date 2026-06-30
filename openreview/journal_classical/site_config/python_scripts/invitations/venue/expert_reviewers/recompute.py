import datetime as dt
import json
from collections import defaultdict

import openreview


MILLIS_PER_DAY = 24 * 60 * 60 * 1000
EXPECTED_RATING_SCORES = {
    "No rating": 0,
    "Exceeds expectations": 1,
    "Meets expectations": 0,
    "Falls below expectations": -1,
    "Report problem": -2,
}


def now_millis():
    return int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)


def days_in_month(year, month):
    if month == 12:
        next_month = dt.date(year + 1, 1, 1)
    else:
        next_month = dt.date(year, month + 1, 1)
    return (next_month - dt.timedelta(days=1)).day


def months_ago_millis(timestamp, months):
    date = dt.datetime.fromtimestamp(timestamp / 1000, tz=dt.timezone.utc)
    year = date.year
    month = date.month - int(months)
    while month <= 0:
        month += 12
        year -= 1
    day = min(date.day, days_in_month(year, month))
    return int(date.replace(year=year, month=month, day=day).timestamp() * 1000)


def content_value(note_or_edit, key, default=None):
    value = getattr(note_or_edit, "content", {}).get(key, {})
    if isinstance(value, dict):
        return value.get("value", default)
    return default


def get_group_members(client, group_id):
    try:
        group = client.get_group(group_id)
    except Exception:
        return []
    return list(getattr(group, "members", None) or [])


def post_group_members(client, venue_id, group_id, members):
    group = openreview.api.Group(id=group_id, members=sorted(set(members)))
    group.signatures = [venue_id]
    client.post_group_edit(
        invitation=f"{venue_id}/-/Edit",
        signatures=[venue_id],
        group=group,
    )


def expert_reviewer_state_group_id(venue_id):
    return f"{venue_id}/Expert_Reviewer_State"


def normalize_last_qualified_at(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            value = {}
    if not isinstance(value, dict):
        return {}
    normalized = {}
    for profile_id, timestamp in value.items():
        try:
            normalized[str(profile_id)] = int(timestamp)
        except Exception:
            continue
    return normalized


def normalize_listing_opt_out(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            value = {}
    if not isinstance(value, dict):
        return {}
    normalized = {}
    for profile_id, opted_out in value.items():
        normalized[str(profile_id)] = bool(opted_out)
    return normalized


def expert_reviewer_listing_preference_invitation_id(venue_id):
    return f"{venue_id}/Reviewers/-/Expert_Reviewer_Listing_Preference"


def load_listing_opt_out_preferences(client, venue_id):
    try:
        edges = client.get_all_edges(
            invitation=expert_reviewer_listing_preference_invitation_id(venue_id),
            head=expert_reviewer_state_group_id(venue_id),
            domain=venue_id,
        )
    except Exception:
        return {}
    preferences = {}
    for edge in edges or []:
        if getattr(edge, "ddate", None) or not getattr(edge, "tail", None):
            continue
        preferences[str(edge.tail)] = getattr(edge, "label", None) == "Opt_Out"
    return preferences


def load_openreview_state(client, venue_id):
    state_group_id = expert_reviewer_state_group_id(venue_id)
    try:
        state_group = client.get_group(state_group_id)
    except Exception:
        return {"last_qualified_at": {}, "listing_opt_out": {}}
    content = getattr(state_group, "content", None) or {}
    last_qualified_field = content.get("last_qualified_at", {})
    last_qualified_at = last_qualified_field.get("value") if isinstance(last_qualified_field, dict) else last_qualified_field
    listing_opt_out_field = content.get("listing_opt_out", {})
    listing_opt_out = listing_opt_out_field.get("value") if isinstance(listing_opt_out_field, dict) else listing_opt_out_field
    return {
        "last_qualified_at": normalize_last_qualified_at(last_qualified_at),
        "listing_opt_out": normalize_listing_opt_out(listing_opt_out),
    }


def post_openreview_state(client, venue_id, state):
    state_group_id = expert_reviewer_state_group_id(venue_id)
    last_qualified_at = normalize_last_qualified_at((state or {}).get("last_qualified_at", {}))
    listing_opt_out = normalize_listing_opt_out((state or {}).get("listing_opt_out", {}))
    group = openreview.api.Group(
        id=state_group_id,
        readers=[venue_id, f"{venue_id}/Editors_In_Chief"],
        writers=[venue_id],
        signatures=[venue_id],
        members=[],
    )
    group.content = {
        "description": {
            "value": "Non-assigning Top Reviewer recognition state. Stores last_qualified_at timestamps and public-listing opt-out preferences only."
        },
        "last_qualified_at": {"value": json.dumps(last_qualified_at, sort_keys=True)},
        "listing_opt_out": {"value": json.dumps(listing_opt_out, sort_keys=True)},
    }
    client.post_group_edit(
        invitation=f"{venue_id}/-/Edit",
        signatures=[venue_id],
        group=group,
    )


def note_is_review(note):
    return any(str(invitation).endswith("/-/Review") for invitation in getattr(note, "invitations", []) or [])


def note_is_rating(note):
    return any(str(invitation).endswith("/-/Rating") for invitation in getattr(note, "invitations", []) or [])


def reviewer_from_review_signature(client, review):
    signatures = getattr(review, "signatures", []) or []
    if not signatures:
        return None
    try:
        signature_group = client.get_group(signatures[0])
    except Exception:
        return None
    members = getattr(signature_group, "members", None) or []
    if not members:
        return None
    try:
        profile = openreview.tools.get_profile(client, members[0])
    except Exception:
        profile = None
    return getattr(profile, "id", None) or members[0]


def collect_forum_notes(client, venue_id):
    notes = []
    submissions = client.get_all_notes(invitation=f"{venue_id}/-/Submission")
    for submission in submissions:
        try:
            notes.extend(client.get_all_notes(forum=submission.id))
        except Exception as error:
            print(f"WARNING: could not fetch forum notes for Paper{submission.number}: {error}")
    return notes


def collect_reviewer_stats(client, venue_id, since_millis, rating_scores):
    stats = defaultdict(
        lambda: {
            "reviews_submitted": 0,
            "past_due": 0,
            "rating_total": 0,
            "rating_count": 0,
            "ratings": defaultdict(int),
        }
    )
    notes = collect_forum_notes(client, venue_id)
    reviews_by_id = {note.id: note for note in notes if note_is_review(note)}
    ratings_by_review = {}
    for note in notes:
        if note_is_rating(note):
            review_id = content_value(note, "review_note_id")
            if review_id:
                ratings_by_review[review_id] = note

    for review in reviews_by_id.values():
        submitted_at = getattr(review, "tcdate", None) or getattr(review, "cdate", None) or 0
        if submitted_at < since_millis:
            continue
        reviewer_id = None
        rating_note = ratings_by_review.get(review.id)
        if rating_note:
            reviewer_id = content_value(rating_note, "reviewer_profile_id")
        if not reviewer_id:
            reviewer_id = reviewer_from_review_signature(client, review)
        if not reviewer_id:
            continue

        reviewer_stats = stats[reviewer_id]
        reviewer_stats["reviews_submitted"] += 1
        rating_label = content_value(rating_note, "rating", "No rating") if rating_note else "No rating"
        timeliness = content_value(rating_note, "timeliness") if rating_note else None
        reviewer_stats["ratings"][rating_label] += 1
        reviewer_stats["rating_total"] += int(rating_scores.get(rating_label, 0))
        reviewer_stats["rating_count"] += 1
        if timeliness == "Past due":
            reviewer_stats["past_due"] += 1
        elif not timeliness:
            invitation_id = (getattr(review, "invitations", []) or [""])[0]
            try:
                review_invitation = client.get_invitation(invitation_id)
                due_date = getattr(review_invitation, "duedate", None)
            except Exception:
                due_date = None
            if due_date and submitted_at > due_date:
                reviewer_stats["past_due"] += 1

    for reviewer_stats in stats.values():
        reviews_submitted = reviewer_stats["reviews_submitted"]
        reviewer_stats["past_due_rate"] = reviewer_stats["past_due"] / reviews_submitted if reviews_submitted else 0
        rating_count = reviewer_stats["rating_count"]
        reviewer_stats["average_rating"] = reviewer_stats["rating_total"] / rating_count if rating_count else 0
        reviewer_stats["ratings"] = dict(reviewer_stats["ratings"])
    return dict(stats)


def qualifies(reviewer_stats, conditions):
    for condition in conditions:
        if reviewer_stats.get("reviews_submitted", 0) < condition.get("min_reviews", 0):
            continue
        if reviewer_stats.get("past_due_rate", 1) > condition.get("max_past_due_rate", 0):
            continue
        if reviewer_stats.get("average_rating", 0) < condition.get("min_average_rating", 0):
            continue
        return True
    return False


def reviewer_display_name(client, profile_id):
    try:
        profile = openreview.tools.get_profile(client, profile_id)
    except Exception:
        profile = None
    if profile and getattr(profile, "content", None):
        names = profile.content.get("names", [])
        if names:
            fullname = names[0].get("fullname")
            if fullname:
                return fullname
    return profile_id


def build_result(*, client, venue_id, selection_config, state=None, migrate_obsolete_ebr=False):
    if migrate_obsolete_ebr:
        raise ValueError("Reviewer-subrole migration is an operations repair path and is not supported by the product helper.")
    timestamp = now_millis()
    state = state or {"last_qualified_at": {}}
    state.setdefault("last_qualified_at", {})
    state.setdefault("listing_opt_out", {})
    lookback_months = int(selection_config.get("review_stats_lookback_months", 12))
    retention_months = int(selection_config.get("minimum_retention_months", 3))
    since_millis = months_ago_millis(timestamp, lookback_months)
    rating_scores = {str(key): int(value) for key, value in selection_config.get("rating_scores", {}).items()}
    missing_rating_scores = {key: value for key, value in EXPECTED_RATING_SCORES.items() if rating_scores.get(key) != value}
    if missing_rating_scores:
        raise ValueError(f"Top Reviewer rating_scores are missing required values: {missing_rating_scores}")
    conditions = list(selection_config.get("conditions", []))

    reviewers_id = f"{venue_id}/Reviewers"
    expert_reviewers_id = f"{venue_id}/Expert_Reviewers"

    current_reviewers = set(get_group_members(client, reviewers_id))
    current_experts = set(get_group_members(client, expert_reviewers_id))
    listing_opt_out = normalize_listing_opt_out(state.get("listing_opt_out", {}))
    listing_opt_out.update(load_listing_opt_out_preferences(client, venue_id))
    state["listing_opt_out"] = listing_opt_out

    stats = collect_reviewer_stats(client, venue_id, since_millis, rating_scores)
    eligible = {reviewer_id for reviewer_id, reviewer_stats in stats.items() if qualifies(reviewer_stats, conditions)}
    eligible &= current_reviewers

    retention_cutoff = months_ago_millis(timestamp, retention_months)
    last_qualified_at = state.setdefault("last_qualified_at", {})
    for reviewer_id in eligible:
        last_qualified_at[reviewer_id] = timestamp

    retained = {
        reviewer_id
        for reviewer_id in current_experts
        if (
            reviewer_id in current_reviewers
            and reviewer_id not in eligible
            and int(last_qualified_at.get(reviewer_id, 0)) > retention_cutoff
        )
    }
    opted_out_reviewers = {reviewer_id for reviewer_id, opted_out in listing_opt_out.items() if opted_out}
    target_experts = (eligible | retained) - opted_out_reviewers

    rows = []
    for reviewer_id in sorted(target_experts):
        reviewer_stats = stats.get(
            reviewer_id,
            {
                "reviews_submitted": 0,
                "past_due": 0,
                "past_due_rate": 0,
                "average_rating": 0,
                "ratings": {},
            },
        )
        rows.append(
            {
                "name": reviewer_display_name(client, reviewer_id),
                "profile_id": reviewer_id,
                "reviews_submitted": reviewer_stats["reviews_submitted"],
                "past_due": reviewer_stats["past_due"],
                "past_due_rate": reviewer_stats["past_due_rate"],
                "average_rating": reviewer_stats["average_rating"],
                "ratings": reviewer_stats["ratings"],
                "eligible_now": reviewer_id in eligible,
                "qualified_now": reviewer_id in eligible,
                "retained_by_grace_period": reviewer_id in retained,
                "retained_by_minimum_months": reviewer_id in retained,
                "last_qualified_at": last_qualified_at.get(reviewer_id),
                "listing_opted_out": False,
            }
        )

    removal_rows = []
    for reviewer_id in sorted(current_experts - target_experts):
        last_qualified = int(last_qualified_at.get(reviewer_id, 0) or 0)
        removal_rows.append(
            {
                "name": reviewer_display_name(client, reviewer_id),
                "profile_id": reviewer_id,
                "qualified_now": False,
                "retained_by_grace_period": False,
                "last_qualified_at": last_qualified or None,
                "listing_opted_out": reviewer_id in opted_out_reviewers,
                "removed_by_listing_opt_out": reviewer_id in opted_out_reviewers,
                "removed_after_grace_period": bool(last_qualified and last_qualified <= retention_cutoff),
                "never_qualified": not bool(last_qualified),
            }
        )

    return {
        "timestamp": timestamp,
        "lookback_months": lookback_months,
        "retention_months": retention_months,
        "reviewers_id": reviewers_id,
        "expert_reviewers_id": expert_reviewers_id,
        "expert_reviewer_state_group_id": expert_reviewer_state_group_id(venue_id),
        "current_reviewers": sorted(current_reviewers),
        "current_expert_reviewers": sorted(current_experts),
        "listing_opted_out_reviewers": sorted(opted_out_reviewers),
        "target_expert_reviewers": sorted(target_experts),
        "expert_additions": sorted(target_experts - current_experts),
        "expert_removals": sorted(current_experts - target_experts),
        "reviewer_stats": stats,
        "expert_reviewer_rows": rows,
        "expert_removal_rows": removal_rows,
        "state": state,
    }


def recompute_and_apply_recognition(client, venue_id, selection_config):
    state = load_openreview_state(client, venue_id)
    result = build_result(
        client=client,
        venue_id=venue_id,
        selection_config=selection_config,
        state=state,
        migrate_obsolete_ebr=False,
    )
    post_group_members(client, venue_id, result["expert_reviewers_id"], result["target_expert_reviewers"])
    post_openreview_state(client, venue_id, result["state"])
    return result
