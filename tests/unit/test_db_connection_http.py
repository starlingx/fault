#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Cover db/sqlalchemy/api.py Connection,
http, shell, wrapping."""
import unittest
from unittest import mock
from tests.base import BaseDbTestCase, make_http_client
from tests import constants as TC


class TestDbConnectionMethods(BaseDbTestCase):
    """Cover Connection methods by calling them with mocked queries."""

    @mock.patch('fm.db.sqlalchemy.api._session_for_write')
    def test_alarm_create(self, msw):
        self._mock_write()
        self._call('alarm_create', {'alarm_id': TC.TEST_ALARM_ID})

    def test_alarm_get(self):
        self._call('alarm_get', 'uuid-1')

    def test_alarm_get_by_ids(self):
        self._call('alarm_get_by_ids', TC.TEST_ALARM_ID, 'host=ctrl-0')

    def test_alarm_get_all_no_filter(self):
        self._call('alarm_get_all')

    def test_alarm_get_all_with_filters(self):
        self._call('alarm_get_all',
                   alarm_id=TC.TEST_ALARM_ID, entity_type_id='system',
                   entity_instance_id='host=ctrl-0', severity='major',
                   alarm_type='equipment')

    @mock.patch('fm.db.sqlalchemy.api._session_for_write')
    def test_alarm_destroy(self, msw):
        self._mock_write()
        self._call('alarm_destroy', 'uuid-1')

    @mock.patch('fm.db.sqlalchemy.api._session_for_write')
    def test_alarm_destroy_by_ids(self, msw):
        self._mock_write()
        self._call('alarm_destroy_by_ids', '100.104', 'host=ctrl-0')

    def test_event_log_get(self):
        self._call('event_log_get', 'uuid-1')

    def test_event_log_get_all_no_filter(self):
        self._call('event_log_get_all')

    def test_event_log_get_all_with_filters(self):
        self._call('event_log_get_all',
                   event_log_id=TC.TEST_ALARM_ID, entity_type_id='system',
                   entity_instance_id='host=ctrl-0', severity='major',
                   event_log_type='equipment')

    @mock.patch('fm.db.sqlalchemy.api._paginate_query')
    def test_alarm_get_list(self, mpq):
        mpq.return_value = []
        self._call('alarm_get_list', limit=10, sort_key='id')

    @mock.patch('fm.db.sqlalchemy.api._paginate_query')
    def test_event_log_get_list(self, mpq):
        mpq.return_value = []
        self._call('event_log_get_list', limit=10)

    @mock.patch('fm.db.sqlalchemy.api._paginate_query')
    def test_event_log_get_list_alarm(self, mpq):
        mpq.return_value = []
        self._call('event_log_get_list', evtType="alarm")

    @mock.patch('fm.db.sqlalchemy.api._paginate_query')
    def test_event_log_get_list_log(self, mpq):
        mpq.return_value = []
        self._call('event_log_get_list', evtType="log")

    def test_event_suppression_get_all(self):
        self._call('event_suppression_get_all')


class TestFmclientHttpCover(unittest.TestCase):
    """Cover http.py SessionClient all methods."""

    def test_get(self):
        c = make_http_client()
        r, b = c.get('/v1/alarms')
        self.assertIsNotNone(b)

    def test_post(self):
        c = make_http_client()
        r, b = c.post('/v1/alarms', body='{}')
        self.assertIsNotNone(b)

    def test_patch(self):
        c = make_http_client()
        r, b = c.patch('/v1/event_suppression/u1', data='[]')
        self.assertIsNotNone(b)

    def test_put(self):
        c = make_http_client()
        r, b = c.put('/v1/alarms/u1', body='{}')
        self.assertIsNotNone(b)

    def test_delete(self):
        c = make_http_client(status=204, data=None,
                             content_type='text/plain')
        c.delete('/v1/alarms/u1')


class TestFmclientShellCover(unittest.TestCase):
    """Cover shell.py error paths."""

    def test_main_keyboard_interrupt(self):
        from fmclient import shell
        with mock.patch.object(shell.FmShell, 'main',
                               side_effect=KeyboardInterrupt):
            with self.assertRaises(SystemExit):
                shell.main()

    def test_main_ioerror(self):
        from fmclient import shell
        with mock.patch.object(shell.FmShell, 'main',
                               side_effect=IOError):
            with self.assertRaises(SystemExit):
                shell.main()

    def test_main_exception(self):
        from fmclient import shell
        with mock.patch.object(shell.FmShell, 'main',
                               side_effect=Exception("err")):
            with self.assertRaises(SystemExit):
                shell.main()

    def test_get_subcommand_parser(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        p = sh.get_subcommand_parser('1')
        self.assertIsNotNone(p)


class TestWrappingFormattersCover(unittest.TestCase):
    """Cover remaining wrapping_formatters lines."""

    def test_wrapper_context_full(self):
        from fmclient.common import wrapping_formatters as wf
        ctx = wf.WrapperContext()
        ctx.set_num_columns(3)
        ctx.terminal_width = 120
        w1 = wf.WrapperPercentWidthFormatter(ctx, 'f1', 0.3)
        w2 = wf.WrapperPercentWidthFormatter(ctx, 'f2', 0.7)
        ctx.add_column_formatter('f1', w1)
        ctx.add_column_formatter('f2', w2)
        self.assertFalse(ctx.is_table_too_wide())

    def test_wrapper_context_too_wide(self):
        from fmclient.common import wrapping_formatters as wf
        ctx = wf.WrapperContext()
        ctx.set_num_columns(3)
        ctx.terminal_width = 20
        for i in range(3):
            w = wf.WrapperFixedWidthFormatter(ctx, f'f{i}', 50)
            ctx.add_column_formatter(f'f{i}', w)
        self.assertTrue(ctx.is_table_too_wide())

    def test_get_remaining_row_chars(self):
        from fmclient.common import wrapping_formatters as wf
        ctx = wf.WrapperContext()
        ctx.set_num_columns(2)
        ctx.terminal_width = 100
        w1 = wf.WrapperFixedWidthFormatter(ctx, 'f1', 20)
        w2 = wf.WrapperFixedWidthFormatter(ctx, 'f2', 20)
        ctx.add_column_formatter('f1', w1)
        ctx.add_column_formatter('f2', w2)
        remaining = w1.get_remaining_row_chars()
        self.assertGreater(remaining, 0)

    def test_actual_column_shrink(self):
        from fmclient.common import wrapping_formatters as wf
        ctx = wf.WrapperContext()
        ctx.set_num_columns(2)
        ctx.terminal_width = 30
        w1 = wf.WrapperFixedWidthFormatter(ctx, 'f1', 20)
        w1.min_width = 5
        w2 = wf.WrapperFixedWidthFormatter(ctx, 'f2', 20)
        w2.min_width = 5
        w2.actual_column_char_len = 20
        ctx.add_column_formatter('f1', w1)
        ctx.add_column_formatter('f2', w2)
        actual = w1.get_actual_column_char_len(20)
        self.assertGreaterEqual(actual, 5)

    def test_wrapper_with_custom_setattr(self):
        from fmclient.common import wrapping_formatters as wf
        ctx = wf.WrapperContext()
        ctx.set_num_columns(1)
        ctx.terminal_width = 100
        inner = wf.WrapperPercentWidthFormatter(ctx, 'f', 0.5)
        w = wf.WrapperWithCustomFormatter(
            ctx, 'f', lambda x: str(x).upper(), inner)
        w.no_wrap = True
        self.assertTrue(inner.no_wrap)
        w.add_blank_line = True
        self.assertTrue(inner.add_blank_line)
        w.header_width = 10
        self.assertEqual(inner.header_width, 10)
        w.set_min_width(5)
        self.assertEqual(inner.min_width, 5)
        w.set_actual_column_len(15)
        self.assertEqual(inner.actual_column_char_len, 15)

    def test_build_wrapping_formatters_dict_spec(self):
        from fmclient.common import wrapping_formatters as wf
        objs = [mock.MagicMock()]
        objs[0].name = 'test'
        spec = {'name': {'formatter': lambda x: str(x),
                         'wrapperFormatter': 0.5}}
        result = wf.build_wrapping_formatters(
            objs, ['name'], ['Name'], spec)
        self.assertIn('name', result)


if __name__ == '__main__':
    unittest.main()
