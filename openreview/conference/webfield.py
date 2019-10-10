from __future__ import absolute_import

import os
import json



class WebfieldBuilder(object):

    def __init__(self, client):
        self.client = client

    def __build_options(self, default, options):

        merged_options = {}
        for k in default:
            merged_options[k] = default[k]

        for o in options:
            merged_options[o] = options[o]

        return merged_options

    def set_landing_page(self, group, options = {}):
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
                content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
                content = content.replace("var VENUE_LINKS = [];", "var VENUE_LINKS = " + json.dumps(links) + ";")
                group.web = content
                return self.client.post_group(group)

        elif links:
            # parse existing webfield and add new links
            # get links array without square brackets
            link_str = json.dumps(links)
            link_str = link_str[1:-1]
            start_pos = group.web.find('VENUE_LINKS = [') + len('VENUE_LINKS = [')
            group.web = group.web[:start_pos] +link_str + ','+ group.web[start_pos:]
            return self.client.post_group(group)


    def set_home_page(self, group, layout, options = {}):

        default_header = {
            'title': group.id,
            'subtitle': group.id,
            'location': 'TBD',
            'date': 'TBD',
            'website': 'nourl',
            'instructions': '',
            'deadline': 'TBD'
        }

        header = self.__build_options(default_header, options)

        template_name = 'simpleConferenceWebfield.js'

        if layout == 'tabs':
            template_name = 'tabsConferenceWebfield.js'

        if layout == 'decisions':
            template_name = 'tabsConferenceDecisionsWebfield.js'

        with open(os.path.join(os.path.dirname(__file__), 'templates/' + template_name)) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + group.id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = '" + options.get('reviewers_name', '') + "';")
            content = content.replace("var AREA_CHAIRS_NAME = '';", "var AREA_CHAIRS_NAME = '" + options.get('area_chairs_name', '') + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + options.get('submission_id', '') + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + options.get('blind_submission_id') + "';")
            content = content.replace("var WITHDRAWN_INVITATION = '';", "var WITHDRAWN_INVITATION = '" + options.get('withdrawn_invitation', '') + "';")
            content = content.replace("var DECISION_INVITATION_REGEX = '';", "var DECISION_INVITATION_REGEX = '" + options.get('decision_invitation_regex', '') + "';")
            content = content.replace("var AREA_CHAIRS_ID = '';", "var AREA_CHAIRS_ID = '" + options.get('area_chairs_id', '') + "';")
            content = content.replace("var REVIEWERS_ID = '';", "var REVIEWERS_ID = '" + options.get('reviewers_id', '') + "';")
            content = content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + options.get('program_chairs_id', '') + "';")
            content = content.replace("var AUTHORS_ID = '';", "var AUTHORS_ID = '" + options.get('authors_id', '') + "';")
            content = content.replace("var DECISION_HEADING_MAP = {};", "var DECISION_HEADING_MAP = " + json.dumps(options.get('decision_heading_map', '{}'), sort_keys=True) + ";")
            content = content.replace("var WITHDRAWN_SUBMISSION_ID = '';", "var WITHDRAWN_SUBMISSION_ID = '" + options.get('withdrawn_submission_id', '') + "';")
            content = content.replace("var DESK_REJECTED_SUBMISSION_ID = '';", "var DESK_REJECTED_SUBMISSION_ID = '" + options.get('desk_rejected_submission_id', '') + "';")

            group.web = content
            group.signatures = [group.id]
            return self.client.post_group(group)

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
                        Where possible, your previously authored papers from selected conferences were imported from <a href=https://dblp.org>DBLP.org</a> to populate this list. The keywords in these papers will be used to recommend submissions for you during the bidding process, and to assign submissions to you during the review process.
                </p>
                <br>
                <p class=\"dark\"><strong>Important Notes:</strong></p>
                <ul>
                        <li>By default, each paper is considered, unless you click on \"Exclude\" for a paper.</li>
                        <li>Papers not included as part of this import process can be uploaded by using the Upload button below</b>.</li>
                        <li>When uploading a paper, <b>the upload will not appear on this page if you do not include your email address in the \"authorids\" field, but it will be included in the recommendations process, even if it does not appear here</b>.
                </ul>
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

            invitation.web = content
            return self.client.post_invitation(invitation)

    def set_bid_page(self, conference, invitation, group_id):

        sorted_tip = ''
        if conference.bid_stage.use_affinity_score:
            sorted_tip = '''
            <li>
                Papers are sorted based on keyword similarity with the papers
                that you provided in the Expertise Selection Interface.
            </li>'''

        instructions_html = '''
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
            <br>'''.format(sorted_tip=sorted_tip)

        default_header = {
            'title': conference.get_short_name() + ' Bidding Console',
            'instructions': instructions_html
        }

        header = self.__build_options(default_header, conference.get_bidpage_header())

        with open(os.path.join(os.path.dirname(__file__), 'templates/bidWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + conference.get_blind_submission_id() + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var BID_ID = '';", "var BID_ID = '" + invitation.id + "';")
            content = content.replace("var SUBJECT_AREAS = '';", "var SUBJECT_AREAS = " + str(conference.submission_stage.subject_areas) + ";")
            content = content.replace("var CONFLICT_SCORE_ID = '';", "var CONFLICT_SCORE_ID = '" + conference.get_conflict_score_id(group_id) + "';")

            if conference.bid_stage.use_affinity_score:
                content = content.replace("var AFFINITY_SCORE_ID = '';", "var AFFINITY_SCORE_ID = '" + conference.get_affinity_score_id(group_id) + "';")

            invitation.web = content
            return self.client.post_invitation(invitation)

    def set_recommendation_page(self, conference, invitation):

        default_header = {
            'title': conference.get_short_name() + ' Reviewer Recommendation Console',
            'instructions': '<p class="dark">Please select the reviewers you want to recommend for each paper.</p>\
                <p class="dark"><strong>Please note:</strong></p>\
                <ul>\
                    <li>The list of reviewers for each papers are sorted by assignment score.</li>\
                    <li>Assigned: reviewers assigned using the first macthing, Alternate: next possible reviewers to assign.</li>\
                </ul>\
                <p class="dark"><strong>A few tips:</strong></p>\
                <ul>\
                    <li>.</li>\
                    <li>.</li>\
                </ul>\
                <br>'
        }

        header = self.__build_options(default_header, {})

        with open(os.path.join(os.path.dirname(__file__), 'templates/recommendationWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + conference.get_blind_submission_id() + "';")
            content = content.replace("var SUBJECT_AREAS = '';", "var SUBJECT_AREAS = " + str(conference.submission_stage.subject_areas) + ";")

            invitation.web = content
            return self.client.post_invitation(invitation)

    def set_recruit_page(self, conference_id, invitation, options = {}):

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
            invitation.web = content
            return self.client.post_invitation(invitation)


    def set_author_page(self, conference, group):

        default_header = {
            'title': 'Authors Console',
            'instructions': '',
            'schedule': 'TBD'
        }

        header = self.__build_options(default_header, conference.get_authorpage_header())

        with open(os.path.join(os.path.dirname(__file__), 'templates/authorWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.id + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            group.web = content
            return self.client.post_group(group)

    def set_reviewer_page(self, conference, group):

        reviewers_name = conference.reviewers_name

        default_header = {
            'title': reviewers_name.replace('_', ' ') + ' Console',
            'instructions': '<p class="dark">This page provides information and status \
            updates for the ' + conference.get_short_name() + '. It will be regularly updated as the conference \
            progresses, so please check back frequently for news and other updates.</p>',
            'schedule': '<h4>Coming Soon</h4>\
            <p>\
                <em><strong>Please check back later for updates.</strong></em>\
            </p>'
        }

        header = self.__build_options(default_header, conference.get_reviewerpage_header())

        with open(os.path.join(os.path.dirname(__file__), 'templates/reviewerWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + conference.get_blind_submission_id() + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var REVIEWER_NAME = {};", "var REVIEWER_NAME = " + conference.reviewers_name + ";")
            content = content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + conference.review_stage.name + "';")
            content = content.replace("var LEGACY_INVITATION_ID = false;", "var LEGACY_INVITATION_ID = true;" if conference.legacy_invitation_id else "var LEGACY_INVITATION_ID = false;")
            group.web = content
            return self.client.post_group(group)

    def set_area_chair_page(self, conference, group):

        area_chair_name = conference.area_chairs_name

        default_header = {
            'title': area_chair_name.replace('_', ' ') + ' Console',
            'instructions': '<p class="dark">This page provides information and status \
            updates for the ' + conference.get_short_name() + '. It will be regularly updated as the conference \
            progresses, so please check back frequently for news and other updates.</p>',
            'schedule': '<h4>Coming Soon</h4>\
            <p>\
                <em><strong>Please check back later for updates.</strong></em>\
            </p>'
        }

        header = self.__build_options(default_header, conference.get_areachairpage_header())

        with open(os.path.join(os.path.dirname(__file__), 'templates/areachairWebfield.js')) as f:
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
            group.web = content
            return self.client.post_group(group)

    def set_program_chair_page(self, conference, group):

        program_chairs_name = conference.program_chairs_name

        instruction_str = '<p class="dark">This page provides information and status \
            updates for the ' + conference.get_short_name() + '. It will be regularly updated as the conference \
            progresses, so please check back frequently for news and other updates.</p>'

        header = {
            'title': program_chairs_name.replace('_', ' ') + ' Console',
            'instructions': instruction_str
        }

        submission_id = conference.get_submission_id()
        if conference.get_submissions():
            submission_id = conference.get_blind_submission_id()

        with open(os.path.join(os.path.dirname(__file__), 'templates/programchairWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var SHORT_PHRASE = '';", "var SHORT_PHRASE = '" + conference.short_name + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + submission_id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var SHOW_AC_TAB = false;", "var SHOW_AC_TAB = true;" if conference.use_area_chairs else "var SHOW_AC_TAB = false;")
            content = content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + conference.review_stage.name + "';")
            content = content.replace("var OFFICIAL_META_REVIEW_NAME = '';", "var OFFICIAL_META_REVIEW_NAME = '" + conference.meta_review_stage.name + "';")
            content = content.replace("var DECISION_NAME = '';", "var DECISION_NAME = '" + conference.decision_stage.name + "';")
            content = content.replace("var COMMENT_NAME = '';", "var COMMENT_NAME = '" + conference.comment_stage.name + "';")
            content = content.replace("var BID_NAME = '';", "var BID_NAME = '" + conference.bid_stage.name + "';")
            content = content.replace("var LEGACY_INVITATION_ID = false;", "var LEGACY_INVITATION_ID = true;" if conference.legacy_invitation_id else "var LEGACY_INVITATION_ID = false;")
            content = content.replace("var AUTHORS_ID = '';", "var AUTHORS_ID = '" + conference.get_authors_id() + "';")
            content = content.replace("var REVIEWERS_ID = '';", "var REVIEWERS_ID = '" + conference.get_reviewers_id() + "';")
            content = content.replace("var ENABLE_REVIEWER_REASSIGNMENT = false;", "var ENABLE_REVIEWER_REASSIGNMENT = true;" if conference.enable_reviewer_reassignment else "var ENABLE_REVIEWER_REASSIGNMENT = false;")
            if conference.has_area_chairs:
                content = content.replace("var AREA_CHAIRS_ID = '';", "var AREA_CHAIRS_ID = '" + conference.get_area_chairs_id() + "';")
            content = content.replace("var PROGRAM_CHAIRS_ID = '';", "var PROGRAM_CHAIRS_ID = '" + conference.get_program_chairs_id() + "';")
            if conference.request_form_id:
                content = content.replace("var REQUEST_FORM_ID = '';", "var REQUEST_FORM_ID = '" + conference.request_form_id + "';")
            group.web = content
            return self.client.post_group(group)

