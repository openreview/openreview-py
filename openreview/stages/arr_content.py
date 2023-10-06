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
            "type": "group[]",
            "regex": "^~\\S+$|([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,},){0,}([a-z0-9_\\-\\.]{1,}@[a-z0-9_\\-\\.]{2,}\\.[a-z]{2,})"
            }
        }
    },
    "TLDR": {
        "order": 4,
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
        "order": 5,
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
        "order": 6,
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
    "responsible_NLP_research": {
        "order": 7,
        "description": "Upload a single PDF of your completed responsible NLP research checklist (see https://aclrollingreview.org/responsibleNLPresearch/).",
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
        "order": 8,
        "description": "Short or long. See the CFP for the requirements for short and long papers.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "long",
                    "short"
                ],
                "input": "radio"
            }
        }
    },
    "research_area": {
        "order": 9,
        "description": "Research Areas / Tracks. Select the most relevant research area / track for your paper. This will be used to inform the reviewer and action editor assignment.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "Computational Social Science and Cultural Analytics",
                    "Dialogue and Interactive Systems",
                    "Discourse and Pragmatics",
                    "Efficient/Low-Resource Methods for NLP",
                    "Ethics, Bias, and Fairness",
                    "Generation",
                    "Information Extraction",
                    "Information Retrieval and Text Mining",
                    "Interpretability and Analysis of Models for NLP",
                    "Linguistic theories, Cognitive Modeling and Psycholinguistics",
                    "Machine Learning for NLP",
                    "Machine Translation",
                    "Multilinguality and Language Diversity",
                    "Multimodality and Language Grounding to Vision, Robotics and Beyond",
                    "Phonology, Morphology and Word Segmentation",
                    "Question Answering",
                    "Resources and Evaluation",
                    "Semantics: Lexical",
                    "Semantics: Sentence-level Semantics, Textual Inference and Other areas",
                    "Sentiment Analysis, Stylistic Analysis, and Argument Mining",
                    "Speech recognition, text-to-speech and spoken language understanding",
                    "Summarization",
                    "Syntax: Tagging, Chunking and Parsing / ML",
                    "NLP Applications"
                ],
                "input": "radio"
            }
        }
    },
    "previous_URL": {
        "order": 10,
        "description": "Provide the URL of your previous submission to ACL Rolling Review if this is a resubmission",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 500,
                "optional": True
            }
        }
    },
    "previous_PDF": {
      "description": "If this is a resubmission, upload a single PDF of your previous submission to ACL Rolling Review.",
      "order": 11,
      "value": {
            "param": {
                "type": "file",
                "maxSize": 80,
                "extensions": [
                    "pdf"
                ],
                "optional": True
            }
        }
    },
    "response_PDF": {
      "description": "If this is a resubmission, upload a single PDF describing how you have changed your paper in response to your previous round of reviews. Note: this should NOT be a printout of your comments from the in-cycle author response period. This should be a new document that maintains anonymity and describes changes since your last submission.",
      "order": 12,
      "value": {
            "param": {
                "type": "file",
                "maxSize": 80,
                "extensions": [
                    "pdf"
                ],
                "optional": True
            }
        }
    },
    "reassignment_request_action_editor": {
        "order": 13,
        "description": "Do you want your submission to go to a different action editor? If you want your submission to go to the same action editor and they are unavailable this cycle, you will be assigned a new action editor.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "Yes, I want a different action editor for our submission",
                    "No, I want the same action editor from our previous submission and understand that a new action editor may be assigned if the previous one is unavailable"
                ],
                "input": "radio",
                "optional": True
            }
        }
    },
    "reassignment_request_reviewers": {
        "order": 14,
        "description": "Do you want your submission to go to a different set of reviewers? If you want your submission to go to the same set of reviewers and at least one are unavailable this cycle, you will be assigned new reviewers in their place.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "Yes, I want a different set of reviewers",
                    "No, I want the same set of reviewers from our previous submission and understand that new reviewers may be assigned if any of the previous ones are unavailable"
                ],
                "input": "radio",
                "optional": True
            }
        }
    },
    "justification_for_not_keeping_action_editor_or_reviewers": {
        "order": 15,
        "description": "Please specify reason for any reassignment request. Reasons may include clear lack of expertise in the area or dismissing the work without any concrete comments regarding correctness of the results or argumentation, limited perceived impact of the methods or findings, lack of clarity in exposition, or other valid criticisms. It is up to the discretion of the action editors or editors in chief regarding whether to heed these requests.",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 10000,
                "optional": True
            }
        }
    },
    "software": {
        "order": 16,
        "description": "Each ARR submission can be accompanied by one .tgz or .zip archive containing software (max. 200MB).",
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
        }
    },
    "data": {
        "order": 17,
        "description": "Each ARR submission can be accompanied by one .tgz or .zip archive containing data (max. 200MB).",
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
        }
    },
    "preprint": {
        "order": 18,
        "description": "Would the authors like to have a public anonymous pre-print of the submission? This includes PDF, abstract and all supplemental material.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "yes",
                    "no"
                ],
                "input": "radio"
            }
        }
    },
    "existing_preprints": {
        "order": 19,
        "description": "If there are any publicly available non-anonymous preprints of this paper, please list them here (provide the URLs please).",
        "value": {
            "param": {
                "type": "string",
                "minLength": 1,
                "optional": True
            }
        }
    },
    "preferred_venue": {
        "order": 20,
        "description": "If you have a venue that you are hoping to submit this paper to, please enter it here. You must enter the designated acronym from this list: https://aclrollingreview.org/dates. Note that entering a preferred venue is not a firm commitment to submit your paper to this venue, but it will help ARR and the venue chairs in planning, so we highly recommend filling in your current intentions. Please enter only your first choice.",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 300,
                "optional": True
            }
        }
    },
    "consent_to_share_data": {
        "order": 21,
        "description": "I agree for the anonymized metadata associated with my submission to be included in a publicly available dataset. This dataset WILL include scores, anonymized paper and reviewer IDs that allow grouping the reviews by paper and by reviewer, as well as acceptance decisions and other numerical and categorical metadata. This dataset WILL NOT include any textual or uniquely attributable data like names, submission titles and texts, review texts, author responses, etc. Your decision to opt-in the data does not affect the reviewing of your submission in any way.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "yes",
                    "no"
                ],
                "input": "radio"
            }
        }
    },
    "consent_to_review": {
        "order": 22,
        "description": "By submitting this paper, all authors of this paper agree to serve as reviewers for ACL Rolling Review if eligible and invited.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "yes"
                ],
                "input": "radio"
            }
        }
    },
}

hide_fields = [
    "TLDR",
    "preprint",
    "existing_preprints",
    "preferred_venue",
    "consent_to_review",
    "consent_to_share_data",
    "software",
    "data",
    "responsible_NLP_research",
    "previous_URL",
    "previous_PDF",
    "response_PDF",
    "reassignment_request_action_editor",
    "reassignment_request_reviewers",
    "justification_for_not_keeping_action_editor_or_reviewers"
]

arr_official_review_content = {
    "confidence": {
        "order": 6,
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "5 = Positive that my evaluation is correct. I read the paper very carefully and am familiar with related work.",
                    "4 = Quite sure. I tried to check the important points carefully. It's unlikely, though conceivable, that I missed something that should affect my ratings.",
                    "3 =  Pretty sure, but there's a chance I missed something. Although I have a good feel for this area in general, I did not carefully check the paper's details, e.g., the math or experimental design.",
                    "2 =  Willing to defend my evaluation, but it is fairly likely that I missed some details, didn't understand some central points, or can't be sure about the novelty of the work.",
                    "1 = Not my area, or paper is very hard to understand. My evaluation is just an educated guess."
                ],
                "input": "radio",
                "optional": True
            }
        }
    },
    "paper_summary": {
        "order": 1,
        "description": "Describe what this paper is about. This should help action editors and area chairs to understand the topic of the work and highlight any possible misunderstandings. Maximum length 1000 characters.",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 20000,
                "markdown": True,
                "input": "textarea"
            }
        }
    },
    "summary_of_strengths": {
        "order": 2,
        "description": "What are the major reasons to publish this paper at a selective *ACL venue? These could include novel and useful methodology, insightful empirical results or theoretical analysis, clear organization of related literature, or any other reason why interested readers of *ACL papers may find the paper useful. Maximum length 5000 characters.",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 20000,
                "markdown": True,
                "input": "textarea"
            }
        }
    },
    "summary_of_weaknesses": {
        "order": 3,
        "description": "What are the concerns that you have about the paper that would cause you to favor prioritizing other high-quality papers that are also under consideration for publication? These could include concerns about correctness of the results or argumentation, limited perceived impact of the methods or findings (note that impact can be significant both in broad or in narrow sub-fields), lack of clarity in exposition, or any other reason why interested readers of *ACL papers may gain less from this paper than they would from other papers under consideration. Where possible, please number your concerns so authors may respond to them individually. Maximum length 5000 characters.",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 20000,
                "markdown": True,
                "input": "textarea"
            }
        }
    },
    "comments_suggestions_and_typos": {
        "order": 4,
        "description": "If you have any comments to the authors about how they may improve their paper, other than addressing the concerns above, please list them here.\n Maximum length 5000 characters.",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 20000,
                "markdown": True,
                "input": "textarea"
            }
        }
    },
    "overall_assessment": {
        "order": 5,
        "description": "Would you personally like to see this paper presented at an *ACL event that invites submissions on this topic? For example, you may feel that a paper should be presented if its contributions would be useful to its target audience, deepen the understanding of a given topic, or help establish cross-disciplinary connections. Note: Even high-scoring papers can be in need of minor changes (e.g. typos, non-core missing refs, etc.).",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "5 = Top-Notch: This is one of the best papers I read recently, of great interest for the (broad or narrow) sub-communities that might build on it.",
                    "4.5 ",
                    "4 = This paper represents solid work, and is of significant interest for the (broad or narrow) sub-communities that might build on it.",
                    "3.5 ",
                    "3 = Good: This paper makes a reasonable contribution, and might be of interest for some (broad or narrow) sub-communities, possibly with minor revisions.",
                    "2.5 ",
                    "2 = Revisions Needed: This paper has some merit, but also significant flaws, and needs work before it would be of interest to the community.",
                    "1.5 ",
                    "1 = Major Revisions Needed: This paper has significant flaws, and needs substantial work before it would be of interest to the community.",
                    "0 = This paper is not relevant to the *ACL community (for example, is in no way related to natural language processing)."
                ],
                "input": "radio"
            }
        }
    },
    "best_paper": {
        "order": 7,
        "description": "Could this be a best paper in a top-tier *ACL venue?",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "Yes",
                    "Maybe",
                    "No"
                ],
                "input": "radio"
            }
        }
    },
    "best_paper_justification": {
        "order": 8,
        "description": "If you answered Yes or Maybe to the question about consideration for an award, please briefly describe why.",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 5000,
                "markdown": True,
                "optional": True,
                "input": "textarea"
            }
        }
    },
    "limitations_and_societal_impact": {
        "order": 9,
        "description": "Have the authors adequately discussed the limitations and potential positive and negative societal impacts of their work? If not, please include constructive suggestions for improvement. Authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact. You are encouraged to think through whether any critical points are missing and provide these as feedback for the authors. Consider, for example, cases of exclusion of user groups, overgeneralization of findings, unfair impacts on traditionally marginalized populations, bias confirmation, under- and overexposure of languages or approaches, and dual use (see Hovy and Spruit, 2016, for examples of those). Consider who benefits from the technology if it is functioning as intended, as well as who might be harmed, and how. Consider the failure modes, and in case of failure, who might be harmed and how.",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 10000,
                "markdown": True,
                "optional": True,
                "input": "textarea"
            }
        }
    },
    "ethical_concerns": {
        "order": 10,
        "description": "Please review the ACL code of ethics (https://www.aclweb.org/portal/content/acl-code-ethics) and the ARR checklist submitted by the authors in the submission form. If there are ethical issues with this paper, please describe them and the extent to which they have been acknowledged or addressed by the authors.",
        "value": {
            "param": {
                "type": "string",
                "maxLength": 10000,
                "markdown": True,
                "input": "textarea"
            }
        }
    },
    "needs_ethics_review": {
        "order": 11,
        "description": "Should this paper be sent for an in-depth ethics review? We have a small ethics committee that can specially review very challenging papers when it comes to ethical issues. If this seems to be such a paper, then please explain why here, and we will try to ensure that it receives a separate review.",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "Yes",
                    "No"
                ],
                "optional": True,
                "markdown": True,
                "input": "radio"
            }
        }
    },
    "reproducibility": {
        "order": 12,
        "description": "Is there enough information in this paper for a reader to reproduce the main results, use results presented in this paper in future work (e.g., as a baseline), or build upon this work?",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "5 = They could easily reproduce the results.",
                    "4 = They could mostly reproduce the results, but there may be some variation because of sample variance or minor variations in their interpretation of the protocol or method.",
                    "3 = They could reproduce the results with some difficulty. The settings of parameters are underspecified or subjectively determined, and/or the training/evaluation data are not widely available.",
                    "2 = They would be hard pressed to reproduce the results: The contribution depends on data that are simply not available outside the author's institution or consortium and/or not enough details are provided.",
                    "1 = They would not be able to reproduce the results here no matter how hard they tried."
                ],
                "input": "radio"
            }
        }
    },
    "datasets": {
        "order": 13,
        "description": "If the authors state (in anonymous fashion) that datasets will be released, how valuable will they be to others?",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "5 = Enabling: The newly released datasets should affect other people's choice of research or development projects to undertake.",
                    "4 = Useful: I would recommend the new datasets to other researchers or developers for their ongoing work.",
                    "3 = Potentially useful: Someone might find the new datasets useful for their work.",
                    "2 = Documentary: The new datasets will be useful to study or replicate the reported research, although for other purposes they may have limited interest or limited usability. (Still a positive rating)",
                    "1 = No usable datasets submitted."
                ],
                "input": "radio"
            }
        }
    },
    "software": {
        "order": 14,
        "description": "If the authors state (in anonymous fashion) that their software will be available, how valuable will it be to others?",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "5 = Enabling: The newly released software should affect other people's choice of research or development projects to undertake.",
                    "4 = Useful: I would recommend the new software to other researchers or developers for their ongoing work.",
                    "3 = Potentially useful: Someone might find the new software useful for their work.",
                    "2 = Documentary: The new software will be useful to study or replicate the reported research, although for other purposes it may have limited interest or limited usability. (Still a positive rating)",
                    "1 = No usable software released."
                ],
                "input": "radio"
            }
        }
    },
    "author_identity_guess": {
        "order": 15,
        "description": "Do you know the author identity or have an educated guess?",
        "value": {
            "param": {
                "type": "string",
                "enum": [
                    "5 = From a violation of the anonymity-window or other double-blind-submission rules, I know/can guess at least one author's name.",
                    "4 = From an allowed pre-existing preprint or workshop paper, I know/can guess at least one author's name.",
                    "3 = From the contents of the submission itself, I know/can guess at least one author's name.",
                    "2 = From social media/a talk/other informal communication, I know/can guess at least one author's name.",
                    "1 = I do not have even an educated guess about author identity."
                ],
                "input": "radio"
            }
        }
    }
}