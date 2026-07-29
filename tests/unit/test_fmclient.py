#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for python-fmclient modules."""
# pylint: disable=protected-access,unused-argument
import unittest
from unittest import mock


class TestFmclientCommonBase(unittest.TestCase):
    """Test fmclient.common.base module."""

    def setUp(self):
        from fmclient.common import base
        self.base = base

    def test_getid_with_object(self):
        obj = mock.MagicMock()
        obj.id = 'uuid-123'
        self.assertEqual(self.base.getid(obj), 'uuid-123')

    def test_getid_with_string(self):
        self.assertEqual(self.base.getid('uuid-123'), 'uuid-123')

    def test_manager_init(self):
        api = mock.MagicMock()
        mgr = self.base.Manager(api)
        self.assertEqual(mgr.api, api)

    def test_manager_json_get(self):
        api = mock.MagicMock()
        api.get.return_value = (mock.MagicMock(), {'key': 'val'})
        mgr = self.base.Manager(api)
        result = mgr._json_get('/test')
        self.assertEqual(result, {'key': 'val'})

    def test_manager_format_body_data_with_key(self):
        mgr = self.base.Manager(mock.MagicMock())
        body = {'items': [1, 2, 3]}
        result = mgr._format_body_data(body, 'items')
        self.assertEqual(result, [1, 2, 3])

    def test_manager_format_body_data_missing_key(self):
        mgr = self.base.Manager(mock.MagicMock())
        body = {'other': [1]}
        result = mgr._format_body_data(body, 'items')
        self.assertEqual(result, [])

    def test_manager_format_body_data_no_key(self):
        mgr = self.base.Manager(mock.MagicMock())
        body = {'a': 1}
        result = mgr._format_body_data(body, None)
        self.assertEqual(result, [{'a': 1}])

    def test_manager_delete(self):
        api = mock.MagicMock()
        mgr = self.base.Manager(api)
        mgr._delete('/test/1')
        api.delete.assert_called_once_with('/test/1')

    def test_resource_init(self):
        mgr = mock.MagicMock()
        info = {'id': '1', 'name': 'test'}
        res = self.base.Resource(mgr, info, loaded=True)
        self.assertEqual(res.id, '1')
        self.assertEqual(res.name, 'test')
        self.assertTrue(res.is_loaded())

    def test_resource_repr(self):
        mgr = mock.MagicMock()
        info = {'id': '1', 'name': 'test'}
        res = self.base.Resource(mgr, info, loaded=True)
        r = repr(res)
        self.assertIn('Resource', r)

    def test_resource_to_dict(self):
        mgr = mock.MagicMock()
        info = {'id': '1', 'name': 'test'}
        res = self.base.Resource(mgr, info, loaded=True)
        d = res.to_dict()
        self.assertEqual(d, info)

    def test_resource_eq(self):
        mgr = mock.MagicMock()
        r1 = self.base.Resource(mgr, {'id': '1'}, loaded=True)
        r2 = self.base.Resource(mgr, {'id': '1'}, loaded=True)
        self.assertEqual(r1, r2)

    def test_resource_ne(self):
        mgr = mock.MagicMock()
        r1 = self.base.Resource(mgr, {'id': '1'}, loaded=True)
        r2 = self.base.Resource(mgr, {'id': '2'}, loaded=True)
        self.assertNotEqual(r1, r2)

    def test_resource_ne_different_type(self):
        mgr = mock.MagicMock()
        r1 = self.base.Resource(mgr, {'id': '1'}, loaded=True)
        self.assertNotEqual(r1, "not a resource")

    def test_resource_set_loaded(self):
        mgr = mock.MagicMock()
        res = self.base.Resource(mgr, {'id': '1'}, loaded=False)
        self.assertFalse(res.is_loaded())
        res.set_loaded(True)
        self.assertTrue(res.is_loaded())


class TestFmclientCommonOptions(unittest.TestCase):
    """Test fmclient.common.options module."""

    def setUp(self):
        from fmclient.common import options
        self.options = options

    def test_build_url_no_query(self):
        result = self.options.build_url('/v1/alarms', None)
        self.assertEqual(result, '/v1/alarms')

    def test_build_url_with_params(self):
        result = self.options.build_url('/v1/alarms', None,
                                        ['limit=10'])
        self.assertIn('limit=10', result)

    def test_build_url_with_query(self):
        q = [{'field': 'severity', 'op': 'eq', 'value': 'critical',
              'type': ''}]
        result = self.options.build_url('/v1/alarms', q)
        self.assertIn('q.field=severity', result)

    def test_build_url_with_query_and_params(self):
        q = [{'field': 'severity', 'op': 'eq', 'value': 'critical',
              'type': ''}]
        result = self.options.build_url('/v1/alarms', q, ['limit=5'])
        self.assertIn('q.field', result)
        self.assertIn('limit=5', result)

    def test_build_url_params_only_multiple(self):
        result = self.options.build_url('/v1/alarms', None,
                                        ['limit=10', 'marker=abc'])
        self.assertIn('limit=10', result)
        self.assertIn('marker=abc', result)

    def test_cli_to_array_none(self):
        self.assertIsNone(self.options.cli_to_array(None))

    def test_cli_to_array_simple(self):
        result = self.options.cli_to_array('severity=critical')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'severity')
        self.assertEqual(result[0]['op'], 'eq')
        self.assertEqual(result[0]['value'], 'critical')

    def test_cli_to_array_with_type(self):
        result = self.options.cli_to_array('count>=integer::5')
        self.assertEqual(result[0]['op'], 'ge')
        self.assertEqual(result[0]['type'], 'integer')
        self.assertEqual(result[0]['value'], '5')

    def test_cli_to_array_multiple(self):
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

    def test_cli_to_array_missing_operator(self):
        with self.assertRaises(ValueError):
            self.options.cli_to_array('noop')

    def test_cli_to_array_missing_value(self):
        with self.assertRaises(ValueError):
            self.options.cli_to_array('field=')

    def test_cli_to_array_missing_field(self):
        with self.assertRaises(ValueError):
            self.options.cli_to_array('=value')


class TestFmclientCliNoWrap(unittest.TestCase):
    """Test fmclient.common.cli_no_wrap module."""

    def setUp(self):
        from fmclient.common import cli_no_wrap
        self.cli = cli_no_wrap
        self.cli._no_wrap = [False]

    def test_is_nowrap_set_default(self):
        self.assertFalse(self.cli.is_nowrap_set())

    def test_is_nowrap_set_true_param(self):
        self.assertTrue(self.cli.is_nowrap_set(True))

    def test_is_nowrap_set_false_param(self):
        self.assertFalse(self.cli.is_nowrap_set(False))

    def test_set_no_wrap_true(self):
        result = self.cli.set_no_wrap(True)
        self.assertTrue(result)

    def test_set_no_wrap_false(self):
        self.cli.set_no_wrap(True)
        result = self.cli.set_no_wrap(False)
        self.assertFalse(result)

    def test_set_no_wrap_none(self):
        self.cli.set_no_wrap(None)
        self.assertFalse(self.cli.is_nowrap_set())

    def test_is_nowrap_set_global(self):
        self.cli._no_wrap[0] = True
        self.assertTrue(self.cli.is_nowrap_set())


class TestFmclientI18n(unittest.TestCase):
    """Test fmclient.common.i18n module."""

    def test_translator_exists(self):
        from fmclient.common import i18n
        self.assertTrue(callable(i18n._))


class TestFmclientV1Alarm(unittest.TestCase):
    """Test fmclient.v1.alarm module."""

    def setUp(self):
        from fmclient.v1 import alarm
        self.alarm = alarm

    def test_alarm_repr(self):
        mgr = mock.MagicMock()
        a = self.alarm.Alarm(mgr, {'uuid': 'test-uuid'}, loaded=True)
        self.assertIn('Alarm', repr(a))

    def test_alarm_manager_path_no_id(self):
        self.assertEqual(self.alarm.AlarmManager._path(),
                         '/v1/alarms')

    def test_alarm_manager_path_with_id(self):
        self.assertEqual(self.alarm.AlarmManager._path('uuid-1'),
                         '/v1/alarms/uuid-1')

    def test_alarm_manager_list(self):
        api = mock.MagicMock()
        api.get.return_value = (None, {'alarms': []})
        mgr = self.alarm.AlarmManager(api)
        result = mgr.list()
        self.assertIsInstance(result, list)

    def test_alarm_manager_get_found(self):
        api = mock.MagicMock()
        api.get.return_value = (None, [{'uuid': 'u1'}])
        mgr = self.alarm.AlarmManager(api)
        result = mgr.get('u1')
        self.assertIsNotNone(result)

    def test_alarm_manager_get_not_found(self):
        api = mock.MagicMock()
        api.get.return_value = (None, [])
        mgr = self.alarm.AlarmManager(api)
        result = mgr.get('u1')
        self.assertIsNone(result)

    def test_alarm_manager_delete(self):
        api = mock.MagicMock()
        mgr = self.alarm.AlarmManager(api)
        mgr.delete('uuid-1')
        api.delete.assert_called_once()


class TestFmclientV1EventLog(unittest.TestCase):
    """Test fmclient.v1.event_log module."""

    def setUp(self):
        from fmclient.v1 import event_log
        self.el = event_log

    def test_event_log_repr(self):
        mgr = mock.MagicMock()
        e = self.el.EventLog(mgr, {'uuid': 'test'}, loaded=True)
        self.assertIn('EventLog', repr(e))

    def test_event_log_manager_path(self):
        self.assertEqual(self.el.EventLogManager._path(),
                         '/v1/event_log')
        self.assertEqual(self.el.EventLogManager._path('id-1'),
                         '/v1/event_log/id-1')

    def test_event_log_manager_get_not_found(self):
        api = mock.MagicMock()
        api.get.return_value = (None, [])
        mgr = self.el.EventLogManager(api)
        result = mgr.get('id-1')
        self.assertIsNone(result)


class TestFmclientV1EventSuppression(unittest.TestCase):
    """Test fmclient.v1.event_suppression module."""

    def setUp(self):
        from fmclient.v1 import event_suppression
        self.es = event_suppression

    def test_event_suppression_repr(self):
        mgr = mock.MagicMock()
        e = self.es.EventSuppression(mgr, {'uuid': 'test'}, loaded=True)
        self.assertIn('EventSuppression', repr(e))

    def test_event_suppression_manager_path(self):
        self.assertEqual(self.es.EventSuppressionManager._path(),
                         '/v1/event_suppression')
        self.assertEqual(self.es.EventSuppressionManager._path('id-1'),
                         '/v1/event_suppression/id-1')

    def test_event_suppression_manager_get_not_found(self):
        api = mock.MagicMock()
        api.get.return_value = (None, [])
        mgr = self.es.EventSuppressionManager(api)
        result = mgr.get('id-1')
        self.assertIsNone(result)

    def test_event_suppression_manager_update(self):
        api = mock.MagicMock()
        api.patch.return_value = (None, {'uuid': 'u1'})
        mgr = self.es.EventSuppressionManager(api)
        mgr.update('u1', [{'op': 'replace', 'path': '/status',
                           'value': 'suppressed'}])
        api.patch.assert_called_once()


class TestFmclientV1Client(unittest.TestCase):
    """Test fmclient.v1.client module."""

    def test_client_init_with_session(self):
        from fmclient.v1 import client
        session = mock.MagicMock()
        c = client.Client(endpoint='http://localhost:18002',
                          session=session)
        self.assertIsNotNone(c.alarm)
        self.assertIsNotNone(c.event_log)
        self.assertIsNotNone(c.event_suppression)

    def test_client_init_no_endpoint_no_version(self):
        from fmclient.v1 import client
        from fmclient.common import exceptions as exc
        with self.assertRaises(exc.EndpointException):
            client.Client()


class TestFmclientCommonExceptions(unittest.TestCase):
    """Test fmclient.common.exceptions module."""

    def test_all_exception_codes(self):
        from fmclient import exc
        self.assertEqual(exc.HTTPMultipleChoices.code, 300)
        self.assertEqual(exc.Unauthorized.code, 401)
        self.assertEqual(exc.NotFound.code, 404)
        self.assertEqual(exc.HTTPMethodNotAllowed.code, 405)
        self.assertEqual(exc.HTTPInternalServerError.code, 500)
        self.assertEqual(exc.HTTPNotImplemented.code, 501)
        self.assertEqual(exc.HTTPBadGateway.code, 502)


class TestFmclientCommonUtils(unittest.TestCase):
    """Test fmclient.common.utils module."""

    def setUp(self):
        from fmclient.common import utils
        self.utils = utils

    def test_safe_header_sensitive(self):
        name, value = self.utils.safe_header('X-Auth-Token', 'secret')
        self.assertIn('{SHA1}', value)

    def test_safe_header_normal(self):
        name, value = self.utils.safe_header('Content-Type', 'json')
        self.assertEqual(value, 'json')

    def test_safe_header_none_value(self):
        name, value = self.utils.safe_header('X-Auth-Token', None)
        self.assertIsNone(value)

    def test_strip_version_with_version(self):
        endpoint, version = self.utils.strip_version(
            'http://localhost:18002/v1')
        self.assertEqual(endpoint, 'http://localhost:18002')
        self.assertEqual(version, 1.0)

    def test_strip_version_without_version(self):
        endpoint, version = self.utils.strip_version(
            'http://localhost:18002')
        self.assertIsNone(version)

    def test_strip_version_trailing_slash(self):
        endpoint, version = self.utils.strip_version(
            'http://localhost:18002/v2.0/')
        self.assertEqual(version, 2.0)

    def test_strip_version_invalid_input(self):
        with self.assertRaises(ValueError):
            self.utils.strip_version(12345)

    def test_endpoint_version_from_url(self):
        ep, ver = self.utils.endpoint_version_from_url(
            'http://localhost:18002/v1')
        self.assertEqual(ep, 'http://localhost:18002')
        self.assertEqual(ver, 1.0)

    def test_endpoint_version_from_url_none(self):
        ep, ver = self.utils.endpoint_version_from_url(None, '1.0')
        self.assertIsNone(ep)
        self.assertEqual(ver, '1.0')

    def test_endpoint_version_from_url_default(self):
        ep, ver = self.utils.endpoint_version_from_url(
            'http://localhost:18002', '1.0')
        self.assertEqual(ver, '1.0')

    def test_help_formatter(self):
        fmt = self.utils.HelpFormatter('prog')
        self.assertIsNotNone(fmt)


if __name__ == '__main__':
    unittest.main()
