# Copyright 2021 The Oppia Authors. All Rights Reserved.
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

"""Tests for mailchimp services."""

from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from core.platform.bulk_email import mailchimp_bulk_email_services
from core.tests import test_utils
import feconf
import python_utils

from mailchimp3 import mailchimpclient

from typing import Any, Dict


class MailchimpServicesUnitTests(test_utils.GenericTestBase):
    """Tests for mailchimp services."""

    def setUp(self) -> None:
        super(MailchimpServicesUnitTests, self).setUp() # type: ignore[no-untyped-call]
        self.user_email_1 = 'test1@example.com'
        self.user_email_2 = 'test2@example.com'
        self.user_email_3 = 'test3@example.com'

    class MockMailchimpClass(python_utils.OBJECT):
        """Class to mock Mailchimp class."""

        update_call_data: Dict[str, str] = {}

        class MailchimpLists(python_utils.OBJECT):
            """Class to mock Mailchimp lists object."""

            class MailchimpMembers(python_utils.OBJECT):
                """Class to mock Mailchimp members object."""

                def __init__(self) -> None:
                    self.users_data = [{
                        # Email: test1@example.com.
                        'email_hash': 'aa99b351245441b8ca95d54a52d2998c',
                        'status': 'unsubscribed'
                    }, {
                        # Email: test2@example.com.
                        'email_hash': '43b05f394d5611c54a1a9e8e20baee21',
                        'status': 'subscribed'
                    }]

                def get(
                        self, _list_id: str, subscriber_hash: str
                ) -> Dict[str, str]:
                    """Mocks the get function of the mailchimp api.

                    Args:
                        _list_id: str. List Id of mailchimp list.
                        subscriber_hash: str. Subscriber hash, which is an MD5
                            hash of subscriber's email ID.

                    Raises:
                        MailchimpError. Error 404 or 401 to mock API server
                            error.

                    Returns:
                        dict. The updated status dict for users.
                    """
                    if not self.users_data:
                        raise mailchimpclient.MailChimpError(
                            {'status': 401, 'detail': 'Server Error'})
                    for user in self.users_data:
                        if user['email_hash'] == subscriber_hash:
                            return user

                    raise mailchimpclient.MailChimpError({'status': 404})

                def update(
                        self,
                        _list_id: str,
                        subscriber_hash: str,
                        data: Dict[str, str]
                ) -> None:
                    """Mocks the update function of the mailchimp api. This
                    function just sets the payload data to a private variable
                    to test it.

                    Args:
                        _list_id: str. List Id of mailchimp list.
                        subscriber_hash: str. Subscriber hash, which is an MD5
                            hash of subscriber's email ID.
                        data: dict. Payload received.
                    """
                    for user in self.users_data:
                        if user['email_hash'] == subscriber_hash:
                            user['status'] = data['status']

                def create(self, _list_id: str, data: Dict[str, str]) -> None:
                    """Mocks the create function of the mailchimp api. This
                    function just sets the payload data to a private variable
                    to test it.

                    Args:
                        _list_id: str. List Id of mailchimp list.
                        data: dict. Payload received.
                    """
                    if data['email_address'] == 'test3@example.com':
                        self.users_data.append({
                            # Email: test3@example.com.
                            'email': 'fedd8b80a7a813966263853b9af72151',
                            'status': data['status']
                        })
                    elif data['email_address'] == 'test4@example.com':
                        raise mailchimpclient.MailChimpError({
                            'status': 400,
                            'title': 'Forgotten Email Not Subscribed'})
                    else:
                        raise mailchimpclient.MailChimpError({
                            'status': 404, 'title': 'Invalid email',
                            'detail': 'Server Issue'})

                def delete_permanent(
                        self, _list_id: str, subscriber_hash: str
                ) -> None:
                    """Mocks the delete function of the mailchimp api. This
                    function just sets the deleted user to a private variable
                    to test it.

                    Args:
                        _list_id: str. List Id of mailchimp list.
                        subscriber_hash: str. Subscriber hash, which is an MD5
                            hash of subscriber's email ID.
                    """
                    self.users_data = [
                        user for user in self.users_data
                        if user['email_hash'] != subscriber_hash]

            def __init__(self) -> None:
                self.members = self.MailchimpMembers()

        def __init__(self) -> None:
            self.lists = self.MailchimpLists()

    def test_get_subscriber_hash(self) -> None:
        sample_email = 'test@example.com'
        subscriber_hash = '55502f40dc8b7c769880b10874abc9d0'
        self.assertEqual(
            mailchimp_bulk_email_services._get_subscriber_hash(sample_email), # pylint: disable=protected-access
            subscriber_hash)

        sample_email_2 = 5
        with self.assertRaisesRegexp( # type: ignore[no-untyped-call]
            Exception, 'Invalid type for email. Expected string, received 5'):
            mailchimp_bulk_email_services._get_subscriber_hash(sample_email_2) # type: ignore[arg-type]  # pylint: disable=protected-access

    def test_get_mailchimp_class_error(self) -> None:
        observed_log_messages = []

        def _mock_logging_function(
                msg: str, *args: Any, **unused_kwargs: Any) -> None:
            """Mocks logging.exception().

            Args:
                msg: str. The logging message.
                *args: list(*). A list of arguments.
                **unused_kwargs: *. Keyword arguments.
            """
            observed_log_messages.append(msg % args)

        logging_swap = self.swap(logging, 'exception', _mock_logging_function)
        with logging_swap:
            mailchimp_bulk_email_services._get_mailchimp_class() # pylint: disable=protected-access
            self.assertItemsEqual( # type: ignore[no-untyped-call]
                observed_log_messages, ['Mailchimp API key is not available.'])

            observed_log_messages = []
            swap_api = self.swap(feconf, 'MAILCHIMP_API_KEY', 'key')
            with swap_api:
                mailchimp_bulk_email_services._get_mailchimp_class() # pylint: disable=protected-access
                self.assertItemsEqual( # type: ignore[no-untyped-call]
                    observed_log_messages, ['Mailchimp username is not set.'])

            # For the tests below, the email ID for the user doesn't matter
            # since the function should return earlier if mailchimp api key or
            # username is not set.
            # Permanently deletes returns None when mailchimp keys are not set.
            self.assertIsNone(
                mailchimp_bulk_email_services.permanently_delete_user_from_list( # type: ignore[func-returns-value]
                    'sample_email'))
            self.assertFalse(
                mailchimp_bulk_email_services.add_or_update_user_status(
                    'sample_email', True))

    def test_add_or_update_mailchimp_user_status(self) -> None:
        mailchimp = self.MockMailchimpClass()
        swapped_mailchimp = lambda: mailchimp
        swap_mailchimp_context = self.swap(
            mailchimp_bulk_email_services, '_get_mailchimp_class',
            swapped_mailchimp)
        swap_api = self.swap(feconf, 'MAILCHIMP_API_KEY', 'key')
        swap_username = self.swap(feconf, 'MAILCHIMP_USERNAME', 'username')

        with swap_mailchimp_context, swap_api, swap_username:
            # Tests condition where user was initally unsubscribed in list and
            # becomes subscribed.
            self.assertEqual(
                mailchimp.lists.members.users_data[0]['status'], 'unsubscribed')
            mailchimp_bulk_email_services.add_or_update_user_status(
                self.user_email_1, True)
            self.assertEqual(
                mailchimp.lists.members.users_data[0]['status'], 'subscribed')

            # Tests condition where user was initally subscribed in list and
            # becomes unsubscribed.
            self.assertEqual(
                mailchimp.lists.members.users_data[1]['status'],
                'subscribed')
            mailchimp_bulk_email_services.add_or_update_user_status(
                self.user_email_2, False)
            self.assertEqual(
                mailchimp.lists.members.users_data[1]['status'],
                'unsubscribed')

            # Creates a mailchimp entry for a new user.
            self.assertEqual(len(mailchimp.lists.members.users_data), 2)
            return_status = (
                mailchimp_bulk_email_services.add_or_update_user_status(
                    self.user_email_3, True))
            self.assertTrue(return_status)
            self.assertEqual(
                mailchimp.lists.members.users_data[2]['status'], 'subscribed')

            mailchimp.lists.members.users_data = None # type: ignore[assignment]
            with self.assertRaisesRegexp( # type: ignore[no-untyped-call]
                Exception, 'Server Error'):
                mailchimp_bulk_email_services.add_or_update_user_status(
                    self.user_email_1, True)

    def test_catch_or_raise_errors_when_creating_new_invalid_user(self) -> None:
        mailchimp = self.MockMailchimpClass()
        swapped_mailchimp = lambda: mailchimp
        swap_mailchimp_context = self.swap(
            mailchimp_bulk_email_services, '_get_mailchimp_class',
            swapped_mailchimp)
        swap_api = self.swap(feconf, 'MAILCHIMP_API_KEY', 'key')
        swap_username = self.swap(feconf, 'MAILCHIMP_USERNAME', 'username')

        with swap_mailchimp_context, swap_api, swap_username:
            # Creates a mailchimp entry for a deleted user.
            self.assertEqual(len(mailchimp.lists.members.users_data), 2)
            return_status = (
                mailchimp_bulk_email_services.add_or_update_user_status(
                    'test4@example.com', True))
            self.assertFalse(return_status)
            self.assertEqual(len(mailchimp.lists.members.users_data), 2)

            # Create user raises exception for other errors.
            with self.assertRaisesRegexp( # type: ignore[no-untyped-call]
                Exception, 'Server Issue'):
                mailchimp_bulk_email_services.add_or_update_user_status(
                    'test5@example.com', True)

    def test_permanently_delete_user(self) -> None:
        mailchimp = self.MockMailchimpClass()
        swapped_mailchimp = lambda: mailchimp
        swap_mailchimp_context = self.swap(
            mailchimp_bulk_email_services, '_get_mailchimp_class',
            swapped_mailchimp)
        swap_api = self.swap(feconf, 'MAILCHIMP_API_KEY', 'key')
        swap_username = self.swap(feconf, 'MAILCHIMP_USERNAME', 'username')

        with swap_mailchimp_context, swap_api, swap_username:
            self.assertEqual(len(mailchimp.lists.members.users_data), 2)
            mailchimp_bulk_email_services.permanently_delete_user_from_list(
                self.user_email_1)
            self.assertEqual(len(mailchimp.lists.members.users_data), 1)

            mailchimp.lists.members.users_data = None # type: ignore[assignment]
            with self.assertRaisesRegexp( # type: ignore[no-untyped-call]
                Exception, 'Server Error'):
                mailchimp_bulk_email_services.permanently_delete_user_from_list(
                    self.user_email_1)
