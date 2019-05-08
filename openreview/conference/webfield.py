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

        default_header = {
            'title': group.id,
            'description': ''
        }

        children_groups = self.client.get_groups(regex = group.id + '/[^/]+/?$')

        links = []

        for children in children_groups:
            links.append({ 'url': '/group?id=' + children.id, 'name': children.id})

        header = self.__build_options(default_header, options)

        with open(os.path.join(os.path.dirname(__file__), 'templates/landingWebfield.js')) as f:
            content = f.read()
            content = content.replace("var GROUP_ID = '';", "var GROUP_ID = '" + group.id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var VENUE_LINKS = [];", "var VENUE_LINKS = " + json.dumps(links) + ";")
            group.web = content
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
            content = content.replace("var DECISION_HEADING_MAP = {};", "var DECISION_HEADING_MAP = " + json.dumps(options.get('decision_heading_map', '{}')) + ";")

            group.web = content
            group.signatures = [group.id]
            return self.client.post_group(group)

    def set_bid_page(self, conference, invitation):

        default_header = {
            'title': conference.get_short_name() + ' Bidding Console',
            'instructions': '<p class="dark">Please indicate your level of interest in reviewing \
                the submitted papers below, on a scale from "Very Low" to "Very High".</p>\
                <p class="dark"><strong>Please note:</strong></p>\
                <ul>\
                    <li>Please update your Conflict of Interest details on your profile page, specifically "Emails", "Education and Career History" & "Advisors and Other Relations" fields.</li>\
                    <li>The default bid on each paper is \"No Bid\".</li>\
                </ul>\
                <p class="dark"><strong>A few tips:</strong></p>\
                <ul>\
                    <li>Please bid on as many papers as possible to ensure that your preferences are taken into account.</li>\
                    <li>For the best bidding experience, <strong>it is recommended that you filter papers by Subject Area</strong> and search for key phrases in paper metadata using the search form.</li>\
                </ul>\
                <p class="dark"><strong>Bid Score Value Mapping:</strong></p>\
                <ul>\
                    <li>Very high (+1.0)</li>\
                    <li>High (+0.5)</li>\
                    <li>Neutral, No Bid (0.0)</li>\
                    <li>Low (-0.5) </li>\
                    <li>Very Low (-1.0)</li>\
                </ul><br>'
        }

        header = self.__build_options(default_header, conference.get_bidpage_header())

        with open(os.path.join(os.path.dirname(__file__), 'templates/bidWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + conference.get_blind_submission_id() + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var BID_ID = '';", "var BID_ID = '" + conference.get_bid_id() + "';")
            content = content.replace("var SUBJECT_AREAS = '';", "var SUBJECT_AREAS = " + str(conference.get_subject_areas()) + ";")

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
            content = content.replace("var SUBJECT_AREAS = '';", "var SUBJECT_AREAS = " + str(conference.get_subject_areas()) + ";")

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
            content = content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + conference.review_name + "';")
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
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var AREA_CHAIR_NAME = '';", "var AREA_CHAIR_NAME = '" + conference.area_chairs_name + "';")
            content = content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + conference.review_name + "';")
            content = content.replace("var OFFICIAL_META_REVIEW_NAME = '';", "var OFFICIAL_META_REVIEW_NAME = '" + conference.meta_review_name + "';")
            content = content.replace("var LEGACY_INVITATION_ID = false;", "var LEGACY_INVITATION_ID = true;" if conference.legacy_invitation_id else "var LEGACY_INVITATION_ID = false;")
            group.web = content
            return self.client.post_group(group)

    def set_program_chair_page(self, conference, group):

        program_chairs_name = conference.program_chairs_name

        instruction_str = '<p class="dark">This page provides information and status \
            updates for the ' + conference.get_short_name() + '. It will be regularly updated as the conference \
            progresses, so please check back frequently for news and other updates.</p>\
                <ul>'

        if conference.use_area_chairs:
            instruction_str =  instruction_str + '<li>{0} Members - <a href=\"/group?id={1}&mode=info\">Accepted</a>, \
                <a href=\"/group?id={1}/Invited&mode=info\">Invited</a>, \
                <a href=\"/group?id={1}/Declined&mode=info\">Declined</a></li>'.format(conference.area_chairs_name.replace('_', ' '), conference.get_area_chairs_id())

        instruction_str = instruction_str + '<li>{0} Members - <a href=\"/group?id={1}&mode=info\">Accepted</a>, \
            <a href=\"/group?id={1}/Invited&mode=info\">Invited</a>, \
            <a href=\"/group?id={1}/Declined&mode=info\">Declined</a></li>'.format(conference.reviewers_name.replace('_', ' '), conference.get_reviewers_id())

        instruction_str = instruction_str + '</ul>'

        default_header = {
            'title': program_chairs_name.replace('_', ' ') + ' Console',
            'instructions': instruction_str
        }

        header = self.__build_options(default_header, {})

        submission_id = conference.get_submission_id()
        if next(conference.get_submissions(), None):
            submission_id = conference.get_blind_submission_id()

        with open(os.path.join(os.path.dirname(__file__), 'templates/programchairWebfield.js')) as f:
            content = f.read()
            content = content.replace("var CONFERENCE_ID = '';", "var CONFERENCE_ID = '" + conference.get_id() + "';")
            content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference.get_submission_id() + "';")
            content = content.replace("var BLIND_SUBMISSION_ID = '';", "var BLIND_SUBMISSION_ID = '" + submission_id + "';")
            content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
            content = content.replace("var SHOW_AC_TAB = false;", "var SHOW_AC_TAB = true;" if conference.use_area_chairs else "var SHOW_AC_TAB = false;")
            content = content.replace("var OFFICIAL_REVIEW_NAME = '';", "var OFFICIAL_REVIEW_NAME = '" + conference.review_name + "';")
            content = content.replace("var OFFICIAL_META_REVIEW_NAME = '';", "var OFFICIAL_META_REVIEW_NAME = '" + conference.meta_review_name + "';")
            content = content.replace("var DECISION_NAME = '';", "var DECISION_NAME = '" + conference.decision_name + "';")
            content = content.replace("var LEGACY_INVITATION_ID = false;", "var LEGACY_INVITATION_ID = true;" if conference.legacy_invitation_id else "var LEGACY_INVITATION_ID = false;")
            group.web = content
            return self.client.post_group(group)

