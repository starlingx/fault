#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for python-fmclient: common, v1, shell, client modules."""
# pylint: disable=protected-access,unused-argument

import os
import unittest
from unittest import mock
from tests.base import make_http_client


class TestFmclientCommonBase(unittest.TestCase):
    """Test fmclient.common.base module."""

    def setUp(self):
        from fmclient.common import base
        self.base = base

    def test_getid(self):
        obj = mock.MagicMock()
        obj.id = 'uuid-123'
        self.assertEqual(self.base.getid(obj), 'uuid-123')
        self.assertEqual(self.base.getid('uuid-123'), 'uuid-123')

    def test_manager(self):
        api = mock.MagicMock()
        api.get.return_value = (mock.MagicMock(), {'key': 'val'})
        mgr = self.base.Manager(api)
        self.assertEqual(mgr._json_get('/test'), {'key': 'val'})
        mgr._delete('/test/1')
        api.delete.assert_called_once_with('/test/1')

    def test_manager_format_body_data(self):
        mgr = self.base.Manager(mock.MagicMock())
        self.assertEqual(
            mgr._format_body_data({'items': [1, 2]}, 'items'), [1, 2])
        self.assertEqual(
            mgr._format_body_data({'other': [1]}, 'items'), [])
        self.assertEqual(
            mgr._format_body_data({'a': 1}, None), [{'a': 1}])

    def test_resource(self):
        mgr = mock.MagicMock()
        info = {'id': '1', 'name': 'test'}
        res = self.base.Resource(mgr, info, loaded=True)
        self.assertEqual(res.id, '1')
        self.assertTrue(res.is_loaded())
        self.assertEqual(res.to_dict(), info)
        self.assertIn('Resource', repr(res))
        r2 = self.base.Resource(mgr, {'id': '1'}, loaded=True)
        self.assertEqual(res, r2)
        r3 = self.base.Resource(mgr, {'id': '2'}, loaded=True)
        self.assertNotEqual(res, r3)
        self.assertNotEqual(res, "not a resource")


class TestFmclientCommonOptions(unittest.TestCase):
    """Test fmclient.common.options module."""

    def setUp(self):
        from fmclient.common import options
        self.options = options

    def test_build_url(self):
        self.assertEqual(
            self.options.build_url('/v1/alarms', None), '/v1/alarms')
        result = self.options.build_url(
            '/v1/alarms', None, ['limit=10'])
        self.assertIn('limit=10', result)
        q = [{'field': 'severity', 'op': 'eq',
              'value': 'critical', 'type': ''}]
        self.assertIn('q.field=severity',
                      self.options.build_url('/v1/alarms', q))

    def test_cli_to_array(self):
        self.assertIsNone(self.options.cli_to_array(None))
        result = self.options.cli_to_array('severity=critical')
        self.assertEqual(result[0]['field'], 'severity')
        self.assertEqual(result[0]['op'], 'eq')
        result = self.options.cli_to_array('a=1;b!=2')
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]['op'], 'ne')

    def test_cli_to_array_all_operators(self):
        ops = [('=', 'eq'), ('!=', 'ne'), ('>=', 'ge'),
               ('<=', 'le'), ('>', 'gt'), ('<', 'lt')]
        for op_str, op_name in ops:
            result = self.options.cli_to_array(
                'field%svalue' % op_str)
            self.assertEqual(result[0]['op'], op_name)

    def test_cli_to_array_errors(self):
        for bad in ['noop', 'field=', '=value']:
            with self.assertRaises(ValueError):
                self.options.cli_to_array(bad)


class TestFmclientCliNoWrap(unittest.TestCase):
    """Test fmclient.common.cli_no_wrap module."""

    def setUp(self):
        from fmclient.common import cli_no_wrap
        self.cli = cli_no_wrap
        self.cli._no_wrap = [False]

    def test_nowrap(self):
        self.assertFalse(self.cli.is_nowrap_set())
        self.assertTrue(self.cli.is_nowrap_set(True))
        self.cli.set_no_wrap(True)
        self.assertTrue(self.cli.is_nowrap_set())
        self.cli.set_no_wrap(False)
        self.assertFalse(self.cli.is_nowrap_set())


class TestFmclientV1Alarm(unittest.TestCase):
    """Test fmclient.v1.alarm module."""

    def setUp(self):
        from fmclient.v1 import alarm
        self.alarm = alarm

    def test_alarm_manager(self):
        self.assertEqual(self.alarm.AlarmManager._path(), '/v1/alarms')
        self.assertEqual(
            self.alarm.AlarmManager._path('u1'), '/v1/alarms/u1')
        api = mock.MagicMock()
        api.get.return_value = (None, {'alarms': []})
        mgr = self.alarm.AlarmManager(api)
        self.assertIsInstance(mgr.list(), list)
        mgr.list(limit=10, marker='m', sort_key='severity',
                 sort_dir='asc', include_suppress=True, expand=True)
        api.get.return_value = (None, [{'uuid': 'u1'}])
        self.assertIsNotNone(mgr.get('u1'))
        api.get.return_value = (None, [])
        self.assertIsNone(mgr.get('u1'))
        mgr.delete('uuid-1')
        api.delete.assert_called_once()

    def test_alarm_manager_summary(self):
        api = mock.MagicMock()
        api.get.return_value = (None, [])
        mgr = self.alarm.AlarmManager(api)
        mgr.summary(include_suppress=True)
        api.get.assert_called()


class TestFmclientV1EventLog(unittest.TestCase):
    """Test fmclient.v1.event_log module."""

    def setUp(self):
        from fmclient.v1 import event_log
        self.el = event_log

    def test_event_log_manager(self):
        self.assertEqual(
            self.el.EventLogManager._path(), '/v1/event_log')
        api = mock.MagicMock()
        api.get.return_value = (None, [])
        mgr = self.el.EventLogManager(api)
        self.assertIsNone(mgr.get('id-1'))
        api.get.return_value = (None, {'event_log': []})
        mgr.list(alarms=True, logs=False, limit=5,
                 include_suppress=True, expand=True)
        mgr.list(alarms=False, logs=True)


class TestFmclientV1EventSuppression(unittest.TestCase):
    """Test fmclient.v1.event_suppression module."""

    def test_event_suppression_manager(self):
        from fmclient.v1 import event_suppression as es
        self.assertEqual(
            es.EventSuppressionManager._path(),
            '/v1/event_suppression')
        api = mock.MagicMock()
        api.get.return_value = (None, [])
        mgr = es.EventSuppressionManager(api)
        self.assertIsNone(mgr.get('id-1'))
        api.patch.return_value = (None, {'uuid': 'u1'})
        mgr.update('u1', [{'op': 'replace', 'path': '/status',
                           'value': 'suppressed'}])
        api.patch.assert_called_once()


class TestFmclientV1Client(unittest.TestCase):
    """Test fmclient.v1.client module."""

    def test_client_init(self):
        from fmclient.v1 import client
        from fmclient.common import exceptions as exc
        session = mock.MagicMock()
        c = client.Client(endpoint='http://localhost:18002',
                          session=session)
        self.assertIsNotNone(c.alarm)
        self.assertIsNotNone(c.event_log)
        self.assertIsNotNone(c.event_suppression)
        with self.assertRaises(exc.EndpointException):
            client.Client()


class TestFmclientCommonExceptions(unittest.TestCase):
    """Test fmclient.common.exceptions module."""

    def test_from_response(self):
        from fmclient.common import exceptions as exc
        for code in [400, 401, 404, 500, 418]:
            resp = mock.MagicMock()
            resp.status_code = code
            self.assertIsNotNone(exc.from_response(resp, "msg"))

    def test_exception_codes(self):
        from fmclient import exc
        self.assertEqual(exc.HTTPMultipleChoices.code, 300)
        self.assertEqual(exc.Unauthorized.code, 401)
        self.assertEqual(exc.NotFound.code, 404)
        self.assertEqual(exc.HTTPInternalServerError.code, 500)
        self.assertEqual(exc.HTTPNotImplemented.code, 501)
        self.assertEqual(exc.HTTPBadGateway.code, 502)


class TestFmclientCommonUtils(unittest.TestCase):
    """Test fmclient.common.utils module."""

    def setUp(self):
        from fmclient.common import utils
        self.utils = utils

    def test_safe_header(self):
        _, v = self.utils.safe_header('X-Auth-Token', 'secret')
        self.assertIn('{SHA1}', v)
        _, v = self.utils.safe_header('Content-Type', 'json')
        self.assertEqual(v, 'json')
        _, v = self.utils.safe_header('X-Auth-Token', None)
        self.assertIsNone(v)

    def test_strip_version(self):
        ep, ver = self.utils.strip_version(
            'http://localhost:18002/v1')
        self.assertEqual(ep, 'http://localhost:18002')
        self.assertEqual(ver, 1.0)
        ep, ver = self.utils.strip_version(
            'http://localhost:18002')
        self.assertIsNone(ver)
        with self.assertRaises(ValueError):
            self.utils.strip_version(12345)

    def test_endpoint_version_from_url(self):
        ep, ver = self.utils.endpoint_version_from_url(
            'http://localhost:18002/v1')
        self.assertEqual(ver, 1.0)
        ep, ver = self.utils.endpoint_version_from_url(None, '1.0')
        self.assertIsNone(ep)

    def test_env(self):
        os.environ['_TEST_FM_VAR'] = 'val'
        self.assertEqual(self.utils.env('_TEST_FM_VAR'), 'val')
        del os.environ['_TEST_FM_VAR']
        self.assertEqual(
            self.utils.env('_NONEXISTENT_VAR', default='d'), 'd')

    def test_print_functions(self):
        o = mock.MagicMock()
        o.name = 'test'
        with mock.patch('builtins.print'):
            self.utils.print_list([o], ['name'], ['Name'])
            self.utils.print_list([o], ['name'], ['Name'], sortby=0)
            self.utils.print_dict({'k': 'v' * 200}, wrap=72)
            self.utils.print_long_list(
                [o], ['name'], ['Name'], no_paging=True)


class TestFmclientCommonHttp(unittest.TestCase):
    """Test fmclient.common.http module."""

    def test_session_client_methods(self):
        c = make_http_client(data={'alarms': []})
        _, b = c.get('/v1/alarms')
        self.assertEqual(b, {'alarms': []})

    def test_session_client_post(self):
        c = make_http_client(status=201, data={'uuid': 'n'})
        _, b = c.post('/v1/a', body='{}')
        self.assertEqual(b['uuid'], 'n')

    def test_session_client_patch(self):
        c = make_http_client(data={'uuid': 'u'})
        _, b = c.patch('/v1/e/u', data='[]')
        self.assertEqual(b['uuid'], 'u')

    def test_session_client_put(self):
        c = make_http_client(data={'uuid': 'u'})
        _, b = c.put('/v1/a/u', body='{}')
        self.assertEqual(b['uuid'], 'u')

    def test_session_client_delete(self):
        from tests.base import make_http_client
        make_http_client(
            status=204, data=None,
            content_type='text/plain').delete('/v1/a/u')

    def test_session_client_errors(self):
        for code in [404, 500, 401]:
            c = make_http_client(
                status=code, content_type='text/plain')
            try:
                c.get('/v1/alarms/bad')
            except Exception:
                pass

    def test_encode_headers(self):
        from fmclient.common.http import encode_headers
        self.assertIsNotNone(
            encode_headers({'Content-Type': 'application/json'}))

    def test_get_http_client(self):
        from fmclient.common import http
        c = http.get_http_client(
            'http://h:18002', session=mock.MagicMock())
        self.assertIsNotNone(c)


class TestFmclientWrappingFormatters(unittest.TestCase):
    """Test fmclient.common.wrapping_formatters module."""

    def setUp(self):
        from fmclient.common import wrapping_formatters as wf
        self.wf = wf

    def test_wrapper_formatter(self):
        ctx = self.wf.WrapperContext()
        ctx.set_num_columns(1)
        ctx.terminal_width = 80
        w = self.wf.WrapperFormatter(ctx, None)
        w.get_field_value = lambda d: d
        self.assertEqual(w.format('hello'), 'hello')
        fn = w.as_function()
        self.assertTrue(callable(fn))
        self.assertTrue(
            self.wf.WrapperFormatter.is_wrapper_formatter(fn))
        self.assertFalse(
            self.wf.WrapperFormatter.is_wrapper_formatter(lambda x: x))

    def test_build_wrapping_formatters(self):
        o = mock.MagicMock()
        o.name = 'test'
        for spec in [{'name': 0.5}, {'name': 20},
                     {'name': lambda x: str(x).upper()},
                     {'name': {'formatter': lambda x: str(x),
                               'wrapperFormatter': 0.5}}]:
            r = self.wf.build_wrapping_formatters(
                [o], ['name'], ['Name'], spec)
            self.assertIn('name', r)

    def test_wrapper_context(self):
        ctx = self.wf.WrapperContext()
        ctx.set_num_columns(2)
        ctx.terminal_width = 100
        w1 = self.wf.WrapperFixedWidthFormatter(ctx, 'f1', 20)
        w2 = self.wf.WrapperFixedWidthFormatter(ctx, 'f2', 20)
        ctx.add_column_formatter('f1', w1)
        ctx.add_column_formatter('f2', w2)
        self.assertFalse(ctx.is_table_too_wide())

    def test_set_no_wrap_on_formatters(self):
        ctx = self.wf.WrapperContext()
        ctx.set_num_columns(1)
        ctx.terminal_width = 80
        w = self.wf.WrapperPercentWidthFormatter(ctx, 'f', 0.5)
        fn = w.as_function()
        fmts = {'f': fn}
        orig = self.wf.set_no_wrap_on_formatters(True, fmts)
        self.assertIsInstance(orig, dict)
        self.wf.unset_no_wrap_on_formatters(orig)

    def test_get_terminal_width(self):
        self.assertGreater(self.wf._get_terminal_width(), 0)


class TestFmclientClientModule(unittest.TestCase):
    """Test fmclient.client module."""

    def test_get_client_token_endpoint(self):
        from fmclient import client
        with mock.patch(
                'oslo_utils.importutils.import_versioned_module') as m:
            mock_mod = mock.MagicMock()
            mock_mod.Client.return_value = mock.MagicMock()
            m.return_value = mock_mod
            self.assertIsNotNone(client.get_client(
                1, endpoint='http://h:18002', auth_token='tok'))

    def test_get_client_no_endpoint(self):
        from fmclient import client, exc
        with self.assertRaises(exc.AuthSystem):
            client.get_client(1)


class TestFmclientShell(unittest.TestCase):
    """Test fmclient shell module."""

    def test_shell_errors(self):
        from fmclient import shell
        for exc_type in [KeyboardInterrupt, IOError, Exception("e")]:
            with mock.patch.object(shell.FmShell, 'main',
                                   side_effect=exc_type):
                with self.assertRaises(SystemExit):
                    shell.main()

    def test_get_subcommand_parser(self):
        from fmclient.shell import FmShell
        self.assertIsNotNone(FmShell().get_subcommand_parser('1'))

    def test_alarm_shell_list(self):
        from fmclient.v1 import alarm_shell
        cc = mock.MagicMock()
        cc.alarm.list.return_value = []
        args = mock.MagicMock()
        args.query = None
        args.uuid = True
        args.include_suppress = True
        args.mgmt_affecting = True
        args.degrade_affecting = True
        with mock.patch('fmclient.common.utils.print_list'):
            alarm_shell.do_alarm_list(cc, args)


class TestFmclientExc(unittest.TestCase):
    """Test fmclient.exc module."""

    def test_exceptions(self):
        from fmclient import exc
        self.assertEqual(str(exc.CommandError("bad")), "bad")
        self.assertEqual(exc.HTTPException("d").code, 'N/A')
        self.assertEqual(exc.HTTPMultipleChoices().code, 300)
        self.assertIsInstance(exc.HTTPUnauthorized(), exc.Unauthorized)
        self.assertIsInstance(exc.HTTPNotFound(), exc.NotFound)
        self.assertIsNotNone(str(exc.AuthSystem("auth failed")))
        self.assertIsNotNone(str(exc.EndpointException("ep error")))


if __name__ == '__main__':
    unittest.main()
