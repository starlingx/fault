#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Base test classes and mixins implementing DRY principles.

Provides reusable OOP components for all test files:
- Environment setup (sys.path, mock modules)
- Base test classes with common setUp/tearDown
- Factory methods for test data objects
- Mixins for specific test patterns
"""

import os
import sys
import time
import unittest
from unittest import mock

# ── Path Constants ───────────────────────────────────────────────

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')

REST_API_PATH = os.path.join(PROJECT_ROOT, 'fm-rest-api', 'fm')

FM_API_SOURCE = os.path.join(PROJECT_ROOT, 'fm-api', 'source')

FM_COMMON_SOURCES = os.path.join(PROJECT_ROOT, 'fm-common', 'sources')

FM_DOC_PATH = os.path.join(PROJECT_ROOT, 'fm-doc', 'fm_doc')

FMCLIENT_PATH = os.path.join(
    PROJECT_ROOT, 'python-fmclient', 'fmclient')

# ── Module Mocking ───────────────────────────────────────────────

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


def setup_environment():
    """Register mock modules and add source paths to sys.path."""
    for mod in _MOCK_MODULES:
        sys.modules.setdefault(mod, mock.MagicMock())
    sys.modules.setdefault(
        'tsconfig.tsconfig',
        mock.MagicMock(VOLATILE_PATH='/tmp'))
    for path in [REST_API_PATH, FM_API_SOURCE,
                 FM_COMMON_SOURCES, FM_DOC_PATH, FMCLIENT_PATH]:
        if path not in sys.path:
            sys.path.insert(0, path)


# Auto-setup on import
setup_environment()

# ── Test Data Constants ──────────────────────────────────────────

TEST_UUID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
TEST_ALARM_ID = '100.104'

# ── Factory Functions ────────────────────────────────────────────


def make_fault(**overrides):
    """Create a Fault object with sensible defaults."""
    from fm_api.fm_api import Fault
    defaults = dict(
        alarm_id=TEST_ALARM_ID,
        alarm_state='set',
        entity_type_id='system',
        entity_instance_id='host=controller-0',
        severity='major',
        reason_text='Test alarm',
        alarm_type='equipment',
        probable_cause='software-error',
        proposed_repair_action='Fix it',
    )
    defaults.update(overrides)
    return Fault(**defaults)


def make_alarm_str():
    """Create a valid alarm separator-delimited string."""
    from fm_api import constants
    sep = constants.FM_CLIENT_STR_SEP
    parts = ['uuid-1', TEST_ALARM_ID, 'set', 'system',
             'host=ctrl-0', '2024-01-01', 'major',
             'Test', 'equipment', 'software-error',
             'Fix', 'False', 'False', 'False']
    return sep.join(parts)


class RpcObject:
    """Mock RPC object supporting [], setattr, and as_dict()."""

    def __init__(self, data):
        self._d = dict(data)
        for k, v in data.items():
            setattr(self, k, v)

    def __getitem__(self, key):
        return self._d[key]

    def __setitem__(self, key, value):
        self._d[key] = value

    def as_dict(self):
        return dict(self._d)


def make_alarm_rpc(**overrides):
    """Create an RPC-like alarm object."""
    data = dict(
        uuid=TEST_UUID, alarm_id=TEST_ALARM_ID, alarm_state='set',
        entity_type_id='system', entity_instance_id='host=c',
        timestamp=None, severity='major', reason_text='t',
        alarm_type='equipment', probable_cause='software-error',
        proposed_repair_action='fix', service_affecting=False,
        suppression=False, inhibit_alarms=False, masked=False,
        suppression_status='unsuppressed',
        mgmt_affecting='warning', degrade_affecting='none')
    data.update(overrides)
    return RpcObject(data)


def make_event_log_rpc(**overrides):
    """Create an RPC-like event log object."""
    data = dict(
        uuid=TEST_UUID, event_log_id=TEST_ALARM_ID, state='set',
        entity_type_id='system', entity_instance_id='host=c',
        timestamp=None, severity='major', reason_text='t',
        event_log_type='equipment', probable_cause='software-error',
        proposed_repair_action='fix', service_affecting=False,
        suppression=False, suppression_status='unsuppressed')
    data.update(overrides)
    return RpcObject(data)


def make_suppression_rpc(**overrides):
    """Create an RPC-like event suppression object."""
    data = dict(
        uuid=TEST_UUID, alarm_id=TEST_ALARM_ID,
        description='t', suppression_status='unsuppressed')
    data.update(overrides)
    return RpcObject(data)


def make_mock_query():
    """Create a fully-chained mock query object."""
    q = mock.MagicMock()
    for attr in ['filter_by', 'filter', 'join', 'outerjoin',
                 'add_columns', 'order_by', 'limit']:
        getattr(q, attr).return_value = q
    q.all.return_value = []
    q.one.return_value = (mock.MagicMock(), 'u', 'w', 'n')
    q.first.return_value = mock.MagicMock()
    return q


def make_http_client(status=200, data=None,
                     content_type='application/json'):
    """Create a mocked SessionClient with preset response."""
    import json as json_mod
    from fmclient.common.http import SessionClient
    session = mock.MagicMock()
    resp = mock.MagicMock()
    resp.status_code = status
    body = json_mod.dumps(data or {}).encode()
    resp.content = body
    resp.text = body.decode()
    resp.json.return_value = data or {}
    resp.headers = {'Content-Type': content_type}
    session.request.return_value = resp
    return SessionClient(
        session=session, endpoint_override='http://h:18002',
        service_type='fm', interface='internal')


def make_audit_state(method='POST',
                     content_type='application/json'):
    """Create a mock pecan state for AuditLogging tests."""
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
    state.request.json = {'data': 'x'}
    state.request.headers = mock.MagicMock()
    state.request.headers.get = mock.MagicMock(
        side_effect=lambda k, d=None: {
            'X-User-Id': 'uid', 'X-User': 'admin',
            'X-Tenant-Id': 'tid', 'X-Tenant': 'admin',
            'X-User-Domain-Name': 'Default',
            'Content-Type': content_type,
        }.get(k, d))
    state.response.status_int = 200
    state.response.content_length = 42
    return state


# ── Base Test Classes ────────────────────────────────────────────


class BaseDbTestCase(unittest.TestCase):
    """Base class for DB layer tests with mocked model_query."""

    def setUp(self):
        from fm.db.sqlalchemy import api
        self.api = api
        self.patcher = mock.patch(
            'fm.db.sqlalchemy.api.model_query')
        self.mq = self.patcher.start()
        self.mq.return_value = make_mock_query()
        self.conn = api.Connection()

    def tearDown(self):
        self.patcher.stop()

    def _call(self, method_name, *args, **kwargs):
        """Call Connection method via __wrapped__ if available."""
        method = getattr(type(self.conn), method_name)
        if hasattr(method, '__wrapped__'):
            return method.__wrapped__(self.conn, *args, **kwargs)
        return method(self.conn, *args, **kwargs)

    def _mock_write(self):
        """Patch _session_for_write and return mock session."""
        p = mock.patch('fm.db.sqlalchemy.api._session_for_write')
        m = p.start()
        s = mock.MagicMock()
        m.return_value.__enter__ = mock.MagicMock(return_value=s)
        m.return_value.__exit__ = mock.MagicMock(return_value=False)
        self.addCleanup(p.stop)
        return s


class BaseFmApiTestCase(unittest.TestCase):
    """Base class for fm_api tests."""

    def setUp(self):
        from fm_api.fm_api import FaultAPIsBase, Fault
        from fm_api import constants
        self.base = FaultAPIsBase()
        self.Fault = Fault
        self.constants = constants

    def _make_fault(self, **kwargs):
        return make_fault(**kwargs)


class BaseControllerTestCase(unittest.TestCase):
    """Base class for controller tests."""

    def _alarm_rpc(self, **overrides):
        return make_alarm_rpc(**overrides)

    def _elog_rpc(self, **overrides):
        return make_event_log_rpc(**overrides)

    def _es_rpc(self, **overrides):
        return make_suppression_rpc(**overrides)
