exec({{PYTHON_SCRIPT_JSON:invitations/venue/expert_reviewers/recompute.py}})


EXPERT_REVIEWER_SELECTION_CONFIG = {{EXPERT_REVIEWER_SELECTION_CONFIG_JSON}}


def process(client, invitation):
    result = recompute_and_apply_recognition(client, "JMLR", EXPERT_REVIEWER_SELECTION_CONFIG)
    print(
        "Top Reviewer dateprocess updated {group_id}: {count} members, {adds} additions, {removals} removals; state group {state_group_id}".format(
            group_id=result["expert_reviewers_id"],
            count=len(result["target_expert_reviewers"]),
            adds=len(result["expert_additions"]),
            removals=len(result["expert_removals"]),
            state_group_id=result["expert_reviewer_state_group_id"],
        )
    )
