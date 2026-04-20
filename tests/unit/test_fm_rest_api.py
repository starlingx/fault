#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for fm-rest-api objects and utility modules."""
# pylint: disable=protected-access,unused-argument
import datetime
import os
import sys
import unittest
from unittest import mock
from tests import test_helpers  # noqa: F401,E402
from tests import constants as TC

# Mock only the truly unavailable modules
_rest_api_path = os.path.join(
    os.path.dirname(__file__), '..', '..', 'fm-rest-api', 'fm')
if _rest_api_path not in sys.path:
    sys.path.insert(0, _rest_api_path)


class TestObjectsUtils(unittest.TestCase):
    """Test fm.objects.utils module."""

    def setUp(self):
        from fm.objects import utils
        self.utils = utils

    def test_datetime_or_none_with_none(self):
        self.assertIsNone(self.utils.datetime_or_none(None))

    def test_datetime_or_none_with_naive_datetime(self):
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0)
        result = self.utils.datetime_or_none(dt)
        self.assertIsNotNone(result.tzinfo)

    def test_datetime_or_none_with_aware_datetime(self):
        import iso8601
        dt = datetime.datetime(2024, 1, 1, tzinfo=iso8601.UTC)
        result = self.utils.datetime_or_none(dt)
        self.assertEqual(result, dt)

    def test_datetime_or_none_invalid(self):
        with self.assertRaises(ValueError):
            self.utils.datetime_or_none("not a datetime")

    def test_datetime_or_str_or_none_with_none(self):
        self.assertIsNone(self.utils.datetime_or_str_or_none(None))

    def test_datetime_or_str_or_none_with_string(self):
        result = self.utils.datetime_or_str_or_none(
            "2024-01-01T00:00:00")
        self.assertIsNotNone(result)

    def test_bool_or_none_with_none(self):
        self.assertFalse(self.utils.bool_or_none(None))

    def test_bool_or_none_with_true_string(self):
        self.assertTrue(self.utils.bool_or_none('true'))

    def test_bool_or_none_with_int_one(self):
        self.assertTrue(self.utils.bool_or_none(1))

    def test_bool_or_none_with_int_zero(self):
        self.assertFalse(self.utils.bool_or_none(0))

    def test_int_or_none_with_none(self):
        self.assertIsNone(self.utils.int_or_none(None))

    def test_int_or_none_with_value(self):
        self.assertEqual(self.utils.int_or_none(42), 42)

    def test_str_or_none_with_none(self):
        self.assertIsNone(self.utils.str_or_none(None))

    def test_str_or_none_with_value(self):
        self.assertEqual(self.utils.str_or_none(42), '42')

    def test_uuid_or_none_with_none(self):
        self.assertIsNone(self.utils.uuid_or_none(None))

    def test_uuid_or_none_with_valid(self):
        u = TC.TEST_UUID
        self.assertEqual(self.utils.uuid_or_none(u), u)

    def test_uuid_or_none_invalid(self):
        with self.assertRaises(ValueError):
            self.utils.uuid_or_none(12345)

    def test_dt_serializer(self):
        fn = self.utils.dt_serializer('timestamp')
        self.assertTrue(callable(fn))

    def test_dt_deserializer_none(self):
        self.assertIsNone(self.utils.dt_deserializer(None, None))

    def test_dt_deserializer_value(self):
        result = self.utils.dt_deserializer(None, "2024-01-01T00:00:00")
        self.assertIsNotNone(result)


class TestFmCommonExceptions(unittest.TestCase):
    """Test fm.common.exceptions module."""

    def setUp(self):
        from fm.common import exceptions
        self.exc = exceptions

    def test_api_error_default(self):
        e = self.exc.ApiError()
        self.assertIsNotNone(str(e))

    def test_api_error_with_message(self):
        e = self.exc.ApiError(message="test error")
        self.assertIn("test error", str(e))

    def test_not_found(self):
        self.assertEqual(self.exc.NotFound.code, 404)

    def test_alarm_not_found(self):
        e = self.exc.AlarmNotFound(alarm='test-123')
        self.assertIn('test-123', str(e))

    def test_event_log_not_found(self):
        e = self.exc.EventLogNotFound(eventLog='log-1')
        self.assertIn('log-1', str(e))

    def test_node_not_found(self):
        e = self.exc.NodeNotFound(node='n1')
        self.assertIn('n1', str(e))

    def test_server_not_found(self):
        e = self.exc.ServerNotFound(server='s1')
        self.assertIn('s1', str(e))

    def test_invalid(self):
        self.assertEqual(self.exc.Invalid.code, 400)

    def test_patch_error(self):
        e = self.exc.PatchError(patch='p1', reason='bad')
        self.assertIn('p1', str(e))

    def test_config_invalid(self):
        e = self.exc.ConfigInvalid(error_msg='bad')
        self.assertIn('bad', str(e))

    def test_invalid_parameter_value(self):
        e = self.exc.InvalidParameterValue(err='bad')
        self.assertIn('bad', str(e))

    def test_invalid_identity(self):
        e = self.exc.InvalidIdentity(identity='xyz')
        self.assertIn('xyz', str(e))

    def test_policy_not_authorized(self):
        self.assertEqual(self.exc.PolicyNotAuthorized.code, 401)

    def test_conflict(self):
        self.assertEqual(self.exc.Conflict.code, 409)

    def test_alarm_already_exists(self):
        e = self.exc.AlarmAlreadyExists(uuid='u1')
        self.assertIn('u1', str(e))

    def test_event_log_already_exists(self):
        e = self.exc.EventLogAlreadyExists(id='i1')
        self.assertIn('i1', str(e))

    def test_format_message(self):
        e = self.exc.ApiError(message="test")
        self.assertIsNotNone(e.format_message())


class TestFmCommonUtils(unittest.TestCase):
    """Test fm.common.utils module."""

    def setUp(self):
        from fm.common import utils
        self.utils = utils

    def test_safe_rstrip_normal(self):
        self.assertEqual(self.utils.safe_rstrip('hello/', '/'), 'hello')

    def test_safe_rstrip_empty_result(self):
        self.assertEqual(self.utils.safe_rstrip('/', '/'), '/')

    def test_safe_rstrip_non_string(self):
        self.assertEqual(self.utils.safe_rstrip(123), 123)

    @mock.patch('builtins.open', mock.mock_open(
        read_data='VERSION_CODENAME=bullseye\n'))
    def test_get_debian_codename(self):
        self.utils.get_debian_codename.cache_clear()
        self.assertEqual(self.utils.get_debian_codename(), 'bullseye')

    @mock.patch('builtins.open', side_effect=FileNotFoundError)
    def test_get_debian_codename_missing(self, _):
        self.utils.get_debian_codename.cache_clear()
        self.assertIsNone(self.utils.get_debian_codename())


class TestFmCommonConstants(unittest.TestCase):
    """Test fm.common.constants module."""

    def test_suppression_constants(self):
        from fm.common import constants
        self.assertEqual(constants.FM_SUPPRESSED, 'suppressed')
        self.assertEqual(constants.FM_UNSUPPRESSED, 'unsuppressed')

    def test_db_constants(self):
        from fm.common import constants
        self.assertEqual(constants.DB_SUPPRESS_STATUS, 1)
        self.assertEqual(constants.DB_MGMT_AFFECTING, 2)
        self.assertEqual(constants.DB_DEGRADE_AFFECTING, 3)

    def test_os_constants(self):
        from fm.common import constants
        self.assertEqual(constants.OS_DEBIAN_BULLSEYE, 'bullseye')
        self.assertEqual(constants.OS_DEBIAN_TRIXIE, 'trixie')


class TestFmCommonI18n(unittest.TestCase):
    """Test fm.common.i18n module."""

    def test_translator_exists(self):
        from fm.common import i18n
        self.assertTrue(callable(i18n._))


class TestFmCommonPolicy(unittest.TestCase):
    """Test fm.common.policy module."""

    def test_reset(self):
        from fm.common import policy
        policy.reset()

    def test_init(self):
        from fm.common import policy
        policy.reset()
        result = policy.init()
        self.assertIsNotNone(result)


class TestFmDbApi(unittest.TestCase):
    """Test fm.db.api module."""

    def test_backend_mapping(self):
        from fm.db import api
        self.assertIn('sqlalchemy', api._BACKEND_MAPPING)


class TestFmDbMigration(unittest.TestCase):
    """Test fm.db.migration module."""

    def test_migrate_repo_path(self):
        from fm.db import migration
        self.assertIn('migrations', migration.MIGRATE_REPO_PATH)

    def test_functions_exist(self):
        from fm.db import migration
        self.assertTrue(callable(migration.db_sync))
        self.assertTrue(callable(migration.upgrade))
        self.assertTrue(callable(migration.version))


if __name__ == '__main__':
    unittest.main()
