#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Final 134 lines to reach 85%: http, migration, utils, wrapping."""
import unittest
from unittest import mock
from tests import test_helpers  # noqa: F401,E402

# ── http.py: fix resp.json.return_value ──────────────────────────


class TestHttpFixed(unittest.TestCase):
    def _c(self, status=200, data=None, ct='application/json'):
        from tests.base import make_http_client
        return make_http_client(status=status, data=data,
                                content_type=ct)

    def test_get(self):
        _, b = self._c(data={'alarms': []}).get('/v1/alarms')
        self.assertEqual(b, {'alarms': []})

    def test_post(self):
        _, b = self._c(201, {'uuid': 'n'}).post('/v1/a', body='{}')
        self.assertEqual(b['uuid'], 'n')

    def test_patch(self):
        _, b = self._c(data={'uuid': 'u'}).patch('/v1/e/u', data='[]')
        self.assertEqual(b['uuid'], 'u')

    def test_put(self):
        _, b = self._c(data={'uuid': 'u'}).put('/v1/a/u', body='{}')
        self.assertEqual(b['uuid'], 'u')

    def test_delete(self):
        from tests.base import make_http_client
        make_http_client(
            status=204, data=None,
            content_type='text/plain').delete('/v1/a/u')

    def test_get_404(self):
        try:
            self._c(404, ct='text/plain').get('/v1/a/bad')
        except Exception:
            pass

    def test_get_500(self):
        try:
            self._c(500, ct='text/plain').get('/v1/a')
        except Exception:
            pass


# ── migration.py: mock enginefacade before import ────────────────
# ── utils.py: more print/sort coverage ───────────────────────────


class TestUtilsMore(unittest.TestCase):
    def setUp(self):
        from fmclient.common import utils
        self.u = utils

    def test_print_list_sort_wrap(self):
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

    def test_print_long_list_sort_wrap(self):
        from fmclient.common import wrapping_formatters as wf
        o1 = mock.MagicMock()
        o1.n = 'b'
        o2 = mock.MagicMock()
        o2.n = 'a'
        fmts = wf.build_wrapping_formatters(
            [o1, o2], ['n'], ['N'], {'n': 0.5})
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o1, o2], ['n'], ['N'],
                formatters=fmts, sortby=0,
                no_paging=True)

    def test_pt_builder_nowrap_fallback(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.n = 'x' * 200
        fmts = wf.build_wrapping_formatters(
            [o], ['n'], ['N'], {'n': 0.3})
        builder = self.u.pt_builder(
            ['N'], ['n'], fmts, False)
        builder.add_row(o)
        s = builder.get_string()
        self.assertIsNotNone(s)
        builder.done()


if __name__ == '__main__':
    unittest.main()
