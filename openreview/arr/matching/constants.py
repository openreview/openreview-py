"""
Constants and default values used throughout the ARR matching workflow
"""
PROFILE_ID_FIELD = 'profile_id'


# author_form -> registration form
DEFAULT_REGISTRATION_CONTENT = {
    'profile_confirmed': 'Yes',
    'expertise_confirmed': 'Yes',
    'domains': 'Yes',
    'emails': 'Yes',
    'DBLP': 'Yes',
    'semantic_scholar': 'Yes'
}
DEFAULT_EMERGENCY_CONTENT = {
    'emergency_reviewing_agreement': { 'value': 'Yes' }
}
REGISTRATION_FORM_MAPPING = {
    "confirm_your_profile_has_past_domains": "domains",
    "confirm_your_profile_has_all_email_addresses": "emails",
    "indicate_languages_you_study": "languages_studied",
    "indicate_your_research_areas": "research_area",
    "confirm_your_openreview_profile_contains_a_dblp_link": "DBLP", # DBLP should just be ticked
    "confirm_your_openreview_profile_contains_a_semantic_scholar_link": "semantic_scholar", # This should also be ticked
}
LOAD_FORM_MAPPING = {
    'meta_data_donation': 'meta_data_donation'
}
# author_form -> license_form
LICENSE_FORM_MAPPING = {
    "agreement": "agreement",
    "attribution": "attribution",
}
# author_form -> emergency form
EMERGENCY_FORM_MAPPING = {
    "indicate_emergency_reviewer_load": "emergency_load",
    'indicate_your_research_areas': 'research_area'
}

DEFAULT_REVIEWER_MATCHING_CONFIG = {
    "title": {
        "value": ""
    },
    "user_demand": {
        "value": "3"
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
        "value": "VENUE_ID/Reviewers"
    },
    "scores_specification": {
        "value": {
            "VENUE_ID/Reviewers/-/Affinity_Score": {
                "weight": 1,
                "default": 0
            },
            "VENUE_ID/Reviewers/-/Research_Area": {
                "weight": 1,
                "default": 0
            }
        }
    },
    "constraints_specification": {
        "value": {
            "VENUE_ID/Reviewers/-/Seniority": [
                {
                "min_users": 1,
                "label": "Senior"
                }
            ]
        }
    },
    "aggregate_score_invitation": {
        "value": "VENUE_ID/Reviewers/-/Aggregate_Score"
    },
    "conflicts_invitation": {
        "value": "VENUE_ID/Reviewers/-/Conflict"
    },
    'custom_user_demand_invitation': {
        "value": "VENUE_ID/Reviewers/-/Custom_User_Demands"
    },
    'custom_max_papers_invitation': {
        "value": "VENUE_ID/Reviewers/-/Custom_Max_Papers"
    },
    "solver": {
        "value": "FairIR"
    },
    "status": {
        "value": "Initialized"
    }
}

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