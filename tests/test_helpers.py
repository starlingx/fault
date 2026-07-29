#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Shared test helpers, base class, and mock setup.

Provides reusable components for all test files:
- Mock setup for unavailable dependencies
- Base test class with common setUp
- Helper functions for creating mock objects

:returns: None (module-level setup)
"""

import os
import sys
import unittest
from unittest import mock

# Path constants
REST_API_PATH = os.path.join(
    os.path.dirname(__file__), '..',
    'fm-rest-api', 'fm')

PROJECT_ROOT = os.path.join(
    os.path.dirname(__file__), '..')

# Modules requiring mocks
_MOCK_MODULES = [
    'fm_core',
    'tsconfig',
    'cgtsclient',
    'cgtsclient.exc',
    'cgtsclient.v1',
    'cgtsclient.v1.client',
    'platform_util',
    'platform_util.oidc',
    'platform_util.oidc.oidc_utils',
]


def setup_mocks():
    """Register mock modules for unavailable deps.

    :returns: None
    """
    for mod in _MOCK_MODULES:
        sys.modules.setdefault(
            mod, mock.MagicMock())
    sys.modules.setdefault(
        'tsconfig.tsconfig',
        mock.MagicMock(VOLATILE_PATH='/tmp'))


def add_rest_api_path():
    """Add fm-rest-api to sys.path.

    :returns: None
    """
    if REST_API_PATH not in sys.path:
        sys.path.insert(0, REST_API_PATH)


# Auto-setup on import
setup_mocks()
add_rest_api_path()


class RpcObject:
    """Mock RPC object supporting [] and as_dict().

    :param data: dict of attribute values
    :returns: RpcObject instance
    """

    def __init__(self, data):
        """Initialize with data dict.

        :param data: attribute dictionary
        :returns: None
        """
        self._d = dict(data)
        for k, v in data.items():
            setattr(self, k, v)

    def __getitem__(self, key):
        """Get item by key.

        :param key: attribute name
        :returns: attribute value
        """
        return self._d[key]

    def __setitem__(self, key, value):
        """Set item by key.

        :param key: attribute name
        :param value: attribute value
        :returns: None
        """
        self._d[key] = value

    def as_dict(self):
        """Return data as dictionary.

        :returns: dict -- copy of data
        """
        return dict(self._d)


def make_rpc(data):
    """Create an RPC-like mock object.

    :param data: dict of attribute values
    :returns: RpcObject instance
    """
    return RpcObject(data)


def make_mock_query():
    """Create a fully-chained mock query object.

    :returns: MagicMock with chained methods
    """
    query = mock.MagicMock()
    for attr in [
        'filter_by', 'filter', 'join',
        'outerjoin', 'add_columns', 'order_by',
    ]:
        getattr(query, attr).return_value = query
    query.all.return_value = []
    query.one.return_value = (
        mock.MagicMock(), 'u', 'w', 'n')
    query.first.return_value = mock.MagicMock()
    return query


def make_http_client(
        status=200, data=None,
        content_type='application/json'):
    """Create a mocked HTTP SessionClient.

    :param status: HTTP status code
    :param data: response body dict
    :param content_type: Content-Type header
    :returns: SessionClient instance
    """
    import json
    from fmclient.common.http import SessionClient
    session = mock.MagicMock()
    resp = mock.MagicMock()
    resp.status_code = status
    body = json.dumps(data or {}).encode()
    resp.content = body
    resp.text = body.decode()
    resp.json.return_value = data or {}
    resp.headers = {
        'Content-Type': content_type}
    session.request.return_value = resp
    return SessionClient(
        session=session,
        endpoint_override='http://h:18002',
        service_type='fm',
        interface='internal')


def mock_session_for_write():
    """Create a mock for _session_for_write.

    :returns: MagicMock context manager
    """
    msw = mock.patch(
        'fm.db.sqlalchemy.api'
        '._session_for_write')
    m = msw.start()
    sess = mock.MagicMock()
    m.return_value.__enter__ = (
        mock.MagicMock(return_value=sess))
    m.return_value.__exit__ = (
        mock.MagicMock(return_value=False))
    return msw, sess


class BaseFaultTestCase(unittest.TestCase):
    """Base test class with common setup.

    Provides mocked model_query and DB
    Connection for subclasses.
    """

    def setUp(self):
        """Set up mocked DB query and connection.

        :returns: None
        """
        from fm.db.sqlalchemy import api
        self.db_api = api
        self.mq_patcher = mock.patch(
            'fm.db.sqlalchemy.api.model_query')
        self.mock_query = self.mq_patcher.start()
        self.mock_query.return_value = (
            make_mock_query())
        self.conn = api.Connection()

    def tearDown(self):
        """Stop model_query patcher.

        :returns: None
        """
        self.mq_patcher.stop()

    def call_unwrapped(self, method_name,
                       *args, **kwargs):
        """Call Connection method via __wrapped__.

        Bypasses @db_session_cleanup decorator.

        :param method_name: name of method to call
        :returns: method return value
        """
        method = getattr(
            type(self.conn), method_name)
        if hasattr(method, '__wrapped__'):
            return method.__wrapped__(
                self.conn, *args, **kwargs)
        return method(
            self.conn, *args, **kwargs)
