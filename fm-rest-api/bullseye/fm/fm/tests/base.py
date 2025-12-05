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
import os

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

sys.modules['fm_core'] = mock.Mock()


class TestCase(testtools.TestCase):
    """Test case base class for all unit tests."""

    def setUp(self):
        """Run before each test method to initialize test environment."""
        super(TestCase, self).setUp()

        test_timeout = os.environ.get('OS_TEST_TIMEOUT', 0)
        try:
            test_timeout = int(test_timeout)
        except ValueError:
            # If timeout value is invalid do not set a timeout.
            test_timeout = 0
        if test_timeout > 0:
            self.useFixture(fixtures.Timeout(test_timeout, gentle=True))
        self.useFixture(fixtures.NestedTempfile())
        self.useFixture(fixtures.TempHomeDir())

        if (os.environ.get('OS_STDOUT_CAPTURE') == 'True' or
                os.environ.get('OS_STDOUT_CAPTURE') == '1'):
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        if (os.environ.get('OS_STDERR_CAPTURE') == 'True' or
                os.environ.get('OS_STDERR_CAPTURE') == '1'):
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))

        self.log_fixture = self.useFixture(fixtures.FakeLogger())

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
