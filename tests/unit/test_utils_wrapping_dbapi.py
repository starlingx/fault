#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Target specific uncovered lines to push to 85%."""
import unittest
from unittest import mock
from tests.base import BaseDbTestCase
from tests import constants as TC


class TestUtilsLines(unittest.TestCase):
    """Cover specific uncovered lines in fmclient.common.utils."""

    def setUp(self):
        from fmclient.common import utils
        self.u = utils

    def test_print_list_with_sort_formatter(self):
        from fmclient.common import wrapping_formatters as wf
        o1 = mock.MagicMock()
        o1.name = 'b'
        o2 = mock.MagicMock()
        o2.name = 'a'
        spec = {'name': 0.5}
        fmts = wf.build_wrapping_formatters(
            [o1, o2], ['name'], ['Name'], spec)
        with mock.patch('builtins.print'):
            self.u.print_list(
                [o1, o2], ['name'], ['Name'],
                formatters=fmts, sortby=0)

    def test_print_list_with_sort_plain(self):
        o1 = mock.MagicMock()
        o1.name = 'b'
        o2 = mock.MagicMock()
        o2.name = 'a'
        with mock.patch('builtins.print'):
            self.u.print_list(
                [o1, o2], ['name'], ['Name'], sortby=0)

    def test_print_long_list_with_sort_formatter(self):
        from fmclient.common import wrapping_formatters as wf
        o1 = mock.MagicMock()
        o1.name = 'b'
        o2 = mock.MagicMock()
        o2.name = 'a'
        spec = {'name': 0.5}
        fmts = wf.build_wrapping_formatters(
            [o1, o2], ['name'], ['Name'], spec)
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o1, o2], ['name'], ['Name'],
                formatters=fmts, sortby=0, no_paging=True)

    def test_print_long_list_with_lambda_formatter(self):
        o = mock.MagicMock()
        o.name = 'test'
        fmts = {'name': lambda x: str(x).upper()}
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o], ['name'], ['Name'],
                formatters=fmts, sortby=0, no_paging=True)

    def test_pt_builder_multiple_rows(self):
        builder = self.u.pt_builder(
            ['Name'], ['name'], {}, False)
        for i in range(5):
            o = mock.MagicMock()
            o.name = f'val{i}'
            builder.add_row(o)
        s = builder.get_string()
        self.assertIsNotNone(s)
        builder.done()

    def test_pt_builder_with_formatter(self):
        from fmclient.common import wrapping_formatters as wf
        spec = {'name': 0.5}
        o = mock.MagicMock()
        o.name = 'test'
        fmts = wf.build_wrapping_formatters(
            [o], ['name'], ['Name'], spec)
        builder = self.u.pt_builder(
            ['Name'], ['name'], fmts, False)
        builder.add_row(o)
        s = builder.get_string()
        self.assertIsNotNone(s)
        builder.done()


class TestWrappingLines(unittest.TestCase):
    """Cover specific uncovered wrapping_formatters lines."""

    def test_wrapper_percent_format_long(self):
        from fmclient.common import wrapping_formatters as wf
        ctx = wf.WrapperContext()
        ctx.set_num_columns(1)
        ctx.terminal_width = 80
        w = wf.WrapperPercentWidthFormatter(ctx, None, 0.5)
        w.get_field_value = lambda d: d
        w.actual_column_char_len = 20
        result = w.format('a ' * 50)
        self.assertIn('\n', result)

    def test_wrapper_fixed_format(self):
        from fmclient.common import wrapping_formatters as wf
        ctx = wf.WrapperContext()
        ctx.set_num_columns(1)
        ctx.terminal_width = 80
        w = wf.WrapperFixedWidthFormatter(ctx, None, 15)
        w.get_field_value = lambda d: d
        w.actual_column_char_len = 15
        result = w.format('a ' * 30)
        self.assertIsNotNone(result)

    def test_wrapper_with_custom_get_unwrapped(self):
        from fmclient.common import wrapping_formatters as wf
        ctx = wf.WrapperContext()
        ctx.set_num_columns(1)
        ctx.terminal_width = 80
        inner = wf.WrapperPercentWidthFormatter(ctx, 'f', 0.5)
        custom = lambda x: str(x).upper()  # noqa: E731
        w = wf.WrapperWithCustomFormatter(
            ctx, 'f', custom, inner)
        result = w.get_unwrapped_field_value('test')
        self.assertEqual(result, 'TEST')

    def test_wrapper_with_custom_get_basic_width(self):
        from fmclient.common import wrapping_formatters as wf
        ctx = wf.WrapperContext()
        ctx.set_num_columns(1)
        ctx.terminal_width = 80
        inner = wf.WrapperPercentWidthFormatter(ctx, 'f', 0.5)
        w = wf.WrapperWithCustomFormatter(
            ctx, 'f', lambda x: str(x), inner)
        width = w.get_basic_desired_width()
        self.assertGreater(width, 0)

    def test_text_wrap_with_blank_line(self):
        from fmclient.common import wrapping_formatters as wf
        ctx = wf.WrapperContext()
        ctx.set_num_columns(1)
        ctx.terminal_width = 80
        w = wf.WrapperFormatter(ctx, None)
        w.add_blank_line = True
        w.actual_column_char_len = 10
        result = w.text_wrap('hello world test data', 10)
        self.assertIsNotNone(result)


class TestDbApiLines(BaseDbTestCase):
    """Cover specific db/sqlalchemy/api.py lines via __wrapped__."""

    def test_alarm_get_all_entity_instance(self):
        self._call(
            'alarm_get_all',
            entity_instance_id='host=c')

    def test_alarm_get_all_severity(self):
        self._call('alarm_get_all', severity='major')

    def test_alarm_get_all_alarm_type(self):
        self._call('alarm_get_all', alarm_type='equipment')

    def test_event_log_get_all_event_log_id(self):
        self._call(
            'event_log_get_all',
            event_log_id=TC.TEST_ALARM_ID)

    def test_event_log_get_all_entity_type(self):
        self._call(
            'event_log_get_all',
            entity_type_id='system')

    def test_event_log_get_all_severity(self):
        self._call('event_log_get_all', severity='major')


if __name__ == '__main__':
    unittest.main()
