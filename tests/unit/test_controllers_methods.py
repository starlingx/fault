#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Cover controller methods via __wrapped__
to bypass @wsme_pecan.wsexpose."""
import unittest
from unittest import mock
from tests import test_helpers  # noqa: F401,E402
from tests import constants as TC

UID = TC.TEST_UUID


from tests.base import make_event_log_rpc  # noqa: E402


class TestAlarmControllerMethods(unittest.TestCase):
    """Call AlarmController methods via __wrapped__."""

    @mock.patch('pecan.request')
    @mock.patch('fm.db.api.get_instance')
    def test_summary(self, mdb, mr):
        from fm.api.controllers.v1 import alarm as ac
        mr.host_url = 'http://h:18002'
        dbapi = mock.MagicMock()
        dbapi.alarm_get_all.return_value = []
        mr.dbapi = dbapi
        ctrl = ac.AlarmController()
        result = ac.AlarmController.summary.__wrapped__(ctrl)
        self.assertIsNotNone(result)

    def test_enforce_policy(self):
        from fm.api.controllers.v1 import alarm as ac
        ctrl = ac.AlarmController()
        req = mock.MagicMock()
        req.context = mock.MagicMock()
        with mock.patch('fm.common.policy.authorize'):
            ctrl.enforce_policy('get_one', req)


class TestEventLogControllerMethods(unittest.TestCase):
    """Call EventLogController methods via __wrapped__."""

    def _elog_rpc(self):
        return make_event_log_rpc()

    @mock.patch('pecan.request')
    @mock.patch('fm.db.api.get_instance')
    def test_get_all(self, mdb, mr):
        from fm.api.controllers.v1 import event_log as ec
        mr.host_url = 'http://h:18002'
        dbapi = mock.MagicMock()
        dbapi.event_log_get_all.return_value = [
            self._elog_rpc()]
        mr.dbapi = dbapi
        ctrl = ec.EventLogController()
        result = ec.EventLogController.get_all.__wrapped__(
            ctrl, limit=100, sort_key='id', sort_dir='asc')
        self.assertIsNotNone(result)

    def test_enforce_policy(self):
        from fm.api.controllers.v1 import event_log as ec
        ctrl = ec.EventLogController()
        req = mock.MagicMock()
        with mock.patch('fm.common.policy.authorize'):
            ctrl.enforce_policy('get_one', req)


class TestEventSuppControllerMethods(unittest.TestCase):
    """Call EventSuppressionController methods via __wrapped__."""

    def _es_rpc(self):
        from tests.base import make_suppression_rpc
        return make_suppression_rpc()

    def test_enforce_policy(self):
        from fm.api.controllers.v1 import event_suppression as esc
        ctrl = esc.EventSuppressionController()
        req = mock.MagicMock()
        with mock.patch('fm.common.policy.authorize'):
            ctrl.enforce_policy('get_one', req)


if __name__ == '__main__':
    unittest.main()
