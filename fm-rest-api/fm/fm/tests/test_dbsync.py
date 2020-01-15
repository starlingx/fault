# Copyright 2020 Intel Corporation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from fm.db import migration
from fm.db.sqlalchemy import api as db_api
from fm.tests.db import base


class DbSyncTestCase(base.DbTestCase):
    def setUp(self):
        super(DbSyncTestCase, self).setUp()

    def test_sync_and_version(self):
        migration.db_sync()
        engine = db_api.get_engine()
        v = migration.get_backend().db_version(engine, migration.MIGRATE_REPO_PATH, None)
        self.assertTrue(v > base.INIT_VERSION)
