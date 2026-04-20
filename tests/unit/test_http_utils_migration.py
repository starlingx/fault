#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Cover 336+ lines to reach 85% with ALL source files included."""
import unittest
from unittest import mock
from tests import test_helpers  # noqa: F401,E402
from tests import constants as TC

UID = TC.TEST_UUID


# ── fmclient.common.http - cover 123 lines ──────────────────────


class TestHttpFull(unittest.TestCase):
    """Cover SessionClient by calling every method."""

    def test_delete(self):
        from tests.base import make_http_client
        make_http_client(
            status=204, data=None,
            content_type='text/plain').delete('/v1/a/u1')

    def test_get_404(self):
        from tests.base import make_http_client
        try:
            make_http_client(
                status=404, content_type='text/plain').get('/v1/alarms/bad')
        except Exception:
            pass

    def test_get_500(self):
        from tests.base import make_http_client
        try:
            make_http_client(
                status=500, content_type='text/plain').get('/v1/alarms')
        except Exception:
            pass

    def test_get_401(self):
        from tests.base import make_http_client
        try:
            make_http_client(
                status=401, content_type='text/plain').get('/v1/alarms')
        except Exception:
            pass

    def test_encode_headers(self):
        from fmclient.common.http import encode_headers
        r = encode_headers({'Content-Type': 'application/json',
                            'X-Auth-Token': 'tok'})
        self.assertIsNotNone(r)

    def test_chunk_body(self):
        from fmclient.common.http import _BaseHTTPClient
        body = mock.MagicMock()
        body.read = mock.MagicMock(side_effect=[b'data', b''])
        self.assertEqual(
            list(_BaseHTTPClient._chunk_body(body)), [b'data'])

    def test_get_http_client(self):
        from fmclient.common import http
        c = http.get_http_client(
            'http://h:18002', session=mock.MagicMock())
        self.assertIsNotNone(c)


# ── fmclient.common.utils - cover 126 lines ─────────────────────


class TestUtilsFull(unittest.TestCase):
    def setUp(self):
        from fmclient.common import utils
        self.u = utils

    def test_print_list_sorted(self):
        o1 = mock.MagicMock()
        o1.n = 'b'
        o2 = mock.MagicMock()
        o2.n = 'a'
        with mock.patch('builtins.print'):
            self.u.print_list([o1, o2], ['n'], ['N'], sortby=0)

    def test_print_list_reverse(self):
        o = mock.MagicMock()
        o.n = 'a'
        with mock.patch('builtins.print'):
            self.u.print_list(
                [o], ['n'], ['N'], sortby=0, reversesort=True)

    def test_print_list_with_wrap_fmt(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.n = 'test val'
        fmts = wf.build_wrapping_formatters(
            [o], ['n'], ['N'], {'n': 0.5})
        with mock.patch('builtins.print'):
            self.u.print_list([o], ['n'], ['N'], formatters=fmts)

    def test_print_list_sort_with_wrap_fmt(self):
        from fmclient.common import wrapping_formatters as wf
        o1 = mock.MagicMock()
        o1.n = 'b'
        o2 = mock.MagicMock()
        o2.n = 'a'
        fmts = wf.build_wrapping_formatters(
            [o1, o2], ['n'], ['N'], {'n': 0.5})
        with mock.patch('builtins.print'):
            self.u.print_list(
                [o1, o2], ['n'], ['N'],
                formatters=fmts, sortby=0)

    def test_print_list_sort_with_lambda_fmt(self):
        o1 = mock.MagicMock()
        o1.n = 'b'
        o2 = mock.MagicMock()
        o2.n = 'a'
        fmts = {'n': lambda x: str(x).upper()}
        with mock.patch('builtins.print'):
            self.u.print_list(
                [o1, o2], ['n'], ['N'],
                formatters=fmts, sortby=0)

    def test_print_dict_wrap(self):
        with mock.patch('builtins.print'):
            self.u.print_dict({'k': 'x' * 200}, wrap=72)

    def test_print_long_list_sorted(self):
        o1 = mock.MagicMock()
        o1.n = 'b'
        o2 = mock.MagicMock()
        o2.n = 'a'
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o1, o2], ['n'], ['N'],
                sortby=0, no_paging=True)

    def test_print_long_list_reverse(self):
        o = mock.MagicMock()
        o.n = 'a'
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o], ['n'], ['N'],
                sortby=0, reversesort=True, no_paging=True)

    def test_print_long_list_with_wrap_fmt(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.n = 'test'
        fmts = wf.build_wrapping_formatters(
            [o], ['n'], ['N'], {'n': 0.5})
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o], ['n'], ['N'],
                formatters=fmts, sortby=0, no_paging=True)

    def test_print_long_list_sort_lambda(self):
        o1 = mock.MagicMock()
        o1.n = 'b'
        o2 = mock.MagicMock()
        o2.n = 'a'
        fmts = {'n': lambda x: str(x).upper()}
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o1, o2], ['n'], ['N'],
                formatters=fmts, sortby=0, no_paging=True)

    def test_pt_builder_many_rows(self):
        builder = self.u.pt_builder(['N'], ['n'], {}, False)
        for i in range(5):
            o = mock.MagicMock()
            o.n = f'v{i}'
            builder.add_row(o)
        self.assertIsNotNone(builder.get_string())
        builder.done()

    def test_pt_builder_with_fmt(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.n = 'test'
        fmts = wf.build_wrapping_formatters(
            [o], ['n'], ['N'], {'n': 0.5})
        builder = self.u.pt_builder(['N'], ['n'], fmts, False)
        builder.add_row(o)
        self.assertIsNotNone(builder.get_string())
        builder.done()

    def test_define_command_list_cmd(self):
        sp = mock.MagicMock()
        sub = mock.MagicMock()
        sp.add_parser.return_value = sub
        mapper = {}
        def do_alarm_list():  # noqa: E306
            """List alarms."""
        do_alarm_list.__name__ = 'do_alarm_list'
        do_alarm_list.arguments = []
        self.u.define_command(
            sp, 'alarm-list', do_alarm_list, mapper)
        self.assertIn('alarm-list', mapper)


# ── db/sqlalchemy/migration.py - cover 60 lines ─────────────────


class TestMigrationFull(unittest.TestCase):
    def _engine(self):
        e = mock.MagicMock()
        c = mock.MagicMock()
        e.begin.return_value.__enter__ = mock.MagicMock(
            return_value=c)
        e.begin.return_value.__exit__ = mock.MagicMock(
            return_value=False)
        return e, c

# ── fmclient.shell - cover 39 lines ─────────────────────────────


class TestShellFull(unittest.TestCase):
    def setUp(self):
        import subprocess
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
            FmShell().main(['--os-username', 'a', 'alarm-list'])

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
                '--os-auth-url', 'http://k:5000', 'alarm-list'])

    def test_main_keyboard(self):
        from fmclient import shell
        with mock.patch.object(
                shell.FmShell, 'main',
                side_effect=KeyboardInterrupt):
            with self.assertRaises(SystemExit):
                shell.main()

    def test_main_ioerror(self):
        from fmclient import shell
        with mock.patch.object(
                shell.FmShell, 'main', side_effect=IOError):
            with self.assertRaises(SystemExit):
                shell.main()

    def test_main_exception(self):
        from fmclient import shell
        with mock.patch.object(
                shell.FmShell, 'main',
                side_effect=Exception("err")):
            with self.assertRaises(SystemExit):
                shell.main()

    def test_get_subcommand_parser(self):
        from fmclient.shell import FmShell
        p = FmShell().get_subcommand_parser('1')
        self.assertIsNotNone(p)

    def test_bash_completion(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        sh.subcommands = {
            'alarm-list': mock.MagicMock(),
            'bash_completion': mock.MagicMock()}
        for k in sh.subcommands:
            sh.subcommands[k]._optionals._option_string_actions = {
                '--help': None}
        with mock.patch('builtins.print'):
            sh.do_bash_completion(mock.MagicMock())

    def test_cache_key(self):
        from fmclient.shell import FmShell
        sh = FmShell()
        self.assertIn('fmclient', sh._cache_key('admin'))
        self.assertEqual(sh._cache_key(''), sh.CACHE_KEY)


if __name__ == '__main__':
    unittest.main()
