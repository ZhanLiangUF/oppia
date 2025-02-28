# coding: utf-8
#
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

"""Tests for core.storage.opportunity.gae_models."""

from __future__ import absolute_import
from __future__ import unicode_literals

from core.platform import models
from core.tests import test_utils
import python_utils

MYPY = False
if MYPY: # pragma: no cover
    from mypy_imports import base_models
    from mypy_imports import opportunity_models

(base_models, opportunity_models) = models.Registry.import_models(
    [models.NAMES.base_model, models.NAMES.opportunity])


class ExplorationOpportunitySummaryModelUnitTest(test_utils.GenericTestBase):
    """Test the ExplorationOpportunitySummaryModel class."""

    def setUp(self) -> None:
        super(ExplorationOpportunitySummaryModelUnitTest, self).setUp() # type: ignore[no-untyped-call]

        opportunity_models.ExplorationOpportunitySummaryModel(
            id='opportunity_id1',
            topic_id='topic_id1',
            topic_name='A topic',
            story_id='story_id1',
            story_title='A story title',
            chapter_title='A chapter title',
            content_count=20,
            incomplete_translation_language_codes=['hi', 'ar'],
            translation_counts={},
            language_codes_needing_voice_artists=['en'],
            language_codes_with_assigned_voice_artists=[]
        ).put()
        opportunity_models.ExplorationOpportunitySummaryModel(
            id='opportunity_id2',
            topic_id='topic_id2',
            topic_name='A new topic',
            story_id='story_id2',
            story_title='A new story title',
            chapter_title='A new chapter title',
            content_count=120,
            incomplete_translation_language_codes=['hi'],
            translation_counts={},
            language_codes_needing_voice_artists=['en'],
            language_codes_with_assigned_voice_artists=[]
        ).put()

    def test_get_deletion_policy(self) -> None:
        self.assertEqual(
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_deletion_policy(),
            base_models.DELETION_POLICY.NOT_APPLICABLE)

    def test_get_all_translation_opportunities(self) -> None:
        results, cursor, more = (
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_all_translation_opportunities(5, None, 'hi'))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, 'opportunity_id1')
        self.assertEqual(results[1].id, 'opportunity_id2')
        self.assertFalse(more)
        self.assertTrue(isinstance(cursor, python_utils.BASESTRING))

    def test_get_all_translation_opportunities_pagination(self) -> None:
        results, cursor, more = (
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_all_translation_opportunities(1, None, 'hi'))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 'opportunity_id1')
        self.assertTrue(more)
        self.assertTrue(isinstance(cursor, python_utils.BASESTRING))

        results, new_cursor, more = (
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_all_translation_opportunities(1, cursor, 'hi'))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 'opportunity_id2')
        self.assertFalse(more)
        self.assertTrue(isinstance(new_cursor, python_utils.BASESTRING))

    def test_get_all_voiceover_opportunities(self) -> None:
        results, cursor, more = (
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_all_voiceover_opportunities(5, None, 'en'))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, 'opportunity_id1')
        self.assertEqual(results[1].id, 'opportunity_id2')
        self.assertFalse(more)
        self.assertTrue(isinstance(cursor, python_utils.BASESTRING))

    def test_get_all_voiceover_opportunities_pagination(self) -> None:
        results, cursor, more = (
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_all_voiceover_opportunities(1, None, 'en'))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 'opportunity_id1')
        self.assertTrue(more)
        self.assertTrue(isinstance(cursor, python_utils.BASESTRING))

        results, new_cursor, more = (
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_all_voiceover_opportunities(1, cursor, 'en'))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 'opportunity_id2')
        self.assertFalse(more)
        self.assertTrue(isinstance(new_cursor, python_utils.BASESTRING))

    def test_get_by_topic(self) -> None:
        model_list = (
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_by_topic('topic_id1'))
        # Ruling out the possibility of None for mypy type checking.
        assert model_list is not None
        self.assertEqual(len(model_list), 1)
        self.assertEqual(model_list[0].id, 'opportunity_id1')

        model_list = (
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_by_topic('topic_id2'))
        # Ruling out the possibility of None for mypy type checking.
        assert model_list is not None
        self.assertEqual(len(model_list), 1)
        self.assertEqual(model_list[0].id, 'opportunity_id2')

    def test_get_by_topic_for_non_existing_topic(self) -> None:
        model_list = (
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_by_topic('non_existing_topic_id'))
        # Ruling out the possibility of None for mypy type checking.
        assert model_list is not None
        self.assertEqual(len(model_list), 0)

    def test_delete_all(self) -> None:
        results, _, more = (
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_all_translation_opportunities(1, None, 'hi'))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 1)
        self.assertTrue(more)

        opportunity_models.ExplorationOpportunitySummaryModel.delete_all()

        results, _, more = (
            opportunity_models.ExplorationOpportunitySummaryModel
            .get_all_translation_opportunities(1, None, 'hi'))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 0)
        self.assertFalse(more)


class SkillOpportunityModelTest(test_utils.GenericTestBase):
    """Tests for the SkillOpportunityModel class."""

    def setUp(self) -> None:
        super(SkillOpportunityModelTest, self).setUp() # type: ignore[no-untyped-call]

        opportunity_models.SkillOpportunityModel(
            id='opportunity_id1',
            skill_description='A skill description',
            question_count=20,
        ).put()
        opportunity_models.SkillOpportunityModel(
            id='opportunity_id2',
            skill_description='A skill description',
            question_count=30,
        ).put()

    def test_get_deletion_policy(self) -> None:
        self.assertEqual(
            opportunity_models.SkillOpportunityModel.get_deletion_policy(),
            base_models.DELETION_POLICY.NOT_APPLICABLE)

    def test_get_skill_opportunities(self) -> None:
        results, cursor, more = (
            opportunity_models.SkillOpportunityModel
            .get_skill_opportunities(5, None))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, 'opportunity_id1')
        self.assertEqual(results[1].id, 'opportunity_id2')
        self.assertFalse(more)
        self.assertTrue(isinstance(cursor, python_utils.BASESTRING))

    def test_get_skill_opportunities_pagination(self) -> None:
        results, cursor, more = (
            opportunity_models.SkillOpportunityModel.get_skill_opportunities(
                1, None))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 'opportunity_id1')
        self.assertTrue(more)
        self.assertTrue(isinstance(cursor, python_utils.BASESTRING))

        results, cursor, more = (
            opportunity_models.SkillOpportunityModel.get_skill_opportunities(
                1, cursor))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 'opportunity_id2')
        self.assertFalse(more)
        self.assertTrue(isinstance(cursor, python_utils.BASESTRING))

    def test_delete_all_skill_opportunities(self) -> None:
        results, _, more = (
            opportunity_models.SkillOpportunityModel.get_skill_opportunities(
                1, None))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 1)
        self.assertTrue(more)

        opportunity_models.SkillOpportunityModel.delete_all()

        results, _, more = (
            opportunity_models.SkillOpportunityModel.get_skill_opportunities(
                1, None))
        # Ruling out the possibility of None for mypy type checking.
        assert results is not None
        self.assertEqual(len(results), 0)
        self.assertFalse(more)
