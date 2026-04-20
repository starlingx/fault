#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Deep coverage for wrapping_formatters,
utils, http, shell, controllers."""
import unittest
from unittest import mock
from tests import constants as TC


class TestWrapperFormatterClasses(unittest.TestCase):
    def setUp(self):
        from fmclient.common import wrapping_formatters as wf
        self.wf = wf
        self.ctx = wf.WrapperContext()
        self.ctx.set_num_columns(3)
        self.ctx.terminal_width = 120

    def test_wrapper_formatter_init(self):
        w = self.wf.WrapperFormatter(self.ctx, 'name')
        self.assertEqual(w.field, 'name')
        self.assertEqual(w.min_width, 0)

    def test_wrapper_formatter_basic_desired_width(self):
        w = self.wf.WrapperFormatter(self.ctx, 'name')
        w.min_width = 10
        self.assertEqual(w.get_basic_desired_width(), 10)

    def test_wrapper_formatter_calculated_desired_width(self):
        w = self.wf.WrapperFormatter(self.ctx, 'name')
        w.min_width = 10
        w.header_width = 20
        self.assertEqual(w.get_calculated_desired_width(), 20)

    def test_wrapper_formatter_format(self):
        w = self.wf.WrapperFormatter(self.ctx, None)
        w.get_field_value = lambda d: d
        self.assertEqual(w.format('hello'), 'hello')

    def test_wrapper_formatter_as_function(self):
        w = self.wf.WrapperFormatter(self.ctx, None)
        fn = w.as_function()
        self.assertTrue(callable(fn))
        self.assertTrue(fn.WrapperFormatterMarker)

    def test_is_wrapper_formatter_true(self):
        w = self.wf.WrapperFormatter(self.ctx, None)
        fn = w.as_function()
        self.assertTrue(
            self.wf.WrapperFormatter
            .is_wrapper_formatter(fn))

    def test_is_wrapper_formatter_false(self):
        self.assertFalse(
            self.wf.WrapperFormatter.is_wrapper_formatter(None))
        self.assertFalse(
            self.wf.WrapperFormatter.is_wrapper_formatter(lambda x: x))

    def test_text_wrap_nowrap(self):
        w = self.wf.WrapperFormatter(self.ctx, None)
        w.no_wrap = True
        w.actual_column_char_len = 10
        self.assertEqual(w.text_wrap('hello world', 10), 'hello world')

    def test_text_wrap_wrap(self):
        w = self.wf.WrapperFormatter(self.ctx, None)
        w.actual_column_char_len = 5
        result = w.text_wrap('hello world test', 5)
        self.assertIn('\n', result)

    def test_set_min_width(self):
        w = self.wf.WrapperFormatter(self.ctx, None)
        w.set_min_width(15)
        self.assertEqual(w.min_width, 15)

    def test_get_actual_column_char_len_cached(self):
        w = self.wf.WrapperFormatter(self.ctx, None)
        w.actual_column_char_len = 42
        self.assertEqual(w.get_actual_column_char_len(10), 42)

    def test_get_actual_column_char_len_min(self):
        w = self.wf.WrapperFormatter(self.ctx, None)
        w.min_width = 20
        result = w.get_actual_column_char_len(
            5, check_remaining_row_chars=False)
        self.assertEqual(result, 20)

    def test_wrapper_fixed_width(self):
        w = self.wf.WrapperFixedWidthFormatter(self.ctx, None, 15)
        self.assertEqual(w.get_basic_desired_width(), 15)

    def test_wrapper_percent_width(self):
        w = self.wf.WrapperPercentWidthFormatter(self.ctx, None, 0.5)
        width = w.get_basic_desired_width()
        self.assertGreater(width, 0)

    def test_wrapper_percent_width_format(self):
        w = self.wf.WrapperPercentWidthFormatter(self.ctx, None, 0.5)
        w.get_field_value = lambda d: d
        w.actual_column_char_len = 50
        result = w.format('test data')
        self.assertIsInstance(result, str)

    def test_wrapper_lambda_formatter(self):
        w = self.wf.WrapperLambdaFormatter(
            self.ctx, None, lambda x: x.upper())
        w.get_field_value = lambda d: d
        self.assertEqual(w.format('hello'), 'HELLO')

    def test_wrapper_with_custom_formatter(self):
        inner = self.wf.WrapperPercentWidthFormatter(
            self.ctx, 'name', 0.3)
        w = self.wf.WrapperWithCustomFormatter(
            self.ctx, 'name', lambda x: str(x).upper(), inner)
        self.assertIsNotNone(w)
        w.no_wrap = True
        w.set_min_width(5)

    def test_field_value_function_factory_dict(self):
        w = self.wf.WrapperFormatter(self.ctx, 'name')
        fn = self.wf.field_value_function_factory(w, 'name')
        result = fn({'name': 'test'})
        self.assertEqual(result, 'test')

    def test_field_value_function_factory_obj(self):
        w = self.wf.WrapperFormatter(self.ctx, 'name')
        fn = self.wf.field_value_function_factory(w, 'name')
        obj = mock.MagicMock()
        obj.name = 'test'
        result = fn(obj)
        self.assertEqual(result, 'test')

    def test_wrapper_formatter_factory_int(self):
        w = self.wf.wrapper_formatter_factory(self.ctx, 'f', 15)
        self.assertIsNotNone(w)

    def test_wrapper_formatter_factory_float(self):
        w = self.wf.wrapper_formatter_factory(self.ctx, 'f', 0.25)
        self.assertIsNotNone(w)

    def test_wrapper_formatter_factory_callable(self):
        w = self.wf.wrapper_formatter_factory(
            self.ctx, 'f', lambda x: str(x))
        self.assertIsNotNone(w)

    def test_wrapper_formatter_factory_dict(self):
        spec = {'formatter': lambda x: str(x),
                'wrapperFormatter': 0.2}
        w = self.wf.wrapper_formatter_factory(self.ctx, 'f', spec)
        self.assertIsNotNone(w)

    def test_build_wrapping_formatters_with_spec(self):
        objs = [mock.MagicMock()]
        objs[0].name = 'test'
        objs[0].value = 'data'
        spec = {'name': 0.3, 'value': 0.7}
        result = self.wf.build_wrapping_formatters(
            objs, ['name', 'value'], ['Name', 'Value'], spec)
        self.assertIsInstance(result, dict)

    def test_wrapper_context_is_table_too_wide(self):
        self.ctx.terminal_width = 10
        for _ in range(3):
            w = self.wf.WrapperFixedWidthFormatter(self.ctx, None, 50)
            self.ctx.add_column_formatter('f', w)
        self.assertTrue(self.ctx.is_table_too_wide())

    def test_wrapper_context_get_table_width(self):
        ctx = self.wf.WrapperContext()
        ctx.set_num_columns(1)
        ctx.terminal_width = 200
        w = self.wf.WrapperFixedWidthFormatter(ctx, None, 20)
        w.actual_column_char_len = 20
        ctx.add_column_formatter('f', w)
        width = ctx.get_table_width()
        self.assertGreater(width, 0)

    def test_prettytable_builder(self):
        from fmclient.common.utils import prettytable_builder
        pt = prettytable_builder(['Col1', 'Col2'])
        self.assertIsNotNone(pt)

    def test_wr_pretty_table(self):
        from fmclient.common.utils import prettytable_builder
        pt = prettytable_builder(['A', 'B'])
        pt.add_row(['1', '2'])
        s = pt.get_string()
        self.assertIn('A', s)


class TestFmclientUtilsDeep(unittest.TestCase):
    def setUp(self):
        from fmclient.common import utils
        self.u = utils

    def test_str_height_empty(self):
        self.assertEqual(self.u.str_height(None), 1)
        self.assertEqual(self.u.str_height(''), 1)

    def test_str_height_multiline(self):
        self.assertEqual(self.u.str_height('a\nb\nc'), 3)

    def test_row_height_empty(self):
        self.assertEqual(self.u.row_height(None), 1)
        self.assertEqual(self.u.row_height([]), 1)

    def test_row_height_values(self):
        self.assertEqual(self.u.row_height(['a', 'b\nc']), 2)

    def test_sort_list_by_field(self):
        o1 = mock.MagicMock()
        o1.name = 'b'
        o2 = mock.MagicMock()
        o2.name = 'a'
        if hasattr(self.u, 'sort_list_by_field'):
            result = self.u.sort_list_by_field([o1, o2], ['name'], 0)
            self.assertEqual(result[0].name, 'a')

    def test_sort_list_by_field_none(self):
        if hasattr(self.u, 'sort_list_by_field'):
            result = self.u.sort_list_by_field([1, 2], ['f'], None)
            self.assertEqual(result, [1, 2])

    def test_print_long_list(self):
        o = mock.MagicMock()
        o.f1 = 'v1'
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o], ['f1'], ['F1'], no_paging=True)

    def test_pt_builder(self):
        builder = self.u.pt_builder(
            ['F1'], ['f1'], {}, False)
        self.assertIsNotNone(builder)
        o = mock.MagicMock()
        o.f1 = 'val'
        builder.add_row(o)
        s = builder.get_string()
        self.assertIsNotNone(s)
        builder.done()

    def test_is_service_impacting_command(self):
        if hasattr(self.u, '_is_service_impacting_command'):
            r = self.u._is_service_impacting_command('alarm-delete')
            self.assertIsInstance(r, bool)

    def test_build_row_from_object(self):
        if hasattr(self.u, '_build_row_from_object'):
            o = mock.MagicMock()
            o.f1 = 'v1'
            row = self.u._build_row_from_object(['f1'], {}, o)
            self.assertEqual(row, ['v1'])


class TestFmclientHttpDeep(unittest.TestCase):
    def test_supported_endpoint_scheme(self):
        from fmclient.common import http
        self.assertIn('http', http.SUPPORTED_ENDPOINT_SCHEME)
        self.assertIn('https', http.SUPPORTED_ENDPOINT_SCHEME)

    def test_default_version(self):
        from fmclient.common import http
        self.assertEqual(http.DEFAULT_VERSION, '1')

    def test_user_agent(self):
        from fmclient.common import http
        self.assertEqual(http.USER_AGENT, 'python-fmclient')

    def test_session_client_post(self):
        from tests.base import make_http_client
        c = make_http_client(status=201)
        r, body = c.post('/v1/alarms', body='{}')
        self.assertIsNotNone(body)


class TestFmShellDeep(unittest.TestCase):
    def setUp(self):
        import subprocess
        self._keyctl_patch = mock.patch(
            'fmclient.common.utils.subprocess.run',
            side_effect=subprocess.CalledProcessError(1, 'keyctl')
        )
        self._keyctl_patch.start()

    def tearDown(self):
        self._keyctl_patch.stop()

    def test_shell_main_no_username(self):
        from fmclient.shell import FmShell
        from fmclient import exc
        sh = FmShell()
        with self.assertRaises(exc.CommandError):
            sh.main(['alarm-list'])

    def test_shell_help_subcommand(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        sh.parser = mock.MagicMock()
        sh.subcommands = {'alarm-list': mock.MagicMock()}
        args = mock.MagicMock()
        args.command = 'alarm-list'
        sh.do_help(args)

    def test_shell_help_invalid_subcommand(self):
        from fmclient.shell import FmShell
        from fmclient import exc
        sh = FmShell()
        sh.parser = mock.MagicMock()
        sh.subcommands = {}
        args = mock.MagicMock()
        args.command = 'nonexistent'
        with self.assertRaises(exc.CommandError):
            sh.do_help(args)

    def test_main_function(self):
        from fmclient import shell
        with self.assertRaises(SystemExit):
            with mock.patch.object(
                    shell.FmShell, 'main',
                    side_effect=Exception("test")):
                shell.main()


class TestEventSuppressionShellDeep(unittest.TestCase):
    def test_do_event_suppress(self):
        from fmclient.v1 import event_suppression_shell as ess
        if hasattr(ess, 'do_event_suppress'):
            cc = mock.MagicMock()
            cc.event_suppression.list.return_value = [
                mock.MagicMock(uuid='u1', alarm_id=TC.TEST_ALARM_ID,
                               suppression_status='unsuppressed')]
            args = mock.MagicMock()
            args.alarm_id = TC.TEST_ALARM_ID
            with mock.patch('fmclient.common.utils.print_list'):
                ess.do_event_suppress(cc, args)

    def test_do_event_unsuppress(self):
        from fmclient.v1 import event_suppression_shell as ess
        if hasattr(ess, 'do_event_unsuppress'):
            cc = mock.MagicMock()
            cc.event_suppression.list.return_value = [
                mock.MagicMock(uuid='u1', alarm_id=TC.TEST_ALARM_ID,
                               suppression_status='suppressed')]
            args = mock.MagicMock()
            args.alarm_id = TC.TEST_ALARM_ID
            with mock.patch('fmclient.common.utils.print_list'):
                ess.do_event_unsuppress(cc, args)

    def test_do_event_suppress_list(self):
        from fmclient.v1 import event_suppression_shell as ess
        if hasattr(ess, 'do_event_suppress_list'):
            cc = mock.MagicMock()
            cc.event_suppression.list.return_value = []
            args = mock.MagicMock()
            args.query = None
            args.uuid = False
            args.nopaging = True
            with mock.patch('fmclient.common.utils.print_long_list'):
                ess.do_event_suppress_list(cc, args)


class TestAlarmControllerDeep(unittest.TestCase):
    def test_alarm_imports(self):
        from fm.api.controllers.v1 import alarm
        self.assertTrue(hasattr(alarm, 'AlarmController'))
        self.assertTrue(hasattr(alarm, 'Alarm'))
        self.assertTrue(hasattr(alarm, 'AlarmCollection'))

    def test_event_log_imports(self):
        from fm.api.controllers.v1 import event_log
        self.assertTrue(hasattr(event_log, 'EventLogController'))
        self.assertTrue(hasattr(event_log, 'EventLog'))

    def test_event_suppression_imports(self):
        from fm.api.controllers.v1 import event_suppression
        self.assertTrue(hasattr(event_suppression,
                                'EventSuppressionController'))


class TestApiHooksDeep(unittest.TestCase):
    def test_access_policy_hook(self):
        from fm.api import hooks
        self.assertTrue(hasattr(hooks, 'AccessPolicyHook'))

    def test_audit_after_get(self):
        from fm.api import hooks
        al = hooks.AuditLogging()
        state = mock.MagicMock()
        state.request.method = 'GET'
        al.after(state)

    def test_audit_after_post_exception(self):
        from fm.api import hooks
        al = hooks.AuditLogging()
        state = mock.MagicMock()
        state.request.method = 'POST'
        state.request.start_time = 0
        state.request.environ = {'SERVER_PROTOCOL': 'HTTP/1.1'}
        state.request.headers = mock.MagicMock()
        state.request.headers.get = mock.MagicMock(
            side_effect=Exception("test"))
        al.after(state)


if __name__ == '__main__':
    unittest.main()
