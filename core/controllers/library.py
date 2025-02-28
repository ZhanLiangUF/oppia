# Copyright 2014 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Controllers for the library page."""

from __future__ import absolute_import
from __future__ import unicode_literals

import logging
import string

from constants import constants
from core.controllers import acl_decorators
from core.controllers import base
from core.domain import collection_services
from core.domain import exp_services
from core.domain import summary_services
from core.domain import user_services
import feconf
import python_utils
import utils


def get_matching_activity_dicts(
        query_string, categories, language_codes, search_offset):
    """Given the details of a query and a search offset, returns a list of
    activity dicts that satisfy the query.

    Args:
        query_string: str. The search query string (this is what the user
            enters).
        categories: list(str). The list of categories to query for. If it is
            empty, no category filter is applied to the results. If it is not
            empty, then a result is considered valid if it matches at least one
            of these categories.
        language_codes: list(str). The list of language codes to query for. If
            it is empty, no language code filter is applied to the results. If
            it is not empty, then a result is considered valid if it matches at
            least one of these language codes.
        search_offset: str or None. Offset indicating where, in the list of
            exploration search results, to start the search from. If None,
            collection search results are returned first before the
            explorations.

    Returns:
        tuple. A tuple consisting of two elements:
            - list(dict). Each element in this list is a collection or
                exploration summary dict, representing a search result.
            - str. The exploration index offset from which to start the
                next search.
    """
    # We only populate collections in the initial load, since the current
    # frontend search infrastructure is set up to only deal with one search
    # offset at a time.
    # TODO(sll): Remove this special casing.
    collection_ids = []
    if not search_offset:
        collection_ids, _ = (
            collection_services.get_collection_ids_matching_query(
                query_string, categories, language_codes))

    exp_ids, new_search_offset = (
        exp_services.get_exploration_ids_matching_query(
            query_string, categories, language_codes, offset=search_offset))
    activity_list = (
        summary_services.get_displayable_collection_summary_dicts_matching_ids(
            collection_ids) +
        summary_services.get_displayable_exp_summary_dicts_matching_ids(
            exp_ids))

    if len(activity_list) == feconf.DEFAULT_QUERY_LIMIT:
        logging.exception(
            '%s activities were fetched to load the library page. '
            'You may be running up against the default query limits.'
            % feconf.DEFAULT_QUERY_LIMIT)
    return activity_list, new_search_offset


class OldLibraryRedirectPage(base.BaseHandler):
    """Redirects the old library URL to the new one."""

    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {
        'GET': {}
    }

    @acl_decorators.open_access
    def get(self):
        """Handles GET requests."""
        self.redirect(feconf.LIBRARY_INDEX_URL, permanent=True)


class LibraryIndexHandler(base.BaseHandler):
    """Provides data for the default library index page."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON
    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {
        'GET': {}
    }

    @acl_decorators.open_access
    def get(self):
        """Handles GET requests."""
        # TODO(sll): Support index pages for other language codes.
        summary_dicts_by_category = summary_services.get_library_groups([
            constants.DEFAULT_LANGUAGE_CODE])
        top_rated_activity_summary_dicts = (
            summary_services.get_top_rated_exploration_summary_dicts(
                [constants.DEFAULT_LANGUAGE_CODE],
                feconf.NUMBER_OF_TOP_RATED_EXPLORATIONS_FOR_LIBRARY_PAGE))
        featured_activity_summary_dicts = (
            summary_services.get_featured_activity_summary_dicts(
                [constants.DEFAULT_LANGUAGE_CODE]))

        preferred_language_codes = [constants.DEFAULT_LANGUAGE_CODE]
        if self.user_id:
            user_settings = user_services.get_user_settings(self.user_id)
            preferred_language_codes = user_settings.preferred_language_codes

        if top_rated_activity_summary_dicts:
            summary_dicts_by_category.insert(
                0, {
                    'activity_summary_dicts': top_rated_activity_summary_dicts,
                    'categories': [],
                    'header_i18n_id': (
                        feconf.LIBRARY_CATEGORY_TOP_RATED_EXPLORATIONS),
                    'has_full_results_page': True,
                    'full_results_url': feconf.LIBRARY_TOP_RATED_URL,
                    'protractor_id': 'top-rated',
                })
        if featured_activity_summary_dicts:
            summary_dicts_by_category.insert(
                0, {
                    'activity_summary_dicts': featured_activity_summary_dicts,
                    'categories': [],
                    'header_i18n_id': (
                        feconf.LIBRARY_CATEGORY_FEATURED_ACTIVITIES),
                    'has_full_results_page': False,
                    'full_results_url': None,
                })

        self.values.update({
            'activity_summary_dicts_by_category': (
                summary_dicts_by_category),
            'preferred_language_codes': preferred_language_codes,
        })
        self.render_json(self.values)


class LibraryGroupIndexHandler(base.BaseHandler):
    """Provides data for categories such as top rated and recently published."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON
    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {
        'GET': {
            'group_name': {
                'schema': {
                    'type': 'basestring',
                    'choices': [
                        feconf.LIBRARY_GROUP_RECENTLY_PUBLISHED,
                        feconf.LIBRARY_GROUP_TOP_RATED
                    ]
                }
            }
        }
    }

    @acl_decorators.open_access
    def get(self):
        """Handles GET requests for group pages."""
        # TODO(sll): Support index pages for other language codes.
        group_name = self.normalized_request.get('group_name')
        activity_list = []
        header_i18n_id = ''

        if group_name == feconf.LIBRARY_GROUP_RECENTLY_PUBLISHED:
            recently_published_summary_dicts = (
                summary_services.get_recently_published_exp_summary_dicts(
                    feconf.RECENTLY_PUBLISHED_QUERY_LIMIT_FULL_PAGE))
            if recently_published_summary_dicts:
                activity_list = recently_published_summary_dicts
                header_i18n_id = feconf.LIBRARY_CATEGORY_RECENTLY_PUBLISHED

        elif group_name == feconf.LIBRARY_GROUP_TOP_RATED:
            top_rated_activity_summary_dicts = (
                summary_services.get_top_rated_exploration_summary_dicts(
                    [constants.DEFAULT_LANGUAGE_CODE],
                    feconf.NUMBER_OF_TOP_RATED_EXPLORATIONS_FULL_PAGE))
            if top_rated_activity_summary_dicts:
                activity_list = top_rated_activity_summary_dicts
                header_i18n_id = feconf.LIBRARY_CATEGORY_TOP_RATED_EXPLORATIONS

        preferred_language_codes = [constants.DEFAULT_LANGUAGE_CODE]
        if self.user_id:
            user_settings = user_services.get_user_settings(self.user_id)
            preferred_language_codes = user_settings.preferred_language_codes

        self.values.update({
            'activity_list': activity_list,
            'header_i18n_id': header_i18n_id,
            'preferred_language_codes': preferred_language_codes,
        })
        self.render_json(self.values)


class SearchHandler(base.BaseHandler):
    """Provides data for activity search results."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON
    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {
        'GET': {
            'q': {
                'schema': {
                    'type': 'basestring'
                },
                'default_value': ''
            },
            'category': {
                'schema': {
                    'type': 'basestring',
                    'validators': [{
                        'id': 'is_search_query_string'
                    }, {
                        'id': 'is_regex_matched',
                        'regex_pattern': '[\\-\\w+()"\\s]*'
                    }]
                },
                'default_value': ''
            },
            'language_code': {
                'schema': {
                    'type': 'basestring',
                    'validators': [{
                        'id': 'is_search_query_string'
                    }, {
                        'id': 'is_regex_matched',
                        'regex_pattern': '[\\-\\w+()"\\s]*'
                    }]
                },
                'default_value': ''
            },
            'cursor': {
                'schema': {
                    'type': 'basestring'
                },
                'default_value': None
            }
        }
    }

    @acl_decorators.open_access
    def get(self):
        """Handles GET requests."""
        query_string = utils.unescape_encoded_uri_component(
            self.normalized_request.get('q'))
        # Remove all punctuation from the query string, and replace it with
        # spaces. See http://stackoverflow.com/a/266162 and
        # http://stackoverflow.com/a/11693937
        remove_punctuation_map = dict(
            (ord(char), None) for char in string.punctuation)
        query_string = query_string.translate(remove_punctuation_map)

        # If there is a category parameter, it should be in the following form:
        #     category=("Algebra" OR "Math")
        category_string = self.normalized_request.get('category')

        # The 2 and -2 account for the '("" and '")' characters at the
        # beginning and end.
        categories = (
            category_string[2:-2].split('" OR "') if category_string else [])

        # If there is a language code parameter, it should be in the following
        # form:
        #     language_code=("en" OR "hi")
        language_code_string = self.normalized_request.get('language_code')

        # The 2 and -2 account for the '("" and '")' characters at the
        # beginning and end.
        language_codes = (
            language_code_string[2:-2].split('" OR "')
            if language_code_string else [])

        # TODO(#11314): Change 'cursor' to 'offset' here and in the frontend.
        search_offset = self.normalized_request.get('cursor')

        activity_list, new_search_offset = get_matching_activity_dicts(
            query_string, categories, language_codes, search_offset)

        self.values.update({
            'activity_list': activity_list,
            'search_cursor': new_search_offset,
        })

        self.render_json(self.values)


class LibraryRedirectPage(base.BaseHandler):
    """An old 'gallery' page that should redirect to the library index page."""

    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {
        'GET': {}
    }

    @acl_decorators.open_access
    def get(self):
        """Handles GET requests."""
        self.redirect('/community-library')


class ExplorationSummariesHandler(base.BaseHandler):
    """Returns summaries corresponding to ids of public explorations. This
    controller supports returning private explorations for the given user.
    """

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON
    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {
        'GET': {
            'stringified_exp_ids': {
                'schema': {
                    'type': 'custom',
                    'obj_type': 'JsonEncodedInString'
                }
            },
            'include_private_explorations': {
                'schema': {
                    'type': 'bool'
                },
                'default_value': False
            }
        }
    }

    @acl_decorators.open_access
    def get(self):
        """Handles GET requests."""
        exp_ids = self.normalized_request.get('stringified_exp_ids')
        include_private_exps = self.normalized_request.get(
            'include_private_explorations')

        editor_user_id = self.user_id if include_private_exps else None
        if not editor_user_id:
            include_private_exps = False

        if (not isinstance(exp_ids, list) or not all(
                isinstance(
                    exp_id, python_utils.BASESTRING) for exp_id in exp_ids)):
            raise self.PageNotFoundException

        if include_private_exps:
            summaries = (
                summary_services.get_displayable_exp_summary_dicts_matching_ids(
                    exp_ids, user=self.user))
        else:
            summaries = (
                summary_services.get_displayable_exp_summary_dicts_matching_ids(
                    exp_ids))
        self.values.update({
            'summaries': summaries
        })
        self.render_json(self.values)


class CollectionSummariesHandler(base.BaseHandler):
    """Returns collection summaries corresponding to collection ids."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON
    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {
        'GET': {
            'stringified_collection_ids': {
                'schema': {
                    'type': 'custom',
                    'obj_type': 'JsonEncodedInString'
                }
            }
        }
    }

    @acl_decorators.open_access
    def get(self):
        """Handles GET requests."""
        collection_ids = (
            self.normalized_request.get('stringified_collection_ids'))

        summaries = (
            summary_services.get_displayable_collection_summary_dicts_matching_ids( # pylint: disable=line-too-long
                collection_ids))
        self.values.update({
            'summaries': summaries
        })
        self.render_json(self.values)
