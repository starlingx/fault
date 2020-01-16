# Copyright 2020 Intel Corporation.
#
# SPDX-License-Identifier: Apache-2.0
#


"""Tests for Alarm via the DB API"""

from fm.db import api as dbapi
from fm.tests.db import base
from fm.tests.db import utils


class DbAlarmTestCase(base.DbTestCase):

    def setUp(self):
        super(DbAlarmTestCase, self).setUp()
        self.dbapi = dbapi.get_instance()

    def test_create_alarm(self):
        uuid = 1234567
        alarm = utils.get_test_alarm(uuid=uuid)
        alarm_exist = self.dbapi.alarm_create(alarm)
        self.assertEqual(uuid, alarm_exist.uuid)
