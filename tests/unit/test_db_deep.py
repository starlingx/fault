#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Mock-heavy tests for db/sqlalchemy/api.py and migration.py."""
import unittest
from unittest import mock


from tests import constants as TC


class TestDbSqlalchemyApi(unittest.TestCase):
    """Test db/sqlalchemy/api.py with mocked DB."""

    def _get_api(self):
        from fm.db.sqlalchemy import api
        return api

    def _mock_session(self, msw):
        """Configure _session_for_write mock, return session."""
        sess = mock.MagicMock()
        msw.return_value.__enter__ = mock.MagicMock(return_value=sess)
        msw.return_value.__exit__ = mock.MagicMock(return_value=False)
        return sess

    @mock.patch('fm.db.sqlalchemy.api.enginefacade.writer')
    def test_get_engine(self, mock_writer):
        api = self._get_api()
        api.get_engine()
        mock_writer.get_engine.assert_called()

    @mock.patch('fm.db.sqlalchemy.api.enginefacade.writer')
    @mock.patch('fm.db.sqlalchemy.api.orm.get_maker')
    def test_get_session(self, mock_maker, mock_writer):
        api = self._get_api()
        mock_maker.return_value = mock.MagicMock()
        api.get_session()
        mock_maker.assert_called()

    def test_get_backend(self):
        api = self._get_api()
        conn = api.get_backend()
        self.assertIsNotNone(conn)

    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_add_event_log_filter_suppress(self, mq):
        api = self._get_api()
        query = mock.MagicMock()
        result = api.add_event_log_filter_by_event_suppression(
            query, include_suppress=True)
        self.assertIsNotNone(result)

    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_add_event_log_filter_no_suppress(self, mq):
        api = self._get_api()
        query = mock.MagicMock()
        result = api.add_event_log_filter_by_event_suppression(
            query, include_suppress=False)
        self.assertIsNotNone(result)

    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_add_alarm_filter_suppress(self, mq):
        api = self._get_api()
        query = mock.MagicMock()
        result = api.add_alarm_filter_by_event_suppression(
            query, include_suppress=True)
        self.assertIsNotNone(result)

    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_add_alarm_filter_no_suppress(self, mq):
        api = self._get_api()
        query = mock.MagicMock()
        result = api.add_alarm_filter_by_event_suppression(
            query, include_suppress=False)
        self.assertIsNotNone(result)

    def test_add_alarm_mgmt_affecting(self):
        api = self._get_api()
        query = mock.MagicMock()
        fn = api.add_alarm_mgmt_affecting_by_event_suppression
        result = fn(query)
        self.assertIsNotNone(result)

    def test_add_alarm_degrade_affecting(self):
        api = self._get_api()
        query = mock.MagicMock()
        fn = api.add_alarm_degrade_affecting_by_event_suppression
        result = fn(query)
        self.assertIsNotNone(result)

    @mock.patch('fm.db.sqlalchemy.api._session_for_write')
    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_connection_alarm_create(self, mq, msw):
        api = self._get_api()
        conn = api.Connection()
        self._mock_session(msw)
        result = conn.alarm_create({'alarm_id': TC.TEST_ALARM_ID})
        self.assertIsNotNone(result)

    @mock.patch(
        'fm.db.sqlalchemy.api'
        '.add_alarm_degrade_affecting'
        '_by_event_suppression')
    @mock.patch(
        'fm.db.sqlalchemy.api'
        '.add_alarm_mgmt_affecting'
        '_by_event_suppression')
    @mock.patch(
        'fm.db.sqlalchemy.api'
        '.add_alarm_filter'
        '_by_event_suppression')
    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_connection_alarm_get(self, mq, maf, mma, mda):
        api = self._get_api()
        conn = api.Connection()
        mock_alarm = mock.MagicMock()
        mda.return_value.one.return_value = (
            mock_alarm, 'unsuppressed', 'warning', 'none')
        result = conn.alarm_get('uuid-1')
        self.assertIsNotNone(result)

    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_connection_alarm_get_all(self, mq):
        api = self._get_api()
        conn = api.Connection()
        mq.return_value.join.return_value = mq.return_value
        mq.return_value.add_columns.return_value = mq.return_value
        mq.return_value.filter.return_value = mq.return_value
        mq.return_value.filter_by.return_value = mq.return_value
        mq.return_value.all.return_value = []
        result = conn.alarm_get_all()
        self.assertIsInstance(result, list)

    @mock.patch('fm.db.sqlalchemy.api._session_for_write')
    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_connection_alarm_destroy(self, mq, msw):
        api = self._get_api()
        conn = api.Connection()
        mock_alarm = mock.MagicMock()
        mq.return_value.filter_by\
            .return_value.one\
            .return_value = mock_alarm
        self._mock_session(msw)
        conn.alarm_destroy('uuid-1')

    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_connection_event_log_get_all(self, mq):
        api = self._get_api()
        conn = api.Connection()
        mq.return_value.outerjoin.return_value = mq.return_value
        mq.return_value.add_columns.return_value = mq.return_value
        mq.return_value.filter.return_value = mq.return_value
        mq.return_value.filter_by.return_value = mq.return_value
        mq.return_value.all.return_value = []
        result = conn.event_log_get_all()
        self.assertIsInstance(result, list)

    @mock.patch('fm.db.sqlalchemy.api.model_query')
    def test_paginate_query(self, mq):
        api = self._get_api()
        model = mock.MagicMock()
        mq.return_value = mock.MagicMock()
        pth = ('oslo_db.sqlalchemy'
               '.utils.paginate_query')
        with mock.patch(pth) as mpq:
            mpq.return_value.all.return_value = []
            result = api._paginate_query(model, limit=10)
            self.assertIsInstance(result, list)

    def test_model_query(self):
        api = self._get_api()
        model = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx._db_session = mock.MagicMock()
        with mock.patch('eventlet.greenthread.getcurrent',
                        return_value=ctx):
            result = api.model_query(model)
            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
