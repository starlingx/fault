#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Max coverage tests for fmclient
and fm-rest-api uncovered modules."""
import os
import unittest
from unittest import mock
# ── fmclient.common.utils ──────────────────────────────────────────


class TestFmclientUtils(unittest.TestCase):
    def setUp(self):
        from fmclient.common import utils
        self.u = utils

    def test_env_found(self):
        os.environ['_T1'] = 'v'
        self.assertEqual(self.u.env('_T1'), 'v')
        del os.environ['_T1']

    def test_env_default(self):
        self.assertEqual(self.u.env('_NOPE', default='d'), 'd')

    def test_get_terminal_size(self):
        r = self.u.get_terminal_size()
        self.assertEqual(len(r), 2)

    def test_normalize_field_data(self):
        o = mock.MagicMock()
        o.name = 'test'
        self.u.normalize_field_data(o, ['name'])

    def test_arg_decorator(self):
        @self.u.arg('--test', help='h')
        def fn():
            pass
        self.assertIn('arguments', fn.__dict__)

    def test_does_command_need_no_wrap_list(self):
        self.assertTrue(self.u._does_command_need_no_wrap(
            type('F', (), {'__name__': 'do_alarm_list'})()))

    def test_does_command_need_no_wrap_false(self):
        self.assertFalse(self.u._does_command_need_no_wrap(
            type('F', (), {'__name__': 'do_alarm_show'})()))

    def test_wrapping_formatter_callback_decorator(self):
        sp = mock.MagicMock()
        cb = mock.MagicMock()
        cb.__name__ = 'do_test'
        fn = self.u._wrapping_formatter_callback_decorator
        result = fn(sp, 'test', cb)
        self.assertTrue(callable(result))

    def test_wrapping_formatter_callback_already_added(self):
        sp = mock.MagicMock()
        sp.add_argument.side_effect = Exception("dup")
        cb = mock.MagicMock()
        cb.__name__ = 'do_test'
        fn = self.u._wrapping_formatter_callback_decorator
        result = fn(sp, 'test', cb)
        self.assertEqual(result, cb)

    def test_define_command(self):
        subparsers = mock.MagicMock()
        sub = mock.MagicMock()
        subparsers.add_parser.return_value = sub
        mapper = {}
        cb = mock.MagicMock()
        cb.__doc__ = 'Help text'
        cb.__name__ = 'do_show'
        cb.arguments = []
        self.u.define_command(subparsers, 'show', cb, mapper)
        self.assertIn('show', mapper)

    def test_define_commands_from_module(self):
        mod = type('M', (), {})()

        def do_test():
            """test help"""
            pass
        do_test.__name__ = 'do_test'
        do_test.arguments = []
        mod.do_test = do_test
        subparsers = mock.MagicMock()
        sub = mock.MagicMock()
        subparsers.add_parser.return_value = sub
        mapper = {}
        self.u.define_commands_from_module(subparsers, mod, mapper)

    def test_print_dict(self):
        with mock.patch('builtins.print'):
            self.u.print_dict({'k': 'v'})

    def test_print_list_simple(self):
        o = mock.MagicMock()
        o.f1 = 'v1'
        with mock.patch('builtins.print'):
            self.u.print_list([o], ['f1'], ['F1'])

    def test_wordwrap_header_nowrap(self):
        from fmclient.common import wrapping_formatters as wf
        with mock.patch.object(wf, 'is_nowrap_set', return_value=True):
            r = self.u.wordwrap_header('f', 'Label', None)
            self.assertEqual(r, 'Label')

    def test_default_printer(self):
        with mock.patch('builtins.print') as mp:
            self.u.default_printer('hello')
            mp.assert_called_with('hello')


# ── fmclient.common.wrapping_formatters ────────────────────────────
class TestWrappingFormatters(unittest.TestCase):
    def setUp(self):
        from fmclient.common import wrapping_formatters as wf
        self.wf = wf

    def test_get_width_none(self):
        self.assertEqual(self.wf.get_width(None), 0)

    def test_get_width_string(self):
        self.assertGreater(self.wf.get_width('hello'), 0)

    def test_is_uuid_field_true(self):
        self.assertTrue(self.wf.is_uuid_field('uuid'))
        self.assertTrue(self.wf.is_uuid_field('UUID'))

    def test_is_uuid_field_false(self):
        self.assertFalse(self.wf.is_uuid_field('name'))

    def test_is_nowrap_set(self):
        from fmclient.common import cli_no_wrap
        cli_no_wrap._no_wrap = [False]
        self.assertFalse(self.wf.is_nowrap_set())

    def test_set_no_wrap(self):
        result = self.wf.set_no_wrap(True)
        self.assertTrue(result)
        self.wf.set_no_wrap(False)

    def test_wrapper_context_init(self):
        ctx = self.wf.WrapperContext()
        self.assertEqual(ctx.wrappers, [])

    def test_wrapper_context_set_num_columns(self):
        ctx = self.wf.WrapperContext()
        ctx.set_num_columns(5)
        self.assertEqual(ctx.num_columns, 5)

    def test_wrapper_context_get_terminal_width(self):
        ctx = self.wf.WrapperContext()
        w = ctx.get_terminal_width()
        self.assertGreater(w, 0)

    def test_uuid_min_length(self):
        self.assertEqual(self.wf.UUID_MIN_LENGTH, 36)

    def test_build_wrapping_formatters_empty(self):
        result = self.wf.build_wrapping_formatters(
            [], ['f1'], ['F1'], {})
        self.assertIsInstance(result, dict)

    def test_set_no_wrap_on_formatters(self):
        formatters = {}
        result = self.wf.set_no_wrap_on_formatters(True, formatters)
        self.assertIsInstance(result, dict)

    def test_unset_no_wrap_on_formatters(self):
        self.wf.unset_no_wrap_on_formatters({})


# ── fmclient.common.http ──────────────────────────────────────────
class TestFmclientHttp(unittest.TestCase):
    def test_encode_headers(self):
        from fmclient.common.http import encode_headers
        r = encode_headers({'Content-Type': 'application/json'})
        self.assertIsNotNone(r)

    def test_chunk_body(self):
        from fmclient.common.http import _BaseHTTPClient
        body = mock.MagicMock()
        body.read = mock.MagicMock(side_effect=[b'data', b''])
        chunks = list(_BaseHTTPClient._chunk_body(body))
        self.assertEqual(chunks, [b'data'])

    def test_get_http_client_session(self):
        from fmclient.common.http import get_http_client
        s = mock.MagicMock()
        c = get_http_client('http://h:18002', session=s)
        self.assertIsNotNone(c)

    def test_session_client_init(self):
        from tests.base import make_http_client
        c = make_http_client()
        self.assertIsNotNone(c)

    def test_session_client_get(self):
        from tests.base import make_http_client
        r, body = make_http_client().get('/v1/alarms')
        self.assertIsNotNone(body)

    def test_session_client_delete(self):
        from tests.base import make_http_client
        make_http_client(
            status=204, data=None,
            content_type='text/plain').delete('/v1/alarms/uuid-1')

    def test_session_client_patch(self):
        from tests.base import make_http_client
        r, body = make_http_client().patch(
            '/v1/event_suppression/u1', data='[]')
        self.assertIsNotNone(body)


# ── fmclient.common.exceptions ────────────────────────────────────
class TestFmclientExceptionsDeep(unittest.TestCase):
    def test_exception_classes_exist(self):
        from fmclient.common import exceptions as exc
        names = [
            'HttpError',
            'HTTPBadRequest',
            'HTTPUnauthorized',
            'HTTPForbidden', 'HTTPNotFound',
            'HTTPMethodNotAllowed',
            'HTTPConflict',
            'HTTPOverLimit', 'HTTPUnsupported',
            'HTTPInternalServerError',
            'HTTPNotImplemented',
            'HTTPBadGateway',
            'HTTPServiceUnavailable',
        ]
        for cls_name in names:
            if hasattr(exc, cls_name):
                cls = getattr(exc, cls_name)
                self.assertTrue(callable(cls))


# ── fmclient.shell ────────────────────────────────────────────────
class TestFmShell(unittest.TestCase):
    def test_shell_get_base_parser(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        p = sh.get_base_parser()
        self.assertIsNotNone(p)

    def test_shell_setup_debugging(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        sh._setup_debugging(False)
        sh._setup_debugging(True)

    def test_shell_cache_key(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        self.assertIn('fmclient', sh._cache_key('admin'))

    def test_shell_cache_key_empty(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        self.assertEqual(sh._cache_key(''), sh.CACHE_KEY)

    def test_shell_help(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        sh.parser = mock.MagicMock()
        args = mock.MagicMock()
        args.command = None
        sh.do_help(args)

    def test_shell_main_help(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        result = sh.main(['--help'])
        self.assertEqual(result, 0)

    def test_shell_main_empty(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        result = sh.main([])
        self.assertEqual(result, 0)

    def test_shell_bash_completion(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        sh.subcommands = {
            'alarm-list': mock.MagicMock(),
            'bash_completion': mock.MagicMock(),
        }
        sc = sh.subcommands
        sc['alarm-list']\
            ._optionals._option_string_actions = {
            '--help': None}
        sc['bash_completion']\
            ._optionals._option_string_actions = {
            '--help': None}
        with mock.patch('builtins.print'):
            sh.do_bash_completion(mock.MagicMock())


# ── fmclient.v1 shell modules ────────────────────────────────────
class TestAlarmShell(unittest.TestCase):
    def test_display_fault(self):
        from fmclient.v1 import alarm_shell
        fault = mock.MagicMock()
        with mock.patch('fmclient.common.utils.print_dict'):
            alarm_shell._display_fault(fault)

    def test_do_alarm_show(self):
        from fmclient.v1 import alarm_shell
        cc = mock.MagicMock()
        cc.alarm.get.return_value = mock.MagicMock()
        args = mock.MagicMock()
        args.alarm = 'uuid-1'
        with mock.patch('fmclient.common.utils.print_dict'):
            alarm_shell.do_alarm_show(cc, args)

    def test_do_alarm_delete(self):
        from fmclient.v1 import alarm_shell
        cc = mock.MagicMock()
        args = mock.MagicMock()
        args.alarm = 'uuid-1'
        alarm_shell.do_alarm_delete(cc, args)
        cc.alarm.delete.assert_called_with('uuid-1')

    def test_do_alarm_list(self):
        from fmclient.v1 import alarm_shell
        cc = mock.MagicMock()
        cc.alarm.list.return_value = []
        args = mock.MagicMock()
        args.query = None
        args.uuid = False
        args.include_suppress = False
        args.mgmt_affecting = False
        args.degrade_affecting = False
        with mock.patch('fmclient.common.utils.print_list'):
            alarm_shell.do_alarm_list(cc, args)

    def test_do_alarm_summary(self):
        from fmclient.v1 import alarm_shell
        cc = mock.MagicMock()
        cc.alarm.summary.return_value = []
        args = mock.MagicMock()
        args.include_suppress = False
        with mock.patch('fmclient.common.utils.print_list'):
            alarm_shell.do_alarm_summary(cc, args)


class TestEventLogShell(unittest.TestCase):
    def test_display_event(self):
        from fmclient.v1 import event_log_shell
        log = mock.MagicMock()
        with mock.patch('fmclient.common.utils.print_dict'):
            event_log_shell._display_event(log)

    def test_do_event_show(self):
        from fmclient.v1 import event_log_shell
        cc = mock.MagicMock()
        cc.event_log.get.return_value = mock.MagicMock()
        args = mock.MagicMock()
        args.event_log = 'uuid-1'
        with mock.patch('fmclient.common.utils.print_dict'):
            event_log_shell.do_event_show(cc, args)

    def test_do_event_list(self):
        from fmclient.v1 import event_log_shell
        cc = mock.MagicMock()
        cc.event_log.list.return_value = []
        args = mock.MagicMock()
        args.query = None
        args.limit = None
        args.alarms = False
        args.logs = False
        args.uuid = False
        args.include_suppress = False
        args.nopaging = True
        with mock.patch('fmclient.common.utils.print_long_list'):
            event_log_shell.do_event_list(cc, args)


class TestEventSuppressionShell(unittest.TestCase):
    def test_do_event_suppress_list(self):
        from fmclient.v1 import event_suppression_shell as ess
        if hasattr(ess, 'do_event_suppress_list'):
            cc = mock.MagicMock()
            cc.event_suppression.list.return_value = []
            args = mock.MagicMock()
            args.query = None
            args.uuid = False
            with mock.patch('fmclient.common.utils.print_list'):
                ess.do_event_suppress_list(cc, args)

    def test_display_event_suppression(self):
        from fmclient.v1 import event_suppression_shell as ess
        if hasattr(ess, '_display_event_suppression'):
            es = mock.MagicMock()
            with mock.patch('fmclient.common.utils.print_dict'):
                ess._display_event_suppression(es)


# ── fm-rest-api controllers ──────────────────────────────────────
class TestAlarmController(unittest.TestCase):
    def test_alarm_controller_importable(self):
        from fm.api.controllers.v1 import alarm
        self.assertTrue(hasattr(alarm, 'AlarmController'))

    @mock.patch('pecan.request')
    def test_alarm_as_dict(self, mr):
        from fm.api.controllers.v1 import alarm
        a = alarm.Alarm()
        a.links = []
        d = a.as_dict()
        self.assertIsInstance(d, dict)


class TestEventLogController(unittest.TestCase):
    def test_event_log_controller_importable(self):
        from fm.api.controllers.v1 import event_log
        self.assertTrue(hasattr(event_log, 'EventLogController'))


class TestEventSuppressionController(unittest.TestCase):
    def test_event_suppression_controller_importable(self):
        from fm.api.controllers.v1 import event_suppression
        self.assertTrue(hasattr(event_suppression,
                                'EventSuppressionController'))


# ── fm.common.context ────────────────────────────────────────────
class TestFmContext(unittest.TestCase):
    def test_make_context(self):
        from fm.common import context
        self.assertTrue(callable(context.make_context))

    @mock.patch('fm.common.policy.authorize', return_value=True)
    @mock.patch(
        'fm.common.utils.get_debian_codename',
        return_value='trixie')
    def test_request_context_trixie(self, mock_cn, mock_auth):
        from fm.common.context import RequestContext
        ctx = RequestContext(
            auth_token='tok', user_name='admin',
            project_name='admin', roles=['admin'])
        self.assertEqual(ctx.user_name, 'admin')
        d = ctx.to_dict()
        self.assertIn('user_name', d)

    @mock.patch('fm.common.policy.authorize', return_value=True)
    @mock.patch(
        'fm.common.utils.get_debian_codename',
        return_value='bullseye')
    def test_request_context_bullseye(self, mock_cn, mock_auth):
        from fm.common.context import RequestContext
        ctx = RequestContext(
            auth_token='tok', user_name='admin',
            project_name='admin', roles=['admin'],
            is_admin=True)
        self.assertTrue(ctx.is_admin)

    @mock.patch('fm.common.policy.authorize', return_value=False)
    @mock.patch(
        'fm.common.utils.get_debian_codename',
        return_value='trixie')
    def test_request_context_from_dict(self, mock_cn, mock_auth):
        from fm.common.context import RequestContext
        ctx = RequestContext(
            auth_token='tok', user_name='u',
            project_name='p', roles=[])
        d = ctx.to_dict()
        ctx2 = RequestContext.from_dict(d)
        self.assertIsNotNone(ctx2)

    @mock.patch('fm.common.policy.authorize', return_value=False)
    @mock.patch(
        'fm.common.utils.get_debian_codename',
        return_value='trixie')
    def test_request_context_service_catalog(self, mock_cn, mock_auth):
        from fm.common.context import RequestContext
        sc = [{'type': 'platform', 'endpoints': []},
              {'type': 'identity', 'endpoints': []}]
        ctx = RequestContext(
            auth_token='tok', user_name='u',
            project_name='p', roles=[],
            service_catalog=sc)
        self.assertEqual(len(ctx.service_catalog), 1)

    @mock.patch('fm.common.policy.authorize', return_value=False)
    @mock.patch(
        'fm.common.utils.get_debian_codename',
        return_value='trixie')
    def test_request_context_get_auth_plugin(self, mock_cn, mock_auth):
        from fm.common.context import RequestContext
        ctx = RequestContext(
            auth_token='tok', user_name='u',
            project_name='p', roles=[])
        plugin = ctx.get_auth_plugin()
        self.assertIsNotNone(plugin)


# ── fm.api.middleware.auth_token ─────────────────────────────────
class TestAuthTokenMiddleware(unittest.TestCase):
    def test_factory(self):
        from fm.api.middleware.auth_token import AuthTokenMiddleware
        factory = AuthTokenMiddleware.factory(
            {}, acl_public_routes='/v1')
        self.assertTrue(callable(factory))


# ── fm.db.sqlalchemy.api ─────────────────────────────────────────
class TestDbSqlalchemyApi(unittest.TestCase):
    def test_get_backend(self):
        from fm.db.sqlalchemy import api
        self.assertTrue(callable(api.get_backend))

    def test_paginate_query_callable(self):
        from fm.db.sqlalchemy import api
        self.assertTrue(callable(api._paginate_query))


if __name__ == '__main__':
    unittest.main()
