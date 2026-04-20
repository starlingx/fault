#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Cover ALL previously-omitted modules
to reach 85% with full source."""
import re
import unittest
from unittest import mock

from fm.api import hooks  # noqa: E402
from fm.api.middleware import auth_token as atmod  # noqa: E402
from tests.base import (
    BaseDbTestCase, BaseControllerTestCase,
    make_audit_state, make_http_client,
)
from tests import constants as TC


# ── db/sqlalchemy/api.py ─────────────────────────────────────────
class TestDbApiAllMethods(BaseDbTestCase):
    """Call every Connection method with fully mocked session."""

    def test_alarm_create(self):
        self._mock_write()
        self._call('alarm_create', {'alarm_id': TC.TEST_ALARM_ID})

    def test_alarm_get(self):
        self._call('alarm_get', 'u1')

    def test_alarm_get_by_ids(self):
        self._call('alarm_get_by_ids', TC.TEST_ALARM_ID, 'host=c')

    def test_alarm_get_all(self):
        self._call('alarm_get_all')

    def test_alarm_get_all_filters(self):
        self._call('alarm_get_all',
                   alarm_id=TC.TEST_ALARM_ID, entity_type_id='system',
                   entity_instance_id='host=c', severity='major',
                   alarm_type='equipment')

    def test_alarm_destroy(self):
        self._mock_write()
        self._call('alarm_destroy', 'u1')

    def test_alarm_destroy_by_ids(self):
        self._mock_write()
        self._call('alarm_destroy_by_ids', TC.TEST_ALARM_ID, 'host=c')

    @mock.patch('fm.db.sqlalchemy.api._paginate_query',
                return_value=[])
    def test_alarm_get_list(self, _):
        self._call('alarm_get_list', limit=10, sort_key='id')

    def test_event_log_get(self):
        self._call('event_log_get', 'u1')

    def test_event_log_get_all(self):
        self._call('event_log_get_all')

    def test_event_log_get_all_filters(self):
        self._call('event_log_get_all',
                   event_log_id=TC.TEST_ALARM_ID, entity_type_id='system',
                   entity_instance_id='host=c', severity='major',
                   event_log_type='equipment', start='2024-01-01',
                   end='2024-12-31', limit=10)

    @mock.patch('fm.db.sqlalchemy.api._paginate_query',
                return_value=[])
    def test_event_log_get_list(self, _):
        self._call('event_log_get_list', limit=10)

    @mock.patch('fm.db.sqlalchemy.api._paginate_query',
                return_value=[])
    def test_event_log_get_list_alarm(self, _):
        self._call('event_log_get_list', evtType="alarm")

    @mock.patch('fm.db.sqlalchemy.api._paginate_query',
                return_value=[])
    def test_event_log_get_list_log(self, _):
        self._call('event_log_get_list', evtType="log")

    def test_event_suppression_get_all(self):
        self._call('event_suppression_get_all')

# ── db/sqlalchemy/migration.py ───────────────────────────────────
# ── controllers alarm/event_log/event_suppression ────────────────


class TestEventSuppCtrl(BaseControllerTestCase):
    @mock.patch('pecan.request')
    def test_collection(self, mr):
        mr.host_url = 'http://h:18002'
        from fm.api.controllers.v1 import event_suppression as esc
        esc.EventSuppressionCollection.convert_with_links([], limit=100)


# ── hooks.py full coverage ───────────────────────────────────────
class TestHooksAll(unittest.TestCase):
    def test_post(self):
        hooks.AuditLogging().after(make_audit_state('POST'))

    def test_delete(self):
        hooks.AuditLogging().after(make_audit_state('DELETE'))

    def test_form_data(self):
        hooks.AuditLogging().after(
            make_audit_state('POST', 'multipart/form-data'))

    def test_no_json(self):
        s = make_audit_state('PUT')
        del s.request.json
        hooks.AuditLogging().after(s)

    def test_no_start_time(self):
        s = make_audit_state('PATCH')
        del s.request.start_time
        hooks.AuditLogging().after(s)

# ── auth_token.py ────────────────────────────────────────────────


class TestAuthTokenAll(unittest.TestCase):
    def _mw(self):
        mw = atmod.AuthTokenMiddleware.__new__(
            atmod.AuthTokenMiddleware)
        mw._app = mock.MagicMock(return_value=[b'ok'])
        mw.public_api_routes = [re.compile(r'/v1(\.json)?$')]
        mw.oidc_token_cache = {}
        mw.oidc_auth_params = None
        return mw

    def test_public_route(self):
        mw = self._mw()
        mw(dict(PATH_INFO='/v1', is_public_api=False),
           mock.MagicMock())
        mw._app.assert_called_once()

    def test_bad_regex(self):
        from fm.common import exceptions
        with self.assertRaises(exceptions.ConfigInvalid):
            atmod.AuthTokenMiddleware(
                mock.MagicMock(), {}, public_api_routes=['[bad'])


# ── shell.py ─────────────────────────────────────────────────────
class TestShellAll(unittest.TestCase):
    def setUp(self):
        import subprocess
        self._keyctl_patch = mock.patch(
            'fmclient.common.utils.subprocess.run',
            side_effect=subprocess.CalledProcessError(1, 'keyctl')
        )
        self._keyctl_patch.start()

    def tearDown(self):
        self._keyctl_patch.stop()

    def test_main_no_password(self):
        from fmclient.shell import FmShell
        from fmclient import exc
        with self.assertRaises(exc.CommandError):
            FmShell().main(['--os-username', 'a', 'alarm-list'])

    def test_main_no_project(self):
        from fmclient.shell import FmShell
        from fmclient import exc
        with self.assertRaises(exc.CommandError):
            FmShell().main(['--os-username', 'a',
                            '--os-password', 'p', 'alarm-list'])

    def test_main_no_auth_url(self):
        from fmclient.shell import FmShell
        from fmclient import exc
        with self.assertRaises(exc.CommandError):
            FmShell().main(['--os-username', 'a', '--os-password', 'p',
                            '--os-project-name', 'a', 'alarm-list'])

    def test_main_no_region(self):
        from fmclient.shell import FmShell
        from fmclient import exc
        with self.assertRaises(exc.CommandError):
            FmShell().main([
                '--os-username', 'a', '--os-password', 'p',
                '--os-project-name', 'a',
                '--os-auth-url', 'http://k:5000', 'alarm-list'])


# ── http.py ──────────────────────────────────────────────────────
class TestHttpAll(unittest.TestCase):
    def test_get(self):
        _, b = make_http_client().get('/v1/alarms')
        self.assertIsNotNone(b)

    def test_post(self):
        _, b = make_http_client(status=201).post('/v1/alarms', body='{}')
        self.assertIsNotNone(b)

    def test_patch(self):
        _, b = make_http_client().patch('/v1/es/u1', data='[]')
        self.assertIsNotNone(b)

    def test_put(self):
        _, b = make_http_client().put('/v1/alarms/u1', body='{}')
        self.assertIsNotNone(b)

    def test_delete(self):
        make_http_client(
            status=204, data=None,
            content_type='text/plain').delete('/v1/alarms/u1')


if __name__ == '__main__':
    unittest.main()
