#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for fm.db.sqlalchemy.api and fm.db.migration."""
# pylint: disable=protected-access,unused-argument

import unittest
from unittest import mock
from tests.base import BaseDbTestCase, TEST_ALARM_ID


class TestDbConnection(BaseDbTestCase):
    """Test Connection methods with mocked DB."""

    @mock.patch('fm.db.sqlalchemy.api._session_for_write')
    def test_alarm_create(self, msw):
        self._mock_write()
        self._call('alarm_create', {'alarm_id': TEST_ALARM_ID})

    @mock.patch('fm.db.sqlalchemy.api._session_for_write')
    def test_alarm_create_duplicate(self, msw):
        from oslo_db import exception as db_exc
        from fm.common import exceptions
        s = self._mock_write()
        s.add.side_effect = db_exc.DBDuplicateEntry()
        with self.assertRaises(exceptions.AlarmAlreadyExists):
            self._call('alarm_create', {'alarm_id': TEST_ALARM_ID})

    def test_alarm_get(self):
        self._call('alarm_get', 'uuid-1')

    def test_alarm_get_by_ids(self):
        self._call('alarm_get_by_ids', TEST_ALARM_ID, 'host=c')

    def test_alarm_get_by_ids_none(self):
        self._call('alarm_get_by_ids', None, None)

    def test_alarm_get_all_no_filter(self):
        self._call('alarm_get_all')

    def test_alarm_get_all_with_filters(self):
        self._call('alarm_get_all',
                   alarm_id=TEST_ALARM_ID, entity_type_id='system',
                   entity_instance_id='host=c', severity='major',
                   alarm_type='equipment')

    def test_alarm_get_all_uuid(self):
        self._call('alarm_get_all', uuid='uuid-1')

    def test_alarm_destroy(self):
        self._mock_write()
        self._call('alarm_destroy', 'uuid-1')

    def test_alarm_destroy_by_ids(self):
        self._mock_write()
        self._call('alarm_destroy_by_ids', TEST_ALARM_ID, 'host=c')

    @mock.patch('fm.db.sqlalchemy.api._paginate_query',
                return_value=[])
    def test_alarm_get_list(self, _):
        self._call('alarm_get_list', limit=10, sort_key='id')

    def test_event_log_get(self):
        self._call('event_log_get', 'uuid-1')

    def test_event_log_get_all_no_filter(self):
        self._call('event_log_get_all')

    def test_event_log_get_all_with_filters(self):
        self._call('event_log_get_all',
                   event_log_id=TEST_ALARM_ID, entity_type_id='system',
                   entity_instance_id='host=c', severity='major',
                   event_log_type='equipment')

    def test_event_log_get_all_with_time(self):
        self._call('event_log_get_all',
                   start='2024-01-01', end='2024-12-31')

    def test_event_log_get_all_with_limit(self):
        self._call('event_log_get_all', limit=5)

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


class TestDbApiFunctions(unittest.TestCase):
    """Test module-level DB API functions."""

    @mock.patch('fm.db.sqlalchemy.api.enginefacade.writer')
    def test_get_engine(self, mock_writer):
        from fm.db.sqlalchemy import api
        api.get_engine()
        mock_writer.get_engine.assert_called()

    @mock.patch('fm.db.sqlalchemy.api.enginefacade.writer')
    @mock.patch('fm.db.sqlalchemy.api.orm.get_maker')
    def test_get_session(self, mock_maker, mock_writer):
        from fm.db.sqlalchemy import api
        mock_maker.return_value = mock.MagicMock()
        api.get_session()
        mock_maker.assert_called()

    def test_get_backend(self):
        from fm.db.sqlalchemy import api
        self.assertIsNotNone(api.get_backend())

    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_add_event_log_filter_suppress(self, mq):
        from fm.db.sqlalchemy import api
        q = mock.MagicMock()
        self.assertIsNotNone(
            api.add_event_log_filter_by_event_suppression(
                q, include_suppress=True))

    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_add_event_log_filter_no_suppress(self, mq):
        from fm.db.sqlalchemy import api
        q = mock.MagicMock()
        self.assertIsNotNone(
            api.add_event_log_filter_by_event_suppression(
                q, include_suppress=False))

    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_add_alarm_filter(self, mq):
        from fm.db.sqlalchemy import api
        q = mock.MagicMock()
        self.assertIsNotNone(
            api.add_alarm_filter_by_event_suppression(
                q, include_suppress=True))
        self.assertIsNotNone(
            api.add_alarm_filter_by_event_suppression(
                q, include_suppress=False))

    def test_add_alarm_mgmt_affecting(self):
        from fm.db.sqlalchemy import api
        q = mock.MagicMock()
        self.assertIsNotNone(
            api.add_alarm_mgmt_affecting_by_event_suppression(q))

    def test_add_alarm_degrade_affecting(self):
        from fm.db.sqlalchemy import api
        q = mock.MagicMock()
        self.assertIsNotNone(
            api.add_alarm_degrade_affecting_by_event_suppression(q))

    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_paginate_query(self, mq):
        from fm.db.sqlalchemy import api
        model = mock.MagicMock()
        mq.return_value = mock.MagicMock()
        with mock.patch('oslo_db.sqlalchemy.utils.paginate_query') as m:
            m.return_value.all.return_value = []
            self.assertIsInstance(
                api._paginate_query(model, limit=10), list)

    def test_model_query(self):
        from fm.db.sqlalchemy import api
        model = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx._db_session = mock.MagicMock()
        with mock.patch('eventlet.greenthread.getcurrent',
                        return_value=ctx):
            self.assertIsNotNone(api.model_query(model))


class TestDbMigration(unittest.TestCase):
    """Test fm.db.migration module."""

    def test_backend_mapping(self):
        from fm.db import api
        self.assertIn('sqlalchemy', api._BACKEND_MAPPING)

    def test_migrate_repo_path(self):
        from fm.db import migration
        self.assertIn('migrations', migration.MIGRATE_REPO_PATH)

    def test_functions_exist(self):
        from fm.db import migration
        self.assertTrue(callable(migration.db_sync))
        self.assertTrue(callable(migration.upgrade))
        self.assertTrue(callable(migration.version))

    @mock.patch('stevedore.driver.DriverManager')
    def test_get_backend(self, mock_dm):
        from fm.db import migration
        migration._IMPL = None
        mock_dm.return_value = mock.MagicMock()
        self.assertIsNotNone(migration.get_backend())
        migration._IMPL = None


if __name__ == '__main__':
    unittest.main()
