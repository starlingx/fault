#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Cover controllers, hooks, middleware, app,
    cmd by bypassing decorators."""
import re
import time
import unittest
from unittest import mock

from fm.api import hooks  # noqa: E402
from fm.api.middleware import auth_token as auth_mod  # noqa: E402
from tests import test_helpers  # noqa: F401,E402
from tests import constants as TC


class TestHooksCover(unittest.TestCase):
    """Cover every line in hooks.py."""

    def _make_state(self, method='POST'):
        state = mock.MagicMock()
        state.request.method = method
        state.request.start_time = time.time()
        state.request.environ = {'SERVER_PROTOCOL': 'HTTP/1.1'}
        state.request.path_qs = '/v1/alarms'
        state.request.remote_addr = '127.0.0.1'
        state.request.host = 'localhost'
        state.request.user_agent = 'test'
        state.request.context.request_id = 'req-1'
        state.request.params = {}
        state.request.headers = mock.MagicMock()
        state.request.headers.get = mock.MagicMock(
            side_effect=lambda k, d=None: {
                'X-User-Id': 'uid', 'X-User': 'admin',
                'X-Tenant-Id': 'tid', 'X-Tenant': 'admin',
                'X-User-Domain-Name': 'Default',
                'Content-Type': 'application/json',
            }.get(k, d))
        state.response.status_int = 200
        state.response.content_length = 42
        state.request.json = {'key': 'val'}
        return state

    def test_audit_post(self):
        al = hooks.AuditLogging()
        al.after(self._make_state('POST'))

    def test_audit_put(self):
        al = hooks.AuditLogging()
        al.after(self._make_state('PUT'))

    def test_audit_patch(self):
        al = hooks.AuditLogging()
        al.after(self._make_state('PATCH'))

    def test_audit_delete(self):
        al = hooks.AuditLogging()
        al.after(self._make_state('DELETE'))

    def test_audit_no_start_time(self):
        al = hooks.AuditLogging()
        state = self._make_state('POST')
        del state.request.start_time
        al.after(state)

    def test_audit_no_request_id(self):
        al = hooks.AuditLogging()
        state = self._make_state('POST')
        type(state.request).context = mock.PropertyMock(
            side_effect=AttributeError)
        al.after(state)

    def test_audit_form_data(self):
        al = hooks.AuditLogging()
        state = self._make_state('POST')
        state.request.headers.get = mock.MagicMock(
            side_effect=lambda k, d=None: {
                'Content-Type': 'multipart/form-data',
                'X-User-Id': 'uid', 'X-Tenant-Id': 'tid',
                'X-User-Domain-Name': 'D',
            }.get(k, d))
        al.after(state)

    def test_access_policy_enforce_exception(self):
        import webob.exc
        hook = hooks.AccessPolicyHook()
        state = mock.MagicMock()
        state.request.environ = {'is_public_api': False}
        ctrl = mock.MagicMock()
        ctrl.enforce_policy.side_effect = Exception("denied")
        state.controller.__self__ = ctrl
        state.controller.__name__ = 'get'
        with self.assertRaises(webob.exc.HTTPForbidden):
            hook.before(state)


class TestAuthTokenCover(unittest.TestCase):
    """Cover auth_token.py."""

    def test_call_public_route(self):
        app = mock.MagicMock()
        app.return_value = [b'ok']
        mw = auth_mod.AuthTokenMiddleware.__new__(
            auth_mod.AuthTokenMiddleware)
        mw._app = app
        mw.public_api_routes = [re.compile(r'/v1(\.json)?$')]
        mw.oidc_token_cache = {}
        mw.oidc_auth_params = None
        env = {'PATH_INFO': '/v1'}
        sr = mock.MagicMock()
        result = mw(env, sr)
        app.assert_called_once()

    def test_init_bad_regex(self):
        from fm.common import exceptions
        with self.assertRaises(exceptions.ConfigInvalid):
            auth_mod.AuthTokenMiddleware(
                mock.MagicMock(), {}, public_api_routes=['[invalid'])


class TestCmdApiCover(unittest.TestCase):
    """Cover cmd/api.py."""

    def test_resolve_host_once_success(self):
        from fm.cmd import api
        with mock.patch('subprocess.run') as mr:
            mr.return_value = mock.MagicMock(
                returncode=0, stdout='10.0.0.1\n', stderr='')
            r = api._resolve_host_once('host.internal', 'A')
            self.assertEqual(r, '10.0.0.1')

    def test_resolve_host_once_ipv6(self):
        from fm.cmd import api
        with mock.patch('subprocess.run') as mr:
            mr.return_value = mock.MagicMock(
                returncode=0, stdout='fd00::1\n', stderr='')
            r = api._resolve_host_once('host.internal', 'AAAA')
            self.assertEqual(r, 'fd00::1')

    def test_resolve_host_once_no_result(self):
        from fm.cmd import api
        with mock.patch('subprocess.run') as mr:
            mr.return_value = mock.MagicMock(
                returncode=0, stdout='\n', stderr='')
            r = api._resolve_host_once('host.internal', 'A')
            self.assertIsNone(r)

    def test_resolve_host_once_error(self):
        from fm.cmd import api
        with mock.patch('subprocess.run') as mr:
            mr.return_value = mock.MagicMock(
                returncode=1, stdout='', stderr='err')
            r = api._resolve_host_once('host.internal', 'A')
            self.assertIsNone(r)

    def test_resolve_host_once_exception(self):
        from fm.cmd import api
        with mock.patch('subprocess.run', side_effect=OSError("no")):
            r = api._resolve_host_once('host.internal', 'A')
            self.assertIsNone(r)

    def test_wait_not_internal(self):
        from fm.cmd import api
        api._wait_for_host_dns_resolution('localhost')

    def test_wait_resolves(self):
        from fm.cmd import api
        with mock.patch.object(api, '_resolve_host_once',
                               return_value='10.0.0.1'):
            api._wait_for_host_dns_resolution(
                'ctrl.internal', retries=1)

    def test_wait_fails(self):
        from fm.cmd import api
        with mock.patch.object(api, '_resolve_host_once',
                               return_value=None):
            with mock.patch('eventlet.sleep'):
                api._wait_for_host_dns_resolution(
                    'ctrl.internal', retries=2)


class TestControllerUtilsCover(unittest.TestCase):
    """Cover api/controllers/v1/utils.py."""

    def test_replace_name_with_uuid_port(self):
        from fm.api.controllers.v1 import utils
        with mock.patch.object(utils, '_get_port') as mgp:
            port = mock.MagicMock()
            port.uuid = 'port-uuid-1'
            mgp.return_value = port
            r = utils.replace_name_with_uuid('host=ctrl-0.port=eth0')
            self.assertIn('port-uuid-1', r)

    def test_replace_name_with_uuid_port_not_found(self):
        from fm.api.controllers.v1 import utils
        from fm.common import exceptions
        with mock.patch.object(utils, '_get_port',
                               side_effect=exceptions.NodeNotFound(
                                   node='ctrl-0')):
            r = utils.replace_name_with_uuid('host=ctrl-0.port=eth0')
            self.assertIn('eth0', r)

    def test_replace_name_with_uuid_server_not_found(self):
        from fm.api.controllers.v1 import utils
        from fm.common import exceptions
        with mock.patch.object(utils, '_get_port',
                               side_effect=exceptions.ServerNotFound(
                                   server='eth0')):
            r = utils.replace_name_with_uuid('host=ctrl-0.port=eth0')
            self.assertIn('eth0', r)

    def test_replace_uuid_with_name_port(self):
        from fm.api.controllers.v1 import utils
        port = mock.MagicMock()
        port.name = 'eth0'
        with mock.patch('pecan.request') as mr:
            with mock.patch.object(utils, 'cgtsclient') as mc:
                mc.return_value.port.get.return_value = port
                r = utils.replace_uuid_with_name(
                    'port', TC.TEST_UUID)
                self.assertIn('eth0', r)

    def test_replace_uuid_with_name_not_found(self):
        from fm.api.controllers.v1 import utils
        from fm.common import exceptions
        with mock.patch('pecan.request') as mr:
            with mock.patch.object(utils, 'cgtsclient') as mc:
                mc.return_value.port.get.side_effect = (
                    exceptions.ServerNotFound(server='x'))
                r = utils.replace_uuid_with_name('port', 'uuid-1')
                self.assertIsNone(r)

    def test_replace_uuids_with_uuid(self):
        from fm.api.controllers.v1 import utils
        port = mock.MagicMock()
        port.name = 'eth0'
        with mock.patch('pecan.request') as mr:
            with mock.patch.object(utils, 'cgtsclient') as mc:
                mc.return_value.port.get.return_value = port
                r = utils.replace_uuids(
                    'host=c.port=a1b2c3d4-e5f6-7890-abcd-ef1234567890')
                self.assertIn('eth0', r)

    def test_get_port(self):
        from fm.api.controllers.v1 import utils
        host = mock.MagicMock()
        host.hostname = 'ctrl-0'
        host.uuid = 'host-uuid'
        port = mock.MagicMock()
        port.name = 'eth0'
        with mock.patch('pecan.request') as mr:
            with mock.patch.object(utils, 'cgtsclient') as mc:
                mc.return_value.ihost.list.return_value = [host]
                mc.return_value.port.list.return_value = [port]
                r = utils._get_port('ctrl-0', 'eth0')
                self.assertEqual(r, port)

    def test_get_port_not_found(self):
        from fm.api.controllers.v1 import utils
        with mock.patch('pecan.request') as mr:
            with mock.patch.object(utils, 'cgtsclient') as mc:
                mc.return_value.ihost.list.return_value = []
                r = utils._get_port('ctrl-0', 'eth0')
                self.assertIsNone(r)


if __name__ == '__main__':
    unittest.main()
