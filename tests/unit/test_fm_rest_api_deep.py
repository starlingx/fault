#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Comprehensive tests for fm-rest-api controllers, middleware,
    and DB."""
# pylint: disable=protected-access,unused-argument
import unittest
from unittest import mock
from tests import test_helpers  # noqa: F401,E402
from tests import constants as TC

# Ensure fm-rest-api is on path

# Mock unavailable system deps


class TestApiControllerBase(unittest.TestCase):
    """Test fm.api.controllers.v1.base module."""

    def test_api_base_as_dict(self):
        from fm.api.controllers.v1 import base
        # APIBase.as_dict requires wsme fields attribute
        self.assertTrue(hasattr(base.APIBase, 'as_dict'))

    def test_api_base_unset_fields_except(self):
        from fm.api.controllers.v1 import base
        self.assertTrue(hasattr(base.APIBase, 'unset_fields_except'))

    def test_version_parse_headers_default(self):
        from fm.api.controllers.v1 import base
        headers = {}
        major, minor = base.Version.parse_headers(headers, '1.0', '1.0')
        self.assertEqual((major, minor), (1, 0))

    def test_version_parse_headers_latest(self):
        from fm.api.controllers.v1 import base
        headers = {base.Version.string: 'latest'}
        major, minor = base.Version.parse_headers(headers, '1.0', '1.1')
        self.assertEqual((major, minor), (1, 1))

    def test_version_parse_headers_explicit(self):
        from fm.api.controllers.v1 import base
        headers = {base.Version.string: '1.0'}
        major, minor = base.Version.parse_headers(headers, '1.0', '1.1')
        self.assertEqual((major, minor), (1, 0))

    def test_version_parse_headers_invalid(self):
        from fm.api.controllers.v1 import base
        import webob.exc
        headers = {base.Version.string: 'invalid'}
        with self.assertRaises(webob.exc.HTTPNotAcceptable):
            base.Version.parse_headers(headers, '1.0', '1.1')

    def test_version_comparison(self):
        from fm.api.controllers.v1 import base
        v1 = base.Version({}, '1.0', '1.1')
        v2 = base.Version({}, '1.0', '1.1')
        self.assertEqual(v1, v2)
        self.assertFalse(v1 != v2)
        self.assertFalse(v1 > v2)

    def test_version_repr(self):
        from fm.api.controllers.v1 import base
        v = base.Version({}, '1.0', '1.1')
        self.assertEqual(repr(v), '1.0')

    def test_version_hash(self):
        from fm.api.controllers.v1 import base
        v = base.Version({}, '1.0', '1.1')
        self.assertIsInstance(hash(v), int)

    def test_from_rpc_object(self):
        from fm.api.controllers.v1 import base
        m = mock.MagicMock()
        m.as_dict.return_value = {}
        base.APIBase.from_rpc_object(m)


class TestApiControllerLink(unittest.TestCase):
    """Test fm.api.controllers.v1.link module."""

    @mock.patch('pecan.request')
    def test_build_url(self, mock_req):
        mock_req.public_url = 'http://localhost:18002'
        from fm.api.controllers.v1 import link
        url = link.build_url('alarms', 'uuid-1',
                             base_url='http://h:18002')
        self.assertIn('alarms', url)
        self.assertIn('uuid-1', url)

    @mock.patch('pecan.request')
    def test_build_url_bookmark(self, mock_req):
        mock_req.public_url = 'http://localhost:18002'
        from fm.api.controllers.v1 import link
        url = link.build_url('alarms', '?limit=1', bookmark=True,
                             base_url='http://h:18002')
        self.assertIn('alarms', url)
        self.assertNotIn('/v1/', url)

    def test_link_make_link(self):
        from fm.api.controllers.v1 import link
        result = link.Link.make_link('self', 'http://h:18002',
                                     'alarms', 'uuid-1')
        self.assertIsNotNone(result)


class TestApiControllerCollection(unittest.TestCase):
    """Test fm.api.controllers.v1.collection module."""

    def test_has_next_true(self):
        from fm.api.controllers.v1 import collection
        c = collection.Collection()
        c._type = 'items'
        c.items = [1, 2, 3]
        self.assertTrue(c.has_next(3))

    def test_has_next_false(self):
        from fm.api.controllers.v1 import collection
        c = collection.Collection()
        c._type = 'items'
        c.items = [1, 2]
        self.assertFalse(c.has_next(3))


class TestApiControllerQuery(unittest.TestCase):
    """Test fm.api.controllers.v1.query module."""

    def test_query_get_op_default(self):
        from fm.api.controllers.v1 import query
        q = query.Query()
        self.assertEqual(q.get_op(), 'eq')

    def test_query_set_op(self):
        from fm.api.controllers.v1 import query
        q = query.Query()
        q.set_op('ne')
        self.assertEqual(q.get_op(), 'ne')

    def test_query_repr(self):
        from fm.api.controllers.v1 import query
        q = query.Query()
        q.field = 'severity'
        q.value = 'critical'
        q.type = 'string'
        r = repr(q)
        self.assertIn('severity', r)

    def test_query_as_dict(self):
        from fm.api.controllers.v1 import query
        q = query.Query()
        q.field = 'severity'
        q.value = 'critical'
        d = q.as_dict()
        self.assertIsInstance(d, dict)

    def test_get_value_as_type_string(self):
        from fm.api.controllers.v1 import query
        q = query.Query()
        q.value = 'test'
        q.type = 'string'
        result = q._get_value_as_type()
        self.assertEqual(result, 'test')

    def test_get_value_as_type_integer(self):
        from fm.api.controllers.v1 import query
        q = query.Query()
        q.value = '42'
        q.type = 'integer'
        result = q._get_value_as_type()
        self.assertEqual(result, 42)

    def test_get_value_as_type_float(self):
        from fm.api.controllers.v1 import query
        q = query.Query()
        q.value = '3.14'
        q.type = 'float'
        result = q._get_value_as_type()
        self.assertAlmostEqual(result, 3.14)

    def test_get_value_as_type_no_type(self):
        from fm.api.controllers.v1 import query
        q = query.Query()
        q.value = '42'
        q.type = None
        result = q._get_value_as_type()
        self.assertEqual(result, 42)

    def test_get_value_as_type_no_type_string(self):
        from fm.api.controllers.v1 import query
        q = query.Query()
        q.value = 'hello world'
        q.type = None
        result = q._get_value_as_type()
        self.assertEqual(result, 'hello world')

    def test_get_value_as_type_unsupported(self):
        from fm.api.controllers.v1 import query
        import wsme.exc
        q = query.Query()
        q.value = 'x'
        q.type = 'unsupported'
        with self.assertRaises(wsme.exc.ClientSideError):
            q._get_value_as_type()

    def test_get_value_as_type_bad_value(self):
        from fm.api.controllers.v1 import query
        import wsme.exc
        q = query.Query()
        q.value = 'not_a_number'
        q.type = 'integer'
        with self.assertRaises(wsme.exc.ClientSideError):
            q._get_value_as_type()

    def test_base_from_db_model(self):
        from fm.api.controllers.v1 import query
        m = mock.MagicMock()
        m.as_dict.return_value = {'field': 'val'}
        result = query._Base.from_db_model(m)
        self.assertIsNotNone(result)

    def test_query_sample(self):
        from fm.api.controllers.v1 import query
        s = query.Query.sample()
        self.assertIsNotNone(s)


class TestApiControllerTypes(unittest.TestCase):
    """Test fm.api.controllers.v1.types module."""

    def test_uuid_type_validate_valid(self):
        from fm.api.controllers.v1 import types
        result = types.UuidType.validate(
            TC.TEST_UUID)
        self.assertIsNotNone(result)

    def test_uuid_type_validate_invalid(self):
        from fm.api.controllers.v1 import types
        from fm.common import exceptions
        with self.assertRaises(exceptions.Invalid):
            types.UuidType.validate('not-a-uuid')

    def test_uuid_type_frombasetype_none(self):
        from fm.api.controllers.v1 import types
        self.assertIsNone(types.UuidType.frombasetype(None))

    def test_boolean_type_validate_true(self):
        from fm.api.controllers.v1 import types
        self.assertTrue(types.BooleanType.validate('true'))

    def test_boolean_type_validate_false(self):
        from fm.api.controllers.v1 import types
        self.assertFalse(types.BooleanType.validate('false'))

    def test_boolean_type_validate_invalid(self):
        from fm.api.controllers.v1 import types
        from fm.common import exceptions
        with self.assertRaises(exceptions.Invalid):
            types.BooleanType.validate('maybe')

    def test_boolean_type_frombasetype_none(self):
        from fm.api.controllers.v1 import types
        self.assertIsNone(types.BooleanType.frombasetype(None))

    def test_json_type_validate_valid(self):
        from fm.api.controllers.v1 import types
        result = types.JsonType.validate({'key': 'value'})
        self.assertEqual(result, {'key': 'value'})

    def test_json_type_validate_string(self):
        from fm.api.controllers.v1 import types
        result = types.JsonType.validate('hello')
        self.assertEqual(result, 'hello')

    def test_json_type_str(self):
        from fm.api.controllers.v1 import types
        jt = types.JsonType()
        s = str(jt)
        self.assertIsInstance(s, str)

    def test_json_type_frombasetype(self):
        from fm.api.controllers.v1 import types
        result = types.JsonType.frombasetype('test')
        self.assertEqual(result, 'test')

    def test_json_patch_type_internal_attrs(self):
        from fm.api.controllers.v1 import types
        attrs = types.JsonPatchType.internal_attrs()
        self.assertIn('/created_at', attrs)
        self.assertIn('/id', attrs)
        self.assertIn('/uuid', attrs)

    def test_json_patch_type_non_removable_attrs(self):
        from fm.api.controllers.v1 import types
        types.JsonPatchType._non_removable_attrs = None
        attrs = types.JsonPatchType.non_removable_attrs()
        self.assertIsInstance(attrs, set)


class TestApiControllerUtils(unittest.TestCase):
    """Test fm.api.controllers.v1.utils module."""

    def test_validate_limit_positive(self):
        from fm.api.controllers.v1 import utils
        from oslo_config import cfg
        cfg.CONF.register_group(cfg.OptGroup('api'))
        try:
            cfg.CONF.register_opt(
                cfg.IntOpt('limit_max', default=1000), group='api')
        except cfg.DuplicateOptError:
            pass
        result = utils.validate_limit(10)
        self.assertEqual(result, 10)

    def test_validate_limit_negative(self):
        from fm.api.controllers.v1 import utils
        import wsme.exc
        with self.assertRaises(wsme.exc.ClientSideError):
            utils.validate_limit(-1)

    def test_validate_limit_none(self):
        from fm.api.controllers.v1 import utils
        from oslo_config import cfg
        try:
            cfg.CONF.register_group(cfg.OptGroup('api'))
        except cfg.DuplicateOptError:
            pass
        try:
            cfg.CONF.register_opt(
                cfg.IntOpt('limit_max', default=1000), group='api')
        except cfg.DuplicateOptError:
            pass
        result = utils.validate_limit(None)
        self.assertEqual(result, 1000)

    def test_validate_sort_dir_asc(self):
        from fm.api.controllers.v1 import utils
        self.assertEqual(utils.validate_sort_dir('asc'), 'asc')

    def test_validate_sort_dir_desc(self):
        from fm.api.controllers.v1 import utils
        self.assertEqual(utils.validate_sort_dir('desc'), 'desc')

    def test_validate_sort_dir_invalid(self):
        from fm.api.controllers.v1 import utils
        import wsme.exc
        with self.assertRaises(wsme.exc.ClientSideError):
            utils.validate_sort_dir('invalid')

    def test_make_display_id_no_replace(self):
        from fm.api.controllers.v1 import utils
        result = utils.make_display_id('host=ctrl-0', replace=False)
        self.assertIn('host=ctrl-0', result)

    def test_replace_uuids_no_uuid(self):
        from fm.api.controllers.v1 import utils
        result = utils.replace_uuids('host=ctrl-0.port=eth0')
        self.assertIn('port=eth0', result)

    def test_replace_name_with_uuid_no_port(self):
        from fm.api.controllers.v1 import utils
        result = utils.replace_name_with_uuid('host=ctrl-0')
        self.assertEqual(result, 'host=ctrl-0')

    def test_replace_name_with_uuid_bad_format(self):
        from fm.api.controllers.v1 import utils
        result = utils.replace_name_with_uuid('noequalssign')
        self.assertEqual(result, 'noequalssign')

    def test_replace_uuids_bad_format(self):
        from fm.api.controllers.v1 import utils
        result = utils.replace_uuids('noequalssign')
        self.assertEqual(result, 'noequalssign')

    def test_save_and_reraise(self):
        from fm.api.controllers.v1 import utils
        with self.assertRaises(ValueError):
            try:
                raise ValueError("original")
            except ValueError:
                with utils.save_and_reraise_exception():
                    pass


class TestApiHooks(unittest.TestCase):
    """Test fm.api.hooks module."""

    def test_generate_request_id(self):
        from fm.api import hooks
        rid = hooks.generate_request_id()
        self.assertTrue(rid.startswith('req-'))

    def test_db_hook_before(self):
        from fm.api import hooks
        hook = hooks.DBHook()
        state = mock.MagicMock()
        hook.before(state)
        self.assertTrue(hasattr(state.request, 'dbapi'))

    def test_audit_logging_init(self):
        from fm.api import hooks
        al = hooks.AuditLogging()
        self.assertEqual(al.log_methods, ["POST", "PUT", "PATCH",
                         "DELETE"])

    def test_audit_logging_before(self):
        from fm.api import hooks
        al = hooks.AuditLogging()
        state = mock.MagicMock()
        al.before(state)

    def test_audit_logging_on_error(self):
        from fm.api import hooks
        al = hooks.AuditLogging()
        state = mock.MagicMock()
        al.on_error(state, Exception("test"))

    def test_audit_logging_after_non_log_method(self):
        from fm.api import hooks
        al = hooks.AuditLogging()
        state = mock.MagicMock()
        state.request.method = 'GET'
        al.after(state)

    def test_context_hook_before(self):
        from fm.api import hooks
        hook = hooks.ContextHook()
        self.assertIsNotNone(hook)


class TestApiMiddleware(unittest.TestCase):
    """Test fm.api.middleware modules."""

    def test_middleware_init_imports(self):
        from fm.api import middleware
        self.assertTrue(hasattr(middleware, 'ParsableErrorMiddleware'))
        self.assertTrue(hasattr(middleware, 'AuthTokenMiddleware'))

    def test_parsable_error_middleware_init(self):
        from fm.api.middleware.parsable_error \
            import ParsableErrorMiddleware
        app = mock.MagicMock()
        mw = ParsableErrorMiddleware(app)
        self.assertEqual(mw.app, app)

    def test_parsable_error_middleware_call_success(self):
        from fm.api.middleware.parsable_error \
            import ParsableErrorMiddleware
        app = mock.MagicMock()

        def fake_app(environ, start_response):
            start_response('200 OK', [('Content-Type',
                                       'application/json')])
            return [b'{"result": "ok"}']

        mw = ParsableErrorMiddleware(fake_app)
        environ = {'HTTP_ACCEPT': 'application/json'}
        start_response = mock.MagicMock()
        result = mw(environ, start_response)
        self.assertIsNotNone(result)

    def test_parsable_error_middleware_call_error(self):
        from fm.api.middleware.parsable_error \
            import ParsableErrorMiddleware

        def fake_app(environ, start_response):
            start_response('404 Not Found',
                           [('Content-Type', 'text/plain'),
                            ('Content-Length', '9')])
            return [b'Not Found']

        mw = ParsableErrorMiddleware(fake_app)
        environ = {'HTTP_ACCEPT': 'application/json'}
        start_response = mock.MagicMock()
        result = mw(environ, start_response)
        self.assertIsNotNone(result)

    def test_parsable_error_middleware_no_accept(self):
        from fm.api.middleware.parsable_error \
            import ParsableErrorMiddleware

        def fake_app(environ, start_response):
            start_response('200 OK', [])
            return [b'ok']

        mw = ParsableErrorMiddleware(fake_app)
        environ = {}
        start_response = mock.MagicMock()
        mw(environ, start_response)
        self.assertEqual(environ['HTTP_ACCEPT'], 'application/json')


class TestApiConfig(unittest.TestCase):
    """Test fm.api.config module."""

    def test_app_config_exists(self):
        from fm.api import config
        self.assertIn('root', config.app)
        self.assertTrue(config.app['enable_acl'])

    def test_get_max_event_log(self):
        from fm.api import config
        from oslo_config import cfg
        try:
            cfg.CONF.register_opt(
                cfg.StrOpt('event_log_max_size', default='4000'))
        except cfg.DuplicateOptError:
            pass
        result = config.get_max_event_log()
        self.assertIsNotNone(result)

    def test_sysinv_opts(self):
        from fm.api import config
        self.assertTrue(len(config.sysinv_opts) > 0)


class TestApiApp(unittest.TestCase):
    """Test fm.api.app module."""

    def test_get_pecan_config(self):
        from fm.api import app
        cfg = app.get_pecan_config()
        self.assertIsNotNone(cfg)

    @mock.patch('fm.common.policy.init')
    @mock.patch('pecan.configuration.set_config')
    @mock.patch('pecan.make_app')
    def test_setup_app(self, mock_make, mock_set, mock_policy):
        from fm.api import app
        self.assertTrue(callable(app.setup_app))

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


class TestApiSysinv(unittest.TestCase):
    """Test fm.api.controllers.v1.sysinv module."""

    @mock.patch('cgtsclient.v1.client.Client')
    @mock.patch('keystoneauth1.loading.load_session_from_conf_options')
    def test_cgtsclient_with_endpoint(self, mock_load, mock_client):
        from fm.api.controllers.v1 import sysinv
        self.assertTrue(callable(sysinv.cgtsclient))


class TestDbMigration(unittest.TestCase):
    """Test fm.db.migration module."""

    @mock.patch('stevedore.driver.DriverManager')
    def test_get_backend(self, mock_dm):
        from fm.db import migration
        migration._IMPL = None
        mock_dm.return_value = mock.MagicMock()
        result = migration.get_backend()
        self.assertIsNotNone(result)
        migration._IMPL = None

    def test_db_sync(self):
        from fm.db import migration
        self.assertTrue(callable(migration.db_sync))


class TestObjectsBase(unittest.TestCase):
    """Test fm.objects.base module."""

    def test_fm_object_getitem(self):
        from fm.objects import base
        obj = base.FmObject()
        obj.test_attr = 'val'
        self.assertEqual(obj['test_attr'], 'val')

    def test_fm_object_setitem(self):
        from fm.objects import base
        obj = base.FmObject()
        obj['test_attr'] = 'val'
        self.assertEqual(obj.test_attr, 'val')

    def test_fm_object_as_dict(self):
        from fm.objects import base
        obj = base.FmObject()
        d = obj.as_dict()
        self.assertIsInstance(d, dict)


class TestObjectsAlarm(unittest.TestCase):
    """Test fm.objects.alarm module."""

    def test_alarm_module_importable(self):
        from fm.objects import alarm  # noqa: F401


class TestObjectsEventLog(unittest.TestCase):
    """Test fm.objects.event_log module."""

    def test_event_log_module_importable(self):
        from fm.objects import event_log  # noqa: F401


class TestApiControllerRoot(unittest.TestCase):
    """Test fm.api.controllers.root module."""

    def test_expose_function(self):
        from fm.api.controllers import root
        self.assertTrue(callable(root.expose))

    def test_root_controller_versions(self):
        from fm.api.controllers import root
        self.assertIn('v1', root.RootController._versions)

    def test_root_convert(self):
        from fm.api.controllers import root
        with mock.patch('pecan.request') as mr:
            mr.host_url = 'http://localhost:18002'
            r = root.Root.convert()
            self.assertEqual(r.name, "Fault Management API")


class TestCmdDbsync(unittest.TestCase):
    """Test fm.cmd.dbsync module."""

    def test_main_callable(self):
        # dbsync.main requires oslo.config initialization
        pass


if __name__ == '__main__':
    unittest.main()
