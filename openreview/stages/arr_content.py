from copy import deepcopy
from datetime import datetime

arr_tracks = [
    "Computational Social Science and Cultural Analytics",
    "Dialogue and Interactive Systems",
    "Discourse and Pragmatics",
    "Efficient/Low-Resource Methods for NLP",
    "Ethics, Bias, and Fairness",
    "Generation",
    "Human-Centered NLP",
    "Information Extraction",
    "Information Retrieval and Text Mining",
    "Interpretability and Analysis of Models for NLP",
    "Language Modeling",
    "Linguistic theories, Cognitive Modeling and Psycholinguistics",
    "Machine Learning for NLP",
    "Machine Translation",
    "Multilingualism and Cross-Lingual NLP",
    "Multimodality and Language Grounding to Vision, Robotics and Beyond",
    "NLP Applications",
    "Phonology, Morphology and Word Segmentation",
    "Question Answering",
    "Resources and Evaluation",
    "Semantics: Lexical and Sentence-Level",
    "Sentiment Analysis, Stylistic Analysis, and Argument Mining",
    "Summarization",
    "Syntax: Tagging, Chunking and Parsing",
    "Special Theme (conference specific)"
]

arr_submission_content = {
    "title": {
        "order": 1,
        "description": "Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.",
        "value": {
            "param": {
                "type": "string",
                "regex": "^.{1,250}$"
            }
        }
    },
    "authors": {
        "order": 2,
        "value": {
            "param": {
                "type": "string[]",
                "regex": "[^;,\\n]+(,[^,\\n]+)*",
                "hidden": True
            }
        }
    },
    "authorids": {
        "order": 3,
        "description": "Search author profile by first, middle and last name or email address. If the profile is not found, you can add the author by completing first, middle, and last names as well as author email address.",
        "value": {
            "param": {
                "type": "profile[]",
                "regex": "^~\\S+$|([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,},){0,}([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,})"
            }
        }
    },
    "reviewing_volunteers": {
        "order": 4,
        "description": "From the list of authors, enter the authors that are going to be responsible for reviewing for this cycle. See this blog post for further information: https://aclrollingreview.org/reviewing-workload-requirement/ .",
        "value": {
            "param": {
                "type": "profile[]",
                "regex": "^~\\S+$|([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,},){0,}([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,})",
                "optional": True
            }
        }
    },
    "reviewing_no_volunteers_reason": {
        "order": 5,
        "description": "If no authors were provided in the previous question, please indicate the reason:",
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "All authors are new to the ACL community.",
                    "None of the authors are sufficiently qualified to review.",
                    "All qualified authors are already involved in the reviewing process in some capacity (as Area Chairs, as Senior Area Chairs, etc.).",
                    "Another reason - if you select this option the editors may contact you to confirm the reason is suitable.",
                    "N/A - An author was provided in the previous question."
                ],
                "optional": False,
                "type": "string"
            }
        }
    },
    "TLDR": {
        "order": 6,
        "description": "\"Too Long; Didn't Read\": a short sentence describing your paper",
        "value": {
            "param": {
                "fieldName": "TL;DR",
                "type": "string",
                "minLength": 1,
                "optional": True
            }
        }
    },
    "abstract": {
        "order": 7,
        "description": "Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 5000,
                "markdown": True,
                "input": "textarea"
            }
        }
    },
    "pdf": {
        "order": 8,
        "description": "Upload a PDF file that ends with .pdf.",
        "value": {
            "param": {
                "type": "file",
                "maxSize": 50,
                "extensions": [
                    "pdf"
                ]
            }
        }
    },
    "paper_type": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Long",
                    "Short"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Long or short. See the CFP for the requirements for long and short papers.",
        "order": 9
    },
    "research_area": {
        "value": {
            "param": {
                "input": "radio",
                "enum": arr_tracks,
                "optional": False,
                "type": "string"
            }
        },
        "description": "Research Areas / Tracks. Select the most relevant research area / track for your paper. This will be used to inform the reviewer and action editor assignment.",
        "order": 10
    },
    "research_area_keywords": {
        "order": 11,
        "description": "Area-specific keywords. Please provide a comma-separated list of keywords from this page: https://aclrollingreview.org/areas",
        "value": {
            "param": {
                "type": "string",
                "regex": "^.{1,250}$"
            }
        }
    },
    "contribution_types": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "Model analysis & interpretability",
                    "NLP engineering experiment",
                    "Reproduction study",
                    "Approaches to low-resource settings",
                    "Approaches low compute settings-efficiency",
                    "Publicly available software and/or pre-trained models",
                    "Data resources",
                    "Data analysis",
                    "Position papers",
                    "Surveys",
                    "Theory"
                ],
                "optional": True,
                "type": "string[]"
            }
        },
        "description": "Which of the following types of contributions does your paper make? This will inform the reviewers and meta-reviewer about what to look for in your work.",
        "order": 12
    },
    "languages_studied": {
        "value": {
            "param": {
                "regex": ".{1,1000}",
                "optional": False,
                "type": "string"
            }
        },
        "description": "Please list the languages studied in your paper, separated by commas.",
        "order": 13
    },
    "previous_URL": {
        "value": {
            "param": {
                "regex": 'https:\/\/openreview\.net\/forum\?id=.*',
                "optional": True,
                "type": "string",
                'mismatchError': 'must be a valid link to an OpenReview submission: https://openreview.net/forum?id=...'
            }
        },
        "description": "If this is a resubmission, provide the URL of your previous submission to ACL Rolling Review (this URL will look like https://openreview.net/forum?id=<some string>). Make sure to only add the paper id and not other parameters after &.",
        "order": 14
    },
    "response_PDF": {
        "value": {
            "param": {
                "type": "file",
                "maxSize": 80,
                "extensions": [
                    "pdf"
                ],
                "optional": True
            }
        },
        "description": "If this is a resubmission, upload a single PDF describing how you have changed your paper in response to your previous round of reviews. Note: this should NOT be a printout of your comments from the in-cycle author response period. This should be a new document that maintains anonymity and describes changes since your last submission.",
        "order": 15
    },
    "reassignment_request_action_editor": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, I want a different action editor for our submission",
                    "No, I want the same action editor from our previous submission and understand that a new action editor may be assigned if the previous one is unavailable",
                    "This is not a resubmission"
                ],
                "type": "string"
            }
        },
        "description": "Do you want your submission to go to a different action editor? If you want your submission to go to the same action editor and they are unavailable this cycle, you will be assigned a new action editor.",
        "order": 16
    },
    "reassignment_request_reviewers": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes, I want a different set of reviewers",
                    "No, I want the same set of reviewers from our previous submission and understand that new reviewers may be assigned if any of the previous ones are unavailable",
                    "This is not a resubmission"
                ],
                "type": "string"
            }
        },
        "description": "Do you want your submission to go to a different set of reviewers? If you want your submission to go to the same set of reviewers and at least one are unavailable this cycle, you will be assigned new reviewers in their place.",
        "order": 17
    },
    "justification_for_not_keeping_action_editor_or_reviewers": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "Please specify reason for any reassignment request. Reasons may include clear lack of expertise in the area or dismissing the work without any concrete comments regarding correctness of the results or argumentation, limited perceived impact of the methods or findings, lack of clarity in exposition, or other valid criticisms. It is up to the discretion of the action editors or editors in chief regarding whether to heed these requests.",
        "order": 18
    },
    "software": {
        "value": {
            "param": {
                "type": "file",
                "maxSize": 50,
                "extensions": [
                    "tgz",
                    "zip"
                ],
                "optional": True
            }
        },
        "description": "Each ARR submission can be accompanied by one .tgz or .zip archive containing software (max. 200MB).",
        "order": 19
    },
    "data": {
        "value": {
            "param": {
                "type": "file",
                "maxSize": 50,
                "extensions": [
                    "tgz",
                    "zip"
                ],
                "optional": True
            }
        },
        "description": "Each ARR submission can be accompanied by one .tgz or .zip archive containing data (max. 200MB).",
        "order": 20
    },
    "preprint": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "yes",
                    "no"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Would the authors like ARR to release a public anonymous pre-print of the submission?",
        "order": 21
    },
    "preprint_status": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "There is a non-anonymous preprint (URL specified in the next question).",
                    "We plan to release a non-anonymous preprint in the next two months (i.e., during the reviewing process).",
                    "We are considering releasing a non-anonymous preprint in the next two months (i.e., during the reviewing process).",
                    "There is no non-anonymous preprint and we do not intend to release one."
                ],
                "type": "string"
            }
        },
        "description": "Is there are a publicly available non-anonymous preprints of this paper, or do you plan to release one? Note, all options for this question are permitted under the updated ACL preprint policy. We are collecting this information to help inform the review process.",
        "order": 22
    },
    "existing_preprints": {
        "value": {
            "param": {
                "regex": ".{1,1000}",
                "optional": True,
                "type": "string"
            }
        },
        "description": "If there are any publicly available non-anonymous preprints of this paper, please list them here (provide the URLs please).",
        "order": 23
    },
    "preferred_venue": {
        "value": {
            "param": {
                "regex": ".{1,300}",
                "optional": True,
                "type": "string"
            }
        },
        "description": "If you have a venue that you are hoping to submit this paper to, please enter it here. You must enter the designated acronym from this list: https://aclrollingreview.org/dates. Note that entering a preferred venue is not a firm commitment to submit your paper to this venue, but it will help ARR and the venue chairs in planning, so we highly recommend filling in your current intentions. Please enter only your first choice.",
        "order": 24
    },
    "consent_to_share_data": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "yes",
                    "no"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "I agree for the anonymized metadata associated with my submission to be included in a publicly available dataset. This dataset WILL include scores, anonymized paper and reviewer IDs that allow grouping the reviews by paper and by reviewer, as well as acceptance decisions and other numerical and categorical metadata. This dataset WILL NOT include any textual or uniquely attributable data like names, submission titles and texts, review texts, author responses, etc. Your decision to opt-in the data does not affect the reviewing of your submission in any way.",
        "order": 25
    },
    "consent_to_share_submission_details": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "On behalf of all authors, we agree to the terms above to share our submission details."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Upon submitting this paper, authors agree to allow us to share their submission details (such as title, author names, and potentially abstract) with program committees from other conference venues for the purpose of verifying compliance with submission requirements.",
        "order": 26
    },
    "A1_limitations_section": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "This paper has a limitations section."
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Authors are required to discuss the limitations of their work in a dedicated section titled \"Limitations\". Papers without this section will be desk rejected. Please confirm that your paper has a limitations section by checking this box.",
        "order": 27
    },
    "A2_potential_risks": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you discuss any potential risks of your work? Note, this question, and those that follow, are from the Responsible Research Checklist (details here: https://aclrollingreview.org/responsibleNLPresearch/ )",
        "order": 28
    },
    "A2_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 29
    },
    "A3_abstract_and_introduction_summarize_claims": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Do the abstract and introduction summarize the paper's main claims?",
        "order": 30
    },
    "A3_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 31
    },
    "B_use_or_create_scientific_artifacts": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "type": "string"
            }
        },
        "description": "Did you use or create scientific artifacts?",
        "order": 32
    },
    "B1_cite_creators_of_artifacts": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you cite the creators of artifacts you used?",
        "order": 33
    },
    "B1_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 34
    },
    "B2_discuss_the_license_for_artifacts": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you discuss the license or terms for use and/or distribution of any artifacts?",
        "order": 35
    },
    "B2_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 36
    },
    "B3_artifact_use_consistent_with_intended_use": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you discuss if your use of existing artifact(s) was consistent with their intended use, provided that it was specified? For the artifacts you create, do you specify intended use and whether that is compatible with the original access conditions (in particular, derivatives of data accessed for research purposes should not be used outside of research contexts)?",
        "order": 37
    },
    "B3_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 38
    },
    "B4_data_contains_personally_identifying_info_or_offensive_content": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you discuss the steps taken to check whether the data that was collected/used contains any information that names or uniquely identifies individual people or offensive content, and the steps taken to protect/anonymize it?",
        "order": 39
    },
    "B4_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 40
    },
    "B5_documentation_of_artifacts": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you provide documentation of the artifacts, e.g., coverage of domains, languages, and linguistic phenomena, demographic groups represented, etc.?",
        "order": 41
    },
    "B5_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 42
    },
    "B6_statistics_for_data": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report relevant statistics like the number of examples, details of train/test/dev splits, etc. for the data that you used/created?",
        "order": 43
    },
    "B6_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 44
    },
    "C_computational_experiments": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "type": "string"
            }
        },
        "description": "Did you run computational experiments?",
        "order": 45
    },
    "C1_model_size_and_budget": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report the number of parameters in the models used, the total computational budget (e.g., GPU hours), and computing infrastructure used?",
        "order": 46
    },
    "C1_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 47
    },
    "C2_experimental_setup_and_hyperparameters": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you discuss the experimental setup, including hyperparameter search and best-found hyperparameter values?",
        "order": 48
    },
    "C2_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 49
    },
    "C3_descriptive_statistics": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report descriptive statistics about your results (e.g., error bars around results, summary statistics from sets of experiments), and is it transparent whether you are reporting the max, mean, etc. or just a single run?",
        "order": 50
    },
    "C3_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 51
    },
    "C4_parameters_for_packages": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "If you used existing packages (e.g., for preprocessing, for normalization, or for evaluation), did you report the implementation, model, and parameter settings used (e.g., NLTK, Spacy, ROUGE, etc.)?",
        "order": 52
    },
    "C4_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 53
    },
    "D_human_subjects_including_annotators": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "type": "string"
            }
        },
        "description": "Did you use human annotators (e.g., crowdworkers) or research with human subjects?",
        "order": 54
    },
    "D1_instructions_given_to_participants": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report the full text of instructions given to participants, including e.g., screenshots, disclaimers of any risks to participants or annotators, etc.?",
        "order": 55
    },
    "D1_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 56
    },
    "D2_recruitment_and_payment": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report information about how you recruited (e.g., crowdsourcing platform, students) and paid participants, and discuss if such payment is adequate given the participants' demographic (e.g., country of residence)?",
        "order": 57
    },
    "D2_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 58
    },
    "D3_data_consent": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you discuss whether and how consent was obtained from people whose data you're using/curating (e.g., did your instructions explain how the data would be used)?",
        "order": 59
    },
    "D3_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 60
    },
    "D4_ethics_review_board_approval": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Was the data collection protocol approved (or determined exempt) by an ethics review board?",
        "order": 61
    },
    "D4_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 62
    },
    "D5_characteristics_of_annotators": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you report the basic demographic and geographic characteristics of the annotator population that is the source of the data?",
        "order": 63
    },
    "D5_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 64
    },
    "E_ai_assistants_in_research_or_writing": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "type": "string"
            }
        },
        "description": "Did you use AI assistants (e.g., ChatGPT, Copilot) in your research, coding, or writing?",
        "order": 65
    },
    "E1_information_about_use_of_ai_assistants": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "N/A"
                ],
                "type": "string"
            }
        },
        "description": "Did you include information about your use of AI assistants?",
        "order": 66
    },
    "E1_elaboration": {
        "value": {
            "param": {
                "minLength": 1,
                "type": "string",
                "optional": True
            }
        },
        "description": "For yes, provide a section number. For no, justify why not.",
        "order": 67
    },
    "Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement": {
        "order": 68,
        "description": "Please read and decide whether to transfer the license to your blind submission draft and its associated peer reviewing data in the current and/or previous iterations of ARR.\n*** DISCLAIMER ***\nYour participation is strictly voluntary. By transferring this license you grant ACL the right to distribute your draft and associated peer reviews. In particular, we may include your draft with donated review texts and scores in research datasets. Please note, to attribute authors for their draft, the author names are explicitly listed along with the draft and its associated peer reviews. Only reviews for accepted papers will be eventually made publicly available. The reviewers have to agree to the release of the textual review data associated with your submission.\n\nThis Blind Submission License Agreement (\"Agreement\") is entered into between the Association for Computational Linguistics (\"ACL\") and the Authors listed in connection with Authors\u2019 blind submission paper listed above (referred as \"Blind Submission Content\").\nIn exchange of adequate consideration, ACL and the Authors agree as follows:\n\nSection 1: Grant of License\nAfter the peer review process is concluded and upon acceptance of the paper, Authors grant ACL a worldwide, irrevocable, and royalty-free license to use the blind submission paper version and, if applicable, the associated amendment notes and author responses to reviewers\u2019 inquiries  (referred as \"Content\"). The foregoing license grants ACL the right to reproduce, publish, distribute, prepare derivative work, and otherwise make use of the Content, and to sub-license the Content to the public according to terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.\nNotwithstanding the foregoing, the Parties acknowledge and agree that this Agreement does not transfer to ACL the ownership of any proprietary rights pertaining to the Content, and that the Authors retain their respective ownership in and to the Content.\n\nSection 2: Permission to Publish Peer Reviewers Content\nAfter the peer review process is concluded and upon acceptance of the paper, Authors have the option to grant ACL permission to publish peer reviewers content associated with the Content, which may include text, review form\nscores and metadata, charts, graphics, spreadsheets, and any other materials developed by peer reviewers in connection with the peer review process.\n\nSection 3: Attribution and Public Access License\nA. The Parties agree that for purpose of administering the public access license, ACL will be\nidentified as the licensor of the Content with the following copyright notice:\n\nCopyright \u00a9 2023 administered by the Association for Computational Linguistics (ACL) on behalf of the authors and content contributors. Content displayed on this webpage is made available under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.\n\nB. The Parties understand and acknowledge that the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License is irrevocable once granted unless the licensee breaches the public access license terms.\n\nSection 4: Effective Date\nThe grant of license pursuant to Section 1 and permission to publish peer reviewers content pursuant to Section 2 becomes effective in the event Authors\u2019 blind submission paper has passed through this ACL Rolling Review cycle's peer review process and the cycle has ended; the end of a cycle is marked by the fact that authors received both the assigned peer review reports and the final meta-review report for this submission.\n\nSection 5: Warranty\nAuthors represent and warrant that the Content is Authors\u2019 original work and does not infringe on the proprietary rights of others. Authors further warrant that they have\nobtained all necessary permissions from any persons or organizations whose materials are included in the Content, and that the Content includes appropriate citations that give credit to the original sources.\n\nSection 6: Legal Relationship\nThe Parties agree that this Agreement is not intended to create any joint venture, partnership, or agency relationship of any kind; and both agree not to contract any obligations in the name of the other.\n\nBy selecting 'On behalf of all authors, I agree' below, I confirm that all Authors have agreed to the above terms and that I am authorized to execute this Agreement on their behalf. Optionally, if you wish to transfer the license to the peer reviewing and blind submission data of all previous versions of this paper submitted to ARR, please select 'On behalf of all authors, I agree for all previous versions of this submission'.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "On behalf of all authors, I agree",
                    "On behalf of all authors, I do not agree",
                    "On behalf of all authors, I agree for this and all previous versions of this submission"
                ],
                "input": "radio",
                "scroll": True,
                "optional": False
            }
        }
    },
    "section_2_permission_to_publish_peer_reviewers_content_agreement": {
        "order": 69,
        "description": "After the peer review process is concluded and upon acceptance of the paper, Authors have the option to grant ACL permission to publish peer reviewers content associated with the Content (as defined in the previous question), which may include text, review form\nscores and metadata, charts, graphics, spreadsheets, and any other materials developed by peer reviewers in connection with the peer review process.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "Authors grant permission for ACL to publish peer reviewers' content",
                    "Authors decline to grant permission for ACL to publish peer reviewers' content"
                ],
                "input": "radio",
                "scroll": True,
                "optional": False
            }
        }
    }
}



arr_author_consent_content = {
    "Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement": {
        "order": 1,
        "description": "Association for Computational Linguistics - Blind Submission License Agreement\n\nPlease read and decide whether to transfer the license to your blind submission draft and its associated peer reviewing data in the current and/or previous iterations of ARR.\n*** DISCLAIMER ***\nYour participation is strictly voluntary. By transferring this license you grant ACL the right to distribute your draft and associated peer reviews. In particular, we may include your draft with donated review texts and scores in research datasets. Please note, to attribute authors for their draft, the author names are explicitly listed along with the draft and its associated peer reviews. Only reviews for accepted papers will be made publicly available directly after acceptance. For papers that are not accepted, the donated data will be kept confidential for the two years following the submission date and then released to the public. The reviewers have to agree to the release of the textual review data associated with your submission.\n\nName of the ACL Conference: ACL Rolling Review\n\nBlind Submission Title: as stated above\n\nAuthors' names: as stated above\n\nThis Blind Submission License Agreement (“Agreement”) is entered into between the Association for Computational Linguistics (“ACL”) and the Authors listed in connection with Authors’ blind submission paper listed above (referred as “Blind Submission Content”).\n\nIn exchange of adequate consideration, ACL and the Authors agree as follows:\n\nSection 1: Grant of License\nAfter the peer review process is concluded, Authors grant ACL a worldwide, irrevocable, and royalty-free license to use the blind submission paper version and, if applicable, the associated amendment notes and author responses to reviewers’ inquiries  (referred as “Content”). The foregoing license grants ACL the right to reproduce, publish, distribute, prepare derivative work, and otherwise make use of the Content, and to sub-license the Content to the public according to terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.\nNotwithstanding the foregoing, the Parties acknowledge and agree that this Agreement does not transfer to ACL the ownership of any proprietary rights pertaining to the Content, and that the Authors retain their respective ownership in and to the Content.\n\nSection 2: Permission to Publish Peer Reviewers' Content\nAfter the peer review process is concluded, Authors have the option to grant ACL permission to publish peer reviewers content associated with the Content, which may include text, review form scores and metadata, charts, graphics, spreadsheets, and any other materials developed by peer reviewers in connection with the peer review process.\n\nSection 3: Attribution and Public Access License\nA. The Parties agree that for purpose of administering the public access license, ACL will be identified as the licensor of the Content with the following copyright notice:\n\nCopyright © 2024 administered by the Association for Computational Linguistics (ACL) on behalf of the authors and content contributors. Content displayed on this webpage is made available under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.\n\nB. The Parties understand and acknowledge that the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License is irrevocable once granted unless the licensee breaches the public access license terms.\n\nSection 4: Effective Date\nThe grant of license pursuant to Section 1 and permission to publish peer reviewers content pursuant to Section 2 becomes effective in the event Authors’ blind submission paper is accepted for publication by ACL, or upon the passing of two years from the date of submission, whichever event occurs first. If the blind submission paper is not accepted, the Content and associated peer reviewers content will remain confidential until the two years from the date of submission have passed.\n\nSection 5: Warranty\nAuthors represent and warrant that the Content is Authors’ original work and does not infringe on the proprietary rights of others. Authors further warrant that they have obtained all necessary permissions from any persons or organizations whose materials are included in the Content, and that the Content includes appropriate citations that give credit to the original sources.\n\nSection 6: Legal Relationship\nThe Parties agree that this Agreement is not intended to create any joint venture, partnership, or agency relationship of any kind; and both agree not to contract any obligations in the name of the other.\n\nAgreement\n\nBy selecting 'On behalf of all authors, I agree' below, I confirm that all Authors have agreed to the above terms and that I am authorized to execute this Agreement on their behalf. Optionally, if you wish to transfer the license to the peer reviewing and blind submission data of all previous versions of this paper submitted to ARR, please select 'On behalf of all authors, I agree for all previous versions of this submission'.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "On behalf of all authors, I agree",
                    "On behalf of all authors, I do not agree",
                    "On behalf of all authors, I agree for this and all previous versions of this submission"
                ],
                "input": "radio",
                "scroll": True,
                "optional": False
            }
        }
    },
    "section_2_permission_to_publish_peer_reviewers_content_agreement": {
        "order": 2,
        "description": "After the peer review process is concluded and upon acceptance of the paper, Authors have the option to grant ACL permission to publish peer reviewers content associated with the Content, which may include text, review form\nscores and metadata, charts, graphics, spreadsheets, and any other materials developed by peer reviewers in connection with the peer review process.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "Authors grant permission for ACL to publish peer reviewers' content",
                    "Authors decline to grant permission for ACL to publish peer reviewers' content"
                ],
                "input": "radio",
                "scroll": True,
                "optional": False
            }
        }
    },
}

hide_fields = [
    "TLDR",
    "preprint",
    "existing_preprints",
    "preferred_venue",
    "consent_to_share_data",
    "consent_to_share_submission_details",
    "existing_preprints",
    "Association_for_Computational_Linguistics_-_Blind_Submission_License_Agreement",
    "section_2_permission_to_publish_peer_reviewers_content_agreement",
    "reviewing_volunteers",
    "reviewing_no_volunteers_reason",
    "preprint_status",
]

hide_fields_from_public = [
    "software",
    "data",
    "previous_URL",
    "response_PDF",
    "reassignment_request_action_editor",
    "reassignment_request_reviewers",
    "justification_for_not_keeping_action_editor_or_reviewers",
    "A1_limitations_section",
    "A2_potential_risks",
    "A2_elaboration",
    "A3_abstract_and_introduction_summarize_claims",
    "A3_elaboration",
    "B_use_or_create_scientific_artifacts",
    "B1_cite_creators_of_artifacts",
    "B1_elaboration",
    "B2_discuss_the_license_for_artifacts",
    "B2_elaboration",
    "B3_artifact_use_consistent_with_intended_use",
    "B3_elaboration",
    "B4_data_contains_personally_identifying_info_or_offensive_content",
    "B4_elaboration",
    "B5_documentation_of_artifacts",
    "B5_elaboration",
    "B6_statistics_for_data",
    "B6_elaboration",
    "C_computational_experiments",
    "C1_model_size_and_budget",
    "C1_elaboration",
    "C2_experimental_setup_and_hyperparameters",
    "C2_elaboration",
    "C3_descriptive_statistics",
    "C3_elaboration",
    "C4_parameters_for_packages",
    "C4_elaboration",
    "D_human_subjects_including_annotators",
    "D1_instructions_given_to_participants",
    "D1_elaboration",
    "D2_recruitment_and_payment",
    "D2_elaboration",
    "D3_data_consent",
    "D3_elaboration",
    "D4_ethics_review_board_approval",
    "D4_elaboration",
    "D5_characteristics_of_annotators",
    "D5_elaboration",
    "E_ai_assistants_in_research_or_writing",
    "E1_information_about_use_of_ai_assistants",
    "E1_elaboration",
]

arr_official_review_content = {
    "paper_summary": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "type": "string"
            }
        },
        "order": 1,
        "description": "Describe what this paper is about. This should help action editors and area chairs to understand the topic of the work and highlight any possible misunderstandings. Maximum length 20000 characters."
    },
    "summary_of_strengths": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "type": "string"
            }
        },
        "order": 2,
        "description": "What are the major reasons to publish this paper at a selective *ACL venue? These could include novel and useful methodology, insightful empirical results or theoretical analysis, clear organization of related literature, or any other reason why interested readers of *ACL papers may find the paper useful. Maximum length 20000 characters."
    },
    "summary_of_weaknesses": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "type": "string"
            }
        },
        "order": 3,
        "description": "What are the concerns that you have about the paper that would cause you to favor prioritizing other high-quality papers that are also under consideration for publication? These could include concerns about correctness of the results or argumentation, limited perceived impact of the methods or findings (note that impact can be significant both in broad or in narrow sub-fields), lack of clarity in exposition, or any other reason why interested readers of *ACL papers may gain less from this paper than they would from other papers under consideration. Where possible, please number your concerns so authors may respond to them individually. Maximum length 20000 characters."
    },
    "comments_suggestions_and_typos": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "type": "string"
            }
        },
        "order": 4,
        "description": "If you have any comments to the authors about how they may improve their paper, other than addressing the concerns above, please list them here.\n Maximum length 20000 characters."
    },
    "confidence": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5,
                        "description": "5 = Positive that my evaluation is correct. I read the paper very carefully and am familiar with related work."
                    },
                    {
                        "value": 4,
                        "description": "4 = Quite sure. I tried to check the important points carefully. It's unlikely, though conceivable, that I missed something that should affect my ratings."
                    },
                    {
                        "value": 3,
                        "description": "3 =  Pretty sure, but there's a chance I missed something. Although I have a good feel for this area in general, I did not carefully check the paper's details, e.g., the math or experimental design."
                    },
                    {
                        "value": 2,
                        "description": "2 =  Willing to defend my evaluation, but it is fairly likely that I missed some details, didn't understand some central points, or can't be sure about the novelty of the work."
                    },
                    {
                        "value": 1,
                        "description": "1 = Not my area, or paper is very hard to understand. My evaluation is just an educated guess."
                    }
                ],
                "optional": False,
                "type": "integer"
            }
        },
        "order": 5
    },
    "soundness": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5.0,
                        "description": "5 = Excellent: This study is one of the most thorough I have seen, given its type."
                    },
                    {
                        "value": 4.5,
                        "description": "4.5 "
                    },
                    {
                        "value": 4.0,
                        "description": "4 = Strong: This study provides sufficient support for all of its claims/arguments. Some extra experiments could be nice, but not essential."
                    },
                    {
                        "value": 3.5,
                        "description": "3.5 "
                    },
                    {
                        "value": 3.0,
                        "description": "3 = Acceptable: This study provides sufficient support for its major claims/arguments. Some minor points may need extra support or details."
                    },
                    {
                        "value": 2.5,
                        "description": "2.5 "
                    },
                    {
                        "value": 2.0,
                        "description": "2 = Poor: Some of the main claims/arguments are not sufficiently supported. There are major technical/methodological problems."
                    },
                    {
                        "value": 1.5,
                        "description": "1.5 "
                    },
                    {
                        "value": 1.0,
                        "description": "1 = Major Issues: This study is not yet sufficiently thorough to warrant publication or is not relevant to ACL."
                    }
                ],
                "optional": False,
                "type": "float"
            }
        },
        "order": 6,
        "description": "How sound and thorough is this study? Does the paper clearly state scientific claims and provide adequate support for them? For experimental papers: consider the depth and/or breadth of the research questions investigated, technical soundness of experiments, methodological validity of evaluation. For position papers, surveys: consider the current state of the field is adequately represented, and main counter-arguments acknowledged. For resource papers: consider the data collection methodology, resulting data & the difference from existing resources are described in sufficient detail. Please adjust your baseline to account for the length of the paper."
    },
    "overall_assessment": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5.0,
                        "description": "5 = Top-Notch: This is one of the best papers I read recently, of great interest for the (broad or narrow) sub-communities that might build on it."
                    },
                    {
                        "value": 4.5,
                        "description": "4.5 "
                    },
                    {
                        "value": 4.0,
                        "description": "4 = This paper represents solid work, and is of significant interest for the (broad or narrow) sub-communities that might build on it."
                    },
                    {
                        "value": 3.5,
                        "description": "3.5 "
                    },
                    {
                        "value": 3.0,
                        "description": "3 = Good: This paper makes a reasonable contribution, and might be of interest for some (broad or narrow) sub-communities, possibly with minor revisions."
                    },
                    {
                        "value": 2.5,
                        "description": "2.5 "
                    },
                    {
                        "value": 2.0,
                        "description": "2 = Revisions Needed: This paper has some merit, but also significant flaws, and needs work before it would be of interest to the community."
                    },
                    {
                        "value": 1.5,
                        "description": "1.5 "
                    },
                    {
                        "value": 1.0,
                        "description": "1 = Major Revisions Needed: This paper has significant flaws, and needs substantial work before it would be of interest to the community."
                    },
                    {
                        "value": 0.0,
                        "description": "0 = This paper is not relevant to the *ACL community (for example, is in no way related to natural language processing)."
                    }
                ],
                "optional": False,
                "type": "float"
            }
        },
        "order": 7,
        "description": "Would you personally like to see this paper presented at an *ACL event that invites submissions on this topic? For example, you may feel that a paper should be presented if its contributions would be useful to its target audience, deepen the understanding of a given topic, or help establish cross-disciplinary connections. Note: Even high-scoring papers can be in need of minor changes (e.g. typos, non-core missing refs, etc.)."
    },
    "best_paper": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "Maybe",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "order": 8,
        "description": "Could the camera-ready version of this paper merit consideration for an 'outstanding paper' award (up to 2.5% of accepted papers at *ACL conferences will be recognized in this way)? Outstanding papers should be either fascinating, controversial, surprising, impressive, or potentially field-changing. Awards will be decided based on the camera-ready version of the paper."
    },
    "best_paper_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 9,
        "description": "If you answered Yes or Maybe to the question about consideration for an award, please briefly describe why."
    },
    "limitations_and_societal_impact": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 10,
        "description": "Have the authors adequately discussed the limitations and potential positive and negative societal impacts of their work? If not, please include constructive suggestions for improvement. Authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact. You are encouraged to think through whether any critical points are missing and provide these as feedback for the authors. Consider, for example, cases of exclusion of user groups, overgeneralization of findings, unfair impacts on traditionally marginalized populations, bias confirmation, under- and overexposure of languages or approaches, and dual use (see Hovy and Spruit, 2016, for examples of those). Consider who benefits from the technology if it is functioning as intended, as well as who might be harmed, and how. Consider the failure modes, and in case of failure, who might be harmed and how."
    },
    "ethical_concerns": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "type": "string",
                "default": "There are no concerns with this submission"
            }
        },
        "order": 11,
        "description": "Please review the ACL code of ethics (https://www.aclweb.org/portal/content/acl-code-ethics) and the ARR checklist submitted by the authors in the submission form. If there are ethical issues with this paper, please describe them and the extent to which they have been acknowledged or addressed by the authors. Otherwise, enter None."
    },
    "needs_ethics_review": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": True,
                "type": "string"
            }
        },
        "order": 12,
        "description": "Should this paper be sent for an in-depth ethics review? Before you answer this question, please refer to https://aclrollingreview.org/ethics-flagging-guidelines/ for guidelines on what papers should and shouldn't be flagged. If your answer is yes, then ensure you have explained why in the question above, and we will try to ensure that it receives a separate ethics review."
    },
    "reproducibility": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5,
                        "description": "5 = They could easily reproduce the results."
                    },
                    {
                        "value": 4,
                        "description": "4 = They could mostly reproduce the results, but there may be some variation because of sample variance or minor variations in their interpretation of the protocol or method."
                    },
                    {
                        "value": 3,
                        "description": "3 = They could reproduce the results with some difficulty. The settings of parameters are underspecified or subjectively determined, and/or the training/evaluation data are not widely available."
                    },
                    {
                        "value": 2,
                        "description": "2 = They would be hard pressed to reproduce the results: The contribution depends on data that are simply not available outside the author's institution or consortium and/or not enough details are provided."
                    },
                    {
                        "value": 1,
                        "description": "1 = They would not be able to reproduce the results here no matter how hard they tried."
                    }
                ],
                "optional": False,
                "type": "integer"
            }
        },
        "order": 13,
        "description": "Is there enough information in this paper for a reader to reproduce the main results, use results presented in this paper in future work (e.g., as a baseline), or build upon this work?"
    },
    "datasets": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5,
                        "description": "5 = Enabling: The newly released datasets should affect other people's choice of research or development projects to undertake."
                    },
                    {
                        "value": 4,
                        "description": "4 = Useful: I would recommend the new datasets to other researchers or developers for their ongoing work."
                    },
                    {
                        "value": 3,
                        "description": "3 = Potentially useful: Someone might find the new datasets useful for their work."
                    },
                    {
                        "value": 2,
                        "description": "2 = Documentary: The new datasets will be useful to study or replicate the reported research, although for other purposes they may have limited interest or limited usability. (Still a positive rating)"
                    },
                    {
                        "value": 1,
                        "description": "1 = No usable datasets submitted."
                    }
                ],
                "optional": False,
                "type": "integer"
            }
        },
        "order": 14,
        "description": "If the authors state (in anonymous fashion) that datasets will be released, how valuable will they be to others?"
    },
    "software": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5,
                        "description": "5 = Enabling: The newly released software should affect other people's choice of research or development projects to undertake."
                    },
                    {
                        "value": 4,
                        "description": "4 = Useful: I would recommend the new software to other researchers or developers for their ongoing work."
                    },
                    {
                        "value": 3,
                        "description": "3 = Potentially useful: Someone might find the new software useful for their work."
                    },
                    {
                        "value": 2,
                        "description": "2 = Documentary: The new software will be useful to study or replicate the reported research, although for other purposes it may have limited interest or limited usability. (Still a positive rating)"
                    },
                    {
                        "value": 1,
                        "description": "1 = No usable software released."
                    }
                ],
                "optional": False,
                "type": "integer"
            }
        },
        "order": 15,
        "description": "If the authors state (in anonymous fashion) that their software will be available, how valuable will it be to others?"
    },
    "Knowledge_of_or_educated_guess_at_author_identity": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "order": 16,
        "description": "Do you think you know who wrote this paper (at least one author name or affiliation)?"
    },
    "Knowledge_of_paper": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "N/A, I do not know anything about the paper from outside sources",
                    "Before the review process",
                    "After the review process started"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "order": 17,
        "description": "When did you come to know about the paper from outsde sources?"
    },
    "Knowledge_of_paper_source": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "N/A, I do not know anything about the paper from outside sources",
                    "Preprint on arxiv",
                    "Social media post",
                    "A research talk",
                    "I can guess",
                    "other (specify)"
                ],
                "optional": False,
                "type": "string[]"
            }
        },
        "order": 18,
        "description": "How did you come to know about the paper from outside sources?"
    },
    "Knowledge_of_paper_source_other": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "If you selected 'other' in the previous question, please provide details here.",
        "order": 19
    },
    "impact_of_knowledge_of_paper": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "N/A, I do not know anything about the paper from outside sources",
                    "Not at all",
                    "Not much",
                    "Somehow",
                    "A lot"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "How (if at all) do you think your comments and ratings might have been different without this outside knowledge?",
        "order": 20
    },
    "Knowledge_of_paper_additional": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "Is there anything you would like to explain about your answers to the last six questions? (optional)",
        "order": 21
    },
    "Knowledge_of_authors_guess": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "If you chose that you 'can guess' authors identity in the question above, please write your guess here. (optional)",
        "order": 22
    },
    "reviewer_certification": {
        "order": 23,
        "value": {
            "param": {
                "type": "string",
                "enum": [{ "value": "Yes", "description": "I certify that the review I entered accurately reflects my assessment of the work. If you used any type of automated tool to help you craft your review, I hereby certify that its use was restricted to improving grammar and style, and the substance of the review is either my own work or the work of an acknowledged secondary reviewer."}],
                "input": "checkbox"
            }
        }        
    }
}


arr_metareview_content = {
    "metareview" : {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 1,
        "description": "Describe what this paper is about. This should help SACs at publication venues understand what sessions the paper might fit in. Maximum 5000 characters. Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq"
    },
    "summary_of_reasons_to_publish": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 2,
        "description": "What are the major reasons to publish this paper at a *ACL venue? This should help SACs at publication venues understand why they might want to accept the paper. Maximum 5000 characters."
    },
    "summary_of_suggested_revisions": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 3,
        "description": "What revisions could the authors make to the research and the paper that would improve it? This should help authors understand the reviews in context, and help them plan any future resubmission. Maximum 5000 characters."
    },
    "overall_assessment": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5,
                        "description": "5 = The paper is largely complete and there are no clear points of revision"
                    },
                    {
                        "value": 4,
                        "description": "4 = There are minor points that may be revised"
                    },
                    {
                        "value": 3,
                        "description": "3 = There are major points that may be revised"
                    },
                    {
                        "value": 2,
                        "description": "2 = The paper would need significant revisions to reach a publishable state"
                    },
                    {
                        "value": 1,
                        "description": "1 = Even after revisions, the paper is not likely to be publishable at an *ACL venue"
                    }
                ],
                "optional": False,
                "type": "integer"
            }
        },
        "order": 4
    },
    "suggested_venues": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 5,
        "description": "You are encouraged to suggest conferences or workshops that would be suitable for this paper."
    },
    "best_paper_ae": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "Maybe",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "order": 6,
        "description": "Could the camera-ready version of this paper merit consideration for an 'outstanding paper' award (up to 2.5% of accepted papers at *ACL conferences will be recognized in this way)? Outstanding papers should be either fascinating, controversial, surprising, impressive, or potentially field-changing. Awards will be decided based on the camera-ready version of the paper."
    },
    "best_paper_ae_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "input": "textarea",
                "markdown": True,
                "type": "string"
            }
        },
        "order": 7,
        "description": "If you answered Yes or Maybe to the question about consideration for an award, please briefly describe why."
    },
    "ethical_concerns": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "input": "textarea",
                "markdown": True,
                "type": "string",
                "default": "There are no concerns with this submission"
            }
        },
        "order": 8,
        "description": "Independent of your judgement of the quality of the work, please review the ACL code of ethics (https://www.aclweb.org/portal/content/acl-code-ethics) and list any ethical concerns related to this paper. Maximum length 2000 characters. Otherwise, enter None"
    },
    "needs_ethics_review": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": True,
                "type": "string"
            }
        },
        "order": 9,
        "description": "Should this paper be sent for an in-depth ethics review? Before you answer this question, please refer to https://aclrollingreview.org/ethics-flagging-guidelines/ for guidelines on what papers should and shouldn't be flagged. If your answer is yes, then ensure you have explained why in the question above, and we will try to ensure that it receives a separate ethics review."
    },
    "author_identity_guess": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    {
                        "value": 5,
                        "description": "5 = From a violation of the anonymity-window or other double-blind-submission rules, I know/can guess at least one author's name."
                    },
                    {
                        "value": 4,
                        "description": "4 = From an allowed pre-existing preprint or workshop paper, I know/can guess at least one author's name."
                    },
                    {
                        "value": 3,
                        "description": "3 = From the contents of the submission itself, I know/can guess at least one author's name."
                    },
                    {
                        "value": 2,
                        "description": "2 = From social media/a talk/other informal communication, I know/can guess at least one author's name."
                    },
                    {
                        "value": 1,
                        "description": "1 = I do not have even an educated guess about author identity."
                    }
                ],
                "optional": False,
                "type": "integer"
            }
        },
        "order": 10,
        "description": "Do you know the author identity or have an educated guess?"
    },
    "great_reviews": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 11,
        "description": "Please list the ids of all reviewers who went beyond expectations in terms of providing informative and constructive reviews and discussion. For example: jAxb, zZac"
    },
    "poor_reviews": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "order": 12,
        "description": "Please list the ids of all reviewers whose reviews did not meet expectations. For example: jAxb, zZac"
    }
}

arr_ethics_review_content = {
    "recommendation": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "type": "string"
            }
        },
        "order": 1,
        "description": "Recommendation."
    },
    "issues": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": [
                    "1.1 Contribute to society and to human well-being, acknowledging that all people are stakeholders in computing",
                    "1.2 Avoid harm",
                    "1.3 Be honest and trustworthy",
                    "1.4 Be fair and take action not to discriminate",
                    "1.5 Respect the work required to produce new ideas, inventions, creative works, and computing artifacts",
                    "1.6 Respect privacy",
                    "1.7 Honor confidentiality",
                    "2.1 Strive to achieve high quality in both the processes and products of professional work",
                    "2.2 Maintain high standards of professional competence, conduct, and ethical practice",
                    "2.3 Know and respect existing rules pertaining to professional work",
                    "2.4 Accept and provide appropriate professional review",
                    "2.5 Give comprehensive and thorough evaluations of computer systems and their impacts, including analysis of possible risks",
                    "2.6 Perform work only in areas of competence",
                    "2.7 Foster public awareness and understanding of computing, related technologies, and their consequences",
                    "2.8 Access computing and communication resources only when authorized or when compelled by the public good",
                    "2.9 Design and implement systems that are robustly and usably secure",
                    "3.1 Ensure that the public good is the central concern during all professional computing work",
                    "3.2 Articulate, encourage acceptance of, and evaluate fulfillment of social responsibilities by members of the organization or group",
                    "3.3 Manage personnel and resources to enhance the quality of working life",
                    "3.4 Articulate, apply, and support policies and processes that reflect the principles of the Code",
                    "3.5 Create opportunities for members of the organization or group to grow as professionals",
                    "3.6 Use care when modifying or retiring systems",
                    "3.7 Recognize and take special care of systems that become integrated into the infrastructure of society",
                    "4.1 Uphold, promote, and respect the principles of the Code",
                    "4.2 Treat violations of the Code as inconsistent with membership in the ACM",
                    "None"
                ],
                "optional": False,
                "type": "string[]"
            }
        },
        "description": "Please check all relevant aspects of the ACL code of ethics which apply to the paper (either through omission or violation)",
        "order": 2
    },
    "explanation": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": False,
                "type": "string"
            }
        },
        "order": 3,
        "description": "Detailed explanation of your selection (max. 10000 characters)."
    }
}



arr_reviewer_ac_recognition_task_forum = {
    "title": "Requesting a Letter of Recognition",
    "instructions": "Please add a letter of recognition request to this forum if you want one for this month."
}

arr_reviewer_ac_recognition_task = {
    "request_a_letter_of_recognition":{
        "order": 1,
        "description": "If you want to receive a letter of recognition for your reviewing activities at ARR, please select 'Yes' below",
        "value": {
            "param": {
                "type": "string",
                "enum": ["Yes, please send me a letter of recognition for my service as a reviewer / AE", "No, I do not need a letter of recognition for my service as a reviewer / AE"],
                "input": "radio",
                "optional": False,
            }
        }
    }
}

arr_max_load_task_forum = {
    "title": "Unavailability and Maximum Load Request",
    "instructions": "Please complete this form to indicate your (un)availability for reviewing. If you do not complete this form, you will receive the default load of this cycle.\n\nIf you wish to change your maximum load, please delete your previous request using the trash can icon, refresh the page and submit a new request."
}

arr_max_load_task = {
    "maximum_load_this_cycle": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [0, 4, 5, 6, 7, 8],
                "optional": False,
                "type": "integer",
            }
        },
        "description": "Enter your maximum reviewing load for papers in this cycle. This refers only to the specific role mentioned at the top of this page. A load of '0' indicates you are unable to review new submissions.",
        "order": 1,
    },
    "maximum_load_this_cycle_for_resubmissions": {
        "value": {
            "param": {
                "input": "radio",
                "enum": ["Yes", "No"],
                "optional": False,
                "type": "string",
            }
        },
        "description": "Are you able to review resubmissions of papers you previously reviewed? (even if you answered '0' to the previous question)",
        "order": 2,
    },
    "next_available_month": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ],
                "optional": True,
                "type": "string",
            }
        },
        "description": "If you are going to be unavailable for an extended period of time, please indicate the next month that you will be available. Leave",
        "order": 4,
    },
    "next_available_year": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [datetime.today().year + i for i in range(5)],
                "optional": True,
                "type": "integer",
            }
        },
        "description": "If you are going to be unavailable for an extended period of time, please fill out the next year, in combination with the previously filled out month, that you will be available.",
        "order": 5,
    }
}

arr_reviewer_max_load_task = deepcopy(arr_max_load_task)

arr_reviewer_max_load_task["meta_data_donation"] = {
    "value": {
        "param": {
            "input": "radio",
            "enum": [
                "Yes, I consent to donating anonymous metadata of my review for research.",
                "No, I do not consent to donating anonymous metadata of my review for research."
            ],
            "type": "string",
        }
    },
    "description": "Do you agree for the anonymized metadata associated with your reviews produced in this cycle to be included in a publicly available dataset? This dataset WILL include scores, anonymized paper and reviewer IDs that allow grouping the reviews by paper and by reviewer, as well as meta-review decisions and other numerical and categorical metadata. This dataset WILL NOT include any textual or uniquely attributable data like names, submission titles and texts, review texts, author responses, etc.",
    "order": 3
}

arr_ac_max_load_task = deepcopy(arr_max_load_task)
arr_ac_max_load_task["maximum_load_this_cycle"] = {
        "value": {
            "param": {
                "input": "radio",
                "enum": [0, 6, 7, 8, 9, 10, 11, 12],
                "optional": False,
                "type": "integer",
            }
        },
        "description": "Enter your maximum reviewing load for papers in this cycle. This refers only to the specific role mentioned at the top of this page. A load of '0' indicates you are unable to review new submissions.",
        "order": 1,
    }
arr_sac_max_load_task = deepcopy(arr_max_load_task)
del arr_sac_max_load_task["maximum_load_this_cycle_for_resubmissions"]
arr_sac_max_load_task["maximum_load_this_cycle"] = {
    "value": {
        "param": {
            "optional": False,
            "type": "integer"
        }
    },
    "description": "Enter your maximum reviewing load for papers in this cycle. This refers only to the specific role mentioned at the top of this page. A load of '0' indicates you are unable to review new submissions.",
    "order": 1,
}

arr_reviewer_emergency_load_task_forum = {
    "title": "Emergency Reviewing Form",
    "instructions": "Use the form below to opt in as an emergency reviewer. Your new maximum load will be made immediately available to the editors.\n\nTo edit your agreement, please click the trash can button in the top right corner of your submitted form, refresh the page, and submit another form indicating your adjusted availability\n\nTo withdraw your agreement, please click the trash can button in the top right corner of your submitted form, refresh the page, and submit another form indicating \"No\" for the \"Emergency Reviewing Agreement\"\n\nThe emergency review due is at the start day and time of the Author response period. This is a hard deadline. You can find the start date and time on https://aclrollingreview.org/dates"
}

arr_reviewer_emergency_load_task = {
    "emergency_reviewing_agreement": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "By selecting Yes, you agree to being an emergency reviewer for this cycle.",
        "order": 1
    },
    "emergency_load": {
        "value": {
            "param": {
                "optional": True,
                "type": "integer"
            }
        },
        "description": "Enter your emergency reviewing load. This will be added to your originally submitted load.",
        "order": 2
    },
    "research_area": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": arr_tracks,
                "optional": True,
                "type": "string[]"
            }
        },
        "description": "Research Areas / Tracks. Select the most relevant research areas / tracks for your expertise",
        "order": 3
    }
}

arr_ac_emergency_load_task_forum = {
    "title": "Emergency Reviewing Form",
    "instructions": "Use the form below to opt in as an emergency action editor. Your new maximum load will be made immediately available to the senior action editors.\n\nTo edit your agreement, please click the trash can button in the top right corner of your submitted form, refresh the page, and submit another form indicating your adjusted availability.\n\nTo withdraw your agreement, please click the trash can button in the top right corner of your submitted form, refresh the page, and submit another form indicating \"No\" for the \"Emergency Metareviewing Agreement\"",
}

arr_ac_emergency_load_task = {
    "emergency_reviewing_agreement": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "By selecting Yes, you agree to being an emergency reviewer for this cycle.",
        "order": 1
    },
    "emergency_load": {
        "value": {
            "param": {
                "optional": True,
                "type": "integer"
            }
        },
        "description": "Enter your emergency reviewing load. This will be added to your originally submitted load.",
        "order": 2
    },
    "research_area": {
        "value": {
            "param": {
                "input": "checkbox",
                "enum": arr_tracks,
                "optional": True,
                "type": "string[]"
            }
        },
        "description": "Research Areas / Tracks. Select the most relevant research areas / tracks for your expertise",
        "order": 3
    }
}


arr_content_license_task_forum = {
    "title": "Association for Computational Linguistics - Peer Reviewer Content License Agreement",
    "instructions": "If you have not reviewed for the previous ARR cycle, please ignore this task. If you have reviewed, please read and decide whether to transfer the license to your reviewing data for this iteration of ARR.\n\n***DISCLAIMER***\n\nYour participation is strictly voluntary. By transferring this license you grant ACL the right to distribute the text of your review. In particular, we may include your review text and scores in research datasets without revealing the OpenReview identifier that produced the review. Keep in mind that as with any text, your identity might be approximated using author profiling techniques. Only reviews for accepted papers will be eventually made publicly available. The authors of the papers will have to agree to the release of the textual review data associated with their papers.\n\nName of the ACL Conference: previous ARR cycle\n\n**Introduction**\nThis Peer Reviewer Content License Agreement (“Agreement”) is entered into between the Association for Computational Linguistics (“ACL”) and the Peer Reviewer listed above in connection with content developed and contributed by Peer Reviewer during the peer review process (referred as “Peer Review Content”). In exchange of adequate consideration, ACL and the Peer Reviewer agree as follows:\n\n**Section 1: Grant of License**\nPeer Reviewer grants ACL a worldwide, irrevocable, and royalty-free license to use the Peer Review Content developed and prepared by Peer Reviewer in connection with the peer review process for the ACL Conference listed above, including but not limited to text, review form scores and metadata, charts, graphics, spreadsheets, and any other materials according to the following terms: A. For Peer Review Content associated with papers accepted for publication, and subject to the Authors permission, ACL may reproduce, publish, distribute, prepare derivative work, and otherwise make use of the Peer Review Content, and to sub-license the Peer Review Content to the public according to terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. B. For Peer Review Content associated with papers not accepted for publication, ACL may use the Peer Review Content for internal research, program analysis, and record- keeping purposes. Notwithstanding the foregoing, the Parties acknowledge and agree that this Agreement does not transfer to ACL the ownership of any proprietary rights pertaining to the Peer Review Content, and that Peer Review retains respective ownership in and to the Peer Review Content.\n\n**Section 2: Attribution and Public Access License**\nA.The Parties agree that for purpose of administering the public access license, ACL will be identified as the licensor of the Content with the following copyright notice: Copyright © 2022 administered by the Association for Computational Linguistics (ACL) on behalf of ACL content contributors: ______________ (list names of peer reviewers who wish to be attributed), and other contributors who wish to remain anonymous. Content displayed on this webpage is made available under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. B.In the event Peer Reviewer intends to modify the attribution displayed in connection with the copyright notice above, ACL will use reasonable efforts to modify the copyright notice after receipt of Peer Reviewer’s written request. Notwithstanding the foregoing, Peer Reviewer acknowledges and agrees that any modification in connection with attribution will not be retroactively applied. C.The Parties understand and acknowledge that the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License is irrevocable once granted unless the licensee breaches the public access license terms.\n\n**Section 3: Warranty**\nPeer Reviewer represents and warrants that the Content is Peer Reviewer’s original work and does not infringe on the proprietary rights of others. Peer Reviewer further warrants that he or she has obtained all necessary permissions from any persons or organizations whose materials are included in the Content, and that the Content includes appropriate citations that give credit to the original sources.\n\n**Section 4: Legal Relationship**\nThe Parties agree that this Agreement is not intended to create any joint venture, partnership, or agency relationship of any kind; and both agree not to contract any obligations in the name of the other.\n\n"
}

arr_content_license_task = {
    "attribution": {
        "order": 1,
        "description": "Unless the peer reviewer elects to be attributed according to Section 2, the peer reviewer’s name will not be identified in connection with publication of the Peer Review Content. If you wish to be attributed, please check the box below. ATTENTION: this will allow you to get credit for your reviews, but it will also DEANONYMIZE your reviews. Please select after careful consideration.",
         "value": {
            "param": {
                "type": "string",
                "enum": ["Yes, I wish to be attributed."],
                "input": "radio",
                "optional": True
            }
        }
    },
    "agreement": {
      "description": "By selecting 'I agree' below you confirm that you agree to this license agreement.",
      "order": 2,
      "value": {
            "param": {
                "type": "string",
                "enum": [
                    "I agree",
                    "I agree for this cycle and all future cycles until I explicitly revoke my decision",
                    "I do not agree"
                ],
                "input": "radio",
                "optional": False
            }
        }
    }
}

arr_metareview_license_task_forum = {
    "title": "Association for Computational Linguistics - Meta-reviewer Content License Agreement",
    "instructions": "If you have not meta-reviewed for this cycle, please ignore this task. If you have meta-reviewed, please read and decide whether to transfer the license to your meta-reviewing data for this iteration of ARR.\n\n*** DISCLAIMER ***\nYour participation is strictly voluntary. By transferring this license you grant ACL the right to distribute the text of your review. In particular, we may include your review text and scores in research datasets without revealing the OpenReview identifier that produced the review. Keep in mind that as with any text, your identity might be approximated using author profiling techniques. Only reviews for accepted papers will be eventually made publicly available. The authors of the papers will have to agree to the release of the textual review data associated with their papers.\n\nThis Meta-reviewer Content License Agreement (“Agreement”) is entered into between the Association for Computational Linguistics (“ACL”) and the Meta-reviewer listed above in connection with content developed and contributed by meta-reviewer during the peer review process (referred as “Meta-review Content”). In exchange of adequate consideration, ACL and the Meta-reviewer agree as follows:\n\nSection 1: Grant Of License\nMeta-reviewer grants ACL a worldwide, irrevocable, and royalty-free license to use the Meta-review Content developed and prepared by meta-reviewer in connection with the peer review process for the ACL Conference listed above, including but not limited to text, review form scores and metadata, charts, graphics, spreadsheets, and any other materials according to the following terms: A. For Meta-review Content associated with papers accepted for publication, and subject to the Authors permission, ACL may reproduce, publish, distribute, prepare derivative work, and otherwise make use of the Meta-review Content, and to sub-license the Meta-review Content to the public according to terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. B. For Meta-review Content associated with papers not accepted for publication, ACL may use the Meta-review Content for internal research, program analysis, and record- keeping purposes. Notwithstanding the foregoing, the Parties acknowledge and agree that this Agreement does not transfer to ACL the ownership of any proprietary rights pertaining to the Meta-review Content, and that Meta-reviewer retains respective ownership in and to the Meta-review Content.\n\nSection 2 Attribution and Public Access License\nA.The Parties agree that for purpose of administering the public access license, ACL will be identified as the licensor of the Content with the following copyright notice: Copyright © 2022 administered by the Association for Computational Linguistics (ACL) on behalf of ACL content contributors: ______________ (name of meta-reviewer who wishes to be attributed), and other contributors who wish to remain anonymous. Content displayed on this webpage is made available under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. B.In the event Meta-reviewer intends to modify the attribution displayed in connection with the copyright notice above, ACL will use reasonable efforts to modify the copyright notice after receipt of Meta-reviewer’s written request. Notwithstanding the foregoing, Meta-reviewer acknowledges and agrees that any modification in connection with attribution will not be retroactively applied. C.The Parties understand and acknowledge that the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License is irrevocable once granted unless the licensee breaches the public access license terms.\n\nSection 3 Warranty\nMeta-reviewer represents and warrants that the Content is Meta-reviewer’s original work and does not infringe on the proprietary rights of others. Meta-reviewer further warrants that he or she has obtained all necessary permissions from any persons or organizations whose materials are included in the Content, and that the Content includes appropriate citations that give credit to the original sources.\n\nSection 4 Legal Relationship\nThe Parties agree that this Agreement is not intended to create any joint venture, partnership, or agency relationship of any kind; and both agree not to contract any obligations in the name of the other."
}

arr_metareview_license_task = {
    "attribution": {
        "order": 1,
        "description": "Unless the meta-reviewer elects to be attributed according to Section 2, the meta-reviewer’s name will not be identified in connection with publication of the Meta-review Content. If you wish to be attributed, please check the box below. ATTENTION: this will allow you to get credit for your reviews, but it will also DEANONYMIZE your reviews. Please select after careful consideration.",
         "value": {
            "param": {
                "type": "string",
                "enum": ["Yes, I wish to be attributed."],
                "input": "radio",
                "optional": True
            }
        }
    },
    "agreement": {
      "description": "By selecting 'I agree' below you confirm that you agree to this license agreement.",
      "order": 2,
      "value": {
            "param": {
                "type": "string",
                "enum": [
                    "I agree",
                    "I do not agree"
                ],
                "input": "radio",
                "optional": False
            }
        }
    }
}

arr_registration_task_forum = {
    "title": "Registration",
    "instructions": "Please check below points and verify that you provided the required pieces of information in your OpenReview profile.\nView and edit your profile at https://openreview.net/profile\n\nSelect papers for your expertise by going to this cycle's console, clicking on the tasks tab and clicking \"Expertise Selection\"",
}

arr_registration_task = {
    "domains": {
        "order": 1,
        "description": "I confirm that I have specified the history of domains I am and previously was affiliated with.",
        "value": {
            "param": {
                "type": "string",
                "enum": ["Yes"],
                "input": "checkbox",
                "optional": False
            }
        }
    },
    "emails": {
        "order": 2,
        "description": "I confirm that I have specified all (professional) email addresses I use and used beforehand.",
        "value": {
            "param": {
                "type": "string",
                "enum": ["Yes"],
                "input": "checkbox",
                "optional": False
            }
        }
    },
    "DBLP": {
        "order": 3,
        "description": "I confirm that I specified the URL to my DBLP profile (if existent).",
        "value": {
            "param": {
                "type": "string",
                "enum": ["Yes"],
                "input": "checkbox",
                "optional": False
            }
        }
    },
    "semantic_scholar": {
        "order": 4,
        "description": "I confirm that I specified the URL to my Semantic Scholar profile (if existent).",
        "value": {
            "param": {
                "type": "string",
                "enum": ["Yes"],
                "input": "checkbox",
                "optional": False
            }
        }
    },
    "research_area": {
        "order": 5,
        "description": "Research Areas / Tracks. Select all relevant research areas / tracks that are the best fit for your expertise. These will be used to inform the reviewer and action editor assignment",
        "value": {
            "param": {
                "type": "string[]",
                "enum": arr_tracks,
                "input": "checkbox",
                "optional": False
            }
        }
    },
    "languages_studied": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "Please list the languages that fall udner your expertise, separated by commas.",
        "order": 6
    },
}

arr_desk_reject_verification = {
    "verification": {
        "order": 1,
        "description": "Indicate whether or not a decision to desk reject this paper has been made or not",
        "value": {
            "param": {
                "type": "string",
                "enum": ["I have checked the potential violation(s) and have decided to either desk reject this submission or decided that no further action is required."],
                "input": "checkbox",
                "optional": False
            }
        }
    }
}

arr_ae_checklist = {
    "appropriateness": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Is the paper appropriate to *ACL?",
        "order": 1
    },
    "formatting": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Is the paper properly formatted according to the template? Templates for *ACL conferences found here: https://github.com/acl-org/acl-style-files",
        "order": 2
    },
    "length": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Does the paper have the proper length? Short papers: 4 content pages maximum, Long papers: 8 content pages maximum, Ethical considerations: 1 content page maximum",
        "order": 3
    },
    "anonymity": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Is the paper anonymous?",
        "order": 4
    },
    "limitations": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Does the paper have a section entitled \"Limitations\"?",
        "order": 5
    },
    "responsible_checklist": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Have the authors completed the responsible NLP research checklist?",
        "order": 6
    },
    "potential_violation_justification": {
        "value": {
            "param": {
                "regex": ".{1,250}",
                "optional": False,
                "default": "There are no violations with this submission",
                "type": "string"
            }
        },
        "description": "Modify only if a violation is marked. If you have marked any violation on this checklist, please give a brief explanation of the issue",
        "order": 7
    },
    "number_of_assignments": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Does the submission have 3 reviewers?",
        "order": 8
    },
    "diversity": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Are the reviewers diverse, in regards to seniority, geographies and institutions? If not, answer 'no' and please modify the assignments",
        "order": 9
    },
    "need_ethics_review": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Should this paper be sent for an in-depth ethics review? We have a small ethics committee that can specially review very challenging papers when it comes to ethical issues. If this seems to be such a paper, then please explain why below, and we will try to ensure that it receives a separate review.",
        "order": 10
    },
    "ethics_review_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A (I answered no to the previous question)",
                "optional": False,
                "type": "string"
            }
        },
        "description": "Please provide a meaningful justification for why this paper needs an ethics review. Note that lack of ethical considerations section, limitations section, copyright details etc. should be directly communicated to the authors in your reviews, and often do not need a full ethics review. When in doubt, please flag. For more guidelines on ethics review flagging, see https://aclrollingreview.org/ethics-flagging-guidelines/",
        "order": 11
    },
    "resubmission": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "This paper is a not a resubmission"
                ],
                "optional": True,
                "type": "string"
            }
        },
        "description": "If the paper is a resubmission, does the link to the previous submission work?",
        "order": 12
    },
    "resubmission_reassignments": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No",
                    "This paper is a not a resubmission"
                ],
                "optional": True,
                "type": "string"
            }
        },
        "description": "If this is a resubmission, has the authors' request regarding keeping or changing reviewers been respected? If not, answer 'No' and please modify the assignments",
        "order": 13
    },
    "comment": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "Your comment or reply (max 10000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq",
        "order": 14
    }
}


arr_reviewer_checklist = {
    "appropriateness": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Is the paper appropriate to *ACL?",
        "order": 1
    },
    "formatting": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Is the paper properly formatted according to the template? Templates for *ACL conferences found here: https://github.com/acl-org/acl-style-files. Please note that ACL has separate LaTeX and Microsoft Word templates, and PDFs produced by these templates look different from each other.",
        "order": 2
    },
    "length": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Does the paper have the proper length? Short papers: 4 content pages maximum, Long papers: 8 content pages maximum, Ethical considerations and Limitations do not count toward this limit",
        "order": 3
    },
    "anonymity": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Is the paper anonymous?",
        "order": 4
    },
    "limitations": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Does the paper have a section entitled \"Limitations\"?",
        "order": 5
    },
    "responsible_checklist": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Have the authors completed the responsible NLP research checklist? The new format for the checklist document is here https://aclrollingreview.org/responsibleNLPresearch/.",
        "order": 6
    },
    "potential_violation_justification": {
        "value": {
            "param": {
                "regex": ".{1,250}",
                "optional": False,
                "default": "There are no violations with this submission",
                "type": "string"
            }
        },
        "description": "Modify only if a violation is marked. If you have marked any violation on this checklist, please give a brief explanation of the issue",
        "order": 7
    },
    "need_ethics_review": {
        "value": {
            "param": {
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": False,
                "type": "string"
            }
        },
        "description": "Should this paper be sent for an in-depth ethics review? We have a small ethics committee that can specially review very challenging papers when it comes to ethical issues. If this seems to be such a paper, then please explain why below, and we will try to ensure that it receives a separate review. Please refer to https://aclrollingreview.org/ethics-flagging-guidelines/",
        "order": 8
    },
    "ethics_review_justification": {
        "value": {
            "param": {
                "minLength": 1,
                "default": "N/A (I answered no to the previous question)",
                "optional": False,
                "type": "string"
            }
        },
        "description": "Please provide a meaningful justification for why this paper needs an ethics review. Note that lack of ethical considerations section, limitations section, copyright details etc. should be directly communicated to the authors in your reviews, and often do not need a full ethics review. When in doubt, please flag. For more guidelines on ethics review flagging, see https://aclrollingreview.org/ethics-flagging-guidelines/",
        "order": 9
    },
    "comment": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string"
            }
        },
        "description": "Your comment or reply (max 10000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq",
        "order": 10
    }
}

arr_review_rating_content = {
    "overall_review_rating": {
        "value": {
            "param": {
                "optional": False,
                "input": "radio",
                "enum": [
                    {
                        "value": 1,
                        "description": "1 = (Poor) - Superficial, unsubstantiated, and/or factually incorrect review. The reviewer completely misunderstood this work and its contributions."
                    },
                    {
                        "value": 2,
                        "description": "2 = (Below Average) - While some of reviewer's claims/observations stand, the review still contains a number of misconceptions and/or factually incorrect and/or unsubstantiated claims."
                    },
                    {
                        "value": 3,
                        "description": "3 = (Average): The review raises several valid points, but also contains some misconceptions, factual errors, and/or unsupported claims."
                    },
                    {
                        "value": 4,
                        "description": "4 = (Above Average) - Main contributions and shortcomings of the work are correctly identified and the work is assessed fairly. Nonetheless, the review still contains some (minor) incorrect observations or unsupported claims."
                    },
                    {
                        "value": 5,
                        "description": "5 = (Solid) - The review is thorough and accurate. The reviewer has correctly identified and fairly judged all strengths and shortcomings of the work. Claims are substantiated and suggestions and/or criticism constructive."
                    }
                ],
                "type": "integer"
            }
        },
        "order": 1,
        "description": "Select the score that, in your opinion, best reflects the quality of this review"
    },
    "aspect_understanding": {
        "value": {
            "param": {
                "optional": False,
                "input": "radio",
                "enum": [
                    {
                        "value": 1,
                        "description": "1 = (Fundamental misconception) - The reviewer completely misunderstood the main contributions (main point) of this work."
                    },
                    {
                        "value": 2,
                        "description": "2 = (Important misunderstanding(s)) - There is an important misunderstanding of one or more crucial parts/aspects of the work (e.g., motivation, novelty, methodology, experimental setup, empirical results)."
                    },
                    {
                        "value": 3,
                        "description": "3 = (Partial Understanding) - The reviewer generally understood work and some of the contributions, but also has a few clear misconceptions."
                    },
                    {
                        "value": 4,
                        "description": "4 = (Sufficient Understanding) - While the reviewer may have misunderstood some smaller bits (e.g., misinterpreted one piece of result), they have correctly understood the central contributions of the work."
                    },
                    {
                        "value": 5,
                        "description": "5 = (Complete Understanding) - The review reflects a complete understanding of the work and all of its aspects. There are no recognizable misconceptions or misunderstandings"
                    }
                ],
                "type": "integer"
            }
        },
        "order": 2,
        "description": "How well did the reviewer understand the contributions of the work?"
    },
    "aspect_substantiation": {
        "value": {
            "param": {
                "optional": False,
                "input": "radio",
                "enum": [
                    {
                        "value": 1,
                        "description": "1 = (Poor) - The vast majority of the claims in the review are vague, generic, and unsubstantiated. No comments that specifically relate to the content/substance of our work."
                    },
                    {
                        "value": 2,
                        "description": "2 = (Insufficient) - Few of the claims in the review are substantiated, i.e., supported by evidence"
                    },
                    {
                        "value": 3,
                        "description": "3 = (Average) - The review contains both valid and supported claims as well some unsubstantiated statements and opinions."
                    },
                    {
                        "value": 4,
                        "description": "4 = (Sufficient) - Most important claims are well justified although some claims and opinions require further substantiation."
                    },
                    {
                        "value": 5,
                        "description": "5 = (Solid) - The vast majority of the claims are meaningful and well supported with evidence; reviewer's opinions are well argued for."
                    }
                ],
                "type": "integer"
            }
        },
        "order": 3,
        "description": "How substantiated (i.e., supported by evidence) do you find the review's claims to be?"
    },
    "aspect_correctness": {
        "value": {
            "param": {
                "optional": False,
                "input": "radio",
                "enum": [
                    {
                        "value": 1,
                        "description": "1 = (Poor) - The vast majority of the reviewer's claims are factually incorrect, i.e., verifiably False."
                    },
                    {
                        "value": 2,
                        "description": "2 = (Insufficient) - Central claims made by the reviewer are (at least partially) incorrect. Correct claims refer to less relevant aspects of the work/paper."
                    },
                    {
                        "value": 3,
                        "description": "3 = (Average) - Some of the claims are correct, but some of the important claims are also at least in part (verifiably) incorrect."
                    },
                    {
                        "value": 4,
                        "description": "4 = (Sufficient) - The most prominent claims in the review are (mostly) correct. A few minor claims are (in part) incorrect."
                    },
                    {
                        "value": 5,
                        "description": "5 = (Solid) - All or (almost all) of the claims in the review are correct."
                    }
                ],
                "type": "integer"
            }
        },
        "order": 4,
        "description": "How factually correct are reviewer's claims?"
    },
    "aspect_constructiveness": {
        "value": {
            "param": {
                "optional": False,
                "input": "radio",
                "enum": [
                    {
                        "value": 1,
                        "description": "1 = (Poor) - Reviewer's remarks and points of criticism are unclear and non-actionable. After reading the review I/we don't know what in our work/paper needs to be improved and in what way."
                    },
                    {
                        "value": 2,
                        "description": "2 = (Insufficient) - A few of the raised points are clear and actionable, but the majority of the remarks are neither clear nor helpful for improving the work."
                    },
                    {
                        "value": 3,
                        "description": "3 = (Average) - The review offers some helpful comments and suggestions, but also a fair share of non-actionable criticism."
                    },
                    {
                        "value": 4,
                        "description": "4 = (Sufficient) - Many of the comments are helpful and offer directions for improving the work; some of the (arguably less relevant) remarks are clear nor helpful."
                    },
                    {
                        "value": 5,
                        "description": "5 = (Solid) - The review is very helpful and offers clarity in form of concrete aspects in which the work/paper could/should be improved."
                    }
                ],
                "type": "integer"
            }
        },
        "order": 5,
        "description": "How constructive/helpful are reviewer's remarks and points of criticism?"
    },
    "scope_impact_or_importance": {
        "value": {
            "param": {
                "optional": False,
                "input": "radio",
                "enum": [
                    "Not at all",
                    "Insufficiently",
                    "Sufficiently",
                    "Extensively"
                ],
                "type": "string"
            }
        },
        "order": 6,
        "description": "To which extent does the review discuss the (potential) impact of your work and its importance for NLP and/or respective subarea?"
    },
    "scope_originality_or_novelty": {
        "value": {
            "param": {
                "optional": False,
                "input": "radio",
                "enum": [
                    "Not at all",
                    "Insufficiently",
                    "Sufficiently",
                    "Extensively"
                ],
                "type": "string"
            }
        },
        "order": 7,
        "description": "To which extent does the review discuss the novelty of your work?"
    },
    "scope_correctness": {
        "value": {
            "param": {
                "optional": False,
                "input": "radio",
                "enum": [
                    "Not at all",
                    "Insufficiently",
                    "Sufficiently",
                    "Extensively"
                ],
                "type": "string"
            }
        },
        "order": 8,
        "description": "To which extent does the review mention the (in)correctness of your work (method choice, implementation, experimental setup, interpretation of results, etc.)?"
    },
    "scope_substance": {
        "value": {
            "param": {
                "optional": False,
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "type": "string"
            }
        },
        "order": 9,
        "description": "Does the review discuss whether the amount of work described in your paper is enough to warrant a (long/short) paper?"
    },
    "scope_meaningful_comparison": {
        "value": {
            "param": {
                "optional": False,
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "type": "string"
            }
        },
        "order": 10,
        "description": "Does the review discuss your (lack of) comparison against relevant related work?"
    },
    "scope_organization_or_presentation": {
        "value": {
            "param": {
                "optional": False,
                "input": "radio",
                "enum": [
                    "Yes",
                    "No"
                ],
                "type": "string"
            }
        },
        "order": 11,
        "description": " Does the review discuss the aspects of organization of your paper or the presentation of the content?"
    },
    "additional_comments": {
        "value": {
            "param": {
                "minLength": 1,
                "optional": True,
                "type": "string",
                "input": "textarea"
            }
        },
        "order": 12
    }
}

