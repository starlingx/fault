#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Bypass decorators via __wrapped__ to cover db and controller code."""
import unittest
from unittest import mock
from tests.base import BaseDbTestCase, TEST_ALARM_ID
from tests import constants as TC


class TestDbConnectionUnwrapped(BaseDbTestCase):
    """Call Connection methods via __wrapped__ to bypass decorator."""

    def test_alarm_create(self):
        self._mock_write()
        self._call('alarm_create', {'alarm_id': TEST_ALARM_ID})

    def test_alarm_get(self):
        self._call('alarm_get', 'uuid-1')

    def test_alarm_get_by_ids(self):
        self._call('alarm_get_by_ids', TC.TEST_ALARM_ID, 'host=c')

    def test_alarm_get_all_no_filter(self):
        self._call('alarm_get_all')

    def test_alarm_get_all_with_filters(self):
        self._call(
            'alarm_get_all', alarm_id=TC.TEST_ALARM_ID,
            entity_type_id='system',
            entity_instance_id='host=c', severity='major',
            alarm_type='equipment')

    def test_alarm_destroy(self):
        self._mock_write()
        self._call('alarm_destroy', 'uuid-1')

    def test_alarm_destroy_by_ids(self):
        self._mock_write()
        self._call('alarm_destroy_by_ids', TC.TEST_ALARM_ID, 'host=c')

    @mock.patch('fm.db.sqlalchemy.api._paginate_query',
                return_value=[])
    def test_alarm_get_list(self, _):
        self._call('alarm_get_list', limit=10, sort_key='id')

    def test_event_log_get(self):
        self._call('event_log_get', 'uuid-1')

    def test_event_log_get_all(self):
        self._call('event_log_get_all')

    def test_event_log_get_all_filters(self):
        self._call(
            'event_log_get_all', event_log_id=TC.TEST_ALARM_ID,
            entity_type_id='system',
            entity_instance_id='host=c', severity='major',
            event_log_type='equipment',
            start='2024-01-01', end='2024-12-31', limit=10)

    @mock.patch('fm.db.sqlalchemy.api._paginate_query',
                return_value=[])
    def test_event_log_get_list(self, _):
        self._call('event_log_get_list', limit=10)

    @mock.patch('fm.db.sqlalchemy.api._paginate_query',
                return_value=[])
    def test_event_log_get_list_alarm(self, _):
        self._call('event_log_get_list', evtType="alarm")

    @mock.patch('fm.db.sqlalchemy.api._paginate_query',
                return_value=[])
    def test_event_log_get_list_log(self, _):
        self._call('event_log_get_list', evtType="log")

    def test_event_suppression_get_all(self):
        self._call('event_suppression_get_all')

    def test_get_session(self):
        with mock.patch('fm.db.sqlalchemy.api.get_session') as mg:
            self._call('get_session')


if __name__ == '__main__':
    unittest.main()
