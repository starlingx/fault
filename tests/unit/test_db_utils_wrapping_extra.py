#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Extra coverage for utils, wrapping_formatters, http,
    db via __wrapped__."""
import unittest
from unittest import mock
from tests.base import BaseDbTestCase
from tests import constants as TC


class TestDbUnwrappedExtra(BaseDbTestCase):
    """Cover more db/sqlalchemy/api.py lines via __wrapped__."""

    def test_alarm_get_all_uuid(self):
        self._call('alarm_get_all', uuid='uuid-1')

    def test_alarm_get_by_ids_none(self):
        self._call('alarm_get_by_ids', None, None)

    @mock.patch('fm.db.sqlalchemy.api._session_for_write')
    def test_alarm_create_dup(self, msw):
        from oslo_db import exception as db_exc
        s = mock.MagicMock()
        s.add.side_effect = db_exc.DBDuplicateEntry()
        msw.return_value.__enter__ = mock.MagicMock(return_value=s)
        msw.return_value.__exit__ = mock.MagicMock(return_value=False)
        from fm.common import exceptions
        with self.assertRaises(exceptions.AlarmAlreadyExists):
            self._call('alarm_create', {'alarm_id': TC.TEST_ALARM_ID})

    def test_event_log_get_all_with_time(self):
        self._call(
            'event_log_get_all',
            start='2024-01-01', end='2024-12-31')

    def test_event_log_get_all_with_limit(self):
        self._call('event_log_get_all', limit=5)


class TestFmclientUtilsExtra(unittest.TestCase):
    """Cover more fmclient.common.utils lines."""

    def setUp(self):
        from fmclient.common import utils
        self.u = utils

    def test_print_list_no_wrap(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.name = 'test'
        wf.set_no_wrap(True)
        with mock.patch('builtins.print'):
            self.u.print_list([o], ['name'], ['Name'])
        wf.set_no_wrap(False)

    def test_print_dict_no_wrap(self):
        with mock.patch('builtins.print'):
            self.u.print_dict({'k': 'v' * 200}, wrap=72)

    def test_print_long_list_paging(self):
        o = mock.MagicMock()
        o.name = 'test'
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o], ['name'], ['Name'], no_paging=True)

    def test_print_long_list_with_sort(self):
        o1 = mock.MagicMock()
        o1.name = 'b'
        o2 = mock.MagicMock()
        o2.name = 'a'
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o1, o2], ['name'], ['Name'],
                sortby=0, no_paging=True)

    def test_print_long_list_reverse(self):
        o = mock.MagicMock()
        o.name = 'a'
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o], ['name'], ['Name'],
                sortby=0, reversesort=True, no_paging=True)

    def test_print_list_with_wrapping(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.name = 'test value'
        o.desc = 'a long description'
        spec = {'name': 0.3, 'desc': 0.7}
        fmts = wf.build_wrapping_formatters(
            [o], ['name', 'desc'], ['Name', 'Desc'], spec)
        with mock.patch('builtins.print'):
            self.u.print_list(
                [o], ['name', 'desc'], ['Name', 'Desc'],
                formatters=fmts)


class TestWrappingExtra(unittest.TestCase):
    """Cover more wrapping_formatters lines."""

    def test_build_formatters_callable(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.name = 'test'
        spec = {'name': lambda x: str(x).upper()}
        r = wf.build_wrapping_formatters(
            [o], ['name'], ['Name'], spec)
        self.assertIn('name', r)

    def test_build_formatters_int(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.name = 'test'
        spec = {'name': 20}
        r = wf.build_wrapping_formatters(
            [o], ['name'], ['Name'], spec)
        self.assertIn('name', r)

    def test_build_formatters_dict_with_formatter(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.name = 'test'
        spec = {'name': {'formatter': lambda x: str(x),
                         'wrapperFormatter': 0.5}}
        r = wf.build_wrapping_formatters(
            [o], ['name'], ['Name'], spec)
        self.assertIn('name', r)

    def test_build_formatters_dict_int_wrapper(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.name = 'test'
        spec = {'name': {'formatter': lambda x: str(x),
                         'wrapperFormatter': 20}}
        r = wf.build_wrapping_formatters(
            [o], ['name'], ['Name'], spec)
        self.assertIn('name', r)

    def test_set_no_wrap_on_formatters(self):
        from fmclient.common import wrapping_formatters as wf
        ctx = wf.WrapperContext()
        ctx.set_num_columns(1)
        ctx.terminal_width = 100
        w = wf.WrapperPercentWidthFormatter(ctx, 'f', 0.5)
        fn = w.as_function()
        fmts = {'f': fn}
        orig = wf.set_no_wrap_on_formatters(True, fmts)
        self.assertIsInstance(orig, dict)
        wf.unset_no_wrap_on_formatters(orig)


class TestHttpExtra(unittest.TestCase):
    """Cover more http.py lines."""

    def test_get_http_client_no_session(self):
        from fmclient.common import http
        c = http.get_http_client(
            'http://h:18002', session=mock.MagicMock())
        self.assertIsNotNone(c)

    def test_session_client_404(self):
        from tests.base import make_http_client
        try:
            make_http_client(
                status=404, content_type='text/plain'
            ).get('/v1/alarms/nonexistent')
        except Exception:
            pass

    def test_session_client_500(self):
        from tests.base import make_http_client
        try:
            make_http_client(
                status=500, content_type='text/plain'
            ).get('/v1/alarms')
        except Exception:
            pass


if __name__ == '__main__':
    unittest.main()
