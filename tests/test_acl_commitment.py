import openreview
import pytest
import datetime
import time
import os
import re

class TestACLCommitment():

    @pytest.fixture(scope="class")
    def conference(self, client):
        now = datetime.datetime.utcnow()
        #pc_client = openreview.Client(username='pc@eccv.org', password='1234')
        builder = openreview.conference.ConferenceBuilder(client)
        assert builder, 'builder is None'

        builder.set_conference_id('aclweb.org/ACL/2022/Conference')
        builder.set_conference_name('60th Annual Meeting of the Association for Computational Linguistics')
        builder.set_conference_short_name('ACL-2022')
        builder.set_homepage_header({
        'title': '60th Annual Meeting of the Association for Computational Linguistics',
        'subtitle': 'ACL-2022',
        'deadline': 'Submission Deadline: March 17, 2019 midnight AoE',
        'date': 'July 11-15, 2019',
        'website': ' https://2022.aclweb.org',
        'location': 'Dublin, Irelant'
        })
        builder.has_area_chairs(True)
        builder.has_senior_area_chairs(True)
        builder.set_submission_stage(name= 'Commitment_Submission',
        double_blind = True,
        due_date = now + datetime.timedelta(minutes = 10),
        additional_fields={
            "title": {
                "description": "Enter the title of the ARR submission that you want to commit to ACL 2022",
                "order": 1,
                "value-regex": ".{1,250}",
                "required": True
            },
            "paper_link": {
                "description": "The link to the paper on ARR (including id). For example: https://openreview.net/forum?id=xdbsU2zUa8O",
                "value-regex": "https://openreview.net/forum\\?id=.*",
                "required": True,
                "markdown": False
            },
            "paper_type": {
                "description": "Indicate whether this is a short (a small, focused contribution; a negative result; an opinion piece; or an interesting application nugget) or a long paper.",
                "value-radio": [
                    "Long paper (up to eight pages of content + unlimited references and appendices)",
                    "Short paper (up to four pages of content + unlimited references and appendices)"
                ],
                "required": True
            },
            "track": {
                "description": "Please enter the subject area under which the submission should be considered. ",
                "value-radio": [
                    "Computational Social Science and Cultural Analytics",
                    "Dialogue and Interactive Systems",
                    "Discourse and Pragmatics",
                    "Ethics in NLP",
                    "Generation",
                    "Information Extraction",
                    "Information Retrieval and Text Mining",
                    "Interpretability and Analysis of Models for NLP",
                    "Language Grounding to Vision, Robotics, and Beyond",
                    "Linguistic Theories, Cognitive Modeling and Psycholinguistics",
                    "Machine Learning for NLP",
                    "Machine Translation and Multilinguality",
                    "NLP Applications",
                    "Phonology, Morphology and Word Segmentation",
                    "Question Answering",
                    "Resources and Evaluation",
                    "Semantics: Lexical",
                    "Semantics: Sentence level, Textual Inference and Other areas",
                    "Sentiment Analysis, Stylistic Analysis, and Argument Mining",
                    "Speech and Multimodality",
                    "Summarization",
                    "Syntax: Tagging, Chunking and Parsing",
                    "Special Theme on Language Diversity: From Low Resource to Endangered Languages"
                ],
                "required": True
            },
            "comment": {
                "description": "(Optional) short comment to the Senior Area Chair (3000 characters) Note that these comments will only be visible to the Senior Area Chairs (SACs), and they will NOT go to the reviewers or to the Action Editors (responding to reviewers and Action Editors should be handled in a response letter if the authors decided to do a resubmission in ARR, which is a completely different process than committing a paper to ACL 2022). These comments to the SACs are mainly to raise concerns about objective misunderstandings by the reviewers and/or by the Action Editor about the technical aspect of the paper that the authors believe will help the SACs in their decision making process. ",
                "value-regex": "[\\S\\s]{1,3000}",
                "required": False,
                "markdown": True
            },
            "author_checklist": {
                "values-checkbox": [
                    "I confirm that I am one of the authors of this paper",
                    "I confirm that this link is for the latest version of the paper in ARR that has reviews"
                ],
                "required": True
            }
        },
        remove_fields=['authors', 'authorids', 'abstract', 'keywords', 'pdf', 'TL;DR'])

        conference = builder.get_result()
        conference.set_program_chairs(emails = ['pcs.acl2022@gmail.com'])
        return conference

    def test_post_submissions(self, client, conference, test_client, helpers):

        invitation = client.get_invitation(conference.get_submission_id())

        assert ['aclweb.org/ACL/2022/Conference', '{signatures}'] == invitation.reply['readers']['values-copied']
        assert ['aclweb.org/ACL/2022/Conference', '{signatures}'] == invitation.reply['writers']['values-copied']

        note = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~SomeFirstName_User1', 'aclweb.org/ACL/2022/Conference'],
            writers = [conference.id, '~SomeFirstName_User1'],
            signatures = ['~SomeFirstName_User1'],
            content = {
                'title': 'ARR Paper title',
                'paper_link': 'https://openreview.net/forum?id=sdfjenxw',
                'paper_type': 'Long paper (up to eight pages of content + unlimited references and appendices)',
                'track': 'Question Answering',
                'author_checklist': ['I confirm that I am one of the authors of this paper']
            }
        )
        test_client.post_note(note)

        helpers.await_queue()

        messages = client.get_messages(subject = 'ACL-2022 has received your submission titled ARR Paper title')
        assert len(messages) == 1

        messages[0]['content']['text'] == f'''<p>Your submission to ACL-2022 has been posted.</p>
<p>Submission Number: 1</p>
<p>Title: ARR Paper title</p>
<p>To view your submission, click here: <a href=\"http://localhost:3030/forum?id={note.id}\">http://localhost:3030/forum?id={note.id}</a></p>
'''

