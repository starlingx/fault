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

"""Base classes for our unit tests.

Allows overriding of config for use of fakes, and some black magic for
inline callbacks.

"""
import sys

import fixtures
import mock
import testtools

from oslo_config import cfg
from oslo_db.sqlalchemy import enginefacade
from oslo_log import log as logging
from fm.db import migration
from fm.tests import conf_fixture


CONF = cfg.CONF
_DB_CACHE = None
INIT_VERSION = 0

sys.modules['fm_core'] = mock.Mock()


class TestCase(testtools.TestCase):
    """Test case base class for all unit tests."""

    def setUp(self):
        """Run before each test method to initialize test environment."""
        super(TestCase, self).setUp()

        def fake_logging_setup(*args):
            pass

        self.useFixture(
            fixtures.MonkeyPatch('oslo_log.log.setup', fake_logging_setup))
        logging.register_options(CONF)

        self.useFixture(conf_fixture.ConfFixture(CONF))

        global _DB_CACHE
        if not _DB_CACHE:
            engine = enginefacade.get_legacy_facade().get_engine()
            engine.dispose()
            engine.connect()
            migration.db_sync(engine=engine)

    def tearDown(self):
        super(TestCase, self).tearDown()
