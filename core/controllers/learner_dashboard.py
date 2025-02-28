# Copyright 2017 The Oppia Authors. All Rights Reserved.
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

"""Controllers for the learner dashboard."""

from __future__ import absolute_import
from __future__ import unicode_literals

from constants import constants
from core.controllers import acl_decorators
from core.controllers import base
from core.domain import exp_fetchers
from core.domain import feedback_services
from core.domain import learner_progress_services
from core.domain import subscription_services
from core.domain import suggestion_services
from core.domain import summary_services
from core.domain import user_services
import feconf
import python_utils
import utils


class OldLearnerDashboardRedirectPage(base.BaseHandler):
    """Redirects the old learner dashboard URL to the new one."""

    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {'GET': {}}

    @acl_decorators.open_access
    def get(self):
        """Handles GET requests."""
        self.redirect(feconf.LEARNER_DASHBOARD_URL, permanent=True)


class LearnerDashboardPage(base.BaseHandler):
    """Page showing the user's learner dashboard."""

    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {'GET': {}}

    @acl_decorators.can_access_learner_dashboard
    def get(self):
        """Handles GET requests."""
        self.render_template('learner-dashboard-page.mainpage.html')


class LearnerDashboardHandler(base.BaseHandler):
    """Provides data for the user's learner dashboard page."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON
    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {'GET': {}}

    @acl_decorators.can_access_learner_dashboard
    def get(self):
        """Handles GET requests."""
        (
            learner_progress, number_of_nonexistent_activities) = (
                learner_progress_services.get_activity_progress(self.user_id))

        completed_exp_summary_dicts = (
            summary_services.get_displayable_exp_summary_dicts(
                learner_progress.completed_exp_summaries))

        incomplete_exp_summary_dicts = (
            summary_services.get_displayable_exp_summary_dicts(
                learner_progress.incomplete_exp_summaries))

        completed_collection_summary_dicts = (
            learner_progress_services.get_collection_summary_dicts(
                learner_progress.completed_collection_summaries))
        incomplete_collection_summary_dicts = (
            learner_progress_services.get_collection_summary_dicts(
                learner_progress.incomplete_collection_summaries))

        completed_story_summary_dicts = (
            learner_progress_services.get_displayable_story_summary_dicts(
                self.user_id, learner_progress.completed_story_summaries))

        learnt_topic_summary_dicts = (
            learner_progress_services.get_displayable_topic_summary_dicts(
                self.user_id, learner_progress.learnt_topic_summaries))
        partially_learnt_topic_summary_dicts = (
            learner_progress_services.get_displayable_topic_summary_dicts(
                self.user_id,
                learner_progress.partially_learnt_topic_summaries))

        exploration_playlist_summary_dicts = (
            summary_services.get_displayable_exp_summary_dicts(
                learner_progress.exploration_playlist_summaries))
        collection_playlist_summary_dicts = (
            learner_progress_services.get_collection_summary_dicts(
                learner_progress.collection_playlist_summaries))

        topics_to_learn_summary_dicts = (
            learner_progress_services.get_displayable_topic_summary_dicts(
                self.user_id, learner_progress.topics_to_learn_summaries))
        all_topic_summary_dicts = (
            learner_progress_services.get_displayable_topic_summary_dicts(
                self.user_id, learner_progress.all_topic_summaries))
        untracked_topic_summary_dicts = (
            learner_progress_services
            .get_displayable_untracked_topic_summary_dicts(
                self.user_id, learner_progress.untracked_topic_summaries))

        full_thread_ids = subscription_services.get_all_threads_subscribed_to(
            self.user_id)
        if len(full_thread_ids) > 0:
            thread_summaries, number_of_unread_threads = (
                feedback_services.get_exp_thread_summaries(
                    self.user_id, full_thread_ids))
        else:
            thread_summaries, number_of_unread_threads = [], 0

        creators_subscribed_to = (
            subscription_services.get_all_creators_subscribed_to(self.user_id))
        creators_settings = user_services.get_users_settings(
            creators_subscribed_to)
        subscription_list = []

        for index, creator_settings in enumerate(creators_settings):
            subscription_summary = {
                'creator_picture_data_url': (
                    creator_settings.profile_picture_data_url),
                'creator_username': creator_settings.username,
                'creator_impact': (
                    user_services.get_user_impact_score(
                        creators_subscribed_to[index]))
            }

            subscription_list.append(subscription_summary)

        self.values.update({
            'completed_explorations_list': completed_exp_summary_dicts,
            'completed_collections_list': completed_collection_summary_dicts,
            'completed_stories_list': completed_story_summary_dicts,
            'learnt_topics_list': learnt_topic_summary_dicts,
            'incomplete_explorations_list': incomplete_exp_summary_dicts,
            'incomplete_collections_list': incomplete_collection_summary_dicts,
            'partially_learnt_topics_list': (
                partially_learnt_topic_summary_dicts),
            'exploration_playlist': exploration_playlist_summary_dicts,
            'collection_playlist': collection_playlist_summary_dicts,
            'topics_to_learn_list': topics_to_learn_summary_dicts,
            'all_topics_list': all_topic_summary_dicts,
            'untracked_topics': untracked_topic_summary_dicts,
            'number_of_nonexistent_activities': (
                number_of_nonexistent_activities),
            'completed_to_incomplete_collections': (
                learner_progress.completed_to_incomplete_collections),
            'completed_to_incomplete_stories': (
                learner_progress.completed_to_incomplete_stories),
            'learnt_to_partially_learnt_topics': (
                learner_progress.learnt_to_partially_learnt_topics),
            'thread_summaries': [s.to_dict() for s in thread_summaries],
            'number_of_unread_threads': number_of_unread_threads,
            'subscription_list': subscription_list
        })
        self.render_json(self.values)


class LearnerDashboardIdsHandler(base.BaseHandler):
    """Gets the progress of the learner.

    Gets the ids of all explorations and collections completed by the user,
    the activities currently being pursued, and the activities present in
    the playlist.
    """

    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {'GET': {}}

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    @acl_decorators.can_access_learner_dashboard
    def get(self):
        """Handles GET requests."""
        learner_dashboard_activities = (
            learner_progress_services.get_learner_dashboard_activities(
                self.user_id))

        self.values.update({
            'learner_dashboard_activity_ids': (
                learner_dashboard_activities.to_dict())
        })
        self.render_json(self.values)


class LearnerDashboardFeedbackThreadHandler(base.BaseHandler):
    """Gets all the messages in a thread."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON
    URL_PATH_ARGS_SCHEMAS = {
        'thread_id': {
            'schema': {
                'type': 'basestring',
                'validators': [{
                    'id': 'is_regex_matched',
                    'regex_pattern': constants.VALID_THREAD_ID_REGEX
                }]
            }
        }
    }
    HANDLER_ARGS_SCHEMAS = {'GET': {}}

    @acl_decorators.can_access_learner_dashboard
    def get(self, thread_id):
        """Handles GET requests."""
        messages = feedback_services.get_messages(thread_id)
        author_ids = [m.author_id for m in messages]
        authors_settings = user_services.get_users_settings(author_ids)

        message_ids = [m.message_id for m in messages]
        feedback_services.update_messages_read_by_the_user(
            self.user_id, thread_id, message_ids)

        message_summary_list = []
        suggestion = suggestion_services.get_suggestion_by_id(thread_id)
        suggestion_thread = feedback_services.get_thread(thread_id)

        exploration_id = feedback_services.get_exp_id_from_thread_id(thread_id)
        if suggestion:
            exploration = exp_fetchers.get_exploration_by_id(exploration_id)
            current_content_html = (
                exploration.states[
                    suggestion.change.state_name].content.html)
            suggestion_summary = {
                'suggestion_html': suggestion.change.new_value['html'],
                'current_content_html': current_content_html,
                'description': suggestion_thread.subject,
                'author_username': authors_settings[0].username,
                'author_picture_data_url': (
                    authors_settings[0].profile_picture_data_url),
                'created_on_msecs': utils.get_time_in_millisecs(
                    messages[0].created_on)
            }
            message_summary_list.append(suggestion_summary)
            messages.pop(0)
            authors_settings.pop(0)

        for m, author_settings in python_utils.ZIP(messages, authors_settings):

            if author_settings is None:
                author_username = None
                author_picture_data_url = None
            else:
                author_username = author_settings.username
                author_picture_data_url = (
                    author_settings.profile_picture_data_url)

            message_summary = {
                'message_id': m.message_id,
                'text': m.text,
                'updated_status': m.updated_status,
                'author_username': author_username,
                'author_picture_data_url': author_picture_data_url,
                'created_on_msecs': utils.get_time_in_millisecs(m.created_on)
            }
            message_summary_list.append(message_summary)

        self.render_json({
            'message_summary_list': message_summary_list
        })
