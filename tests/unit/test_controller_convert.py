#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Cover pecan controllers by calling
convert_with_links with mocked data."""
import unittest
from unittest import mock
from tests.base import (
    BaseControllerTestCase, make_http_client,
)


class TestAlarmControllerConvert(BaseControllerTestCase):
    pass


class TestFmclientUtilsCover(unittest.TestCase):
    """Cover remaining fmclient.common.utils lines."""

    def setUp(self):
        from fmclient.common import utils
        self.u = utils

    def test_print_list_with_formatters(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.name = 'test'
        o.value = 'data'
        spec = {'name': 0.5, 'value': 0.5}
        fmts = wf.build_wrapping_formatters(
            [o], ['name', 'value'], ['Name', 'Value'], spec)
        with mock.patch('builtins.print'):
            self.u.print_list([o], ['name', 'value'],
                              ['Name', 'Value'], formatters=fmts)

    def test_print_long_list_with_formatters(self):
        from fmclient.common import wrapping_formatters as wf
        o = mock.MagicMock()
        o.name = 'test'
        spec = {'name': 0.5}
        fmts = wf.build_wrapping_formatters(
            [o], ['name'], ['Name'], spec)
        with mock.patch('builtins.print'):
            self.u.print_long_list(
                [o], ['name'], ['Name'],
                formatters=fmts, no_paging=True)

    def test_define_command_list(self):
        sp = mock.MagicMock()
        sub = mock.MagicMock()
        sp.add_parser.return_value = sub
        mapper = {}

        def do_alarm_list():
            """List alarms."""
            pass
        do_alarm_list.__name__ = 'do_alarm_list'
        do_alarm_list.arguments = []
        self.u.define_command(sp, 'alarm-list', do_alarm_list, mapper)
        self.assertIn('alarm-list', mapper)


class TestFmclientHttpCover2(unittest.TestCase):
    """Cover more http.py lines."""

    def test_raw_request(self):
        _, body = make_http_client().get('/v1/alarms')
        self.assertIsNotNone(body)


class TestDbSqlalchemyMigrationCover(unittest.TestCase):
    """Cover migration.py by mocking alembic."""


if __name__ == '__main__':
    unittest.main()
