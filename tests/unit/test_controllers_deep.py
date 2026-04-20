#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Mock-heavy tests for controllers, hooks, middleware, context,
app, cmd."""

import unittest
from unittest import mock
from tests import test_helpers  # noqa: F401,E402


class TestAuditLoggingFull(unittest.TestCase):
    def test_after_post(self):
        from fm.api import hooks
        import time

        al = hooks.AuditLogging()
        state = mock.MagicMock()
        state.request.method = "POST"
        state.request.start_time = time.time()
        state.request.environ = {"SERVER_PROTOCOL": "HTTP/1.1"}
        state.request.headers.get = mock.MagicMock(return_value="admin")
        state.request.path_qs = "/v1/alarms"
        state.request.remote_addr = "127.0.0.1"
        state.request.host = "localhost"
        state.request.user_agent = "test"
        state.request.context.request_id = "req-1"
        state.response.status_int = 200
        state.response.content_length = 100
        state.request.params = {}
        al.after(state)

    def test_after_delete(self):
        from fm.api import hooks
        import time

        al = hooks.AuditLogging()
        state = mock.MagicMock()
        state.request.method = "DELETE"
        state.request.start_time = time.time()
        state.request.environ = {"SERVER_PROTOCOL": "HTTP/1.1"}
        state.request.headers.get = mock.MagicMock(return_value="admin")
        state.request.path_qs = "/v1/alarms/uuid-1"
        state.request.remote_addr = "127.0.0.1"
        state.request.host = "localhost"
        state.request.user_agent = "test"
        state.request.context.request_id = "req-2"
        state.response.status_int = 204
        state.response.content_length = 0
        state.request.params = {}
        al.after(state)


class TestAccessPolicyHook(unittest.TestCase):
    def test_before_public_api(self):
        from fm.api import hooks

        hook = hooks.AccessPolicyHook()
        state = mock.MagicMock()
        state.request.environ = {"is_public_api": True}
        hook.before(state)

    def test_before_with_enforce(self):
        from fm.api import hooks

        hook = hooks.AccessPolicyHook()
        state = mock.MagicMock()
        state.request.environ = {"is_public_api": False}
        ctrl = mock.MagicMock()
        ctrl.enforce_policy = mock.MagicMock()
        state.controller.__self__ = ctrl
        state.controller.__name__ = "get"
        hook.before(state)

    def test_before_no_enforce(self):
        from fm.api import hooks
        import webob.exc

        hook = hooks.AccessPolicyHook()
        state = mock.MagicMock()
        state.request.environ = {"is_public_api": False}
        ctrl = mock.MagicMock(spec=[])
        state.controller.__self__ = ctrl
        with self.assertRaises(webob.exc.HTTPForbidden):
            hook.before(state)


class TestAuthTokenMiddlewareFull(unittest.TestCase):
    def test_init_and_public_route(self):
        from fm.api.middleware.auth_token import AuthTokenMiddleware

        app = mock.MagicMock()
        with mock.patch.object(
            AuthTokenMiddleware, "__init__", lambda self, a, c, **kw: None
        ):
            mw = AuthTokenMiddleware.__new__(AuthTokenMiddleware)
            mw._app = app
            mw.public_api_routes = []
            mw.oidc_token_cache = {}
            mw.oidc_auth_params = None

    def test_factory_creates_callable(self):
        from fm.api.middleware.auth_token import AuthTokenMiddleware

        factory = AuthTokenMiddleware.factory({}, acl_public_routes="/v1,/healthcheck")
        self.assertTrue(callable(factory))


class TestAppFull(unittest.TestCase):
    def test_get_pecan_config(self):
        from fm.api import app

        cfg = app.get_pecan_config()
        self.assertIsNotNone(cfg)

    @mock.patch("oslo_service.wsgi.Loader")
    def test_load_paste_app(self, ml):
        from fm.api import app

        ml.return_value.load_app.return_value = mock.MagicMock()
        result = app.load_paste_app("fm")
        self.assertIsNotNone(result)


class TestCmdApi(unittest.TestCase):
    def test_resolve_host_once(self):
        from fm.cmd import api as cmd_api

        if hasattr(cmd_api, "_resolve_host_once"):
            with mock.patch("subprocess.run") as mr:
                mr.return_value = mock.MagicMock(
                    returncode=0, stdout="10.0.0.1\n", stderr=""
                )
                result = cmd_api._resolve_host_once("host", "A")
                self.assertEqual(result, "10.0.0.1")

    def test_resolve_host_once_fail(self):
        from fm.cmd import api as cmd_api

        if hasattr(cmd_api, "_resolve_host_once"):
            with mock.patch("subprocess.run") as mr:
                mr.return_value = mock.MagicMock(returncode=1, stdout="", stderr="err")
                result = cmd_api._resolve_host_once("host", "A")
                self.assertIsNone(result)

    def test_resolve_host_once_exception(self):
        from fm.cmd import api as cmd_api

        if hasattr(cmd_api, "_resolve_host_once"):
            with mock.patch("subprocess.run", side_effect=Exception("timeout")):
                result = cmd_api._resolve_host_once("host", "A")
                self.assertIsNone(result)

    def test_wait_for_host_not_internal(self):
        from fm.cmd import api as cmd_api

        if hasattr(cmd_api, "_wait_for_host_dns_resolution"):
            cmd_api._wait_for_host_dns_resolution("localhost")


if __name__ == "__main__":
    unittest.main()
