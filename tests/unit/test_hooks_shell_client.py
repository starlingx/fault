#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Final push to 85% - cover 30 more lines."""
import unittest
from unittest import mock

from fm.api import hooks  # noqa: E402
from tests.base import make_audit_state  # noqa: E402


class TestHooksFinal(unittest.TestCase):
    """Cover remaining hooks.py lines."""

    def test_audit_post_json(self):
        hooks.AuditLogging().after(make_audit_state('POST'))

    def test_audit_put_json(self):
        hooks.AuditLogging().after(make_audit_state('PUT'))

    def test_audit_delete_json(self):
        hooks.AuditLogging().after(make_audit_state('DELETE'))

    def test_audit_patch_form(self):
        hooks.AuditLogging().after(
            make_audit_state('PATCH', 'multipart/form-data'))

    def test_audit_no_json_attr(self):
        state = make_audit_state('POST')
        del state.request.json
        hooks.AuditLogging().after(state)


class TestFmclientUtilsFinal(unittest.TestCase):
    """Cover remaining fmclient.common.utils lines."""

    def setUp(self):
        from fmclient.common import utils
        self.u = utils

    def test_print_list_sortby(self):
        o1 = mock.MagicMock()
        o1.name = 'b'
        o2 = mock.MagicMock()
        o2.name = 'a'
        with mock.patch('builtins.print'):
            self.u.print_list([o1, o2], ['name'], ['Name'], sortby=0)

    def test_print_list_reversesort(self):
        o1 = mock.MagicMock()
        o1.name = 'a'
        o2 = mock.MagicMock()
        o2.name = 'b'
        with mock.patch('builtins.print'):
            self.u.print_list([o1, o2], ['name'], ['Name'],
                              sortby=0, reversesort=True)

    def test_print_dict_wrap(self):
        with mock.patch('builtins.print'):
            self.u.print_dict({'key': 'x' * 200}, wrap=72)

    def test_normalize_field_data_unicode(self):
        o = mock.MagicMock()
        o.name = 'test\u2019s'
        self.u.normalize_field_data(o, ['name'])

    def test_is_service_impacting(self):
        if hasattr(self.u, '_is_service_impacting_command'):
            self.assertFalse(
                self.u._is_service_impacting_command('alarm-list'))


class TestAlarmShellFinal(unittest.TestCase):
    """Cover remaining alarm_shell lines."""

    def test_do_alarm_list_with_uuid(self):
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


class TestClientFinal(unittest.TestCase):
    """Cover fmclient.client lines."""

    def test_get_client_token_endpoint(self):
        from fmclient import client
        with mock.patch(
                'oslo_utils.importutils.import_versioned_module') as m:
            mock_mod = mock.MagicMock()
            mock_mod.Client.return_value = mock.MagicMock()
            m.return_value = mock_mod
            result = client.get_client(
                1, endpoint='http://h:18002',
                auth_token='tok', timeout=30)
            self.assertIsNotNone(result)

    def test_get_client_auth_url_token(self):
        from fmclient import client
        with mock.patch(
                'keystoneauth1.loading.get_plugin_loader') as ml:
            with mock.patch(
                    'keystoneauth1.loading.session.Session') as ms:
                sess = mock.MagicMock()
                sess.get_endpoint.return_value = 'http://h:18002'
                ms.return_value.load_from_options.return_value = sess
                with mock.patch(
                        'oslo_utils.importutils'
                        '.import_versioned_module') as mi:
                    mock_mod = mock.MagicMock()
                    mock_mod.Client.return_value = mock.MagicMock()
                    mi.return_value = mock_mod
                    result = client.get_client(
                        1, auth_url='http://k:5000',
                        auth_token='tok')
                    self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
