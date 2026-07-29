#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Final push: cover controllers, hooks, auth_token, http, shell,
    utils."""
import re
import unittest
from unittest import mock
from tests.base import (
    BaseControllerTestCase,
    make_audit_state, make_http_client,
)
from tests import constants as TC


class TestAlarmConvert(BaseControllerTestCase):
    @mock.patch('pecan.request')
    def test_convert(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import alarm as ac
        result = ac.Alarm.convert_with_links(self._alarm_rpc())
        self.assertEqual(result.alarm_id, TC.TEST_ALARM_ID)

    @mock.patch('pecan.request')
    def test_convert_tuple(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import alarm as ac
        result = ac.Alarm.convert_with_links(
            (self._alarm_rpc(), 'unsuppressed', 'warning', 'none'))
        self.assertIsNotNone(result)

    @mock.patch('pecan.request')
    def test_convert_no_expand(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import alarm as ac
        result = ac.Alarm.convert_with_links(
            self._alarm_rpc(), expand=False)
        self.assertIsNotNone(result)

    @mock.patch('pecan.request')
    def test_collection(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import alarm as ac
        c = ac.AlarmCollection.convert_with_links(
            [self._alarm_rpc()], limit=100)
        self.assertEqual(len(c.alarms), 1)

    @mock.patch('pecan.request')
    def test_collection_masked(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import alarm as ac
        c = ac.AlarmCollection.convert_with_links(
            [self._alarm_rpc(masked='True')], limit=100)
        self.assertEqual(len(c.alarms), 0)

    @mock.patch('pecan.request')
    def test_collection_tuple(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import alarm as ac
        r = self._alarm_rpc()
        c = ac.AlarmCollection.convert_with_links(
            [(r, 'unsuppressed', 'warning', 'none')], limit=100)
        self.assertEqual(len(c.alarms), 1)


class TestEventLogConvert(BaseControllerTestCase):
    @mock.patch('pecan.request')
    def test_convert(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import event_log as ec
        result = ec.EventLog.convert_with_links(self._elog_rpc())
        self.assertEqual(result.event_log_id, TC.TEST_ALARM_ID)

    @mock.patch('pecan.request')
    def test_convert_tuple(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import event_log as ec
        result = ec.EventLog.convert_with_links(
            (self._elog_rpc(), 'unsuppressed'))
        self.assertIsNotNone(result)

    @mock.patch('pecan.request')
    def test_convert_no_expand(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import event_log as ec
        result = ec.EventLog.convert_with_links(
            self._elog_rpc(), expand=False)
        self.assertIsNotNone(result)

    @mock.patch('pecan.request')
    def test_collection(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import event_log as ec
        c = ec.EventLogCollection.convert_with_links(
            [self._elog_rpc()], limit=100)
        self.assertIsNotNone(c)

    def test_get_event_type(self):
        from fm.api.controllers.v1 import event_log as ec
        self.assertEqual(ec._getEventType(), "ALL")
        self.assertEqual(ec._getEventType(True, True), "ALL")
        self.assertEqual(ec._getEventType(True, False), "ALARM")
        self.assertEqual(ec._getEventType(False, True), "LOG")


class TestEventSuppConvert(BaseControllerTestCase):
    @mock.patch('pecan.request')
    def test_convert(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import event_suppression as esc
        result = esc.EventSuppression.convert_with_links(
            self._es_rpc())
        self.assertIsNotNone(result)

    @mock.patch('pecan.request')
    def test_collection(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import event_suppression as esc
        c = esc.EventSuppressionCollection.convert_with_links(
            [self._es_rpc()], limit=100)
        self.assertIsNotNone(c)


class TestHooksCoverage(unittest.TestCase):
    from fm.api import hooks

    def test_post(self):
        self.hooks.AuditLogging().after(make_audit_state('POST'))

    def test_delete(self):
        self.hooks.AuditLogging().after(make_audit_state('DELETE'))

    def test_form(self):
        self.hooks.AuditLogging().after(
            make_audit_state('PUT', 'multipart/form-data'))

    def test_no_json(self):
        s = make_audit_state('PATCH')
        del s.request.json
        self.hooks.AuditLogging().after(s)

    def test_no_start(self):
        s = make_audit_state('POST')
        del s.request.start_time
        self.hooks.AuditLogging().after(s)

    def test_no_req_id(self):
        s = make_audit_state('POST')
        type(s.request).context = mock.PropertyMock(
            side_effect=AttributeError)
        self.hooks.AuditLogging().after(s)


class TestAuthTokenCoverage(unittest.TestCase):
    from fm.api.middleware import auth_token as atmod

    def _mw(self):
        mw = self.atmod.AuthTokenMiddleware.__new__(
            self.atmod.AuthTokenMiddleware)
        mw._app = mock.MagicMock(return_value=[b'ok'])
        mw.public_api_routes = [re.compile(r'/v1(\.json)?$')]
        mw.oidc_token_cache = {}
        mw.oidc_auth_params = None
        return mw

    def test_public(self):
        mw = self._mw()
        env = {
            'PATH_INFO': '/v1',
            'is_public_api': False,
            'REQUEST_METHOD': 'GET'}
        mw(env, mock.MagicMock())
        self.assertTrue(env['is_public_api'])

    def test_oidc_no_params(self):
        from platform_util.oidc import oidc_utils
        oidc_utils.get_apiserver_oidc_args.return_value = None
        mw = self._mw()
        mw.public_api_routes = []
        env = {'PATH_INFO': '/v1/alarms',
               'HTTP_OIDC_TOKEN': 'tok',
               'is_public_api': False, 'REQUEST_METHOD': 'GET'}
        mw(env, mock.MagicMock())

    def test_oidc_valid(self):
        from platform_util.oidc import oidc_utils
        oidc_utils.get_apiserver_oidc_args.return_value = {
            'oidc-issuer-url': 'u', 'oidc-client-id': 'c',
            'oidc-username-claim': 's', 'oidc-groups-claim': 'g'}
        oidc_utils.validate_oidc_token.return_value = {'sub': 'a'}
        oidc_utils.get_username_from_oidc_token.return_value = 'a'
        oidc_utils.get_keystone_roles_for_oidc_token.return_value = [
            'admin']
        mw = self._mw()
        mw.public_api_routes = []
        mw.oidc_auth_params = None
        env = {'PATH_INFO': '/v1/alarms',
               'HTTP_OIDC_TOKEN': 'tok',
               'is_public_api': False, 'REQUEST_METHOD': 'GET'}
        mw(env, mock.MagicMock())

    def test_oidc_invalid(self):
        from platform_util.oidc import oidc_utils
        oidc_utils.validate_oidc_token.return_value = None
        mw = self._mw()
        mw.public_api_routes = []
        mw.oidc_auth_params = {
            'oidc-issuer-url': 'u', 'oidc-client-id': 'c',
            'oidc-username-claim': 's', 'oidc-groups-claim': 'g'}
        env = {'PATH_INFO': '/v1/alarms',
               'HTTP_OIDC_TOKEN': 'tok',
               'is_public_api': False, 'REQUEST_METHOD': 'GET'}
        mw(env, mock.MagicMock())

    def test_oidc_exc(self):
        from platform_util.oidc import oidc_utils
        oidc_utils.validate_oidc_token.side_effect = Exception("x")
        mw = self._mw()
        mw.public_api_routes = []
        mw.oidc_auth_params = {
            'oidc-issuer-url': 'u', 'oidc-client-id': 'c',
            'oidc-username-claim': 's', 'oidc-groups-claim': 'g'}
        env = {'PATH_INFO': '/v1/alarms',
               'HTTP_OIDC_TOKEN': 'tok',
               'is_public_api': False, 'REQUEST_METHOD': 'GET'}
        mw(env, mock.MagicMock())
        oidc_utils.validate_oidc_token.side_effect = None

    def test_bad_regex(self):
        from fm.common import exceptions
        with self.assertRaises(exceptions.ConfigInvalid):
            self.atmod.AuthTokenMiddleware(
                mock.MagicMock(), {},
                public_api_routes=['[bad'])


class TestHttpCoverage(unittest.TestCase):
    def test_get(self):
        make_http_client().get('/v1/alarms')

    def test_post(self):
        make_http_client(status=201).post('/v1/alarms', body='{}')

    def test_patch(self):
        make_http_client().patch('/v1/es/u1', data='[]')

    def test_put(self):
        make_http_client().put('/v1/a/u1', body='{}')

    def test_delete(self):
        make_http_client(
            status=204, data=None,
            content_type='text/plain').delete('/v1/a/u1')


class TestShellCoverage(unittest.TestCase):
    def setUp(self):
        import subprocess
        # Patch keyctl calls - binary not available in tox
        self._keyctl_patch = mock.patch(
            'fmclient.common.utils.subprocess.run',
            side_effect=subprocess.CalledProcessError(1, 'keyctl')
        )
        self._keyctl_patch.start()

    def tearDown(self):
        self._keyctl_patch.stop()

    def test_no_pw(self):
        from fmclient.shell import FmShell
        from fmclient import exc
        with self.assertRaises(exc.CommandError):
            FmShell().main([
                '--os-username', 'a', 'alarm-list'])

    def test_no_proj(self):
        from fmclient.shell import FmShell
        from fmclient import exc
        with self.assertRaises(exc.CommandError):
            FmShell().main([
                '--os-username', 'a', '--os-password', 'p',
                'alarm-list'])

    def test_no_auth(self):
        from fmclient.shell import FmShell
        from fmclient import exc
        with self.assertRaises(exc.CommandError):
            FmShell().main([
                '--os-username', 'a', '--os-password', 'p',
                '--os-project-name', 'a', 'alarm-list'])

    def test_no_region(self):
        from fmclient.shell import FmShell
        from fmclient import exc
        with self.assertRaises(exc.CommandError):
            FmShell().main([
                '--os-username', 'a', '--os-password', 'p',
                '--os-project-name', 'a',
                '--os-auth-url', 'http://k:5000',
                'alarm-list'])


if __name__ == '__main__':
    unittest.main()
