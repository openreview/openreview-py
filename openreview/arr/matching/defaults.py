DEFAULT_AC_MATCHING_CONFIG = {
    "title": {
        "value": ""
    },
    "user_demand": {
        "value": "1"
    },
    "max_papers": {
        "value": "0"
    },
    "min_papers": {
        "value": "0"
    },
    "alternates": {
        "value": "200"
    },
    "paper_invitation": {
        "value": "VENUE_ID/-/Submission&content.venueid=VENUE_ID/Submission"
    },
    "match_group": {
        "value": "VENUE_ID/Area_Chairs"
    },
    "scores_specification": {
        "value": {
            "VENUE_ID/Area_Chairs/-/Affinity_Score": {
                "weight": 1,
                "default": 0
            },
            "VENUE_ID/Area_Chairs/-/Research_Area": {
                "weight": 1,
                "default": 0
            }
        }
    },
    "aggregate_score_invitation": {
        "value": "VENUE_ID/Area_Chairs/-/Aggregate_Score"
    },
    "conflicts_invitation": {
        "value": "VENUE_ID/Area_Chairs/-/Conflict"
    },
    'custom_user_demand_invitation': {
        "value": "VENUE_ID/Area_Chairs/-/Custom_User_Demands"
    },
    'custom_max_papers_invitation': {
        "value": "VENUE_ID/Area_Chairs/-/Custom_Max_Papers"
    },
    "solver": {
        "value": "FairFlow"
    },
    "status": {
        "value": "Initialized"
    }
}

DEFAULT_SAC_MATCHING_CONFIG = {
    "title": {
        "value": ""
    },
    "user_demand": {
        "value": "1"
    },
    "max_papers": {
        "value": "400"
    },
    "min_papers": {
        "value": "0"
    },
    "alternates": {
        "value": "50"
    },
    "paper_invitation": {
        "value": "VENUE_ID/-/Submission&content.venueid=VENUE_ID/Submission"
    },
    "match_group": {
        "value": "VENUE_ID/Senior_Area_Chairs"
    },
    "scores_specification": {
        "value": {
            "VENUE_ID/Senior_Area_Chairs/-/Affinity_Score": {
                "weight": 1,
                "default": 0
            },
            "VENUE_ID/Senior_Area_Chairs/-/Research_Area": {
                "weight": 1,
                "default": 0
            }
        }
    },
    "aggregate_score_invitation": {
        "value": "VENUE_ID/Senior_Area_Chairs/-/Aggregate_Score"
    },
    "conflicts_invitation": {
        "value": "VENUE_ID/Senior_Area_Chairs/-/Conflict"
    },
    "solver": {
        "value": "FairFlow"
    },
    "status": {
        "value": "Initialized"
    }
}