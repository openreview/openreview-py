from __future__ import absolute_import

import os
import json
import re

class WebfieldBuilder(object):

    def __init__(self, client):
        self.client = client

    def __build_options(self, default, options):

        merged_options = {}
        for k in default:
            merged_options[k] = default[k]

        for o in options:
            if options[o] is not None:
                merged_options[o] = options[o]

        return merged_options

    def __should_update(self, entity):
        return entity.details.get('writable', False) and (not entity.web or entity.web.startswith('// webfield_template'))

    def __update_invitation(self, invitation, content):
        current_invitation=self.client.get_invitation(invitation.id)
        if self.__should_update(current_invitation):
            current_invitation.web = content
            return self.client.post_invitation(current_invitation)
        else:
            return current_invitation

    def __update_group(self, group, content, signature=None):
        current_group=self.client.get_group(group.id)
        if signature:
            current_group.signatures=[signature]
        if self.__should_update(current_group):
            current_group.web = content
            return self.client.post_group(current_group)
        else:
            return current_group

    def set_landing_page(self, group, parentGroup, options = {}):
        # sets webfield to show links to child groups

        children_groups = self.client.get_groups(regex = group.id + '/[^/]+/?$')

        links = []
        for children in children_groups:
            if not group.web or (group.web and children.id not in group.web):
                links.append({ 'url': '/group?id=' + children.id, 'name': children.id})

        if not group.web:
            # create new webfield using template
            default_header = {
                'title': group.id,
                'description': ''
            }
            header = self.__build_options(default_header, options)

            with open(os.path.join(os.path.dirname(__file__), 'templates/landingWebfield.js')) as f:
                content = f.read()
                content = content.replace("var GROUP_ID = '';", "var GROUP_ID = '" + group.id + "';")
                if parentGroup:
                    content = content.replace("var PARENT_GROUP_ID = '';", "var PARENT_GROUP_ID = '" + parentGroup.id + "';")
                content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
                content = content.replace("var VENUE_LINKS = [];", "var VENUE_LINKS = " + json.dumps(links) + ";")
                return self.__update_group(group, content)

        elif links:
            # parse existing webfield and add new links
            # get links array without square brackets
            link_str = json.dumps(links)
            link_str = link_str[1:-1]
            start_pos = group.web.find('VENUE_LINKS = [') + len('VENUE_LINKS = [')
            return self.__update_group(group, group.web[:start_pos] +link_str + ','+ group.web[start_pos:])


    def set_home_page(self, conference, group, layout, options = {}):

        default_header = {
            'title': group.id,
            'subtitle': group.id,
            'location': 'TBD',
            'date': 'TBD',
            'website': 'nourl',
            'instructions': '',
            'deadline': 'TBD'
        }

        header = self.__build_options(default_header, conference.get_homepage_options())

        template_name = 'simpleConferenceWebfield.js'

        if layout == 'tabs':
            template_name = 'tabsConferenceWebfield.js'

        if layout == 'decisions':
            template_name = 'tabsConferenceDecisionsWebfield.js'

        with open(os.path.join(os.path.dirname(__file__), 'templates/' + template_name)) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + group.id + "';")
            content = content.replace("var PARENT_GROUP_ID = '';", "var PARENT_GROUP_ID = '" + options.get('parent_group_id', '')+ "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + conference.reviewers_name + "';")
            content = content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + conference.area_chairs_name + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + conference.get_blind_submission_id() + "';")
            content = content.replace("var DECISION_INVITATION_REGEX = '';", "var DECISION_INVITATION_REGEX = '" + options.get('decision_invitation_regex', '') + "';")
            content = content.replace("var AREA_CHAIRS_ID = '';", "var AREA_CHAIRS_ID = '" + conference.get_area_chairs_id() + "';")
            content = content.replace("var REVIEWERS_ID = '';", "var REVIEWERS_ID = '" + conference.get_reviewers_id() + "';")
            content = content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + conference.get_program_chairs_id() + "';")
            content = content.replace("var AUTHORS_ID = '';", "var AUTHORS_ID = '" + conference.get_authors_id() + "';")
            content = content.replace("var DECISION_HEADING_MAP = {};", "var DECISION_HEADING_MAP = " + json.dumps(options.get('decision_heading_map', '{}'), sort_keys=True) + ";")
            content = content.replace("var WITHDRAWN_SUBMISSION_ID = '';", "var WITHDRAWN_SUBMISSION_ID = '" + conference.submission_stage.get_withdrawn_submission_id(conference) + "';")
            content = content.replace("var DESK_REJECTED_SUBMISSION_ID = '';", "var DESK_REJECTED_SUBMISSION_ID = '" + conference.submission_stage.get_desk_rejected_submission_id(conference) + "';")
            content = content.replace("var PUBLIC = false;", "var PUBLIC = true;" if conference.submission_stage.public else "var PUBLIC = false;")
            content = content.replace("var AUTHOR_SUBMISSION_FIELD = '';", "var AUTHOR_SUBMISSION_FIELD = '" + ('content.authorids' if 'authorids' in conference.submission_stage.get_content() else 'signature') + "';")

            return self.__update_group(group, content, conference.id)

    def set_expertise_selection_page(self, conference, invitation):

        default_header = {
            'title': conference.get_short_name() + ' Expertise Selection',
            'instructions': '''
                <p class=\"dark\">Listed below are all the papers you have authored that exist in the OpenReview database.
                        <br>
                        <br>
                        <b>By default, we consider all of these papers to formulate your expertise. Please click on \"Exclude\" for papers that you do  NOT want to be used to represent your expertise.</b>
                        <br>
                        <br>
                        Your previously authored papers from selected conferences were imported automatically from <a href="https://dblp.org">DBLP.org</a>. The keywords in these papers will be used to rank submissions for you during the bidding process, and to assign submissions to you during the review process. If there are DBLP papers missing, you can add them by editing your <a href="/profile/edit">OpenReview profile</a> and then clicking on 'Add DBLP Papers to Profile'.
                </p>
                <br>
                    Papers not automatically included as part of this import process can be uploaded by using the <b>Upload</b> button. Make sure that your email is part of the "authorids" field of the upload form. Otherwise the paper will not appear in the list, though it will be included in the recommendations process. Only upload papers co-authored by you.
                <br>
                <br>
                <p class=\"dark\"> Please contact <a href=mailto:info@openreview.net>info@openreview.net</a> with any questions or concerns about this interface, or about the expertise scoring process.
                </p>'''
        }

        header = self.__build_options(default_header, conference.get_expertise_selection_page_header())

        with open(os.path.join(os.path.dirname(__file__), 'templates/expertiseBidWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + conference.get_blind_submission_id() + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var EXPERTISE_BID_ID = '';", "var EXPERTISE_BID_ID = '" + conference.get_expertise_selection_id() + "';")

            return self.__update_invitation(invitation, content)

    def set_bid_page(self, conference, invitation, stage):

        sorted_tip = ''
        if stage.score_ids:
            sorted_tip = '''
            <li>
                Papers are sorted based on keyword similarity with the papers
                that you provided in the Expertise Selection Interface.
            </li>'''
            if conference.get_invitation_id(name='TPMS_Score', prefix=stage.committee_id) in stage.score_ids:
                sorted_tip += '''
                <li>
                    Papers can be also sorted by TPMS score, change the sorting criteria using the 'Sort By' dropdown.
                </li>'''

        default_instructions = '''
            <p class="dark"><strong>Instructions:</strong></p>
            <ul>
                <li>
                    Please indicate your <strong>level of interest</strong> in
                    reviewing the submitted papers below,
                    on a scale from "Very Low" interest to "Very High" interest.
                </li>
                <li>
                    Please bid on as many papers as possible
                    to ensure that your preferences are taken into account.
                </li>
                <li>
                    Use the search field to filter papers by keyword or subject area.
                </li>
                <li>
                    Ensure that you have at least <strong>{request_count} bids</strong>.
                </li>
            </ul>
            <p class="dark"><strong>A few tips:</strong></p>
            <ul>
                <li>
                    Papers for which you have a conflict of interest are not shown.
                </li>
                <li>
                    Positive bids ("High" and "Very High") will, in most cases, increase the likelihood that you will be assigned that paper.
                </li>
                <li>
                    Negative bids ("Low" and "Very Low") will, in most cases, decrease the likelihood that you will be assigned that paper.
                </li>
                {sorted_tip}
            </ul>
            <br>'''

        instructions_html = stage.instructions if stage.instructions else default_instructions

        header = {
            'title': stage.committee_id.split('/')[-1].replace('_', ' ') + ' Bidding Console',
            'instructions': instructions_html.format(sorted_tip=sorted_tip, request_count=stage.request_count)
        }

        template = 'templates/profileBidWebfield.js' if stage.committee_id == conference.get_senior_area_chairs_id() else 'templates/paperBidWebfield.js'

        with open(os.path.join(os.path.dirname(__file__), template)) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + conference.get_blind_submission_id() + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var BID_ID = '';", "var BID_ID = '" + invitation.id + "';")
            content = content.replace("var SUBJECT_AREAS = '';", "var SUBJECT_AREAS = " + str(conference.submission_stage.subject_areas) + ";")
            content = content.replace("var CONFLICT_SCORE_ID = '';", "var CONFLICT_SCORE_ID = '" + conference.get_conflict_score_id(stage.committee_id) + "';")
            content = content.replace("var BID_OPTIONS = [];", "var BID_OPTIONS = " + json.dumps(stage.get_bid_options()) + ";")

            if stage.score_ids:
                content = content.replace("var SCORE_IDS = [];", "var SCORE_IDS = " + json.dumps(stage.score_ids) + ";")

            if stage.committee_id == conference.get_senior_area_chairs_id():
                content = content.replace("var PROFILE_GROUP_ID = '';", "var PROFILE_GROUP_ID = '" + conference.get_area_chairs_id() + "';")

            return self.__update_invitation(invitation, content)

    def set_recommendation_page(self, conference, invitation, assignment_title, score_ids, conflict_id, total_recommendations):

        default_header = {
            'title': conference.get_short_name() + ' Reviewer Recommendation',
            'instructions': '<p class="dark">Recommend a ranked list of reviewers for each of your assigned papers.</p>\
                <p class="dark"><strong>Instructions:</strong></p>\
                <ul>\
                    <li>For each of your assigned papers, please select ' + str(total_recommendations) + ' reviewers to recommend.</li>\
                    <li>Recommendations should each be assigned a number from 10 to 1, with 10 being the strongest recommendation and 1 the weakest.</li>\
                    <li>Reviewers who have conflicts with the selected paper are not shown.</li>\
                    <li>The list of reviewers for a given paper can be sorted by different parameters such as affinity score or bid. In addition, the search box can be used to search for a specific reviewer by name or institution.</li>\
                    <li>To get started click the button below.</li>\
                </ul>\
                <br>'
        }

        header = self.__build_options(default_header, {})

        start_param = conference.get_paper_assignment_id(conference.get_area_chairs_id()) + ',label:{assignment_title}'.format(assignment_title=assignment_title) + ',tail:{userId}'
        edit_param = invitation.id
        browse_param = ';'.join(score_ids)
        params = 'start={start_param}&traverse={edit_param}&edit={edit_param}&browse={browse_param}&hide={hide}&referrer=[Return Instructions](/invitation?id={edit_param})&maxColumns=2'.format(start_param=start_param, edit_param=edit_param, browse_param=browse_param, hide=conflict_id)
        with open(os.path.join(os.path.dirname(__file__), 'templates/recommendationWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var EDGE_BROWSER_PARAMS = '';", "var EDGE_BROWSER_PARAMS = '" + params + "';")

            return self.__update_invitation(invitation, content)

    def set_reviewer_proposed_assignment_page(self, conference, assignment_invitation, assignment_title, invite_assignment_invitation):

        reviewers_id=conference.get_reviewers_id()

        header = {
            'title': conference.get_short_name() + ' Reviewer Proposed Assignments',
            'instructions': '<p class="dark">Review the proposed reviewer assignments for each of your assigned papers.</p>\
                <p class="dark"><strong>Instructions:</strong></p>\
                <ul>\
                    <li>For each of your assigned papers, TODO.</li>\
                    <li>TODO.</li>\
                    <li>Reviewers who have conflicts with the selected paper are not shown.</li>\
                    <li>Reviewers that reached their custom max papers quota can not be assigned to other papers.</li>\
                    <li>The list of reviewers for a given paper can be sorted by different parameters such as affinity score or bid. In addition, the search box can be used to search for a specific reviewer by name, email or institution.</li>\
                    <li>To get started click the button below.</li>\
                </ul>\
                <br>'
        }

        score_ids = [
            conference.get_invitation_id('Affinity_Score', prefix=reviewers_id),
            conference.get_bid_id(reviewers_id),
            conference.get_custom_max_papers_id(reviewers_id) + ',head:ignore'
        ]

        start_param = f'{conference.get_paper_assignment_id(conference.get_area_chairs_id(), deployed=True)},tail:{{userId}}'
        traverse= f'{assignment_invitation.id}' + f',label:{assignment_title}' if assignment_title else ''
        edit_param = f'{traverse}' + f';{invite_assignment_invitation.id}' if invite_assignment_invitation else ''
        browse_param = ';'.join(score_ids)
        hide=conference.get_conflict_score_id(reviewers_id)
        params = f'start={start_param}&traverse={traverse}&edit={edit_param}&browse={browse_param}&hide={hide}&maxColumns=2&referrer=[Return Instructions](/invitation?id={assignment_invitation.id})'
        with open(os.path.join(os.path.dirname(__file__), 'templates/assignmentWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var EDGE_BROWSER_PARAMS = '';", "var EDGE_BROWSER_PARAMS = '" + params + "';")
            content = content.replace("var BUTTON_NAME = '';", "var BUTTON_NAME = '" + 'Propose Assignments' + "';")
            assignment_invitation.web=content
            assignment_invitation=self.client.post_invitation(assignment_invitation)

            return self.__update_invitation(assignment_invitation, content)

    def set_reduced_load_page(self, conference_id, invitation, options = {}):

        default_header = {
            'title': conference_id,
            'subtitle': conference_id,
            'location': 'TBD',
            'date': 'TBD',
            'website': 'nourl',
            'instructions': '',
            'deadline': 'TBD'
        }

        header = self.__build_options(default_header, options)

        with open(os.path.join(os.path.dirname(__file__), 'templates/recruitReducedLoadWeb.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference_id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            return self.__update_invitation(invitation, content)

    def set_recruit_page(self, conference_id, invitation, options = {}, reduced_load_id=None):

        default_header = {
            'title': conference_id,
            'subtitle': conference_id,
            'location': 'TBD',
            'date': 'TBD',
            'website': 'nourl',
            'instructions': '',
            'deadline': 'TBD'
        }

        header = self.__build_options(default_header, options)

        with open(os.path.join(os.path.dirname(__file__), 'templates/recruitResponseWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference_id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            if reduced_load_id:
                content = content.replace("var REDUCED_LOAD_INVITATION_ID = '';", "var REDUCED_LOAD_INVITATION_ID = '" + reduced_load_id + "';")
            else:
                ## Reduce load is disabled, so we should set an invalid invitation
                content = content.replace("var REDUCED_LOAD_INVITATION_ID = '';", "var REDUCED_LOAD_INVITATION_ID = '" + conference_id + '/-/no_name' + "';")
            return self.__update_invitation(invitation, content)

    def set_paper_recruitment_page(self, conference, invitation):

        with open(os.path.join(os.path.dirname(__file__), 'templates/paperRecruitResponseWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(conference.get_homepage_options()) + ";")
            return self.__update_invitation(invitation, content)

    def set_author_page(self, conference, group):

        default_header = {
            'title': 'Author Console',
            'instructions': '',
            'schedule': ''
        }

        header = self.__build_options(default_header, conference.get_authorpage_header())

        template_file = 'legacyAuthorWebfield' if conference.legacy_anonids else 'authorWebfield'

        with open(os.path.join(os.path.dirname(__file__), f'templates/{template_file}.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + conference.get_blind_submission_id() + "';")
            content = content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + conference.review_stage.name + "';")
            content = content.replace("var DECISION_NAME = '';", "var DECISION_NAME = '" + conference.decision_stage.name + "';")
            content = content.replace("var AUTHOR_SUBMISSION_FIELD = '';", "var AUTHOR_SUBMISSION_FIELD = '" + ('content.authorids' if 'authorids' in conference.submission_stage.get_content() else 'signature') + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            return self.__update_group(group, content)

    def set_reviewer_page(self, conference, group):

        reviewers_name = conference.reviewers_name

        default_header = {
            'title': reviewers_name.replace('_', ' ') + ' Console',
            'instructions': '<p class="dark">This page provides information and status \
            updates for the ' + conference.get_short_name() + '. It will be regularly updated as the conference \
            progresses, so please check back frequently.</p>',
            'schedule': ''
        }

        header = self.__build_options(default_header, conference.get_reviewerpage_header())

        template_file = 'legacyReviewerWebfield' if conference.legacy_anonids else 'reviewerWebfield'

        # Build reduced load invitation ID
        conf_id = conference.get_id()
        reduced_load_id = conf_id + '/' + reviewers_name + '/-/Reduced_Load'

        with open(os.path.join(os.path.dirname(__file__), f'templates/{template_file}.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + conference.get_blind_submission_id() + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var REVIEWER_NAME = '';", "var REVIEWER_NAME = '" + conference.reviewers_name + "';")
            content = content.replace("var AREACHAIR_NAME = '';", "var AREACHAIR_NAME = '" + conference.area_chairs_name + "';")
            content = content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + conference.review_stage.name + "';")
            content = content.replace("var CUSTOM_LOAD_INVITATION = '';", "var CUSTOM_LOAD_INVITATION = '" + reduced_load_id + "';")
            content = content.replace("var LEGACY_INVITATION_ID = false;", "var LEGACY_INVITATION_ID = true;" if conference.legacy_invitation_id else "var LEGACY_INVITATION_ID = false;")
            if conference.legacy_anonids:
                content = content.replace("var REVIEW_LOAD = 0;", "var REVIEW_LOAD = " + str(conference.default_reviewer_load.get(reviewers_name, 0)) + ";")
            elif conference.default_reviewer_load.get(reviewers_name, 0):
                content = content.replace("var REVIEW_LOAD = '';", "var REVIEW_LOAD = '" + str(conference.default_reviewer_load[reviewers_name]) + "';")
            return self.__update_group(group, content)


    def set_area_chair_page(self, conference, group):

        area_chair_name = conference.area_chairs_name

        default_header = {
            'title': area_chair_name.replace('_', ' ') + ' Console',
            'instructions': '<p class="dark">This page provides information and status \
            updates for the ' + conference.get_short_name() + '. It will be regularly updated as the conference \
            progresses, so please check back frequently.</p>',
            'schedule': '<h4>Coming Soon</h4>\
            <p>\
                <em><strong>Please check back later for updates.</strong></em>\
            </p>'
        }

        header = self.__build_options(default_header, conference.get_areachairpage_header())

        template_file = 'legacyAreachairWebfield' if conference.legacy_anonids else 'areachairWebfield'

        with open(os.path.join(os.path.dirname(__file__), f'templates/{template_file}.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + conference.get_blind_submission_id() + "';")
            content = content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var AREA_CHAIR_NAME = '';", "var AREA_CHAIR_NAME = '" + conference.area_chairs_name + "';")
            content = content.replace("var REVIEWER_NAME = '';", "var REVIEWER_NAME = '" + conference.reviewers_name + "';")
            content = content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + conference.review_stage.name + "';")
            content = content.replace("var OFFICIAL_META_REVIEW_NAME = '';", "var OFFICIAL_META_REVIEW_NAME = '" + conference.meta_review_stage.name + "';")
            content = content.replace("var LEGACY_INVITATION_ID = false;", "var LEGACY_INVITATION_ID = true;" if conference.legacy_invitation_id else "var LEGACY_INVITATION_ID = false;")
            content = content.replace("var ENABLE_REVIEWER_REASSIGNMENT = false;", "var ENABLE_REVIEWER_REASSIGNMENT = true;" if conference.enable_reviewer_reassignment else "var ENABLE_REVIEWER_REASSIGNMENT = false;")
            if conference.use_secondary_area_chairs:
                content = content.replace("var SECONDARY_AREA_CHAIR_NAME = '';", "var SECONDARY_AREA_CHAIR_NAME = '" + conference.secondary_area_chairs_name + "';")
                content = content.replace("var OFFICIAL_SECONDARY_META_REVIEW_NAME = '';", "var OFFICIAL_SECONDARY_META_REVIEW_NAME = 'Secondary_Meta_Review';")
            if conference.use_senior_area_chairs:
                content = content.replace("var SENIOR_AREA_CHAIRS_ID = '';", "var SENIOR_AREA_CHAIRS_ID = '" + conference.get_senior_area_chairs_id() + "';")
            return self.__update_group(group, content)


    def set_senior_area_chair_page(self, conference, group):

        senior_area_chair_name = conference.senior_area_chairs_name

        default_header = {
            'title': senior_area_chair_name.replace('_', ' ') + ' Console',
            'instructions': '<p class="dark">This page provides information and status \
            updates for the ' + conference.get_short_name() + '. It will be regularly updated as the conference \
            progresses, so please check back frequently.</p>',
            'schedule': '<h4>Coming Soon</h4>\
            <p>\
                <em><strong>Please check back later for updates.</strong></em>\
            </p>'
        }

        header = self.__build_options(default_header, conference.get_areachairpage_header())

        with open(os.path.join(os.path.dirname(__file__), f'templates/seniorAreaChairWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + conference.get_blind_submission_id() + "';")
            content = content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            content = content.replace("var AREA_CHAIR_NAME = '';", "var AREA_CHAIR_NAME = '" + conference.area_chairs_name + "';")
            content = content.replace("var REVIEWER_NAME = '';", "var REVIEWER_NAME = '" + conference.reviewers_name + "';")
            content = content.replace("var SENIOR_AREA_CHAIR_NAME = '';", "var SENIOR_AREA_CHAIR_NAME = '" + conference.senior_area_chairs_name + "';")
            content = content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + conference.review_stage.name + "';")
            content = content.replace("var OFFICIAL_META_REVIEW_NAME = '';", "var OFFICIAL_META_REVIEW_NAME = '" + conference.meta_review_stage.name + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var REVIEWERS_ID = '';", "var REVIEWERS_ID = '" + conference.get_reviewers_id() + "';")
            content = content.replace("var AREA_CHAIRS_ID = '';", "var AREA_CHAIRS_ID = '" + conference.get_area_chairs_id() + "';")
            return self.__update_group(group, content)

    def set_program_chair_page(self, conference, group):

        program_chairs_name = conference.program_chairs_name

        instruction_str = '<p class="dark">This page provides information and status \
            updates for the ' + conference.get_short_name() + '. It will be regularly updated as the conference \
            progresses, so please check back frequently.</p>'

        header = {
            'title': program_chairs_name.replace('_', ' ') + ' Console',
            'instructions': instruction_str
        }

        submission_id = conference.get_submission_id()
        if conference.get_submissions():
            submission_id = conference.get_blind_submission_id()

        template_file = 'legacyProgramchairWebfield' if conference.legacy_anonids else 'programchairWebfield'

        with open(os.path.join(os.path.dirname(__file__), f'templates/{template_file}.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + submission_id + "';")
            content = content.replace("var WITHDRAWN_SUBMISSION_ID = '';", "var WITHDRAWN_SUBMISSION_ID = '" + conference.submission_stage.get_withdrawn_submission_id(conference) + "';")
            content = content.replace("var DESK_REJECTED_SUBMISSION_ID = '';", "var DESK_REJECTED_SUBMISSION_ID = '" + conference.submission_stage.get_desk_rejected_submission_id(conference) + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + conference.review_stage.name + "';")
            content = content.replace("var OFFICIAL_META_REVIEW_NAME = '';", "var OFFICIAL_META_REVIEW_NAME = '" + conference.meta_review_stage.name + "';")
            content = content.replace("var DECISION_NAME = '';", "var DECISION_NAME = '" + conference.decision_stage.name + "';")
            if conference.comment_stage:
                content = content.replace("var COMMENT_NAME = '';", "var COMMENT_NAME = '" + conference.comment_stage.official_comment_name + "';")
            content = content.replace("var BID_NAME = '';", "var BID_NAME = 'Bid';")
            content = content.replace("var RECOMMENDATION_NAME = '';", "var RECOMMENDATION_NAME = '" + conference.recommendation_name + "';")
            content = content.replace("var SCORES_NAME = '';", "var SCORES_NAME = 'Affinity_Score';")
            content = content.replace("var LEGACY_INVITATION_ID = false;", "var LEGACY_INVITATION_ID = true;" if conference.legacy_invitation_id else "var LEGACY_INVITATION_ID = false;")
            content = content.replace("var AUTHORS_ID = '';", "var AUTHORS_ID = '" + conference.get_authors_id() + "';")
            content = content.replace("var REVIEWERS_ID = '';", "var REVIEWERS_ID = '" + conference.get_reviewers_id() + "';")
            content = content.replace("var ENABLE_REVIEWER_REASSIGNMENT = false;", "var ENABLE_REVIEWER_REASSIGNMENT = true;" if conference.enable_reviewer_reassignment else "var ENABLE_REVIEWER_REASSIGNMENT = false;")
            if conference.use_area_chairs:
                content = content.replace("var AREA_CHAIRS_ID = '';", "var AREA_CHAIRS_ID = '" + conference.get_area_chairs_id() + "';")
            if conference.use_senior_area_chairs:
                content = content.replace("var SENIOR_AREA_CHAIRS_ID = '';", "var SENIOR_AREA_CHAIRS_ID = '" + conference.get_senior_area_chairs_id() + "';")
            content = content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + conference.get_program_chairs_id() + "';")
            if conference.request_form_id:
                content = content.replace("var REQUEST_FORM_ID = '';", "var REQUEST_FORM_ID = '" + conference.request_form_id + "';")
            return self.__update_group(group, content)


    def edit_web_value(self, group, global_name, new_value):
        # replaces a value (ex. true)
        old_value = re.search("var "+global_name+" = .*;", group.web)
        group.web = group.web.replace(old_value.group(), "var "+global_name+" = "+new_value+";")
        return self.client.post_group(group)

    def edit_web_string_value(self, group, global_name, new_value):
        # replaces a string by adding the quotes
        old_value = re.search("var "+global_name+" = .*;", group.web)
        group.web = group.web.replace(old_value.group(),"var " + global_name + " = '" + new_value + "';")
        return self.client.post_group(group)
