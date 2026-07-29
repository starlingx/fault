#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for fm-rest-api: controllers, hooks, middleware, app, objects."""
# pylint: disable=protected-access,unused-argument

import datetime
import unittest
from unittest import mock
from tests.base import (
    BaseControllerTestCase, make_audit_state,
    TEST_UUID, TEST_ALARM_ID,
)


class TestObjectsUtils(unittest.TestCase):
    """Test fm.objects.utils module."""

    def setUp(self):
        from fm.objects import utils
        self.utils = utils

    def test_datetime_or_none(self):
        self.assertIsNone(self.utils.datetime_or_none(None))
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0)
        self.assertIsNotNone(self.utils.datetime_or_none(dt).tzinfo)
        with self.assertRaises(ValueError):
            self.utils.datetime_or_none("not a datetime")

    def test_datetime_or_str_or_none(self):
        self.assertIsNone(self.utils.datetime_or_str_or_none(None))
        self.assertIsNotNone(
            self.utils.datetime_or_str_or_none("2024-01-01T00:00:00"))

    def test_bool_or_none(self):
        self.assertFalse(self.utils.bool_or_none(None))
        self.assertTrue(self.utils.bool_or_none('true'))
        self.assertTrue(self.utils.bool_or_none(1))
        self.assertFalse(self.utils.bool_or_none(0))

    def test_int_or_none(self):
        self.assertIsNone(self.utils.int_or_none(None))
        self.assertEqual(self.utils.int_or_none(42), 42)

    def test_str_or_none(self):
        self.assertIsNone(self.utils.str_or_none(None))
        self.assertEqual(self.utils.str_or_none(42), '42')

    def test_uuid_or_none(self):
        self.assertIsNone(self.utils.uuid_or_none(None))
        self.assertEqual(self.utils.uuid_or_none(TEST_UUID), TEST_UUID)
        with self.assertRaises(ValueError):
            self.utils.uuid_or_none(12345)

    def test_dt_serializer(self):
        self.assertTrue(callable(self.utils.dt_serializer('ts')))

    def test_dt_deserializer(self):
        self.assertIsNone(self.utils.dt_deserializer(None, None))
        self.assertIsNotNone(
            self.utils.dt_deserializer(None, "2024-01-01T00:00:00"))


class TestFmCommonExceptions(unittest.TestCase):
    """Test fm.common.exceptions module."""

    def setUp(self):
        from fm.common import exceptions
        self.exc = exceptions

    def test_api_error(self):
        self.assertIsNotNone(str(self.exc.ApiError()))
        self.assertIn("test", str(self.exc.ApiError(message="test")))

    def test_not_found_variants(self):
        self.assertEqual(self.exc.NotFound.code, 404)
        self.assertIn('t', str(self.exc.AlarmNotFound(alarm='t')))
        self.assertIn('l', str(self.exc.EventLogNotFound(eventLog='l')))
        self.assertIn('n', str(self.exc.NodeNotFound(node='n')))

    def test_invalid_variants(self):
        self.assertEqual(self.exc.Invalid.code, 400)
        self.assertIn('b', str(self.exc.PatchError(patch='p', reason='b')))
        self.assertIn('b', str(self.exc.ConfigInvalid(error_msg='b')))
        self.assertIn('b', str(self.exc.InvalidParameterValue(err='b')))

    def test_conflict_variants(self):
        self.assertEqual(self.exc.Conflict.code, 409)
        self.assertIn('u', str(self.exc.AlarmAlreadyExists(uuid='u')))

    def test_policy_not_authorized(self):
        self.assertEqual(self.exc.PolicyNotAuthorized.code, 401)


class TestFmCommonUtils(unittest.TestCase):
    """Test fm.common.utils module."""

    def setUp(self):
        from fm.common import utils
        self.utils = utils

    def test_safe_rstrip(self):
        self.assertEqual(self.utils.safe_rstrip('hello/', '/'), 'hello')
        self.assertEqual(self.utils.safe_rstrip('/', '/'), '/')
        self.assertEqual(self.utils.safe_rstrip(123), 123)

    @mock.patch('builtins.open', mock.mock_open(
        read_data='VERSION_CODENAME=bullseye\n'))
    def test_get_debian_codename(self):
        self.utils.get_debian_codename.cache_clear()
        self.assertEqual(self.utils.get_debian_codename(), 'bullseye')

    @mock.patch('builtins.open', side_effect=FileNotFoundError)
    def test_get_debian_codename_missing(self, _):
        self.utils.get_debian_codename.cache_clear()
        self.assertIsNone(self.utils.get_debian_codename())


class TestFmCommonConstants(unittest.TestCase):
    """Test fm.common.constants module."""

    def test_constants(self):
        from fm.common import constants
        self.assertEqual(constants.FM_SUPPRESSED, 'suppressed')
        self.assertEqual(constants.FM_UNSUPPRESSED, 'unsuppressed')
        self.assertEqual(constants.DB_SUPPRESS_STATUS, 1)
        self.assertEqual(constants.OS_DEBIAN_BULLSEYE, 'bullseye')


class TestApiHooks(unittest.TestCase):
    """Test fm.api.hooks module."""

    def test_generate_request_id(self):
        from fm.api import hooks
        self.assertTrue(hooks.generate_request_id().startswith('req-'))

    def test_db_hook_before(self):
        from fm.api import hooks
        hook = hooks.DBHook()
        state = mock.MagicMock()
        hook.before(state)
        self.assertTrue(hasattr(state.request, 'dbapi'))

    def test_audit_logging_methods(self):
        from fm.api import hooks
        al = hooks.AuditLogging()
        self.assertEqual(
            al.log_methods, ["POST", "PUT", "PATCH", "DELETE"])
        al.before(mock.MagicMock())
        al.on_error(mock.MagicMock(), Exception("test"))

    def test_audit_logging_after(self):
        from fm.api import hooks
        al = hooks.AuditLogging()
        for method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            al.after(make_audit_state(method))
        # Non-log method
        state = make_audit_state('GET')
        state.request.method = 'GET'
        al.after(state)

    def test_access_policy_hook_public(self):
        from fm.api import hooks
        hook = hooks.AccessPolicyHook()
        state = mock.MagicMock()
        state.request.environ = {'is_public_api': True}
        hook.before(state)

    def test_access_policy_hook_enforce(self):
        from fm.api import hooks
        hook = hooks.AccessPolicyHook()
        state = mock.MagicMock()
        state.request.environ = {'is_public_api': False}
        ctrl = mock.MagicMock()
        ctrl.enforce_policy = mock.MagicMock()
        state.controller.__self__ = ctrl
        state.controller.__name__ = 'get'
        hook.before(state)

    def test_access_policy_hook_no_enforce(self):
        from fm.api import hooks
        import webob.exc
        hook = hooks.AccessPolicyHook()
        state = mock.MagicMock()
        state.request.environ = {'is_public_api': False}
        state.controller.__self__ = mock.MagicMock(spec=[])
        with self.assertRaises(webob.exc.HTTPForbidden):
            hook.before(state)


class TestApiMiddleware(unittest.TestCase):
    """Test fm.api.middleware modules."""

    def test_parsable_error_middleware(self):
        from fm.api.middleware.parsable_error \
            import ParsableErrorMiddleware

        def ok_app(environ, start_response):
            start_response('200 OK',
                           [('Content-Type', 'application/json')])
            return [b'{"result": "ok"}']

        mw = ParsableErrorMiddleware(ok_app)
        result = mw({'HTTP_ACCEPT': 'application/json'},
                    mock.MagicMock())
        self.assertIsNotNone(result)

    def test_parsable_error_middleware_error(self):
        from fm.api.middleware.parsable_error \
            import ParsableErrorMiddleware

        def err_app(environ, start_response):
            start_response('404 Not Found',
                           [('Content-Type', 'text/plain'),
                            ('Content-Length', '9')])
            return [b'Not Found']

        mw = ParsableErrorMiddleware(err_app)
        result = mw({'HTTP_ACCEPT': 'application/json'},
                    mock.MagicMock())
        self.assertIsNotNone(result)

    def test_parsable_error_no_accept(self):
        from fm.api.middleware.parsable_error \
            import ParsableErrorMiddleware

        def app(environ, start_response):
            start_response('200 OK', [])
            return [b'ok']

        mw = ParsableErrorMiddleware(app)
        environ = {}
        mw(environ, mock.MagicMock())
        self.assertEqual(environ['HTTP_ACCEPT'], 'application/json')

    def test_auth_token_factory(self):
        from fm.api.middleware.auth_token import AuthTokenMiddleware
        factory = AuthTokenMiddleware.factory(
            {}, acl_public_routes='/v1,/healthcheck')
        self.assertTrue(callable(factory))


class TestApiConfig(unittest.TestCase):
    """Test fm.api.config module."""

    def test_app_config(self):
        from fm.api import config
        self.assertIn('root', config.app)
        self.assertTrue(config.app['enable_acl'])
        self.assertTrue(len(config.sysinv_opts) > 0)

    def test_get_max_event_log(self):
        from fm.api import config
        from oslo_config import cfg
        try:
            cfg.CONF.register_opt(
                cfg.StrOpt('event_log_max_size', default='4000'))
        except cfg.DuplicateOptError:
            pass
        self.assertIsNotNone(config.get_max_event_log())


class TestApiApp(unittest.TestCase):
    """Test fm.api.app module."""

    def test_get_pecan_config(self):
        from fm.api import app
        self.assertIsNotNone(app.get_pecan_config())

    def test_app_factory(self):
        from fm.api import app
        with mock.patch.object(app, 'setup_app') as m:
            m.return_value = mock.MagicMock()
            app.app_factory({})
            m.assert_called_once()

    def test_serve_twice_raises(self):
        from fm.api import app
        app._launcher = mock.MagicMock()
        with self.assertRaises(RuntimeError):
            app.serve(mock.MagicMock(), mock.MagicMock())
        app._launcher = None

    def test_serve_and_wait(self):
        from fm.api import app
        app._launcher = None
        with mock.patch('oslo_service.service.launch') as ml:
            ml.return_value = mock.MagicMock()
            app.serve(mock.MagicMock(), mock.MagicMock(), workers=1)
            app.wait()
        app._launcher = None

    @mock.patch('oslo_service.wsgi.Loader')
    def test_load_paste_app(self, ml):
        from fm.api import app
        ml.return_value.load_app.return_value = mock.MagicMock()
        self.assertIsNotNone(app.load_paste_app('fm'))


class TestApiControllers(BaseControllerTestCase):
    """Test fm.api.controllers.v1 modules."""

    def test_base_version(self):
        from fm.api.controllers.v1 import base
        v = base.Version({}, '1.0', '1.1')
        self.assertEqual(repr(v), '1.0')
        self.assertIsInstance(hash(v), int)
        self.assertEqual(v, base.Version({}, '1.0', '1.1'))

    def test_version_parse_headers(self):
        from fm.api.controllers.v1 import base
        import webob.exc
        h = {}
        self.assertEqual(
            base.Version.parse_headers(h, '1.0', '1.0'), (1, 0))
        h = {base.Version.string: 'latest'}
        self.assertEqual(
            base.Version.parse_headers(h, '1.0', '1.1'), (1, 1))
        h = {base.Version.string: 'invalid'}
        with self.assertRaises(webob.exc.HTTPNotAcceptable):
            base.Version.parse_headers(h, '1.0', '1.1')

    @mock.patch('pecan.request')
    def test_link_build_url(self, mr):
        mr.public_url = 'http://localhost:18002'
        from fm.api.controllers.v1 import link
        url = link.build_url('alarms', 'uuid-1',
                             base_url='http://h:18002')
        self.assertIn('alarms', url)

    def test_collection_has_next(self):
        from fm.api.controllers.v1 import collection
        c = collection.Collection()
        c._type = 'items'
        c.items = [1, 2, 3]
        self.assertTrue(c.has_next(3))
        c.items = [1, 2]
        self.assertFalse(c.has_next(3))

    def test_query(self):
        from fm.api.controllers.v1 import query
        q = query.Query()
        self.assertEqual(q.get_op(), 'eq')
        q.set_op('ne')
        self.assertEqual(q.get_op(), 'ne')
        q.field = 'severity'
        q.value = 'critical'
        q.type = 'string'
        self.assertIn('severity', repr(q))
        self.assertIsInstance(q.as_dict(), dict)

    def test_query_get_value_as_type(self):
        from fm.api.controllers.v1 import query
        import wsme.exc
        q = query.Query()
        q.value = '42'
        q.type = 'integer'
        self.assertEqual(q._get_value_as_type(), 42)
        q.type = 'float'
        q.value = '3.14'
        self.assertAlmostEqual(q._get_value_as_type(), 3.14)
        q.type = 'unsupported'
        with self.assertRaises(wsme.exc.ClientSideError):
            q._get_value_as_type()

    def test_types(self):
        from fm.api.controllers.v1 import types
        from fm.common import exceptions
        self.assertIsNotNone(types.UuidType.validate(TEST_UUID))
        with self.assertRaises(exceptions.Invalid):
            types.UuidType.validate('not-a-uuid')
        self.assertTrue(types.BooleanType.validate('true'))
        self.assertFalse(types.BooleanType.validate('false'))
        with self.assertRaises(exceptions.Invalid):
            types.BooleanType.validate('maybe')
        self.assertEqual(
            types.JsonType.validate({'k': 'v'}), {'k': 'v'})

    def test_utils(self):
        from fm.api.controllers.v1 import utils
        from oslo_config import cfg
        import wsme.exc
        try:
            cfg.CONF.register_group(cfg.OptGroup('api'))
        except cfg.DuplicateOptError:
            pass
        try:
            cfg.CONF.register_opt(
                cfg.IntOpt('limit_max', default=1000), group='api')
        except cfg.DuplicateOptError:
            pass
        self.assertEqual(utils.validate_limit(10), 10)
        with self.assertRaises(wsme.exc.ClientSideError):
            utils.validate_limit(-1)
        self.assertEqual(utils.validate_sort_dir('asc'), 'asc')
        with self.assertRaises(wsme.exc.ClientSideError):
            utils.validate_sort_dir('invalid')

    @mock.patch('pecan.request')
    def test_alarm_convert(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import alarm as ac
        result = ac.Alarm.convert_with_links(self._alarm_rpc())
        self.assertEqual(result.alarm_id, TEST_ALARM_ID)

    @mock.patch('pecan.request')
    def test_alarm_controller_summary(self, mr):
        from fm.api.controllers.v1 import alarm as ac
        mr.host_url = 'http://h:18002'
        mr.dbapi = mock.MagicMock()
        mr.dbapi.alarm_get_all.return_value = []
        ctrl = ac.AlarmController()
        result = ac.AlarmController.summary.__wrapped__(ctrl)
        self.assertIsNotNone(result)

    def test_alarm_controller_enforce_policy(self):
        from fm.api.controllers.v1 import alarm as ac
        ctrl = ac.AlarmController()
        with mock.patch('fm.common.policy.authorize'):
            ctrl.enforce_policy('get_one', mock.MagicMock())

    @mock.patch('pecan.request')
    def test_event_log_controller_get_all(self, mr):
        from fm.api.controllers.v1 import event_log as ec
        mr.host_url = 'http://h:18002'
        mr.dbapi = mock.MagicMock()
        mr.dbapi.event_log_get_all.return_value = [self._elog_rpc()]
        ctrl = ec.EventLogController()
        result = ec.EventLogController.get_all.__wrapped__(
            ctrl, limit=100, sort_key='id', sort_dir='asc')
        self.assertIsNotNone(result)

    def test_event_log_enforce_policy(self):
        from fm.api.controllers.v1 import event_log as ec
        ctrl = ec.EventLogController()
        with mock.patch('fm.common.policy.authorize'):
            ctrl.enforce_policy('get_one', mock.MagicMock())

    def test_event_suppression_enforce_policy(self):
        from fm.api.controllers.v1 import event_suppression as esc
        ctrl = esc.EventSuppressionController()
        with mock.patch('fm.common.policy.authorize'):
            ctrl.enforce_policy('get_one', mock.MagicMock())

    def test_root_controller(self):
        from fm.api.controllers import root
        self.assertIn('v1', root.RootController._versions)
        with mock.patch('pecan.request') as mr:
            mr.host_url = 'http://localhost:18002'
            r = root.Root.convert()
            self.assertEqual(r.name, "Fault Management API")


class TestCmdApi(unittest.TestCase):
    """Test fm.cmd.api module."""

    def test_resolve_host_once(self):
        from fm.cmd import api as cmd_api
        if hasattr(cmd_api, '_resolve_host_once'):
            with mock.patch('subprocess.run') as mr:
                mr.return_value = mock.MagicMock(
                    returncode=0, stdout='10.0.0.1\n', stderr='')
                self.assertEqual(
                    cmd_api._resolve_host_once('host', 'A'), '10.0.0.1')
            with mock.patch('subprocess.run') as mr:
                mr.return_value = mock.MagicMock(
                    returncode=1, stdout='', stderr='err')
                self.assertIsNone(
                    cmd_api._resolve_host_once('host', 'A'))
            with mock.patch('subprocess.run',
                            side_effect=Exception("timeout")):
                self.assertIsNone(
                    cmd_api._resolve_host_once('host', 'A'))


class TestFmCommonPolicy(unittest.TestCase):
    """Test fm.common.policy module."""

    def test_reset_and_init(self):
        from fm.common import policy
        policy.reset()
        self.assertIsNotNone(policy.init())


class TestObjectsBase(unittest.TestCase):
    """Test fm.objects.base module."""

    def test_fm_object(self):
        from fm.objects import base
        obj = base.FmObject()
        obj['test_attr'] = 'val'
        self.assertEqual(obj['test_attr'], 'val')
        self.assertIsInstance(obj.as_dict(), dict)


if __name__ == '__main__':
    unittest.main()
